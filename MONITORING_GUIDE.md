# Deus Ex Machina Monitoring Guide

This guide explains how to monitor your Deus Ex Machina system in action, understand its output, and interpret its behavior.

## Viewing System Logs

The enhanced Deus Ex Machina system logs all its activities through systemd. To follow these logs in real-time:

```bash
# View complete logs
journalctl -u deus-enhanced.service

# Follow logs in real-time
journalctl -u deus-enhanced.service -f

# Show only the most recent logs
journalctl -u deus-enhanced.service -n 50
```

Additionally, detailed logs are stored in the standard system log directory:

```bash
/var/log/deus-ex-machina/enhanced.log
```

This follows Linux filesystem standards and integrates with the existing Deus Ex Machina logs:

```bash
# View the main log file
cat /var/log/deus-ex-machina/enhanced.log

# Follow the log in real-time
tail -f /var/log/deus-ex-machina/enhanced.log

# View all logs in the directory
ls -la /var/log/deus-ex-machina/
```

**Note:** The enhanced system's logs will appear alongside the existing Deus Ex Machina component logs (heartbeat.log, breath.log, state_engine.log, etc.).

## Monitoring Existing Components

The original Deus Ex Machina system maintains several key status files that provide valuable information about the system:

### Heartbeat Monitoring

```bash
# View current heartbeat metrics
cat /var/log/deus-ex-machina/heartbeat.json
```

Example output:
```json
{
  "timestamp": "2025-04-29 14:08:06",
  "cpu_load": "0.35",
  "memory_free_mb": "995",
  "disk_usage_root": "18",
  "open_ports": 12,
  "uptime": "up 13 weeks, 6 days, 23 hours, 27 minutes",
  "total_processes": 167
}
```

### System State

```bash
# View current system state
cat /var/log/deus-ex-machina/state.json
```

Example output:
```json
{
  "state": "normal",
  "last_transition": "2025-04-29T11:08:01.595039",
  "ttl_seconds": 600
}
```

The enhanced system integrates with these existing components, using their data to inform consciousness transitions.

## Understanding Consciousness States

Deus Ex Machina operates based on a biological consciousness model with five distinct states:

1. **DORMANT**: Minimal functionality, conserving resources during periods of inactivity
2. **DROWSY**: Light monitoring, performing basic checks with local AI only
3. **AWARE**: Standard operational state, regular monitoring with normal analysis
4. **ALERT**: Enhanced monitoring when issues are detected, more intensive analysis
5. **FULLY_AWAKE**: Maximum awareness during critical situations, comprehensive analysis and actions

Watch for state transitions in the logs:
```
Consciousness state changed: AWARE -> ALERT (Detected high CPU usage)
```

## What to Expect During Normal Operation

During normal operation, you'll see these typical log patterns:

1. **Regular State Checks**:
   ```
   consciousness - INFO - Running aware state analysis
   ```

2. **AI Provider Selection**:
   ```
   ai_provider_manager - INFO - Attempting analysis with provider: google_ai
   ai_provider_manager - INFO - Analysis successful with provider: google_ai
   ```

3. **System Health Reports**:
   ```
   deus - INFO - Regular analysis result: System appears to be healthy
   ```

4. **Action Execution** (when needed):
   ```
   action_grammar - INFO - Executing action sequence: system_check
   action.check_disk_space - INFO - Executing command: df -h
   ```

## Monitoring Database Growth

The system stores historical data in an SQLite database. Monitor its size:

```bash
# Check database size
ls -lh /home/DeusExMachina/var/db/metrics.db
```

The database is configured to maintain a maximum size (default: 100MB) and retain data for a set period (default: 30 days).

## Common Indicators of Problems

Watch for these warning signs:

1. **Failed Provider Initialization**:
   ```
   ai_provider.google_ai - WARNING - No API key configured for Google AI
   ```
   
2. **Failed Actions**:
   ```
   action_sequence.critical_investigation - WARNING - Action find_large_files failed
   ```
   
3. **Detected System Issues**:
   ```
   deus - INFO - Issues detected: ['High CPU usage detected', 'Critical disk usage on /']
   ```

## Checking System Status

To check if the service is running properly:

```bash
# Check service status
systemctl status deus-enhanced.service

# See if the process is running
ps aux | grep deus
```

## Interpreting AI Analysis Results

The AI analysis produces structured information about system health:

1. **Summary**: Overall system state assessment
2. **Issues**: Specific problems detected
3. **Anomalies**: Unusual patterns or outliers
4. **Recommendations**: Suggested actions to address issues
5. **Severity**: Problem severity (LOW, MEDIUM, HIGH, CRITICAL)

Example log entry:
```
Enhanced analysis result: Found 2 issue(s) and 0 anomaly/anomalies
Issues detected: ['High CPU usage detected', 'Error detected in ssh']
Recommendations: ['Investigate processes causing high CPU', 'Review system logs for detailed error information']
```

## Performance Impact

Deus Ex Machina is designed to have minimal impact on your system:

- **DORMANT/DROWSY states**: Negligible resource usage
- **AWARE state**: Low resource usage (typically <1% CPU, ~50MB RAM)
- **ALERT/FULLY_AWAKE states**: Moderate resource usage during analysis

The system automatically transitions to lower consciousness states when resource usage needs to be minimized.

## Troubleshooting Common Issues

1. **Service won't start**:
   - Check configuration file for errors
   - Verify API keys are properly set
   - Ensure python modules are installed

2. **AI providers not available**:
   - Verify API keys in environment variables
   - Check internet connectivity for cloud AI providers
   - Make sure the Google GenerativeAI module is installed

3. **Actions failing**:
   - Check permission levels in config.py
   - Verify the system has necessary permissions

4. **Log spam from "No API key configured" warnings**:
   - Either provide API keys or disable unused providers in config.py

## Restarting the Service

If you need to restart the service after configuration changes:

```bash
sudo systemctl restart deus-enhanced.service
```

To verify the service started correctly:

```bash
systemctl status deus-enhanced.service
```