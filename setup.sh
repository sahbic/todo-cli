#!/bin/sh

# Function to print messages in color
print_in_color() {
    local color="$1"
    local message="$2"
    case $color in
        "blue") printf "\033[0;34m%s\033[0m\n" "$message" ;;
        "green") printf "\033[0;32m%s\033[0m\n" "$message" ;;
        "yellow") printf "\033[0;33m%s\033[0m\n" "$message" ;;
        "red") printf "\033[0;31m%s\033[0m\n" "$message" ;;
        *) printf "%s\n" "$message" ;;
    esac
}

# Ensure script is being run from the main directory
if [ -f "td.py" ]; then
    DIR=$(pwd)
    chmod +x "$DIR/td.py"

    print_in_color "blue" "Directory: $DIR"

    # Check if .bashrc or .zshrc exists and set the shell config file
    SHELL_CONFIG=""
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    fi

    # If neither .bashrc nor .zshrc exists, inform the user to add alias manually
    if [ -z "$SHELL_CONFIG" ]; then
        print_in_color "red" "Unsupported shell. Please add the alias 'td' manually."
        exit 1
    fi

    # Check if the alias already exists in the shell config file
    if ! grep -q "alias td=" "$SHELL_CONFIG"; then
        # Add alias to shell config file in a new paragraph with title "todo-cli alias" if it doesn't exist
        echo "" >> "$SHELL_CONFIG"
        echo "# todo-cli alias" >> "$SHELL_CONFIG"
        echo "alias td='$DIR/venv/bin/python $DIR/td.py'" >> "$SHELL_CONFIG"
        print_in_color "green" "Alias 'td' added to $SHELL_CONFIG"
    else
        print_in_color "yellow" "Alias 'td' already exists in $SHELL_CONFIG"
    fi

    echo ""
    print_in_color "yellow" "Reload your shell configuration by running:"
    print_in_color "yellow" "source $SHELL_CONFIG"
else
    print_in_color "red" "Make sure you are in the main directory of the todo-cli project"
    exit 1
fi

# Create .env file from .env.example if it doesn't exist and guide the user
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_in_color "green" "Created .env file."

    while true; do
        echo ""
        echo "Do you want to fill it with the guided setup? (y/n): "
        read fill
        case $fill in
            [Yy]* )
                echo ""
                echo "Enter the directory where you want to store the todo list, e.g. /home/user/todo-list: "
                read dir
                if [ -d "$dir" ]; then
                    sed -i "s|TODO_FILE_PATH=.*|TODO_FILE_PATH=$dir|g" .env
                    print_in_color "green" "The directory has been set to $dir in .env file"
                else
                    print_in_color "red" "Directory does not exist. Please create it and try again."
                fi
                break;;
            [Nn]* )
                print_in_color "yellow" "You have to fill the .env file manually to use the todo-cli."
                break;;
            * )
                print_in_color "red" "Invalid input. Please answer y or n."
                ;;
        esac
    done
else
    print_in_color "yellow" ".env file already exists."
fi

echo ""
print_in_color "green" "Setup complete"

# guide the user to run the todo-cli and show help
echo ""

print_in_color "yellow" "Run 'td --help' to see the available commands"
