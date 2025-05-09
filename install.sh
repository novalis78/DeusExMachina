#!/bin/bash
#
# DeusExMachina Improved Installation Script
# This script provides a streamlined installation process for DeusExMachina
#

set -e  # Exit on any error

# ASCII art banner
cat << "EOF"
╔╦╗╔═╗╦ ╦╔═╗  ╔═╗═╗ ╦  ╔╦╗╔═╗╔═╗╦ ╦╦╔╗╔╔═╗
 ║║║╣ ║ ║╚═╗  ║╣ ╔╩╦╝  ║║║╠═╣║  ╠═╣║║║║╠═╣
═╩╝╚═╝╚═╝╚═╝  ╚═╝╩ ╚═  ╩ ╩╩ ╩╚═╝╩ ╩╩╝╚╝╩ ╩
EOF
echo "Intelligent Server Guardian - Installation Script"
echo "------------------------------------------------"

# Default installation paths
DEFAULT_INSTALL_DIR="/opt/deus-ex-machina"
DEFAULT_LOG_DIR="/var/log/deus-ex-machina"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR=$(mktemp -d -t deus-XXXXXXXXXX)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored status messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

# Cleanup on exit
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT

# Help message
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help                   Show this help message"
    echo "  -i, --install-dir DIR        Installation directory (default: $DEFAULT_INSTALL_DIR)"
    echo "  -l, --log-dir DIR            Log directory (default: $DEFAULT_LOG_DIR)"
    echo "  -g, --gemini-key KEY         Gemini API key (optional)"
    echo "  -a, --anthropic-key KEY      Anthropic API key (optional)"
    echo "  -o, --openai-key KEY         OpenAI API key (optional)"
    echo "  -y, --yes                    Non-interactive mode, assume yes to all prompts"
    echo "  -n, --no-deps                Skip installing dependencies"
    echo "  -u, --user                   Install in user mode (no root required)"
    echo "  -b, --break-system-packages  Use --break-system-packages with pip"
    echo "  -v, --verbose                Enable verbose output"
    echo ""
    echo "Example:"
    echo "  $0 --install-dir /opt/deus --log-dir /var/log/deus --gemini-key YOUR_API_KEY"
}

# Parse command-line arguments
INSTALL_DIR="$DEFAULT_INSTALL_DIR"
LOG_DIR="$DEFAULT_LOG_DIR"
GEMINI_API_KEY=""
ANTHROPIC_API_KEY=""
OPENAI_API_KEY=""
ASSUME_YES=false
SKIP_DEPS=false
USER_MODE=false
BREAK_SYSTEM_PACKAGES=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -l|--log-dir)
            LOG_DIR="$2"
            shift 2
            ;;
        -g|--gemini-key)
            GEMINI_API_KEY="$2"
            shift 2
            ;;
        -a|--anthropic-key)
            ANTHROPIC_API_KEY="$2"
            shift 2
            ;;
        -o|--openai-key)
            OPENAI_API_KEY="$2"
            shift 2
            ;;
        -y|--yes)
            ASSUME_YES=true
            shift
            ;;
        -n|--no-deps)
            SKIP_DEPS=true
            shift
            ;;
        -u|--user)
            USER_MODE=true
            shift
            ;;
        -b|--break-system-packages)
            BREAK_SYSTEM_PACKAGES=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set appropriate flags based on user mode
if [ "$USER_MODE" = true ]; then
    PIP_USER_ARG="--user"
    MKDIR_USER_ARG=""
    INSTALL_OWNER=$USER
else
    PIP_USER_ARG=""
    MKDIR_USER_ARG="-m 0755"
    INSTALL_OWNER="root:root"
    
    # Check for root permissions if not in user mode
    if [ "$(id -u)" -ne 0 ]; then
        log_error "This script must be run as root when not in user mode"
        log_info "Either run with sudo or use --user flag to install in user mode"
        exit 1
    fi
fi

# Set pip arguments based on break-system-packages flag
if [ "$BREAK_SYSTEM_PACKAGES" = true ]; then
    PIP_BREAK_ARG="--break-system-packages"
else
    PIP_BREAK_ARG=""
fi

# Function to execute commands with optional verbosity
run_cmd() {
    if [ "$VERBOSE" = true ]; then
        echo "+ $@"
        "$@"
    else
        "$@" > /dev/null 2>&1 || { log_error "Command failed: $@"; return 1; }
    fi
}

# Function to ask for confirmation
confirm() {
    if [ "$ASSUME_YES" = true ]; then
        return 0
    fi
    
    local message="$1"
    read -p "$message [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to create necessary directories
create_directories() {
    print_step "Creating necessary directories"
    
    if [ "$USER_MODE" = true ]; then
        # User-mode installation
        mkdir -p "$INSTALL_DIR"/{core,enhanced,plugins,var/db,var/logs/actions}
        mkdir -p "$LOG_DIR"
    else
        # Root-mode installation
        run_cmd mkdir -p "$MKDIR_USER_ARG" "$INSTALL_DIR"/{core,enhanced,plugins,var/db,var/logs/actions}
        run_cmd mkdir -p "$MKDIR_USER_ARG" "$LOG_DIR"
        
        # Set proper permissions
        run_cmd chown -R "$INSTALL_OWNER" "$INSTALL_DIR"
        run_cmd chown -R "$INSTALL_OWNER" "$LOG_DIR"
    fi
    
    log_success "Created directory structure"
}

# Function to check and install system dependencies
install_system_dependencies() {
    if [ "$SKIP_DEPS" = true ]; then
        log_info "Skipping system dependencies installation as requested"
        return 0
    fi
    
    print_step "Checking and installing system dependencies"
    
    # Detect package manager
    if command -v apt-get > /dev/null; then
        PKG_MANAGER="apt-get"
        PKG_UPDATE="apt-get update"
        PKG_INSTALL="apt-get install -y"
        PACKAGES="python3 python3-pip sqlite3 python3-venv"
    elif command -v dnf > /dev/null; then
        PKG_MANAGER="dnf"
        PKG_UPDATE="dnf check-update"
        PKG_INSTALL="dnf install -y"
        PACKAGES="python3 python3-pip sqlite python3-virtualenv"
    elif command -v yum > /dev/null; then
        PKG_MANAGER="yum"
        PKG_UPDATE="yum check-update"
        PKG_INSTALL="yum install -y"
        PACKAGES="python3 python3-pip sqlite python3-virtualenv"
    elif command -v pacman > /dev/null; then
        PKG_MANAGER="pacman"
        PKG_UPDATE="pacman -Sy"
        PKG_INSTALL="pacman -S --noconfirm"
        PACKAGES="python python-pip sqlite python-virtualenv"
    else
        log_warn "Unable to detect package manager. Please install Python 3, pip, and sqlite3 manually."
        return 1
    fi
    
    log_info "Detected package manager: $PKG_MANAGER"
    
    if [ "$USER_MODE" = false ]; then
        log_info "Updating package lists..."
        run_cmd $PKG_UPDATE
        
        log_info "Installing required packages: $PACKAGES"
        run_cmd $PKG_INSTALL $PACKAGES
    else
        log_warn "Skipping system package installation in user mode"
        log_info "Please ensure you have the following packages installed: $PACKAGES"
    fi
    
    log_success "System dependencies installation completed"
}

# Function to install Python dependencies
install_python_dependencies() {
    if [ "$SKIP_DEPS" = true ]; then
        log_info "Skipping Python dependencies installation as requested"
        return 0
    fi
    
    print_step "Installing Python dependencies"
    
    # Create requirements.txt in temp directory
    cat > "$TEMP_DIR/requirements.txt" << EOF
numpy>=1.20.0
pandas>=1.3.0
scikit-learn>=0.24.0
matplotlib>=3.4.0
requests>=2.25.0
google-generativeai>=0.3.0
EOF
    
    log_info "Installing Python packages..."
    run_cmd pip3 install $PIP_USER_ARG $PIP_BREAK_ARG -r "$TEMP_DIR/requirements.txt"
    
    log_success "Python dependencies installation completed"
}

# Function to copy core files
copy_core_files() {
    print_step "Installing core components"
    
    # Copy core components
    log_info "Copying core components..."
    
    # Core directories
    for dir in breath heartbeat state_engine vigilance; do
        log_info "Installing $dir components..."
        if [ -d "$SCRIPT_DIR/core/$dir" ]; then
            cp -r "$SCRIPT_DIR/core/$dir/"* "$INSTALL_DIR/core/$dir/"
            chmod +x "$INSTALL_DIR/core/$dir/"*.sh 2>/dev/null || true
        else
            log_warn "Directory $SCRIPT_DIR/core/$dir not found, skipping"
        fi
    done
    
    # Enhanced components
    log_info "Installing enhanced components..."
    if [ -d "$SCRIPT_DIR/enhanced" ]; then
        cp -r "$SCRIPT_DIR/enhanced/"*.py "$INSTALL_DIR/enhanced/"
    else
        log_warn "Directory $SCRIPT_DIR/enhanced not found, skipping"
    fi
    
    # Plugin components
    log_info "Installing plugins..."
    if [ -d "$SCRIPT_DIR/enhanced/plugins" ]; then
        mkdir -p "$INSTALL_DIR/plugins/backup_restore"
        mkdir -p "$INSTALL_DIR/plugins/network_monitor"
        
        # Copy plugin files if they exist
        if [ -f "$SCRIPT_DIR/enhanced/plugins/backup_restore.py" ]; then
            cp "$SCRIPT_DIR/enhanced/plugins/backup_restore.py" "$INSTALL_DIR/plugins/backup_restore/"
        fi
        
        if [ -f "$SCRIPT_DIR/enhanced/plugins/network_monitor.py" ]; then
            cp "$SCRIPT_DIR/enhanced/plugins/network_monitor.py" "$INSTALL_DIR/plugins/network_monitor/"
        fi
        
        # Create plugin metadata
        cat > "$INSTALL_DIR/plugins/backup_restore/plugin_metadata.json" << EOT
{
    "name": "Backup/Restore Plugin",
    "version": "1.0.0",
    "description": "Provides backup and restore functionality for Deus Ex Machina",
    "author": "DeusExMachina Team",
    "main_module": "backup_restore.py",
    "main_class": "BackupRestorePlugin"
}
EOT

        cat > "$INSTALL_DIR/plugins/network_monitor/plugin_metadata.json" << EOT
{
    "name": "Network Monitor Plugin",
    "version": "1.0.0",
    "description": "Monitors network connections and detects unusual activity",
    "author": "DeusExMachina Team",
    "main_module": "network_monitor.py",
    "main_class": "NetworkMonitorPlugin"
}
EOT
    else
        log_warn "Directory $SCRIPT_DIR/enhanced/plugins not found, skipping"
    fi
    
    # Copy documentation
    log_info "Installing documentation..."
    for doc in README.md DEPLOYMENT_GUIDE.md ENHANCED_README.md DEVELOPMENT.md MONITORING_GUIDE.md; do
        if [ -f "$SCRIPT_DIR/$doc" ]; then
            cp "$SCRIPT_DIR/$doc" "$INSTALL_DIR/"
        fi
    done
    
    log_success "Core components installation completed"
}

# Function to create necessary configuration files
create_config_files() {
    print_step "Creating configuration files"
    
    # Create main config file
    log_info "Creating config.py..."
    cat > "$INSTALL_DIR/enhanced/config.py" << EOT
# Configuration for Deus Ex Machina Enhanced
CONFIG = {
    "install_dir": "$INSTALL_DIR",
    "log_dir": "$LOG_DIR",
    "database_path": "$INSTALL_DIR/var/db/metrics.db",
    "action_log_dir": "$INSTALL_DIR/var/logs/actions",
    "plugins_dir": "$INSTALL_DIR/plugins",
    "db_dir": "$INSTALL_DIR/var/db",
    "metric_retention_days": 90,
    "monitoring_interval_seconds": 300,
    "use_google_ai": True,
    "permission_level": "RESTART",  # Available levels: OBSERVE, RESTART, CLEAN, CONFIGURE, ADMIN
    "enable_self_healing": True,
    "enable_prediction": True,
    "enabled_plugins": ["backup_restore", "network_monitor"],
    "consciousness": {
        "initial_state": "DORMANT",
        "check_interval": 60
    },
    "ai_providers": {
        "default": "google",
        "google": {
            "enabled": True,
            "model": "gemini-pro"
        },
        "anthropic": {
            "enabled": False,
            "model": "claude-3-sonnet-20240229"
        },
        "openai": {
            "enabled": False,
            "model": "gpt-4-turbo"
        }
    },
    "max_permission_level": "RESTART"
}
EOT

    # Create API key config
    log_info "Creating API key configuration..."
    cat > "$INSTALL_DIR/enhanced/gemini_config.py" << EOT
# Google Gemini API configuration
GEMINI_API_KEY = "${GEMINI_API_KEY}"
EOT

    # Create runner script
    log_info "Creating runner script..."
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
    
    # Initialize state.json
    log_info "Initializing state.json..."
    cat > "$LOG_DIR/state.json" << EOT
{
  "state": "normal",
  "last_updated": "$(date -Iseconds)",
  "ttl": 600,
  "reason": "Initial state",
  "metrics": {
    "cpu_load": 0.5,
    "memory_free_mb": 1024,
    "open_ports": 50
  }
}
EOT

    # Initialize heartbeat.json
    log_info "Initializing heartbeat.json..."
    cat > "$LOG_DIR/heartbeat.json" << EOT
{
  "timestamp": "$(date -Iseconds)",
  "metrics": {
    "cpu_load": 0.5,
    "memory_free_mb": 1024,
    "open_ports": 50,
    "disk_usage_root": 45.2,
    "disk_usage_var": 32.7,
    "processes": 152,
    "system_load_1min": 0.8,
    "system_load_5min": 0.6,
    "system_load_15min": 0.4,
    "users_logged_in": 1,
    "network_connections": 32
  }
}
EOT

    # Copy heartbeat.json to heartbeat_prev.json for comparison
    cp "$LOG_DIR/heartbeat.json" "$LOG_DIR/heartbeat_prev.json"
    
    log_success "Configuration files created"
}

# Function to initialize the database
initialize_database() {
    print_step "Initializing database"
    
    python3 - << EOT
import os
import sqlite3

def initialize_database(db_path):
    """Create database tables if they don't exist"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
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
db_path = "$INSTALL_DIR/var/db/metrics.db"
initialize_database(db_path)
EOT
    
    log_success "Database initialized"
}

# Function to set up systemd service
setup_systemd_service() {
    if [ "$USER_MODE" = true ]; then
        log_info "Skipping systemd service setup in user mode"
        return 0
    fi
    
    print_step "Setting up systemd service"
    
    # Create systemd service file
    log_info "Creating systemd service file..."
    cat > "/etc/systemd/system/deus-enhanced.service" << EOT
[Unit]
Description=Deus Ex Machina Enhanced System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/enhanced/integration.py monitor --interval 300
Restart=on-failure
RestartSec=5s
# Environment variables for AI provider API keys
Environment="GEMINI_API_KEY=$GEMINI_API_KEY"
Environment="ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
Environment="OPENAI_API_KEY=$OPENAI_API_KEY"
# Other environment variables
Environment="PYTHONUNBUFFERED=1"
Environment="DEUS_INSTALL_DIR=$INSTALL_DIR"
Environment="DEUS_LOG_DIR=$LOG_DIR"

[Install]
WantedBy=multi-user.target
EOT
    
    # Create log files
    log_info "Creating log files..."
    touch "$LOG_DIR"/{heartbeat,breath,vigilance,state_engine,state_trigger,integration}.log
    touch "$LOG_DIR"/ai_assessment.json
    
    # Set permissions
    chmod 644 "$LOG_DIR"/*.log
    chmod 666 "$LOG_DIR"/{state.json,ai_assessment.json,heartbeat.json,heartbeat_prev.json}
    
    # Reload systemd
    log_info "Reloading systemd daemon..."
    systemctl daemon-reload
    
    # Enable and start service
    if confirm "Do you want to enable and start the DeusExMachina service now?"; then
        log_info "Enabling and starting service..."
        systemctl enable deus-enhanced.service
        systemctl start deus-enhanced.service
        
        # Check service status
        if systemctl is-active --quiet deus-enhanced.service; then
            log_success "Service started successfully"
        else
            log_warn "Service failed to start, check status with: systemctl status deus-enhanced.service"
        fi
    else
        log_info "Service setup completed but not started"
        log_info "You can start it later with: sudo systemctl start deus-enhanced.service"
    fi
    
    log_success "Systemd service setup completed"
}

# Function to verify installation
verify_installation() {
    print_step "Verifying installation"
    
    local errors=0
    
    # Check core directories
    log_info "Checking core directories..."
    for dir in core enhanced plugins var/db var/logs; do
        if [ ! -d "$INSTALL_DIR/$dir" ]; then
            log_error "Missing directory: $INSTALL_DIR/$dir"
            errors=$((errors+1))
        fi
    done
    
    # Check critical files
    log_info "Checking critical files..."
    for file in enhanced/config.py enhanced/integration.py run_enhanced.py; do
        if [ ! -f "$INSTALL_DIR/$file" ]; then
            log_error "Missing file: $INSTALL_DIR/$file"
            errors=$((errors+1))
        fi
    done
    
    # Check log directory
    log_info "Checking log directory..."
    if [ ! -d "$LOG_DIR" ]; then
        log_error "Missing log directory: $LOG_DIR"
        errors=$((errors+1))
    fi
    
    # Check database
    log_info "Checking database..."
    if [ ! -f "$INSTALL_DIR/var/db/metrics.db" ]; then
        log_error "Missing database: $INSTALL_DIR/var/db/metrics.db"
        errors=$((errors+1))
    fi
    
    # Check heartbeat files
    log_info "Checking heartbeat files..."
    if [ ! -f "$LOG_DIR/heartbeat.json" ] || [ ! -f "$LOG_DIR/heartbeat_prev.json" ]; then
        log_error "Missing heartbeat files in $LOG_DIR"
        errors=$((errors+1))
    fi
    
    # Check service if not in user mode
    if [ "$USER_MODE" = false ]; then
        log_info "Checking systemd service..."
        if [ ! -f "/etc/systemd/system/deus-enhanced.service" ]; then
            log_error "Missing systemd service file"
            errors=$((errors+1))
        fi
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "Installation verification passed"
    else
        log_warn "Installation verification found $errors issues"
    fi
}

# Function to run a test
run_test() {
    print_step "Running system test"
    
    if [ -f "$INSTALL_DIR/run_enhanced.py" ]; then
        log_info "Executing test run..."
        python3 "$INSTALL_DIR/run_enhanced.py"
        log_success "Test completed"
    else
        log_error "Test script not found: $INSTALL_DIR/run_enhanced.py"
    fi
}

# Function to show installation summary
show_summary() {
    print_step "Installation Summary"
    
    echo -e "${GREEN}DeusExMachina has been installed successfully.${NC}"
    echo ""
    echo "Installation Directory: $INSTALL_DIR"
    echo "Log Directory: $LOG_DIR"
    echo "Database: $INSTALL_DIR/var/db/metrics.db"
    echo ""
    
    if [ "$USER_MODE" = false ]; then
        echo "Service Status: $(systemctl is-active deus-enhanced.service)"
        echo ""
        echo "To manage the service:"
        echo "  Start: sudo systemctl start deus-enhanced.service"
        echo "  Stop: sudo systemctl stop deus-enhanced.service"
        echo "  Status: sudo systemctl status deus-enhanced.service"
        echo "  View logs: sudo journalctl -u deus-enhanced.service -f"
    else
        echo "To run manually (user mode):"
        echo "  python3 $INSTALL_DIR/run_enhanced.py"
    fi
    
    echo ""
    echo "To view detailed logs:"
    echo "  tail -f $LOG_DIR/integration.log"
    echo ""
    echo "To monitor different consciousness states:"
    echo "  cat $LOG_DIR/state.json"
    echo ""
    
    if [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${YELLOW}NOTE:${NC} No Gemini API key was provided. For AI capabilities,"
        echo "edit $INSTALL_DIR/enhanced/gemini_config.py and set your API key."
    fi
    
    echo ""
    echo -e "${GREEN}Thank you for installing DeusExMachina!${NC}"
}

# Main installation process
main() {
    # Print installation details
    echo "Installation details:"
    echo "  Installation directory: $INSTALL_DIR"
    echo "  Log directory: $LOG_DIR"
    echo "  User mode: $USER_MODE"
    echo "  Skip dependencies: $SKIP_DEPS"
    echo "  Break system packages: $BREAK_SYSTEM_PACKAGES"
    echo ""
    
    # Confirm installation
    if ! confirm "Do you want to proceed with the installation?"; then
        echo "Installation aborted by user"
        exit 0
    fi
    
    # Begin installation
    echo ""
    echo "Starting installation..."
    
    # Create directories
    create_directories
    
    # Install system dependencies
    install_system_dependencies
    
    # Install Python dependencies
    install_python_dependencies
    
    # Copy core files
    copy_core_files
    
    # Create configuration files
    create_config_files
    
    # Initialize database
    initialize_database
    
    # Setup systemd service
    setup_systemd_service
    
    # Verify installation
    verify_installation
    
    # Run test
    run_test
    
    # Show summary
    show_summary
}

# Execute main function
main