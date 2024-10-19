#!/bin/bash

COMMANDS_URL=$(dirname "'_{{url}}_'")
PLUGIN_NAME=$(basename "$COMMANDS_URL")

#{% if description %}
cat << EOF
'_{{ description }}_'
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
        echo "Updating the package list..."
        apt update
        is_updated=1
    fi
}

#{% for dependency in dependencies %}
# Check if '_{{ dependency.command }}_' is installed
if ! command -v '_{{ dependency.command }}_' &> /dev/null; then
    echo "The '_{{ dependency.command }}_' command not found."
    #{% if dependency.install_func %}
    if [ "$EUID" -ne 0 ]; then
        echo "Please run this script as root or install the package before running."
        echo "One can install the package using the following command:"
        # '_{{echo(dependency.install_func.body, indent=2)}}_'
        exit 1
    fi
    run_update_once
    # Function that install commands '_{{function(dependency.install_func, indent=1)}}_'
    echo "Installing the '_{{ dependency.command }}_' package..."
    if ! '_{{dependency.install_func.name}}_'; then
        echo "Failed to install the '_{{ dependency.command }}_' package."
        exit 1
    fi
    #{% else %}
    echo "Please install the package '_{{ dependency.command }}_' before running the script."
    #{% endif %}
fi
#{% endfor %}

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
