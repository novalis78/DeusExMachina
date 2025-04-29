#!/usr/bin/env python3
"""
Generate a sample report to preview the weekly reporting feature.
This script creates an HTML and text version of the weekly report
without actually sending an email.
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the weekly report module
from weekly_report import WeeklyReportGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('sample_report')

def generate_sample_report(output_dir=None):
    """Generate a sample report and save it to files"""
    try:
        # Define default output directory
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output file paths
        html_path = os.path.join(output_dir, f"deus_report_{datetime.now().strftime('%Y%m%d')}.html")
        text_path = os.path.join(output_dir, f"deus_report_{datetime.now().strftime('%Y%m%d')}.txt")
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config', 'report_config.json')
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # Initialize report generator
        install_dir = os.environ.get('DEUS_INSTALL_DIR', '/home/DeusExMachina')
        log_dir = os.environ.get('DEUS_LOG_DIR', '/var/log/deus-ex-machina')
        
        generator = WeeklyReportGenerator(install_dir, log_dir, config)
        
        # Collect data
        data = generator.collect_system_data()
        
        # Generate reports
        text_report = generator.generate_text_report(data)
        html_report = generator.generate_html_report(data)
        
        # Save reports to files
        with open(html_path, 'w') as f:
            f.write(html_report)
            
        with open(text_path, 'w') as f:
            f.write(text_report)
            
        logger.info(f"Sample HTML report saved to: {html_path}")
        logger.info(f"Sample text report saved to: {text_path}")
        
        return html_path, text_path
        
    except Exception as e:
        logger.error(f"Error generating sample report: {str(e)}")
        return None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a sample weekly report')
    parser.add_argument('--output-dir', help='Directory to save the report files')
    
    args = parser.parse_args()
    
    html_file, text_file = generate_sample_report(args.output_dir)
    
    if html_file and text_file:
        print(f"Sample report files generated successfully!")
        print(f"HTML report: {html_file}")
        print(f"Text report: {text_file}")
    else:
        print("Failed to generate sample report files.")
        sys.exit(1)