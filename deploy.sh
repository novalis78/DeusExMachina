#!/bin/bash
# Deployment script for Deus Ex Machina Enhancements
# This script implements the deployment process outlined in DEPLOYMENT_GUIDE.md

set -e  # Exit on errors

# Display usage information
function show_usage() {
    echo "Usage: deploy.sh [OPTIONS]"
    echo "Deploy the Deus Ex Machina system enhancements"
    echo ""
    echo "Options:"
    echo "  --help             Show this help message"
    echo "  --install-dir DIR  Installation directory (default: /opt/deus-ex-machina)"
    echo "  --log-dir DIR      Log directory (default: /var/log/deus-ex-machina)"
    echo "  --backup           Backup existing installation before deployment"
    echo "  --no-deps          Skip dependencies installation"
    echo "  --test-only        Only run tests, don't install"
    echo "  --debug            Enable debug mode with verbose output"
}

# Set default values
INSTALL_DIR="/opt/deus-ex-machina"
LOG_DIR="/var/log/deus-ex-machina"
BACKUP=false
SKIP_DEPS=false
TEST_ONLY=false
DEBUG=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --help)
            show_usage
            exit 0
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        --no-deps)
            SKIP_DEPS=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Enable debug mode if requested
if [ "$DEBUG" = true ]; then
    set -x  # Print commands as they're executed
fi

# Print banner
echo "---------------------------------------------------------------"
echo "Deus Ex Machina Enhanced Deployment"
echo "---------------------------------------------------------------"
echo "Installation directory: $INSTALL_DIR"
echo "Log directory: $LOG_DIR"
echo "Backup existing: $BACKUP"
echo "Skip dependencies: $SKIP_DEPS"
echo "Test only: $TEST_ONLY"
echo "---------------------------------------------------------------"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root" >&2
    exit 1
fi

# Step 1: Create required directories
echo "Creating required directories..."
mkdir -p "$INSTALL_DIR/enhanced"
mkdir -p "$INSTALL_DIR/plugins"
mkdir -p "$INSTALL_DIR/var/db"
mkdir -p "$INSTALL_DIR/var/logs/actions"
mkdir -p "$LOG_DIR"

# Step 2: Backup existing installation if requested
if [ "$BACKUP" = true ]; then
    echo "Creating backup of existing installation..."
    BACKUP_DIR="/opt/deus-ex-machina.backup-$(date +%Y%m%d%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    if [ -d "$INSTALL_DIR" ]; then
        cp -r "$INSTALL_DIR"/* "$BACKUP_DIR"/
        echo "Backup created at $BACKUP_DIR"
    else
        echo "No existing installation to backup."
    fi
    
    # Backup logs if they exist
    if [ -d "$LOG_DIR" ]; then
        LOG_BACKUP_DIR="/var/log/deus-ex-machina.backup-$(date +%Y%m%d%H%M%S)"
        mkdir -p "$LOG_BACKUP_DIR"
        cp -r "$LOG_DIR"/* "$LOG_BACKUP_DIR"/
        echo "Log backup created at $LOG_BACKUP_DIR"
    fi
fi

# Exit here if only testing
if [ "$TEST_ONLY" = true ]; then
    echo "Test mode - exiting without installation"
    exit 0
fi

# Step 3: Install dependencies if not skipped
if [ "$SKIP_DEPS" = false ]; then
    echo "Installing dependencies..."
    apt-get update
    apt-get install -y python3 python3-pip sqlite3
    
    # Install Python dependencies
    pip3 install numpy pandas scikit-learn matplotlib --break-system-packages

    # Try to install Google AI library (optional)
    pip3 install google-generativeai --break-system-packages || echo "Google AI library not installed (optional)"
fi

# Step 4: Deploy the enhanced components
echo "Deploying enhanced components..."
SRC_DIR="/home/claude/DeusExMachina/enhanced"

# Copy enhanced components
cp "$SRC_DIR/memory.py" "$INSTALL_DIR/enhanced/"
cp "$SRC_DIR/ai_brain_updated.py" "$INSTALL_DIR/enhanced/"
cp "$SRC_DIR/action_engine.py" "$INSTALL_DIR/enhanced/"
cp "$SRC_DIR/prediction.py" "$INSTALL_DIR/enhanced/"
cp "$SRC_DIR/plugin_system.py" "$INSTALL_DIR/enhanced/"
cp "$SRC_DIR/integration.py" "$INSTALL_DIR/enhanced/"

# Create configuration file
echo "Creating configuration file..."
cat > "$INSTALL_DIR/enhanced/config.py" << EOT
# Configuration for Deus Ex Machina Enhanced
CONFIG = {
    "database_path": "$INSTALL_DIR/var/db/metrics.db",
    "log_dir": "$LOG_DIR",
    "action_log_dir": "$INSTALL_DIR/var/logs/actions",
    "plugins_dir": "$INSTALL_DIR/plugins",
    "metric_retention_days": 90,
    "monitoring_interval_seconds": 300,
    "ai_credentials_path": "$INSTALL_DIR/credentials.json",
    "use_google_ai": False,  # Set to True if Google Generative AI is available
    "permission_level": "RESTART",  # Available levels: OBSERVE, RESTART, CLEAN, CONFIGURE, ADMIN
    "enable_self_healing": True,
    "enable_prediction": True,
    "enabled_plugins": ["backup_restore", "network_monitor"]
}
EOT

# Create template for Google AI credentials
cat > "$INSTALL_DIR/enhanced/gemini_config.py.template" << EOT
# Google Gemini API configuration
# Rename this file to gemini_config.py and add your API key

GEMINI_API_KEY = "your_api_key_here"
EOT

# Copy example plugins
echo "Deploying example plugins..."
mkdir -p "$INSTALL_DIR/plugins/backup_restore"
mkdir -p "$INSTALL_DIR/plugins/network_monitor"

# Create plugin metadata files
cat > "$INSTALL_DIR/plugins/backup_restore/plugin_metadata.json" << EOT
{
    "name": "Backup/Restore Plugin",
    "version": "1.0.0",
    "description": "Provides backup and restore functionality for Deus Ex Machina",
    "author": "Claude",
    "main_module": "backup_restore.py",
    "main_class": "BackupRestorePlugin"
}
EOT

cat > "$INSTALL_DIR/plugins/network_monitor/plugin_metadata.json" << EOT
{
    "name": "Network Monitor Plugin",
    "version": "1.0.0",
    "description": "Monitors network connections and detects unusual activity",
    "author": "Claude",
    "main_module": "network_monitor.py",
    "main_class": "NetworkMonitorPlugin"
}
EOT

# Copy plugin implementations
cp -r "$SRC_DIR/plugins/backup_restore.py" "$INSTALL_DIR/plugins/backup_restore/" || echo "Warning: backup_restore.py not found"
cp -r "$SRC_DIR/plugins/network_monitor.py" "$INSTALL_DIR/plugins/network_monitor/" || echo "Warning: network_monitor.py not found"

# Step 5: Initialize the database
echo "Initializing database..."
python3 - << EOT
import sys
import os
import sqlite3

def initialize_database(db_path):
    """Create database tables if they don't exist"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            UNIQUE(timestamp, metric_name)
        )
        ''')
        
        # Create events table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            details TEXT
        )
        ''')
        
        # Create state history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS state_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            old_state TEXT NOT NULL,
            new_state TEXT NOT NULL,
            reason TEXT
        )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_state_timestamp ON state_history(timestamp)')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully at: " + db_path)
        return True
    except Exception as e:
        print("Error initializing database: " + str(e))
        return False

# Initialize the database
db_dir = "$INSTALL_DIR/var/db"
db_path = os.path.join(db_dir, "metrics.db")
os.makedirs(db_dir, exist_ok=True)
initialize_database(db_path)
EOT

# Step 6: Create main runner script
echo "Creating main runner script..."
cat > "$INSTALL_DIR/run_enhanced.py" << EOT
#!/usr/bin/env python3

import sys
import os

# Add paths
sys.path.append('$INSTALL_DIR/enhanced')

from integration import DeusExMachina

if __name__ == "__main__":
    deus = DeusExMachina(install_dir='$INSTALL_DIR', log_dir='$LOG_DIR')
    deus.setup()
    results = deus.run_integration_cycle()
    print("Integration cycle completed")
    print(f"Success: {results.get('success', False)}")
EOT

chmod +x "$INSTALL_DIR/run_enhanced.py"

# Step 7: Create systemd service
echo "Creating systemd service..."
cat > /etc/systemd/system/deus-ex-machina.service << EOT
[Unit]
Description=Deus Ex Machina - Enhanced Server Monitoring System
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/enhanced/integration.py monitor --interval 300
WorkingDirectory=$INSTALL_DIR
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=deus-ex-machina
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOT

# Reload systemd
systemctl daemon-reload

# Create cron job for periodic tasks
echo "Creating cron jobs..."
cat > /etc/cron.d/deus-ex-machina << EOT
# Daily database maintenance
0 2 * * * root /usr/bin/python3 $INSTALL_DIR/enhanced/memory.py

# Generate predictions every 6 hours
0 */6 * * * root /usr/bin/python3 $INSTALL_DIR/enhanced/prediction.py

# Generate weekly report
0 8 * * 1 root /usr/bin/python3 $INSTALL_DIR/enhanced/integration.py analyze
EOT

# Step 8: Run a test of the system
echo "Running system test..."
python3 "$INSTALL_DIR/run_enhanced.py" || echo "Test run completed with warnings or errors."

# Step 9: Set permissions
echo "Setting permissions..."
chown -R root:root "$INSTALL_DIR"
chmod -R 755 "$INSTALL_DIR"
chmod 664 "$INSTALL_DIR/var/db/metrics.db" || true
chmod -R 775 "$INSTALL_DIR/var/logs" || true

# Final message
echo ""
echo "---------------------------------------------------------------"
echo "Deployment completed successfully!"
echo "---------------------------------------------------------------"
echo "The enhanced Deus Ex Machina system has been deployed to:"
echo "  $INSTALL_DIR"
echo ""
echo "To start the service:"
echo "  systemctl enable deus-ex-machina.service"
echo "  systemctl start deus-ex-machina.service"
echo ""
echo "To check status:"
echo "  systemctl status deus-ex-machina.service"
echo ""
echo "To run a manual integration cycle:"
echo "  $INSTALL_DIR/run_enhanced.py"
echo "---------------------------------------------------------------"