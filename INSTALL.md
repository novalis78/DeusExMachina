# DeusExMachina Installation Guide

This guide provides comprehensive instructions for installing the DeusExMachina system on your server.

## Quick Start

For most users, the simplest way to install DeusExMachina is using our installation script:

```bash
# Clone the repository
git clone https://github.com/novalis78/DeusExMachina.git
cd DeusExMachina

# Make the installer executable
chmod +x install.sh

# Run the installer (requires sudo)
sudo ./install.sh
```

The installer will guide you through the process and set up everything for you.

## Installation Options

The installer supports several options to customize your installation:

```bash
Usage: ./install.sh [OPTIONS]

Options:
  -h, --help                   Show this help message
  -i, --install-dir DIR        Installation directory (default: /opt/deus-ex-machina)
  -l, --log-dir DIR            Log directory (default: /var/log/deus-ex-machina)
  -g, --gemini-key KEY         Gemini API key (optional)
  -a, --anthropic-key KEY      Anthropic API key (optional)
  -o, --openai-key KEY         OpenAI API key (optional)
  -y, --yes                    Non-interactive mode, assume yes to all prompts
  -n, --no-deps                Skip installing dependencies
  -u, --user                   Install in user mode (no root required)
  -b, --break-system-packages  Use --break-system-packages with pip
  -v, --verbose                Enable verbose output
```

### Examples

#### Installing with an API key:
```bash
sudo ./install.sh --gemini-key YOUR_GEMINI_API_KEY
```

#### Installing to a custom location:
```bash
sudo ./install.sh --install-dir /path/to/custom/location --log-dir /path/to/logs
```

#### User-mode installation (no root required):
```bash
./install.sh --user --install-dir ~/deus-ex-machina
```

## Manual Installation

If you prefer to install the system manually or need more control over the process, follow these steps:

### 1. System Requirements

- Python 3.8 or higher
- pip (Python package manager)
- SQLite3 database
- System permissions to create service files (for system-wide installation)

### 2. Install Dependencies

Install system packages:

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y python3 python3-pip sqlite3

# RHEL/CentOS/Fedora
sudo dnf install -y python3 python3-pip sqlite

# Arch Linux
sudo pacman -S python python-pip sqlite
```

Install Python packages:

```bash
pip3 install -r requirements.txt
```

If you encounter issues with system-managed environments, you can use the `--break-system-packages` flag:

```bash
pip3 install -r requirements.txt --break-system-packages
```

### 3. Create Directory Structure

```bash
# Create installation directories
sudo mkdir -p /opt/deus-ex-machina/{core,enhanced,plugins,var/db,var/logs/actions}
sudo mkdir -p /var/log/deus-ex-machina

# Set permissions
sudo chown -R root:root /opt/deus-ex-machina
sudo chown -R root:root /var/log/deus-ex-machina
```

### 4. Copy Core Files

```bash
# Copy core components
sudo cp -r core/* /opt/deus-ex-machina/core/
sudo cp -r enhanced/* /opt/deus-ex-machina/enhanced/

# Make scripts executable
sudo chmod +x /opt/deus-ex-machina/core/**/*.sh
```

### 5. Configure the System

Create configuration file:

```bash
sudo nano /opt/deus-ex-machina/enhanced/config.py
```

Add your API key:

```bash
sudo nano /opt/deus-ex-machina/enhanced/gemini_config.py
```

### 6. Create System Service

```bash
sudo nano /etc/systemd/system/deus-enhanced.service
```

Add the following content:

```ini
[Unit]
Description=Deus Ex Machina Enhanced System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/deus-ex-machina
ExecStart=/usr/bin/python3 /opt/deus-ex-machina/enhanced/integration.py monitor --interval 300
Restart=on-failure
RestartSec=5s
# Environment variables for AI provider API keys
Environment="GEMINI_API_KEY=your_key_here"
Environment="PYTHONUNBUFFERED=1"
Environment="DEUS_INSTALL_DIR=/opt/deus-ex-machina"
Environment="DEUS_LOG_DIR=/var/log/deus-ex-machina"

[Install]
WantedBy=multi-user.target
```

Activate the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable deus-enhanced.service
sudo systemctl start deus-enhanced.service
```

## Post-Installation

### Verify Installation

```bash
# Check service status
systemctl status deus-enhanced.service

# View logs
tail -f /var/log/deus-ex-machina/integration.log
```

### Test the System

```bash
# Run a test cycle
python3 /opt/deus-ex-machina/run_enhanced.py
```

## Troubleshooting

### Common Issues

#### 1. Service fails to start

Check the logs for errors:

```bash
journalctl -u deus-enhanced.service -n 50
```

#### 2. Python dependency issues

If you encounter problems with Python dependencies, try using a virtual environment:

```bash
python3 -m venv /opt/deus-ex-machina/venv
source /opt/deus-ex-machina/venv/bin/activate
pip install -r requirements.txt
```

Then update the service file to use the virtual environment Python:

```bash
ExecStart=/opt/deus-ex-machina/venv/bin/python /opt/deus-ex-machina/enhanced/integration.py monitor --interval 300
```

#### 3. Path issues

Ensure all paths in the configuration match your actual installation:

```bash
grep -r "/opt/deus-ex-machina" /opt/deus-ex-machina/enhanced/
```

#### 4. Permission problems

Make sure all directories and files have correct permissions:

```bash
sudo chown -R root:root /opt/deus-ex-machina
sudo chown -R root:root /var/log/deus-ex-machina
sudo chmod -R 755 /opt/deus-ex-machina
sudo chmod 664 /var/log/deus-ex-machina/*.log
sudo chmod 664 /var/log/deus-ex-machina/*.json
```

### Getting Help

If you encounter issues not covered here, please:

1. Review the detailed logs in `/var/log/deus-ex-machina/`
2. Check the GitHub repository for known issues
3. Open a new issue on GitHub with detailed information about your problem

## Upgrading

To upgrade to a newer version:

1. Stop the service: `sudo systemctl stop deus-enhanced.service`
2. Backup your installation: `sudo cp -r /opt/deus-ex-machina /opt/deus-ex-machina.bak`
3. Follow the installation instructions for the new version
4. Restore your configuration if needed
5. Start the service: `sudo systemctl start deus-enhanced.service`

## Uninstallation

To remove DeusExMachina from your system:

```bash
# Stop and disable the service
sudo systemctl stop deus-enhanced.service
sudo systemctl disable deus-enhanced.service

# Remove service file
sudo rm /etc/systemd/system/deus-enhanced.service
sudo systemctl daemon-reload

# Remove installation and log directories
sudo rm -rf /opt/deus-ex-machina
sudo rm -rf /var/log/deus-ex-machina
```