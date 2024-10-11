#!/bin/bash

COMMANDS_URL=$(dirname "'{{request.url}}'")
PLUGIN_NAME=$(basename "$COMMANDS_URL")

#{% if description %}
cat << EOF
'{{ description }}'
EOF
#{% endif %}

echo -n "Do you want to install ${PLUGIN_NAME} (mqtt-rest)? [y/n] "
read -r user_choice
user_choice=$(echo "$user_choice" | tr '[:upper:]' '[:lower:]')

if [[ "$user_choice" == "no" || "$user_choice" == "n" ]]; then
    echo "Exiting the script."
    exit 0
fi

#{% if dependencies %}
commands=('{{ dependencies|join(", ", attribute="command") }}')
packages=('{{ dependencies|join(", ", attribute="package") }}')
not_installed=()

# Check if the dependencies are installed if not then add related package to not_installed array
for command in "${commands[@]}"; do
    if ! command -v "$command" &> /dev/null; then
        not_installed+=("${packages[$(echo "${commands[@]}" | tr ' ' '\n' | grep -n "$command" | cut -d: -f1)]}")
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
if ! wget -q -O "$DOWNLOAD_LOCATION" "${COMMANDS_URL}/manager"
then
    echo "Failed to download the manager for ${PLUGIN_NAME} plugin."
    exit 1
fi
chmod +x "$DOWNLOAD_LOCATION"

echo "The ${PLUGIN_NAME} plugin has been installed successfully."
echo
echo "You can now run the plugin using the following command:"
echo "$DOWNLOAD_LOCATION"
echo

$DOWNLOAD_LOCATION -h
