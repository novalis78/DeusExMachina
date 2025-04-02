#!/usr/bin/env python3
# ai_brain.py - AI-powered system analysis for critical situations
# Part of the Deus Ex Machina project

import os
import json
import re
import logging
import sys
from datetime import datetime
import google.generativeai as genai

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import configuration
try:
    from config.config import LOG_DIR, ALERT_LOG, get_gemini_api_key, MIN_LINES_TO_WAKE_AI
except ImportError:
    # Fallback configuration
    LOG_DIR = "/var/log/deus-ex-machina"
    ALERT_LOG = f"{LOG_DIR}/vigilance_alerts.log"
    MIN_LINES_TO_WAKE_AI = 10
    
    def get_gemini_api_key():
        """Fallback method to get API key"""
        # Try environment variable
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            return api_key
        
        # Try config file
        try:
            from config.gemini_config import GEMINI_API_KEY
            return GEMINI_API_KEY
        except ImportError:
            return None

# Create log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logging with rotation
ASSESSMENT_PATH = f"{LOG_DIR}/ai_assessment.json"
LOG_FILE = f"{LOG_DIR}/ai_brain.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AwakenedAwareness")

def validate_api_key():
    """Check if API key is available and valid"""
    api_key = get_gemini_api_key()
    if not api_key:
        logger.error("No API key available. Set GEMINI_API_KEY environment variable or configure gemini_config.py")
        return False
    
    # Basic validation
    if not isinstance(api_key, str) or len(api_key) < 10:
        logger.error("API key appears invalid")
        return False
        
    return True

def load_alert_log():
    """Load and validate alert log data"""
    if not os.path.exists(ALERT_LOG):
        logger.info("No alert log found. Returning to sleep.")
        return None
    
    try:
        with open(ALERT_LOG, 'r') as f:
            log_lines = f.readlines()
        
        if len(log_lines) < MIN_LINES_TO_WAKE_AI:
            logger.info(f"Not enough signals to wake up ({len(log_lines)} < {MIN_LINES_TO_WAKE_AI}). Returning to sleep.")
            return None
            
        return log_lines
    except Exception as e:
        logger.error(f"Error reading alert log: {str(e)}")
        return None

def extract_json_response(response_text):
    """Extract JSON from AI response with robust error handling"""
    if not response_text:
        return None
        
    # Try direct parsing first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in the response text
    try:
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    # Last resort: try to find anything between triple backticks
    try:
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return None

def awakened_awareness():
    """Main function for AI analysis"""
    logger.info("Awakened awareness starting")
    
    # Early validation checks
    if not validate_api_key():
        return
    
    log_lines = load_alert_log()
    if not log_lines:
        return
    
    try:
        # Import Gemini only after validation to avoid errors
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=get_gemini_api_key())
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        system_prompt = """
        You are a hyper-aware AI security agent who has just awakened from slumber to investigate unusual system behavior.
        Your job is to:
        1. Assess the severity and nature of anomalies detected.
        2. Take inventory of what might be happening.
        3. Leave yourself a detailed, structured note for the next time you awaken.
        
        Think like a caretaker of the machine — cautious, methodical, slightly poetic if inspired.
        Only use information found in the log. If insufficient, say so.
        Respond in JSON format with the following structure:
        {
            "severity": "low|medium|high|critical",
            "confidence": 0-100,
            "summary": "Brief overview of the situation",
            "analysis": "Detailed assessment of observed anomalies",
            "recommendations": ["List", "of", "suggested", "actions"],
            "next_steps": "What to monitor next"
        }
        """
        
        user_prompt = f"""
        Alert Log Contents (last {len(log_lines)} lines):
        {''.join(log_lines[-MIN_LINES_TO_WAKE_AI:])}
        """
        
        try:
            # Generate response with more reliability settings
            response = model.generate_content(
                [system_prompt, user_prompt],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 2048,
                    "response_mime_type": "application/json"
                }
            )
            
            response_text = response.text.strip()
            reflection = extract_json_response(response_text)
            
            if reflection:
                # Add metadata
                reflection["timestamp"] = datetime.utcnow().isoformat()
                reflection["alert_count"] = len(log_lines)
                
                # Save to file
                with open(ASSESSMENT_PATH, 'w') as f:
                    json.dump(reflection, f, indent=2)
                logger.info("Awakened awareness complete. Assessment written.")
            else:
                logger.warning("Could not extract valid JSON from AI response.")
                
        except Exception as e:
            logger.error(f"Error during Gemini analysis: {str(e)}")
            
    except ImportError:
        logger.error("Failed to import google.generativeai. Is the package installed?")
    except Exception as e:
        logger.error(f"Unexpected error in Gemini processing: {str(e)}")

if __name__ == "__main__":
    awakened_awareness()
