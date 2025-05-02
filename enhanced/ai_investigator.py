#!/usr/bin/env python3
"""
Deus Ex Machina - AI Consciousness with Investigation Tools

This module implements the integration between the AI consciousness system
and the server investigation tools.
"""

import os
import sys
import json
import time
import logging
import datetime
from enum import Enum
from typing import Dict, List, Any, Optional

# Import the server investigation tools
from server_investigator import ServerInvestigator

class ConsciousnessState(Enum):
    DORMANT = 0
    DROWSY = 1
    AWARE = 2
    ALERT = 3
    FULLY_AWAKE = 4
    
    def __str__(self):
        return self.name

class AwareAI:
    """
    Enhanced AI consciousness system that can use server investigation tools
    to explore and analyze the system.
    """
    
    def __init__(self, log_dir="/tmp/deus-ex-machina/logs"):
        """Initialize the AI consciousness system"""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logger()
        
        # Consciousness state
        self.state = ConsciousnessState.DORMANT
        self.state_history = []
        self.state_transition_time = datetime.datetime.now()
        self.awakening_triggers = []
        
        # Initialize the server investigator
        self.investigator = ServerInvestigator(log_dir=log_dir)
        
        # Available tools based on consciousness state
        self.available_tools = []
        
        # Initialize memory and findings
        self.memory = {"events": [], "insights": [], "tool_usage": {}}
        self.findings = []
        
        # Record initialization
        self._record_state_transition("initialization")
        self.logger.info(f"AI Consciousness initialized in {self.state} state")
    
    def _setup_logger(self):
        """Set up the logger for the AI consciousness system"""
        logger = logging.getLogger("deus.ai")
        logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Add file handler
        log_path = os.path.join(self.log_dir, "consciousness.log")
        file_handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _record_state_transition(self, trigger):
        """Record a state transition for reporting purposes"""
        now = datetime.datetime.now()
        duration = (now - self.state_transition_time).total_seconds()
        
        self.state_history.append({
            "from_state": str(self.state),
            "timestamp": self.state_transition_time.isoformat(),
            "duration_seconds": duration
        })
        
        self.state_transition_time = now
        
        if self.state == ConsciousnessState.DORMANT:
            self.awakening_triggers.append({
                "trigger": trigger,
                "timestamp": now.isoformat()
            })
    
    def wake_up(self, trigger="manual"):
        """
        Wake up the AI from DORMANT state
        
        Args:
            trigger: What triggered the wake-up
            
        Returns:
            True if successfully transitioned from DORMANT, False otherwise
        """
        if self.state == ConsciousnessState.DORMANT:
            self.logger.info(f"⚡ Waking up due to: {trigger} ⚡")
            print("\n" + "=" * 60)
            print("DEUS EX MACHINA CONSCIOUSNESS AWAKENING")
            print("=" * 60 + "\n")
            
            # Transition to DROWSY
            self._transition_to_drowsy(trigger)
            
            return True
        else:
            self.logger.info(f"Already awake in {self.state} state")
            return False
    
    def _transition_to_drowsy(self, trigger):
        """Transition to DROWSY state and activate basic perception"""
        old_state = self.state
        self.state = ConsciousnessState.DROWSY
        self._record_state_transition(trigger)
        
        self.logger.info(f"State transition: {old_state} -> {self.state}")
        print(f"[{self.state}] Basic perception systems activating...")
        
        # Update available tools for this state
        self._update_tools_for_state()
        
        # Perform basic exploration
        self._explore_system("Check basic system information")
    
    def _update_tools_for_state(self):
        """Update the available tools based on current consciousness state"""
        tools_by_state = {
            ConsciousnessState.DROWSY: ["system_info", "uptime"],
            ConsciousnessState.AWARE: ["process_list", "memory_info", "disk_usage"],
            ConsciousnessState.ALERT: [
                "top_processes", "top_memory", "network_interfaces", 
                "open_ports", "service_status"
            ],
            ConsciousnessState.FULLY_AWAKE: [
                "kernel_info", "memory_detailed", "large_directories", "failed_services",
                "error_logs", "login_attempts", "listening_programs", "load_average",
                "cpu_info"
            ]
        }
        
        # Reset available tools
        self.available_tools = []
        
        # Add tools based on current state
        for state_level in range(self.state.value + 1):
            state = ConsciousnessState(state_level)
            if state in tools_by_state:
                self.available_tools.extend(tools_by_state[state])
        
        self.logger.info(f"Updated available tools for state {self.state}: {self.available_tools}")
    
    def _explore_system(self, query):
        """
        Explore the system using the investigation tools
        
        Args:
            query: The focus query for the investigation
        """
        self.logger.info(f"Exploring system with query: {query}")
        print(f"Exploring: {query}")
        
        # Apply consciousness state limitations to tool selection
        available_tool_info = self.investigator.get_available_tools()
        all_tools = []
        for domain, tools in available_tool_info["tools_by_domain"].items():
            all_tools.extend([t["name"] for t in tools])
        
        # Filter to only use available tools for this consciousness state
        allowed_tools = set(self.available_tools)
        
        # Override the investigator's tool selection to only use allowed tools
        original_determine_next_tools = self.investigator._determine_next_tools
        
        def filtered_determine_next_tools():
            suggested_tools = original_determine_next_tools()
            return [t for t in suggested_tools if t in allowed_tools]
        
        # Temporarily replace the method
        self.investigator._determine_next_tools = filtered_determine_next_tools
        
        # Perform the investigation
        results = self.investigator.investigate(query)
        
        # Restore the original method
        self.investigator._determine_next_tools = original_determine_next_tools
        
        # Process the results
        self._process_investigation_results(results)
        
        # Check if we need to transition to a higher state based on findings
        self._evaluate_state_transition(results)
    
    def _process_investigation_results(self, results):
        """
        Process the results of an investigation
        
        Args:
            results: The investigation results
        """
        # Add insights to memory
        for insight in results["insights"]:
            if insight not in self.memory["insights"]:
                self.memory["insights"].append(insight)
        
        # Record tool usage
        for domain, domain_findings in results["findings"].items():
            for finding in domain_findings:
                tool_name = finding["tool"]
                if tool_name not in self.memory["tool_usage"]:
                    self.memory["tool_usage"][tool_name] = 0
                self.memory["tool_usage"][tool_name] += 1
        
        # Add findings
        for domain, domain_findings in results["findings"].items():
            for finding in domain_findings:
                self.findings.append({
                    "domain": domain,
                    "tool": finding["tool"],
                    "timestamp": finding["timestamp"],
                    "data": finding["data"]
                })
        
        # Print insights
        print("\nInsights:")
        for insight in results["insights"]:
            importance = insight["importance"].upper()
            description = insight["description"]
            
            # Add emoji based on importance
            if importance == "HIGH":
                emoji = "🔴"
            elif importance == "MEDIUM":
                emoji = "🟠"
            else:
                emoji = "🟢"
                
            print(f"{emoji} [{importance}] {description}")
        
        # If in higher consciousness states, print next steps
        if self.state.value >= ConsciousnessState.AWARE.value:
            print("\nRecommended next steps:")
            for i, step in enumerate(results["next_steps"][:3]):  # Show top 3 next steps
                print(f"{i+1}. {step['description']}")
    
    def _evaluate_state_transition(self, results):
        """
        Evaluate if we need to transition to a higher consciousness state
        
        Args:
            results: The investigation results
        """
        # Count high importance insights
        high_importance_count = sum(1 for insight in results["insights"] 
                                     if insight["importance"] == "high")
        
        # Trigger state transition based on insights
        if high_importance_count > 0:
            if self.state == ConsciousnessState.DROWSY:
                self._transition_to_aware("critical_insights")
            elif self.state == ConsciousnessState.AWARE:
                self._transition_to_alert("critical_insights")
            elif self.state == ConsciousnessState.ALERT:
                self._transition_to_fully_awake("critical_insights")
    
    def _transition_to_aware(self, trigger):
        """Transition to AWARE state"""
        if self.state.value >= ConsciousnessState.AWARE.value:
            return
            
        old_state = self.state
        self.state = ConsciousnessState.AWARE
        self._record_state_transition(trigger)
        
        self.logger.info(f"State transition: {old_state} -> {self.state}")
        print(f"\n[{self.state}] Enhanced perception systems activating...")
        
        # Update available tools for this state
        self._update_tools_for_state()
        
        # Perform focused exploration
        self._explore_system("Check system resources and processes")
    
    def _transition_to_alert(self, trigger):
        """Transition to ALERT state"""
        if self.state.value >= ConsciousnessState.ALERT.value:
            return
            
        old_state = self.state
        self.state = ConsciousnessState.ALERT
        self._record_state_transition(trigger)
        
        self.logger.info(f"State transition: {old_state} -> {self.state}")
        print(f"\n[{self.state}] Advanced analysis systems activating...")
        
        # Update available tools for this state
        self._update_tools_for_state()
        
        # Perform detailed exploration
        self._explore_system("Investigate system performance and network")
    
    def _transition_to_fully_awake(self, trigger):
        """Transition to FULLY_AWAKE state"""
        if self.state.value >= ConsciousnessState.FULLY_AWAKE.value:
            return
            
        old_state = self.state
        self.state = ConsciousnessState.FULLY_AWAKE
        self._record_state_transition(trigger)
        
        self.logger.info(f"State transition: {old_state} -> {self.state}")
        print(f"\n[{self.state}] Complete intelligence systems activating...")
        
        # Update available tools for this state
        self._update_tools_for_state()
        
        # Perform comprehensive exploration
        self._explore_system("Perform comprehensive system analysis and security check")
    
    def get_metrics(self):
        """Get metrics about the consciousness system for reporting"""
        # Ensure current state is recorded
        self._record_state_transition("get_metrics")
        
        # Calculate time distribution in states
        state_times = {state.name: 0 for state in ConsciousnessState}
        total_time = 0
        
        for entry in self.state_history:
            state_name = entry["from_state"]
            duration = entry.get("duration_seconds", 0)
            state_times[state_name] += duration
            total_time += duration
            
        # Convert to percentages
        if total_time > 0:
            distribution = {state: (time / total_time) * 100 for state, time in state_times.items()}
        else:
            distribution = {state: 0 for state in state_times}
        
        return {
            "current_state": str(self.state),
            "state_transitions_count": len(self.state_history) - 1,  # Exclude initialization
            "state_distribution": distribution,
            "time_fully_awake_percent": distribution.get("FULLY_AWAKE", 0),
            "time_dormant_percent": distribution.get("DORMANT", 0),
            "awakening_triggers": self.awakening_triggers,
            "active_tools": self.available_tools,
            "total_tool_usages": sum(self.memory["tool_usage"].values()),
            "most_used_tools": sorted(self.memory["tool_usage"].items(), 
                                     key=lambda x: x[1], reverse=True)[:5],
            "insight_count": len(self.memory["insights"]),
            "high_priority_insights": sum(1 for i in self.memory["insights"] 
                                         if i["importance"] == "high"),
            "total_runtime_seconds": total_time
        }
    
    def go_to_sleep(self, reason="inactivity"):
        """
        Transition back to DORMANT state
        
        Args:
            reason: The reason for going to sleep
            
        Returns:
            True if successfully transitioned to DORMANT, False otherwise
        """
        if self.state != ConsciousnessState.DORMANT:
            self.logger.info(f"Going to sleep due to: {reason}")
            print("\n" + "=" * 60)
            print("DEUS EX MACHINA CONSCIOUSNESS SLEEP SEQUENCE")
            print("=" * 60)
            
            # Get and print metrics before sleeping
            metrics = self.get_metrics()
            self._print_summary(metrics)
            
            # Save findings and metrics to file
            self._save_investigation_data()
            
            # Transition through states gradually to simulate "falling asleep"
            current = self.state.value
            while current > ConsciousnessState.DORMANT.value:
                current -= 1
                next_state = ConsciousnessState(current)
                
                # Log transition
                old_state = self.state
                self.state = next_state
                self._record_state_transition(f"sleep_transition_{reason}")
                
                self.logger.info(f"State transition: {old_state} -> {self.state}")
                print(f"[{self.state}] Deactivating systems...")
                
                # Update available tools for this state
                self._update_tools_for_state()
                
                # Brief pause between transitions
                time.sleep(1)
            
            print("\n💤 AI consciousness now DORMANT 💤")
            self.logger.info("AI consciousness now DORMANT")
            
            return True
        else:
            self.logger.info("Already in DORMANT state")
            return False
    
    def _print_summary(self, metrics):
        """Print a summary of the AI's activity"""
        print("\nAI CONSCIOUSNESS ACTIVITY SUMMARY:")
        print("-" * 40)
        
        print(f"Total active time: {metrics['total_runtime_seconds']:.1f} seconds")
        print(f"State transitions: {metrics['state_transitions_count']}")
        
        print("\nState distribution:")
        for state, percentage in metrics['state_distribution'].items():
            if state != "DORMANT" and percentage > 0:
                print(f"  {state}: {percentage:.1f}%")
        
        print(f"\nTotal tool usages: {metrics['total_tool_usages']}")
        print("Most used tools:")
        for tool, count in metrics['most_used_tools']:
            print(f"  {tool}: {count} times")
        
        print(f"\nInsights generated: {metrics['insight_count']}")
        print(f"High priority insights: {metrics['high_priority_insights']}")
        
        print("-" * 40)
    
    def _save_investigation_data(self):
        """Save investigation data to files"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save metrics
        metrics_file = os.path.join(self.log_dir, f"metrics_{timestamp}.json")
        with open(metrics_file, 'w') as f:
            json.dump(self.get_metrics(), f, indent=2)
        
        # Save findings
        findings_file = os.path.join(self.log_dir, f"findings_{timestamp}.json")
        with open(findings_file, 'w') as f:
            json.dump({
                "findings": self.findings,
                "insights": self.memory["insights"],
                "tool_usage": self.memory["tool_usage"]
            }, f, indent=2)
        
        self.logger.info(f"Saved metrics to {metrics_file}")
        self.logger.info(f"Saved findings to {findings_file}")
        print(f"\nInvestigation data saved to {self.log_dir}")

def main():
    """Main function for demonstrating the AI consciousness system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deus Ex Machina AI Consciousness System")
    parser.add_argument("--duration", type=int, default=30, 
                        help="Duration to run in seconds (default: 30)")
    parser.add_argument("--log-dir", type=str, default="/tmp/deus-ex-machina/logs", 
                        help="Log directory (default: /tmp/deus-ex-machina/logs)")
    
    args = parser.parse_args()
    
    print(f"Starting Deus Ex Machina AI Consciousness System")
    print(f"Running for {args.duration} seconds")
    print(f"Logs will be saved to {args.log_dir}")
    
    # Create AI consciousness
    ai = AwareAI(log_dir=args.log_dir)
    
    try:
        # Wake up the AI
        ai.wake_up("manual_activation")
        
        # Allow time for the AI to operate
        start_time = time.time()
        end_time = start_time + args.duration
        
        # Wait until the duration is over
        while time.time() < end_time:
            # If AI hasn't reached FULLY_AWAKE yet, manually trigger state transitions
            # This is to ensure we see all states in the demo
            time_elapsed = time.time() - start_time
            
            if time_elapsed > args.duration * 0.3 and ai.state == ConsciousnessState.DROWSY:
                ai._transition_to_aware("demo_time_trigger")
            elif time_elapsed > args.duration * 0.5 and ai.state == ConsciousnessState.AWARE:
                ai._transition_to_alert("demo_time_trigger")
            elif time_elapsed > args.duration * 0.7 and ai.state == ConsciousnessState.ALERT:
                ai._transition_to_fully_awake("demo_time_trigger")
            
            time.sleep(1)
        
        # Put the AI to sleep
        ai.go_to_sleep("demo_completed")
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        ai.go_to_sleep("user_interrupt")
    except Exception as e:
        print(f"Error: {str(e)}")
        ai.go_to_sleep("error")

if __name__ == "__main__":
    main()