#!/usr/bin/env python3
"""
Network Monitoring Plugin for Deus Ex Machina
Provides extended network monitoring capabilities
"""
import os
import sys
import json
import logging
import subprocess
import socket
import time
import threading
from datetime import datetime

# Plugin base class - assuming this is imported from the plugin_system module
from plugin_system import DeusPlugin

class NetworkMonitorPlugin(DeusPlugin):
    """Plugin for advanced network monitoring"""
    
    def __init__(self):
        super().__init__(
            name="network_monitor",
            version="1.0.0",
            description="Advanced network monitoring and analysis",
            permission_level="OBSERVE"  # This plugin only observes, doesn't modify anything
        )
        self.running = False
        self.monitor_thread = None
        self.monitoring_interval = 300  # seconds
        self.endpoints = []
        self.metrics = {}
    
    def initialize(self):
        """Initialize the plugin"""
        try:
            # Load configuration if available
            config_path = "/opt/deus-ex-machina/config/network_monitor.json"
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                
                self.monitoring_interval = config.get("interval", 300)
                self.endpoints = config.get("endpoints", [])
            
            # Add default endpoints if none specified
            if not self.endpoints:
                self.endpoints = [
                    {"name": "Default Gateway", "address": self._get_default_gateway()},
                    {"name": "DNS Server", "address": "8.8.8.8"},
                    {"name": "Internet", "address": "www.google.com"}
                ]
            
            self.logger.info("Network monitor plugin initialized with %d endpoints", 
                             len(self.endpoints))
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize network monitor: %s", str(e))
            return False
    
    def execute(self, action, params=None):
        """Execute the specified action with parameters"""
        params = params or {}
        
        if action == "start_monitoring":
            return self.start_monitoring()
            
        elif action == "stop_monitoring":
            return self.stop_monitoring()
            
        elif action == "get_metrics":
            return self.get_metrics()
            
        elif action == "add_endpoint":
            return self.add_endpoint(params.get("name"), params.get("address"))
            
        elif action == "remove_endpoint":
            return self.remove_endpoint(params.get("name"))
            
        elif action == "check_connectivity":
            return self.check_connectivity(params.get("address"))
            
        else:
            return {"success": False, "message": f"Unknown action: {action}"}
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        if self.running:
            return {"success": False, "message": "Monitoring already running"}
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        return {
            "success": True,
            "message": "Network monitoring started",
            "interval_seconds": self.monitoring_interval,
            "endpoint_count": len(self.endpoints)
        }
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if not self.running:
            return {"success": False, "message": "Monitoring not running"}
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        return {
            "success": True,
            "message": "Network monitoring stopped"
        }
    
    def get_metrics(self):
        """Get the current network metrics"""
        return {
            "success": True,
            "metrics": self.metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_endpoint(self, name, address):
        """Add a new endpoint to monitor"""
        if not name or not address:
            return {
                "success": False,
                "message": "Both name and address are required"
            }
        
        # Check if endpoint already exists
        if any(e["name"] == name for e in self.endpoints):
            return {
                "success": False,
                "message": f"Endpoint '{name}' already exists"
            }
        
        # Add the new endpoint
        self.endpoints.append({"name": name, "address": address})
        
        # Save configuration
        self._save_config()
        
        return {
            "success": True,
            "message": f"Added endpoint: {name} ({address})",
            "endpoint_count": len(self.endpoints)
        }
    
    def remove_endpoint(self, name):
        """Remove an endpoint from monitoring"""
        initial_count = len(self.endpoints)
        self.endpoints = [e for e in self.endpoints if e["name"] != name]
        
        if len(self.endpoints) < initial_count:
            # Save configuration
            self._save_config()
            
            return {
                "success": True,
                "message": f"Removed endpoint: {name}",
                "endpoint_count": len(self.endpoints)
            }
        else:
            return {
                "success": False,
                "message": f"Endpoint not found: {name}"
            }
    
    def check_connectivity(self, address=None):
        """
        Check connectivity to a specific address or all monitored endpoints
        Returns latency in milliseconds
        """
        if address:
            # Check a specific address
            latency = self._ping_host(address)
            return {
                "success": True,
                "address": address,
                "reachable": latency is not None,
                "latency_ms": latency,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Check all endpoints
            results = {}
            for endpoint in self.endpoints:
                name = endpoint["name"]
                addr = endpoint["address"]
                latency = self._ping_host(addr)
                results[name] = {
                    "address": addr,
                    "reachable": latency is not None,
                    "latency_ms": latency
                }
            
            return {
                "success": True,
                "endpoints": results,
                "timestamp": datetime.now().isoformat()
            }
    
    def _monitoring_loop(self):
        """Background thread for continuous monitoring"""
        self.logger.info("Network monitoring thread started")
        
        while self.running:
            try:
                # Collect metrics
                open_ports = self._get_open_ports()
                active_connections = self._get_active_connections()
                connectivity = self.check_connectivity()
                
                # Update metrics store
                self.metrics = {
                    "open_ports": open_ports,
                    "active_connections": active_connections,
                    "connectivity": connectivity.get("endpoints", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Look for anomalies
                self._check_for_anomalies()
                
            except Exception as e:
                self.logger.error(f"Error in network monitoring: {str(e)}")
            
            # Sleep for the monitoring interval
            time.sleep(self.monitoring_interval)
    
    def _get_default_gateway(self):
        """Get the default gateway IP address"""
        try:
            # Try to get default gateway
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True, text=True, check=True
            )
            
            # Parse output for the gateway IP
            output = result.stdout.strip()
            if output:
                parts = output.split()
                if len(parts) >= 3 and parts[0] == "default":
                    return parts[2]
            
            # Fallback to a common gateway address
            return "192.168.1.1"
            
        except Exception as e:
            self.logger.error(f"Error getting default gateway: {str(e)}")
            return "192.168.1.1"
    
    def _ping_host(self, host):
        """Ping a host and return latency in milliseconds, or None if unreachable"""
        try:
            # Use ping command to check connectivity
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", host],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Parse output for latency
                output = result.stdout
                time_match = re.search(r"time=(\d+\.\d+) ms", output)
                if time_match:
                    return float(time_match.group(1))
                return 0  # Reachable but couldn't parse time
            
            return None  # Unreachable
            
        except Exception as e:
            self.logger.error(f"Error pinging {host}: {str(e)}")
            return None
    
    def _get_open_ports(self):
        """Get currently open network ports"""
        try:
            # Use ss command to list listening ports
            result = subprocess.run(
                ["ss", "-tuln"],
                capture_output=True, text=True, check=True
            )
            
            ports = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    # Extract address:port
                    local_address = parts[4]
                    port_part = local_address.split(':')[-1]
                    
                    # Try to extract protocol and port
                    try:
                        port = int(port_part)
                        protocol = "tcp" if "tcp" in parts[0].lower() else "udp"
                        ports.append({"port": port, "protocol": protocol})
                    except ValueError:
                        pass
            
            return ports
            
        except Exception as e:
            self.logger.error(f"Error getting open ports: {str(e)}")
            return []
    
    def _get_active_connections(self):
        """Get active network connections"""
        try:
            # Use ss command to list established connections
            result = subprocess.run(
                ["ss", "-tu", "state", "established"],
                capture_output=True, text=True, check=True
            )
            
            connections = []
            for line in result.stdout.split('\n')[1:]:  # Skip header
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) >= 5:
                    # Extract local and remote addresses
                    local_address = parts[3]
                    remote_address = parts[4]
                    protocol = "tcp" if "tcp" in parts[0].lower() else "udp"
                    
                    connections.append({
                        "protocol": protocol,
                        "local": local_address,
                        "remote": remote_address
                    })
            
            return connections
            
        except Exception as e:
            self.logger.error(f"Error getting active connections: {str(e)}")
            return []
    
    def _check_for_anomalies(self):
        """Check for network anomalies"""
        # This is a placeholder for more sophisticated anomaly detection
        # In a real implementation, this would analyze patterns and report issues
        
        # Simple check: count unreachable endpoints
        if "connectivity" in self.metrics:
            unreachable = [
                name for name, data in self.metrics["connectivity"].items()
                if not data.get("reachable", False)
            ]
            
            if unreachable:
                self.logger.warning(f"Network anomaly: {len(unreachable)} unreachable endpoints: {', '.join(unreachable)}")
    
    def _save_config(self):
        """Save current configuration to disk"""
        try:
            config_dir = "/opt/deus-ex-machina/config"
            os.makedirs(config_dir, exist_ok=True)
            
            config = {
                "interval": self.monitoring_interval,
                "endpoints": self.endpoints
            }
            
            with open(f"{config_dir}/network_monitor.json", "w") as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")

# Don't forget to import re module for _ping_host
import re

# Plugin factory function - required for dynamic loading
def get_plugin():
    """Return an instance of the plugin"""
    return NetworkMonitorPlugin()