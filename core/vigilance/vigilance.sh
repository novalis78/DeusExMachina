#!/bin/bash
# vigilance.sh - Deep anomaly detection and AI escalation trigger
# Part of the Deus Ex Machina project

MERKLE_BASE_DIR="/etc /usr/bin /usr/sbin /home"
MERKLE_STORE="/var/log/deus-ex-machina/merkle_root.hash"
MERKLE_TEMP="/tmp/current_merkle.hash"
AUTH_LOG="/var/log/auth.log"
ALERT_LOG="/var/log/deus-ex-machina/vigilance_alerts.log"

mkdir -p /var/log/deus-ex-machina

# Function to generate a recursive hash of files (Merkle-ish)
generate_merkle_hash() {
  echo "[Vigilance] Generating Merkle-style hash..."
  find $MERKLE_BASE_DIR -type f -exec sha256sum {} + 2>/dev/null | sort | sha256sum | awk '{print $1}' > "$MERKLE_TEMP"
}

# Compare against previous Merkle root
check_integrity() {
  if [ ! -f "$MERKLE_STORE" ]; then
    cp "$MERKLE_TEMP" "$MERKLE_STORE"
    echo "[Vigilance] Initial Merkle root stored."
    return
  fi

  old=$(cat "$MERKLE_STORE")
  new=$(cat "$MERKLE_TEMP")
  if [ "$old" != "$new" ]; then
    echo "[Vigilance] 🔥 SYSTEM INTEGRITY ALERT: Merkle root mismatch!" | tee -a "$ALERT_LOG"
    echo "Old: $old" >> "$ALERT_LOG"
    echo "New: $new" >> "$ALERT_LOG"
    cp "$MERKLE_TEMP" "$MERKLE_STORE"
    # Placeholder: trigger AI investigation or alert system
  else
    echo "[Vigilance] ✅ Merkle root unchanged."
  fi
}

# Analyze auth log for anomalies
scan_auth_logs() {
  echo "[Vigilance] Scanning $AUTH_LOG for suspicious entries..."
  grep -Ei "failed|invalid|root|sudo|unauthorized|break-in" "$AUTH_LOG" | tail -n 20 >> "$ALERT_LOG"
}

# Network anomaly scan
scan_network() {
  echo "[Vigilance] Scanning for unexpected listeners..."
  ss -tulnp | grep -v "127.0.0.1" | grep -v ":22" >> "$ALERT_LOG"
}

# Main
generate_merkle_hash
check_integrity
scan_auth_logs
scan_network

# Placeholder: if $ALERT_LOG exceeds X lines, trigger AI analysis
/usr/bin/python3 /opt/deus-ex-machina/core/vigilance/ai_brain.py
