#!/usr/bin/env python3
# memory.py - Database foundation for Deus Ex Machina metrics and events
# Implements persistent memory and trend analysis

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import configuration
try:
    from config.config import LOG_DIR, HEARTBEAT_JSON
except ImportError:
    # Fallback configuration
    LOG_DIR = "/var/log/deus-ex-machina"
    HEARTBEAT_JSON = f"{LOG_DIR}/heartbeat.json"

# Set up database path
DB_DIR = os.path.join(LOG_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "deus_memory.db")
MAX_DB_SIZE_MB = 100  # Maximum database size in MB
RETENTION_DAYS = 30   # Default retention period for metrics

# Set up logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "memory.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Memory")

# Create directories if they don't exist
os.makedirs(DB_DIR, exist_ok=True)

class DeusMemory:
    """Main class for metrics storage and analysis"""
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize the memory system"""
        self.db_path = db_path
        self.conn = None
        self.initialize_database()
        
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.conn:
            self.conn.close()
            
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper error handling"""
        if self.conn is None:
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
            except sqlite3.Error as e:
                logger.error(f"Database connection error: {str(e)}")
                raise
        return self.conn
        
    def initialize_database(self) -> None:
        """Create database tables if they don't exist"""
        try:
            conn = self.get_connection()
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
            
            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_state_timestamp ON state_history(timestamp)')
            
            conn.commit()
            logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
            
    def store_current_metrics(self) -> bool:
        """Store the current metrics from heartbeat.json"""
        try:
            if not os.path.exists(HEARTBEAT_JSON):
                logger.warning(f"Heartbeat file not found: {HEARTBEAT_JSON}")
                return False
                
            with open(HEARTBEAT_JSON, 'r') as f:
                metrics = json.load(f)
                
            # Extract timestamp
            timestamp = metrics.get('timestamp')
            if not timestamp:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            # Convert to ISO format for consistency
            try:
                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                timestamp_iso = dt.isoformat()
            except ValueError:
                timestamp_iso = datetime.now().isoformat()
                
            # Store each metric separately
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for key, value in metrics.items():
                if key == 'timestamp':
                    continue
                    
                # Convert string values to numeric if possible
                if isinstance(value, str):
                    try:
                        if value.replace('.', '', 1).isdigit():
                            value = float(value)
                        elif value.isdigit():
                            value = int(value)
                    except ValueError:
                        pass
                        
                # Skip non-numeric values
                if not isinstance(value, (int, float)):
                    continue
                    
                try:
                    cursor.execute(
                        'INSERT OR REPLACE INTO metrics (timestamp, metric_name, metric_value) VALUES (?, ?, ?)',
                        (timestamp_iso, key, value)
                    )
                except sqlite3.Error as e:
                    logger.error(f"Error storing metric {key}: {str(e)}")
                    
            conn.commit()
            logger.info(f"Stored {len(metrics) - 1} metrics from heartbeat")
            return True
        except Exception as e:
            logger.error(f"Error storing metrics: {str(e)}")
            return False
            
    def record_event(self, event_type: str, severity: str, description: str, details: Optional[Dict] = None) -> bool:
        """Record a significant event"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            details_json = json.dumps(details) if details else None
            
            cursor.execute(
                'INSERT INTO events (timestamp, event_type, severity, description, details) VALUES (?, ?, ?, ?, ?)',
                (timestamp, event_type, severity, description, details_json)
            )
            
            conn.commit()
            logger.info(f"Recorded event: {event_type} ({severity})")
            return True
        except Exception as e:
            logger.error(f"Error recording event: {str(e)}")
            return False
            
    def record_state_change(self, old_state: str, new_state: str, reason: Optional[str] = None) -> bool:
        """Record a state transition"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            cursor.execute(
                'INSERT INTO state_history (timestamp, old_state, new_state, reason) VALUES (?, ?, ?, ?)',
                (timestamp, old_state, new_state, reason)
            )
            
            conn.commit()
            logger.info(f"Recorded state change: {old_state} -> {new_state}")
            return True
        except Exception as e:
            logger.error(f"Error recording state change: {str(e)}")
            return False
            
    def get_metric_history(self, metric_name: str, days: int = 7) -> List[Tuple[str, float]]:
        """Get historical values for a specific metric"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute(
                'SELECT timestamp, metric_value FROM metrics WHERE metric_name = ? AND timestamp >= ? ORDER BY timestamp',
                (metric_name, start_date)
            )
            
            return [(row['timestamp'], row['metric_value']) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching metric history: {str(e)}")
            return []
            
    def calculate_metric_trends(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Calculate trends for a specific metric"""
        values = self.get_metric_history(metric_name, days)
        
        if not values:
            return {
                'metric': metric_name,
                'available': False,
                'reason': 'No data available'
            }
            
        try:
            # Extract values
            timestamps = [t for t, _ in values]
            data_points = [v for _, v in values]
            
            # Basic statistics
            if len(data_points) >= 2:
                mean = sum(data_points) / len(data_points)
                variance = sum((x - mean) ** 2 for x in data_points) / len(data_points)
                std_dev = variance ** 0.5
                
                # Trend direction
                first_half = data_points[:len(data_points)//2]
                second_half = data_points[len(data_points)//2:]
                first_half_avg = sum(first_half) / len(first_half) if first_half else 0
                second_half_avg = sum(second_half) / len(second_half) if second_half else 0
                
                trend_direction = "stable"
                if second_half_avg > first_half_avg * 1.1:
                    trend_direction = "increasing"
                elif second_half_avg < first_half_avg * 0.9:
                    trend_direction = "decreasing"
                
                # Rate of change
                if len(data_points) >= 3:
                    try:
                        # Simple linear regression
                        x = list(range(len(data_points)))
                        y = data_points
                        
                        # Calculate slope (m) for y = mx + b
                        n = len(x)
                        sum_x = sum(x)
                        sum_y = sum(y)
                        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
                        sum_xx = sum(xi * xi for xi in x)
                        
                        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
                        
                        # Normalize slope to percentage change per day
                        normalized_slope = slope * 24 / mean if mean != 0 else 0
                    except:
                        slope = 0
                        normalized_slope = 0
                else:
                    slope = 0
                    normalized_slope = 0
                
                return {
                    'metric': metric_name,
                    'available': True,
                    'count': len(data_points),
                    'current': data_points[-1],
                    'min': min(data_points),
                    'max': max(data_points),
                    'mean': mean,
                    'std_dev': std_dev,
                    'trend': trend_direction,
                    'slope': slope,
                    'change_rate_pct': normalized_slope * 100
                }
            else:
                return {
                    'metric': metric_name,
                    'available': True,
                    'count': len(data_points),
                    'current': data_points[-1],
                    'trend': 'insufficient_data'
                }
        except Exception as e:
            logger.error(f"Error calculating trends for {metric_name}: {str(e)}")
            return {
                'metric': metric_name,
                'available': False,
                'reason': f'Error: {str(e)}'
            }
            
    def check_database_size(self) -> Dict[str, Any]:
        """Check database size and run cleanup if needed"""
        try:
            db_size_bytes = os.path.getsize(self.db_path)
            db_size_mb = db_size_bytes / (1024 * 1024)
            
            result = {
                'size_mb': db_size_mb,
                'max_size_mb': MAX_DB_SIZE_MB,
                'needs_cleanup': db_size_mb > MAX_DB_SIZE_MB
            }
            
            if result['needs_cleanup']:
                self.cleanup_old_data()
                # Get new size after cleanup
                new_size_bytes = os.path.getsize(self.db_path)
                new_size_mb = new_size_bytes / (1024 * 1024)
                result['new_size_mb'] = new_size_mb
                result['cleaned_mb'] = db_size_mb - new_size_mb
                
            return result
        except Exception as e:
            logger.error(f"Error checking database size: {str(e)}")
            return {'error': str(e)}
            
    def cleanup_old_data(self, retention_days: int = RETENTION_DAYS) -> bool:
        """Remove data older than retention_days"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=retention_days)).isoformat()
            
            # Delete old metrics
            cursor.execute('DELETE FROM metrics WHERE timestamp < ?', (cutoff_date,))
            metrics_deleted = cursor.rowcount
            
            # Delete old events
            cursor.execute('DELETE FROM events WHERE timestamp < ?', (cutoff_date,))
            events_deleted = cursor.rowcount
            
            # Delete old state history
            cursor.execute('DELETE FROM state_history WHERE timestamp < ?', (cutoff_date,))
            states_deleted = cursor.rowcount
            
            # Vacuum database to reclaim space
            cursor.execute('VACUUM')
            
            conn.commit()
            logger.info(f"Cleaned up database: removed {metrics_deleted} metrics, {events_deleted} events, {states_deleted} state records")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up database: {str(e)}")
            return False
            
    def detect_anomalies(self, metric_name: str, days: int = 7, threshold: float = 2.0) -> Dict[str, Any]:
        """Detect anomalies in a metric using simple statistical methods"""
        try:
            # Get historical data
            values = self.get_metric_history(metric_name, days)
            
            if len(values) < 3:
                return {
                    'metric': metric_name,
                    'anomalies_detected': False,
                    'reason': 'Insufficient data points'
                }
                
            # Extract values and calculate statistics
            data_points = [v for _, v in values]
            timestamps = [t for t, _ in values]
            
            mean = sum(data_points) / len(data_points)
            variance = sum((x - mean) ** 2 for x in data_points) / len(data_points)
            std_dev = variance ** 0.5
            
            # Detect points beyond threshold standard deviations
            anomalies = []
            for i, (ts, val) in enumerate(values):
                z_score = (val - mean) / std_dev if std_dev > 0 else 0
                if abs(z_score) > threshold:
                    anomalies.append({
                        'timestamp': ts,
                        'value': val,
                        'z_score': z_score,
                        'deviation_pct': (val - mean) / mean * 100 if mean != 0 else 0
                    })
            
            return {
                'metric': metric_name,
                'anomalies_detected': len(anomalies) > 0,
                'anomaly_count': len(anomalies),
                'anomalies': anomalies,
                'mean': mean,
                'std_dev': std_dev,
                'threshold': threshold
            }
        except Exception as e:
            logger.error(f"Error detecting anomalies for {metric_name}: {str(e)}")
            return {
                'metric': metric_name,
                'anomalies_detected': False,
                'reason': f'Error: {str(e)}'
            }
            
    def get_system_summary(self, days: int = 7) -> Dict[str, Any]:
        """Generate a comprehensive system summary with trends"""
        try:
            # Get list of all metrics
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('SELECT DISTINCT metric_name FROM metrics')
            metrics = [row['metric_name'] for row in cursor.fetchall()]
            
            # Calculate trends for each metric
            trends = {}
            anomalies = {}
            
            for metric in metrics:
                trends[metric] = self.calculate_metric_trends(metric, days)
                # Check for anomalies only on critical metrics
                if metric in ['cpu_load', 'memory_free_mb', 'disk_usage_root', 'open_ports']:
                    anomalies[metric] = self.detect_anomalies(metric, days)
            
            # Get recent state changes
            cursor.execute('SELECT * FROM state_history ORDER BY timestamp DESC LIMIT 10')
            state_changes = [dict(row) for row in cursor.fetchall()]
            
            # Get recent events
            cursor.execute('SELECT * FROM events ORDER BY timestamp DESC LIMIT 10')
            recent_events = [dict(row) for row in cursor.fetchall()]
            
            # Calculate overall system health
            health_scores = []
            critical_metrics = ['cpu_load', 'memory_free_mb', 'disk_usage_root']
            
            for metric in critical_metrics:
                if metric in trends and trends[metric].get('available', False):
                    if metric == 'memory_free_mb':
                        # For memory, lower is worse
                        current = trends[metric].get('current', 0)
                        threshold = 500  # Arbitrary threshold (MB)
                        score = min(100, max(0, (current / threshold) * 100))
                    elif metric == 'cpu_load':
                        # For CPU, higher is worse
                        current = trends[metric].get('current', 0)
                        threshold = 2.0  # Arbitrary threshold
                        score = min(100, max(0, (1 - current / threshold) * 100))
                    elif metric == 'disk_usage_root':
                        # For disk usage, higher is worse
                        current = trends[metric].get('current', 0)
                        threshold = 90  # Arbitrary threshold (%)
                        score = min(100, max(0, (1 - current / threshold) * 100))
                    else:
                        score = 50  # Default score
                        
                    health_scores.append(score)
            
            overall_health = sum(health_scores) / len(health_scores) if health_scores else 50
            
            return {
                'timestamp': datetime.now().isoformat(),
                'metrics_tracked': len(metrics),
                'trends': trends,
                'anomalies': anomalies,
                'recent_state_changes': state_changes,
                'recent_events': recent_events,
                'overall_health': overall_health,
                'days_analyzed': days
            }
        except Exception as e:
            logger.error(f"Error generating system summary: {str(e)}")
            return {'error': str(e)}
            
    def monitor(self) -> None:
        """Main monitoring function to be called by cron or scheduler"""
        try:
            # Store current metrics
            self.store_current_metrics()
            
            # Check database size and cleanup if needed
            self.check_database_size()
            
            # Detect anomalies in critical metrics
            critical_metrics = ['cpu_load', 'memory_free_mb', 'disk_usage_root', 'open_ports']
            
            for metric in critical_metrics:
                anomaly_result = self.detect_anomalies(metric)
                if anomaly_result.get('anomalies_detected', False):
                    anomalies = anomaly_result.get('anomalies', [])
                    for anomaly in anomalies:
                        # Only record recent anomalies (within the last hour)
                        anomaly_time = datetime.fromisoformat(anomaly['timestamp'])
                        if datetime.now() - anomaly_time < timedelta(hours=1):
                            self.record_event(
                                event_type='anomaly_detected',
                                severity='warning',
                                description=f"Anomaly detected in {metric}",
                                details={
                                    'metric': metric,
                                    'value': anomaly['value'],
                                    'deviation_pct': anomaly['deviation_pct']
                                }
                            )
                            
            logger.info("Monitoring cycle completed")
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {str(e)}")

if __name__ == "__main__":
    # When run directly, perform a monitoring cycle
    with DeusMemory() as memory:
        memory.monitor()