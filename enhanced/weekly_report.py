#!/usr/bin/env python3
"""
Deus Ex Machina - Weekly Report Generator

This script generates and sends a weekly email report of system findings
from the Deus Ex Machina AI consciousness system.
"""

import os
import json
import glob
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
LOG_DIR = os.path.expanduser("~/deus-ex-machina/logs")
REPORT_RECIPIENT = "your.email@example.com"  # Change this
SMTP_SERVER = "smtp.example.com"  # Change this
SMTP_PORT = 587
SMTP_USER = "username"  # Change this
SMTP_PASSWORD = "password"  # Change this

def generate_weekly_report():
    """Generate a weekly report of system findings and insights"""
    # Get findings from the past week
    one_week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    findings_files = glob.glob(os.path.join(LOG_DIR, "findings_*.json"))
    
    # Sort by modification time, newest first
    findings_files.sort(key=os.path.getmtime, reverse=True)
    
    # Collect recent findings
    recent_findings = []
    
    for file_path in findings_files:
        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_time >= one_week_ago:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    recent_findings.append({
                        "timestamp": file_time.isoformat(),
                        "data": data
                    })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Get metrics from the past week
    metrics_files = glob.glob(os.path.join(LOG_DIR, "metrics_*.json"))
    metrics_files.sort(key=os.path.getmtime, reverse=True)
    
    recent_metrics = []
    for file_path in metrics_files:
        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        if file_time >= one_week_ago:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    recent_metrics.append({
                        "timestamp": file_time.isoformat(),
                        "data": data
                    })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Count insights by importance
    high_insights = []
    medium_insights = []
    low_insights = []
    
    for finding in recent_findings:
        for insight in finding["data"].get("insights", []):
            if insight["importance"] == "high":
                high_insights.append({
                    "description": insight["description"],
                    "timestamp": finding["timestamp"],
                    "type": insight.get("type", "unknown")
                })
            elif insight["importance"] == "medium":
                medium_insights.append({
                    "description": insight["description"],
                    "timestamp": finding["timestamp"],
                    "type": insight.get("type", "unknown")
                })
            else:
                low_insights.append({
                    "description": insight["description"],
                    "timestamp": finding["timestamp"],
                    "type": insight.get("type", "unknown")
                })
    
    # Calculate average time spent in each consciousness state
    state_times = {
        "DORMANT": 0,
        "DROWSY": 0,
        "AWARE": 0,
        "ALERT": 0,
        "FULLY_AWAKE": 0
    }
    
    state_time_samples = 0
    
    for metric in recent_metrics:
        for state, percentage in metric["data"].get("state_distribution", {}).items():
            if state in state_times:
                state_times[state] += percentage
                state_time_samples += 1
    
    # Calculate averages
    avg_state_times = {}
    if state_time_samples > 0:
        for state, total in state_times.items():
            avg_state_times[state] = total / state_time_samples
    
    # Generate HTML report
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333366; }}
            h2 {{ color: #666699; }}
            .high {{ color: #cc0000; }}
            .medium {{ color: #ff6600; }}
            .low {{ color: #339933; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .chart-container {{ height: 200px; margin-bottom: 20px; }}
            .bar {{ display: inline-block; background-color: #6699cc; margin-right: 5px; }}
            .bar-label {{ text-align: center; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>Deus Ex Machina - Weekly System Report</h1>
        <p>Report generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <ul>
                <li>Runs in the past week: {len(recent_findings)}</li>
                <li>High priority insights: {len(high_insights)}</li>
                <li>Medium priority insights: {len(medium_insights)}</li>
                <li>Low priority insights: {len(low_insights)}</li>
            </ul>
        </div>
        
        <h2>Consciousness State Distribution</h2>
        <div class="chart-container">
            {"".join(f'<div style="width: {percentage:.1f}%; height: 30px; background-color: {"#ff6666" if state == "FULLY_AWAKE" else "#ffcc66" if state == "ALERT" else "#66cc66" if state == "AWARE" else "#6699cc" if state == "DROWSY" else "#cccccc"}; display: inline-block; margin-right: 5px;"></div>' for state, percentage in avg_state_times.items() if state != "DORMANT" and percentage > 0)}
        </div>
        <table>
            <tr>
                <th>State</th>
                <th>Average Time (%)</th>
            </tr>
            {"".join(f"<tr><td>{state}</td><td>{percentage:.1f}%</td></tr>" for state, percentage in avg_state_times.items() if percentage > 0)}
        </table>
        
        <h2 class="high">High Priority Insights</h2>
        <table>
            <tr><th>Timestamp</th><th>Type</th><th>Description</th></tr>
            {"".join(f"<tr><td>{i['timestamp']}</td><td>{i['type']}</td><td>{i['description']}</td></tr>" for i in high_insights) if high_insights else "<tr><td colspan='3'>No high priority insights</td></tr>"}
        </table>
        
        <h2 class="medium">Medium Priority Insights</h2>
        <table>
            <tr><th>Timestamp</th><th>Type</th><th>Description</th></tr>
            {"".join(f"<tr><td>{i['timestamp']}</td><td>{i['type']}</td><td>{i['description']}</td></tr>" for i in medium_insights) if medium_insights else "<tr><td colspan='3'>No medium priority insights</td></tr>"}
        </table>
        
        <h2>System Activity</h2>
        <table>
            <tr><th>Date</th><th>Tools Used</th><th>Insights</th></tr>
            {"".join(f"<tr><td>{f['timestamp']}</td><td>{sum(f['data'].get('tool_usage', {}).values())}</td><td>{len(f['data'].get('insights', []))}</td></tr>" for f in recent_findings[:10]) if recent_findings else "<tr><td colspan='3'>No activity</td></tr>"}
        </table>
        
        <h2>Most Used Tools</h2>
        <table>
            <tr><th>Tool</th><th>Usage Count</th></tr>
            {"".join(f"<tr><td>{tool}</td><td>{count}</td></tr>" for tool, count in sorted([(t, c) for metrics in recent_metrics for t, c in metrics['data'].get('most_used_tools', [])], key=lambda x: x[1], reverse=True)[:10]) if recent_metrics else "<tr><td colspan='2'>No tool usage data</td></tr>"}
        </table>
        
        <p>Report generated by Deus Ex Machina Enhanced AI System</p>
    </body>
    </html>
    """
    
    # Generate plain text version
    text = f"""
    Deus Ex Machina - Weekly System Report
    ======================================
    
    Report generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Summary:
    - Runs in the past week: {len(recent_findings)}
    - High priority insights: {len(high_insights)}
    - Medium priority insights: {len(medium_insights)}
    - Low priority insights: {len(low_insights)}
    
    Consciousness State Distribution:
    {"".join(f"- {state}: {percentage:.1f}%\n" for state, percentage in avg_state_times.items() if percentage > 0)}
    
    HIGH PRIORITY INSIGHTS:
    {"".join(f"- {i['description']} ({i['timestamp']})\n" for i in high_insights) if high_insights else "None\n"}
    
    MEDIUM PRIORITY INSIGHTS:
    {"".join(f"- {i['description']} ({i['timestamp']})\n" for i in medium_insights) if medium_insights else "None\n"}
    
    Report generated by Deus Ex Machina Enhanced AI System
    """
    
    return html, text

def send_email(html_content, text_content):
    """Send an email with the weekly report"""
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Deus Ex Machina - Weekly System Report - {datetime.datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = SMTP_USER
    msg['To'] = REPORT_RECIPIENT
    
    # Attach parts
    part1 = MIMEText(text_content, 'plain')
    part2 = MIMEText(html_content, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    # Send email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {REPORT_RECIPIENT}")
    except Exception as e:
        print(f"Error sending email: {e}")
        
    # Also save the report locally
    report_file = os.path.join(LOG_DIR, f"weekly_report_{datetime.datetime.now().strftime('%Y%m%d')}.html")
    with open(report_file, 'w') as f:
        f.write(html_content)
    print(f"Report saved to {report_file}")

if __name__ == "__main__":
    # Create the log directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Generate and send the weekly report
    html, text = generate_weekly_report()
    send_email(html, text)