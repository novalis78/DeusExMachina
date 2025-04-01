#!/usr/bin/env python3
# state_engine.py - Core state manager for Deus Ex Machina
import json
import os
import logging
import sys
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config.config import STATE_FILE, HEARTBEAT_JSON, THRESHOLDS, DEFAULT_TTL, LOG_DIR

# Set up logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "state_engine.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StateEngine")

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

DEFAULT_STATE = {
    "state": "normal",
    "last_transition": datetime.now().isoformat(),
    "ttl_seconds": DEFAULT_TTL
}

TRANSITIONS = {
    "normal": {
        "thresholds": THRESHOLDS["normal"],
        "next": "suspicious",
        "previous": None
    },
    "suspicious": {
        "thresholds": THRESHOLDS["suspicious"],
        "next": "alert",
        "previous": "normal"
    },
    "alert": {
        "thresholds": THRESHOLDS["alert"],
        "next": "critical",
        "previous": "suspicious"
    },
    "critical": {
        "thresholds": {},
        "next": "critical",
        "previous": "alert"
    }
}

def load_state():
    """Load current state from file or return default"""
    try:
        if not os.path.exists(STATE_FILE):
            return DEFAULT_STATE
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading state: {str(e)}")
        return DEFAULT_STATE

def save_state(state):
    """Save current state to file"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving state: {str(e)}")

def should_escalate(current_metrics, state):
    """Determine if system state should escalate based on metrics"""
    current_state = state["state"]
    thresholds = TRANSITIONS[current_state]["thresholds"]
    
    # Check each threshold
    for key, value in thresholds.items():
        try:
            # For metrics where lower is worse (like memory_free)
            if key == "memory_free_mb":
                if float(current_metrics.get(key, 9999)) < value:
                    logger.info(f"Escalation triggered by {key}: {current_metrics.get(key)} < {value}")
                    return True
            # For metrics where higher is worse
            elif float(current_metrics.get(key, 0)) > value:
                logger.info(f"Escalation triggered by {key}: {current_metrics.get(key)} > {value}")
                return True
        except (ValueError, TypeError) as e:
            logger.warning(f"Error checking threshold {key}: {str(e)}")
            continue
    return False

def should_decay(state):
    """Check if enough time has passed to decay to a lower state"""
    try:
        last = datetime.fromisoformat(state["last_transition"])
        should_decay = datetime.now() > last + timedelta(seconds=state["ttl_seconds"])
        if should_decay:
            logger.info(f"State decay triggered: {datetime.now()} > {last + timedelta(seconds=state['ttl_seconds'])}")
        return should_decay
    except Exception as e:
        logger.error(f"Error checking decay: {str(e)}")
        return False

def transition_state(current_metrics):
    """Determine if state should change based on metrics and time"""
    state = load_state()
    current_state = state["state"]

    # Check if we should escalate
    if should_escalate(current_metrics, state):
        next_state = TRANSITIONS[current_state]["next"]
        if next_state != current_state:
            logger.warning(f"Escalating from {current_state} to {next_state}")
            state["state"] = next_state
            state["last_transition"] = datetime.now().isoformat()
            save_state(state)
            return state

    # Check if we should decay
    elif should_decay(state):
        previous_state = TRANSITIONS[current_state].get("previous")
        if previous_state and previous_state != current_state:
            logger.info(f"Decaying from {current_state} to {previous_state}")
            state["state"] = previous_state
            state["last_transition"] = datetime.now().isoformat()
            save_state(state)
            return state

    # No change
    save_state(state)
    return state

def main():
    """Main function"""
    logger.info("State engine started")
    
    # Check if heartbeat file exists
    if not os.path.exists(HEARTBEAT_JSON):
        logger.error("Heartbeat file not found.")
        return

    try:
        # Load metrics
        with open(HEARTBEAT_JSON) as f:
            metrics = json.load(f)

        # Convert types if needed
        metrics["cpu_load"] = float(metrics.get("cpu_load", 0))
        metrics["open_ports"] = int(metrics.get("open_ports", 0))
        metrics["memory_free_mb"] = int(metrics.get("memory_free_mb", 0))
    except Exception as e:
        logger.error(f"Error parsing metrics: {e}")
        return

    updated_state = transition_state(metrics)
    logger.info(f"Current state: {updated_state['state']}")
    print(f"Current state: {updated_state['state']}")

if __name__ == "__main__":
    main()