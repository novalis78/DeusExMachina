#!/usr/bin/env python3
# Central configuration file for Deus Ex Machina
import os

# Base directories
INSTALL_DIR = os.environ.get("DEUS_INSTALL_DIR", "/opt/deus-ex-machina")
LOG_DIR = os.environ.get("DEUS_LOG_DIR", "/var/log/deus-ex-machina")

# Paths to core components
HEARTBEAT_SCRIPT = os.path.join(INSTALL_DIR, "core/heartbeat/heartbeat.sh")
BREATH_SCRIPT = os.path.join(INSTALL_DIR, "core/breath/breath.sh")
VIGILANCE_SCRIPT = os.path.join(INSTALL_DIR, "core/vigilance/vigilance.sh")
AI_BRAIN_SCRIPT = os.path.join(INSTALL_DIR, "core/vigilance/ai_brain.py")

# File locations
STATE_FILE = os.path.join(LOG_DIR, "state.json")
HEARTBEAT_JSON = os.path.join(LOG_DIR, "heartbeat.json")
HEARTBEAT_PREV_JSON = os.path.join(LOG_DIR, "heartbeat_prev.json")
BREATH_HASHES = os.path.join(LOG_DIR, "breath_hashes.json")
MERKLE_ROOT = os.path.join(LOG_DIR, "merkle_root.hash")
ALERT_LOG = os.path.join(LOG_DIR, "vigilance_alerts.log")
AI_ASSESSMENT = os.path.join(LOG_DIR, "ai_assessment.json")

# Timeouts and intervals
HEARTBEAT_INTERVAL = 60  # seconds
STATE_ENGINE_INTERVAL = 120  # seconds
DEFAULT_TTL = 600  # seconds

# Monitoring settings
SCAN_PATHS = [
    "/etc/passwd",
    "/etc/ssh/sshd_config",
    "/etc/fstab",
    "/etc/crontab",
    "/etc/shadow",  # Added sensitive file
    "/etc/hosts"    # Added network config file
]

MERKLE_BASE_DIRS = ["/etc", "/usr/bin", "/usr/sbin", "/home"]

# State transition thresholds
THRESHOLDS = {
    "normal": {"cpu_load": 1.0, "open_ports": 100, "memory_free_mb": 500},
    "suspicious": {"cpu_load": 2.0, "open_ports": 150, "memory_free_mb": 300},
    "alert": {"cpu_load": 4.0, "open_ports": 200, "memory_free_mb": 150}
}

# Security settings
MIN_LINES_TO_WAKE_AI = 10

# Gemini settings - access these via environment for security
# Always set GEMINI_API_KEY via environment variable
def get_gemini_api_key():
    """Retrieve Gemini API key from environment or config file"""
    # Priority 1: Environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    # Priority 2: Config file (legacy support)
    try:
        from config.gemini_config import GEMINI_API_KEY as CONFIG_KEY
        return CONFIG_KEY
    except ImportError:
        return None

# Logging configuration
LOG_ROTATION_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5