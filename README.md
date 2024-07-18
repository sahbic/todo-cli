# todo-cli

## Overview

This is a command-line interface (CLI) tool for managing todo lists. It allows you to add tasks, mark them as done, list tasks, edit todo files, and more.

## Prerequisites

Before using this tool, ensure you have the following installed and set up:

- Python 3.x
- Git (optional, required for version control features)

## Setup

Follow these steps to set up the todo CLI on your system:

1. **Clone the Repository:**

   ```bash
   git clone <repository-url>
   cd todo-cli
   ```

2. **Create a Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Activate the virtual environment
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run Setup Script**

   ```bash
   sh setup.sh
   ```

5. **Configuration**

- Configure the following variables in `.env`:
  - TODO_FILE_PATH: Path to the directory where todo files will be stored.
  - DEFAULT_TODO_FILE_NAME: Default name for todo files.
  - TODO_EDITOR: Your preferred text editor for editing todo files.
  - LOG_FILE_NAME: Name of the log file.
  - MAX_LIST_ITEMS: Maximum number of tasks to display in lists.

## Usage

Once set up, use the following commands to manage your todo lists:

- **Add a task:**

  ```bash
  td add "Task description"
  ```

  Optional: Specify priority with `-p` or `--priority`.

- **Edit a todo file:**

  ```bash
  td edit
  ```

  Opens the todo file in your specified editor.

- **Mark a task as done:**

  ```bash
  td mark <task-index>
  ```

- **List tasks:**

  ```bash
  td list
  ```

- **List all todo files:**

  ```bash
  td list_all
  ```

- **Move a task between todo files:**

  ```bash
  td move <task-index> -s <source-todo> -d <destination-todo>
  ```

- **Tag a task with a priority:**
  ```bash
  td tag <task-index> -p <new-priority>
  ```

## Credits

This project was inspired by a comment of [codazoda](https://news.ycombinator.com/user?id=codazoda) on [Hacker News](https://news.ycombinator.com/item?id=40950584).

## License

This project is licensed under the [MIT License](LICENSE).
