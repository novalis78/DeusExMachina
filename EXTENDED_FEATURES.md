# Extended Features for Deus Ex Machina

This document outlines advanced features added to the Deus Ex Machina system that extend its autonomous capabilities.

## Multi-Provider AI System

The enhanced system now supports multiple AI providers through a unified interface, providing superior resilience and flexibility.

### Features

- **Multiple AI Providers**: Support for Google Gemini, Anthropic Claude, OpenAI, and local fallback
- **Automatic Failover**: If one AI service is unavailable, the system automatically tries alternatives
- **Consistent Response Format**: All providers return standardized analysis for seamless integration
- **Configurable Priority**: Customize which providers to use and in what order
- **Local Fallback**: Rule-based analysis always available even when all external services are down

### Implementation

The system uses a provider manager that tries each configured AI service in sequence:

```python
class AIProviderManager:
    def analyze(self, system_info, log_data, metrics_data):
        # Try each provider until one succeeds
        for provider in self.providers:
            if not provider.is_available():
                continue
                
            try:
                result = provider.analyze(system_info, log_data, metrics_data)
                if result:
                    return result
            except Exception:
                pass
                
        # If all fail, use local analysis
        return self.local_provider.analyze(system_info, log_data, metrics_data)
```

## Action Grammar System

The Action Grammar system provides a structured way for the AI to interact with the operating system while maintaining safety boundaries.

### Features

- **Safe Command Execution**: Execute system commands with proper permission checks
- **Structured Actions**: Different action types (command, file, service) with appropriate validations
- **Permission Levels**: Granular control over what actions can be performed
- **Action Sequences**: Chain multiple actions together with contextual awareness
- **Variable Substitution**: Use results from previous actions in subsequent commands
- **Result Parsing**: Automatically parse command output into structured data
- **Audit Logging**: Comprehensive logging of all actions for accountability

### Example Usage

```python
# Create a sequence of actions to investigate high disk usage
disk_check = action_grammar.create_command_action(
    name="check_disk_usage",
    command=["df", "-h"],
    permission_level="OBSERVE",
    parser=parse_df_output
)

find_large_files = action_grammar.create_command_action(
    name="find_large_files",
    command=["find", "/var/log", "-type", "f", "-size", "+100M"],
    permission_level="OBSERVE"
)

clean_logs = action_grammar.create_command_action(
    name="clean_old_logs",
    command=["find", "/var/log", "-type", "f", "-name", "*.gz", "-mtime", "+30", "-delete"],
    permission_level="CLEAN"
)

sequence = action_grammar.create_sequence(
    name="disk_cleanup",
    description="Investigate and clean up disk space",
    actions=[disk_check, find_large_files, clean_logs]
)

# Execute the sequence
result = action_grammar.execute_sequence(sequence)
```

## Biological Consciousness Model

The system now implements a biological-inspired consciousness model that manages different awareness states.

### Features

- **Multiple Consciousness States**:
  - **DORMANT**: Lowest resource usage, biological systems only
  - **DROWSY**: Periodic light processing of accumulated data
  - **AWARE**: Regular moderate AI analysis
  - **ALERT**: Enhanced monitoring due to anomalies
  - **FULLY_AWAKE**: Full AI analysis and active problem-solving

- **Automatic State Transitions**: System automatically transitions between states based on:
  - Time of day (circadian rhythm)
  - Detected anomalies
  - Resource usage
  - Time limits for resource-intensive states

- **Event-driven Architecture**: State changes trigger appropriate handlers
- **Persistent State**: System remembers its state across restarts
- **Activity Tracking**: System tracks different activities to inform state transitions

### Implementation

The system uses a dedicated consciousness module that manages these states:

```python
class Consciousness:
    def __init__(self, initial_state=ConsciousnessState.DORMANT):
        self.state = initial_state
        self.state_history = []
        self.last_state_change = datetime.now()
        self.last_activity = {}
        
    def change_state(self, new_state, reason):
        # Record the transition
        transition = ConsciousnessTransition(
            from_state=self.state,
            to_state=new_state,
            reason=reason
        )
        
        self.state_history.append(transition)
        self.state = new_state
        self.last_state_change = datetime.now()
        
        # Trigger event handlers
        self._trigger_handlers(old_state, new_state, reason)
```

## Integration with Core System

These new features are fully integrated with the existing Deus Ex Machina architecture:

1. **Memory System**: Stores consciousness state and action history
2. **AI Brain**: Uses the multi-provider system for analysis
3. **Action Engine**: Enhanced with the Action Grammar for safer execution
4. **Integration Controller**: Manages consciousness state transitions

## Configuration

The enhancements can be configured in `config.py`:

```python
CONFIG = {
    # ... existing config ...
    
    # AI Provider Configuration
    "ai_providers": {
        "google_ai": {
            "enabled": True,
            "api_key_path": "/path/to/google_key.json",
            "model": "gemini-pro"
        },
        "anthropic": {
            "enabled": True,
            "api_key_env": "ANTHROPIC_API_KEY",
            "model": "claude-3-haiku-20240307"
        },
        "openai": {
            "enabled": False,
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-4-turbo"
        }
    },
    
    # Action Grammar Configuration
    "action_grammar": {
        "max_permission_level": "RESTART",
        "audit_log_path": "/var/log/deus-ex-machina/action_audit.log",
        "max_sequence_length": 10
    },
    
    # Consciousness Configuration
    "consciousness": {
        "initial_state": "DORMANT",
        "check_interval": 60,
        "scheduled_wake_hour": 3,  # 3 AM
        "max_fully_awake_hours": 2
    }
}
```

## Security Considerations

Security has been a primary focus in these enhancements:

1. **Permission Levels**: All actions are subject to strict permission controls
2. **Command Validation**: Commands are validated before execution to prevent dangerous operations
3. **Sandboxed Execution**: Actions run with appropriate restrictions
4. **Audit Trails**: All actions are logged for accountability
5. **Consciousness Limits**: Resource-intensive states have automatic time limits
6. **API Key Security**: AI provider keys are stored securely and accessed only when needed

## Usage Examples

### Investigating and Resolving a High CPU Issue

```python
# System detects high CPU usage and increases consciousness level
consciousness.change_state(ConsciousnessState.ALERT, "High CPU usage detected")

# AI analyzes the situation
analysis = ai_provider_manager.analyze(system_info, log_data, metrics_data)

# Create action sequence based on analysis
actions = []
actions.append(action_grammar.create_command_action(
    name="check_processes",
    command=["ps", "auxf", "--sort=-pcpu"],
    permission_level="OBSERVE",
    parser=parse_ps_output
))

if "java" in analysis["issues"][0]:
    actions.append(action_grammar.create_service_action(
        name="restart_java_service",
        service_name="tomcat",
        operation="restart",
        permission_level="RESTART"
    ))

# Execute the actions
sequence = action_grammar.create_sequence(
    name="cpu_issue_resolution",
    description="Investigate and resolve high CPU usage",
    actions=actions
)
result = action_grammar.execute_sequence(sequence)

# Return to lower consciousness state when resolved
consciousness.change_state(ConsciousnessState.AWARE, "CPU issue resolved")
```

## Future Enhancements

1. **Learning System**: Build a knowledge base of successful resolutions for faster problem-solving
2. **Predictive Awakening**: Use prediction engine to wake up before issues occur
3. **Multi-Node Awareness**: Extend consciousness model to coordinate across multiple servers
4. **Natural Language Interface**: Allow direct conversation with the system for manual investigations