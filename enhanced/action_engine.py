#!/usr/bin/env python3
# action_engine.py - Automated remediation system for Deus Ex Machina
# Part of the Phase 2 Self-Healing implementation

import os
import sys
import json
import logging
import subprocess
import shlex
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import hashlib
import random

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import configuration
try:
    from config.config import LOG_DIR
except ImportError:
    # Fallback configuration
    LOG_DIR = "/var/log/deus-ex-machina"

# Permission levels for actions
PERMISSION_LEVEL = {
    "OBSERVE": 0,  # Read-only operations
    "RESTART": 1,  # Restart services
    "CLEAN": 2,    # Clean up disk space, remove temp files
    "CONFIGURE": 3, # Modify configuration files
    "ADMIN": 4     # Administrative operations (full control)
}

# Set up logging
AUDIT_LOG = os.path.join(LOG_DIR, "action_audit.log")
ACTION_HISTORY = os.path.join(LOG_DIR, "action_history.json")
ROLLBACK_DIR = os.path.join(LOG_DIR, "rollbacks")

# Create directories if they don't exist
os.makedirs(ROLLBACK_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "action_engine.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ActionEngine")

class ActionEngine:
    """Main class for executing automated remediation actions"""
    
    def __init__(self, max_permission_level: int = PERMISSION_LEVEL["RESTART"]):
        """Initialize the action engine with a default permission level"""
        self.max_permission_level = max_permission_level
        self.action_registry = {}
        self.register_default_actions()
        
    def register_action(self, name: str, func: Callable, permission_level: int, 
                       description: str, reversible: bool = False) -> None:
        """Register an action in the action registry"""
        if permission_level > PERMISSION_LEVEL["ADMIN"]:
            logger.error(f"Invalid permission level for action {name}")
            return
            
        self.action_registry[name] = {
            "function": func,
            "permission_level": permission_level,
            "description": description,
            "reversible": reversible
        }
        logger.info(f"Registered action: {name} (level {permission_level})")
        
    def register_default_actions(self) -> None:
        """Register the default set of remediation actions"""
        # Service management actions
        self.register_action(
            name="restart_service",
            func=self._restart_service,
            permission_level=PERMISSION_LEVEL["RESTART"],
            description="Restart a system service",
            reversible=True
        )
        
        self.register_action(
            name="check_service_status",
            func=self._check_service_status,
            permission_level=PERMISSION_LEVEL["OBSERVE"],
            description="Check the status of a service",
            reversible=False
        )
        
        # Disk cleanup actions
        self.register_action(
            name="clean_temp_files",
            func=self._clean_temp_files,
            permission_level=PERMISSION_LEVEL["CLEAN"],
            description="Clean temporary files",
            reversible=False
        )
        
        self.register_action(
            name="clean_log_files",
            func=self._clean_log_files,
            permission_level=PERMISSION_LEVEL["CLEAN"],
            description="Rotate and compress old log files",
            reversible=False
        )
        
        # Network security actions
        self.register_action(
            name="block_ip",
            func=self._block_ip,
            permission_level=PERMISSION_LEVEL["ADMIN"],
            description="Block an IP address using iptables",
            reversible=True
        )
        
        self.register_action(
            name="check_open_ports",
            func=self._check_open_ports,
            permission_level=PERMISSION_LEVEL["OBSERVE"],
            description="Check for open network ports",
            reversible=False
        )
        
        # Configuration actions
        self.register_action(
            name="backup_config",
            func=self._backup_config,
            permission_level=PERMISSION_LEVEL["OBSERVE"],
            description="Create a backup of a configuration file",
            reversible=False
        )
        
        self.register_action(
            name="restore_config",
            func=self._restore_config,
            permission_level=PERMISSION_LEVEL["CONFIGURE"],
            description="Restore a configuration file from backup",
            reversible=True
        )
        
        # Memory management actions
        self.register_action(
            name="clear_memory_caches",
            func=self._clear_memory_caches,
            permission_level=PERMISSION_LEVEL["CLEAN"],
            description="Clear system memory caches",
            reversible=False
        )
        
    def execute_action(self, action_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a registered action with proper logging and permission checks"""
        if not params:
            params = {}
            
        if action_name not in self.action_registry:
            error_msg = f"Unknown action: {action_name}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        action = self.action_registry[action_name]
        
        # Check permission level
        if action["permission_level"] > self.max_permission_level:
            error_msg = f"Permission denied: {action_name} requires level {action['permission_level']}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        # Generate action ID
        action_id = self._generate_action_id(action_name, params)
        
        # Log action start
        self._audit_log(action_id, action_name, "START", params)
        
        try:
            # Execute the action
            result = action["function"](**params)
            
            # Create backup for reversible actions
            if action["reversible"]:
                self._save_rollback_info(action_id, action_name, params, result)
                
            # Log action completion
            self._audit_log(action_id, action_name, "COMPLETE", result)
            
            # Store in action history
            self._update_action_history(action_id, action_name, params, result)
            
            # Add action ID to result
            result["action_id"] = action_id
            
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Action {action_name} failed: {error_msg}")
            
            # Log action failure
            self._audit_log(action_id, action_name, "FAILED", {"error": error_msg})
            
            return {"success": False, "error": error_msg, "action_id": action_id}
            
    def rollback_action(self, action_id: str) -> Dict[str, Any]:
        """Attempt to roll back a previously executed action"""
        rollback_file = os.path.join(ROLLBACK_DIR, f"{action_id}.json")
        
        if not os.path.exists(rollback_file):
            error_msg = f"No rollback information found for action {action_id}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
        try:
            with open(rollback_file, 'r') as f:
                rollback_info = json.load(f)
                
            action_name = rollback_info.get("action_name")
            params = rollback_info.get("params", {})
            rollback_data = rollback_info.get("rollback_data", {})
            
            if not action_name:
                error_msg = "Invalid rollback information (missing action name)"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            if action_name not in self.action_registry:
                error_msg = f"Unknown action: {action_name}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            action = self.action_registry[action_name]
            
            # Check if action is reversible
            if not action.get("reversible", False):
                error_msg = f"Action {action_name} is not reversible"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            # Execute rollback
            rollback_func_name = f"_rollback_{action_name}"
            if hasattr(self, rollback_func_name):
                rollback_func = getattr(self, rollback_func_name)
                rollback_result = rollback_func(params, rollback_data)
                
                # Log rollback
                self._audit_log(
                    action_id, 
                    f"ROLLBACK_{action_name}", 
                    "COMPLETE", 
                    rollback_result
                )
                
                return {
                    "success": True,
                    "action_id": action_id,
                    "message": f"Successfully rolled back {action_name}",
                    "details": rollback_result
                }
            else:
                error_msg = f"No rollback method found for {action_name}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            error_msg = f"Error during rollback: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
            
    def _safe_execute(self, command: List[str], timeout: int = 60) -> Dict[str, Any]:
        """Safely execute a system command with timeout and proper error handling"""
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": ' '.join(command)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": ' '.join(command)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join(command)
            }
            
    def _generate_action_id(self, action_name: str, params: Dict[str, Any]) -> str:
        """Generate a unique ID for an action"""
        timestamp = datetime.now().isoformat()
        seed = f"{timestamp}_{action_name}_{json.dumps(params, sort_keys=True)}"
        hash_obj = hashlib.md5(seed.encode())
        return hash_obj.hexdigest()
        
    def _audit_log(self, action_id: str, action_name: str, status: str, details: Dict[str, Any]) -> None:
        """Write to the audit log"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "action_id": action_id,
            "action_name": action_name,
            "status": status,
            "details": details
        }
        
        try:
            with open(AUDIT_LOG, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Error writing to audit log: {str(e)}")
            
    def _save_rollback_info(self, action_id: str, action_name: str, params: Dict[str, Any], 
                           result: Dict[str, Any]) -> None:
        """Save rollback information for reversible actions"""
        rollback_info = {
            "timestamp": datetime.now().isoformat(),
            "action_id": action_id,
            "action_name": action_name,
            "params": params,
            "result": result,
            "rollback_data": result.get("rollback_data", {})
        }
        
        rollback_file = os.path.join(ROLLBACK_DIR, f"{action_id}.json")
        
        try:
            with open(rollback_file, 'w') as f:
                json.dump(rollback_info, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving rollback information: {str(e)}")
            
    def _update_action_history(self, action_id: str, action_name: str, 
                             params: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Update the action history JSON file"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "action_id": action_id,
            "action_name": action_name,
            "params": params,
            "success": result.get("success", False),
            "summary": result.get("message", ""),
            "details": result
        }
        
        try:
            # Load existing history
            if os.path.exists(ACTION_HISTORY):
                with open(ACTION_HISTORY, 'r') as f:
                    try:
                        history = json.load(f)
                    except json.JSONDecodeError:
                        history = {"actions": []}
            else:
                history = {"actions": []}
                
            # Add new entry
            history["actions"].insert(0, history_entry)
            
            # Keep only the last 100 actions
            history["actions"] = history["actions"][:100]
            
            # Write back
            with open(ACTION_HISTORY, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating action history: {str(e)}")
            
    # --------------------------
    # Action implementations
    # --------------------------
    
    def _restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a system service"""
        # Input validation
        if not re.match(r'^[a-zA-Z0-9_.-]+$', service_name):
            return {"success": False, "error": "Invalid service name"}
            
        # Get current status for rollback
        status_cmd = ["systemctl", "status", service_name]
        status_result = self._safe_execute(status_cmd)
        was_active = "active (running)" in status_result.get("stdout", "")
        
        # Execute the restart
        restart_cmd = ["systemctl", "restart", service_name]
        result = self._safe_execute(restart_cmd)
        
        # Verify the restart
        if result["success"]:
            # Wait briefly for service to stabilize
            time.sleep(2)
            
            # Check new status
            new_status_cmd = ["systemctl", "status", service_name]
            new_status_result = self._safe_execute(new_status_cmd)
            now_active = "active (running)" in new_status_result.get("stdout", "")
            
            result["message"] = f"Service {service_name} restarted"
            result["status_changed"] = was_active != now_active
            result["rollback_data"] = {
                "was_active": was_active,
                "status_output": status_result.get("stdout", "")
            }
        else:
            result["message"] = f"Failed to restart service {service_name}"
            
        return result
        
    def _rollback_restart_service(self, params: Dict[str, Any], rollback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback a service restart by returning to previous state"""
        service_name = params.get("service_name")
        was_active = rollback_data.get("was_active", False)
        
        if not service_name:
            return {"success": False, "error": "Missing service name for rollback"}
            
        # Get current status
        status_cmd = ["systemctl", "status", service_name]
        status_result = self._safe_execute(status_cmd)
        now_active = "active (running)" in status_result.get("stdout", "")
        
        # If status has changed, restore previous state
        if was_active != now_active:
            if was_active:
                # Service was running, but now it's not - start it
                action_cmd = ["systemctl", "start", service_name]
                action_type = "start"
            else:
                # Service was not running, but now it is - stop it
                action_cmd = ["systemctl", "stop", service_name]
                action_type = "stop"
                
            result = self._safe_execute(action_cmd)
            result["message"] = f"Rolled back service {service_name} by {action_type}"
        else:
            # No change needed
            result = {
                "success": True,
                "message": f"No rollback needed for {service_name}, state already matches original"
            }
            
        return result
        
    def _check_service_status(self, service_name: str) -> Dict[str, Any]:
        """Check the status of a service"""
        # Input validation
        if not re.match(r'^[a-zA-Z0-9_.-]+$', service_name):
            return {"success": False, "error": "Invalid service name"}
            
        # Execute the status check
        status_cmd = ["systemctl", "status", service_name]
        result = self._safe_execute(status_cmd)
        
        # Parse the status output
        if result["success"] or result["returncode"] == 3:  # 3 means service is not running
            stdout = result.get("stdout", "")
            active_status = re.search(r'Active:\s+(\S+)', stdout)
            
            if active_status:
                status = active_status.group(1)
                result["service_status"] = status
                result["is_active"] = "active" in status
                result["message"] = f"Service {service_name} status: {status}"
                result["success"] = True  # Even if service is inactive, the check is successful
            else:
                result["message"] = f"Could not determine status of {service_name}"
                result["success"] = False
        else:
            result["message"] = f"Failed to check status of service {service_name}"
            
        return result
        
    def _clean_temp_files(self, directory: str = "/tmp", pattern: str = "*", 
                         max_age_days: int = 7) -> Dict[str, Any]:
        """Clean old temporary files"""
        # Input validation
        if not os.path.isdir(directory):
            return {"success": False, "error": f"Directory not found: {directory}"}
            
        if not re.match(r'^[a-zA-Z0-9_.*?-]+$', pattern):
            return {"success": False, "error": "Invalid file pattern"}
            
        # Find and delete old files
        find_cmd = [
            "find", directory, "-type", "f", 
            "-name", pattern,
            "-mtime", f"+{max_age_days}",
            "-delete", "-print"
        ]
        
        result = self._safe_execute(find_cmd, timeout=300)  # Longer timeout for large dirs
        
        # Count deleted files
        deleted_files = 0
        if result["success"]:
            deleted_files = len(result["stdout"].strip().split('\n')) if result["stdout"].strip() else 0
            result["message"] = f"Deleted {deleted_files} temporary files from {directory}"
            result["deleted_files"] = deleted_files
        else:
            result["message"] = f"Failed to clean temporary files from {directory}"
            
        return result
        
    def _clean_log_files(self, log_dir: str = "/var/log", 
                       max_age_days: int = 30) -> Dict[str, Any]:
        """Rotate and compress old log files"""
        # Input validation
        if not os.path.isdir(log_dir):
            return {"success": False, "error": f"Directory not found: {log_dir}"}
            
        # Use logrotate if available
        logrotate_cmd = ["logrotate", "-f", "/etc/logrotate.conf"]
        result = self._safe_execute(logrotate_cmd)
        
        if result["success"]:
            result["message"] = "Log rotation completed successfully"
        else:
            # Fallback to manual cleanup of old log files
            find_cmd = [
                "find", log_dir, "-type", "f", 
                "-name", "*.log*",
                "-mtime", f"+{max_age_days}",
                "-delete", "-print"
            ]
            
            find_result = self._safe_execute(find_cmd, timeout=300)
            
            if find_result["success"]:
                deleted_files = len(find_result["stdout"].strip().split('\n')) if find_result["stdout"].strip() else 0
                result = find_result
                result["message"] = f"Manually cleaned {deleted_files} old log files"
                result["deleted_files"] = deleted_files
            else:
                result["message"] = "Failed to clean old log files"
                
        return result
        
    def _block_ip(self, ip_address: str, protocol: str = "all", 
                reason: str = "Blocked by Deus Ex Machina") -> Dict[str, Any]:
        """Block an IP address using iptables"""
        # Input validation
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if not re.match(ip_pattern, ip_address):
            return {"success": False, "error": "Invalid IP address"}
            
        if protocol not in ["all", "tcp", "udp", "icmp"]:
            return {"success": False, "error": "Invalid protocol"}
            
        # Check if the IP is already blocked
        check_cmd = ["iptables", "-L", "INPUT", "-n"]
        check_result = self._safe_execute(check_cmd)
        
        if ip_address in check_result.get("stdout", ""):
            return {
                "success": True,
                "message": f"IP {ip_address} is already blocked",
                "already_blocked": True
            }
            
        # Add the block rule
        block_cmd = ["iptables", "-A", "INPUT", "-s", ip_address]
        if protocol != "all":
            block_cmd.extend(["-p", protocol])
        block_cmd.extend(["-j", "DROP", "-m", "comment", "--comment", reason])
        
        result = self._safe_execute(block_cmd)
        
        if result["success"]:
            result["message"] = f"Successfully blocked IP {ip_address}"
            result["rollback_data"] = {
                "ip_address": ip_address,
                "protocol": protocol
            }
        else:
            result["message"] = f"Failed to block IP {ip_address}"
            
        return result
        
    def _rollback_block_ip(self, params: Dict[str, Any], rollback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Unblock a previously blocked IP address"""
        ip_address = params.get("ip_address") or rollback_data.get("ip_address")
        protocol = params.get("protocol") or rollback_data.get("protocol") or "all"
        
        if not ip_address:
            return {"success": False, "error": "Missing IP address for rollback"}
            
        # Remove the block rule
        unblock_cmd = ["iptables", "-D", "INPUT", "-s", ip_address]
        if protocol != "all":
            unblock_cmd.extend(["-p", protocol])
        unblock_cmd.extend(["-j", "DROP"])
        
        result = self._safe_execute(unblock_cmd)
        
        if result["success"]:
            result["message"] = f"Successfully unblocked IP {ip_address}"
        else:
            result["message"] = f"Failed to unblock IP {ip_address}"
            
        return result
        
    def _check_open_ports(self) -> Dict[str, Any]:
        """Check for open network ports"""
        ss_cmd = ["ss", "-tuln"]
        result = self._safe_execute(ss_cmd)
        
        if result["success"]:
            # Parse the output to extract listening ports
            lines = result["stdout"].strip().split('\n')
            listening_ports = []
            
            for line in lines[1:]:  # Skip header line
                parts = line.split()
                if len(parts) >= 5:
                    addr_port = parts[4]
                    if ":" in addr_port:
                        addr, port = addr_port.rsplit(":", 1)
                        listening_ports.append({
                            "address": addr,
                            "port": port,
                            "protocol": "tcp" if "tcp" in line else "udp"
                        })
            
            result["listening_ports"] = listening_ports
            result["port_count"] = len(listening_ports)
            result["message"] = f"Found {len(listening_ports)} open ports"
        else:
            result["message"] = "Failed to check open ports"
            
        return result
        
    def _backup_config(self, config_path: str) -> Dict[str, Any]:
        """Create a backup of a configuration file"""
        # Input validation
        if not os.path.isfile(config_path):
            return {"success": False, "error": f"File not found: {config_path}"}
            
        # Create timestamp for the backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(config_path)
        backup_path = os.path.join(ROLLBACK_DIR, f"{filename}.{timestamp}.bak")
        
        # Create the backup
        cp_cmd = ["cp", "-p", config_path, backup_path]
        result = self._safe_execute(cp_cmd)
        
        if result["success"]:
            result["message"] = f"Successfully backed up {config_path}"
            result["backup_path"] = backup_path
        else:
            result["message"] = f"Failed to back up {config_path}"
            
        return result
        
    def _restore_config(self, backup_path: str, 
                       destination_path: str = None) -> Dict[str, Any]:
        """Restore a configuration file from backup"""
        # Input validation
        if not os.path.isfile(backup_path):
            return {"success": False, "error": f"Backup file not found: {backup_path}"}
            
        # If destination path not provided, derive it from the backup filename
        if not destination_path:
            filename = os.path.basename(backup_path)
            # Remove timestamp suffix (format: filename.YYYYMMDD_HHMMSS.bak)
            original_name = re.sub(r'\.\d{8}_\d{6}\.bak$', '', filename)
            # Assume original was in /etc
            destination_path = f"/etc/{original_name}"
            
        # Create a backup of the current file before restoring
        if os.path.exists(destination_path):
            current_backup = self._backup_config(destination_path)
            if not current_backup["success"]:
                return {
                    "success": False,
                    "error": f"Could not backup current file before restore: {current_backup['error']}"
                }
                
        # Restore the backup
        cp_cmd = ["cp", "-p", backup_path, destination_path]
        result = self._safe_execute(cp_cmd)
        
        if result["success"]:
            result["message"] = f"Successfully restored {destination_path} from backup"
            result["destination_path"] = destination_path
            if 'current_backup' in locals():
                result["current_backup_path"] = current_backup["backup_path"]
        else:
            result["message"] = f"Failed to restore {destination_path} from backup"
            
        return result
        
    def _clear_memory_caches(self) -> Dict[str, Any]:
        """Clear system memory caches"""
        # This requires elevated privileges
        sync_cmd = ["sync"]
        self._safe_execute(sync_cmd)
        
        # Write to drop_caches
        echo_cmd = ["sh", "-c", "echo 3 > /proc/sys/vm/drop_caches"]
        result = self._safe_execute(echo_cmd)
        
        if result["success"]:
            result["message"] = "Successfully cleared memory caches"
            
            # Get memory info before and after
            free_cmd = ["free", "-m"]
            after_result = self._safe_execute(free_cmd)
            result["memory_info"] = after_result.get("stdout", "")
        else:
            result["message"] = "Failed to clear memory caches"
            
        return result

if __name__ == "__main__":
    # When run directly, execute a basic self-test
    engine = ActionEngine()
    
    # Run a simple service status check
    result = engine.execute_action("check_service_status", {"service_name": "cron"})
    print(json.dumps(result, indent=2))