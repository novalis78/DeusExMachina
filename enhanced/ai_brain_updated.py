#!/usr/bin/env python3
# ai_brain.py - AI-powered system analysis for critical situations
# Part of the Deus Ex Machina project

import os
import json
import re
import logging
import sys
from datetime import datetime
import subprocess
import shlex
from collections import Counter

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

def analyze_log_locally(log_lines):
    """Use local parsing and analysis when Gemini is not available"""
    logger.info("Using local analysis as fallback for AI")
    
    # Initialize patterns to look for
    failed_auth_pattern = re.compile(r'(failed|invalid|unauthorized|break-in)', re.IGNORECASE)
    ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    port_pattern = re.compile(r'port (\d+)', re.IGNORECASE)
    
    # Collect metrics
    auth_failures = 0
    suspicious_ips = set()
    suspicious_ports = set()
    
    # Extract most common words for topic analysis
    all_text = ' '.join(log_lines)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
    word_count = Counter(words)
    common_words = [word for word, count in word_count.most_common(10) if word not in 
                   {'the', 'and', 'for', 'with', 'from', 'that', 'this', 'alert'}]
    
    # Count auth failures and collect IPs
    for line in log_lines:
        if failed_auth_pattern.search(line):
            auth_failures += 1
            # Extract IPs
            ip_matches = ip_pattern.findall(line)
            for ip in ip_matches:
                suspicious_ips.add(ip)
        
        # Extract suspicious ports
        port_matches = port_pattern.findall(line)
        for port in port_matches:
            suspicious_ports.add(port)
    
    # Determine severity based on metrics
    severity = "low"
    if auth_failures > 50 or len(suspicious_ips) > 5:
        severity = "medium"
    if auth_failures > 200 or len(suspicious_ips) > 10:
        severity = "high"
    if auth_failures > 500 or len(suspicious_ips) > 20:
        severity = "critical"
    
    # Generate recommendations based on findings
    recommendations = []
    if auth_failures > 0:
        recommendations.append(f"Investigate {auth_failures} authentication failures")
    if suspicious_ips:
        recommendations.append(f"Block {len(suspicious_ips)} suspicious IPs at the firewall")
    if suspicious_ports:
        recommendations.append(f"Check open ports: {', '.join(list(suspicious_ports)[:5])}")
    
    # Create structured assessment
    assessment = {
        "severity": severity,
        "confidence": 75,
        "summary": f"Detected {auth_failures} auth failures, {len(suspicious_ips)} suspicious IPs, and activity on {len(suspicious_ports)} ports",
        "analysis": f"Most frequent keywords in alert logs: {', '.join(common_words)}. This suggests suspicious activity related to authentication and network access.",
        "recommendations": recommendations or ["Continue monitoring the system"],
        "next_steps": "Increase monitoring frequency and check for common attack patterns",
        "timestamp": datetime.utcnow().isoformat(),
        "alert_count": len(log_lines),
        "analysis_method": "local_fallback"
    }
    
    logger.info(f"Local analysis complete with severity {severity}")
    return assessment

def get_system_info():
    """Get basic system information for context"""
    system_info = {}
    
    try:
        # Get uptime
        uptime_proc = subprocess.run(['uptime'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if uptime_proc.returncode == 0:
            system_info['uptime'] = uptime_proc.stdout.strip()
        
        # Get disk usage
        df_proc = subprocess.run(['df', '-h', '/'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if df_proc.returncode == 0:
            system_info['disk_usage'] = df_proc.stdout.strip()
        
        # Get memory info
        free_proc = subprocess.run(['free', '-m'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if free_proc.returncode == 0:
            system_info['memory'] = free_proc.stdout.strip()
            
        return system_info
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {}

def awakened_awareness():
    """Main function for AI analysis"""
    logger.info("Awakened awareness starting")
    
    # Load alert logs
    log_lines = load_alert_log()
    if not log_lines:
        return
    
    # Get additional system context
    system_info = get_system_info()
    
    # Try to use Gemini if available
    assessment = None
    try:
        has_valid_key = validate_api_key()
        gemini_available = False
        
        if has_valid_key:
            try:
                # Dynamic import to avoid errors if module isn't available
                import importlib.util
                if importlib.util.find_spec("google.generativeai"):
                    import google.generativeai as genai
                    gemini_available = True
            except ImportError:
                logger.warning("google.generativeai module not found")
                gemini_available = False
                
        # If Gemini is available, use it
        if gemini_available:
            logger.info("Using Gemini for analysis")
            try:
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
                
                # Add system info to prompt
                system_info_text = "\n".join([f"{k}: {v}" for k, v in system_info.items()])
                
                user_prompt = f"""
                Alert Log Contents (last {len(log_lines)} lines):
                {''.join(log_lines[-MIN_LINES_TO_WAKE_AI:])}
                
                System Information:
                {system_info_text}
                """
                
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
                assessment = extract_json_response(response_text)
                
                if assessment:
                    # Add metadata
                    assessment["timestamp"] = datetime.utcnow().isoformat()
                    assessment["alert_count"] = len(log_lines)
                    assessment["analysis_method"] = "gemini"
                else:
                    logger.warning("Could not extract valid JSON from Gemini response")
            except Exception as e:
                logger.error(f"Error during Gemini analysis: {str(e)}")
                
        # If Gemini failed or isn't available, use local analysis
        if not assessment:
            assessment = analyze_log_locally(log_lines)
        
        # Save the assessment
        if assessment:
            with open(ASSESSMENT_PATH, 'w') as f:
                json.dump(assessment, f, indent=2)
            logger.info(f"Assessment written with severity: {assessment.get('severity', 'unknown')}")
        else:
            logger.error("Failed to generate assessment")
                
    except Exception as e:
        logger.error(f"Unexpected error in AI processing: {str(e)}")

if __name__ == "__main__":
    awakened_awareness()