#!/usr/bin/env python3
"""
Backup and Restore Plugin for Deus Ex Machina
Provides functionality to backup and restore system configurations
"""
import os
import sys
import json
import logging
import subprocess
import shutil
from datetime import datetime

# Plugin base class - assuming this is imported from the plugin_system module
from plugin_system import DeusPlugin

class BackupRestorePlugin(DeusPlugin):
    """Plugin for system backup and restore operations"""
    
    def __init__(self):
        super().__init__(
            name="backup_restore",
            version="1.0.0",
            description="Provides backup and restore functionality for system configurations",
            permission_level="ADMIN"  # This plugin requires admin permissions
        )
        self.backup_dir = "/opt/deus-ex-machina/backups"
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def initialize(self):
        """Initialize the plugin"""
        self.logger.info("Backup/Restore plugin initialized")
        return True
    
    def execute(self, action, params=None):
        """Execute the specified action with parameters"""
        params = params or {}
        
        if action == "backup":
            return self.create_backup(params.get("name", "manual"), params.get("directories", []))
            
        elif action == "restore":
            return self.restore_backup(params.get("backup_id"))
            
        elif action == "list_backups":
            return self.list_backups()
            
        else:
            return {"success": False, "message": f"Unknown action: {action}"}
    
    def create_backup(self, name, directories=None):
        """Create a backup of the specified directories"""
        try:
            # Default directories to backup if none specified
            if not directories:
                directories = [
                    "/opt/deus-ex-machina/config",
                    "/opt/deus-ex-machina/plugins",
                    "/opt/deus-ex-machina/var/db"
                ]
            
            # Create a timestamped backup ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"{timestamp}_{name}"
            backup_path = os.path.join(self.backup_dir, backup_id)
            
            # Create the backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup each directory
            for directory in directories:
                if os.path.exists(directory):
                    dir_name = os.path.basename(directory)
                    dest_path = os.path.join(backup_path, dir_name)
                    shutil.copytree(directory, dest_path)
                    self.logger.info(f"Backed up {directory} to {dest_path}")
                else:
                    self.logger.warning(f"Directory not found: {directory}")
            
            # Create a metadata file
            metadata = {
                "backup_id": backup_id,
                "name": name,
                "timestamp": timestamp,
                "directories": directories,
                "created_by": "Deus Ex Machina"
            }
            
            with open(os.path.join(backup_path, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)
            
            return {
                "success": True,
                "backup_id": backup_id,
                "message": f"Backup created successfully: {backup_id}"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            return {
                "success": False,
                "message": f"Backup failed: {str(e)}"
            }
    
    def restore_backup(self, backup_id):
        """Restore from a specified backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_id)
            
            if not os.path.exists(backup_path):
                return {
                    "success": False,
                    "message": f"Backup not found: {backup_id}"
                }
            
            # Read metadata to determine what to restore
            metadata_file = os.path.join(backup_path, "metadata.json")
            if not os.path.exists(metadata_file):
                return {
                    "success": False,
                    "message": f"Invalid backup (no metadata): {backup_id}"
                }
            
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            # Restore each directory
            restored_dirs = []
            for directory in metadata["directories"]:
                dir_name = os.path.basename(directory)
                source_path = os.path.join(backup_path, dir_name)
                
                if os.path.exists(source_path):
                    # Create a backup of the current directory before restoring
                    if os.path.exists(directory):
                        temp_backup = f"{directory}.bak.{int(datetime.now().timestamp())}"
                        shutil.move(directory, temp_backup)
                        self.logger.info(f"Created temporary backup: {temp_backup}")
                    
                    # Restore from backup
                    shutil.copytree(source_path, directory)
                    self.logger.info(f"Restored {directory} from backup")
                    restored_dirs.append(directory)
                else:
                    self.logger.warning(f"Directory not found in backup: {dir_name}")
            
            return {
                "success": True,
                "restored_directories": restored_dirs,
                "message": f"Restored {len(restored_dirs)} directories from backup {backup_id}"
            }
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {str(e)}")
            return {
                "success": False,
                "message": f"Restore failed: {str(e)}"
            }
    
    def list_backups(self):
        """List all available backups"""
        try:
            backups = []
            
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                
                if os.path.isdir(item_path):
                    # Try to read metadata
                    metadata_file = os.path.join(item_path, "metadata.json")
                    if os.path.exists(metadata_file):
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        backups.append(metadata)
                    else:
                        # Basic info if no metadata
                        backups.append({
                            "backup_id": item,
                            "name": "unknown",
                            "timestamp": "unknown",
                            "directories": []
                        })
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return {
                "success": True,
                "backups": backups,
                "count": len(backups)
            }
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to list backups: {str(e)}"
            }

# Plugin factory function - required for dynamic loading
def get_plugin():
    """Return an instance of the plugin"""
    return BackupRestorePlugin()