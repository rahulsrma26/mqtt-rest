#!/bin/bash

COMMANDS_URL=$(dirname "'{{url}}'")
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

is_updated=0
run_update_once() {
    if [ $is_updated -eq 0 ]; then
        apt update
        is_updated=1
    fi
}

#{% if dependencies %}
#{% for dependency in dependencies %}
# Check if '{{ dependency.command }}' is installed
if ! command -v '{{ dependency.command }}' &> /dev/null; then
    echo "The '{{ dependency.package }}' package is required to run this plugin."
    if [ "$EUID" -ne 0 ]; then
        echo "Please run this script as root or install the package before running."
        exit 1
    fi
    echo "Installing the '{{ dependency.package }}' package..."
    run_update_once
    apt install -y '{{ dependency.package }}'
    #{% if dependency.post_install %}
    # Function that run the post install commands '{{function(dependency.post_install, call_afterwards=True, indent=1)}}'
    #{% endif %}
fi
#{% endfor %}
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
