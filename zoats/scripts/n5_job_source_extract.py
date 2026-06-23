#!/usr/bin/env python3
"""
Extract job postings from URLs and add to Google Sheets.
Fully automated with Google Sheets API integration.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)sZ %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration — read from config/job_sourcing.json
import json as _json

def _load_job_sourcing_config():
    config_path = Path(__file__).resolve().parent.parent / "config" / "job_sourcing.json"
    if not config_path.exists():
        logger.error(f"Config file missing: {config_path}")
        logger.error("Copy config/job_sourcing.example.json to config/job_sourcing.json and fill in your values.")
        sys.exit(1)
    with open(config_path) as f:
        return _json.load(f)

_config = _load_job_sourcing_config()
SHEET_ID = _config["sheet_id"]
CREDENTIALS_PATH = str(Path(__file__).resolve().parent.parent / _config.get("credentials_path", "config/credentials/google_service_account.json"))


def get_sheets_client():
    """Initialize and return Google Sheets client."""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_PATH,
        scope
    )
    return gspread.authorize(creds)


def extract_job_title_from_content(content: str) -> str:
    """Extract job title from markdown content."""
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('# ') and len(line) > 2:
            return line.lstrip('#').strip()
    return "Untitled Position"


def extract_location_from_content(content: str) -> str:
    """Extract location from markdown content."""
    lines = content.split('\n')
    for line in lines:
        line_lower = line.lower()
        if 'location' in line_lower or 'where:' in line_lower:
            if ':' in line:
                location = line.split(':', 1)[1].strip()
                if location:
                    return location
        # Look for common location patterns
        if any(keyword in line_lower for keyword in ['remote', 'hybrid', 'on-site', 'onsite']):
            return line.strip()
    return "Not specified"


def append_job_to_sheet(job_data: dict) -> bool:
    """
    Append job data to Google Sheet.
    Returns True if successful, False otherwise.
    """
    try:
        client = get_sheets_client()
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.get_worksheet(0)
        
        # Prepare row data
        row = [
            job_data['date'],
            job_data['title'],
            job_data['location'],
            job_data['description'],
            job_data['url']
        ]
        
        # Append to sheet
        worksheet.append_row(row, value_input_option='RAW')
        
        logger.info(f"✓ Successfully added job to sheet: {job_data['title']}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to append to sheet: {e}")
        return False


def main(url: str, md_content: str = None, title: str = None, location: str = None):
    """
    Main workflow:
    1. Accept extracted job content (from Zo's view_webpage)
    2. Parse job data
    3. Append to Google Sheet
    
    Args:
        url: Job posting URL
        md_content: Extracted markdown content (optional, Zo will provide)
        title: Job title (optional, will extract from content if not provided)
        location: Job location (optional, will extract from content if not provided)
    """
    logger.info(f"Starting job extraction workflow for: {url}")
    
    if not md_content:
        logger.error("No content provided. This script expects Zo to extract content first.")
        print("ERROR: This script must be called with extracted job content.")
        print("Please use: n5 job-source-extract <url>")
        print("(Zo will handle the extraction and call this script)")
        return 1
    
    # Extract metadata
    if not title:
        title = extract_job_title_from_content(md_content)
    if not location:
        location = extract_location_from_content(md_content)
    
    # Prepare job data
    job_data = {
        'date': datetime.now().strftime("%m/%d/%Y"),
        'title': title,
        'location': location,
        'description': md_content,
        'url': url
    }
    
    logger.info(f"Job title: {title}")
    logger.info(f"Location: {location}")
    logger.info(f"Description length: {len(md_content)} characters")
    
    # Append to Google Sheet
    success = append_job_to_sheet(job_data)
    
    if success:
        logger.info("="*60)
        logger.info("SUCCESS! Job added to Google Sheet.")
        logger.info(f"View sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        logger.info("="*60)
        return 0
    else:
        logger.error("Failed to add job to sheet. Check logs above.")
        return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python n5_job_source_extract.py <job_url> [--content <markdown_file>]")
        print()
        print("Note: This script is designed to be called by Zo after extracting job content.")
        print("For end-to-end workflow, use: n5 job-source-extract <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Check if content file provided
    md_content = None
    if len(sys.argv) >= 4 and sys.argv[2] == "--content":
        content_file = Path(sys.argv[3])
        if content_file.exists():
            md_content = content_file.read_text()
    
    sys.exit(main(url, md_content))
