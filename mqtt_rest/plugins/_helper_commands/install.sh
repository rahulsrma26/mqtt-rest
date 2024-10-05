#!/bin/bash

COMMANDS_URL=$(dirname "{{request.url}}")
PLUGIN_NAME=$(basename "$COMMANDS_URL")

if [[ $ASSUME_YES -eq 1 ]]; then
    user_choice="yes"
else
    echo "Do you want to install ${PLUGIN_NAME} (mqtt-rest)? (yes/no): "
    read -r user_choice
fi
user_choice=$(echo "$user_choice" | tr '[:upper:]' '[:lower:]')

if [[ "$user_choice" == "no" || "$user_choice" == "n" ]]; then
    echo "Exiting the script."
    exit 0
fi

#{% if dependencies %}
dependencies=({{dependencies}})
not_installed=()
for dependency in "${dependencies[@]}"; do
    if ! command -v "$dependency" &> /dev/null; then
        not_installed+=("$dependency")
    fi
done
if [ ${#not_installed[@]} -ne 0 ]; then
    echo "The following dependencies are not installed: ${not_installed[*]}"
    if [ "$EUID" -ne 0 ]; then
        echo "Please run this script as root or install them before running."
        exit 1
    fi

    echo "Installing the dependencies..."
    apt update
    apt install -y "${not_installed[@]}"
fi
#{% endif %}

PLUGIN_DIR="$HOME/mqtt-rest/${PLUGIN_NAME}"
mkdir -p "${PLUGIN_DIR}"
DOWNLOAD_LOCATION="${PLUGIN_DIR}/manager"
wget -q -O "$DOWNLOAD_LOCATION" "${COMMANDS_URL}/manager"
chmod +x "$DOWNLOAD_LOCATION"

echo "The ${PLUGIN_NAME} plugin has been installed successfully."
echo "You can now run the plugin using the following command:"
echo "$DOWNLOAD_LOCATION"

$DOWNLOAD_LOCATION -h
