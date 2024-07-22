#!/usr/bin/env python3
import os
import sys
import base64
import logging
import requests
import subprocess
import typer
from dotenv import load_dotenv
from typing import Optional

app = typer.Typer(add_completion=False, help="An awesome todo list CLI app.")
load_dotenv()

TODO_FILE_PATH = os.getenv("TODO_FILE_PATH")
DEFAULT_TODO_FILE_NAME = os.getenv("DEFAULT_TODO_FILE_NAME")
TODO_EDITOR = os.getenv("TODO_EDITOR")
LOG_FILE_NAME = os.getenv("LOG_FILE_NAME")
MAX_LIST_ITEMS = int(os.getenv("MAX_LIST_ITEMS"))
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
*_, REPO_OWNER, REPO_NAME = GITHUB_REPO.split("/") if GITHUB_REPO else [None, None, None]
LOG_FILE_PATH = os.path.join(TODO_FILE_PATH, LOG_FILE_NAME)

if not TODO_FILE_PATH:
    typer.echo("Environment variable TODO_FILE_PATH not set.")
    sys.exit(1)

log_file_path = os.path.expanduser(LOG_FILE_PATH)
logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


## Github API functions


def github_api_request(method, url, **kwargs):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    response = requests.request(method, url, headers=headers, **kwargs)
    response.raise_for_status()
    return response.json()


def get_file_sha(file_name):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_name}"
    try:
        response = github_api_request("GET", url)
        return response["sha"]
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise


def get_file_content_github(file_path):
    file_name = os.path.basename(file_path)
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_name}"
    response = github_api_request("GET", url)
    content = response["content"]
    return base64.b64decode(content).decode("utf-8")


def update_file_github(file_name, content, message):
    sha = get_file_sha(file_name)
    data = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "sha": sha,
    }
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_name}"
    github_api_request("PUT", url, json=data)


def update_github(file_path, message):
    file_name = os.path.basename(file_path)
    with open(file_path, "r") as f:
        content = f.read()
    update_file_github(file_name, content, message)


def is_git_repo(path: str) -> bool:
    return (
        subprocess.call(
            ["git", "-C", path, "rev-parse"],
            stderr=subprocess.STDOUT,
            stdout=open(os.devnull, "w"),
        )
        == 0
    )


def update_file_from_github(todo_file_path: str):
    # Fetch the latest content from GitHub
    content = get_file_content_github(todo_file_path)

    # Write the content to the local file
    with open(todo_file_path, "w") as f:
        f.write(content)
    return content


def log_update_github(file_path: str, message: str):
    if is_git_repo(TODO_FILE_PATH) and GITHUB_TOKEN and GITHUB_REPO:
        file_name = os.path.basename(file_path)
        update_file_from_github(LOG_FILE_PATH)
        logging.info(f"{file_name} - {message}")
        update_github(LOG_FILE_PATH, f"Update: {file_path} - {message}")
        update_github(file_path, message)
    else:
        logging.info(f"{file_path} - {message}")


def create_todo_file_if_not_exists(todo_file_path: str):
    if not os.path.exists(todo_file_path):
        with open(todo_file_path, "w"):
            pass
        message = f"Create new todo list: {os.path.basename(todo_file_path)}"
        log_update_github(todo_file_path, message)


## To Do functions


def add_task(todo_file_path: str, task: str, priority: int = 4):
    create_todo_file_if_not_exists(todo_file_path)
    task_line = f"{priority}:{task}\n"

    if is_git_repo(TODO_FILE_PATH) and GITHUB_TOKEN and GITHUB_REPO:
        try:
            update_file_from_github(todo_file_path)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                update_file_github(os.path.basename(todo_file_path), "", "Create new todo list")

    with open(todo_file_path, "r") as f:
        lines = f.readlines()

    if len(lines) >= MAX_LIST_ITEMS:
        typer.echo(f"Maximum number of tasks ({MAX_LIST_ITEMS}) reached.")
        typer.echo("Please edit your todo list to add more tasks.")
        return

    with open(todo_file_path, "a") as f:
        f.write(task_line)
    typer.echo(f"Task added with priority {priority}: {task}")

    message = f"Task added: {task}"
    log_update_github(todo_file_path, message)


def mark_task_as_done(todo_file_path: str, task_index: int):
    tasks = get_tasks(todo_file_path)

    with open(todo_file_path, "r") as f:
        lines = f.readlines()

    if 1 <= task_index <= len(tasks):
        completed_task = tasks[task_index - 1].strip()
        lines.remove(f"{completed_task}\n")

        with open(todo_file_path, "w") as f:
            f.writelines(lines)

        typer.echo(f"Task marked as done: {completed_task}")
        message = f"Task completed: {completed_task}"
        log_update_github(todo_file_path, message)
    else:
        typer.echo("Invalid task number.")


def get_tasks(todo_file_path: str):
    create_todo_file_if_not_exists(todo_file_path)

    if is_git_repo(TODO_FILE_PATH) and GITHUB_TOKEN and GITHUB_REPO:
        content = update_file_from_github(todo_file_path)
    else:
        with open(todo_file_path, "r") as f:
            content = f.read()

    tasks = sorted(content.splitlines(), key=lambda x: int(x.split(":")[0]))

    return tasks


def list_tasks(todo_file_path: str):
    tasks = get_tasks(todo_file_path)
    num_tasks = min(len(tasks), MAX_LIST_ITEMS)
    for i in range(num_tasks):
        typer.echo(f"{i+1}. {tasks[i].strip()}")
    if num_tasks == 0:
        typer.echo("No tasks in To Do.")


def edit_todo_file(todo_file_path: str):
    if is_git_repo(TODO_FILE_PATH) and GITHUB_TOKEN and GITHUB_REPO:
        update_file_from_github(todo_file_path)

    os.system(f"{TODO_EDITOR} {todo_file_path}")
    file_name = os.path.basename(todo_file_path)
    message = f"Edit todo file: {file_name}"
    log_update_github(todo_file_path, message)


def list_all_todo_files():
    todo_files = [
        filename
        for filename in os.listdir(TODO_FILE_PATH)
        if filename.startswith("todo_")
    ]

    if todo_files:
        for todo_file in todo_files:
            todo_file_path = os.path.join(TODO_FILE_PATH, todo_file)
            todo_name = todo_file.replace("todo_", "").replace(".md", "")
            typer.echo(f"{todo_name}:")
            list_tasks(todo_file_path)
            typer.echo()  # Add a blank line between lists
    else:
        typer.echo("No todo lists found.")


def move_task(source_todo_file_path: str, task_index: int, dest_todo_file_path: str):
    source_tasks = get_tasks(source_todo_file_path)
    dest_tasks = get_tasks(dest_todo_file_path)

    if 1 <= task_index <= len(source_tasks):
        task_to_move = source_tasks[task_index - 1].strip()

        with open(source_todo_file_path, "r") as f:
            source_lines = f.readlines()

        source_lines.remove(f"{task_to_move}\n")

        with open(source_todo_file_path, "w") as f:
            f.writelines(source_lines)

        with open(dest_todo_file_path, "a") as f:
            f.write(f"{task_to_move}\n")

        source_name = (
            source_todo_file_path.replace(TODO_FILE_PATH, "")
            .replace("todo_", "")
            .replace(".md", "")
        )
        dest_name = (
            dest_todo_file_path.replace(TODO_FILE_PATH, "")
            .replace("todo_", "")
            .replace(".md", "")
        )
        typer.echo(f"Task moved: {task_to_move} from {source_name} to {dest_name}")
        message = f"Move task: {task_to_move} from {source_name} to {dest_name}"
        log_update_github(source_todo_file_path, message)
        log_update_github(dest_todo_file_path, message)
    else:
        typer.echo("Invalid task number.")


def tag_task(todo_file_path: str, task_index: int, priority: int):
    tasks = get_tasks(todo_file_path)

    if 1 <= task_index <= len(tasks):
        tagged_task = tasks[task_index - 1].strip().split(":", 1)[1].strip()

        with open(todo_file_path, "r") as f:
            lines = f.readlines()

        lines[lines.index(f"{tasks[task_index - 1]}\n")] = f"{priority}:{tagged_task}\n"

        with open(todo_file_path, "w") as f:
            f.writelines(lines)

        typer.echo(f"Task tagged with priority {priority}: {tagged_task}")
        message = f"Tag task with priority {priority}: {tagged_task}"
        log_update_github(todo_file_path, message)
    else:
        typer.echo("Invalid task number.")


def next_task(todo_file_path: str):
    tasks = get_tasks(todo_file_path)
    if tasks:
        next_task = tasks[0].strip()
        typer.echo(f"Next task: {next_task}")
    else:
        typer.echo("No tasks in To Do.")


## CLI functions


@app.command(help="Add a new task to the todo list")
def add(
    task: str,
    priority: int = typer.Option(4, "-p", "--priority", help="Priority of the task"),
    todo_file_name: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-f", "--todo-file-name", help="Name of the todo file"
    ),
):
    todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{todo_file_name}.md")
    )
    add_task(todo_file_path, task, priority)


@app.command(help="List tasks in the todo list (alias: ls)")
@app.command("ls", hidden=True)
def list(
    todo_file_name: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-f", "--todo-file-name", help="Name of the todo file"
    ),
):
    todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{todo_file_name}.md")
    )
    list_tasks(todo_file_path)


@app.command(help="Get the next highest priority task in the todo list")
def next(
    todo_file_name: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-f", "--todo-file-name", help="Name of the todo file"
    ),
):
    todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{todo_file_name}.md")
    )
    next_task(todo_file_path)


@app.command(help="Mark a task as done")
def mark(
    task_index: int,
    todo_file_name: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-f", "--todo-file-name", help="Name of the todo file"
    ),
):
    todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{todo_file_name}.md")
    )
    mark_task_as_done(todo_file_path, task_index)


@app.command(help="Tag a task with a new priority")
def tag(
    task_index: int,
    priority: int = typer.Option(
        4, "-p", "--priority", help="New priority for the task"
    ),
    todo_file_name: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-f", "--todo-file-name", help="Name of the todo file"
    ),
):
    todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{todo_file_name}.md")
    )
    tag_task(todo_file_path, task_index, priority)


@app.command(help="Edit the todo list")
def edit(
    todo_file_name: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-f", "--todo-file-name", help="Name of the todo file"
    ),
):
    todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{todo_file_name}.md")
    )
    edit_todo_file(todo_file_path)


@app.command(help="List all todo files")
def list_all():
    list_all_todo_files()


@app.command(help="Move a task from one todo list to another (alias: mv)")
@app.command("mv", hidden=True)
def move(
    task_index: int,
    source_todo: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-s", "--source-todo", help="Source todo file name"
    ),
    dest_todo: str = typer.Option(
        DEFAULT_TODO_FILE_NAME,
        "-d",
        "--dest-todo",
        help="Destination todo file name",
    ),
):
    source_todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{source_todo}.md")
    )
    dest_todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{dest_todo}.md")
    )
    move_task(source_todo_file_path, task_index, dest_todo_file_path)


if __name__ == "__main__":
    app()
