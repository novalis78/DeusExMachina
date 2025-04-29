#!/usr/bin/env python3
"""
Configuration for Deus Ex Machina Enhanced System
"""

import os

# Base paths
INSTALL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOG_DIR = os.path.join(INSTALL_DIR, "var/logs")
DB_DIR = os.path.join(INSTALL_DIR, "var/db")

# Database configuration
DB_PATH = os.path.join(DB_DIR, "metrics.db")
MAX_DB_SIZE_MB = 100
RETENTION_DAYS = 30

# AI configuration
MIN_LINES_TO_WAKE_AI = 10
USE_GOOGLE_AI = True
USE_ANTHROPIC = False
USE_OPENAI = False
USE_LOCAL = True

# Action grammar configuration
MAX_PERMISSION_LEVEL = "RESTART"  # OBSERVE, RESTART, CLEAN, CONFIGURE, ADMIN

# Consciousness configuration
INITIAL_CONSCIOUSNESS_STATE = "AWARE"  # DORMANT, DROWSY, AWARE, ALERT, FULLY_AWAKE
CONSCIOUSNESS_CHECK_INTERVAL = 30  # seconds

# Plugin configuration
PLUGINS_DIR = os.path.join(INSTALL_DIR, "plugins")
ENABLED_PLUGINS = ["backup_restore", "network_monitor"]

# Complete configuration dict
CONFIG = {
    "install_dir": INSTALL_DIR,
    "log_dir": LOG_DIR,
    "db_dir": DB_DIR,
    "database_path": DB_PATH,
    "max_db_size_mb": MAX_DB_SIZE_MB,
    "retention_days": RETENTION_DAYS,
    "min_lines_to_wake_ai": MIN_LINES_TO_WAKE_AI,
    "plugins_dir": PLUGINS_DIR,
    "enabled_plugins": ENABLED_PLUGINS,
    "max_permission_level": MAX_PERMISSION_LEVEL,
    
    # AI Provider Configuration
    "ai_providers": {
        "google_ai": {
            "enabled": USE_GOOGLE_AI,
            "api_key_env": "GEMINI_API_KEY",
            "model": "gemini-pro"
        },
        "anthropic": {
            "enabled": USE_ANTHROPIC,
            "api_key_env": "ANTHROPIC_API_KEY",
            "model": "claude-3-haiku-20240307"
        },
        "openai": {
            "enabled": USE_OPENAI,
            "api_key_env": "OPENAI_API_KEY",
            "model": "gpt-4-turbo"
        },
        "local": {
            "enabled": USE_LOCAL
        }
    },
    
    # Consciousness Configuration
    "consciousness": {
        "initial_state": INITIAL_CONSCIOUSNESS_STATE,
        "check_interval": CONSCIOUSNESS_CHECK_INTERVAL,
        "scheduled_wake_hour": 3,  # 3 AM
        "max_fully_awake_hours": 1
    }
}

# Helper functions
def get_gemini_api_key():
    """Get Google Gemini API key from environment"""
    return os.environ.get("GEMINI_API_KEY")

def get_config():
    """Get the complete configuration"""
    return CONFIG