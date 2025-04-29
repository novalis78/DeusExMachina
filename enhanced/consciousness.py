#!/usr/bin/env python3
"""
Consciousness Module - Implement biological-like consciousness patterns
Manages awareness states from dormant to fully awake based on system conditions
"""
import os
import sys
import json
import logging
import time
import math
import random
import threading
import signal
import queue
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum, auto

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('consciousness')

# Default paths
DEFAULT_INSTALL_DIR = "/opt/deus-ex-machina"
DEFAULT_LOG_DIR = "/var/log/deus-ex-machina"
CONSCIOUSNESS_STATE_FILE = "consciousness_state.json"

class ConsciousnessState(Enum):
    """Different consciousness states of the system"""
    DORMANT = auto()       # Lowest resource usage, biological systems only
    DROWSY = auto()        # Periodic light processing of accumulated data
    AWARE = auto()         # Regular moderate AI analysis
    ALERT = auto()         # Enhanced monitoring due to anomalies
    FULLY_AWAKE = auto()   # Full AI analysis and active problem-solving

class ConsciousnessTransition:
    """Represents a transition between consciousness states"""
    
    def __init__(self, 
                from_state: ConsciousnessState,
                to_state: ConsciousnessState,
                reason: str,
                timestamp: Optional[datetime] = None):
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason
        self.timestamp = timestamp or datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "from_state": self.from_state.name,
            "to_state": self.to_state.name,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat()
        }

class Consciousness:
    """Main class for managing system consciousness"""
    
    def __init__(self, 
                install_dir: str = DEFAULT_INSTALL_DIR,
                log_dir: str = DEFAULT_LOG_DIR,
                initial_state: ConsciousnessState = ConsciousnessState.DORMANT):
        self.install_dir = install_dir
        self.log_dir = log_dir
        self.state = initial_state
        self.state_file = os.path.join(log_dir, CONSCIOUSNESS_STATE_FILE)
        self.state_history = []
        self.last_state_change = datetime.now()
        self.last_activity = {}  # Type -> timestamp mapping
        self.active = False
        self.thread = None
        self.state_queue = queue.Queue()
        self.event_handlers = {}
        self.logger = logging.getLogger('consciousness')
        
        # Load state from file if it exists
        self._load_state()
        
    def _load_state(self) -> None:
        """Load consciousness state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                    
                # Set state
                if "state" in state_data:
                    try:
                        self.state = ConsciousnessState[state_data["state"]]
                    except (KeyError, ValueError):
                        self.logger.warning(f"Invalid state in state file: {state_data['state']}")
                        
                # Load history
                if "history" in state_data:
                    for entry in state_data["history"]:
                        try:
                            from_state = ConsciousnessState[entry["from_state"]]
                            to_state = ConsciousnessState[entry["to_state"]]
                            reason = entry["reason"]
                            timestamp = datetime.fromisoformat(entry["timestamp"])
                            
                            transition = ConsciousnessTransition(
                                from_state=from_state,
                                to_state=to_state,
                                reason=reason,
                                timestamp=timestamp
                            )
                            
                            self.state_history.append(transition)
                        except (KeyError, ValueError) as e:
                            self.logger.warning(f"Error loading history entry: {str(e)}")
                            
                # Load last activity timestamps
                if "last_activity" in state_data:
                    for activity, timestamp_str in state_data["last_activity"].items():
                        try:
                            self.last_activity[activity] = datetime.fromisoformat(timestamp_str)
                        except ValueError:
                            self.logger.warning(f"Invalid timestamp for activity {activity}")
                            
                self.logger.info(f"Loaded consciousness state: {self.state.name}")
        except Exception as e:
            self.logger.error(f"Error loading state: {str(e)}")
            
    def _save_state(self) -> None:
        """Save consciousness state to file"""
        try:
            # Prepare state data
            state_data = {
                "state": self.state.name,
                "last_updated": datetime.now().isoformat(),
                "history": [t.to_dict() for t in self.state_history[-50:]],  # Only keep last 50 transitions
                "last_activity": {k: v.isoformat() for k, v in self.last_activity.items()}
            }
            
            # Make sure the directory exists
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            # Write to file
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
            self.logger.debug("Saved consciousness state")
        except Exception as e:
            self.logger.error(f"Error saving state: {str(e)}")
            
    def change_state(self, new_state: ConsciousnessState, reason: str) -> bool:
        """Change the consciousness state"""
        if new_state == self.state:
            return False
            
        # Create a state transition
        transition = ConsciousnessTransition(
            from_state=self.state,
            to_state=new_state,
            reason=reason
        )
        
        # Record the transition
        self.state_history.append(transition)
        
        # Update state and timestamp
        old_state = self.state
        self.state = new_state
        self.last_state_change = datetime.now()
        
        # Log the change
        self.logger.info(f"Consciousness state changed: {old_state.name} -> {new_state.name} ({reason})")
        
        # Save state to file
        self._save_state()
        
        # Put transition in queue for processing
        self.state_queue.put(transition)
        
        # Trigger event handlers
        self._trigger_handlers(old_state, new_state, reason)
        
        return True
        
    def get_current_state(self) -> ConsciousnessState:
        """Get the current consciousness state"""
        return self.state
        
    def get_state_history(self, max_entries: int = 10) -> List[Dict[str, Any]]:
        """Get recent state transitions"""
        return [t.to_dict() for t in self.state_history[-max_entries:]]
        
    def log_activity(self, activity_type: str) -> None:
        """Log an activity to reset sleep timers"""
        self.last_activity[activity_type] = datetime.now()
        self._save_state()
        
    def time_since_activity(self, activity_type: str) -> Optional[timedelta]:
        """Get time since last activity of given type"""
        if activity_type in self.last_activity:
            return datetime.now() - self.last_activity[activity_type]
        return None
        
    def should_transition(self, target_state: ConsciousnessState) -> Optional[str]:
        """
        Check if system should transition to the target state
        Returns reason for transition or None if no transition needed
        """
        current_state = self.state
        
        # Don't transition to the same state
        if current_state == target_state:
            return None
            
        # Implement transition logic based on current state
        if current_state == ConsciousnessState.DORMANT:
            # Dormant can transition to any higher state
            if target_state == ConsciousnessState.DROWSY:
                # Periodic waking from timers
                drowsy_interval = timedelta(hours=8)  # Wake up every 8 hours
                time_since_last_drowsy = self.time_since_state_change(ConsciousnessState.DROWSY)
                
                if time_since_last_drowsy is None or time_since_last_drowsy > drowsy_interval:
                    return "Scheduled awakening for routine check"
                    
            elif target_state == ConsciousnessState.AWARE:
                # Unusual activity pattern detected
                return "Unusual metrics detected in biological monitoring"
                
            elif target_state == ConsciousnessState.ALERT or target_state == ConsciousnessState.FULLY_AWAKE:
                # Critical issue detected by biological systems
                return "Critical issue detected by biological monitoring"
                
        elif current_state == ConsciousnessState.DROWSY:
            # Drowsy can go back to dormant or escalate
            if target_state == ConsciousnessState.DORMANT:
                # Return to dormant if everything is normal
                return "All systems normal, returning to dormant state"
                
            elif target_state in [ConsciousnessState.AWARE, ConsciousnessState.ALERT, ConsciousnessState.FULLY_AWAKE]:
                # Escalate if issues found during drowsy analysis
                return "Issues detected during routine analysis"
                
        elif current_state == ConsciousnessState.AWARE:
            # Aware can de-escalate or escalate
            if target_state in [ConsciousnessState.DORMANT, ConsciousnessState.DROWSY]:
                # De-escalate if situation is resolved
                return "Situation resolved, reducing awareness level"
                
            elif target_state in [ConsciousnessState.ALERT, ConsciousnessState.FULLY_AWAKE]:
                # Escalate if more issues found
                return "Situation worsening, increasing awareness level"
                
        elif current_state == ConsciousnessState.ALERT:
            # Alert can de-escalate or escalate to fully awake
            if target_state in [ConsciousnessState.DORMANT, ConsciousnessState.DROWSY, ConsciousnessState.AWARE]:
                # De-escalate if situation is improving
                return "Situation improving, reducing awareness level"
                
            elif target_state == ConsciousnessState.FULLY_AWAKE:
                # Escalate to fully awake for critical issues
                return "Critical situation detected, full awareness required"
                
        elif current_state == ConsciousnessState.FULLY_AWAKE:
            # Fully awake can only de-escalate
            if target_state != ConsciousnessState.FULLY_AWAKE:
                # De-escalate after crisis is resolved
                return "Crisis resolved, reducing awareness level"
                
        return None
        
    def time_since_state_change(self, state: ConsciousnessState) -> Optional[timedelta]:
        """Get time since last transition to the specified state"""
        for transition in reversed(self.state_history):
            if transition.to_state == state:
                return datetime.now() - transition.timestamp
        return None
        
    def register_handler(self, 
                      state: ConsciousnessState, 
                      handler: Callable[[ConsciousnessTransition], None]) -> None:
        """Register an event handler for a specific state transition"""
        if state not in self.event_handlers:
            self.event_handlers[state] = []
            
        self.event_handlers[state].append(handler)
        self.logger.debug(f"Registered handler for state {state.name}")
        
    def _trigger_handlers(self, 
                       old_state: ConsciousnessState, 
                       new_state: ConsciousnessState, 
                       reason: str) -> None:
        """Trigger event handlers for a state transition"""
        transition = ConsciousnessTransition(
            from_state=old_state,
            to_state=new_state,
            reason=reason
        )
        
        # Trigger handlers for the new state
        if new_state in self.event_handlers:
            for handler in self.event_handlers[new_state]:
                try:
                    handler(transition)
                except Exception as e:
                    self.logger.error(f"Error in handler for state {new_state.name}: {str(e)}")
                    
    def start(self, check_interval: int = 60) -> None:
        """Start the consciousness monitoring thread"""
        if self.active:
            return
            
        def monitor_loop():
            """Background thread for consciousness monitoring"""
            self.logger.info("Consciousness monitoring started")
            
            while self.active:
                try:
                    # Process any queued state changes
                    try:
                        transition = self.state_queue.get(block=False)
                        self.logger.debug(f"Processing queued transition: {transition.from_state.name} -> {transition.to_state.name}")
                        # Process transition logic here
                        self.state_queue.task_done()
                    except queue.Empty:
                        pass
                        
                    # Run state-specific tasks
                    self._run_state_tasks()
                    
                    # Check for automatic state transitions based on time
                    self._check_time_based_transitions()
                    
                except Exception as e:
                    self.logger.error(f"Error in consciousness monitor: {str(e)}")
                    
                # Sleep until next check
                time.sleep(check_interval)
                
        # Set active flag
        self.active = True
        
        # Create and start thread
        self.thread = threading.Thread(target=monitor_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("Consciousness monitoring thread started")
        
    def stop(self) -> None:
        """Stop the consciousness monitoring thread"""
        if not self.active:
            return
            
        # Clear active flag
        self.active = False
        
        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=5)
            
        self.logger.info("Consciousness monitoring stopped")
        
    def _run_state_tasks(self) -> None:
        """Run tasks specific to the current consciousness state"""
        # Tasks depend on the current state
        if self.state == ConsciousnessState.DORMANT:
            # In dormant state, only run minimal maintenance tasks
            pass
            
        elif self.state == ConsciousnessState.DROWSY:
            # In drowsy state, check if we should run a quick analysis
            last_analysis = self.last_activity.get("drowsy_analysis")
            if not last_analysis or (datetime.now() - last_analysis) > timedelta(hours=8):
                self.logger.info("Running drowsy state analysis")
                
                # Record the activity
                self.log_activity("drowsy_analysis")
                
                # TODO: Implement light analysis logic here
                
        elif self.state == ConsciousnessState.AWARE:
            # In aware state, run regular analysis
            last_analysis = self.last_activity.get("aware_analysis")
            if not last_analysis or (datetime.now() - last_analysis) > timedelta(hours=4):
                self.logger.info("Running aware state analysis")
                
                # Record the activity
                self.log_activity("aware_analysis")
                
                # TODO: Implement regular analysis logic here
                
        elif self.state == ConsciousnessState.ALERT:
            # In alert state, run frequent analysis
            last_analysis = self.last_activity.get("alert_analysis")
            if not last_analysis or (datetime.now() - last_analysis) > timedelta(hours=1):
                self.logger.info("Running alert state analysis")
                
                # Record the activity
                self.log_activity("alert_analysis")
                
                # TODO: Implement enhanced analysis logic here
                
        elif self.state == ConsciousnessState.FULLY_AWAKE:
            # In fully awake state, run continuous analysis
            last_analysis = self.last_activity.get("full_analysis")
            if not last_analysis or (datetime.now() - last_analysis) > timedelta(minutes=15):
                self.logger.info("Running fully awake state analysis")
                
                # Record the activity
                self.log_activity("full_analysis")
                
                # TODO: Implement comprehensive analysis logic here
                
    def _check_time_based_transitions(self) -> None:
        """Check for automatic state transitions based on time"""
        current_state = self.state
        
        # Time since last state change
        time_since_change = datetime.now() - self.last_state_change
        
        # Define time limits for each state
        if current_state == ConsciousnessState.FULLY_AWAKE:
            # Fully awake is resource intensive, step down after 1 hour if not actively working
            if time_since_change > timedelta(hours=1):
                last_action = max(self.last_activity.values()) if self.last_activity else None
                if not last_action or (datetime.now() - last_action) > timedelta(minutes=30):
                    self.change_state(ConsciousnessState.ALERT, "Time limit reached for fully awake state")
                    
        elif current_state == ConsciousnessState.ALERT:
            # Alert should step down to aware after 4 hours if no new issues
            if time_since_change > timedelta(hours=4):
                self.change_state(ConsciousnessState.AWARE, "Time limit reached for alert state")
                
        elif current_state == ConsciousnessState.AWARE:
            # Aware should step down to drowsy after 8 hours if no issues
            if time_since_change > timedelta(hours=8):
                self.change_state(ConsciousnessState.DROWSY, "Time limit reached for aware state")
                
        elif current_state == ConsciousnessState.DROWSY:
            # Drowsy should step down to dormant after analysis completes
            drowsy_analysis = self.last_activity.get("drowsy_analysis")
            if drowsy_analysis and (datetime.now() - drowsy_analysis) > timedelta(minutes=15):
                self.change_state(ConsciousnessState.DORMANT, "Analysis complete, returning to dormant state")
                
        # Check for daily wake-up schedule (regardless of current state)
        # This ensures the system does a full check at least once per day
        last_aware = self.time_since_state_change(ConsciousnessState.AWARE)
        if last_aware is None or last_aware > timedelta(days=1):
            # Calculate the scheduled wake time (e.g., 3 AM)
            now = datetime.now()
            wake_hour = 3  # 3 AM
            
            # Check if it's time for the scheduled wake-up
            if now.hour == wake_hour and self.state.value < ConsciousnessState.AWARE.value:
                self.change_state(ConsciousnessState.AWARE, "Scheduled daily wake-up for system check")
                
    def get_state_info(self) -> Dict[str, Any]:
        """Get complete information about the current system consciousness"""
        # Calculate time in current state
        time_in_state = datetime.now() - self.last_state_change
        
        # Calculate allowed transitions from current state
        allowed_transitions = []
        for state in ConsciousnessState:
            reason = self.should_transition(state)
            if reason:
                allowed_transitions.append({
                    "target_state": state.name,
                    "reason": reason
                })
                
        # Get recent history
        recent_history = self.get_state_history(5)
        
        # Get last activities
        activities = {k: (datetime.now() - v).total_seconds() / 60 for k, v in self.last_activity.items()}
        
        return {
            "current_state": self.state.name,
            "time_in_state_minutes": time_in_state.total_seconds() / 60,
            "last_state_change": self.last_state_change.isoformat(),
            "allowed_transitions": allowed_transitions,
            "recent_history": recent_history,
            "activities_minutes_ago": activities
        }

# Handler for SIGTERM
def handle_sigterm(signum, frame):
    """Handle SIGTERM signal"""
    logger.info("Received SIGTERM signal")
    # We could save state here if needed
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    # Parse command-line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Consciousness module for Deus Ex Machina')
    parser.add_argument('--install-dir', default=DEFAULT_INSTALL_DIR, help='Installation directory')
    parser.add_argument('--log-dir', default=DEFAULT_LOG_DIR, help='Log directory')
    parser.add_argument('--state', help='Set initial state (DORMANT, DROWSY, AWARE, ALERT, FULLY_AWAKE)')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--check-interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--info', action='store_true', help='Print current state info and exit')
    args = parser.parse_args()
    
    # Create consciousness instance
    consciousness = Consciousness(
        install_dir=args.install_dir,
        log_dir=args.log_dir
    )
    
    # Set initial state if specified
    if args.state:
        try:
            state = ConsciousnessState[args.state.upper()]
            consciousness.change_state(state, "Manual state change via command line")
        except KeyError:
            print(f"Invalid state: {args.state}")
            print(f"Valid states: {[s.name for s in ConsciousnessState]}")
            sys.exit(1)
            
    # Print info if requested
    if args.info:
        info = consciousness.get_state_info()
        print(json.dumps(info, indent=2))
        sys.exit(0)
        
    # Run as daemon if requested
    if args.daemon:
        consciousness.start(check_interval=args.check_interval)
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            consciousness.stop()
            
    else:
        # Just print current state and exit
        print(f"Current consciousness state: {consciousness.get_current_state().name}")
        print("Use --daemon to start monitoring thread")