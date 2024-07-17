#!/usr/bin/env python3
import os
import subprocess
import sys
import logging
import typer
from dotenv import load_dotenv
from typing import Optional

app = typer.Typer(add_completion=False)
load_dotenv()

TODO_FILE_PATH = os.getenv("TODO_FILE_PATH")
DEFAULT_TODO_FILE_NAME = os.getenv("DEFAULT_TODO_FILE_NAME")
TODO_EDITOR = os.getenv("TODO_EDITOR")
LOG_FILE_NAME = os.getenv("LOG_FILE_NAME")
MAX_LIST_ITEMS = int(os.getenv("MAX_LIST_ITEMS"))
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


def create_todo_file_if_not_exists(todo_file_path: str):
    if not os.path.exists(todo_file_path):
        with open(todo_file_path, "w"):
            pass
        log_create_todo_list(todo_file_path)


def add_task(todo_file_path: str, task: str, priority: int = 4):
    create_todo_file_if_not_exists(todo_file_path)
    task_line = f"{priority}:{task}\n"

    with open(todo_file_path, "r") as f:
        lines = f.readlines()

    if len(lines) >= MAX_LIST_ITEMS:
        typer.echo(f"Maximum number of tasks ({MAX_LIST_ITEMS}) reached.")
        typer.echo("Please edit your todo list to add more tasks.")
        return

    with open(todo_file_path, "a") as f:
        f.write(task_line)
    typer.echo(f"Task added with priority {priority}: {task}")

    log_task(task)


def log_task(task: str):
    logging.info(f"Task added: {task}")
    if is_git_repo(TODO_FILE_PATH):
        git_commit_and_push(TODO_FILE_PATH, f"Add task: {task}")


def mark_task_as_done(todo_file_path: str, task_index: int):
    create_todo_file_if_not_exists(todo_file_path)

    with open(todo_file_path, "r") as f:
        lines = f.readlines()

    tasks = sorted(lines, key=lambda x: int(x.split(":")[0]))

    if 1 <= task_index <= len(tasks):
        completed_task = tasks[task_index - 1].strip()
        lines.remove(tasks[task_index - 1])

        with open(todo_file_path, "w") as f:
            f.writelines(lines)

        typer.echo(f"Task marked as done: {completed_task}")
        log_task_completed(completed_task)
    else:
        typer.echo("Invalid task number.")


def log_task_completed(task: str):
    logging.info(f"Task completed: {task}")
    if is_git_repo(TODO_FILE_PATH):
        git_commit_and_push(TODO_FILE_PATH, f"Task completed: {task}")


def get_tasks(todo_file_path: str):
    create_todo_file_if_not_exists(todo_file_path)

    if is_git_repo(os.path.dirname(todo_file_path)):
        git_pull(os.path.dirname(todo_file_path))

    with open(todo_file_path, "r") as f:
        lines = f.readlines()

    tasks = sorted(lines, key=lambda x: int(x.split(":")[0]))

    return tasks


def list_tasks(todo_file_path: str):
    tasks = get_tasks(todo_file_path)
    num_tasks = min(len(tasks), MAX_LIST_ITEMS)
    for i in range(num_tasks):
        typer.echo(f"{i+1}: {tasks[i].strip()}")
    if num_tasks == 0:
        typer.echo("No tasks in To Do.")


def edit_todo_file(todo_file_path: str):
    if is_git_repo(os.path.dirname(todo_file_path)):
        git_pull(os.path.dirname(todo_file_path))
    os.system(f"{TODO_EDITOR} {todo_file_path}")


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

        source_lines.remove(source_tasks[task_index - 1])

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
        log_move_task(source_todo_file_path, dest_todo_file_path, task_to_move)
    else:
        typer.echo("Invalid task number.")


def log_move_task(source_todo_file_path: str, dest_todo_file_path: str, task: str):
    logging.info(
        f"Task moved: '{task}' from '{source_todo_file_path}' to '{dest_todo_file_path}'"
    )
    if is_git_repo(TODO_FILE_PATH):
        git_commit_and_push(
            TODO_FILE_PATH,
            f"Move task: '{task}' from '{source_todo_file_path}' to '{dest_todo_file_path}'",
        )


def log_create_todo_list(todo_file_path: str):
    logging.info(f"Created new todo list: '{os.path.basename(todo_file_path)}'")
    if is_git_repo(TODO_FILE_PATH):
        git_commit_and_push(TODO_FILE_PATH, f"Add new todo list: {todo_file_path}")


def is_git_repo(path: str) -> bool:
    return (
        subprocess.call(
            ["git", "-C", path, "rev-parse"],
            stderr=subprocess.STDOUT,
            stdout=open(os.devnull, "w"),
        )
        == 0
    )


def git_commit_and_push(repo_path: str, message: str):
    try:
        for file in os.listdir(repo_path):
            if file.startswith("todo"):
                subprocess.check_call(["git", "-C", repo_path, "add", file])
        subprocess.check_call(
            ["git", "-C", repo_path, "commit", "-m", message, "--quiet"]
        )
        subprocess.check_call(["git", "-C", repo_path, "pull", "--quiet"])
        subprocess.check_call(["git", "-C", repo_path, "push", "--quiet"])
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error during git operations: {e}")


def git_pull(repo_path: str):
    try:
        subprocess.check_call(["git", "-C", repo_path, "pull", "--quiet"])
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error during git pull operation: {e}")


def tag_task(todo_file_path: str, task_index: int, priority: int):
    tasks = get_tasks(todo_file_path)

    if 1 <= task_index <= len(tasks):
        tagged_task = tasks[task_index - 1].strip().split(":", 1)[1].strip()

        with open(todo_file_path, "r") as f:
            lines = f.readlines()

        lines[lines.index(tasks[task_index - 1])] = f"{priority}: {tagged_task}\n"

        with open(todo_file_path, "w") as f:
            f.writelines(lines)

        typer.echo(f"Task tagged with priority {priority}: {tagged_task}")
        log_task(tagged_task)
    else:
        typer.echo("Invalid task number.")


def log_tag_task(task: str, new_priority: int):
    logging.info(f"Task tagged with new priority {new_priority}: {task}")
    if is_git_repo(TODO_FILE_PATH):
        git_commit_and_push(
            TODO_FILE_PATH, f"Tag task with new priority {new_priority}: {task}"
        )


@app.command()
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


@app.command()
def edit(
    todo_file_name: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-f", "--todo-file-name", help="Name of the todo file"
    ),
):
    todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{todo_file_name}.md")
    )
    edit_todo_file(todo_file_path)


@app.command()
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


@app.command()
def list(
    todo_file_name: str = typer.Option(
        DEFAULT_TODO_FILE_NAME, "-f", "--todo-file-name", help="Name of the todo file"
    ),
):
    todo_file_path = os.path.expanduser(
        os.path.join(TODO_FILE_PATH, f"todo_{todo_file_name}.md")
    )
    list_tasks(todo_file_path)


@app.command()
def list_all():
    list_all_todo_files()


@app.command()
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


@app.command()
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


if __name__ == "__main__":
    app()
