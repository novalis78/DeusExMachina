#!/usr/bin/env python3
"""
Deus Ex Machina - Server Investigation Tools

This module provides a comprehensive set of server investigation tools
that the AI consciousness can use to explore and analyze the system.
"""

import os
import sys
import json
import time
import logging
import datetime
import subprocess
from typing import Dict, List, Any, Optional, Tuple

class ServerInvestigator:
    """
    Provides a comprehensive set of server investigation tools
    with structured results and context tracking.
    """
    
    def __init__(self, log_dir="/tmp/deus-ex-machina/logs"):
        """Initialize the server investigator with logging"""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Investigation state
        self.investigation_history = []
        self.current_context = {"focus_areas": [], "findings": {}}
        self.available_tools = self._register_tools()
        
        self.logger.info("Server Investigator initialized with %d tools", len(self.available_tools))
    
    def _setup_logger(self):
        """Set up the logger for the server investigator"""
        logger = logging.getLogger("deus.investigator")
        logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Add file handler
        log_path = os.path.join(self.log_dir, "investigator.log")
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available tools with their metadata"""
        tools = {
            # System information
            "system_info": {
                "description": "Basic system information",
                "command": ["uname", "-a"],
                "parser": self._parse_system_info,
                "domain": "system"
            },
            "uptime": {
                "description": "System uptime and load",
                "command": ["uptime"],
                "parser": self._parse_uptime,
                "domain": "system"
            },
            "kernel_info": {
                "description": "Kernel information",
                "command": ["cat", "/proc/version"],
                "parser": self._parse_kernel_info,
                "domain": "system"
            },
            
            # Process management
            "process_list": {
                "description": "List all running processes",
                "command": ["ps", "aux"],
                "parser": self._parse_process_list,
                "domain": "processes"
            },
            "top_processes": {
                "description": "Show top CPU consuming processes",
                "command": ["ps", "-eo", "pid,ppid,cmd,%mem,%cpu", "--sort=-%cpu", "|", "head", "-n", "11"],
                "parser": self._parse_top_processes,
                "domain": "processes"
            },
            "top_memory": {
                "description": "Show top memory consuming processes",
                "command": ["ps", "-eo", "pid,ppid,cmd,%mem,%cpu", "--sort=-%mem", "|", "head", "-n", "11"],
                "parser": self._parse_top_memory,
                "domain": "processes"
            },
            
            # Memory
            "memory_info": {
                "description": "Memory usage information",
                "command": ["free", "-m"],
                "parser": self._parse_memory_info,
                "domain": "memory"
            },
            "memory_detailed": {
                "description": "Detailed memory statistics",
                "command": ["cat", "/proc/meminfo"],
                "parser": self._parse_meminfo,
                "domain": "memory"
            },
            "swap_info": {
                "description": "Swap usage information",
                "command": ["swapon", "--show"],
                "parser": self._parse_swap_info,
                "domain": "memory"
            },
            
            # Storage
            "disk_usage": {
                "description": "Disk space usage by filesystem",
                "command": ["df", "-h"],
                "parser": self._parse_disk_usage,
                "domain": "storage"
            },
            "inodes_usage": {
                "description": "Inode usage by filesystem",
                "command": ["df", "-i"],
                "parser": self._parse_inodes,
                "domain": "storage"
            },
            "large_directories": {
                "description": "Find large directories",
                "command": ["du", "-h", "--max-depth=2", "/var/"],
                "parser": self._parse_du,
                "domain": "storage",
            },
            
            # Networking
            "network_interfaces": {
                "description": "List network interfaces",
                "command": ["ip", "addr"],
                "parser": self._parse_ip_addr,
                "domain": "network"
            },
            "open_ports": {
                "description": "Show listening ports and services",
                "command": ["ss", "-tuln"],
                "parser": self._parse_open_ports,
                "domain": "network"
            },
            "network_connections": {
                "description": "Current network connections",
                "command": ["ss", "-tan", "state", "established"],
                "parser": self._parse_connections,
                "domain": "network"
            },
            "routing_table": {
                "description": "IP routing table",
                "command": ["ip", "route"],
                "parser": self._parse_routes,
                "domain": "network"
            },
            
            # Services
            "service_status": {
                "description": "Status of system services",
                "command": ["systemctl", "list-units", "--type=service"],
                "parser": self._parse_systemctl,
                "domain": "services"
            },
            "failed_services": {
                "description": "List failed services",
                "command": ["systemctl", "--failed"],
                "parser": self._parse_failed_services,
                "domain": "services"
            },
            
            # Logs
            "recent_logs": {
                "description": "Recent system logs",
                "command": ["journalctl", "-n", "20"],
                "parser": self._parse_journalctl,
                "domain": "logs"
            },
            "error_logs": {
                "description": "Error messages in logs",
                "command": ["journalctl", "-p", "err", "-n", "20"],
                "parser": self._parse_journal_errors,
                "domain": "logs"
            },
            
            # Security
            "login_attempts": {
                "description": "Recent login attempts",
                "command": ["journalctl", "-t", "sshd", "-n", "20"],
                "parser": self._parse_login_attempts,
                "domain": "security"
            },
            "listening_programs": {
                "description": "Programs listening on network",
                "command": ["netstat", "-tulnp"],
                "parser": self._parse_listening_programs,
                "domain": "security"
            },
            
            # Performance
            "load_average": {
                "description": "System load average",
                "command": ["cat", "/proc/loadavg"],
                "parser": self._parse_load_avg,
                "domain": "performance"
            },
            "cpu_info": {
                "description": "CPU information",
                "command": ["lscpu"],
                "parser": self._parse_cpu_info,
                "domain": "performance"
            }
        }
        
        return tools
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return a list of all available tools with their metadata"""
        tool_list = []
        for name, tool in self.available_tools.items():
            tool_info = {
                "name": name,
                "description": tool["description"],
                "domain": tool["domain"]
            }
            tool_list.append(tool_info)
        
        # Group by domain
        domains = {}
        for tool in tool_list:
            domain = tool["domain"]
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(tool)
        
        return {"tools_by_domain": domains, "total_count": len(tool_list)}
    
    def investigate(self, focus_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Begin or continue an investigation based on query or previous findings.
        
        Args:
            focus_query: Optional query to focus the investigation
                         If None, continues the previous investigation
                         
        Returns:
            Dict containing investigation results, insights and next steps
        """
        self.logger.info("Beginning investigation with focus: %s", focus_query or "continuing previous")
        
        if focus_query:
            # New investigation with specific focus
            self.current_context = self._analyze_query(focus_query)
        
        # Determine which tools to use
        tool_names = self._determine_next_tools()
        self.logger.info("Selected tools for investigation: %s", tool_names)
        
        findings = {}
        
        # Execute each tool and gather results
        for tool_name in tool_names:
            self.logger.info("Executing tool: %s", tool_name)
            result = self._execute_tool(tool_name)
            
            if result["success"]:
                # Process and add to findings
                domain = self.available_tools[tool_name]["domain"]
                if domain not in findings:
                    findings[domain] = []
                
                findings[domain].append({
                    "tool": tool_name,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "data": result["parsed_data"]
                })
                
                # Add to investigation history
                self.investigation_history.append({
                    "tool": tool_name,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "focus_query": focus_query,
                    "success": True
                })
            else:
                self.logger.error("Tool %s failed: %s", tool_name, result.get("error", "Unknown error"))
                
                # Add to investigation history
                self.investigation_history.append({
                    "tool": tool_name,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "focus_query": focus_query,
                    "success": False,
                    "error": result.get("error", "Unknown error")
                })
        
        # Update context with new findings
        for domain, domain_findings in findings.items():
            if domain not in self.current_context["findings"]:
                self.current_context["findings"][domain] = []
            
            self.current_context["findings"][domain].extend(domain_findings)
        
        # Generate insights based on findings
        insights = self._generate_insights()
        
        # Update context for next investigation
        self._update_context(insights)
        
        # Determine recommended next steps
        next_steps = self._determine_next_steps()
        
        # Return results
        return {
            "focus_query": focus_query,
            "findings": findings,
            "insights": insights,
            "next_steps": next_steps,
            "total_tools_used": len(self.investigation_history),
            "current_focus_areas": self.current_context["focus_areas"]
        }
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze the initial query to determine focus areas.
        
        Args:
            query: The investigation query
            
        Returns:
            Context dictionary with focus areas
        """
        context = {"focus_areas": [], "findings": {}}
        
        # Simple keyword matching for domains
        domains = {
            "system": ["system", "os", "overview", "general", "info", "information"],
            "processes": ["process", "running", "application", "program", "service", "task"],
            "memory": ["memory", "ram", "swap", "usage"],
            "storage": ["disk", "storage", "space", "filesystem", "drive", "volume"],
            "network": ["network", "connection", "port", "interface", "socket", "ip", "dns"],
            "services": ["service", "daemon", "systemd", "systemctl"],
            "logs": ["log", "error", "message", "journal", "event"],
            "security": ["security", "login", "access", "auth", "permission"],
            "performance": ["performance", "slow", "speed", "bottleneck", "cpu", "load"]
        }
        
        query_lower = query.lower()
        
        # Match query keywords to domains
        for domain, keywords in domains.items():
            for keyword in keywords:
                if keyword in query_lower:
                    context["focus_areas"].append(domain)
                    break  # Only add the domain once
        
        # Check for specific tool mentions
        for tool_name, tool in self.available_tools.items():
            tool_keywords = tool_name.replace("_", " ").lower().split()
            
            if any(keyword in query_lower for keyword in tool_keywords):
                # Add the domain this tool belongs to
                if tool["domain"] not in context["focus_areas"]:
                    context["focus_areas"].append(tool["domain"])
        
        # If no specific areas found, start with general overview
        if not context["focus_areas"]:
            context["focus_areas"] = ["system", "processes", "memory", "storage"]
            
        # Deduplicate focus areas
        context["focus_areas"] = list(set(context["focus_areas"]))
        
        self.logger.info("Analyzed query '%s', focus areas: %s", query, context["focus_areas"])
        
        return context
    
    def _determine_next_tools(self) -> List[str]:
        """
        Determine which tools to use next based on current context.
        
        Returns:
            List of tool names to execute
        """
        selected_tools = []
        
        # Select tools based on focus areas
        for area in self.current_context["focus_areas"]:
            # Find all tools in this domain
            area_tools = [name for name, tool in self.available_tools.items() 
                         if tool["domain"] == area]
            
            # For each domain, select up to 2 tools
            for tool in area_tools[:2]:
                if tool not in selected_tools:
                    selected_tools.append(tool)
        
        # Add tools based on follow-up items from previous investigation
        for item in self.current_context.get("follow_up", []):
            if item["type"] == "high_cpu_process" and "top_processes" not in selected_tools:
                selected_tools.append("top_processes")
            elif item["type"] == "memory_issue" and "memory_detailed" not in selected_tools:
                selected_tools.append("memory_detailed")
            elif item["type"] == "disk_space_issue" and "large_directories" not in selected_tools:
                selected_tools.append("large_directories")
            elif item["type"] == "network_issue" and "network_connections" not in selected_tools:
                selected_tools.append("network_connections")
        
        # Limit to 6 tools for a single investigation
        return selected_tools[:6]
    
    def _execute_tool(self, tool_name: str) -> Dict[str, Any]:
        """
        Execute a specific tool and return the results.
        
        Args:
            tool_name: The name of the tool to execute
            
        Returns:
            Dictionary with execution results
        """
        if tool_name not in self.available_tools:
            return {"success": False, "error": f"Tool {tool_name} not found"}
        
        tool_config = self.available_tools[tool_name]
        
        try:
            # For demonstration, we'll build a safe command as a list
            # In real implementation, handle shell=True carefully
            command = tool_config["command"]
            
            # Execute the command safely using join and shell=False for pipes
            # Note: in a real implementation, handle pipe commands differently
            command_str = " ".join(command)
            self.logger.info("Executing command: %s", command_str)
            
            if "|" in command:
                # For piped commands, we need to use shell=True
                # This has security implications in production
                result = subprocess.check_output(command_str, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
            else:
                # For simple commands, use the safer list approach
                result = subprocess.check_output(command, stderr=subprocess.STDOUT).decode('utf-8')
            
            # Parse the result using the tool's parser
            parser = tool_config["parser"]
            parsed_data = parser(result)
            
            return {
                "success": True,
                "raw_output": result[:1000] if len(result) > 1000 else result,  # Truncate long outputs
                "parsed_data": parsed_data
            }
        except subprocess.CalledProcessError as e:
            self.logger.error("Command execution failed: %s", str(e))
            return {
                "success": False,
                "error": f"Command execution failed: {str(e)}",
                "exit_code": e.returncode,
                "output": e.output.decode('utf-8') if hasattr(e, 'output') else ""
            }
        except Exception as e:
            self.logger.error("Error executing tool %s: %s", tool_name, str(e))
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }
    
    def _update_context(self, insights: List[Dict[str, Any]]) -> None:
        """
        Update context based on insights for the next investigation.
        
        Args:
            insights: List of insights generated from findings
        """
        # Initialize follow-up list if not exists
        if "follow_up" not in self.current_context:
            self.current_context["follow_up"] = []
        
        # Clean up old follow-ups after they've been addressed
        # Keep only the last 5 follow-ups to prevent excessive accumulation
        self.current_context["follow_up"] = self.current_context["follow_up"][-5:]
        
        # Add new follow-ups based on insights
        for insight in insights:
            if insight["importance"] == "high":
                # Add high importance insights to follow-up
                follow_up_item = {
                    "type": insight["type"],
                    "description": insight["description"],
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Only add if not already in follow-ups
                if not any(item["type"] == follow_up_item["type"] for item in self.current_context["follow_up"]):
                    self.current_context["follow_up"].append(follow_up_item)
        
        # Update focus areas based on insights
        insight_domains = set()
        for insight in insights:
            if insight["importance"] in ["high", "medium"]:
                if insight["type"].startswith("cpu_"):
                    insight_domains.add("performance")
                    insight_domains.add("processes")
                elif insight["type"].startswith("memory_"):
                    insight_domains.add("memory")
                elif insight["type"].startswith("disk_"):
                    insight_domains.add("storage")
                elif insight["type"].startswith("network_"):
                    insight_domains.add("network")
                elif insight["type"].startswith("security_"):
                    insight_domains.add("security")
        
        # Update focus areas, prioritizing domains with issues
        if insight_domains:
            # Keep original focus areas but prioritize issue domains
            new_focus_areas = list(insight_domains)
            for area in self.current_context["focus_areas"]:
                if area not in new_focus_areas:
                    new_focus_areas.append(area)
            
            self.current_context["focus_areas"] = new_focus_areas[:5]  # Limit to 5 areas
    
    def _generate_insights(self) -> List[Dict[str, Any]]:
        """
        Generate insights based on findings.
        
        Returns:
            List of insights
        """
        insights = []
        
        # Check each domain for issues
        for domain, findings in self.current_context["findings"].items():
            # Generate domain-specific insights
            domain_insights = self._analyze_domain(domain, findings)
            insights.extend(domain_insights)
        
        # Generate cross-domain insights
        cross_domain_insights = self._analyze_cross_domain()
        insights.extend(cross_domain_insights)
        
        # Sort insights by importance
        importance_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: importance_order.get(x["importance"], 3))
        
        return insights
    
    def _analyze_domain(self, domain: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze findings for a specific domain.
        
        Args:
            domain: The domain to analyze
            findings: List of findings for this domain
            
        Returns:
            List of domain-specific insights
        """
        insights = []
        
        if domain == "processes":
            # Process-related insights
            for finding in findings:
                if finding["tool"] == "top_processes":
                    # Check for high CPU processes
                    high_cpu = [p for p in finding["data"] if float(p["cpu_percent"]) > 50]
                    if high_cpu:
                        insights.append({
                            "type": "cpu_high_process",
                            "importance": "high",
                            "description": f"Process {high_cpu[0]['command']} (PID: {high_cpu[0]['pid']}) is using {high_cpu[0]['cpu_percent']}% CPU",
                            "process": high_cpu[0]
                        })
                
                if finding["tool"] == "top_memory":
                    # Check for high memory processes
                    high_mem = [p for p in finding["data"] if float(p["mem_percent"]) > 30]
                    if high_mem:
                        insights.append({
                            "type": "memory_high_process",
                            "importance": "medium",
                            "description": f"Process {high_mem[0]['command']} (PID: {high_mem[0]['pid']}) is using {high_mem[0]['mem_percent']}% memory",
                            "process": high_mem[0]
                        })
        
        elif domain == "storage":
            # Storage-related insights
            for finding in findings:
                if finding["tool"] == "disk_usage":
                    # Check for filesystems with high usage
                    critical = [fs for fs in finding["data"]["filesystems"] 
                              if int(fs["use_percent"].rstrip("%")) > 90]
                    warning = [fs for fs in finding["data"]["filesystems"] 
                              if int(fs["use_percent"].rstrip("%")) > 80 
                              and int(fs["use_percent"].rstrip("%")) <= 90]
                    
                    for fs in critical:
                        insights.append({
                            "type": "disk_critical_usage",
                            "importance": "high",
                            "description": f"Critical disk space on {fs['mounted_on']}: {fs['use_percent']} used",
                            "filesystem": fs
                        })
                    
                    for fs in warning:
                        insights.append({
                            "type": "disk_warning_usage",
                            "importance": "medium",
                            "description": f"Warning: low disk space on {fs['mounted_on']}: {fs['use_percent']} used",
                            "filesystem": fs
                        })
        
        elif domain == "memory":
            # Memory-related insights
            for finding in findings:
                if finding["tool"] == "memory_info":
                    # Check for high memory usage
                    mem_usage = finding["data"].get("memory_usage_percent")
                    if mem_usage and mem_usage > 90:
                        insights.append({
                            "type": "memory_critical_usage",
                            "importance": "high",
                            "description": f"Critical memory usage: {mem_usage}% used",
                            "memory_info": finding["data"]
                        })
                    elif mem_usage and mem_usage > 80:
                        insights.append({
                            "type": "memory_high_usage",
                            "importance": "medium",
                            "description": f"High memory usage: {mem_usage}% used",
                            "memory_info": finding["data"]
                        })
                    
                    # Check for high swap usage
                    swap_usage = finding["data"].get("swap_usage_percent")
                    if swap_usage and swap_usage > 50:
                        insights.append({
                            "type": "memory_high_swap",
                            "importance": "medium",
                            "description": f"High swap usage: {swap_usage}% used",
                            "memory_info": finding["data"]
                        })
        
        elif domain == "network":
            # Network-related insights
            for finding in findings:
                if finding["tool"] == "open_ports":
                    # Check for potentially problematic open ports
                    sensitive_ports = [22, 3389, 1433, 3306, 5432, 27017, 6379, 9200, 11211]
                    open_sensitive = []
                    
                    for port_info in finding["data"]["ports"]:
                        port = port_info.get("port")
                        if port and int(port) in sensitive_ports:
                            open_sensitive.append(port_info)
                    
                    if open_sensitive:
                        insights.append({
                            "type": "network_sensitive_ports",
                            "importance": "medium",
                            "description": f"{len(open_sensitive)} sensitive ports open: " + 
                                          ", ".join([f"{p['port']}/{p['protocol']}" for p in open_sensitive]),
                            "ports": open_sensitive
                        })
        
        elif domain == "security":
            # Security-related insights
            for finding in findings:
                if finding["tool"] == "login_attempts":
                    # Check for failed login attempts
                    failed_attempts = [entry for entry in finding["data"]["entries"] 
                                      if "Failed password" in entry["message"]]
                    
                    if len(failed_attempts) > 3:
                        insights.append({
                            "type": "security_failed_logins",
                            "importance": "high",
                            "description": f"Multiple failed login attempts detected: {len(failed_attempts)} failures",
                            "attempts": failed_attempts
                        })
        
        elif domain == "services":
            # Services-related insights
            for finding in findings:
                if finding["tool"] == "failed_services":
                    # Check for failed services
                    if finding["data"]["failed_count"] > 0:
                        insights.append({
                            "type": "services_failed",
                            "importance": "high",
                            "description": f"{finding['data']['failed_count']} failed services detected",
                            "services": finding["data"]["failed_services"]
                        })
        
        return insights
    
    def _analyze_cross_domain(self) -> List[Dict[str, Any]]:
        """
        Analyze relationships between findings from different domains.
        
        Returns:
            List of cross-domain insights
        """
        insights = []
        findings = self.current_context["findings"]
        
        # Example: Relate high CPU/memory with disk I/O
        if ("processes" in findings and "storage" in findings and 
            "memory" in findings):
            
            # Check if we have high CPU processes
            high_cpu_process = None
            for finding in findings.get("processes", []):
                if finding["tool"] == "top_processes":
                    high_cpu_procs = [p for p in finding["data"] if float(p["cpu_percent"]) > 70]
                    if high_cpu_procs:
                        high_cpu_process = high_cpu_procs[0]
            
            # Check if we have high memory usage
            high_memory = False
            for finding in findings.get("memory", []):
                if finding["tool"] == "memory_info":
                    if finding["data"].get("memory_usage_percent", 0) > 80:
                        high_memory = True
            
            # Check if we have high disk usage
            high_disk = False
            for finding in findings.get("storage", []):
                if finding["tool"] == "disk_usage":
                    critical_fs = [fs for fs in finding["data"]["filesystems"] 
                                  if int(fs["use_percent"].rstrip("%")) > 85]
                    if critical_fs:
                        high_disk = True
            
            # Generate cross-domain insight if multiple issues found
            if high_cpu_process and high_memory and high_disk:
                insights.append({
                    "type": "cross_resource_pressure",
                    "importance": "high",
                    "description": "System experiencing pressure across CPU, memory, and disk resources",
                    "details": {
                        "cpu_process": high_cpu_process["command"],
                        "cpu_usage": high_cpu_process["cpu_percent"],
                        "high_memory": high_memory,
                        "high_disk": high_disk
                    }
                })
        
        # Example: Relate high disk usage with large files/directories
        if ("storage" in findings):
            disk_critical = False
            critical_mount = None
            
            for finding in findings.get("storage", []):
                if finding["tool"] == "disk_usage":
                    critical_fs = [fs for fs in finding["data"]["filesystems"] 
                                  if int(fs["use_percent"].rstrip("%")) > 90]
                    if critical_fs:
                        disk_critical = True
                        critical_mount = critical_fs[0]["mounted_on"]
                
                if disk_critical and finding["tool"] == "large_directories":
                    # Find large directories in the critical mount point
                    large_dirs = [d for d in finding["data"]["directories"] 
                                 if d["size_human"].endswith("G") and 
                                 (critical_mount in d["path"] or d["path"].startswith(critical_mount))]
                    
                    if large_dirs:
                        insights.append({
                            "type": "disk_large_directories",
                            "importance": "medium",
                            "description": f"Large directories found on critical filesystem {critical_mount}",
                            "directories": large_dirs[:3]
                        })
        
        return insights
    
    def _determine_next_steps(self) -> List[Dict[str, Any]]:
        """
        Determine recommended next steps for the investigation.
        
        Returns:
            List of recommended next steps
        """
        next_steps = []
        
        # Check each domain for follow-up steps
        for domain, findings in self.current_context["findings"].items():
            if domain == "processes" and any(f["tool"] == "top_processes" for f in findings):
                # If we found high CPU processes, suggest deeper investigation
                for finding in findings:
                    if finding["tool"] == "top_processes":
                        high_cpu = [p for p in finding["data"] if float(p["cpu_percent"]) > 50]
                        if high_cpu:
                            next_steps.append({
                                "description": f"Investigate high CPU process: {high_cpu[0]['command']}",
                                "tools": ["top_processes", "process_list"],
                                "importance": "high"
                            })
            
            if domain == "storage" and any(f["tool"] == "disk_usage" for f in findings):
                # If we found high disk usage, suggest finding large directories
                for finding in findings:
                    if finding["tool"] == "disk_usage":
                        critical = [fs for fs in finding["data"]["filesystems"] 
                                  if int(fs["use_percent"].rstrip("%")) > 85]
                        if critical:
                            next_steps.append({
                                "description": f"Investigate disk usage on {critical[0]['mounted_on']}",
                                "tools": ["large_directories"],
                                "importance": "high"
                            })
            
            if domain == "network" and any(f["tool"] == "open_ports" for f in findings):
                # If we found open ports, suggest checking connections
                next_steps.append({
                    "description": "Investigate network connections",
                    "tools": ["network_connections"],
                    "importance": "medium"
                })
        
        # Check for missing but relevant areas
        if self.current_context["findings"]:
            # Only suggest new areas if we already have some findings
            covered_domains = set(self.current_context["findings"].keys())
            
            # Suggest checking security if we've looked at processes or network
            if (("processes" in covered_domains or "network" in covered_domains) 
                and "security" not in covered_domains):
                next_steps.append({
                    "description": "Check security aspects",
                    "tools": ["login_attempts", "listening_programs"],
                    "importance": "medium"
                })
            
            # Suggest checking performance if we've looked at processes or memory
            if (("processes" in covered_domains or "memory" in covered_domains) 
                and "performance" not in covered_domains):
                next_steps.append({
                    "description": "Check performance metrics",
                    "tools": ["load_average", "cpu_info"],
                    "importance": "medium"
                })
        
        # Sort next steps by importance
        importance_order = {"high": 0, "medium": 1, "low": 2}
        next_steps.sort(key=lambda x: importance_order.get(x["importance"], 3))
        
        return next_steps
    
    #
    # Tool Output Parsers
    #
    
    def _parse_system_info(self, output: str) -> Dict[str, Any]:
        """Parse uname -a output"""
        parts = output.strip().split()
        return {
            "kernel": parts[0] if len(parts) > 0 else "",
            "hostname": parts[1] if len(parts) > 1 else "",
            "kernel_release": parts[2] if len(parts) > 2 else "",
            "kernel_version": parts[3] if len(parts) > 3 else "",
            "machine": parts[4] if len(parts) > 4 else "",
            "processor": parts[5] if len(parts) > 5 else ""
        }
    
    def _parse_uptime(self, output: str) -> Dict[str, Any]:
        """Parse uptime command output"""
        output = output.strip()
        
        # Extract uptime
        uptime_str = output
        
        # Extract load averages
        load_avg = []
        if "load average:" in output:
            load_part = output.split("load average:")[1].strip()
            load_avg = [float(x.strip(',')) for x in load_part.split()]
        
        return {
            "uptime_str": uptime_str,
            "load_averages": {
                "1min": load_avg[0] if len(load_avg) > 0 else None,
                "5min": load_avg[1] if len(load_avg) > 1 else None,
                "15min": load_avg[2] if len(load_avg) > 2 else None
            }
        }
    
    def _parse_kernel_info(self, output: str) -> Dict[str, Any]:
        """Parse /proc/version output"""
        return {
            "version_string": output.strip()
        }
    
    def _parse_process_list(self, output: str) -> Dict[str, Any]:
        """Parse ps aux output"""
        lines = output.strip().split('\n')
        header = lines[0]
        processes = []
        
        for line in lines[1:]:
            parts = line.split(None, 10)
            if len(parts) >= 11:
                processes.append({
                    "user": parts[0],
                    "pid": parts[1],
                    "cpu_percent": parts[2],
                    "mem_percent": parts[3],
                    "vsz": parts[4],
                    "rss": parts[5],
                    "tty": parts[6],
                    "stat": parts[7],
                    "start": parts[8],
                    "time": parts[9],
                    "command": parts[10]
                })
        
        return {
            "processes": processes[:20],  # Limit to 20 processes for brevity
            "total_count": len(processes)
        }
    
    def _parse_top_processes(self, output: str) -> List[Dict[str, Any]]:
        """Parse top CPU consuming processes"""
        lines = output.strip().split('\n')
        header = lines[0]
        processes = []
        
        for line in lines[1:]:
            parts = line.split(None, 4)
            if len(parts) >= 5:
                processes.append({
                    "pid": parts[0],
                    "ppid": parts[1],
                    "command": parts[2],
                    "mem_percent": parts[3],
                    "cpu_percent": parts[4]
                })
        
        return processes
    
    def _parse_top_memory(self, output: str) -> List[Dict[str, Any]]:
        """Parse top memory consuming processes"""
        lines = output.strip().split('\n')
        header = lines[0]
        processes = []
        
        for line in lines[1:]:
            parts = line.split(None, 4)
            if len(parts) >= 5:
                processes.append({
                    "pid": parts[0],
                    "ppid": parts[1],
                    "command": parts[2],
                    "mem_percent": parts[3],
                    "cpu_percent": parts[4]
                })
        
        return processes
    
    def _parse_memory_info(self, output: str) -> Dict[str, Any]:
        """Parse free -m output"""
        lines = output.strip().split('\n')
        result = {}
        
        # Process memory line
        if len(lines) > 1:
            mem_parts = lines[1].split()
            if len(mem_parts) >= 7:
                result["total_mb"] = int(mem_parts[1])
                result["used_mb"] = int(mem_parts[2])
                result["free_mb"] = int(mem_parts[3])
                result["shared_mb"] = int(mem_parts[4])
                result["buff_cache_mb"] = int(mem_parts[5])
                result["available_mb"] = int(mem_parts[6])
                
                # Calculate usage percentage
                if result["total_mb"] > 0:
                    result["memory_usage_percent"] = round(
                        (result["total_mb"] - result["available_mb"]) / result["total_mb"] * 100, 1
                    )
        
        # Process swap line
        if len(lines) > 2:
            swap_parts = lines[2].split()
            if len(swap_parts) >= 4:
                result["swap_total_mb"] = int(swap_parts[1])
                result["swap_used_mb"] = int(swap_parts[2])
                result["swap_free_mb"] = int(swap_parts[3])
                
                # Calculate swap usage percentage
                if result["swap_total_mb"] > 0:
                    result["swap_usage_percent"] = round(
                        result["swap_used_mb"] / result["swap_total_mb"] * 100, 1
                    )
                else:
                    result["swap_usage_percent"] = 0
        
        return result
    
    def _parse_meminfo(self, output: str) -> Dict[str, Any]:
        """Parse /proc/meminfo output"""
        lines = output.strip().split('\n')
        result = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Extract numeric value and unit if present
                parts = value.split()
                if len(parts) > 0:
                    try:
                        numeric_value = int(parts[0])
                        result[key] = numeric_value
                        if len(parts) > 1:
                            result[f"{key}_unit"] = parts[1]
                    except ValueError:
                        result[key] = value
        
        return result
    
    def _parse_swap_info(self, output: str) -> Dict[str, Any]:
        """Parse swapon --show output"""
        lines = output.strip().split('\n')
        swap_devices = []
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 4:
                swap_devices.append({
                    "name": parts[0],
                    "type": parts[1],
                    "size": parts[2],
                    "used": parts[3],
                    "priority": parts[4] if len(parts) > 4 else ""
                })
        
        return {
            "swap_devices": swap_devices,
            "count": len(swap_devices)
        }
    
    def _parse_disk_usage(self, output: str) -> Dict[str, Any]:
        """Parse df -h output"""
        lines = output.strip().split('\n')
        filesystems = []
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 6:
                filesystems.append({
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "available": parts[3],
                    "use_percent": parts[4],
                    "mounted_on": parts[5]
                })
        
        return {
            "filesystems": filesystems,
            "count": len(filesystems)
        }
    
    def _parse_inodes(self, output: str) -> Dict[str, Any]:
        """Parse df -i output"""
        lines = output.strip().split('\n')
        filesystems = []
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 6:
                filesystems.append({
                    "filesystem": parts[0],
                    "inodes": parts[1],
                    "used": parts[2],
                    "free": parts[3],
                    "use_percent": parts[4],
                    "mounted_on": parts[5]
                })
        
        return {
            "filesystems": filesystems,
            "count": len(filesystems)
        }
    
    def _parse_du(self, output: str) -> Dict[str, Any]:
        """Parse du -h output"""
        lines = output.strip().split('\n')
        directories = []
        
        for line in lines:
            parts = line.split(None, 1)
            if len(parts) == 2:
                directories.append({
                    "size_human": parts[0],
                    "path": parts[1]
                })
        
        # Sort by size (approximately by looking at the human-readable size)
        def size_to_bytes(size_str):
            multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
            if size_str[-1] in multipliers:
                return float(size_str[:-1]) * multipliers[size_str[-1]]
            return float(size_str)
        
        # Sort directories by size, largest first
        sorted_dirs = sorted(
            directories,
            key=lambda d: size_to_bytes(d["size_human"]) if d["size_human"][-1] in 'KMGT' else float(d["size_human"]),
            reverse=True
        )
        
        return {
            "directories": sorted_dirs[:20],  # Limit to top 20 directories
            "count": len(directories)
        }
    
    def _parse_ip_addr(self, output: str) -> Dict[str, Any]:
        """Parse ip addr output"""
        sections = output.strip().split('\n\n')
        interfaces = []
        
        for section in sections:
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            # Extract interface name and flags
            interface = {}
            first_line_parts = lines[0].split(':', 2)
            if len(first_line_parts) >= 2:
                interface["index"] = first_line_parts[0].strip()
                interface["name"] = first_line_parts[1].strip()
                
                # Extract IP addresses
                interface["addresses"] = []
                for line in lines[1:]:
                    line = line.strip()
                    if "inet " in line:
                        # IPv4 address
                        parts = line.split()
                        address = parts[1]
                        interface["addresses"].append({
                            "type": "inet",
                            "address": address
                        })
                    elif "inet6 " in line:
                        # IPv6 address
                        parts = line.split()
                        address = parts[1]
                        interface["addresses"].append({
                            "type": "inet6",
                            "address": address
                        })
                
                interfaces.append(interface)
        
        return {
            "interfaces": interfaces,
            "count": len(interfaces)
        }
    
    def _parse_open_ports(self, output: str) -> Dict[str, Any]:
        """Parse ss -tuln output"""
        lines = output.strip().split('\n')
        ports = []
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 5:
                # Extract protocol
                protocol = parts[0]
                
                # Extract local address and port
                local_addr = parts[4]
                if ":" in local_addr:
                    addr, port = local_addr.rsplit(":", 1)
                    ports.append({
                        "protocol": protocol,
                        "local_address": addr,
                        "port": port
                    })
        
        return {
            "ports": ports,
            "count": len(ports)
        }
    
    def _parse_connections(self, output: str) -> Dict[str, Any]:
        """Parse ss -tan output"""
        lines = output.strip().split('\n')
        connections = []
        
        for line in lines[1:]:  # Skip header
            parts = line.split()
            if len(parts) >= 5:
                connection = {
                    "state": parts[1],
                    "local_address": parts[3],
                    "remote_address": parts[4]
                }
                connections.append(connection)
        
        return {
            "connections": connections[:20],  # Limit to 20 connections
            "count": len(connections)
        }
    
    def _parse_routes(self, output: str) -> List[Dict[str, Any]]:
        """Parse ip route output"""
        lines = output.strip().split('\n')
        routes = []
        
        for line in lines:
            parts = line.split()
            if parts:
                route = {
                    "destination": parts[0],
                    "full_route": line
                }
                
                # Extract some common fields if present
                if "via" in parts:
                    idx = parts.index("via")
                    if idx + 1 < len(parts):
                        route["gateway"] = parts[idx + 1]
                
                if "dev" in parts:
                    idx = parts.index("dev")
                    if idx + 1 < len(parts):
                        route["device"] = parts[idx + 1]
                
                routes.append(route)
        
        return routes
    
    def _parse_systemctl(self, output: str) -> Dict[str, Any]:
        """Parse systemctl list-units output"""
        lines = output.strip().split('\n')
        services = []
        
        for line in lines[1:]:  # Skip header
            if not line.strip() or line.startswith("LOAD") or line.startswith("●"):
                continue
                
            parts = line.split(None, 4)
            if len(parts) >= 5 and ".service" in parts[0]:
                service_name = parts[0]
                services.append({
                    "name": service_name,
                    "load": parts[1],
                    "active": parts[2],
                    "sub": parts[3],
                    "description": parts[4]
                })
        
        # Count services by state
        active_count = sum(1 for s in services if s["active"] == "active")
        
        return {
            "services": services[:20],  # Limit to 20 services
            "total_count": len(services),
            "active_count": active_count,
            "inactive_count": len(services) - active_count
        }
    
    def _parse_failed_services(self, output: str) -> Dict[str, Any]:
        """Parse systemctl --failed output"""
        lines = output.strip().split('\n')
        failed_services = []
        
        for line in lines[1:]:  # Skip header
            if not line.strip() or line.startswith("LOAD") or line.startswith("●"):
                continue
                
            parts = line.split(None, 4)
            if len(parts) >= 5 and ".service" in parts[0]:
                service_name = parts[0]
                failed_services.append({
                    "name": service_name,
                    "load": parts[1],
                    "active": parts[2],
                    "sub": parts[3],
                    "description": parts[4]
                })
        
        return {
            "failed_services": failed_services,
            "failed_count": len(failed_services)
        }
    
    def _parse_journalctl(self, output: str) -> Dict[str, Any]:
        """Parse journalctl output"""
        lines = output.strip().split('\n')
        entries = []
        
        for line in lines:
            if line.strip():
                # Extract timestamp if present
                timestamp = None
                message = line
                
                if line[0:4].isdigit() and line[4] == "-" and line[7] == "-":
                    # Simple timestamp extraction
                    parts = line.split(" ", 3)
                    if len(parts) >= 4:
                        timestamp = f"{parts[0]} {parts[1]}"
                        message = parts[3]
                
                entries.append({
                    "timestamp": timestamp,
                    "message": message
                })
        
        return {
            "entries": entries,
            "count": len(entries)
        }
    
    def _parse_journal_errors(self, output: str) -> Dict[str, Any]:
        """Parse journalctl error output"""
        # Reuse the journalctl parser
        return self._parse_journalctl(output)
    
    def _parse_login_attempts(self, output: str) -> Dict[str, Any]:
        """Parse journalctl login attempts"""
        # Reuse the journalctl parser but look for specific patterns
        result = self._parse_journalctl(output)
        
        # Count failed login attempts
        failed_count = sum(1 for entry in result["entries"] if "Failed password" in entry["message"])
        successful_count = sum(1 for entry in result["entries"] if "Accepted password" in entry["message"])
        
        result["failed_count"] = failed_count
        result["successful_count"] = successful_count
        
        return result
    
    def _parse_listening_programs(self, output: str) -> Dict[str, Any]:
        """Parse netstat -tulnp output"""
        lines = output.strip().split('\n')
        programs = []
        
        for line in lines[2:]:  # Skip headers
            parts = line.split()
            if len(parts) >= 7 and ("LISTEN" in parts):
                protocol = parts[0]
                local_address = parts[3]
                
                # Extract port
                port = None
                if ":" in local_address:
                    port = local_address.split(":")[-1]
                
                # Extract program
                program = "unknown"
                if "/" in parts[-1]:
                    program = parts[-1].split("/")[-1]
                
                programs.append({
                    "protocol": protocol,
                    "local_address": local_address,
                    "port": port,
                    "program": program
                })
        
        return {
            "listening_programs": programs,
            "count": len(programs)
        }
    
    def _parse_load_avg(self, output: str) -> Dict[str, Any]:
        """Parse /proc/loadavg output"""
        parts = output.strip().split()
        
        return {
            "load_1min": float(parts[0]) if len(parts) > 0 else None,
            "load_5min": float(parts[1]) if len(parts) > 1 else None,
            "load_15min": float(parts[2]) if len(parts) > 2 else None,
            "running_processes": parts[3].split('/')[0] if len(parts) > 3 else None,
            "total_processes": parts[3].split('/')[1] if len(parts) > 3 else None,
            "last_pid": parts[4] if len(parts) > 4 else None
        }
    
    def _parse_cpu_info(self, output: str) -> Dict[str, Any]:
        """Parse lscpu output"""
        lines = output.strip().split('\n')
        cpu_info = {}
        
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                cpu_info[key.strip()] = value.strip()
        
        return cpu_info


# Test function to demonstrate the investigator
def test_investigator():
    """Test the server investigator functionality"""
    investigator = ServerInvestigator()
    
    # Get available tools
    tools = investigator.get_available_tools()
    print(f"Available tools: {tools['total_count']}")
    
    # Perform an investigation
    results = investigator.investigate("Check system performance")
    
    # Print results
    print("\nInvestigation Results:")
    print(f"Focus areas: {results['current_focus_areas']}")
    
    print("\nInsights:")
    for insight in results['insights']:
        print(f"[{insight['importance'].upper()}] {insight['description']}")
    
    print("\nNext Steps:")
    for i, step in enumerate(results['next_steps']):
        print(f"{i+1}. {step['description']} (Tools: {', '.join(step['tools'])})")
    
    # Save results
    results_file = "/tmp/deus-ex-machina/investigation_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {results_file}")

if __name__ == "__main__":
    test_investigator()