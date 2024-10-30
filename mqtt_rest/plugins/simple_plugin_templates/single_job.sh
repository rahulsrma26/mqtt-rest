#!/bin/bash

# {% if need_root %}
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi
# {% endif %}

COMMANDS_URL=$(dirname "'_{{url}}_'")
PLUGIN_NAME=$(basename "$(dirname "$COMMANDS_URL")")
CRON_COMMAND=$(realpath "$0")
COMMAND_DIR=$(dirname "$0")

# Function to display the help message
show_help() {
    echo "Usage: $0 [-a frequency] [-r] [-e] [-s] [-h]"
    echo
    echo "Options:"
    echo "  -a  Add/Update cron job with <frequency> (Default: 1h)"
    echo "      where <frequency> is <number><unit> {m, h, d} i.e. minutes, hours, days."
    echo "  -r  Remove cron job."
    echo "  -e  Execute ${PLUGIN_NAME} script and send the output back to server."
    echo "  -s  Display current status of the script."
    echo "  -h  Show this help message."
    echo
}

# Function that return different frequency options '_{{function(freq2cron_func)}}_'

# Function that run the job '_{{function(job_func)}}_'

# Default values for options
FREQUENCY="1h"
CRON_ADD=0
CRON_REMOVE=0
CRON_STATUS=0
SEND_OUTPUT=0
SHOW_HELP=0

# Parse command-line arguments
while getopts "a:resh" opt; do
    case "$opt" in
        a) CRON_ADD=1
           FREQUENCY=$OPTARG ;;
        r) CRON_REMOVE=1 ;;
        e) SEND_OUTPUT=1 ;;
        s) CRON_STATUS=1 ;;
        h) SHOW_HELP=1 ;;
        *) show_help
           exit 1 ;;
    esac
done

# Show help if the -h flag is set
if [[ $SHOW_HELP -eq 1 ]]; then
    show_help
    exit 0
fi

# Check if the script is executed with -e flag
if [[ $SEND_OUTPUT -eq 1 ]]; then
    OUTPUT=$('_{{job_func.name}}_')
    echo "Output of the job:"
    echo "$OUTPUT"
    echo
    echo "Sending the output to the server."
    echo
    NAME=$(hostname)
    URL_ENCODED_NAME=$(echo "$NAME" | sed -e 's/ /%20/g' -e 's/[^a-zA-Z0-9._-]/%&/g')
    curl -X PUT -H "Content-Type: text/plain" -d "$OUTPUT" "$COMMANDS_URL/devices/$URL_ENCODED_NAME/submit"
    exit 0
fi

CRON_FREQUENCY=$('_{{freq2cron_func.name}}_' "$FREQUENCY")

# check if both -a and -r are set
if [[ $CRON_ADD -eq 1 && $CRON_REMOVE -eq 1 ]]; then
    echo "Error: Cannot add and remove job at the same time."
    show_help
    exit 1
fi

CRON_EXISTS=$(crontab -l | grep -c "$CRON_COMMAND")

if [[ $CRON_STATUS -eq 1 ]]; then
    if [[ $CRON_EXISTS -eq 1 ]]; then
        echo "Cron job for the script is enabled."
    else
        echo "Cron job for the script is disabled."
    fi
fi

if [[ $CRON_ADD -eq 1 && $CRON_EXISTS -eq 1 ]]; then
    echo "Cron job for the script already exists."
    echo "Removing the existing cron job."
    CRON_REMOVE=1
fi

if [[ $CRON_REMOVE -eq 1 ]]; then
    if [[ $CRON_EXISTS -eq 1 ]]; then
        echo "Removing cron job for the script."
        crontab -l | grep -v "$CRON_COMMAND" | crontab -
    else
        echo "Cron job for the script does not exist."
    fi
fi

if [[ $CRON_ADD -eq 1 ]]; then
    echo "Adding cron job to run the script every $FREQUENCY."
    (crontab -l 2>/dev/null; echo "$CRON_FREQUENCY /bin/bash $CRON_COMMAND -e > $COMMAND_DIR/logs.txt 2>&1") | crontab -
fi
