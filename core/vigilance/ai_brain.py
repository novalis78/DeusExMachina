import os
import json
import re
import logging
import google.generativeai as genai
from datetime import datetime

# Configuration (load from external file or environment later)
from config.gemini_config import GEMINI_API_KEY3

LOG_PATH = "/var/log/deus-ex-machina/vigilance_alerts.log"
ASSESSMENT_PATH = "/var/log/deus-ex-machina/ai_assessment.json"
MIN_LINES_TO_WAKE = 10

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AwakenedAwareness")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY3)
model = genai.GenerativeModel("gemini-2.0-flash")

def awakened_awareness():
    if not os.path.exists(LOG_PATH):
        logger.info("No alert log found. Returning to sleep.")
        return

    with open(LOG_PATH, 'r') as f:
        log_lines = f.readlines()

    if len(log_lines) < MIN_LINES_TO_WAKE:
        logger.info("Not enough signals to wake up. Returning to sleep.")
        return

    system_prompt = """
You are a hyper-aware AI security agent who has just awakened from slumber to investigate unusual system behavior.
Your job is to:
1. Assess the severity and nature of anomalies detected.
2. Take inventory of what might be happening.
3. Leave yourself a detailed, structured note for the next time you awaken.

Think like a caretaker of the machine — cautious, methodical, slightly poetic if inspired.
Only use information found in the log. If insufficient, say so.
Respond in JSON format with a reflection, assessment, and next suggestions.
"""

    user_prompt = f"""
Alert Log Contents (last {len(log_lines)} lines):
{''.join(log_lines[-MIN_LINES_TO_WAKE:])}
"""

    try:
        response = model.generate_content(
            [system_prompt, user_prompt],
            generation_config={"temperature": 0.2, "max_output_tokens": 2048}
        )

        response_text = response.text.strip()
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

        if json_match:
            json_str = json_match.group(0)
            reflection = json.loads(json_str)
            reflection["timestamp"] = datetime.utcnow().isoformat()

            with open(ASSESSMENT_PATH, 'w') as f:
                json.dump(reflection, f, indent=2)
            logger.info("Awakened awareness complete. Note written.")
        else:
            logger.warning("Could not extract valid JSON from AI response.")
    except Exception as e:
        logger.error(f"Error during Gemini analysis: {str(e)}")

if __name__ == "__main__":
    awakened_awareness()

