# Enhanced Deus Ex Machina

> A self-evolving, AI-augmented server monitoring and self-healing system with multilayered awareness, intelligent memory, and proactive defense capabilities.

## Overview

This enhanced version of Deus Ex Machina builds on the original biologically-inspired architecture, adding powerful new capabilities across all layers. It maintains the elegant metaphor of a living system while significantly expanding functionality to create a truly intelligent guardian for your servers.

![Deus Ex Machina Architecture](header.png)

## Core Enhancements

### I. Persistent Memory (Database Foundation)

The system now features a robust SQLite database that enables:

- **Metric Persistence**: All system metrics are automatically stored and indexed
- **Trend Analysis**: Statistical analysis of historical data to identify patterns
- **Anomaly Detection**: Mathematically sound identification of outliers
- **Event Correlation**: Connections between related system events
- **Automatic Cleanup**: Self-maintaining database with configurable retention policies

### II. Self-Healing Capabilities

Automated remediation capabilities have been added to respond to detected issues:

- **Action Engine**: Secure framework for executing remediation actions
- **Permission Levels**: Tiered security controls for different action types
- **Rollback Support**: Ability to revert changes if needed
- **Audit Logging**: Comprehensive tracking of all automated actions
- **Remediation Library**: Growing set of responses to common issues

### III. Proactive Intelligence

The system can now anticipate issues before they occur:

- **Time-Series Forecasting**: Predictive modeling of resource utilization
- **Pattern Recognition**: Identification of recurring issues and their triggers
- **Scheduled Maintenance**: Intelligent scheduling of maintenance tasks
- **Threat Modeling**: Recognition of suspicious activity patterns
- **Enhanced AI Integration**: More contextual and effective AI analysis

### IV. Modular Expansion

A plugin architecture enables flexible extension of the system's capabilities:

- **Plugin Framework**: Standardized interface for developing extensions
- **Secure Sandbox**: Isolated execution environment for third-party modules
- **Configuration Management**: Centralized configuration for all components
- **Built-in Plugins**: Ready-to-use modules for common tasks
- **Plugin Marketplace**: Ability to share and install community plugins

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Deus Ex Machina                          │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│  ┌─────────────┐   ┌──────┴─────────┐   ┌─────────────┐     │
│  │  Heartbeat  │◄──┤  State Engine  │──►│   Breath    │     │
│  └─────┬───────┘   └──────┬─────────┘   └─────┬───────┘     │
│        │                  │                   │             │
│  Continuous         State Management       Periodic         │
│  Monitoring                                 Integrity       │
└────────┼──────────────────┼───────────────────┼─────────────┘
         │                  │                   │
         ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐    │
│  │   Memory    │◄─►│  Vigilance  │◄─►│    AI Brain     │    │
│  │  (Database) │   │             │   │                 │    │
│  └─────┬───────┘   └─────┬───────┘   └─────────┬───────┘    │
│        │                 │                     │            │
│    Historical        Deep Analysis      Neural Intelligence  │
│      Storage                                                │
└────────┼─────────────────┼─────────────────────┼────────────┘
         │                 │                     │
         ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐    │
│  │ Prediction  │   │   Action    │   │ Plugin System   │    │
│  │   Engine    │   │   Engine    │   │                 │    │
│  └─────┬───────┘   └─────┬───────┘   └─────────┬───────┘    │
│        │                 │                     │            │
│   Forecasting       Self-Healing         Extensibility      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Enhanced Components

### Memory Module (`memory.py`)

The memory system provides a SQLite-based foundation for storing and analyzing system metrics:

```python
# Store current system metrics
memory.store_current_metrics()

# Get history for a specific metric
cpu_history = memory.get_metric_history("cpu_load", days=7)

# Detect anomalies in a metric
anomalies = memory.detect_anomalies("memory_free_mb")

# Get a comprehensive system summary
summary = memory.get_system_summary()
```

### Action Engine (`action_engine.py`)

The action engine provides a framework for executing automated remediation actions:

```python
# Execute an action
result = action_engine.execute_action("restart_service", {"service_name": "nginx"})

# Clean temporary files
result = action_engine.execute_action("clean_temp_files", {"directory": "/tmp"})

# Roll back a previous action
result = action_engine.rollback_action("a1b2c3d4e5f6")
```

### Prediction Engine (`prediction.py`)

The prediction engine enables forecasting future system states and recognizing patterns:

```python
# Forecast CPU load for next 24 hours
forecast = prediction_engine.forecast_metric("cpu_load", hours_ahead=24)

# Detect recurring patterns in a metric
patterns = prediction_engine.detect_patterns("cpu_load")

# Generate an optimized maintenance schedule
schedule = prediction_engine.generate_schedule(forecasts)

# Analyze recurring issues
issues = prediction_engine.analyze_recurring_issues()
```

### Plugin System (`plugin_system.py`)

The plugin system allows for extending the system with modular components:

```python
# Load a plugin
plugin_manager.load_plugin("network_monitor")

# Execute a plugin
result = plugin_manager.execute_plugin("backup_restore", {"action": "backup"})

# Install a new plugin
plugin_manager.install_plugin("/path/to/plugin")

# Configure a plugin
plugin_manager.update_plugin_config("network_monitor", {"scan_interval": 300})
```

### Integration Controller (`integration.py`)

The integration controller ties all components together and provides a unified interface:

```python
# Set up the controller
deus = DeusExMachina()
deus.setup()

# Run a complete integration cycle
results = deus.run_integration_cycle()

# Start continuous monitoring
deus.monitor_continuously(interval_seconds=600)
```

## Enhanced AI Brain

The AI Brain has been significantly improved to:

1. **Work Without Dependencies**: Falls back to local analysis if Google's Generative AI isn't available
2. **Provide More Context**: Includes system information and historical trends in prompts
3. **Return Structured Data**: All assessments include well-defined fields for programmatic use
4. **Connect With Other Components**: Interfaces with the memory system for richer context

## Included Plugins

### Backup/Restore Plugin

Provides automated backup and restore functionality:

- Create backups of critical system files
- Restore from previous backups
- Manage and list available backups

### Network Monitor Plugin

Monitors network connections and identifies suspicious activity:

- Scan for active network connections
- Detect unusual connection patterns
- Track connection history
- Alert on suspicious activity

## Usage

### Setting Up

```bash
# Install the enhanced components
cd /opt/deus-ex-machina
python3 /path/to/integration.py install

# Start the monitor
python3 /path/to/integration.py monitor
```

### Running Analysis

```bash
# Run a system analysis
python3 /path/to/integration.py analyze

# Execute a specific plugin
python3 /path/to/plugin_system.py execute backup_restore backup

# View prediction data
python3 /path/to/prediction.py forecast cpu_load
```

## Development Roadmap

- [x] **Phase 1: Memory System** - Implemented SQLite database for metrics and events
- [x] **Phase 2: Self-Healing** - Created action engine for automated remediation
- [x] **Phase 3: Proactive Intelligence** - Added prediction engine for forecasting and patterns
- [x] **Phase 4: Modular Expansion** - Built plugin system for extensibility
- [ ] **Phase 5: Advanced Learning** - Implement machine learning for enhanced pattern recognition
- [ ] **Phase 6: Inter-System Communication** - Enable communication between multiple instances
- [ ] **Phase 7: Domain-Specific Optimizations** - Specialized modules for different environments

## Security Considerations

The enhanced Deus Ex Machina implements several security measures:

1. **Permission Levels**: Actions are categorized by risk and permission level
2. **Audit Logging**: All actions are logged for accountability and traceability
3. **Sandboxed Plugins**: Third-party plugins run in an isolated environment
4. **Rollback Support**: System changes can be reverted if issues occur
5. **Minimal Dependencies**: Core functionality works with minimal external requirements

## Contributing

Contributions are welcome! The modular architecture makes it easy to extend the system:

- Add new actions to the action engine
- Create new plugins for specialized functionality
- Enhance prediction algorithms
- Improve AI integration

## License

MIT

## Acknowledgments

- Original Deus Ex Machina concept and implementation
- Unix philosophy of building simple, composable tools
- Biological metaphors for system design
- The watcher that only speaks when it must