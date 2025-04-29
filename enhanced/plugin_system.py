#!/usr/bin/env python3
# plugin_system.py - Plugin architecture for Deus Ex Machina
# Part of the Phase 4 Modular Expansion implementation

import os
import sys
import json
import logging
import importlib
import importlib.util
import inspect
import hashlib
import time
import traceback
import uuid
import re
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Type
from abc import ABC, abstractmethod

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import configuration
try:
    from config.config import LOG_DIR, INSTALL_DIR
except ImportError:
    # Fallback configuration
    LOG_DIR = "/var/log/deus-ex-machina"
    INSTALL_DIR = "/opt/deus-ex-machina"

# Set up paths for plugins
PLUGINS_DIR = os.path.join(INSTALL_DIR, "plugins")
PLUGIN_CONFIG_DIR = os.path.join(INSTALL_DIR, "config/plugins")
SANDBOX_DIR = os.path.join(INSTALL_DIR, "sandbox")

# Set up logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "plugin_system.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PluginSystem")

# Plugin metadata file name
METADATA_FILENAME = "plugin_metadata.json"

# Create required directories
os.makedirs(PLUGINS_DIR, exist_ok=True)
os.makedirs(PLUGIN_CONFIG_DIR, exist_ok=True)
os.makedirs(SANDBOX_DIR, exist_ok=True)

class DeusPlugin(ABC):
    """Abstract base class for all plugins"""
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize the plugin with given context"""
        pass
        
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin's main functionality"""
        pass
        
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        pass
        
    @abstractmethod
    def cleanup(self) -> bool:
        """Clean up any resources used by the plugin"""
        pass

class PluginManager:
    """Manages the plugin system for Deus Ex Machina"""
    
    def __init__(self, plugins_dir: str = PLUGINS_DIR, 
                config_dir: str = PLUGIN_CONFIG_DIR):
        """Initialize the plugin manager"""
        self.plugins_dir = plugins_dir
        self.config_dir = config_dir
        self.loaded_plugins = {}
        self.plugin_metadata = {}
        self.last_scan_time = 0
        
        # Ensure directories exist
        os.makedirs(self.plugins_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        logger.info(f"Plugin system initialized (plugins: {plugins_dir}, config: {config_dir})")
        
    def scan_plugins(self, force_reload: bool = False) -> Dict[str, Any]:
        """Scan for available plugins and load their metadata"""
        current_time = time.time()
        
        # Skip if we've scanned recently, unless forced
        if not force_reload and current_time - self.last_scan_time < 60:
            return {
                "success": True,
                "message": "Using cached plugin data",
                "plugins": list(self.plugin_metadata.values())
            }
            
        try:
            self.last_scan_time = current_time
            found_plugins = []
            
            # List all subdirectories in the plugins directory
            for plugin_name in os.listdir(self.plugins_dir):
                plugin_path = os.path.join(self.plugins_dir, plugin_name)
                
                # Skip if not a directory
                if not os.path.isdir(plugin_path):
                    continue
                    
                # Check for metadata file
                metadata_path = os.path.join(plugin_path, METADATA_FILENAME)
                if not os.path.exists(metadata_path):
                    logger.warning(f"Plugin '{plugin_name}' missing metadata file")
                    continue
                    
                # Load metadata
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        
                    # Add plugin path to metadata
                    metadata["plugin_path"] = plugin_path
                    metadata["plugin_id"] = plugin_name
                    
                    # Verify required fields
                    required_fields = ["name", "version", "description", "main_module", "main_class"]
                    missing_fields = [field for field in required_fields if field not in metadata]
                    
                    if missing_fields:
                        logger.warning(f"Plugin '{plugin_name}' metadata missing fields: {missing_fields}")
                        continue
                        
                    # Verify main module exists
                    main_module = metadata["main_module"]
                    main_module_path = os.path.join(plugin_path, main_module)
                    
                    if not os.path.exists(main_module_path):
                        logger.warning(f"Plugin '{plugin_name}' main module not found: {main_module}")
                        continue
                        
                    # Add additional metadata
                    metadata["loaded"] = plugin_name in self.loaded_plugins
                    metadata["enabled"] = self._is_plugin_enabled(plugin_name)
                    
                    # Store metadata
                    self.plugin_metadata[plugin_name] = metadata
                    found_plugins.append(metadata)
                    
                except Exception as e:
                    logger.error(f"Error loading plugin '{plugin_name}' metadata: {str(e)}")
                    continue
                    
            return {
                "success": True,
                "message": f"Found {len(found_plugins)} plugins",
                "plugins": found_plugins,
                "scan_time": current_time
            }
        except Exception as e:
            logger.error(f"Error scanning plugins: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def load_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Load a specific plugin by ID"""
        try:
            # Check if already loaded
            if plugin_id in self.loaded_plugins:
                return {
                    "success": True,
                    "message": f"Plugin '{plugin_id}' already loaded",
                    "plugin": self.plugin_metadata.get(plugin_id)
                }
                
            # Check if plugin exists
            if plugin_id not in self.plugin_metadata:
                # Scan plugins first
                self.scan_plugins(force_reload=True)
                
                if plugin_id not in self.plugin_metadata:
                    return {
                        "success": False,
                        "error": f"Plugin '{plugin_id}' not found"
                    }
                    
            # Get metadata
            metadata = self.plugin_metadata[plugin_id]
            plugin_path = metadata["plugin_path"]
            main_module = metadata["main_module"]
            main_class = metadata["main_class"]
            
            # Build module name
            module_path = os.path.join(plugin_path, main_module)
            module_name = f"deus_plugin_{plugin_id}"
            
            # Check if plugin is enabled
            if not self._is_plugin_enabled(plugin_id):
                return {
                    "success": False,
                    "error": f"Plugin '{plugin_id}' is disabled"
                }
                
            # Load module
            try:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if not spec:
                    return {
                        "success": False,
                        "error": f"Could not load module spec for '{plugin_id}'"
                    }
                    
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Get the plugin class
                if not hasattr(module, main_class):
                    return {
                        "success": False,
                        "error": f"Main class '{main_class}' not found in plugin '{plugin_id}'"
                    }
                    
                plugin_class = getattr(module, main_class)
                
                # Verify it's a DeusPlugin subclass
                if not issubclass(plugin_class, DeusPlugin):
                    return {
                        "success": False,
                        "error": f"Plugin '{plugin_id}' does not inherit from DeusPlugin"
                    }
                    
                # Instantiate the plugin
                plugin_instance = plugin_class()
                
                # Get configuration for the plugin
                config = self._load_plugin_config(plugin_id)
                
                # Initialize the plugin
                context = {
                    "config": config,
                    "plugin_id": plugin_id,
                    "plugin_path": plugin_path,
                    "log_dir": os.path.join(LOG_DIR, f"plugin_{plugin_id}")
                }
                
                # Create log directory for plugin
                os.makedirs(context["log_dir"], exist_ok=True)
                
                # Initialize the plugin
                if not plugin_instance.initialize(context):
                    return {
                        "success": False,
                        "error": f"Plugin '{plugin_id}' initialization failed"
                    }
                    
                # Store the loaded plugin
                self.loaded_plugins[plugin_id] = plugin_instance
                
                # Update metadata
                self.plugin_metadata[plugin_id]["loaded"] = True
                
                return {
                    "success": True,
                    "message": f"Plugin '{plugin_id}' loaded successfully",
                    "plugin": self.plugin_metadata[plugin_id]
                }
                
            except Exception as e:
                logger.error(f"Error loading plugin '{plugin_id}': {str(e)}")
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error": f"Error loading plugin '{plugin_id}': {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Unexpected error loading plugin '{plugin_id}': {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def unload_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Unload a specific plugin by ID"""
        try:
            # Check if plugin is loaded
            if plugin_id not in self.loaded_plugins:
                return {
                    "success": False,
                    "error": f"Plugin '{plugin_id}' is not loaded"
                }
                
            # Get plugin instance
            plugin = self.loaded_plugins[plugin_id]
            
            # Call cleanup method
            try:
                plugin.cleanup()
            except Exception as e:
                logger.warning(f"Error during plugin '{plugin_id}' cleanup: {str(e)}")
                
            # Remove from loaded plugins
            del self.loaded_plugins[plugin_id]
            
            # Update metadata
            if plugin_id in self.plugin_metadata:
                self.plugin_metadata[plugin_id]["loaded"] = False
                
            # Remove module from sys.modules
            module_name = f"deus_plugin_{plugin_id}"
            if module_name in sys.modules:
                del sys.modules[module_name]
                
            return {
                "success": True,
                "message": f"Plugin '{plugin_id}' unloaded successfully"
            }
        except Exception as e:
            logger.error(f"Error unloading plugin '{plugin_id}': {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def execute_plugin(self, plugin_id: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a plugin with the provided parameters"""
        if not params:
            params = {}
            
        try:
            # Check if plugin is loaded
            if plugin_id not in self.loaded_plugins:
                # Try to load it
                load_result = self.load_plugin(plugin_id)
                if not load_result["success"]:
                    return load_result
                    
            # Get plugin instance
            plugin = self.loaded_plugins[plugin_id]
            
            # Execute the plugin
            start_time = time.time()
            
            try:
                result = plugin.execute(params)
                
                # Calculate execution time
                execution_time = time.time() - start_time
                
                # Add execution metadata
                result["execution_time"] = execution_time
                result["executed_at"] = datetime.now().isoformat()
                result["plugin_id"] = plugin_id
                
                return result
            except Exception as e:
                logger.error(f"Error executing plugin '{plugin_id}': {str(e)}")
                logger.error(traceback.format_exc())
                
                return {
                    "success": False,
                    "error": f"Error executing plugin '{plugin_id}': {str(e)}",
                    "execution_time": time.time() - start_time,
                    "executed_at": datetime.now().isoformat(),
                    "plugin_id": plugin_id
                }
                
        except Exception as e:
            logger.error(f"Unexpected error executing plugin '{plugin_id}': {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _is_plugin_enabled(self, plugin_id: str) -> bool:
        """Check if a plugin is enabled"""
        # Check for disable file
        disable_file = os.path.join(self.config_dir, f"{plugin_id}.disabled")
        return not os.path.exists(disable_file)
        
    def _load_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """Load configuration for a plugin"""
        config_file = os.path.join(self.config_dir, f"{plugin_id}.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config for plugin '{plugin_id}': {str(e)}")
                
        # Return empty config if file doesn't exist or has an error
        return {}
        
    def _save_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Save configuration for a plugin"""
        config_file = os.path.join(self.config_dir, f"{plugin_id}.json")
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving config for plugin '{plugin_id}': {str(e)}")
            return False
            
    def enable_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Enable a plugin"""
        # Check if plugin exists
        if plugin_id not in self.plugin_metadata:
            self.scan_plugins(force_reload=True)
            if plugin_id not in self.plugin_metadata:
                return {
                    "success": False,
                    "error": f"Plugin '{plugin_id}' not found"
                }
                
        # Remove disable file if it exists
        disable_file = os.path.join(self.config_dir, f"{plugin_id}.disabled")
        if os.path.exists(disable_file):
            try:
                os.remove(disable_file)
            except Exception as e:
                logger.error(f"Error enabling plugin '{plugin_id}': {str(e)}")
                return {
                    "success": False,
                    "error": f"Error enabling plugin '{plugin_id}': {str(e)}"
                }
                
        # Update metadata
        if plugin_id in self.plugin_metadata:
            self.plugin_metadata[plugin_id]["enabled"] = True
            
        return {
            "success": True,
            "message": f"Plugin '{plugin_id}' enabled"
        }
        
    def disable_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Disable a plugin"""
        # Check if plugin exists
        if plugin_id not in self.plugin_metadata:
            self.scan_plugins(force_reload=True)
            if plugin_id not in self.plugin_metadata:
                return {
                    "success": False,
                    "error": f"Plugin '{plugin_id}' not found"
                }
                
        # Unload plugin if it's loaded
        if plugin_id in self.loaded_plugins:
            self.unload_plugin(plugin_id)
            
        # Create disable file
        disable_file = os.path.join(self.config_dir, f"{plugin_id}.disabled")
        try:
            with open(disable_file, 'w') as f:
                f.write(f"Disabled at {datetime.now().isoformat()}")
        except Exception as e:
            logger.error(f"Error disabling plugin '{plugin_id}': {str(e)}")
            return {
                "success": False,
                "error": f"Error disabling plugin '{plugin_id}': {str(e)}"
            }
            
        # Update metadata
        if plugin_id in self.plugin_metadata:
            self.plugin_metadata[plugin_id]["enabled"] = False
            
        return {
            "success": True,
            "message": f"Plugin '{plugin_id}' disabled"
        }
        
    def install_plugin(self, source_path: str, plugin_id: str = None) -> Dict[str, Any]:
        """Install a plugin from a directory or ZIP file"""
        try:
            # Generate plugin ID if not provided
            if not plugin_id:
                plugin_id = self._generate_plugin_id(source_path)
                
            # Validate plugin ID
            if not re.match(r'^[a-zA-Z0-9_-]+$', plugin_id):
                return {
                    "success": False,
                    "error": "Invalid plugin ID (only alphanumeric, underscore, and hyphen allowed)"
                }
                
            # Check if plugin already exists
            if os.path.exists(os.path.join(self.plugins_dir, plugin_id)):
                return {
                    "success": False,
                    "error": f"Plugin with ID '{plugin_id}' already exists"
                }
                
            # Determine source type (directory or ZIP)
            is_zip = source_path.lower().endswith('.zip')
            
            # Create target directory
            target_path = os.path.join(self.plugins_dir, plugin_id)
            os.makedirs(target_path, exist_ok=True)
            
            # Copy or extract files
            if is_zip:
                # Extract ZIP file
                import zipfile
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(target_path)
            else:
                # Copy directory contents
                for item in os.listdir(source_path):
                    s = os.path.join(source_path, item)
                    d = os.path.join(target_path, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
                        
            # Verify plugin structure
            metadata_path = os.path.join(target_path, METADATA_FILENAME)
            if not os.path.exists(metadata_path):
                # Cleanup
                shutil.rmtree(target_path)
                return {
                    "success": False,
                    "error": f"Invalid plugin: metadata file '{METADATA_FILENAME}' not found"
                }
                
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            # Verify main module exists
            main_module = metadata.get("main_module")
            if not main_module or not os.path.exists(os.path.join(target_path, main_module)):
                # Cleanup
                shutil.rmtree(target_path)
                return {
                    "success": False,
                    "error": f"Invalid plugin: main module '{main_module}' not found"
                }
                
            # Refresh plugin list
            self.scan_plugins(force_reload=True)
            
            return {
                "success": True,
                "message": f"Plugin '{plugin_id}' installed successfully",
                "plugin": self.plugin_metadata.get(plugin_id)
            }
        except Exception as e:
            logger.error(f"Error installing plugin: {str(e)}")
            # Cleanup if target path was created
            if 'target_path' in locals() and os.path.exists(target_path):
                shutil.rmtree(target_path)
                
            return {
                "success": False,
                "error": f"Error installing plugin: {str(e)}"
            }
            
    def uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Uninstall a plugin"""
        try:
            # Check if plugin exists
            plugin_path = os.path.join(self.plugins_dir, plugin_id)
            if not os.path.exists(plugin_path):
                return {
                    "success": False,
                    "error": f"Plugin '{plugin_id}' not found"
                }
                
            # Unload plugin if it's loaded
            if plugin_id in self.loaded_plugins:
                self.unload_plugin(plugin_id)
                
            # Remove plugin directory
            shutil.rmtree(plugin_path)
            
            # Remove configuration
            config_file = os.path.join(self.config_dir, f"{plugin_id}.json")
            if os.path.exists(config_file):
                os.remove(config_file)
                
            # Remove disable file if it exists
            disable_file = os.path.join(self.config_dir, f"{plugin_id}.disabled")
            if os.path.exists(disable_file):
                os.remove(disable_file)
                
            # Remove from metadata
            if plugin_id in self.plugin_metadata:
                del self.plugin_metadata[plugin_id]
                
            return {
                "success": True,
                "message": f"Plugin '{plugin_id}' uninstalled successfully"
            }
        except Exception as e:
            logger.error(f"Error uninstalling plugin '{plugin_id}': {str(e)}")
            return {
                "success": False,
                "error": f"Error uninstalling plugin '{plugin_id}': {str(e)}"
            }
            
    def _generate_plugin_id(self, source_path: str) -> str:
        """Generate a plugin ID from the source path"""
        # Get basename without extension
        basename = os.path.basename(source_path)
        if basename.lower().endswith('.zip'):
            basename = os.path.splitext(basename)[0]
            
        # Clean up name
        plugin_id = re.sub(r'[^a-zA-Z0-9_-]', '_', basename.lower())
        
        # Ensure it's not empty
        if not plugin_id:
            plugin_id = f"plugin_{int(time.time())}"
            
        return plugin_id
        
    def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        """Get detailed information about a plugin"""
        try:
            # Check if plugin exists
            if plugin_id not in self.plugin_metadata:
                self.scan_plugins(force_reload=True)
                if plugin_id not in self.plugin_metadata:
                    return {
                        "success": False,
                        "error": f"Plugin '{plugin_id}' not found"
                    }
                    
            # Get basic metadata
            info = dict(self.plugin_metadata[plugin_id])
            
            # Add status information
            info["loaded"] = plugin_id in self.loaded_plugins
            info["enabled"] = self._is_plugin_enabled(plugin_id)
            
            # Get configuration
            info["config"] = self._load_plugin_config(plugin_id)
            
            # Get plugin files
            plugin_path = info["plugin_path"]
            files = []
            
            for root, dirs, filenames in os.walk(plugin_path):
                rel_path = os.path.relpath(root, plugin_path)
                if rel_path == '.':
                    rel_path = ''
                    
                for filename in filenames:
                    file_path = os.path.join(rel_path, filename)
                    files.append(file_path)
                    
            info["files"] = sorted(files)
            
            # If plugin is loaded, get runtime metadata
            if plugin_id in self.loaded_plugins:
                try:
                    runtime_metadata = self.loaded_plugins[plugin_id].get_metadata()
                    info["runtime_metadata"] = runtime_metadata
                except Exception as e:
                    logger.warning(f"Error getting runtime metadata for plugin '{plugin_id}': {str(e)}")
                    info["runtime_metadata_error"] = str(e)
                    
            return {
                "success": True,
                "plugin": info
            }
        except Exception as e:
            logger.error(f"Error getting plugin info for '{plugin_id}': {str(e)}")
            return {
                "success": False,
                "error": f"Error getting plugin info: {str(e)}"
            }
            
    def update_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration for a plugin"""
        try:
            # Check if plugin exists
            if plugin_id not in self.plugin_metadata:
                self.scan_plugins(force_reload=True)
                if plugin_id not in self.plugin_metadata:
                    return {
                        "success": False,
                        "error": f"Plugin '{plugin_id}' not found"
                    }
                    
            # Save configuration
            if not self._save_plugin_config(plugin_id, config):
                return {
                    "success": False,
                    "error": f"Error saving configuration for plugin '{plugin_id}'"
                }
                
            # If plugin is loaded, reload it
            if plugin_id in self.loaded_plugins:
                self.unload_plugin(plugin_id)
                self.load_plugin(plugin_id)
                
            return {
                "success": True,
                "message": f"Configuration for plugin '{plugin_id}' updated successfully"
            }
        except Exception as e:
            logger.error(f"Error updating plugin config for '{plugin_id}': {str(e)}")
            return {
                "success": False,
                "error": f"Error updating plugin config: {str(e)}"
            }
            
class BackupRestorePlugin(DeusPlugin):
    """Example plugin for backup and restore functionality"""
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize the plugin with given context"""
        self.context = context
        self.plugin_id = context["plugin_id"]
        self.plugin_path = context["plugin_path"]
        self.log_dir = context["log_dir"]
        self.config = context["config"]
        
        # Set up logging
        log_file = os.path.join(self.log_dir, "backup_restore.log")
        self.logger = logging.getLogger(f"Plugin.{self.plugin_id}")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.logger.info(f"Backup/Restore plugin initialized: {self.plugin_id}")
        return True
        
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin's main functionality"""
        self.logger.info(f"Executing with params: {params}")
        
        action = params.get("action")
        
        if action == "backup":
            return self._execute_backup(params)
        elif action == "restore":
            return self._execute_restore(params)
        elif action == "list":
            return self._list_backups(params)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "valid_actions": ["backup", "restore", "list"]
            }
            
    def _execute_backup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a backup operation"""
        target_dir = params.get("target_dir", os.path.join(self.log_dir, "backups"))
        source_dirs = params.get("source_dirs", ["/etc", "/var/log/deus-ex-machina"])
        
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Generate backup name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.tar.gz"
        backup_path = os.path.join(target_dir, backup_name)
        
        try:
            # Create temporary directory for backup
            temp_dir = os.path.join("/tmp", f"deus_backup_{timestamp}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Copy files to temporary directory
            for source_dir in source_dirs:
                if os.path.exists(source_dir):
                    target_subdir = os.path.join(temp_dir, os.path.basename(source_dir))
                    os.makedirs(target_subdir, exist_ok=True)
                    
                    # Use rsync if available
                    try:
                        subprocess.run(
                            ["rsync", "-a", f"{source_dir}/", f"{target_subdir}/"],
                            check=True, capture_output=True, text=True
                        )
                    except (subprocess.SubprocessError, FileNotFoundError):
                        # Fallback to cp
                        for root, dirs, files in os.walk(source_dir):
                            rel_path = os.path.relpath(root, source_dir)
                            target_path = os.path.join(target_subdir, rel_path)
                            os.makedirs(target_path, exist_ok=True)
                            
                            for file in files:
                                try:
                                    shutil.copy2(
                                        os.path.join(root, file),
                                        os.path.join(target_path, file)
                                    )
                                except (shutil.Error, OSError):
                                    pass
                                    
            # Create tar archive
            subprocess.run(
                ["tar", "-czf", backup_path, "-C", "/tmp", f"deus_backup_{timestamp}"],
                check=True, capture_output=True, text=True
            )
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            self.logger.info(f"Backup created: {backup_path}")
            
            return {
                "success": True,
                "message": f"Backup created successfully: {backup_name}",
                "backup_path": backup_path,
                "timestamp": timestamp,
                "source_dirs": source_dirs
            }
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating backup: {str(e)}"
            }
            
    def _execute_restore(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a restore operation"""
        backup_path = params.get("backup_path")
        
        if not backup_path:
            return {
                "success": False,
                "error": "Backup path not provided"
            }
            
        if not os.path.exists(backup_path):
            return {
                "success": False,
                "error": f"Backup not found: {backup_path}"
            }
            
        try:
            # Create temporary directory for extraction
            temp_dir = os.path.join("/tmp", f"deus_restore_{int(time.time())}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Extract archive
            subprocess.run(
                ["tar", "-xzf", backup_path, "-C", temp_dir],
                check=True, capture_output=True, text=True
            )
            
            # Find the extracted backup directory
            backup_dir = None
            for item in os.listdir(temp_dir):
                if os.path.isdir(os.path.join(temp_dir, item)):
                    backup_dir = os.path.join(temp_dir, item)
                    break
                    
            if not backup_dir:
                return {
                    "success": False,
                    "error": "Invalid backup archive structure"
                }
                
            # Restore files
            restored_dirs = []
            
            for item in os.listdir(backup_dir):
                source_path = os.path.join(backup_dir, item)
                if os.path.isdir(source_path):
                    target_path = os.path.join("/", item)
                    
                    if os.path.exists(target_path):
                        # Create backup of existing directory
                        backup = os.path.join(temp_dir, f"{item}_original")
                        shutil.copytree(target_path, backup)
                        
                        # Use rsync to restore
                        try:
                            subprocess.run(
                                ["rsync", "-a", f"{source_path}/", f"{target_path}/"],
                                check=True, capture_output=True, text=True
                            )
                            restored_dirs.append(target_path)
                        except (subprocess.SubprocessError, FileNotFoundError):
                            # Fallback to manual restore
                            for root, dirs, files in os.walk(source_path):
                                rel_path = os.path.relpath(root, source_path)
                                restore_path = os.path.join(target_path, rel_path)
                                os.makedirs(restore_path, exist_ok=True)
                                
                                for file in files:
                                    try:
                                        shutil.copy2(
                                            os.path.join(root, file),
                                            os.path.join(restore_path, file)
                                        )
                                    except (shutil.Error, OSError):
                                        pass
                                        
                            restored_dirs.append(target_path)
                            
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            self.logger.info(f"Restore completed from: {backup_path}")
            
            return {
                "success": True,
                "message": f"Restore completed successfully from: {os.path.basename(backup_path)}",
                "restored_dirs": restored_dirs
            }
        except Exception as e:
            self.logger.error(f"Error restoring backup: {str(e)}")
            return {
                "success": False,
                "error": f"Error restoring backup: {str(e)}"
            }
            
    def _list_backups(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available backups"""
        backup_dir = params.get("backup_dir", os.path.join(self.log_dir, "backups"))
        
        if not os.path.exists(backup_dir):
            return {
                "success": True,
                "message": "No backups found",
                "backups": []
            }
            
        try:
            backups = []
            
            for item in os.listdir(backup_dir):
                if item.startswith("backup_") and item.endswith(".tar.gz"):
                    backup_path = os.path.join(backup_dir, item)
                    
                    # Get file stats
                    stats = os.stat(backup_path)
                    
                    # Extract timestamp from filename
                    timestamp_str = item[7:-7]  # Remove "backup_" and ".tar.gz"
                    
                    backups.append({
                        "name": item,
                        "path": backup_path,
                        "size": stats.st_size,
                        "created": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                        "timestamp": timestamp_str
                    })
                    
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
            return {
                "success": True,
                "message": f"Found {len(backups)} backups",
                "backups": backups,
                "backup_dir": backup_dir
            }
        except Exception as e:
            self.logger.error(f"Error listing backups: {str(e)}")
            return {
                "success": False,
                "error": f"Error listing backups: {str(e)}"
            }
            
    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        return {
            "name": "Backup/Restore Plugin",
            "version": "1.0.0",
            "description": "Provides backup and restore functionality for Deus Ex Machina",
            "author": "Claude",
            "status": "active",
            "config": self.config
        }
        
    def cleanup(self) -> bool:
        """Clean up any resources used by the plugin"""
        self.logger.info("Backup/Restore plugin cleanup")
        return True

class NetworkMonitorPlugin(DeusPlugin):
    """Example plugin for network monitoring"""
    
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize the plugin with given context"""
        self.context = context
        self.plugin_id = context["plugin_id"]
        self.plugin_path = context["plugin_path"]
        self.log_dir = context["log_dir"]
        self.config = context["config"]
        
        # Set up logging
        log_file = os.path.join(self.log_dir, "network_monitor.log")
        self.logger = logging.getLogger(f"Plugin.{self.plugin_id}")
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Initialize connection tracking
        self.connections_file = os.path.join(self.log_dir, "connections.json")
        self.unusual_connections_file = os.path.join(self.log_dir, "unusual_connections.json")
        
        # Create files if they don't exist
        for f in [self.connections_file, self.unusual_connections_file]:
            if not os.path.exists(f):
                with open(f, 'w') as file:
                    json.dump({}, file)
                    
        self.logger.info(f"Network Monitor plugin initialized: {self.plugin_id}")
        return True
        
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin's main functionality"""
        self.logger.info(f"Executing with params: {params}")
        
        action = params.get("action", "scan")
        
        if action == "scan":
            return self._scan_network(params)
        elif action == "analyze":
            return self._analyze_connections(params)
        elif action == "history":
            return self._connection_history(params)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "valid_actions": ["scan", "analyze", "history"]
            }
            
    def _scan_network(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scan network connections"""
        try:
            # Check open connections with ss or netstat
            try:
                # Try ss command first
                result = subprocess.run(
                    ["ss", "-tunap"],
                    check=True, capture_output=True, text=True
                )
                output = result.stdout
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fall back to netstat
                result = subprocess.run(
                    ["netstat", "-tunap"],
                    check=True, capture_output=True, text=True
                )
                output = result.stdout
                
            # Parse the output
            connections = self._parse_connections(output)
            
            # Save connections to history
            self._save_connections(connections)
            
            # Find unusual connections
            unusual = self._find_unusual_connections(connections)
            
            return {
                "success": True,
                "message": f"Scanned {len(connections)} network connections",
                "connections": connections,
                "unusual_connections": unusual,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error scanning network: {str(e)}")
            return {
                "success": False,
                "error": f"Error scanning network: {str(e)}"
            }
            
    def _parse_connections(self, output: str) -> List[Dict[str, Any]]:
        """Parse the output of ss or netstat commands"""
        connections = []
        
        # Regular expressions for different connection details
        ip_port_re = re.compile(r'(\d+\.\d+\.\d+\.\d+):(\d+)')
        
        for line in output.splitlines():
            # Skip header lines
            if not line or line.startswith('Netid') or line.startswith('Proto'):
                continue
                
            # Extract information
            fields = line.split()
            if len(fields) < 5:
                continue
                
            proto = fields[0]
            
            # Identify local and remote addresses
            local_addr = ""
            local_port = ""
            remote_addr = ""
            remote_port = ""
            
            if 'ss' in line:  # ss output format
                local_match = ip_port_re.search(fields[4])
                remote_match = ip_port_re.search(fields[5])
            else:  # netstat output format
                local_match = ip_port_re.search(fields[3])
                remote_match = ip_port_re.search(fields[4])
                
            if local_match:
                local_addr = local_match.group(1)
                local_port = local_match.group(2)
                
            if remote_match:
                remote_addr = remote_match.group(1)
                remote_port = remote_match.group(2)
                
            # Get state and process (if available)
            state = ""
            process = ""
            
            for field in fields:
                if field in ["LISTEN", "ESTABLISHED", "TIME_WAIT", "CLOSE_WAIT"]:
                    state = field
                if "pid=" in field or "users:" in field:
                    process = field
                    
            connections.append({
                "protocol": proto,
                "local_addr": local_addr,
                "local_port": local_port,
                "remote_addr": remote_addr,
                "remote_port": remote_port,
                "state": state,
                "process": process,
                "timestamp": datetime.now().isoformat()
            })
            
        return connections
        
    def _save_connections(self, connections: List[Dict[str, Any]]) -> None:
        """Save connections to history"""
        # Load existing connections
        try:
            with open(self.connections_file, 'r') as f:
                history = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            history = {}
            
        # Add new connections
        timestamp = datetime.now().isoformat()
        history[timestamp] = connections
        
        # Keep only the last 100 scans
        if len(history) > 100:
            # Sort by timestamp and keep only the most recent
            items = sorted(history.items(), key=lambda x: x[0], reverse=True)
            history = dict(items[:100])
            
        # Save back to file
        with open(self.connections_file, 'w') as f:
            json.dump(history, f)
            
    def _find_unusual_connections(self, connections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find unusual connections based on history and known patterns"""
        unusual = []
        
        # Load known connection patterns
        known_patterns = self.config.get("known_patterns", [])
        
        # Common ports to ignore (SSH, DNS, HTTP, HTTPS, etc.)
        common_ports = [
            "22", "53", "80", "443", "25", "587", "993", "995",
            "143", "8080", "8443", "3306", "5432", "27017"
        ]
        
        for conn in connections:
            is_unusual = False
            reason = ""
            
            # Check for non-standard ports
            if (conn["state"] == "LISTEN" and 
                conn["local_port"] not in common_ports and
                not any(conn["local_port"] == p.get("port") for p in known_patterns)):
                is_unusual = True
                reason = f"Unusual listening port: {conn['local_port']}"
                
            # Check for suspicious remote addresses
            elif (conn["state"] == "ESTABLISHED" and
                 not any(conn["remote_addr"] == p.get("addr") for p in known_patterns)):
                # Check for private IP ranges
                if not (conn["remote_addr"].startswith("10.") or
                       conn["remote_addr"].startswith("192.168.") or
                       conn["remote_addr"].startswith("127.") or
                       conn["remote_addr"].startswith("172.")):
                    is_unusual = True
                    reason = f"Connection to external IP: {conn['remote_addr']}"
                    
            if is_unusual:
                unusual_conn = dict(conn)
                unusual_conn["reason"] = reason
                unusual.append(unusual_conn)
                
                # Save to unusual connections file
                self._save_unusual_connection(unusual_conn)
                
        return unusual
        
    def _save_unusual_connection(self, connection: Dict[str, Any]) -> None:
        """Save unusual connection to file"""
        try:
            with open(self.unusual_connections_file, 'r') as f:
                unusual = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            unusual = {}
            
        # Add new unusual connection
        timestamp = datetime.now().isoformat()
        
        # Use connection details as key to avoid duplicates
        key = f"{connection['protocol']}_{connection['local_addr']}:{connection['local_port']}"
        key += f"_{connection['remote_addr']}:{connection['remote_port']}"
        
        unusual[key] = {
            "connection": connection,
            "first_seen": unusual.get(key, {}).get("first_seen", timestamp),
            "last_seen": timestamp,
            "count": unusual.get(key, {}).get("count", 0) + 1
        }
        
        # Save back to file
        with open(self.unusual_connections_file, 'w') as f:
            json.dump(unusual, f)
            
    def _analyze_connections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze connection patterns"""
        try:
            # Load connection history
            try:
                with open(self.connections_file, 'r') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                history = {}
                
            # Load unusual connections
            try:
                with open(self.unusual_connections_file, 'r') as f:
                    unusual = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                unusual = {}
                
            # Count connections by type
            connection_stats = {
                "total_scans": len(history),
                "listening_ports": {},
                "remote_connections": {},
                "connection_states": {},
                "protocols": {}
            }
            
            # Process each scan
            for timestamp, connections in history.items():
                for conn in connections:
                    # Count listening ports
                    if conn["state"] == "LISTEN":
                        port = conn["local_port"]
                        if port not in connection_stats["listening_ports"]:
                            connection_stats["listening_ports"][port] = 0
                        connection_stats["listening_ports"][port] += 1
                        
                    # Count remote connections
                    if conn["state"] == "ESTABLISHED" and conn["remote_addr"]:
                        remote = f"{conn['remote_addr']}:{conn['remote_port']}"
                        if remote not in connection_stats["remote_connections"]:
                            connection_stats["remote_connections"][remote] = 0
                        connection_stats["remote_connections"][remote] += 1
                        
                    # Count connection states
                    state = conn["state"] or "UNKNOWN"
                    if state not in connection_stats["connection_states"]:
                        connection_stats["connection_states"][state] = 0
                    connection_stats["connection_states"][state] += 1
                    
                    # Count protocols
                    proto = conn["protocol"]
                    if proto not in connection_stats["protocols"]:
                        connection_stats["protocols"][proto] = 0
                    connection_stats["protocols"][proto] += 1
                    
            # Sort by frequency
            connection_stats["listening_ports"] = dict(
                sorted(connection_stats["listening_ports"].items(), 
                      key=lambda x: x[1], reverse=True)
            )
            
            connection_stats["remote_connections"] = dict(
                sorted(connection_stats["remote_connections"].items(), 
                      key=lambda x: x[1], reverse=True)
            )
            
            # Get top 10 unusual connections
            unusual_list = []
            for key, details in unusual.items():
                unusual_list.append({
                    "connection": details["connection"],
                    "first_seen": details["first_seen"],
                    "last_seen": details["last_seen"],
                    "count": details["count"]
                })
                
            # Sort by count
            unusual_list.sort(key=lambda x: x["count"], reverse=True)
            
            return {
                "success": True,
                "message": "Connection analysis completed",
                "stats": connection_stats,
                "unusual_connections": unusual_list[:10],
                "total_unusual": len(unusual)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing connections: {str(e)}")
            return {
                "success": False,
                "error": f"Error analyzing connections: {str(e)}"
            }
            
    def _connection_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get connection history"""
        try:
            # Load connection history
            try:
                with open(self.connections_file, 'r') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                history = {}
                
            # Get requested timespan
            hours = int(params.get("hours", 24))
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Filter by timespan
            filtered_history = {}
            for timestamp, connections in history.items():
                if timestamp >= cutoff:
                    filtered_history[timestamp] = connections
                    
            return {
                "success": True,
                "message": f"Retrieved connection history for the last {hours} hours",
                "history": filtered_history,
                "scan_count": len(filtered_history),
                "connection_count": sum(len(c) for c in filtered_history.values())
            }
        except Exception as e:
            self.logger.error(f"Error retrieving connection history: {str(e)}")
            return {
                "success": False,
                "error": f"Error retrieving connection history: {str(e)}"
            }
            
    def get_metadata(self) -> Dict[str, Any]:
        """Return plugin metadata"""
        return {
            "name": "Network Monitor Plugin",
            "version": "1.0.0",
            "description": "Monitors network connections and detects unusual activity",
            "author": "Claude",
            "status": "active",
            "config": self.config
        }
        
    def cleanup(self) -> bool:
        """Clean up any resources used by the plugin"""
        self.logger.info("Network Monitor plugin cleanup")
        return True

if __name__ == "__main__":
    # When run directly, perform a plugin scan and create an example plugin
    manager = PluginManager()
    
    # Scan for existing plugins
    scan_result = manager.scan_plugins(force_reload=True)
    print(f"Found {len(scan_result.get('plugins', []))} plugins")
    
    # Create a backup/restore plugin directory if it doesn't exist
    plugin_dir = os.path.join(PLUGINS_DIR, "backup_restore")
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Create plugin metadata
    metadata = {
        "name": "Backup/Restore Plugin",
        "version": "1.0.0",
        "description": "Provides backup and restore functionality for Deus Ex Machina",
        "author": "Claude",
        "main_module": "backup_restore.py",
        "main_class": "BackupRestorePlugin"
    }
    
    # Write metadata file
    with open(os.path.join(plugin_dir, METADATA_FILENAME), 'w') as f:
        json.dump(metadata, f, indent=2)
        
    # Create plugin module file
    # Note: In a real scenario, we'd extract the class definition from this file
    module_content = inspect.getsource(BackupRestorePlugin)
    
    with open(os.path.join(plugin_dir, "backup_restore.py"), 'w') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("# backup_restore.py - Plugin for backup and restore functionality\n\n")
        f.write("import os\n")
        f.write("import sys\n")
        f.write("import json\n")
        f.write("import logging\n")
        f.write("import shutil\n")
        f.write("import time\n")
        f.write("import subprocess\n")
        f.write("from datetime import datetime\n")
        f.write("from typing import Dict, List, Any, Optional\n\n")
        f.write("# Import plugin base class\n")
        f.write("sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \"../..\")))  \n")
        f.write("from plugin_system import DeusPlugin\n\n")
        f.write(module_content)
        
    # Also create a network monitor plugin
    plugin_dir = os.path.join(PLUGINS_DIR, "network_monitor")
    os.makedirs(plugin_dir, exist_ok=True)
    
    # Create plugin metadata
    metadata = {
        "name": "Network Monitor Plugin",
        "version": "1.0.0",
        "description": "Monitors network connections and detects unusual activity",
        "author": "Claude",
        "main_module": "network_monitor.py",
        "main_class": "NetworkMonitorPlugin"
    }
    
    # Write metadata file
    with open(os.path.join(plugin_dir, METADATA_FILENAME), 'w') as f:
        json.dump(metadata, f, indent=2)
        
    # Create plugin module file
    module_content = inspect.getsource(NetworkMonitorPlugin)
    
    with open(os.path.join(plugin_dir, "network_monitor.py"), 'w') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("# network_monitor.py - Plugin for network monitoring\n\n")
        f.write("import os\n")
        f.write("import sys\n")
        f.write("import json\n")
        f.write("import logging\n")
        f.write("import subprocess\n")
        f.write("import re\n")
        f.write("from datetime import datetime, timedelta\n")
        f.write("from typing import Dict, List, Any, Optional\n\n")
        f.write("# Import plugin base class\n")
        f.write("sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), \"../..\")))  \n")
        f.write("from plugin_system import DeusPlugin\n\n")
        f.write(module_content)
        
    # Scan again to verify plugins were created
    scan_result = manager.scan_plugins(force_reload=True)
    print(f"Now found {len(scan_result.get('plugins', []))} plugins")
    
    # Print example usage
    print("\nExample usage:")
    print("plugin_manager = PluginManager()")
    print("plugin_manager.load_plugin('backup_restore')")
    print("result = plugin_manager.execute_plugin('backup_restore', {'action': 'backup'})")
    print("print(result)")
    
    # Test loading one plugin
    if scan_result.get('plugins'):
        plugin_id = scan_result['plugins'][0]['plugin_id']
        load_result = manager.load_plugin(plugin_id)
        print(f"\nLoaded plugin {plugin_id}: {load_result['success']}")
        if load_result['success']:
            print(f"Plugin metadata: {load_result['plugin']['name']} v{load_result['plugin']['version']}")