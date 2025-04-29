#!/usr/bin/env python3
"""
Action Grammar Module - Safe tool execution framework for AI-directed actions
Provides a structured way for the AI to execute system commands safely
"""
import os
import sys
import json
import logging
import subprocess
import shlex
import re
import tempfile
import time
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('action_grammar')

# Define permission levels
PERMISSION_LEVELS = {
    "OBSERVE": 0,  # Read-only operations (ls, cat, ps, etc.)
    "ANALYZE": 1,  # Analysis operations (grep, find, etc.)
    "RESTART": 2,  # Restart services
    "CLEAN": 3,    # Clean up operations (rm temp files, rotate logs)
    "CONFIGURE": 4, # Configuration operations (edit files)
    "ADMIN": 5     # Administrative operations (full control)
}

class ActionResult:
    """Result of an action execution"""
    
    def __init__(self, 
                success: bool, 
                output: str = "", 
                error: str = "", 
                return_code: int = 0,
                action_id: str = "",
                parsed_result: Optional[Any] = None):
        self.success = success
        self.output = output
        self.error = error
        self.return_code = return_code
        self.action_id = action_id
        self.parsed_result = parsed_result
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "return_code": self.return_code,
            "action_id": self.action_id,
            "parsed_result": self.parsed_result,
            "timestamp": self.timestamp
        }
        
    def __str__(self) -> str:
        """String representation"""
        return f"ActionResult(success={self.success}, return_code={self.return_code}, output_length={len(self.output)})"

class Action:
    """Base class for all actions"""
    
    def __init__(self, 
                name: str, 
                permission_level: str,
                params: Dict[str, Any] = None):
        self.name = name
        self.permission_level = PERMISSION_LEVELS.get(permission_level, 0)
        self.params = params or {}
        self.logger = logging.getLogger(f'action.{name}')
        
    def execute(self, context: Dict[str, Any] = None) -> ActionResult:
        """Execute the action"""
        raise NotImplementedError("Subclasses must implement execute()")
        
    def validate(self) -> bool:
        """Validate action parameters"""
        return True
        
    def generate_id(self) -> str:
        """Generate a unique ID for this action"""
        data = f"{self.name}_{json.dumps(self.params, sort_keys=True)}_{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()

class CommandAction(Action):
    """Action to execute a system command"""
    
    def __init__(self, 
                name: str, 
                command: Union[str, List[str]],
                permission_level: str = "OBSERVE",
                timeout: int = 60,
                parser: Optional[Callable[[str], Any]] = None,
                params: Dict[str, Any] = None):
        super().__init__(name, permission_level, params)
        self.command = command
        self.timeout = timeout
        self.parser = parser
        
    def validate(self) -> bool:
        """Validate command parameters"""
        # Convert command to list if it's a string
        if isinstance(self.command, str):
            self.command = shlex.split(self.command)
            
        # Basic validation
        if not self.command:
            self.logger.error("Empty command")
            return False
            
        # Check for dangerous commands based on permission level
        restricted_commands = {
            "OBSERVE": ["rm", "mv", "cp", "dd", "mkfs", "fdisk", "mkswap", "chmod", "chown"],
            "ANALYZE": ["rm", "mv", "dd", "mkfs", "fdisk", "mkswap"],
            "RESTART": ["rm -rf", "mkfs", "fdisk"],
            "CLEAN": ["mkfs", "fdisk"],
            "CONFIGURE": [],
            "ADMIN": []
        }
        
        # Get the relevant permission level name
        level_name = next((k for k, v in PERMISSION_LEVELS.items() if v == self.permission_level), "OBSERVE")
        
        # Check if command contains restricted elements
        cmd_str = " ".join(self.command)
        for restricted in restricted_commands.get(level_name, []):
            if restricted in cmd_str:
                self.logger.error(f"Command '{cmd_str}' contains restricted element '{restricted}' for permission level {level_name}")
                return False
                
        return True
        
    def execute(self, context: Dict[str, Any] = None) -> ActionResult:
        """Execute the command"""
        if not self.validate():
            return ActionResult(
                success=False,
                error=f"Command validation failed: {self.command}",
                return_code=1,
                action_id=self.generate_id()
            )
            
        try:
            # Apply variable substitution from context
            command = self._substitute_variables(self.command, context or {})
            
            # Execute the command
            self.logger.info(f"Executing command: {' '.join(command)}")
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout
            )
            
            # Parse the output if a parser is provided
            parsed_result = None
            if self.parser and result.returncode == 0:
                try:
                    parsed_result = self.parser(result.stdout)
                except Exception as e:
                    self.logger.error(f"Error parsing command output: {str(e)}")
                    
            action_id = self.generate_id()
            
            return ActionResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                return_code=result.returncode,
                action_id=action_id,
                parsed_result=parsed_result
            )
        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                error=f"Command timed out after {self.timeout} seconds",
                return_code=124,  # Standard timeout exit code
                action_id=self.generate_id()
            )
        except Exception as e:
            return ActionResult(
                success=False,
                error=f"Error executing command: {str(e)}",
                return_code=1,
                action_id=self.generate_id()
            )
            
    def _substitute_variables(self, command: List[str], context: Dict[str, Any]) -> List[str]:
        """Substitute variables in command with values from context"""
        result = []
        
        for item in command:
            # Check for variable references like {{variable_name}}
            matches = re.findall(r'\{\{([^}]+)\}\}', item)
            
            if matches:
                new_item = item
                for match in matches:
                    if match in context:
                        # Replace the variable with its value
                        value = str(context[match])
                        new_item = new_item.replace(f"{{{{{match}}}}}", value)
                    else:
                        self.logger.warning(f"Variable '{match}' not found in context")
                        
                result.append(new_item)
            else:
                result.append(item)
                
        return result

class FileAction(Action):
    """Action to read or write a file"""
    
    def __init__(self, 
                name: str, 
                operation: str,  # "read" or "write"
                file_path: str,
                content: Optional[str] = None,
                permission_level: str = "OBSERVE",
                params: Dict[str, Any] = None):
        super().__init__(name, permission_level, params)
        self.operation = operation
        self.file_path = file_path
        self.content = content
        
    def validate(self) -> bool:
        """Validate file action parameters"""
        # Check operation
        if self.operation not in ["read", "write"]:
            self.logger.error(f"Invalid operation: {self.operation}")
            return False
            
        # For write operations, check permission level
        if self.operation == "write" and self.permission_level < PERMISSION_LEVELS["CONFIGURE"]:
            self.logger.error(f"Writing files requires CONFIGURE permission or higher")
            return False
            
        # For write operations, content must be provided
        if self.operation == "write" and self.content is None:
            self.logger.error("Content must be provided for write operations")
            return False
            
        # Basic path sanitization
        if ".." in self.file_path or not self.file_path.startswith("/"):
            self.logger.error(f"Invalid or relative file path: {self.file_path}")
            return False
            
        # For read operations, check if the file exists
        if self.operation == "read" and not os.path.isfile(self.file_path):
            self.logger.error(f"File not found: {self.file_path}")
            return False
            
        return True
        
    def execute(self, context: Dict[str, Any] = None) -> ActionResult:
        """Execute the file action"""
        if not self.validate():
            return ActionResult(
                success=False,
                error=f"File action validation failed: {self.operation} {self.file_path}",
                return_code=1,
                action_id=self.generate_id()
            )
            
        try:
            # Apply variable substitution from context
            file_path = self._substitute_variables(self.file_path, context or {})
            
            if self.operation == "read":
                # Read the file
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                return ActionResult(
                    success=True,
                    output=content,
                    action_id=self.generate_id(),
                    parsed_result={"file": file_path, "content": content}
                )
            elif self.operation == "write":
                # Apply variable substitution to content
                content = self._substitute_variables(self.content, context or {})
                
                # Write to the file
                # First, write to a temporary file
                dir_name = os.path.dirname(file_path)
                with tempfile.NamedTemporaryFile(mode='w', dir=dir_name, delete=False) as temp_file:
                    temp_path = temp_file.name
                    temp_file.write(content)
                    
                # Then, move the temporary file to the target path
                os.rename(temp_path, file_path)
                
                return ActionResult(
                    success=True,
                    output=f"Wrote {len(content)} bytes to {file_path}",
                    action_id=self.generate_id(),
                    parsed_result={"file": file_path, "size": len(content)}
                )
        except Exception as e:
            return ActionResult(
                success=False,
                error=f"Error in file action: {str(e)}",
                return_code=1,
                action_id=self.generate_id()
            )
            
    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Substitute variables in text with values from context"""
        # Check for variable references like {{variable_name}}
        matches = re.findall(r'\{\{([^}]+)\}\}', text)
        
        result = text
        for match in matches:
            if match in context:
                # Replace the variable with its value
                value = str(context[match])
                result = result.replace(f"{{{{{match}}}}}", value)
            else:
                self.logger.warning(f"Variable '{match}' not found in context")
                
        return result

class ServiceAction(Action):
    """Action to manage services"""
    
    def __init__(self, 
                name: str, 
                service_name: str,
                operation: str,  # "status", "start", "stop", "restart"
                permission_level: str = "OBSERVE",
                params: Dict[str, Any] = None):
        super().__init__(name, permission_level, params)
        self.service_name = service_name
        self.operation = operation
        
    def validate(self) -> bool:
        """Validate service action parameters"""
        # Validate operation
        valid_operations = ["status", "start", "stop", "restart", "reload"]
        if self.operation not in valid_operations:
            self.logger.error(f"Invalid operation: {self.operation}")
            return False
            
        # Check permission level for operations other than status
        if self.operation != "status" and self.permission_level < PERMISSION_LEVELS["RESTART"]:
            self.logger.error(f"Operation {self.operation} requires RESTART permission or higher")
            return False
            
        # Validate service name (basic sanitization)
        if not re.match(r'^[a-zA-Z0-9_.-]+$', self.service_name):
            self.logger.error(f"Invalid service name: {self.service_name}")
            return False
            
        return True
        
    def execute(self, context: Dict[str, Any] = None) -> ActionResult:
        """Execute the service action"""
        if not self.validate():
            return ActionResult(
                success=False,
                error=f"Service action validation failed: {self.operation} {self.service_name}",
                return_code=1,
                action_id=self.generate_id()
            )
            
        try:
            # Apply variable substitution from context
            service_name = self._substitute_variables(self.service_name, context or {})
            
            # Construct the systemctl command
            command = ["systemctl", self.operation, service_name]
            
            # Execute the command
            self.logger.info(f"Executing service action: {' '.join(command)}")
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )
            
            action_id = self.generate_id()
            
            # For status operation, parse the result
            parsed_result = None
            if self.operation == "status" and result.returncode in [0, 3]:  # 3 means service is not running
                active = "Active: active" in result.stdout
                running = "running" in result.stdout
                
                parsed_result = {
                    "service": service_name,
                    "active": active,
                    "running": running,
                    "exit_code": result.returncode
                }
                
                # Status check is successful even if service is not running
                return ActionResult(
                    success=True,
                    output=result.stdout,
                    error=result.stderr,
                    return_code=result.returncode,
                    action_id=action_id,
                    parsed_result=parsed_result
                )
            
            return ActionResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr,
                return_code=result.returncode,
                action_id=action_id,
                parsed_result=parsed_result
            )
        except Exception as e:
            return ActionResult(
                success=False,
                error=f"Error in service action: {str(e)}",
                return_code=1,
                action_id=self.generate_id()
            )
            
    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Substitute variables in text with values from context"""
        # Check for variable references like {{variable_name}}
        matches = re.findall(r'\{\{([^}]+)\}\}', text)
        
        result = text
        for match in matches:
            if match in context:
                # Replace the variable with its value
                value = str(context[match])
                result = result.replace(f"{{{{{match}}}}}", value)
            else:
                self.logger.warning(f"Variable '{match}' not found in context")
                
        return result

class ActionSequence:
    """A sequence of actions to be executed in order"""
    
    def __init__(self, 
                name: str,
                description: str,
                actions: List[Action],
                max_permission_level: str = "OBSERVE"):
        self.name = name
        self.description = description
        self.actions = actions
        self.max_permission_level = PERMISSION_LEVELS.get(max_permission_level, 0)
        self.logger = logging.getLogger(f'action_sequence.{name}')
        self.context = {}  # Shared context between actions
        
    def execute(self) -> Dict[str, Any]:
        """Execute all actions in sequence"""
        results = []
        success = True
        
        # Check if any action exceeds the permission level
        for action in self.actions:
            if action.permission_level > self.max_permission_level:
                self.logger.error(f"Action {action.name} requires permission level higher than {self.max_permission_level}")
                return {
                    "success": False,
                    "error": f"Permission denied: {action.name} requires higher permission level",
                    "name": self.name,
                    "description": self.description,
                    "results": []
                }
                
        # Execute each action
        start_time = time.time()
        
        for i, action in enumerate(self.actions):
            self.logger.info(f"Executing action {i+1}/{len(self.actions)}: {action.name}")
            
            # Execute action with current context
            result = action.execute(self.context)
            results.append({
                "action": action.name,
                "result": result.to_dict()
            })
            
            # Update context with result
            self.context[f"action_{i+1}_success"] = result.success
            self.context[f"action_{i+1}_output"] = result.output
            self.context[f"action_{i+1}_error"] = result.error
            self.context[f"action_{i+1}_result"] = result.parsed_result
            
            # Also store with action name for easier reference
            safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', action.name)
            self.context[f"{safe_name}_success"] = result.success
            self.context[f"{safe_name}_output"] = result.output
            self.context[f"{safe_name}_error"] = result.error
            self.context[f"{safe_name}_result"] = result.parsed_result
            
            # If action failed and it's not the last one, abort sequence
            if not result.success and i < len(self.actions) - 1:
                self.logger.warning(f"Action {action.name} failed, aborting sequence")
                success = False
                break
                
        elapsed_time = time.time() - start_time
        
        return {
            "success": success,
            "name": self.name,
            "description": self.description,
            "actions_executed": len(results),
            "total_actions": len(self.actions),
            "elapsed_time": elapsed_time,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

class ActionGrammar:
    """Main class for managing and executing actions"""
    
    def __init__(self, max_permission_level: str = "RESTART", log_dir: str = "/var/log/deus-ex-machina"):
        self.max_permission_level = PERMISSION_LEVELS.get(max_permission_level, PERMISSION_LEVELS["RESTART"])
        self.log_dir = log_dir
        self.logger = logging.getLogger('action_grammar')
        self.action_history = []
        self.history_file = os.path.join(log_dir, "action_grammar_history.json")
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
    def create_command_action(self, 
                           name: str, 
                           command: Union[str, List[str]],
                           permission_level: str = "OBSERVE",
                           timeout: int = 60,
                           parser: Optional[Callable[[str], Any]] = None,
                           params: Dict[str, Any] = None) -> CommandAction:
        """Create a command action"""
        return CommandAction(
            name=name,
            command=command,
            permission_level=permission_level,
            timeout=timeout,
            parser=parser,
            params=params
        )
        
    def create_file_action(self,
                        name: str,
                        operation: str,
                        file_path: str,
                        content: Optional[str] = None,
                        permission_level: str = "OBSERVE",
                        params: Dict[str, Any] = None) -> FileAction:
        """Create a file action"""
        return FileAction(
            name=name,
            operation=operation,
            file_path=file_path,
            content=content,
            permission_level=permission_level,
            params=params
        )
        
    def create_service_action(self,
                           name: str,
                           service_name: str,
                           operation: str,
                           permission_level: str = "OBSERVE",
                           params: Dict[str, Any] = None) -> ServiceAction:
        """Create a service action"""
        return ServiceAction(
            name=name,
            service_name=service_name,
            operation=operation,
            permission_level=permission_level,
            params=params
        )
        
    def create_sequence(self,
                     name: str,
                     description: str,
                     actions: List[Action]) -> ActionSequence:
        """Create an action sequence"""
        return ActionSequence(
            name=name,
            description=description,
            actions=actions,
            max_permission_level=next((k for k, v in PERMISSION_LEVELS.items() if v == self.max_permission_level), "OBSERVE")
        )
        
    def execute_sequence(self, sequence: ActionSequence) -> Dict[str, Any]:
        """Execute an action sequence and record results"""
        self.logger.info(f"Executing action sequence: {sequence.name}")
        
        result = sequence.execute()
        
        # Record in history
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "sequence": sequence.name,
            "description": sequence.description,
            "success": result["success"],
            "actions_executed": result["actions_executed"],
            "total_actions": result["total_actions"]
        })
        
        # Save history to file
        self._save_history()
        
        return result
        
    def _save_history(self) -> None:
        """Save action history to file"""
        try:
            # Keep only the last 100 entries
            history = self.action_history[-100:]
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving action history: {str(e)}")
            
    def from_json(self, json_data: Dict[str, Any]) -> Optional[ActionSequence]:
        """Create an action sequence from JSON data"""
        try:
            # Extract sequence metadata
            name = json_data.get("name", "unnamed_sequence")
            description = json_data.get("description", "")
            
            # Extract actions
            actions_data = json_data.get("actions", [])
            actions = []
            
            for action_data in actions_data:
                action_type = action_data.get("type")
                action_name = action_data.get("name", "unnamed_action")
                
                if action_type == "command":
                    actions.append(CommandAction(
                        name=action_name,
                        command=action_data.get("command", ""),
                        permission_level=action_data.get("permission_level", "OBSERVE"),
                        timeout=action_data.get("timeout", 60),
                        params=action_data.get("params", {})
                    ))
                elif action_type == "file":
                    actions.append(FileAction(
                        name=action_name,
                        operation=action_data.get("operation", "read"),
                        file_path=action_data.get("file_path", ""),
                        content=action_data.get("content"),
                        permission_level=action_data.get("permission_level", "OBSERVE"),
                        params=action_data.get("params", {})
                    ))
                elif action_type == "service":
                    actions.append(ServiceAction(
                        name=action_name,
                        service_name=action_data.get("service_name", ""),
                        operation=action_data.get("operation", "status"),
                        permission_level=action_data.get("permission_level", "OBSERVE"),
                        params=action_data.get("params", {})
                    ))
                    
            if not actions:
                self.logger.warning(f"No valid actions found in JSON data")
                return None
                
            # Create sequence
            return ActionSequence(
                name=name,
                description=description,
                actions=actions,
                max_permission_level=next((k for k, v in PERMISSION_LEVELS.items() if v == self.max_permission_level), "OBSERVE")
            )
        except Exception as e:
            self.logger.error(f"Error creating sequence from JSON: {str(e)}")
            return None

# Helper function to parse disk usage from df output
def parse_df_output(output: str) -> List[Dict[str, Any]]:
    """Parse the output of df command"""
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return []
        
    results = []
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 6:
            filesystem = parts[0]
            size = parts[1]
            used = parts[2]
            available = parts[3]
            use_percent = parts[4].rstrip('%')
            mount_point = parts[5]
            
            results.append({
                "filesystem": filesystem,
                "size": size,
                "used": used,
                "available": available,
                "use_percent": int(use_percent) if use_percent.isdigit() else 0,
                "mount_point": mount_point
            })
            
    return results

# Helper function to parse process list from ps output
def parse_ps_output(output: str) -> List[Dict[str, Any]]:
    """Parse the output of ps command"""
    lines = output.strip().split('\n')
    if len(lines) < 2:
        return []
        
    results = []
    for line in lines[1:]:  # Skip header
        parts = line.split(None, 10)  # Split by whitespace, max 11 parts
        if len(parts) >= 4:
            pid = parts[0]
            ppid = parts[1]
            cpu = parts[2]
            mem = parts[3]
            
            # Command might contain spaces
            command = parts[-1] if len(parts) > 4 else ""
            
            results.append({
                "pid": int(pid) if pid.isdigit() else 0,
                "ppid": int(ppid) if ppid.isdigit() else 0,
                "cpu": float(cpu) if cpu.replace('.', '', 1).isdigit() else 0,
                "mem": float(mem) if mem.replace('.', '', 1).isdigit() else 0,
                "command": command
            })
            
    return results

if __name__ == "__main__":
    # Example usage
    grammar = ActionGrammar(max_permission_level="ADMIN")
    
    # Create some actions
    df_action = grammar.create_command_action(
        name="check_disk_space",
        command=["df", "-h"],
        permission_level="OBSERVE",
        parser=parse_df_output
    )
    
    ps_action = grammar.create_command_action(
        name="check_processes",
        command=["ps", "auxf"],
        permission_level="OBSERVE",
        parser=parse_ps_output
    )
    
    service_action = grammar.create_service_action(
        name="check_web_server",
        service_name="nginx",
        operation="status",
        permission_level="OBSERVE"
    )
    
    # Create a sequence
    sequence = grammar.create_sequence(
        name="system_status_check",
        description="Check system status including disk space, processes, and web server",
        actions=[df_action, ps_action, service_action]
    )
    
    # Execute the sequence
    result = grammar.execute_sequence(sequence)
    
    # Print results
    print(json.dumps(result, indent=2))