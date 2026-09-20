set shell := ["bash", "-c"]

default:
    just --list

initialise:= 'set -euxo pipefail
    initialise() {
        # Clear the terminal window title on exit
        echo -ne "\033]0; \007"
    }
    trap initialise EXIT
    just _terminal-description'


alias a := app
# Run the web app
app:
    #!/usr/bin/env bash
    {{initialise}} "web app"
    poetry run python app/app.py
    
_terminal-description message=" ":
    echo -ne "\033]0;{{message}}\007"

alias s := setup-terminal-description
# Set up the description for terminal windows
setup-terminal-description:
    #!/usr/bin/env bash
    {{initialise}} setup-terminal-description
    alias_definition="alias j='just'"

    if grep -Fxq "$alias_definition" ~/.zshrc
    then
        echo "Alias already exists in ~/.zshrc"
    else
        echo "$alias_definition" >> ~/.zshrc
        echo "Alias added to ~/.zshrc"
    fi
    
    echo "Please run the following command to apply the changes to this terminal:"
    echo "source ~/.zshrc"


    