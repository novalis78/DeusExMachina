#!/bin/bash
# breath.sh - Integrity scanning and configuration state snapshot
# Part of the Deus Ex Machina project

SCAN_PATHS=(
  "/etc/passwd"
  "/etc/ssh/sshd_config"
  "/etc/fstab"
  "/etc/crontab"
)

HASH_STORE="/var/log/deus-ex-machina/breath_hashes.json"
TEMP_HASHES="/tmp/current_breath_hashes.json"
SERVICE_STATUS="/var/log/deus-ex-machina/service_status.log"
CRON_SNAPSHOT="/var/log/deus-ex-machina/cron_snapshot.txt"

mkdir -p /var/log/deus-ex-machina

# Calculate file hashes
calculate_hashes() {
  echo "{" > "$TEMP_HASHES"
  for file in "${SCAN_PATHS[@]}"; do
    if [ -f "$file" ]; then
      hash=$(sha256sum "$file" | awk '{print $1}')
      echo "  \"$file\": \"$hash\"," >> "$TEMP_HASHES"
    fi
  done
  sed -i '$ s/,$//' "$TEMP_HASHES"
  echo "}" >> "$TEMP_HASHES"
}

# Compare with previous
compare_hashes() {
  if [ ! -f "$HASH_STORE" ]; then
    cp "$TEMP_HASHES" "$HASH_STORE"
    echo "[Breath] Initial hash state saved."
    return
  fi

  changes=$(diff "$HASH_STORE" "$TEMP_HASHES")
  if [ -n "$changes" ]; then
    echo "[Breath] 🔍 Change detected in configuration files!"
    echo "$changes" > /var/log/deus-ex-machina/breath_diff.log
    cp "$TEMP_HASHES" "$HASH_STORE"
  else
    echo "[Breath] ✅ No changes detected."
  fi
}

# Check failed systemd services
check_services() {
  systemctl list-units --state=failed > "$SERVICE_STATUS"
  echo "[Breath] Logged failed services to $SERVICE_STATUS"
}

# Snapshot cron jobs
snapshot_cron() {
  echo "[Breath] Capturing cron jobs..." > "$CRON_SNAPSHOT"
  for user in $(cut -f1 -d: /etc/passwd); do
    crontab -l -u "$user" >> "$CRON_SNAPSHOT" 2>/dev/null
  done
  echo "[Breath] Cron snapshot saved."
}

# Main
calculate_hashes
compare_hashes
check_services
snapshot_cron
