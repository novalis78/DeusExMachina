#!/usr/bin/env python3
# state_trigger.py - Triggers appropriate modules based on system state
import json
import os
import subprocess
import logging
import sys
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config.config import STATE_FILE, BREATH_SCRIPT, VIGILANCE_SCRIPT, LOG_DIR

# Set up logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "state_trigger.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StateTrigger")

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

def load_state():
    """Load current state from file"""
    try:
        if not os.path.exists(STATE_FILE):
            logger.warning(f"State file not found: {STATE_FILE}")
            return {"state": "normal"}
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading state: {str(e)}")
        return {"state": "normal"}

def trigger(script_path, script_name):
    """Safely trigger a script and log its output"""
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    try:
        logger.info(f"Running {script_name}...")
        start_time = datetime.now()
        
        # Run the script and capture output
        process = subprocess.Popen(
            ["bash", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate(timeout=300)  # 5-minute timeout
        
        # Log the result
        duration = (datetime.now() - start_time).total_seconds()
        if process.returncode == 0:
            logger.info(f"{script_name} completed successfully in {duration:.2f}s")
            return True
        else:
            logger.error(f"{script_name} failed with code {process.returncode} in {duration:.2f}s")
            logger.error(f"STDERR: {stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"{script_name} timed out after 300 seconds")
        return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        return False

def main():
    """Main function to trigger appropriate modules based on state"""
    logger.info("State trigger started")
    
    state = load_state()
    current_state = state.get("state", "normal")
    logger.info(f"Current state: {current_state}")

    if current_state == "suspicious":
        logger.info("Suspicious state detected - running breath module")
        trigger(BREATH_SCRIPT, "Breath module")

    elif current_state in ["alert", "critical"]:
        logger.info(f"{current_state.capitalize()} state detected - running breath and vigilance modules")
        breath_success = trigger(BREATH_SCRIPT, "Breath module")
        
        # Only run vigilance if breath succeeded, to avoid overloading the system
        if breath_success:
            trigger(VIGILANCE_SCRIPT, "Vigilance module")
        else:
            logger.warning("Skipping vigilance module due to breath module failure")

    else:
        logger.info(f"No action needed in {current_state} state")

if __name__ == "__main__":
    main()