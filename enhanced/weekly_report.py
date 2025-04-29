#!/usr/bin/env python3
"""
Weekly Report Module - Generate and send weekly system reports
Summarizes system health, incidents, and actions over the past week
"""
import os
import sys
import json
import logging
import datetime
import smtplib
import requests
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('weekly_report')

class EmailProvider:
    """Base class for email providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def send_email(self, to: str, subject: str, text_content: str, html_content: str) -> bool:
        """Send an email using this provider"""
        raise NotImplementedError("Subclasses must implement send_email")

class SMTPEmailProvider(EmailProvider):
    """Standard SMTP email provider"""
    
    def send_email(self, to: str, subject: str, text_content: str, html_content: str) -> bool:
        """Send an email using SMTP"""
        try:
            # Get SMTP settings
            smtp_server = self.config.get('smtp_server')
            smtp_port = int(self.config.get('smtp_port', 587))
            smtp_username = self.config.get('smtp_username')
            smtp_password = self.config.get('smtp_password')
            from_email = self.config.get('from_email', smtp_username)
            
            if not all([smtp_server, smtp_port, smtp_username, smtp_password, from_email]):
                logger.error("SMTP configuration is incomplete")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Connect to server and send
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(from_email, to, msg.as_string())
                
            logger.info(f"Email sent to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

class SendgridEmailProvider(EmailProvider):
    """Sendgrid API email provider"""
    
    def send_email(self, to: str, subject: str, text_content: str, html_content: str) -> bool:
        """Send an email using Sendgrid API"""
        try:
            # Get API key
            api_key = self.config.get('api_key')
            from_email = self.config.get('from_email')
            
            if not api_key or not from_email:
                logger.error("Sendgrid configuration is incomplete")
                return False
                
            # Prepare request
            url = "https://api.sendgrid.com/v3/mail/send"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "personalizations": [
                    {
                        "to": [{"email": to}],
                        "subject": subject
                    }
                ],
                "from": {"email": from_email},
                "content": [
                    {
                        "type": "text/plain",
                        "value": text_content
                    },
                    {
                        "type": "text/html",
                        "value": html_content
                    }
                ]
            }
            
            # Send request
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent to {to} via Sendgrid")
                return True
            else:
                logger.error(f"Sendgrid API error: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending via Sendgrid: {str(e)}")
            return False

class MailgunEmailProvider(EmailProvider):
    """Mailgun API email provider"""
    
    def send_email(self, to: str, subject: str, text_content: str, html_content: str) -> bool:
        """Send an email using Mailgun API"""
        try:
            # Get API key and domain
            api_key = self.config.get('api_key')
            domain = self.config.get('domain')
            from_email = self.config.get('from_email', f"deus-ex-machina@{domain}")
            
            if not api_key or not domain:
                logger.error("Mailgun configuration is incomplete")
                return False
                
            # Prepare request
            url = f"https://api.mailgun.net/v3/{domain}/messages"
            auth = ("api", api_key)
            
            data = {
                "from": from_email,
                "to": to,
                "subject": subject,
                "text": text_content,
                "html": html_content
            }
            
            # Send request
            response = requests.post(url, auth=auth, data=data)
            
            if response.status_code == 200:
                logger.info(f"Email sent to {to} via Mailgun")
                return True
            else:
                logger.error(f"Mailgun API error: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending via Mailgun: {str(e)}")
            return False

class WeeklyReportGenerator:
    """Generates weekly system reports"""
    
    def __init__(self, install_dir: str, log_dir: str, config: Dict[str, Any]):
        self.install_dir = install_dir
        self.log_dir = log_dir
        self.config = config
        self.email_provider = self._initialize_email_provider()
        
    def _initialize_email_provider(self) -> Optional[EmailProvider]:
        """Initialize the email provider based on configuration"""
        provider_type = self.config.get('email_provider', 'smtp')
        
        if provider_type == 'smtp':
            provider_config = self.config.get('email_config', {})
            return SMTPEmailProvider(provider_config)
        elif provider_type == 'sendgrid':
            provider_config = self.config.get('sendgrid_config', {})
            return SendgridEmailProvider(provider_config)
        elif provider_type == 'mailgun':
            provider_config = self.config.get('mailgun_config', {})
            return MailgunEmailProvider(provider_config)
        else:
            logger.error(f"Unknown email provider: {provider_type}")
            return None
            
    def collect_system_data(self) -> Dict[str, Any]:
        """Collect data from system logs and metrics"""
        data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'current_metrics': {},
            'uptime_days': 0,
            'state_history': [],
            'consciousness_data': {
                'current_state': 'UNKNOWN',
                'state_transitions_count': 0,
                'state_distribution': {},
                'time_fully_awake_percent': 0,
                'time_dormant_percent': 0,
                'awakening_triggers': [],
                'ai_providers_used': []
            },
            'incidents': [],
            'service_issues': [],
            'recommendations': []
        }
        
        # Get current heartbeat data
        try:
            heartbeat_path = os.path.join(self.log_dir, "heartbeat.json")
            if os.path.exists(heartbeat_path):
                with open(heartbeat_path, 'r') as f:
                    heartbeat = json.load(f)
                    data['current_metrics'] = heartbeat
                    
                    # Extract uptime in days
                    uptime_str = heartbeat.get('uptime', '')
                    weeks = 0
                    days = 0
                    if 'week' in uptime_str:
                        weeks_match = re.search(r'(\d+) weeks?', uptime_str)
                        if weeks_match:
                            weeks = int(weeks_match.group(1))
                    if 'day' in uptime_str:
                        days_match = re.search(r'(\d+) days?', uptime_str)
                        if days_match:
                            days = int(days_match.group(1))
                    data['uptime_days'] = (weeks * 7) + days
        except Exception as e:
            logger.error(f"Error collecting heartbeat data: {str(e)}")
            
        # Get current state
        try:
            state_path = os.path.join(self.log_dir, "state.json")
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state_data = json.load(f)
                    data['current_state'] = state_data.get('state', 'unknown')
        except Exception as e:
            logger.error(f"Error collecting state data: {str(e)}")
            
        # Get service issues
        try:
            service_path = os.path.join(self.log_dir, "service_status.log")
            if os.path.exists(service_path):
                with open(service_path, 'r') as f:
                    service_data = f.read()
                    failed_services = []
                    for line in service_data.split('\n'):
                        if 'failed failed' in line:
                            # Extract service name
                            service_match = re.search(r'●\s+([^\s]+)', line)
                            if service_match:
                                failed_services.append(service_match.group(1))
                    data['service_issues'] = failed_services
        except Exception as e:
            logger.error(f"Error collecting service data: {str(e)}")
            
        # Get state history from logs
        try:
            state_log_path = os.path.join(self.log_dir, "state_engine.log")
            if os.path.exists(state_log_path):
                # Get entries from the past week
                with open(state_log_path, 'r') as f:
                    log_data = f.read()
                    # Extract state transitions
                    transitions = re.findall(r'State changed from ([a-z]+) to ([a-z]+) \(([^)]+)\)', log_data)
                    # Keep only the last 10 transitions for the report
                    data['state_history'] = [
                        {'from': t[0], 'to': t[1], 'reason': t[2]} 
                        for t in transitions[-10:]
                    ]
        except Exception as e:
            logger.error(f"Error collecting state history: {str(e)}")
            
        # Get consciousness data from enhanced logs
        try:
            enhanced_log_path = os.path.join(self.log_dir, "enhanced.log")
            if os.path.exists(enhanced_log_path):
                with open(enhanced_log_path, 'r') as f:
                    log_lines = f.readlines()
                    
                # Process log lines to extract consciousness information
                consciousness_states = {}
                state_transitions = []
                ai_providers = set()
                awakening_triggers = []
                current_state = "UNKNOWN"
                
                # Process the last week of logs (up to 10000 lines)
                for line in log_lines[-10000:]:
                    # Extract consciousness state changes
                    if "Consciousness state changed:" in line:
                        match = re.search(r'Consciousness state changed: ([A-Z_]+) -> ([A-Z_]+) \(([^)]+)\)', line)
                        if match:
                            from_state, to_state, reason = match.groups()
                            state_transitions.append((from_state, to_state, reason))
                            current_state = to_state
                            
                            # Save awakening triggers (transitions to higher states)
                            if to_state in ['ALERT', 'FULLY_AWAKE'] and "Manual" not in reason:
                                awakening_triggers.append(reason)
                    
                    # Extract current state info
                    elif "Current state: " in line:
                        match = re.search(r'Current state: ([A-Z_]+)', line)
                        if match:
                            current_state = match.group(1)
                    
                    # Count time spent in each state
                    elif "Running " in line and " state " in line:
                        for state in ["DORMANT", "DROWSY", "AWARE", "ALERT", "FULLY_AWAKE"]:
                            if f"Running {state.lower()} state" in line:
                                consciousness_states[state] = consciousness_states.get(state, 0) + 1
                    
                    # Track AI providers used
                    elif "Analysis successful with provider:" in line:
                        match = re.search(r'Analysis successful with provider: ([a-z_]+)', line)
                        if match:
                            ai_providers.add(match.group(1))
                            
                # Calculate statistics
                total_entries = sum(consciousness_states.values()) or 1  # Avoid division by zero
                
                # Set the consciousness data
                data['consciousness_data']['current_state'] = current_state
                data['consciousness_data']['state_transitions_count'] = len(state_transitions)
                data['consciousness_data']['state_distribution'] = {
                    state: round((count / total_entries) * 100, 1) 
                    for state, count in consciousness_states.items()
                }
                
                # Calculate time spent in highest and lowest states
                data['consciousness_data']['time_fully_awake_percent'] = data['consciousness_data']['state_distribution'].get('FULLY_AWAKE', 0)
                data['consciousness_data']['time_dormant_percent'] = data['consciousness_data']['state_distribution'].get('DORMANT', 0)
                
                # Get unique awakening triggers and AI providers
                data['consciousness_data']['awakening_triggers'] = list(set(awakening_triggers))[-5:]  # Last 5 unique triggers
                data['consciousness_data']['ai_providers_used'] = list(ai_providers)
                
        except Exception as e:
            logger.error(f"Error collecting consciousness data: {str(e)}")
            
        # Generate recommendations based on collected data
        recommendations = []
        
        # Check failed services
        if data['service_issues']:
            recommendations.append(f"Investigate failed services: {', '.join(data['service_issues'])}")
            
        # Check uptime
        if data['uptime_days'] > 90:
            recommendations.append(f"Consider a planned reboot as system uptime is {data['uptime_days']} days")
            
        # Check disk usage
        disk_usage = int(data['current_metrics'].get('disk_usage_root', '0'))
        if disk_usage > 80:
            recommendations.append(f"Disk usage is high ({disk_usage}%). Consider cleaning old logs or temporary files")
            
        data['recommendations'] = recommendations
        
        return data
        
    def generate_text_report(self, data: Dict[str, Any]) -> str:
        """Generate a plain text report"""
        report = [
            "DEUS EX MACHINA - WEEKLY SYSTEM REPORT",
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "CURRENT SYSTEM STATE",
            "=====================",
            f"State: {data.get('current_state', 'Unknown')}",
            f"CPU Load: {data['current_metrics'].get('cpu_load', 'Unknown')}",
            f"Memory Free: {data['current_metrics'].get('memory_free_mb', 'Unknown')}MB",
            f"Disk Usage (Root): {data['current_metrics'].get('disk_usage_root', 'Unknown')}%",
            f"Open Ports: {data['current_metrics'].get('open_ports', 'Unknown')}",
            f"Total Processes: {data['current_metrics'].get('total_processes', 'Unknown')}",
            f"System Uptime: {data['current_metrics'].get('uptime', 'Unknown')}",
            "",
        ]
        
        # Add service issues
        if data['service_issues']:
            report.extend([
                "FAILED SERVICES",
                "===============",
            ])
            for service in data['service_issues']:
                report.append(f"- {service}")
            report.append("")
        
        # Add state history
        if data['state_history']:
            report.extend([
                "RECENT STATE TRANSITIONS",
                "=======================",
            ])
            for transition in data['state_history']:
                report.append(f"- {transition['from']} → {transition['to']}: {transition['reason']}")
            report.append("")
            
        # Add AI consciousness section
        report.extend([
            "AI CONSCIOUSNESS ACTIVITY",
            "=========================",
            f"Current State: {data['consciousness_data']['current_state']}",
            f"State Transitions: {data['consciousness_data']['state_transitions_count']} times",
            f"Time Fully Awake: {data['consciousness_data']['time_fully_awake_percent']}%",
            f"Time Dormant: {data['consciousness_data']['time_dormant_percent']}%",
            "",
        ])
        
        # Add state distribution if available
        if data['consciousness_data']['state_distribution']:
            report.append("Time Spent in Each State:")
            for state, percentage in data['consciousness_data']['state_distribution'].items():
                report.append(f"- {state}: {percentage}%")
            report.append("")
            
        # Add awakening triggers if available
        if data['consciousness_data']['awakening_triggers']:
            report.append("Recent Awakening Triggers:")
            for trigger in data['consciousness_data']['awakening_triggers']:
                report.append(f"- {trigger}")
            report.append("")
            
        # Add AI providers used if available
        if data['consciousness_data']['ai_providers_used']:
            report.append("AI Providers Used:")
            for provider in data['consciousness_data']['ai_providers_used']:
                report.append(f"- {provider}")
            report.append("")
            
        # Add recommendations
        if data['recommendations']:
            report.extend([
                "RECOMMENDATIONS",
                "===============",
            ])
            for recommendation in data['recommendations']:
                report.append(f"- {recommendation}")
            report.append("")
            
        # Add footer
        report.extend([
            "",
            "This report was automatically generated by Deus Ex Machina.",
            "To modify your report settings, update your configuration file."
        ])
        
        return "\n".join(report)
        
    def generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate an HTML report"""
        # CSS styles for the report
        styles = """
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f7f7f7;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #fff;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .consciousness-overview {
                background-color: #f0f7ff;
                border-left: 4px solid #3498db;
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 4px;
            }
            .state-distribution {
                max-width: 60%;
            }
            .status-dormant {
                color: #6c757d;
            }
            h3 {
                color: #34495e;
                margin-top: 25px;
            }
            .triggers-list li, .providers-list li {
                margin-bottom: 8px;
            }
            .header {
                background-color: #2c3e50;
                color: #fff;
                padding: 20px;
                border-radius: 5px 5px 0 0;
                margin: -20px -20px 20px;
            }
            h1 {
                margin: 0;
                font-size: 24px;
            }
            h2 {
                color: #2c3e50;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
                margin-top: 30px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            .status-ok {
                color: #28a745;
            }
            .status-warning {
                color: #ffc107;
            }
            .status-critical {
                color: #dc3545;
            }
            .footer {
                margin-top: 30px;
                padding-top: 10px;
                border-top: 1px solid #eee;
                font-size: 12px;
                color: #777;
            }
        </style>
        """
        
        # Determine system status
        system_status = "status-ok"
        if data['service_issues'] or len(data['recommendations']) > 0:
            system_status = "status-warning"
            
        # Format disk usage with color
        disk_usage = int(data['current_metrics'].get('disk_usage_root', '0'))
        disk_class = "status-ok"
        if disk_usage > 85:
            disk_class = "status-critical"
        elif disk_usage > 70:
            disk_class = "status-warning"
            
        # Build HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Deus Ex Machina - Weekly System Report</title>
            {styles}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Deus Ex Machina - Weekly System Report</h1>
                    <p>Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <h2>System Overview</h2>
                <table>
                    <tr>
                        <th>Status</th>
                        <td><span class="{system_status}">● {data.get('current_state', 'Unknown').upper()}</span></td>
                    </tr>
                    <tr>
                        <th>Uptime</th>
                        <td>{data['current_metrics'].get('uptime', 'Unknown')}</td>
                    </tr>
                    <tr>
                        <th>CPU Load</th>
                        <td>{data['current_metrics'].get('cpu_load', 'Unknown')}</td>
                    </tr>
                    <tr>
                        <th>Memory Free</th>
                        <td>{data['current_metrics'].get('memory_free_mb', 'Unknown')}MB</td>
                    </tr>
                    <tr>
                        <th>Disk Usage (Root)</th>
                        <td><span class="{disk_class}">{data['current_metrics'].get('disk_usage_root', 'Unknown')}%</span></td>
                    </tr>
                    <tr>
                        <th>Open Ports</th>
                        <td>{data['current_metrics'].get('open_ports', 'Unknown')}</td>
                    </tr>
                    <tr>
                        <th>Total Processes</th>
                        <td>{data['current_metrics'].get('total_processes', 'Unknown')}</td>
                    </tr>
                </table>
        """
        
        # Add service issues section if there are any
        if data['service_issues']:
            html += """
                <h2>Failed Services</h2>
                <table>
                    <tr>
                        <th>Service</th>
                    </tr>
            """
            for service in data['service_issues']:
                html += f"""
                    <tr>
                        <td class="status-critical">{service}</td>
                    </tr>
                """
            html += "</table>"
            
        # Add state history section if there is any
        if data['state_history']:
            html += """
                <h2>Recent State Transitions</h2>
                <table>
                    <tr>
                        <th>From</th>
                        <th>To</th>
                        <th>Reason</th>
                    </tr>
            """
            for transition in data['state_history']:
                html += f"""
                    <tr>
                        <td>{transition['from']}</td>
                        <td>{transition['to']}</td>
                        <td>{transition['reason']}</td>
                    </tr>
                """
            html += "</table>"
            
        # Add AI Consciousness section
        html += """
            <h2>AI Consciousness Activity</h2>
            <p>Information about the system's biological-inspired awareness states and activity.</p>
            
            <div class="consciousness-overview">
                <table>
                    <tr>
                        <th>Current State</th>
                        <td><strong>{}</strong></td>
                    </tr>
                    <tr>
                        <th>State Transitions</th>
                        <td>{} times</td>
                    </tr>
                    <tr>
                        <th>Time Fully Awake</th>
                        <td>{}%</td>
                    </tr>
                    <tr>
                        <th>Time Dormant</th>
                        <td>{}%</td>
                    </tr>
                </table>
            </div>
        """.format(
            data['consciousness_data']['current_state'],
            data['consciousness_data']['state_transitions_count'],
            data['consciousness_data']['time_fully_awake_percent'],
            data['consciousness_data']['time_dormant_percent']
        )
        
        # Add consciousness state distribution if available
        if data['consciousness_data']['state_distribution']:
            html += """
                <h3>Time Spent in Each State</h3>
                <div class="state-distribution">
                    <table>
                        <tr>
                            <th>State</th>
                            <th>Percentage</th>
                        </tr>
            """
            
            for state, percentage in data['consciousness_data']['state_distribution'].items():
                # Determine color based on the state
                color_class = "status-ok"
                if state == "ALERT":
                    color_class = "status-warning"
                elif state == "FULLY_AWAKE":
                    color_class = "status-critical"
                elif state == "DORMANT":
                    color_class = "status-dormant"
                    
                html += f"""
                        <tr>
                            <td>{state}</td>
                            <td class="{color_class}">{percentage}%</td>
                        </tr>
                """
                
            html += """
                    </table>
                </div>
            """
            
        # Add awakening triggers if available
        if data['consciousness_data']['awakening_triggers']:
            html += """
                <h3>Recent Awakening Triggers</h3>
                <ul class="triggers-list">
            """
            
            for trigger in data['consciousness_data']['awakening_triggers']:
                html += f"""
                    <li>{trigger}</li>
                """
                
            html += """
                </ul>
            """
            
        # Add AI providers used if available
        if data['consciousness_data']['ai_providers_used']:
            html += """
                <h3>AI Providers Used</h3>
                <ul class="providers-list">
            """
            
            for provider in data['consciousness_data']['ai_providers_used']:
                html += f"""
                    <li>{provider}</li>
                """
                
            html += """
                </ul>
            """
        
        # Add recommendations section if there are any
        if data['recommendations']:
            html += """
                <h2>Recommendations</h2>
                <ul>
            """
            for recommendation in data['recommendations']:
                html += f"""
                    <li>{recommendation}</li>
                """
            html += "</ul>"
            
        # Add footer and close HTML
        html += """
                <div class="footer">
                    <p>This report was automatically generated by Deus Ex Machina.</p>
                    <p>To modify your report settings, update your configuration file.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
        
    def send_report(self, to_email: str) -> bool:
        """Generate and send a weekly report"""
        if not self.email_provider:
            logger.error("No email provider configured")
            return False
            
        # Collect data
        data = self.collect_system_data()
        
        # Generate reports
        text_report = self.generate_text_report(data)
        html_report = self.generate_html_report(data)
        
        # Generate hostname for subject
        hostname = data['current_metrics'].get('hostname', 'unknown-server')
        if not hostname:
            try:
                import socket
                hostname = socket.gethostname()
            except:
                hostname = "unknown-server"
        
        # Send email
        subject = f"Deus Ex Machina Weekly Report - {hostname}"
        return self.email_provider.send_email(to_email, subject, text_report, html_report)
        
def generate_weekly_report(config_path: str = None, email: str = None) -> bool:
    """Generate and send a weekly report"""
    try:
        # Load configuration
        if config_path is None:
            config_path = "/home/claude/deus_test/config/report_config.json"
            
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                
        # Override email if provided
        if email:
            config['report_email'] = email
            
        # Check if email is configured
        if not config.get('report_email'):
            logger.error("No recipient email configured")
            return False
            
        # Initialize report generator
        install_dir = os.environ.get('DEUS_INSTALL_DIR', '/home/DeusExMachina')
        log_dir = os.environ.get('DEUS_LOG_DIR', '/var/log/deus-ex-machina')
        
        generator = WeeklyReportGenerator(install_dir, log_dir, config)
        
        # Send report
        return generator.send_report(config['report_email'])
        
    except Exception as e:
        logger.error(f"Error generating weekly report: {str(e)}")
        return False
        
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate and send a weekly system report')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--email', help='Email to send report to (overrides config)')
    
    args = parser.parse_args()
    
    if generate_weekly_report(args.config, args.email):
        print("Weekly report sent successfully")
    else:
        print("Failed to send weekly report")
        sys.exit(1)