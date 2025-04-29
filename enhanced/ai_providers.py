#!/usr/bin/env python3
"""
AI Providers Module - Support for multiple AI services
Provides a unified interface for different AI analysis backends
"""
import os
import sys
import json
import logging
import re
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ai_providers')

class AIProvider(ABC):
    """Abstract base class for AI service providers"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f'ai_provider.{name}')
        
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available and configured"""
        pass
        
    @abstractmethod
    def analyze(self, system_info: Dict[str, Any], 
                log_data: str, 
                metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze system state using this AI provider"""
        pass
        
    def _prepare_prompt(self, system_info: Dict[str, Any], 
                      log_data: str, 
                      metrics_data: Dict[str, Any]) -> str:
        """Prepare a standard prompt for the AI"""
        return f"""
        Analyze this server system state and provide:
        1. A summary of current system health
        2. Any identified issues or anomalies
        3. Recommended actions

        SYSTEM INFORMATION:
        {json.dumps(system_info, indent=2)}

        RECENT LOG ENTRIES:
        {log_data[:1000]}  # Truncate to avoid token limits

        SYSTEM METRICS:
        {json.dumps(metrics_data, indent=2)}
        
        FORMAT YOUR RESPONSE AS A JSON OBJECT WITH THE FOLLOWING KEYS:
        - summary: Overall system health summary
        - issues: List of identified issues
        - anomalies: List of anomalies detected
        - recommendations: List of recommended actions
        - severity: Overall severity (LOW, MEDIUM, HIGH, CRITICAL)
        """
        
    def _extract_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from various response formats"""
        try:
            # Direct JSON parsing
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
            
        # Try to find JSON in code blocks
        try:
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
            
        # Try to find any JSON-like structure
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except (json.JSONDecodeError, AttributeError):
            pass
            
        return None
        
    def _ensure_valid_response(self, response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Ensure the response has all required fields"""
        if not response:
            return {
                'summary': 'Unable to parse AI response',
                'issues': ['AI analysis failed'],
                'anomalies': [],
                'recommendations': ['Check AI service and configuration'],
                'severity': 'MEDIUM',
                'provider': self.name,
                'timestamp': datetime.now().isoformat()
            }
            
        # Ensure all required fields are present
        for key in ['summary', 'issues', 'anomalies', 'recommendations', 'severity']:
            if key not in response:
                if key in ['issues', 'anomalies', 'recommendations']:
                    response[key] = []
                elif key == 'severity':
                    response[key] = 'MEDIUM'
                elif key == 'summary':
                    response[key] = 'No summary provided'
                    
        # Add metadata
        response['provider'] = self.name
        response['timestamp'] = datetime.now().isoformat()
        
        return response

class GoogleAIProvider(AIProvider):
    """Google Generative AI (Gemini) provider"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__('google_ai', config)
        self._genai_module = None
        
    def is_available(self) -> bool:
        """Check if Google AI is available"""
        if not self.config.get('api_key'):
            self.logger.warning("No API key configured for Google AI")
            return False
            
        # Check if the module is installed
        try:
            import google.generativeai
            self._genai_module = google.generativeai
            return True
        except ImportError:
            self.logger.warning("Google Generative AI module not installed")
            return False
            
    def analyze(self, system_info: Dict[str, Any], 
               log_data: str, 
               metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze system state using Google AI"""
        if not self.is_available():
            return None
            
        try:
            # Configure the API
            api_key = self.config.get('api_key')
            self._genai_module.configure(api_key=api_key)
            
            # Prepare the prompt
            prompt = self._prepare_prompt(system_info, log_data, metrics_data)
            
            # Generate content
            model = self._genai_module.GenerativeModel('gemini-pro')
            response = model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.2,
                    'max_output_tokens': 2048,
                    'response_mime_type': 'application/json'
                }
            )
            
            # Extract and validate the response
            if response and hasattr(response, 'text'):
                result = self._extract_json(response.text)
                return self._ensure_valid_response(result)
            else:
                self.logger.warning("Empty or invalid response from Google AI")
                return None
                
        except Exception as e:
            self.logger.error(f"Error using Google AI: {str(e)}")
            return None

class AnthropicProvider(AIProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__('anthropic', config)
        
    def is_available(self) -> bool:
        """Check if Anthropic API is available"""
        if not self.config.get('api_key'):
            self.logger.warning("No API key configured for Anthropic")
            return False
            
        # Simple availability check - we don't need the module installed
        return True
        
    def analyze(self, system_info: Dict[str, Any], 
               log_data: str, 
               metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze system state using Anthropic Claude"""
        if not self.is_available():
            return None
            
        try:
            api_key = self.config.get('api_key')
            model = self.config.get('model', 'claude-3-haiku-20240307')
            
            # Prepare the prompt
            prompt = self._prepare_prompt(system_info, log_data, metrics_data)
            
            # Anthropic API call
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000,
                "temperature": 0.2
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get('content', [])
                text = ''.join([item.get('text', '') for item in content if item.get('type') == 'text'])
                
                if text:
                    result = self._extract_json(text)
                    return self._ensure_valid_response(result)
                else:
                    self.logger.warning("Empty response from Anthropic")
                    return None
            else:
                self.logger.error(f"Anthropic API error: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error using Anthropic: {str(e)}")
            return None

class OpenAIProvider(AIProvider):
    """OpenAI provider"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__('openai', config)
        
    def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        if not self.config.get('api_key'):
            self.logger.warning("No API key configured for OpenAI")
            return False
            
        # Simple availability check - we don't need the module installed
        return True
        
    def analyze(self, system_info: Dict[str, Any], 
               log_data: str, 
               metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze system state using OpenAI"""
        if not self.is_available():
            return None
            
        try:
            api_key = self.config.get('api_key')
            model = self.config.get('model', 'gpt-4-turbo')
            
            # Prepare the messages
            system_prompt = "You are a server monitoring AI that analyzes system state and provides actionable recommendations."
            user_prompt = self._prepare_prompt(system_info, log_data, metrics_data)
            
            # OpenAI API call
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.2
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                choices = response_data.get('choices', [])
                if choices:
                    message = choices[0].get('message', {})
                    content = message.get('content', '')
                    
                    if content:
                        result = self._extract_json(content)
                        return self._ensure_valid_response(result)
                    else:
                        self.logger.warning("Empty response from OpenAI")
                        return None
                else:
                    self.logger.warning("No choices in OpenAI response")
                    return None
            else:
                self.logger.error(f"OpenAI API error: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error using OpenAI: {str(e)}")
            return None

class LocalProvider(AIProvider):
    """Local fallback provider using rule-based analysis"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__('local', config)
        
    def is_available(self) -> bool:
        """Local provider is always available"""
        return True
        
    def analyze(self, system_info: Dict[str, Any], 
               log_data: str, 
               metrics_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze system state using local rules"""
        self.logger.info("Performing local analysis")
        
        issues = []
        anomalies = []
        recommendations = []
        severity = "LOW"
        
        # Check CPU load
        if metrics_data.get('cpu_load_percent', 0) > 90:
            issues.append("High CPU usage detected")
            recommendations.append("Investigate processes causing high CPU")
            severity = "HIGH"
        elif metrics_data.get('cpu_load_percent', 0) > 75:
            issues.append("Elevated CPU usage")
            recommendations.append("Monitor CPU trends")
            severity = max(severity, "MEDIUM")
        
        # Check memory usage
        memory_used_percent = metrics_data.get('memory_used_percent', 0)
        if memory_used_percent > 95:
            issues.append("Critical memory usage")
            recommendations.append("Check for memory leaks or add more RAM")
            severity = "CRITICAL"
        elif memory_used_percent > 85:
            issues.append("High memory usage")
            recommendations.append("Identify memory-intensive processes")
            severity = max(severity, "HIGH")
        
        # Check disk space
        for disk, usage in metrics_data.get('disk_usage', {}).items():
            if usage > 95:
                issues.append(f"Critical disk usage on {disk}")
                recommendations.append(f"Free up space on {disk}")
                severity = "CRITICAL"
            elif usage > 85:
                issues.append(f"High disk usage on {disk}")
                recommendations.append(f"Clean up {disk} or expand storage")
                severity = max(severity, "HIGH")
        
        # Check for relevant log patterns
        error_patterns = [
            'error', 'critical', 'exception', 'fail', 'timeout', 'denied',
            'refused', 'segfault', 'unable to', 'cannot', 'fatal'
        ]
        
        log_issues = set()
        for pattern in error_patterns:
            for line in log_data.split('\n'):
                if pattern in line.lower():
                    # Extract service name if present
                    service_match = re.search(r'\b(\w+)d[:\[]', line)
                    service = service_match.group(1) if service_match else "unknown service"
                    log_issues.add(f"Error detected in {service}")
                    
        if log_issues:
            issues.extend(log_issues)
            recommendations.append("Review system logs for detailed error information")
            severity = max(severity, "MEDIUM")
        
        # Check for uptime-related issues
        if system_info.get('uptime_days', 0) > 365:
            recommendations.append("Consider a planned reboot for system maintenance")
        
        # Analyze load trends if available
        load_trend = metrics_data.get('load_trend', 0)
        if load_trend > 0.2:  # Significant increasing trend
            anomalies.append("Steadily increasing system load detected")
            recommendations.append("Investigate cause of increasing system load")
            severity = max(severity, "MEDIUM")
        
        # Prepare the summary based on the findings
        if not issues and not anomalies:
            summary = "System appears to be healthy"
        else:
            issue_count = len(issues)
            anomaly_count = len(anomalies)
            summary = f"Found {issue_count} issue(s) and {anomaly_count} anomaly/anomalies"
        
        return {
            'summary': summary,
            'issues': issues,
            'anomalies': anomalies,
            'recommendations': recommendations,
            'severity': severity,
            'analysis_method': 'local_rules_based',
            'provider': self.name,
            'timestamp': datetime.now().isoformat()
        }

class AIProviderManager:
    """Manages multiple AI providers and handles fallback"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.providers = []
        self.logger = logging.getLogger('ai_provider_manager')
        
        # Initialize providers
        self._initialize_providers()
        
    def _initialize_providers(self) -> None:
        """Initialize all available providers"""
        # Google AI
        google_config = self.config.get('google_ai', {}).copy()  # Create a copy to avoid modifying original
        if 'api_key_env' in google_config and not google_config.get('api_key'):
            env_var = google_config.pop('api_key_env')
            google_config['api_key'] = os.environ.get(env_var)
            self.logger.info(f"Retrieved Google AI key from environment: {env_var}")
        self.providers.append(GoogleAIProvider(google_config))
        
        # Anthropic
        anthropic_config = self.config.get('anthropic', {}).copy()
        if 'api_key_env' in anthropic_config and not anthropic_config.get('api_key'):
            env_var = anthropic_config.pop('api_key_env')
            anthropic_config['api_key'] = os.environ.get(env_var)
            self.logger.info(f"Retrieved Anthropic key from environment: {env_var}")
        self.providers.append(AnthropicProvider(anthropic_config))
        
        # OpenAI
        openai_config = self.config.get('openai', {}).copy()
        if 'api_key_env' in openai_config and not openai_config.get('api_key'):
            env_var = openai_config.pop('api_key_env')
            openai_config['api_key'] = os.environ.get(env_var)
            self.logger.info(f"Retrieved OpenAI key from environment: {env_var}")
        self.providers.append(OpenAIProvider(openai_config))
        
        # Local (always last as fallback)
        local_config = self.config.get('local', {})
        self.providers.append(LocalProvider(local_config))
        
        # Log initialized providers
        available_providers = [p.name for p in self.providers if p.is_available()]
        self.logger.info(f"Initialized AI providers. Available: {', '.join(available_providers)}")
        
    def analyze(self, system_info: Dict[str, Any], 
               log_data: str, 
               metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Try each provider in order until one succeeds"""
        for provider in self.providers:
            if not provider.is_available():
                continue
                
            try:
                self.logger.info(f"Attempting analysis with provider: {provider.name}")
                result = provider.analyze(system_info, log_data, metrics_data)
                
                if result:
                    self.logger.info(f"Analysis successful with provider: {provider.name}")
                    return result
            except Exception as e:
                self.logger.error(f"Error with provider {provider.name}: {str(e)}")
                
        # If all providers fail, return a basic response
        self.logger.error("All AI providers failed")
        return {
            'summary': 'All AI providers failed',
            'issues': ['Unable to analyze system state'],
            'anomalies': [],
            'recommendations': ['Check AI provider configuration'],
            'severity': 'MEDIUM',
            'provider': 'none',
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Simple test when run directly
    manager = AIProviderManager({
        'google_ai': {'api_key': os.environ.get('GEMINI_API_KEY')},
        'anthropic': {'api_key': os.environ.get('ANTHROPIC_API_KEY')},
        'openai': {'api_key': os.environ.get('OPENAI_API_KEY')}
    })
    
    # Sample data
    system_info = {
        "hostname": "test-server",
        "uptime_days": 45,
        "os_version": "Ubuntu 20.04.5 LTS",
        "kernel": "5.4.0-100-generic"
    }
    
    log_data = """
    Apr 28 12:34:56 test-server systemd[1]: Started System Logging Service.
    Apr 28 12:35:02 test-server kernel: [    0.000000] Memory: 8046784K/8046784K available
    Apr 28 12:36:15 test-server kernel: [   15.356356] EXT4-fs (sda1): mounted filesystem
    Apr 28 12:38:22 test-server nginx[1234]: 192.168.1.1 - - [28/Apr/2025:12:38:22 +0000] "GET / HTTP/1.1" 200 1024
    """
    
    metrics_data = {
        "cpu_load_percent": 45,
        "memory_used_percent": 62,
        "disk_usage": {
            "/": 72,
            "/var": 43
        },
        "load_trend": 0.05
    }
    
    # Run analysis
    result = manager.analyze(system_info, log_data, metrics_data)
    print(json.dumps(result, indent=2))