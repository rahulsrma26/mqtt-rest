#!/bin/bash

COMMANDS_URL=$(dirname "{{request.url}}")
PLUGIN_NAME=$(basename "$(dirname "$COMMANDS_URL")")
DATA_COMMAND="{{data_command}}"
CRON_COMMAND=$(realpath "$0")

# Function to display the help message
show_help() {
    echo "Usage: $0 [-a frequency] [-r] [-s] [-h]"
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

get_cron_frequency() {
    local frequency=$1
    local unit=${frequency: -1}
    local number=${frequency:0:${#frequency}-1}

    case $unit in
        m) echo "*/$number * * * *";;
        h) echo "0 */$number * * *";;
        d) echo "0 0 */$number * *";;
        *) echo "Invalid frequency unit. Please use one of {m, h, d}."
           exit 1 ;;
    esac
}

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
    OUTPUT=$($DATA_COMMAND)
    HOSTNAME=$(hostname)
    curl -X PUT -H "Content-Type: text/plain" -d "$OUTPUT" "$COMMANDS_URL/submit/$HOSTNAME"
    exit 0
fi

CRON_FREQUENCY=$(get_cron_frequency "$FREQUENCY")

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
    (crontab -l 2>/dev/null; echo "$CRON_FREQUENCY $CRON_COMMAND -e") | crontab -
fi
