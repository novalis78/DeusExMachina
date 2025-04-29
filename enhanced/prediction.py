#!/usr/bin/env python3
# prediction.py - Time-series forecasting and pattern recognition
# Part of the Phase 3 Proactive Intelligence implementation

import os
import sys
import json
import logging
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import math
import random

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import configuration
try:
    from config.config import LOG_DIR
    from memory import DeusMemory
except ImportError:
    # Fallback configuration
    LOG_DIR = "/var/log/deus-ex-machina"
    
    # Try to import memory module from current directory
    try:
        from memory import DeusMemory
    except ImportError:
        # Define a placeholder
        class DeusMemory:
            def __init__(self, *args, **kwargs):
                pass

# Set up logging
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "prediction.log"),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Prediction")

class PredictionEngine:
    """Forecasting and pattern recognition engine"""
    
    def __init__(self, memory: Optional[DeusMemory] = None):
        """Initialize with an optional memory instance"""
        self.memory = memory or DeusMemory()
        
    def forecast_metric(self, metric_name: str, hours_ahead: int = 24, 
                       history_days: int = 7) -> Dict[str, Any]:
        """Forecast a metric value for specified hours in the future"""
        try:
            # Get historical data from memory system
            history = self.memory.get_metric_history(metric_name, days=history_days)
            
            if not history or len(history) < 24:  # Need at least a day of data
                return {
                    "success": False,
                    "error": f"Insufficient data for {metric_name} (need at least 24 data points)",
                    "metric": metric_name,
                    "required_points": 24,
                    "available_points": len(history) if history else 0
                }
                
            # Extract values and timestamps
            timestamps = []
            values = []
            
            for ts, val in history:
                try:
                    # Convert timestamp to datetime
                    if 'T' in ts:  # ISO format
                        dt = datetime.fromisoformat(ts)
                    else:  # Legacy format
                        dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                    
                    # Get hours since first timestamp or total hours
                    if not timestamps:
                        base_time = dt
                        x = 0
                    else:
                        x = (dt - base_time).total_seconds() / 3600  # Hours
                    
                    timestamps.append(x)
                    values.append(float(val))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid data point ({ts}, {val}): {str(e)}")
                    
            if not timestamps or not values:
                return {
                    "success": False,
                    "error": "No valid data points after parsing",
                    "metric": metric_name
                }
                
            # Fit linear model
            linear_prediction, linear_coef, linear_intercept = self._linear_forecast(
                timestamps, values, hours_ahead
            )
            
            # Fit a simple seasonal model if we have enough data
            if len(values) >= 72:  # At least 3 days for seasonality
                seasonal_prediction, seasonal_data = self._seasonal_forecast(
                    timestamps, values, hours_ahead
                )
            else:
                seasonal_prediction = linear_prediction
                seasonal_data = None
                
            # Fit exponential smoothing if appropriate
            if all(v > 0 for v in values):
                exp_prediction = self._exponential_forecast(values, hours_ahead)
            else:
                exp_prediction = linear_prediction
                
            # Calculate weighted average prediction using validation to determine weights
            ensemble_prediction, weights = self._ensemble_forecast(
                timestamps, values, hours_ahead, 
                linear_prediction, seasonal_prediction, exp_prediction
            )
            
            # Determine confidence interval
            # Wider intervals for longer forecasts
            confidence_width = max(0.05, 0.02 * math.sqrt(hours_ahead))
            
            # Find historical volatility for scaling confidence intervals
            if len(values) > 1:
                volatility = np.std(values) / np.mean(values) if np.mean(values) != 0 else 0.1
            else:
                volatility = 0.1
                
            # Scale confidence by volatility but cap it
            confidence_width = min(0.3, confidence_width * (1 + volatility * 5))
            
            # Calculate prediction intervals
            lower_bound = ensemble_prediction * (1 - confidence_width)
            upper_bound = ensemble_prediction * (1 + confidence_width)
            
            # Use a minimum sensible value for the lower bound
            if metric_name in ["cpu_load", "disk_usage_root"]:
                lower_bound = max(0, lower_bound)
            elif metric_name == "memory_free_mb":
                lower_bound = max(50, lower_bound)  # Minimum sensible free memory
                
            # Format timestamps for result
            current_time = datetime.now()
            forecast_time = current_time + timedelta(hours=hours_ahead)
            
            # Prepare result
            result = {
                "success": True,
                "metric": metric_name,
                "current_value": values[-1] if values else None,
                "current_time": current_time.isoformat(),
                "forecast_value": ensemble_prediction,
                "forecast_time": forecast_time.isoformat(),
                "hours_ahead": hours_ahead,
                "confidence_interval": [lower_bound, upper_bound],
                "confidence_width_pct": confidence_width * 100,
                "model_weights": weights,
                "data_points_used": len(values),
                "trend": {
                    "direction": "increasing" if linear_coef > 0 else "decreasing" if linear_coef < 0 else "stable",
                    "slope": linear_coef,
                    "percent_change_per_day": linear_coef * 24 / values[-1] * 100 if values and values[-1] != 0 else 0
                }
            }
            
            return result
        except Exception as e:
            logger.error(f"Error forecasting {metric_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "metric": metric_name
            }
            
    def _linear_forecast(self, x: List[float], y: List[float], 
                       hours_ahead: int) -> Tuple[float, float, float]:
        """Fit linear model and forecast ahead"""
        if not x or not y or len(x) < 2 or len(y) < 2:
            # Default to last value and no slope
            return y[-1] if y else 0, 0, y[-1] if y else 0
            
        # Linear regression
        x_arr = np.array(x)
        y_arr = np.array(y)
        
        # Calculate coefficients
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
        sum_xx = sum(x_i * x_i for x_i in x)
        
        # Calculate slope and intercept
        try:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
        except ZeroDivisionError:
            slope = 0
            intercept = np.mean(y_arr)
            
        # Forecast
        forecast_x = x[-1] + hours_ahead
        forecast_y = slope * forecast_x + intercept
        
        return forecast_y, slope, intercept
            
    def _seasonal_forecast(self, x: List[float], y: List[float], 
                         hours_ahead: int) -> Tuple[float, Dict[str, Any]]:
        """Fit a basic seasonal model and forecast ahead"""
        # Estimate seasonality if sufficient data
        if len(y) < 48:  # Need at least 2 days for daily seasonality
            return y[-1], {"error": "Insufficient data for seasonality"}
            
        # Assume 24-hour cycle and calculate average pattern
        hours_in_day = 24
        
        # Group values by hour of day
        hour_groups = {}
        last_complete_day = {}
        
        for i, (timestamp, value) in enumerate(zip(x, y)):
            hour = int(timestamp) % hours_in_day
            if hour not in hour_groups:
                hour_groups[hour] = []
            hour_groups[hour].append(value)
            last_complete_day[hour] = value
            
        # Calculate average for each hour
        hourly_averages = {}
        for hour, values in hour_groups.items():
            hourly_averages[hour] = sum(values) / len(values)
            
        # Calculate overall average
        overall_avg = sum(y) / len(y)
        
        # Calculate hourly ratios
        hourly_ratios = {}
        for hour, avg in hourly_averages.items():
            hourly_ratios[hour] = avg / overall_avg if overall_avg != 0 else 1.0
            
        # Determine which hour of the day we'll be at
        current_hour = int(x[-1]) % hours_in_day
        forecast_hour = (current_hour + hours_ahead) % hours_in_day
        
        # Get the ratio for that hour
        forecast_ratio = hourly_ratios.get(forecast_hour, 1.0)
        
        # Use linear regression for the trend
        linear_forecast, slope, intercept = self._linear_forecast(x, y, hours_ahead)
        
        # Apply seasonality
        seasonal_forecast = linear_forecast * forecast_ratio
        
        # Seasonal data for reference
        seasonal_data = {
            "hourly_ratios": hourly_ratios,
            "current_hour": current_hour,
            "forecast_hour": forecast_hour,
            "forecast_ratio": forecast_ratio
        }
        
        return seasonal_forecast, seasonal_data
            
    def _exponential_forecast(self, y: List[float], hours_ahead: int) -> float:
        """Simple exponential smoothing forecast"""
        if not y:
            return 0
            
        # Use only positive values for exponential smoothing
        y_filtered = [v for v in y if v > 0]
        if not y_filtered:
            return y[-1]  # Last value
            
        # Determine best alpha using hold-out validation
        alphas = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
        best_alpha = 0.3  # Default
        best_error = float('inf')
        
        # Split data for validation
        train_size = int(len(y_filtered) * 0.8)
        if train_size >= 10:  # Only validate if we have enough data
            train = y_filtered[:train_size]
            test = y_filtered[train_size:]
            
            for alpha in alphas:
                # Initialize forecast with first value
                forecast = train[0]
                # Generate one-step-ahead forecasts
                forecasts = []
                for val in train[1:]:
                    forecast = alpha * val + (1 - alpha) * forecast
                    forecasts.append(forecast)
                    
                # Continue for test set without updating
                for _ in range(len(test)):
                    forecast = forecast  # No update, just propagate
                    forecasts.append(forecast)
                    
                # Calculate error on test set
                errors = [(f - a)**2 for f, a in zip(forecasts[-len(test):], test)]
                mse = sum(errors) / len(errors) if errors else float('inf')
                
                if mse < best_error:
                    best_error = mse
                    best_alpha = alpha
        
        # Apply exponential smoothing with best alpha
        alpha = best_alpha
        forecast = y_filtered[0]
        for val in y_filtered[1:]:
            forecast = alpha * val + (1 - alpha) * forecast
            
        # Project forward
        # No update for future values, so the forecast remains the same
        # This is appropriate for exponential smoothing without trend or seasonality
        
        return forecast
            
    def _ensemble_forecast(self, x: List[float], y: List[float], hours_ahead: int,
                        linear_pred: float, seasonal_pred: float, exp_pred: float) -> Tuple[float, Dict[str, float]]:
        """Create an ensemble prediction using validation to determine weights"""
        # Default weights
        weights = {
            "linear": 0.4,
            "seasonal": 0.4,
            "exponential": 0.2
        }
        
        try:
            # Only adjust weights if we have enough data
            if len(y) >= 72:  # 3 days or more
                # Split data for validation
                train_size = int(len(y) * 0.7)
                val_size = int(len(y) * 0.2)
                
                if val_size >= 12:  # Need at least 12 hours for validation
                    train_x = x[:train_size]
                    train_y = y[:train_size]
                    val_x = x[train_size:train_size + val_size]
                    val_y = y[train_size:train_size + val_size]
                    
                    # Generate forecasts for validation set
                    val_errors = {"linear": 0, "seasonal": 0, "exponential": 0}
                    
                    for i, ahead in enumerate(range(len(val_x))):
                        # Calculate forecasts
                        linear_val, _, _ = self._linear_forecast(train_x, train_y, ahead)
                        
                        if len(train_y) >= 72:
                            seasonal_val, _ = self._seasonal_forecast(train_x, train_y, ahead)
                        else:
                            seasonal_val = linear_val
                            
                        if all(v > 0 for v in train_y):
                            exp_val = self._exponential_forecast(train_y, ahead)
                        else:
                            exp_val = linear_val
                            
                        # Calculate errors
                        actual = val_y[i]
                        val_errors["linear"] += (linear_val - actual)**2
                        val_errors["seasonal"] += (seasonal_val - actual)**2
                        val_errors["exponential"] += (exp_val - actual)**2
                    
                    # Convert errors to weights inversely proportional to MSE
                    mse = {k: v / val_size for k, v in val_errors.items()}
                    
                    # Handle zero errors
                    for k in mse:
                        if mse[k] == 0:
                            mse[k] = 1e-10
                            
                    # Convert to weights
                    inv_mse = {k: 1/v for k, v in mse.items()}
                    total = sum(inv_mse.values())
                    
                    # Normalize weights
                    if total > 0:
                        weights = {k: v/total for k, v in inv_mse.items()}
                        
                        # Ensure a minimum weight of 0.1 for each method
                        for k in weights:
                            weights[k] = max(0.1, weights[k])
                            
                        # Re-normalize
                        total = sum(weights.values())
                        weights = {k: v/total for k, v in weights.items()}
                    
        except Exception as e:
            logger.warning(f"Error optimizing ensemble weights: {str(e)}")
            # Use default weights
            
        # Calculate ensemble prediction
        ensemble = (
            weights["linear"] * linear_pred +
            weights["seasonal"] * seasonal_pred +
            weights["exponential"] * exp_pred
        )
        
        return ensemble, weights
        
    def detect_patterns(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """Detect recurring patterns in a metric"""
        try:
            # Get historical data
            history = self.memory.get_metric_history(metric_name, days=days)
            
            if not history or len(history) < 24:
                return {
                    "success": False,
                    "error": f"Insufficient data for {metric_name}",
                    "metric": metric_name
                }
                
            # Extract timestamps and values
            timestamps = []
            values = []
            
            for ts, val in history:
                try:
                    if 'T' in ts:  # ISO format
                        dt = datetime.fromisoformat(ts)
                    else:
                        dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                        
                    timestamps.append(dt)
                    values.append(float(val))
                except (ValueError, TypeError):
                    continue
                    
            if not timestamps or not values:
                return {
                    "success": False,
                    "error": "No valid data points after parsing",
                    "metric": metric_name
                }
                
            # Analyze daily patterns
            daily_patterns = self._analyze_daily_patterns(timestamps, values)
            
            # Analyze weekly patterns
            weekly_patterns = self._analyze_weekly_patterns(timestamps, values)
            
            # Analyze trends
            trend_patterns = self._analyze_trends(timestamps, values)
            
            # Combine pattern information
            result = {
                "success": True,
                "metric": metric_name,
                "daily_patterns": daily_patterns,
                "weekly_patterns": weekly_patterns,
                "trends": trend_patterns,
                "data_points": len(values)
            }
            
            return result
        except Exception as e:
            logger.error(f"Error detecting patterns for {metric_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "metric": metric_name
            }
            
    def _analyze_daily_patterns(self, timestamps: List[datetime], 
                               values: List[float]) -> Dict[str, Any]:
        """Analyze patterns by hour of day"""
        if not timestamps or not values or len(timestamps) < 24:
            return {"detected": False, "reason": "Insufficient data"}
            
        # Group by hour of day
        hourly_data = {}
        for dt, val in zip(timestamps, values):
            hour = dt.hour
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(val)
            
        # Calculate statistics for each hour
        hourly_stats = {}
        for hour, vals in hourly_data.items():
            if vals:
                hourly_stats[hour] = {
                    "mean": sum(vals) / len(vals),
                    "min": min(vals),
                    "max": max(vals),
                    "count": len(vals)
                }
                
        # Find peak and trough hours
        if hourly_stats:
            mean_values = [(h, s["mean"]) for h, s in hourly_stats.items()]
            peak_hour = max(mean_values, key=lambda x: x[1])[0]
            trough_hour = min(mean_values, key=lambda x: x[1])[0]
            
            # Calculate variability
            overall_mean = sum(values) / len(values)
            peak_ratio = hourly_stats[peak_hour]["mean"] / overall_mean if overall_mean else 1
            trough_ratio = hourly_stats[trough_hour]["mean"] / overall_mean if overall_mean else 1
            
            # Determine if there's a significant pattern
            pattern_strength = abs(peak_ratio - trough_ratio)
            has_pattern = pattern_strength > 0.2  # Arbitrary threshold
            
            return {
                "detected": has_pattern,
                "peak_hour": peak_hour,
                "peak_value": hourly_stats[peak_hour]["mean"],
                "trough_hour": trough_hour,
                "trough_value": hourly_stats[trough_hour]["mean"],
                "pattern_strength": pattern_strength,
                "hourly_data": hourly_stats
            }
        else:
            return {"detected": False, "reason": "Could not analyze hourly data"}
            
    def _analyze_weekly_patterns(self, timestamps: List[datetime], 
                               values: List[float]) -> Dict[str, Any]:
        """Analyze patterns by day of week"""
        if not timestamps or not values or len(timestamps) < 7 * 24:  # At least a week
            return {"detected": False, "reason": "Need at least a week of data"}
            
        # Group by day of week
        daily_data = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for dt, val in zip(timestamps, values):
            day_idx = dt.weekday()  # 0 = Monday, 6 = Sunday
            day_name = days[day_idx]
            
            if day_name not in daily_data:
                daily_data[day_name] = []
            daily_data[day_name].append(val)
            
        # Check if we have data for all days
        if len(daily_data) < 7:
            return {"detected": False, "reason": "Incomplete weekly data"}
            
        # Calculate statistics for each day
        daily_stats = {}
        for day, vals in daily_data.items():
            if vals:
                daily_stats[day] = {
                    "mean": sum(vals) / len(vals),
                    "min": min(vals),
                    "max": max(vals),
                    "count": len(vals)
                }
                
        # Find peak and trough days
        if daily_stats:
            mean_values = [(d, s["mean"]) for d, s in daily_stats.items()]
            peak_day = max(mean_values, key=lambda x: x[1])[0]
            trough_day = min(mean_values, key=lambda x: x[1])[0]
            
            # Calculate variability
            overall_mean = sum(values) / len(values)
            peak_ratio = daily_stats[peak_day]["mean"] / overall_mean if overall_mean else 1
            trough_ratio = daily_stats[trough_day]["mean"] / overall_mean if overall_mean else 1
            
            # Determine if there's a significant pattern
            pattern_strength = abs(peak_ratio - trough_ratio)
            has_pattern = pattern_strength > 0.15  # Arbitrary threshold
            
            # Check weekday vs weekend pattern
            weekday_vals = []
            weekend_vals = []
            
            for day, stats in daily_stats.items():
                if day in ["Saturday", "Sunday"]:
                    weekend_vals.append(stats["mean"])
                else:
                    weekday_vals.append(stats["mean"])
                    
            weekday_avg = sum(weekday_vals) / len(weekday_vals) if weekday_vals else 0
            weekend_avg = sum(weekend_vals) / len(weekend_vals) if weekend_vals else 0
            
            weekday_weekend_diff = abs(weekday_avg - weekend_avg) / overall_mean if overall_mean else 0
            
            return {
                "detected": has_pattern,
                "peak_day": peak_day,
                "peak_value": daily_stats[peak_day]["mean"],
                "trough_day": trough_day,
                "trough_value": daily_stats[trough_day]["mean"],
                "pattern_strength": pattern_strength,
                "weekday_avg": weekday_avg,
                "weekend_avg": weekend_avg,
                "weekday_weekend_diff": weekday_weekend_diff,
                "weekday_weekend_pattern": weekday_weekend_diff > 0.1,
                "daily_data": daily_stats
            }
        else:
            return {"detected": False, "reason": "Could not analyze daily data"}
            
    def _analyze_trends(self, timestamps: List[datetime], 
                      values: List[float]) -> Dict[str, Any]:
        """Analyze overall trends in the data"""
        if not timestamps or not values or len(timestamps) < 2:
            return {"detected": False, "reason": "Insufficient data"}
            
        # Convert timestamps to hours since start for regression
        t0 = timestamps[0]
        x = [(dt - t0).total_seconds() / 3600 for dt in timestamps]  # Hours
        y = values
        
        # Linear regression
        _, slope, intercept = self._linear_forecast(x, y, 0)
        
        # Calculate percent change per day
        if values[0] != 0:
            percent_change_per_day = (slope * 24) / values[0] * 100
        else:
            percent_change_per_day = 0
            
        # Determine significance of trend
        significant_trend = abs(percent_change_per_day) > 5  # Arbitrary threshold
        
        # Calculate volatility
        if len(values) > 1:
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std_dev = math.sqrt(variance)
            volatility = std_dev / mean if mean != 0 else 0
        else:
            volatility = 0
            
        trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
        
        return {
            "detected": significant_trend,
            "direction": trend_direction,
            "slope": slope,
            "percent_change_per_day": percent_change_per_day,
            "volatility": volatility,
            "is_stable": volatility < 0.2,
            "is_volatile": volatility > 0.5
        }
        
    def generate_schedule(self, predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate an optimized maintenance schedule based on predictions"""
        try:
            # Define maintenance activities and their requirements
            activities = {
                "log_rotation": {
                    "duration_minutes": 10,
                    "impact": "low",
                    "best_time": "when disk usage high",
                    "metric": "disk_usage_root"
                },
                "memory_cleanup": {
                    "duration_minutes": 5,
                    "impact": "low",
                    "best_time": "when memory_free low",
                    "metric": "memory_free_mb"
                },
                "security_scan": {
                    "duration_minutes": 30,
                    "impact": "medium",
                    "best_time": "when cpu_load low",
                    "metric": "cpu_load"
                },
                "system_backup": {
                    "duration_minutes": 60,
                    "impact": "high",
                    "best_time": "when all metrics optimal",
                    "metric": "combined"
                }
            }
            
            # Define the next 7 days in hourly increments
            now = datetime.now()
            schedule = []
            
            for day in range(7):
                for hour in range(24):
                    timestamp = now + timedelta(days=day, hours=hour)
                    time_slot = {
                        "timestamp": timestamp.isoformat(),
                        "day": timestamp.strftime("%A"),
                        "hour": hour,
                        "forecasts": {},
                        "score": 0,
                        "activities": []
                    }
                    
                    # Get forecasts for this time
                    for metric, metric_predictions in predictions.items():
                        if "forecast_value" in metric_predictions:
                            time_slot["forecasts"][metric] = metric_predictions["forecast_value"]
                            
                    # Calculate score for this time slot
                    # Higher is better for scheduling
                    score = 0
                    
                    if "cpu_load" in time_slot["forecasts"]:
                        # Lower CPU load is better
                        cpu_score = 100 - min(100, time_slot["forecasts"]["cpu_load"] * 100)
                        score += cpu_score
                        
                    if "memory_free_mb" in time_slot["forecasts"]:
                        # Higher free memory is better
                        memory_score = min(100, time_slot["forecasts"]["memory_free_mb"] / 10)
                        score += memory_score
                        
                    if "disk_usage_root" in time_slot["forecasts"]:
                        # Lower disk usage is better
                        disk_score = 100 - min(100, time_slot["forecasts"]["disk_usage_root"])
                        score += disk_score
                        
                    # Adjust for time of day preferences
                    # Prefer non-business hours (nights and weekends)
                    if hour < 7 or hour >= 19:  # Night hours
                        score += 50
                    elif timestamp.weekday() >= 5:  # Weekend
                        score += 25
                        
                    time_slot["score"] = score
                    schedule.append(time_slot)
                    
            # Sort schedule by score (highest first)
            schedule.sort(key=lambda x: x["score"], reverse=True)
            
            # Assign activities to slots
            scheduled_activities = {}
            
            for activity_name, activity_info in activities.items():
                # Find the best slot that doesn't have an activity yet
                for slot in schedule:
                    if not slot["activities"] and activity_name not in scheduled_activities:
                        # Check if this slot meets specific metric requirements
                        metric = activity_info["metric"]
                        
                        if metric == "combined":
                            # For combined metrics, use slots with highest scores
                            if slot["score"] > 200:  # Arbitrary threshold
                                slot["activities"].append(activity_name)
                                scheduled_activities[activity_name] = slot["timestamp"]
                                break
                        elif metric in slot["forecasts"]:
                            # Check if metric value is appropriate for this activity
                            if metric == "cpu_load" and slot["forecasts"][metric] < 0.5:
                                slot["activities"].append(activity_name)
                                scheduled_activities[activity_name] = slot["timestamp"]
                                break
                            elif metric == "memory_free_mb" and slot["forecasts"][metric] < 500:
                                slot["activities"].append(activity_name)
                                scheduled_activities[activity_name] = slot["timestamp"]
                                break
                            elif metric == "disk_usage_root" and slot["forecasts"][metric] > 70:
                                slot["activities"].append(activity_name)
                                scheduled_activities[activity_name] = slot["timestamp"]
                                break
                                
            # Filter schedule to only include slots with activities
            active_schedule = [slot for slot in schedule if slot["activities"]]
            
            return {
                "success": True,
                "schedule": active_schedule,
                "activities": activities,
                "scheduled_count": len(active_schedule),
                "generated_at": now.isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating schedule: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def analyze_recurring_issues(self, days: int = 30) -> Dict[str, Any]:
        """Analyze event logs to identify recurring issues"""
        try:
            conn = self.memory.get_connection()
            cursor = conn.cursor()
            
            # Query events from the database
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute(
                'SELECT timestamp, event_type, severity, description FROM events WHERE timestamp >= ? ORDER BY timestamp',
                (start_date,)
            )
            
            events = [dict(row) for row in cursor.fetchall()]
            
            if not events:
                return {
                    "success": True,
                    "message": "No events found for analysis",
                    "recurring_issues": [],
                    "event_count": 0
                }
                
            # Group events by type
            event_types = {}
            for event in events:
                event_type = event["event_type"]
                if event_type not in event_types:
                    event_types[event_type] = []
                event_types[event_type].append(event)
                
            # Analyze each event type for patterns
            recurring_issues = []
            
            for event_type, type_events in event_types.items():
                if len(type_events) < 3:
                    continue  # Need at least 3 events to identify a pattern
                    
                # Analyze timestamps for periodicity
                timestamps = [datetime.fromisoformat(e["timestamp"]) for e in type_events]
                
                # Calculate time differences between consecutive events
                intervals = []
                for i in range(1, len(timestamps)):
                    delta = timestamps[i] - timestamps[i-1]
                    intervals.append(delta.total_seconds() / 3600)  # hours
                    
                # Check for regular intervals
                if intervals:
                    mean_interval = sum(intervals) / len(intervals)
                    variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
                    std_dev = math.sqrt(variance)
                    
                    # Regular intervals have low relative standard deviation
                    regularity = std_dev / mean_interval if mean_interval > 0 else float('inf')
                    
                    is_regular = regularity < 0.5  # Arbitrary threshold
                    
                    # Determine frequency description
                    if is_regular:
                        if 22 <= mean_interval <= 26:
                            frequency = "daily"
                        elif 164 <= mean_interval <= 172:
                            frequency = "weekly"
                        elif mean_interval < 22:
                            frequency = f"every {round(mean_interval)} hours"
                        else:
                            frequency = f"every {round(mean_interval/24)} days"
                    else:
                        frequency = "irregular"
                        
                    # Group by severity
                    severity_counts = {}
                    for event in type_events:
                        severity = event["severity"]
                        severity_counts[severity] = severity_counts.get(severity, 0) + 1
                        
                    dominant_severity = max(severity_counts.items(), key=lambda x: x[1])[0]
                    
                    recurring_issues.append({
                        "event_type": event_type,
                        "count": len(type_events),
                        "is_regular": is_regular,
                        "frequency": frequency,
                        "mean_interval_hours": mean_interval,
                        "regularity": regularity,
                        "dominant_severity": dominant_severity,
                        "first_occurrence": timestamps[0].isoformat(),
                        "last_occurrence": timestamps[-1].isoformat(),
                        "expected_next": (timestamps[-1] + timedelta(hours=mean_interval)).isoformat() if is_regular else None
                    })
                    
            # Sort by count (most frequent first)
            recurring_issues.sort(key=lambda x: x["count"], reverse=True)
            
            return {
                "success": True,
                "recurring_issues": recurring_issues,
                "event_count": len(events),
                "event_types": len(event_types),
                "analyzed_period_days": days
            }
        except Exception as e:
            logger.error(f"Error analyzing recurring issues: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

if __name__ == "__main__":
    # When run directly, execute a test forecast
    try:
        # Create memory instance
        memory = DeusMemory()
        
        # Create prediction engine
        prediction_engine = PredictionEngine(memory)
        
        # Forecast CPU load for next 24 hours
        result = prediction_engine.forecast_metric("cpu_load", hours_ahead=24)
        print(json.dumps(result, indent=2))
        
        # Generate a maintenance schedule
        schedule = prediction_engine.generate_schedule({
            "cpu_load": result,
            "memory_free_mb": prediction_engine.forecast_metric("memory_free_mb", hours_ahead=24),
            "disk_usage_root": prediction_engine.forecast_metric("disk_usage_root", hours_ahead=24)
        })
        print(json.dumps(schedule, indent=2))
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
        raise