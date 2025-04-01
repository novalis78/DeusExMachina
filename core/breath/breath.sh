#!/bin/bash
# breath.sh - Integrity scanning and configuration state snapshot
# Part of the Deus Ex Machina project

# Import configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source bash configuration
if [ -f "$PROJECT_ROOT/scripts/bash_config.sh" ]; then
    source "$PROJECT_ROOT/scripts/bash_config.sh"
else
    # Default configuration if config file doesn't exist
    SCAN_PATHS=(
      "/etc/passwd"
      "/etc/ssh/sshd_config"
      "/etc/fstab"
      "/etc/crontab"
    )
    LOG_DIR="/var/log/deus-ex-machina"
    HASH_STORE="$LOG_DIR/breath_hashes.json"
    TEMP_HASHES="/tmp/current_breath_hashes.json"
    SERVICE_STATUS="$LOG_DIR/service_status.log"
    CRON_SNAPSHOT="$LOG_DIR/cron_snapshot.txt"
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

log_message() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] [Breath] $message" >> "$LOG_DIR/breath.log"
    echo "[Breath] $message"
}

# Calculate file hashes with error handling
calculate_hashes() {
    log_message "INFO" "Calculating file hashes..."
    echo "{" > "$TEMP_HASHES"
    local file_count=0
    
    for file in "${SCAN_PATHS[@]}"; do
        if [ -f "$file" ]; then
            # Check if file is readable
            if [ -r "$file" ]; then
                hash=$(sha256sum "$file" 2>/dev/null | awk '{print $1}')
                if [ -n "$hash" ]; then
                    echo "  \"$file\": \"$hash\"," >> "$TEMP_HASHES"
                    ((file_count++))
                else
                    log_message "WARNING" "Failed to hash $file"
                fi
            else
                log_message "WARNING" "File $file is not readable"
            fi
        else
            log_message "WARNING" "File $file does not exist"
        fi
    done
    
    # Remove trailing comma and close JSON
    sed -i '$ s/,$//' "$TEMP_HASHES"
    echo "}" >> "$TEMP_HASHES"
    log_message "INFO" "Completed hashing $file_count files"
}

# Compare with previous
compare_hashes() {
    if [ ! -f "$HASH_STORE" ]; then
        cp "$TEMP_HASHES" "$HASH_STORE"
        log_message "INFO" "Initial hash state saved."
        return
    fi

    if ! changes=$(diff "$HASH_STORE" "$TEMP_HASHES" 2>/dev/null); then
        log_message "ERROR" "Failed to compare hash files"
        return
    fi
    
    if [ -n "$changes" ]; then
        log_message "ALERT" "🔍 Change detected in configuration files!"
        echo "$changes" > "$LOG_DIR/breath_diff.log"
        cp "$TEMP_HASHES" "$HASH_STORE"
    else
        log_message "INFO" "✅ No changes detected in configuration files."
    fi
}

# Check failed systemd services
check_services() {
    log_message "INFO" "Checking systemd services..."
    if ! systemctl list-units --state=failed > "$SERVICE_STATUS" 2>/dev/null; then
        log_message "ERROR" "Failed to check systemd services"
        return
    fi
    
    failed_count=$(grep -c "failed" "$SERVICE_STATUS" 2>/dev/null || echo "0")
    if [ "$failed_count" -gt "0" ]; then
        log_message "WARNING" "Found $failed_count failed services"
    else
        log_message "INFO" "No failed services detected"
    fi
}

# Snapshot cron jobs with proper error handling
snapshot_cron() {
    log_message "INFO" "Capturing cron jobs..."
    echo "[Breath] Cron snapshot $(date)" > "$CRON_SNAPSHOT"
    
    local error_count=0
    local success_count=0
    
    for user in $(cut -f1 -d: /etc/passwd 2>/dev/null); do
        if crontab -l -u "$user" >> "$CRON_SNAPSHOT" 2>/dev/null; then
            ((success_count++))
        else
            # Only count real errors, not "no crontab for user"
            if [ $? -ne 1 ]; then
                ((error_count++))
            fi
        fi
    done
    
    log_message "INFO" "Cron snapshot captured for $success_count users (errors: $error_count)"
}

# Main function with timing
main() {
    start_time=$(date +%s)
    log_message "INFO" "Breath module starting"
    
    calculate_hashes
    compare_hashes
    check_services
    snapshot_cron
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    log_message "INFO" "Breath module completed in $duration seconds"
}

# Run main function
main