#!/usr/bin/env python3
# integration.py - Main controller for enhanced Deus Ex Machina
# Integrates all components and provides a unified interface

import os
import sys
import json
import logging
import argparse
import time
from datetime import datetime, timedelta
import sqlite3
import shutil
import importlib.util
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set base directories
DEFAULT_INSTALL_DIR = "/opt/deus-ex-machina"
DEFAULT_LOG_DIR = "/var/log/deus-ex-machina"
DEFAULT_DB_DIR = os.path.join(DEFAULT_LOG_DIR, "database")

# Import implementation files
try:
    # Try to import from default location
    from config.config import LOG_DIR, INSTALL_DIR
except ImportError:
    # Fallback to defaults
    LOG_DIR = DEFAULT_LOG_DIR
    INSTALL_DIR = DEFAULT_INSTALL_DIR

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "integration.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Integration")

class DeusExMachina:
    """Main controller class for the enhanced system"""
    
    def __init__(self, install_dir: str = INSTALL_DIR, log_dir: str = LOG_DIR):
        """Initialize the controller"""
        self.install_dir = install_dir
        self.log_dir = log_dir
        self.db_dir = os.path.join(log_dir, "database")
        self.components = {}
        self.initialized = False
        
        # Create required directories
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.db_dir, exist_ok=True)
        
        logger.info(f"Initialized DeusExMachina controller (install: {install_dir}, logs: {log_dir})")
        
    def setup(self) -> bool:
        """Set up all components and verify installation"""
        try:
            # Verify core scripts exist
            required_scripts = [
                os.path.join(self.install_dir, "core/heartbeat/heartbeat.sh"),
                os.path.join(self.install_dir, "core/breath/breath.sh"),
                os.path.join(self.install_dir, "core/vigilance/vigilance.sh"),
                os.path.join(self.install_dir, "core/state_engine/state_engine.py"),
                os.path.join(self.install_dir, "core/state_engine/state_trigger.py")
            ]
            
            for script in required_scripts:
                if not os.path.exists(script):
                    logger.error(f"Required script not found: {script}")
                    return False
            
            # Load or set up components
            self._setup_memory_module()
            self._setup_action_engine()
            self._setup_ai_brain()
            
            self.initialized = True
            logger.info("DeusExMachina setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False
            
    def _setup_memory_module(self) -> None:
        """Set up the memory database module"""
        memory_path = os.path.join(self.install_dir, "core/memory/memory.py")
        os.makedirs(os.path.dirname(memory_path), exist_ok=True)
        
        # Check if we need to install the memory module
        if not os.path.exists(memory_path):
            # Copy the memory.py file to the installation directory
            source_path = os.path.join(self.install_dir, "enhanced/memory.py")
            if os.path.exists(source_path):
                shutil.copy(source_path, memory_path)
                logger.info(f"Installed memory module to {memory_path}")
            else:
                raise FileNotFoundError(f"Memory module source not found: {source_path}")
        
        # Load the memory module
        try:
            spec = importlib.util.spec_from_file_location("memory", memory_path)
            memory_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(memory_module)
            
            # Initialize the memory component
            self.components["memory"] = memory_module.DeusMemory()
            logger.info("Memory module loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load memory module: {str(e)}")
            # Create a placeholder for the component
            self.components["memory"] = None
            
    def _setup_action_engine(self) -> None:
        """Set up the action engine module"""
        action_path = os.path.join(self.install_dir, "core/action_engine/action_engine.py")
        os.makedirs(os.path.dirname(action_path), exist_ok=True)
        
        # Check if we need to install the action engine
        if not os.path.exists(action_path):
            # Copy the action_engine.py file to the installation directory
            source_path = os.path.join(self.install_dir, "enhanced/action_engine.py")
            if os.path.exists(source_path):
                shutil.copy(source_path, action_path)
                logger.info(f"Installed action engine to {action_path}")
            else:
                raise FileNotFoundError(f"Action engine source not found: {source_path}")
        
        # Load the action engine module
        try:
            spec = importlib.util.spec_from_file_location("action_engine", action_path)
            action_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(action_module)
            
            # Initialize the action engine component
            self.components["action_engine"] = action_module.ActionEngine()
            logger.info("Action engine loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load action engine: {str(e)}")
            # Create a placeholder for the component
            self.components["action_engine"] = None
            
    def _setup_ai_brain(self) -> None:
        """Set up the enhanced AI brain module"""
        brain_path = os.path.join(self.install_dir, "core/vigilance/ai_brain.py")
        
        # Check if we need to update the AI brain module
        if os.path.exists(brain_path):
            # Backup the existing AI brain
            backup_path = f"{brain_path}.bak"
            try:
                shutil.copy(brain_path, backup_path)
                logger.info(f"Backed up original AI brain to {backup_path}")
            except Exception as e:
                logger.error(f"Failed to backup AI brain: {str(e)}")
                return
        
        # Copy the updated AI brain to the installation directory
        source_path = os.path.join(self.install_dir, "enhanced/ai_brain_updated.py")
        if os.path.exists(source_path):
            try:
                shutil.copy(source_path, brain_path)
                logger.info(f"Installed enhanced AI brain to {brain_path}")
            except Exception as e:
                logger.error(f"Failed to install enhanced AI brain: {str(e)}")
        else:
            logger.error(f"Enhanced AI brain source not found: {source_path}")
            
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics and store them"""
        if not self.initialized:
            logger.error("System not initialized, cannot collect metrics")
            return {"success": False, "error": "System not initialized"}
            
        # Get the memory component
        memory = self.components.get("memory")
        if not memory:
            logger.error("Memory component not available")
            return {"success": False, "error": "Memory component not available"}
            
        # Store current metrics
        result = memory.store_current_metrics()
        
        if result:
            return {
                "success": True,
                "message": "Metrics collected and stored successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Failed to collect or store metrics",
                "timestamp": datetime.now().isoformat()
            }
            
    def analyze_system(self) -> Dict[str, Any]:
        """Perform system analysis and return results"""
        if not self.initialized:
            logger.error("System not initialized, cannot analyze")
            return {"success": False, "error": "System not initialized"}
            
        # Get the memory component
        memory = self.components.get("memory")
        if not memory:
            logger.error("Memory component not available")
            return {"success": False, "error": "Memory component not available"}
            
        # Get system summary
        try:
            summary = memory.get_system_summary(days=7)
            
            # Check for anomalies
            has_anomalies = False
            critical_metrics = ["cpu_load", "memory_free_mb", "disk_usage_root"]
            
            for metric in critical_metrics:
                if metric in summary.get("anomalies", {}) and summary["anomalies"][metric].get("anomalies_detected", False):
                    has_anomalies = True
                    
            return {
                "success": True,
                "message": "System analysis completed",
                "has_anomalies": has_anomalies,
                "overall_health": summary.get("overall_health", 0),
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"System analysis failed: {str(e)}")
            return {
                "success": False,
                "error": f"System analysis failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            
    def execute_remediation(self, issue_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an automated remediation based on issue type"""
        if not self.initialized:
            logger.error("System not initialized, cannot execute remediation")
            return {"success": False, "error": "System not initialized"}
            
        # Get the action engine component
        action_engine = self.components.get("action_engine")
        if not action_engine:
            logger.error("Action engine component not available")
            return {"success": False, "error": "Action engine component not available"}
            
        if not params:
            params = {}
            
        # Map issue types to actions
        action_map = {
            "high_cpu": "clear_memory_caches",
            "low_memory": "clear_memory_caches",
            "disk_space": "clean_temp_files",
            "log_growth": "clean_log_files",
            "suspicious_auth": "check_service_status",  # Conservative approach
            "suspicious_network": "check_open_ports"     # Conservative approach
        }
        
        if issue_type not in action_map:
            return {
                "success": False,
                "error": f"Unknown issue type: {issue_type}"
            }
            
        # Get the action to execute
        action_name = action_map[issue_type]
        
        # Add default parameters if needed
        if action_name == "check_service_status" and "service_name" not in params:
            params["service_name"] = "sshd"  # Default service to check
            
        # Execute the action
        logger.info(f"Executing remediation {action_name} for issue {issue_type}")
        result = action_engine.execute_action(action_name, params)
        
        # Log the result
        if result.get("success", False):
            logger.info(f"Remediation successful: {result.get('message', '')}")
        else:
            logger.error(f"Remediation failed: {result.get('error', '')}")
            
        return result
        
    def run_integration_cycle(self) -> Dict[str, Any]:
        """Run a complete integration cycle"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        # Step 1: Collect metrics
        results["steps"]["collect_metrics"] = self.collect_metrics()
        
        # Step 2: Analyze system
        analysis = self.analyze_system()
        results["steps"]["analyze_system"] = analysis
        
        # Step 3: Execute remediations if needed
        if analysis.get("success", False) and analysis.get("has_anomalies", False):
            # Get anomalies from the analysis
            anomalies = analysis.get("summary", {}).get("anomalies", {})
            remediation_results = []
            
            # Check for CPU issues
            if "cpu_load" in anomalies and anomalies["cpu_load"].get("anomalies_detected", False):
                cpu_result = self.execute_remediation("high_cpu")
                remediation_results.append({"issue": "high_cpu", "result": cpu_result})
                
            # Check for memory issues
            if "memory_free_mb" in anomalies and anomalies["memory_free_mb"].get("anomalies_detected", False):
                memory_result = self.execute_remediation("low_memory")
                remediation_results.append({"issue": "low_memory", "result": memory_result})
                
            # Check for disk issues
            if "disk_usage_root" in anomalies and anomalies["disk_usage_root"].get("anomalies_detected", False):
                disk_result = self.execute_remediation("disk_space")
                remediation_results.append({"issue": "disk_space", "result": disk_result})
                
            results["steps"]["remediation"] = remediation_results
            
        # Return the complete results
        results["success"] = all(step.get("success", False) for step in results["steps"].values())
        
        return results
        
    def monitor_continuously(self, interval_seconds: int = 600) -> None:
        """Run continuous monitoring in a loop"""
        logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")
        
        try:
            while True:
                try:
                    results = self.run_integration_cycle()
                    success = results.get("success", False)
                    logger.info(f"Integration cycle completed (success: {success})")
                except Exception as e:
                    logger.error(f"Error in integration cycle: {str(e)}")
                    
                # Sleep until next cycle
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring stopped due to error: {str(e)}")
            
    def enhance_bash_scripts(self) -> Dict[str, Any]:
        """Enhance the bash scripts to integrate with the new components"""
        results = {}
        
        # Enhance the breath script to log to the database
        breath_script = os.path.join(self.install_dir, "core/breath/breath.sh")
        if os.path.exists(breath_script):
            backup_path = f"{breath_script}.bak"
            shutil.copy(breath_script, backup_path)
            
            # Add a line to call our memory module at the end
            integration_line = '\n# Call memory module after completing checks\n'
            integration_line += 'python3 "$PROJECT_ROOT/core/memory/memory.py"\n'
            
            with open(breath_script, 'r') as f:
                content = f.read()
                
            # Find the end of the script (just before the last line)
            if "main" in content:
                # Insert just before the "main" call at the end
                modified_content = content.replace("# Run main function\nmain", integration_line + "# Run main function\nmain")
                
                with open(breath_script, 'w') as f:
                    f.write(modified_content)
                    
                results["breath_script"] = {
                    "modified": True,
                    "backup": backup_path
                }
            else:
                results["breath_script"] = {
                    "modified": False,
                    "error": "Could not locate insertion point"
                }
                
        # Return the results
        return results
        
def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="DeusExMachina Integration Controller")
    
    # Set up subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up the enhanced system")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze the system")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start continuous monitoring")
    monitor_parser.add_argument("--interval", type=int, default=600, 
                              help="Monitoring interval in seconds")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install components")
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create the controller
    deus = DeusExMachina()
    
    if args.command == "setup":
        success = deus.setup()
        if success:
            print("Setup completed successfully")
        else:
            print("Setup failed, see log for details")
            sys.exit(1)
            
    elif args.command == "analyze":
        success = deus.setup()
        if success:
            results = deus.analyze_system()
            print(json.dumps(results, indent=2))
        else:
            print("Setup failed, cannot analyze")
            sys.exit(1)
            
    elif args.command == "monitor":
        success = deus.setup()
        if success:
            deus.monitor_continuously(args.interval)
        else:
            print("Setup failed, cannot start monitoring")
            sys.exit(1)
            
    elif args.command == "install":
        success = deus.setup()
        if success:
            # Enhance bash scripts
            results = deus.enhance_bash_scripts()
            print(json.dumps(results, indent=2))
        else:
            print("Setup failed, cannot install components")
            sys.exit(1)
            
    else:
        # If no command specified, print usage
        print("No command specified. Use --help for usage information.")
        sys.exit(1)

if __name__ == "__main__":
    main()