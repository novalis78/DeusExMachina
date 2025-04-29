#!/usr/bin/env python3
"""
Database initialization script for Deus Ex Machina
"""
import os
import sys
import sqlite3
import json
from datetime import datetime

# Add the enhanced directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import configuration
from config import CONFIG

def initialize_database(db_path):
    """Create database tables if they don't exist"""
    try:
        # Make sure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            UNIQUE(timestamp, metric_name)
        )
        ''')
        
        # Create events table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            details TEXT
        )
        ''')
        
        # Create state history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS state_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            old_state TEXT NOT NULL,
            new_state TEXT NOT NULL,
            reason TEXT
        )
        ''')
        
        # Create consciousness_state table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS consciousness_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            state TEXT NOT NULL,
            reason TEXT,
            duration_minutes INTEGER
        )
        ''')
        
        # Create action_history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action_id TEXT NOT NULL,
            action_name TEXT NOT NULL,
            command TEXT,
            success INTEGER NOT NULL,
            output TEXT,
            error TEXT,
            permission_level TEXT
        )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_state_timestamp ON state_history(timestamp)')
        
        # Insert initial sample data
        timestamp = datetime.now().isoformat()
        
        # Sample metrics
        cursor.execute('INSERT OR IGNORE INTO metrics (timestamp, metric_name, metric_value) VALUES (?, ?, ?)',
                      (timestamp, 'cpu_load', 0.45))
        cursor.execute('INSERT OR IGNORE INTO metrics (timestamp, metric_name, metric_value) VALUES (?, ?, ?)',
                      (timestamp, 'memory_used_percent', 62.7))
        cursor.execute('INSERT OR IGNORE INTO metrics (timestamp, metric_name, metric_value) VALUES (?, ?, ?)',
                      (timestamp, 'disk_usage_root', 72.3))
        
        # Sample event
        cursor.execute('''
        INSERT OR IGNORE INTO events (timestamp, event_type, severity, description, details)
        VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, 'system_start', 'INFO', 'System initialized', json.dumps({"source": "initialize_db.py"})))
        
        # Initial consciousness state
        cursor.execute('''
        INSERT OR IGNORE INTO consciousness_state (timestamp, state, reason, duration_minutes)
        VALUES (?, ?, ?, ?)
        ''', (timestamp, 'AWARE', 'Initial system startup', 0))
        
        conn.commit()
        conn.close()
        
        print(f"Database initialized successfully at: {db_path}")
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    # Initialize the database
    db_path = CONFIG["database_path"]
    initialize_database(db_path)