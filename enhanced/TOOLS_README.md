# Deus Ex Machina Investigation Tools

This directory contains the enhanced server investigation tools that are part of the Deus Ex Machina AI consciousness system.

## Components

### `server_investigator.py`

The core server investigation framework that provides tools for analyzing different aspects of the system:

- System information and processes
- Memory and storage usage
- Network interfaces and connections
- Service status and logs
- Security monitoring and anomaly detection

This component executes actual system commands (like `ps aux`, `df -h`, etc.) and parses their outputs into structured data for analysis.

### `ai_investigator.py`

Integrates the server investigation tools with the biological consciousness model:

- Implements the 5-state consciousness model (DORMANT → DROWSY → AWARE → ALERT → FULLY_AWAKE)
- Each state provides access to different tools based on their complexity
- State transitions occur based on findings severity
- Provides a complete investigation workflow from waking up to generating insights

### `weekly_report.py`

Generates comprehensive weekly reports of system findings:

- Aggregates insights from multiple investigations
- Creates HTML reports with visual representations of data
- Can send email reports to system administrators
- Includes consciousness state distribution and tool usage statistics

## Usage

### Running the Investigation System

Run the AI investigator with:

```bash
python3 ai_investigator.py --duration=300
```

Options:
- `--duration=<seconds>`: How long the AI should stay awake (default: 30)
- `--log-dir=<path>`: Where to store logs and findings (default: /tmp/deus-ex-machina/logs)

### Generating Reports

Generate a weekly report with:

```bash
python3 weekly_report.py
```

Update the email settings in the script first to enable email delivery.

## Integration

These tools integrate with the existing Deus Ex Machina components:

- `consciousness.py`: The biological consciousness model
- `action_grammar.py`: Structured command execution
- `memory.py`: Persistent storage for findings
- `ai_providers.py`: Multiple AI backend support

## Output Files

The system generates structured output files:

1. **Findings Files** (`findings_TIMESTAMP.json`):
   - Raw data from system investigation
   - Insights generated during analysis
   - Tool usage statistics

2. **Metrics Files** (`metrics_TIMESTAMP.json`):
   - Consciousness state transitions
   - Time spent in each state
   - Tool usage frequencies

## Extension Points

The modular design allows for easy extension:

1. Add new tools to `_register_tools()` in `server_investigator.py`
2. Create parsers for new tool outputs
3. Update consciousness state tool mappings in `_update_tools_for_state()` in `ai_investigator.py`