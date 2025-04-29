#!/usr/bin/env python3
"""
Main runner script for Deus Ex Machina Enhanced
Starts the consciousness system and monitors the environment
"""
import os
import sys
import time
import logging
import argparse
from datetime import datetime

# Add the enhanced directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "enhanced"))

# Import components
from config import CONFIG
from consciousness import Consciousness, ConsciousnessState
from ai_providers import AIProviderManager
from action_grammar import ActionGrammar

# Set up logging
log_file = os.path.join(CONFIG["log_dir"], "enhanced.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("deus-enhanced")

# Log startup information
logger.info(f"Starting Deus Ex Machina Enhanced, logging to {log_file}")

def generate_sample_data():
    """Generate some sample system data for testing"""
    import random
    
    # System information
    system_info = {
        "hostname": "test-server",
        "uptime_days": 45,
        "os_version": "Ubuntu 20.04.5 LTS",
        "kernel": "5.4.0-100-generic"
    }
    
    # Log data
    log_data = """
    Apr 28 12:34:56 test-server systemd[1]: Started System Logging Service.
    Apr 28 12:35:02 test-server kernel: [    0.000000] Memory: 8046784K/8046784K available
    Apr 28 12:36:15 test-server kernel: [   15.356356] EXT4-fs (sda1): mounted filesystem
    Apr 28 12:38:22 test-server nginx[1234]: 192.168.1.1 - - [28/Apr/2025:12:38:22 +0000] "GET / HTTP/1.1" 200 1024
    Apr 28 12:38:42 test-server sshd[1235]: Failed password for invalid user admin from 203.0.113.1 port 48351 ssh2
    """
    
    # Metrics data - add some randomness
    metrics_data = {
        "cpu_load_percent": random.uniform(30, 75),
        "memory_used_percent": random.uniform(50, 80),
        "disk_usage": {
            "/": random.uniform(65, 85),
            "/var": random.uniform(40, 60)
        },
        "load_trend": random.uniform(-0.1, 0.2)
    }
    
    return system_info, log_data, metrics_data

def run_consciousness_demo():
    """Run a demonstration of the consciousness system"""
    logger.info("Starting consciousness demonstration")
    
    # Create the consciousness system
    consciousness = Consciousness(
        install_dir=CONFIG["install_dir"],
        log_dir=CONFIG["log_dir"],
        initial_state=ConsciousnessState[CONFIG["consciousness"]["initial_state"]]
    )
    
    # Create the AI provider manager
    ai_manager = AIProviderManager(CONFIG["ai_providers"])
    
    # Create the action grammar system
    action_grammar = ActionGrammar(
        max_permission_level=CONFIG["max_permission_level"],
        log_dir=CONFIG["log_dir"]
    )
    
    # Register handlers for different consciousness states
    def handle_dormant(transition):
        logger.info("DORMANT state handler: Minimal functionality active")
        
    def handle_drowsy(transition):
        logger.info("DROWSY state handler: Running light analysis")
        # Generate test data
        system_info, log_data, metrics_data = generate_sample_data()
        # Light analysis with local AI only
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Light analysis result: {result['summary']}")
        
    def handle_aware(transition):
        logger.info("AWARE state handler: Running regular analysis")
        # Generate test data
        system_info, log_data, metrics_data = generate_sample_data()
        # Regular analysis
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Regular analysis result: {result['summary']}")
        
        # Create and execute a simple action sequence
        df_action = action_grammar.create_command_action(
            name="check_disk_space",
            command=["df", "-h"],
            permission_level="OBSERVE"
        )
        
        sequence = action_grammar.create_sequence(
            name="system_check",
            description="Basic system status check",
            actions=[df_action]
        )
        
        result = action_grammar.execute_sequence(sequence)
        logger.info(f"Action sequence result: {result['success']}")
        
    def handle_alert(transition):
        logger.info("ALERT state handler: Running enhanced analysis")
        # Generate test data with high values
        system_info, log_data, metrics_data = generate_sample_data()
        metrics_data["cpu_load_percent"] = 92.5  # Simulate high CPU
        
        # Enhanced analysis
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Enhanced analysis result: {result['summary']}")
        logger.info(f"Issues detected: {result['issues']}")
        logger.info(f"Recommendations: {result['recommendations']}")
        
    def handle_fully_awake(transition):
        logger.info("FULLY_AWAKE state handler: Running comprehensive analysis and actions")
        # Generate test data with critical values
        system_info, log_data, metrics_data = generate_sample_data()
        metrics_data["cpu_load_percent"] = 96.5  # Simulate critical CPU
        metrics_data["disk_usage"]["/"] = 96.2  # Simulate critical disk usage
        
        # Comprehensive analysis
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Comprehensive analysis result: {result['summary']}")
        logger.info(f"Issues detected: {result['issues']}")
        logger.info(f"Recommendations: {result['recommendations']}")
        
        # Create and execute a more complex action sequence
        actions = []
        
        # Check disk space
        actions.append(action_grammar.create_command_action(
            name="check_disk_space",
            command=["df", "-h"],
            permission_level="OBSERVE"
        ))
        
        # Find large files
        actions.append(action_grammar.create_command_action(
            name="find_large_files",
            command=["find", "/tmp", "-type", "f", "-size", "+10M", "-ls"],
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
    
    # Register the handlers
    consciousness.register_handler(ConsciousnessState.DORMANT, handle_dormant)
    consciousness.register_handler(ConsciousnessState.DROWSY, handle_drowsy)
    consciousness.register_handler(ConsciousnessState.AWARE, handle_aware)
    consciousness.register_handler(ConsciousnessState.ALERT, handle_alert)
    consciousness.register_handler(ConsciousnessState.FULLY_AWAKE, handle_fully_awake)
    
    # Start the consciousness system
    consciousness.start(check_interval=CONFIG["consciousness"]["check_interval"])
    
    try:
        # Simulate state transitions for demonstration
        logger.info("Starting state transition demonstration...")
        
        # Initial state info
        current_state = consciousness.get_current_state()
        logger.info(f"Initial state: {current_state.name}")
        logger.info("Waiting for initial state handler to execute...")
        time.sleep(5)
        
        # Transition through all states
        logger.info("Transitioning to DROWSY...")
        consciousness.change_state(ConsciousnessState.DROWSY, "Manual transition for demonstration")
        time.sleep(5)
        
        logger.info("Transitioning to AWARE...")
        consciousness.change_state(ConsciousnessState.AWARE, "Manual transition for demonstration")
        time.sleep(5)
        
        logger.info("Transitioning to ALERT...")
        consciousness.change_state(ConsciousnessState.ALERT, "Manual transition for demonstration")
        time.sleep(5)
        
        logger.info("Transitioning to FULLY_AWAKE...")
        consciousness.change_state(ConsciousnessState.FULLY_AWAKE, "Manual transition for demonstration")
        time.sleep(5)
        
        logger.info("Transitioning back to AWARE...")
        consciousness.change_state(ConsciousnessState.AWARE, "Manual transition for demonstration")
        time.sleep(5)
        
        # Print state info
        state_info = consciousness.get_state_info()
        logger.info(f"Final state info: {state_info}")
        
        # Log some stats
        logger.info("Demonstration completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Demonstration interrupted by user")
    finally:
        # Stop the consciousness system
        consciousness.stop()
        logger.info("Consciousness system stopped")

def run_service():
    """Run as a continuous service"""
    logger.info("Starting Deus Ex Machina Enhanced as a service")
    
    # Create the consciousness system
    consciousness = Consciousness(
        install_dir=CONFIG["install_dir"],
        log_dir=CONFIG["log_dir"],
        initial_state=ConsciousnessState[CONFIG["consciousness"]["initial_state"]]
    )
    
    # Create the AI provider manager
    ai_manager = AIProviderManager(CONFIG["ai_providers"])
    
    # Create the action grammar system
    action_grammar = ActionGrammar(
        max_permission_level=CONFIG["max_permission_level"],
        log_dir=CONFIG["log_dir"]
    )
    
    # Register handlers for different consciousness states
    def handle_dormant(transition):
        logger.info("DORMANT state handler: Minimal functionality active")
        
    def handle_drowsy(transition):
        logger.info("DROWSY state handler: Running light analysis")
        # Generate test data
        system_info, log_data, metrics_data = generate_sample_data()
        # Light analysis with local AI only
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Light analysis result: {result['summary']}")
        
    def handle_aware(transition):
        logger.info("AWARE state handler: Running regular analysis")
        # Generate test data
        system_info, log_data, metrics_data = generate_sample_data()
        # Regular analysis
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Regular analysis result: {result['summary']}")
        
        # Create and execute a simple action sequence
        df_action = action_grammar.create_command_action(
            name="check_disk_space",
            command=["df", "-h"],
            permission_level="OBSERVE"
        )
        
        sequence = action_grammar.create_sequence(
            name="system_check",
            description="Basic system status check",
            actions=[df_action]
        )
        
        result = action_grammar.execute_sequence(sequence)
        logger.info(f"Action sequence result: {result['success']}")
        
    def handle_alert(transition):
        logger.info("ALERT state handler: Running enhanced analysis")
        # Generate test data with high values
        system_info, log_data, metrics_data = generate_sample_data()
        metrics_data["cpu_load_percent"] = 92.5  # Simulate high CPU
        
        # Enhanced analysis
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Enhanced analysis result: {result['summary']}")
        logger.info(f"Issues detected: {result['issues']}")
        logger.info(f"Recommendations: {result['recommendations']}")
        
    def handle_fully_awake(transition):
        logger.info("FULLY_AWAKE state handler: Running comprehensive analysis and actions")
        # Generate test data with critical values
        system_info, log_data, metrics_data = generate_sample_data()
        metrics_data["cpu_load_percent"] = 96.5  # Simulate critical CPU
        metrics_data["disk_usage"]["/"] = 96.2  # Simulate critical disk usage
        
        # Comprehensive analysis
        result = ai_manager.analyze(system_info, log_data, metrics_data)
        logger.info(f"Comprehensive analysis result: {result['summary']}")
        logger.info(f"Issues detected: {result['issues']}")
        logger.info(f"Recommendations: {result['recommendations']}")
        
        # Create and execute a more complex action sequence
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
    
    # Register the handlers
    consciousness.register_handler(ConsciousnessState.DORMANT, handle_dormant)
    consciousness.register_handler(ConsciousnessState.DROWSY, handle_drowsy)
    consciousness.register_handler(ConsciousnessState.AWARE, handle_aware)
    consciousness.register_handler(ConsciousnessState.ALERT, handle_alert)
    consciousness.register_handler(ConsciousnessState.FULLY_AWAKE, handle_fully_awake)
    
    # Start the consciousness system
    consciousness.start(check_interval=CONFIG["consciousness"]["check_interval"])
    
    try:
        # Keep the service running
        logger.info("Service running, press Ctrl+C to exit")
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    finally:
        # Stop the consciousness system
        consciousness.stop()
        logger.info("Consciousness system stopped")

def run_analysis_test():
    """Test the analysis logic using current system state"""
    logger.info("Starting analysis test")
    
    # Create the consciousness system
    consciousness = Consciousness(
        install_dir=CONFIG["install_dir"],
        log_dir=CONFIG["log_dir"],
        initial_state=ConsciousnessState.AWARE
    )
    
    # Test each level of analysis
    for state_name, state in [
        ("DROWSY", ConsciousnessState.DROWSY),
        ("AWARE", ConsciousnessState.AWARE),
        ("ALERT", ConsciousnessState.ALERT),
        ("FULLY_AWAKE", ConsciousnessState.FULLY_AWAKE)
    ]:
        logger.info(f"=== Testing {state_name} state analysis ===")
        
        # Set the consciousness state
        consciousness.state = state
        
        # Force analysis based on state
        if state == ConsciousnessState.DROWSY:
            # Clear the last activity to force execution
            consciousness.last_activity.pop("drowsy_analysis", None)
            # Run the state activities check
            consciousness._check_state_activities()
            
        elif state == ConsciousnessState.AWARE:
            # Clear the last activity to force execution
            consciousness.last_activity.pop("aware_analysis", None)
            # Run the state activities check
            consciousness._check_state_activities()
            
        elif state == ConsciousnessState.ALERT:
            # Clear the last activity to force execution
            consciousness.last_activity.pop("alert_analysis", None)
            # Run the state activities check
            consciousness._check_state_activities()
            
        elif state == ConsciousnessState.FULLY_AWAKE:
            # Clear the last activity to force execution
            consciousness.last_activity.pop("full_analysis", None)
            # Run the state activities check
            consciousness._check_state_activities()
    
    logger.info("Analysis testing completed")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Deus Ex Machina Enhanced')
    parser.add_argument('--demo', action='store_true', help='Run a demonstration')
    parser.add_argument('--initialize', action='store_true', help='Initialize the database')
    parser.add_argument('--service', action='store_true', help='Run as a continuous service')
    parser.add_argument('--test-analysis', action='store_true', help='Test the analysis logic with current system state')
    args = parser.parse_args()
    
    # Make sure directories exist
    os.makedirs(CONFIG["log_dir"], exist_ok=True)
    os.makedirs(CONFIG["db_dir"], exist_ok=True)
    
    # Initialize database if requested
    if args.initialize:
        from initialize_db import initialize_database
        initialize_database(CONFIG["database_path"])
    
    # Run demo if requested
    if args.demo:
        run_consciousness_demo()
    # Run as service if requested
    elif args.service:
        run_service()
    # Test analysis logic if requested
    elif args.test_analysis:
        run_analysis_test()
    else:
        print("No action specified. Use --demo to run a demonstration, --initialize to set up the database, --service to run as a continuous service, or --test-analysis to test the analysis logic.")

if __name__ == "__main__":
    main()