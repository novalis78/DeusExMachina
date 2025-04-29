# Deployment Guide for Deus Ex Machina Enhancements

This guide provides step-by-step instructions for deploying the enhanced components to the existing Deus Ex Machina system.

## Prerequisites

- Python 3.8+ installed
- SQLite3 available
- Access to the existing Deus Ex Machina installation
- Root or sudo access for service configuration

## Step 1: Backup the Existing System

```bash
# Create a backup of the current Deus Ex Machina installation
sudo cp -r /opt/deus-ex-machina/ /opt/deus-ex-machina.backup-$(date +%Y%m%d)

# Create a backup of any existing logs
sudo cp -r /var/log/deus-ex-machina/ /var/log/deus-ex-machina.backup-$(date +%Y%m%d)
```

## Step 2: Install Dependencies

```bash
# Install required Python packages
sudo pip3 install numpy pandas scikit-learn matplotlib sqlite3 watchdog requests

# For optional Google AI dependency (used when available):
# sudo pip3 install google-generativeai
```

## Step 3: Prepare Directory Structure

```bash
# Create enhanced directories
sudo mkdir -p /opt/deus-ex-machina/enhanced
sudo mkdir -p /opt/deus-ex-machina/plugins
sudo mkdir -p /opt/deus-ex-machina/var/db
sudo mkdir -p /opt/deus-ex-machina/var/logs/actions
```

## Step 4: Deploy Enhanced Components

```bash
# Copy enhanced components to appropriate locations
sudo cp /home/DeusExMachina/enhanced/ai_brain_updated.py /opt/deus-ex-machina/enhanced/
sudo cp /home/DeusExMachina/enhanced/memory.py /opt/deus-ex-machina/enhanced/
sudo cp /home/DeusExMachina/enhanced/action_engine.py /opt/deus-ex-machina/enhanced/
sudo cp /home/DeusExMachina/enhanced/prediction.py /opt/deus-ex-machina/enhanced/
sudo cp /home/DeusExMachina/enhanced/plugin_system.py /opt/deus-ex-machina/enhanced/
sudo cp /home/DeusExMachina/enhanced/integration.py /opt/deus-ex-machina/enhanced/

# Copy example plugins
sudo cp -r /home/DeusExMachina/enhanced/plugins/* /opt/deus-ex-machina/plugins/

# Copy documentation
sudo cp /home/DeusExMachina/ENHANCED_README.md /opt/deus-ex-machina/
sudo cp /home/DeusExMachina/HANDOVER.md /opt/deus-ex-machina/
```

## Step 5: Initialize the Database

```bash
# Create SQLite database for metrics storage
sudo python3 -c "
import sys
sys.path.append('/opt/deus-ex-machina/enhanced')
import memory
memory.initialize_database('/opt/deus-ex-machina/var/db/metrics.db')
"
```

## Step 6: Update System Configuration

```bash
# Create configuration file for enhanced components
sudo tee /opt/deus-ex-machina/enhanced/config.py > /dev/null << EOT
CONFIG = {
    "database_path": "/opt/deus-ex-machina/var/db/metrics.db",
    "log_dir": "/opt/deus-ex-machina/var/logs",
    "action_log_dir": "/opt/deus-ex-machina/var/logs/actions",
    "plugins_dir": "/opt/deus-ex-machina/plugins",
    "metric_retention_days": 90,
    "monitoring_interval_seconds": 300,
    "ai_credentials_path": "/opt/deus-ex-machina/credentials.json",
    "use_google_ai": False,  # Set to True if Google Generative AI is available
    "permission_level": "RESTART",  # Available levels: OBSERVE, RESTART, CLEAN, CONFIGURE, ADMIN
    "enable_self_healing": True,
    "enable_prediction": True,
    "enabled_plugins": ["backup_restore", "network_monitor"]
}
EOT
```

## Step 7: Create Integration Entry Point

```bash
# Create main runner script
sudo tee /opt/deus-ex-machina/run_enhanced.py > /dev/null << EOT
#!/usr/bin/env python3

import sys
sys.path.append('/opt/deus-ex-machina/enhanced')

from integration import DeusExMachina

if __name__ == "__main__":
    deus = DeusExMachina()
    deus.setup()
    deus.run_integration_cycle()
EOT

# Make it executable
sudo chmod +x /opt/deus-ex-machina/run_enhanced.py
```

## Step 8: Set Up Systemd Service

```bash
# Create systemd service file for continuous monitoring
sudo tee /etc/systemd/system/deus-ex-machina.service > /dev/null << EOT
[Unit]
Description=Deus Ex Machina - Enhanced Server Monitoring System
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/deus-ex-machina/enhanced/integration.py --daemon
WorkingDirectory=/opt/deus-ex-machina
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

# Reload systemd configuration
sudo systemctl daemon-reload

# Enable service to start at boot
sudo systemctl enable deus-ex-machina.service
```

## Step 9: Set Up Periodic Tasks

```bash
# Create cron job for database maintenance and prediction
sudo tee /etc/cron.d/deus-ex-machina > /dev/null << EOT
# Daily database maintenance
0 2 * * * root /usr/bin/python3 /opt/deus-ex-machina/enhanced/memory.py --maintenance

# Generate predictions every 6 hours
0 */6 * * * root /usr/bin/python3 /opt/deus-ex-machina/enhanced/prediction.py --forecast

# Generate weekly report
0 8 * * 1 root /usr/bin/python3 /opt/deus-ex-machina/enhanced/integration.py --report
EOT
```

## Step 10: Deploy Web UI (Optional)

If you want to add a web interface to monitor the system:

```bash
# Install Flask for web interface
sudo pip3 install flask flask-cors

# Deploy web interface
sudo mkdir -p /opt/deus-ex-machina/webui
sudo cp -r /home/DeusExMachina/enhanced/webui/* /opt/deus-ex-machina/webui/

# Create web service
sudo tee /etc/systemd/system/deus-ex-machina-web.service > /dev/null << EOT
[Unit]
Description=Deus Ex Machina Web Interface
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/deus-ex-machina/webui/app.py
WorkingDirectory=/opt/deus-ex-machina/webui
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=deus-ex-machina-web
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
EOT

# Reload systemd and enable web service
sudo systemctl daemon-reload
sudo systemctl enable deus-ex-machina-web.service
```

## Step 11: Test the Deployment

```bash
# Run a manual test of the enhanced system
sudo python3 /opt/deus-ex-machina/run_enhanced.py --test

# Check for errors in logs
sudo tail -f /opt/deus-ex-machina/var/logs/deus.log
```

## Step 12: Start the Service

```bash
# Start the main service
sudo systemctl start deus-ex-machina.service

# Start web UI if installed
sudo systemctl start deus-ex-machina-web.service
```

## Step 13: Verify Installation

```bash
# Check main service status
sudo systemctl status deus-ex-machina.service

# Test the database
sudo python3 -c "
import sys
sys.path.append('/opt/deus-ex-machina/enhanced')
import memory
print(memory.test_connection())
"

# Test the AI brain
sudo python3 -c "
import sys
sys.path.append('/opt/deus-ex-machina/enhanced')
import ai_brain_updated
print(ai_brain_updated.test_analysis())
"
```

## Troubleshooting

If you encounter issues during deployment:

### Database Issues
```bash
# Check database integrity
sudo sqlite3 /opt/deus-ex-machina/var/db/metrics.db 'PRAGMA integrity_check;'

# Reset database if needed
sudo rm /opt/deus-ex-machina/var/db/metrics.db
sudo python3 -c "
import sys
sys.path.append('/opt/deus-ex-machina/enhanced')
import memory
memory.initialize_database('/opt/deus-ex-machina/var/db/metrics.db')
"
```

### Service Issues
```bash
# Check detailed service logs
sudo journalctl -u deus-ex-machina.service -n 50

# Manually run the service for debugging
sudo python3 /opt/deus-ex-machina/enhanced/integration.py --debug
```

### Permission Issues
```bash
# Ensure proper ownership
sudo chown -R root:root /opt/deus-ex-machina
sudo chmod -R 755 /opt/deus-ex-machina

# Ensure database directory is writable
sudo chmod 775 /opt/deus-ex-machina/var/db
sudo chmod 664 /opt/deus-ex-machina/var/db/metrics.db
```

## Rollback Procedure

If you need to roll back to the original system:

```bash
# Stop enhanced services
sudo systemctl stop deus-ex-machina.service
sudo systemctl stop deus-ex-machina-web.service 2>/dev/null || true

# Disable services
sudo systemctl disable deus-ex-machina.service
sudo systemctl disable deus-ex-machina-web.service 2>/dev/null || true

# Restore from backup
sudo rm -rf /opt/deus-ex-machina
sudo cp -r /opt/deus-ex-machina.backup-YYYYMMDD /opt/deus-ex-machina

# Restart original service (if applicable)
sudo systemctl start deus-original.service || true
```

## Maintenance

### Regular Maintenance Tasks

1. **Database Cleanup**: The system automatically purges old metrics data after the retention period (default: 90 days). To manually clean up:
   ```bash
   sudo python3 /opt/deus-ex-machina/enhanced/memory.py --cleanup
   ```

2. **Log Rotation**: Logs are automatically rotated. To manually rotate:
   ```bash
   sudo logrotate -f /etc/logrotate.d/deus-ex-machina
   ```

3. **Plugin Updates**: To update plugins:
   ```bash
   sudo python3 /opt/deus-ex-machina/enhanced/plugin_system.py --update
   ```

### Monitoring

1. **System Status**:
   ```bash
   sudo python3 /opt/deus-ex-machina/enhanced/integration.py --status
   ```

2. **Generate Reports**:
   ```bash
   sudo python3 /opt/deus-ex-machina/enhanced/integration.py --report
   ```

## Security Considerations

1. **API Keys**: If using Google Generative AI, store API keys securely in `/opt/deus-ex-machina/credentials.json`

2. **Permissions**: The system requires root access for some monitoring tasks. Use the least privilege level needed in the configuration.

3. **Plugin Sandbox**: All plugins run in a restricted sandbox. Be cautious when installing third-party plugins.

## Conclusion

The enhanced Deus Ex Machina system should now be fully deployed and operational. The system will automatically collect metrics, store them in the database, analyze trends, and take remedial actions when necessary.

For any questions or issues, refer to the ENHANCED_README.md and HANDOVER.md documents or contact the system administrator.