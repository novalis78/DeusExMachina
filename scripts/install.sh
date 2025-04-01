#!/bin/bash
# install.sh - Installation script for Deus Ex Machina
# Creates necessary directories, sets up services, and configures the environment

set -e

INSTALL_DIR="/opt/deus-ex-machina"
CONFIG_DIR="${INSTALL_DIR}/config"
LOG_DIR="/var/log/deus-ex-machina"
SYSTEMD_DIR="/etc/systemd/system"

# Print with color
print_status() {
  echo -e "\e[1;34m[INSTALL]\e[0m $1"
}

print_error() {
  echo -e "\e[1;31m[ERROR]\e[0m $1" >&2
}

print_success() {
  echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  print_error "Please run as root"
  exit 1
fi

# Create directories
print_status "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR" 
mkdir -p "$LOG_DIR"

# Get the source directory (where this script is located)
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Copy files
print_status "Copying files to installation directory..."
cp -r "$SOURCE_DIR/core" "$INSTALL_DIR/"
cp -r "$SOURCE_DIR/config" "$INSTALL_DIR/"

# Create config file if it doesn't exist
if [ ! -f "${CONFIG_DIR}/gemini_config.py" ]; then
  print_status "Creating config file..."
  cat > "${CONFIG_DIR}/gemini_config.py" << EOF
# Gemini API configuration
# Replace with your own API key and DO NOT commit this file

GEMINI_API_KEY = "your-google-api-key-here"
EOF
  print_status "Please edit ${CONFIG_DIR}/gemini_config.py to add your Gemini API key"
fi

# Make scripts executable
print_status "Setting permissions..."
find "$INSTALL_DIR" -name "*.sh" -exec chmod +x {} \;
chmod 600 "${CONFIG_DIR}/gemini_config.py"

# Create systemd service
print_status "Installing systemd service..."
cat > "${SYSTEMD_DIR}/deus-heartbeat.service" << EOF
[Unit]
Description=Deus Ex Machina Heartbeat Module
After=network.target

[Service]
Type=simple
ExecStart=${INSTALL_DIR}/core/heartbeat/heartbeat.sh
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# Set up cron jobs
print_status "Setting up cron jobs..."
(crontab -l 2>/dev/null || true; echo "# Deus Ex Machina jobs
*/2 * * * * /usr/bin/python3 ${INSTALL_DIR}/core/state_engine/state_engine.py >> ${LOG_DIR}/state_engine.log 2>&1
*/2 * * * * /usr/bin/python3 ${INSTALL_DIR}/core/state_engine/state_trigger.py >> ${LOG_DIR}/state_trigger.log 2>&1
") | crontab -

# Reload systemd
print_status "Reloading systemd..."
systemctl daemon-reload

print_success "Installation complete! Services are ready but not started."
print_success "To start the heartbeat service, run: systemctl enable --now deus-heartbeat.service"
print_success "To check status, run: systemctl status deus-heartbeat.service"
print_success "Logs will be available in: ${LOG_DIR}"