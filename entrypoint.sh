#!/bin/bash

# Enable verbose mode if requested
VERBOSE_MODE=${VERBOSE_MODE:-false}

# Function to display messages if in verbose mode
log_verbose() {
    if [ "$VERBOSE_MODE" = true ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $@"
    fi
}

# Definition of colors
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
NO_COLOR='\033[0m' # No color

# Function to display warning messages in orange
log_warning() {
    echo -e "${ORANGE}$(date '+%Y-%m-%d %H:%M:%S') - $@${NO_COLOR}"
}

# Function to display error messages in red
log_error() {
    echo -e "${RED}$(date '+%Y-%m-%d %H:%M:%S') - $@${NO_COLOR}"
}

# Function to display success messages in green
log_success() {
    echo -e "${GREEN}$(date '+%Y-%m-%d %H:%M:%S') - $@${NO_COLOR}"
}

# Maximum number of consecutive failures before stopping the script
MAX_FAILS=${MAX_FAILS:-3}
fail_count=0

# Set your thresholds
BATTERY_RUNTIME_LOW=${BATTERY_RUNTIME_LOW:-240}
BATTERY_LOW=${BATTERY_LOW:-15}

# UPS address
UPS_ADDRESS=${UPS_ADDRESS:-"localhost"}

# UPS name as it appears in NUT
UPS_NAME=${UPS_NAME:-"ups"}

# Custom command for shutdown
SHUTDOWN_CMD=${SHUTDOWN_CMD:-"systemctl --no-pager halt"}

# Check interval
CHECK_INTERVAL=${CHECK_INTERVAL:-60}

# Attempt to connect to the UPS and check the status of the command
if ! ups_data=$(upsc "${UPS_NAME}@${UPS_ADDRESS}" 2>&1 | grep -v '^Init SSL'); then
    log_error "Connection to UPS failed: $ups_data"
    exit 1
else
    log_success "Connection to UPS successful. Data retrieved: $ups_data"
fi

# Infinite loop to regularly check the battery status
while true; do
    #log_verbose "Checking UPS status..."

    # Retrieve UPS data
    ups_data=$(upsc "${UPS_NAME}@${UPS_ADDRESS}" 2>&1 | grep -v '^Init SSL')
    
    # Check if the upsc command failed
    if [ $? -ne 0 ]; then
        ((fail_count++))
        log_error "Error retrieving UPS data: $ups_data"
        if [ "$fail_count" -ge "$MAX_FAILS" ]; then
            log_error "Maximum number of consecutive failures reached. Stopping the script."
            exit 1
        else
            log_warning "Attempt $fail_count of $MAX_FAILS before stopping the script."
        fi
        # Wait a bit before trying again
        sleep $CHECK_INTERVAL
        continue # Skip to the next iteration of the loop
    else
        fail_count=0 # Reset the failure counter if the command is successful
    fi

    # Extract the current status of the UPS
    ups_status=$(echo "$ups_data" | grep "ups.status:" | awk '{print $2}')

    # Check if the UPS is on battery
    if [[ "$ups_status" =~ OB.* ]]; then
        log_error "Power outage detected."
    elif [[ "$ups_status" =~ OL.* ]]; then
        log_verbose "Power present, no action required."
        # Wait a bit before checking again
        sleep $CHECK_INTERVAL
        continue # Skip to the next iteration of the loop
    fi

    # Extract the current battery charge and runtime values
    battery_charge=$(echo "$ups_data" | grep "battery.charge:" | awk '{print $2}')
    battery_runtime=$(echo "$ups_data" | grep "battery.runtime:" | awk '{print $2}')
    log_verbose "Battery charge: $battery_charge, Runtime: $battery_runtime"

    # Check if the battery charge or runtime is below the thresholds
    if [[ "$battery_charge" -le "$BATTERY_LOW" || "$battery_runtime" -le "$BATTERY_RUNTIME_LOW" ]]; then
        log_error "Battery low or runtime low - triggering host machine shutdown action"
        # Execute the custom shutdown command
        eval $SHUTDOWN_CMD
        # Exit the loop after triggering the action
        break
    elif [[ "$battery_charge" -le $(($BATTERY_LOW + 10)) ]]; then
        log_warning "Warning: Battery is starting to discharge."
    else
        log_success "Battery level is acceptable."
    fi

    # Wait a bit before checking again
    sleep $CHECK_INTERVAL
done
