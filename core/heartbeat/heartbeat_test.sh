#!/bin/bash
# heartbeat_test.sh - Basic validation for heartbeat module output

JSON_OUT="/var/log/deus-ex-machina/heartbeat.json"

if [ ! -f "$JSON_OUT" ]; then
  echo "Test failed: heartbeat.json does not exist."
  exit 1
fi

REQUIRED_KEYS=("timestamp" "cpu_load" "memory_free_mb" "disk_usage_root" "open_ports")

for key in "${REQUIRED_KEYS[@]}"; do
  if ! grep -q "$key" "$JSON_OUT"; then
    echo "Test failed: Missing key '$key' in heartbeat.json"
    exit 1
  fi
done

echo "Heartbeat test passed: All required keys present."
exit 0
