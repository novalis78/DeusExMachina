#!/usr/bin/env python3
"""
Consciousness Simulation Script

Simulates the Deus Ex Machina system transitioning through different 
consciousness states and using tools to investigate the system.
This creates realistic activity in the logs for testing the reporting features.
"""
import os
import sys
import time
import random
import logging
import argparse
import json
from datetime import datetime

# Add the enhanced directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the necessary modules
from consciousness import Consciousness, ConsciousnessState
from ai_providers import AIProviderManager
from action_grammar import ActionGrammar
from config import CONFIG

# Set up logging
log_dir = CONFIG["log_dir"]
log_file = os.path.join(log_dir, "enhanced.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("deus-enhanced-sim")

class SystemEvent:
    """Represents a system event that could trigger consciousness changes"""
    def __init__(self, name, description, severity, cpu_impact=0, memory_impact=0):
        self.name = name
        self.description = description
        self.severity = severity  # LOW, MEDIUM, HIGH, CRITICAL
        self.cpu_impact = cpu_impact
        self.memory_impact = memory_impact
        
    def __str__(self):
        return f"{self.name} ({self.severity}): {self.description}"

def generate_events():
    """Generate a list of possible system events"""
    return [
        SystemEvent("high_cpu_usage", "Unusually high CPU usage detected", "HIGH", cpu_impact=75),
        SystemEvent("low_memory", "Available memory below threshold", "HIGH", memory_impact=-800),
        SystemEvent("disk_space_warning", "Disk space usage above 85%", "MEDIUM"),
        SystemEvent("failed_login_attempts", "Multiple failed SSH login attempts detected", "HIGH"),
        SystemEvent("process_crash", "Critical process unexpectedly terminated", "HIGH"),
        SystemEvent("network_spike", "Unusual network traffic spike detected", "MEDIUM"),
        SystemEvent("configuration_change", "System configuration file modified", "MEDIUM"),
        SystemEvent("new_user_created", "New user account created on the system", "MEDIUM"),
        SystemEvent("suspicious_cron_job", "Unusual cron job added to system", "HIGH"),
        SystemEvent("kernel_error", "Kernel error reported in system logs", "HIGH"),
        SystemEvent("service_failure", "Critical service failed to start", "HIGH"),
        SystemEvent("port_scan_detected", "External port scan detected", "MEDIUM"),
        SystemEvent("file_permission_change", "Critical file permissions changed", "MEDIUM"),
        SystemEvent("unusual_process", "Unknown process consuming system resources", "HIGH", cpu_impact=50),
        SystemEvent("database_error", "Database connection errors detected", "MEDIUM"),
        SystemEvent("application_error", "Application throwing repeated exceptions", "MEDIUM"),
        SystemEvent("backup_failure", "System backup process failed", "MEDIUM"),
        SystemEvent("certificate_expiration", "SSL certificate near expiration", "LOW"),
        SystemEvent("system_update_available", "Critical system updates available", "LOW"),
        SystemEvent("unusual_outbound_connection", "Unusual outbound network connections", "HIGH")
    ]

def simulate_consciousness_activity(duration_minutes=30, event_frequency=5):
    """Simulate the consciousness system activity for the specified duration"""
    logger.info(f"Starting consciousness simulation for {duration_minutes} minutes")
    
    # Initialize components
    consciousness = Consciousness(
        install_dir=CONFIG["install_dir"],
        log_dir=CONFIG["log_dir"],
        initial_state=ConsciousnessState.DORMANT
    )
    
    ai_manager = AIProviderManager(CONFIG["ai_providers"])
    
    action_grammar = ActionGrammar(
        max_permission_level=CONFIG["max_permission_level"],
        log_dir=CONFIG["log_dir"]
    )
    
    # Get events
    events = generate_events()
    logger.info(f"Generated {len(events)} possible system events")
    
    # Start the consciousness system
    consciousness.start(check_interval=10)  # Short interval for simulation
    logger.info(f"Consciousness system started in {consciousness.state.name} state")
    
    try:
        # Simulate for the specified duration
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            # Simulate passage of time
            current_state = consciousness.state
            
            # Maybe trigger an event
            if random.randint(1, 100) <= event_frequency:
                # Select a random event
                event = random.choice(events)
                logger.info(f"Event triggered: {event}")
                
                # Determine target state based on event severity
                target_state = None
                if event.severity == "LOW":
                    if current_state.value < ConsciousnessState.DROWSY.value:
                        target_state = ConsciousnessState.DROWSY
                elif event.severity == "MEDIUM":
                    if current_state.value < ConsciousnessState.AWARE.value:
                        target_state = ConsciousnessState.AWARE
                elif event.severity == "HIGH":
                    if current_state.value < ConsciousnessState.ALERT.value:
                        target_state = ConsciousnessState.ALERT
                elif event.severity == "CRITICAL":
                    if current_state.value < ConsciousnessState.FULLY_AWAKE.value:
                        target_state = ConsciousnessState.FULLY_AWAKE
                
                # Change state if needed
                if target_state and target_state.value > current_state.value:
                    consciousness.change_state(target_state, f"Responding to {event.name}: {event.description}")
                    logger.info(f"State changed to {target_state.name} due to {event.name}")
                
                # Simulate AI analysis
                simulate_ai_analysis(consciousness, ai_manager, action_grammar, event)
            
            # Simulate automatic state transitions (quieting down)
            if random.randint(1, 100) <= 10 and consciousness.state.value > ConsciousnessState.DORMANT.value:
                if consciousness.time_in_state() > datetime.timedelta(minutes=2):  # Shorter for simulation
                    new_state = ConsciousnessState(consciousness.state.value - 1)  # Step down one level
                    consciousness.change_state(new_state, "System returning to normal after monitoring")
                    logger.info(f"State automatically stepped down to {new_state.name}")
            
            # Wait a bit before next simulation step
            time.sleep(random.uniform(5, 15))  # Random interval for more realistic simulation
            
        logger.info("Simulation completed successfully")
        return True
        
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        return False
    finally:
        # Stop the consciousness system
        consciousness.stop()
        logger.info("Consciousness system stopped")

def simulate_ai_analysis(consciousness, ai_manager, action_grammar, event):
    """Simulate AI analysis based on consciousness state and event"""
    state = consciousness.state
    logger.info(f"AI analysis triggered in {state.name} state for event {event.name}")
    
    # Generate simulated system data
    system_info = {
        "hostname": "simulation-server",
        "uptime_days": random.randint(30, 90),
        "os_version": "Ubuntu 20.04.5 LTS",
        "kernel": "5.4.0-100-generic"
    }
    
    # Generate simulated metrics with the event's impact
    base_cpu = random.uniform(10, 30)
    base_memory = random.uniform(50, 80)
    base_disk = random.uniform(65, 85)
    
    if event.cpu_impact:
        base_cpu += event.cpu_impact
        
    if event.memory_impact:
        # For negative impact (memory loss), reduce free memory
        base_memory = max(5, base_memory + event.memory_impact if event.memory_impact < 0 else base_memory)
        
    metrics_data = {
        "cpu_load_percent": base_cpu,
        "memory_used_percent": base_memory,
        "disk_usage": {
            "/": base_disk,
            "/var": random.uniform(40, 60)
        },
        "load_trend": random.uniform(-0.1, 0.2)
    }
    
    # Generate simulated log data
    log_lines = [
        f"Apr 29 12:34:56 simulation-server systemd[1]: Started System Logging Service.",
        f"Apr 29 12:35:02 simulation-server kernel: [    0.000000] Memory: 8046784K/8046784K available",
        f"Apr 29 12:36:15 simulation-server kernel: [   15.356356] EXT4-fs (sda1): mounted filesystem"
    ]
    
    # Add event-specific log entries
    if event.name == "high_cpu_usage":
        log_lines.append(f"Apr 29 12:38:22 simulation-server kernel: CPU usage spike detected: {base_cpu}%")
    elif event.name == "low_memory":
        log_lines.append(f"Apr 29 12:38:22 simulation-server kernel: Low memory warning: {100-base_memory}% free")
    elif event.name == "failed_login_attempts":
        log_lines.append(f"Apr 29 12:38:42 simulation-server sshd[1235]: Failed password for invalid user admin from 203.0.113.1 port 48351 ssh2")
        log_lines.append(f"Apr 29 12:38:45 simulation-server sshd[1236]: Failed password for invalid user root from 203.0.113.1 port 48355 ssh2")
    elif "error" in event.name.lower():
        log_lines.append(f"Apr 29 12:38:22 simulation-server kernel: ERROR: {event.description}")
        
    log_data = "\n".join(log_lines)
    
    # Simulate AI analysis based on state
    if state == ConsciousnessState.DROWSY:
        logger.info("Performing light analysis")
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Light analysis result: {result['summary']}")
        
    elif state == ConsciousnessState.AWARE:
        logger.info("Performing regular analysis")
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Regular analysis result: {result['summary']}")
        
        # Simulate simple action
        action = action_grammar.create_command_action(
            name="check_disk_space",
            command=["df", "-h"],
            permission_level="OBSERVE"
        )
        
        sequence = action_grammar.create_sequence(
            name="system_check",
            description="Basic system status check",
            actions=[action]
        )
        
        result = action_grammar.execute_sequence(sequence)
        logger.info(f"Action sequence result: {result['success']}")
        
    elif state == ConsciousnessState.ALERT:
        logger.info("Performing enhanced analysis")
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Enhanced analysis result: {result['summary']}")
        logger.info(f"Issues detected: {result['issues']}")
        logger.info(f"Recommendations: {result['recommendations']}")
        
    elif state == ConsciousnessState.FULLY_AWAKE:
        logger.info("Performing comprehensive analysis")
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Comprehensive analysis result: {result['summary']}")
        logger.info(f"Issues detected: {result['issues']}")
        logger.info(f"Recommendations: {result['recommendations']}")
        
        # Simulate more complex action sequence
        actions = []
        
        # Check disk space
        actions.append(action_grammar.create_command_action(
            name="check_disk_space",
            command=["df", "-h"],
            permission_level="OBSERVE"
        ))
        
        # Check process list
        actions.append(action_grammar.create_command_action(
            name="check_processes",
            command=["ps", "aux", "--sort=-pcpu"],
            permission_level="OBSERVE"
        ))
        
        sequence = action_grammar.create_sequence(
            name="critical_investigation",
            description="Investigate critical system issues",
            actions=actions
        )
        
        result = action_grammar.execute_sequence(sequence)
        logger.info(f"Comprehensive action sequence result: {result['success']}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Simulate Deus Ex Machina consciousness activity')
    parser.add_argument('--duration', type=int, default=30, help='Simulation duration in minutes')
    parser.add_argument('--frequency', type=int, default=15, help='Event frequency (percentage chance per check)')
    args = parser.parse_args()
    
    # Make sure log directory exists
    os.makedirs(CONFIG["log_dir"], exist_ok=True)
    
    # Run the simulation
    logger.info(f"Starting consciousness simulation for {args.duration} minutes with event frequency {args.frequency}%")
    simulate_consciousness_activity(args.duration, args.frequency)

if __name__ == "__main__":
    main()