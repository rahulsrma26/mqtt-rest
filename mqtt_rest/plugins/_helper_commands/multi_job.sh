#!/bin/bash

# {% if need_root %}
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi
# {% endif %}


COMMANDS_URL=$(dirname "'{{url}}'")
PLUGIN_NAME=$(basename "$(dirname "$COMMANDS_URL")")
BASE_CRON_COMMAND=$(realpath "$0")

# Function to display the help message
show_help() {
    echo "Usage: $0 [-e arg] [-m] [-h]"
    echo
    echo "Options:"
    echo "  -e  Execute ${PLUGIN_NAME} script with 'arg' and send the output back to server."
    echo "  -m  Manage cron jobs."
    echo "  -h  Show this help message."
    echo
}

# Function that return different frequency options '{{function(get_cron_frequency)}}'

# Function that return different job options '{{function(get_job_options)}}'

# Function that run the job with local $1 as args '{{function(run_job)}}'

manage_cron_jobs() {
    while true; do
        echo "---------------"
        echo "CRON_MANAGEMENT"
        echo "---------------"
        echo "0) Exit"
        OPTIONS=$(get_job_options)
        echo "$OPTIONS" | awk '{print NR ") " $0}'
        echo -n "Select option: "
        read -r OPTION

        if [[ $OPTION -eq 0 ]]; then
            exit 0
        fi

        JOB_ARG=$(echo "$OPTIONS" | sed -n "${OPTION}p")
        CRON_COMMAND="$BASE_CRON_COMMAND -e $JOB_ARG"
        CRON_EXISTS=$(crontab -l | grep -c "$CRON_COMMAND")

        if [[ $CRON_EXISTS -eq 1 ]]; then
            echo -n "Cron job for the script already exists. Do you want to remove it? [y/n] "
            read -r ANSWER
            ANSWER=$(echo "$ANSWER" | tr '[:upper:]' '[:lower:]')
            if [[ "$ANSWER" == "y" ]]; then
                crontab -l | grep -v "$CRON_COMMAND" | crontab -
            fi
        else
            echo -n "Cron job for the script does not exist. Do you want to add it? [y/n] "
            read -r ANSWER
            ANSWER=$(echo "$ANSWER" | tr '[:upper:]' '[:lower:]')
            if [[ "$ANSWER" == "y" ]]; then
                echo -n "Enter the frequency for the job (e.g., 1h, 30m, 1d): "
                read -r FREQUENCY
                CRON_FREQUENCY=$(get_cron_frequency "$FREQUENCY")
                (crontab -l 2>/dev/null; echo "$CRON_FREQUENCY $CRON_COMMAND") | crontab -
            fi
        fi
    done
}

# Default values for options
SEND_OUTPUT=0
JOB_ARG=""
CRON_MANAGE=0
SHOW_HELP=0

# Parse command-line arguments
while getopts "e:mh" opt; do
    case "$opt" in
        e) SEND_OUTPUT=1
           JOB_ARG=$OPTARG ;;
        m) CRON_MANAGE=1 ;;
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
    OUTPUT=$(run_job "$JOB_ARG")
    NAME=$(hostname)
    URL_ENCODED_NAME=$(echo "$NAME" | sed -e 's/ /%20/g' -e 's/[^a-zA-Z0-9._-]/%&/g')
    curl -X PUT -H "Content-Type: text/plain" -d "$OUTPUT" "$COMMANDS_URL/submit/$URL_ENCODED_NAME"
    exit 0
fi

if [[ $CRON_MANAGE -eq 1 ]]; then
    manage_cron_jobs
    exit 0
fi
