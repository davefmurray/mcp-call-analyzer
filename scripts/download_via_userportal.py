#!/usr/bin/env python3
"""
Download Audio via User Portal
Navigate to the correct URL and download MP3 files
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import json
from typing import Dict, List, Optional
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.scraper_api import DCAPIScraper
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def download_call_audio(dc_call_id: str, call_sid: str) -> bool:
    """Download audio for a specific call using browser automation"""
    
    print(f"\n🌐 Downloading audio for call {call_sid}")
    print(f"   DC ID: {dc_call_id}")
    
    # The exact URL pattern you provided
    review_url = f"https://autoservice.digitalconcierge.io/userPortal/calls/review?callId={dc_call_id}"
    print(f"   URL: {review_url}")
    
    # TODO: Use MCP browser automation here
    # For now, returning the URL pattern
    
    return review_url


async def test_userportal_downloads():
    """Test downloading via user portal"""
    
    print("🚀 USER PORTAL DOWNLOAD TEST")
    print("=" * 80)
    print("Using the exact URL pattern from earlier chat")
    print("=" * 80)
    
    # Initialize API scraper to get call data
    api_scraper = DCAPIScraper()
    
    # Authenticate
    print("\n🔑 Getting call data from API...")
    await api_scraper.authenticate()
    
    # Get recent calls
    calls = await api_scraper.get_calls(limit=25, days_back=30)
    
    # Filter calls with recordings
    calls_with_recordings = []
    for call in calls:
        if call.get('RecordingSid'):
            calls_with_recordings.append({
                'call_id': call.get('CallSid'),
                'dc_call_id': call.get('_id'),
                'customer_name': call.get('name', 'Unknown'),
                'recording_sid': call.get('RecordingSid')
            })
    
    print(f"\n✅ Found {len(calls_with_recordings)} calls with recordings")
    
    # Generate URLs for first 5 calls
    print("\n📋 USER PORTAL URLS")
    print("-" * 80)
    
    download_urls = []
    
    for i, call in enumerate(calls_with_recordings[:5], 1):
        print(f"\n[{i}] Call: {call['call_id']}")
        print(f"    Customer: {call['customer_name']}")
        print(f"    DC ID: {call['dc_call_id']}")
        
        url = await download_call_audio(call['dc_call_id'], call['call_id'])
        download_urls.append({
            'call': call,
            'url': url
        })
    
    # Save URLs for reference
    report_data = {
        'test_date': datetime.now().isoformat(),
        'base_url': 'https://autoservice.digitalconcierge.io/',
        'login_url': 'https://autoservice.digitalconcierge.io/',
        'review_url_pattern': 'https://autoservice.digitalconcierge.io/userPortal/calls/review?callId={dc_call_id}',
        'download_urls': download_urls,
        'instructions': [
            '1. Navigate to https://autoservice.digitalconcierge.io/',
            '2. Login with credentials',
            '3. Navigate to review URL with callId parameter',
            '4. Click on the row to launch modal',
            '5. Download MP3 file from modal'
        ]
    }
    
    report_file = f"userportal_urls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n\n📄 URLs saved to: {report_file}")
    
    # Cleanup
    await api_scraper.client.aclose()
    
    print("\n✅ Test complete!")
    print("\nNext step: Use browser automation to navigate to these URLs and download MP3s")


if __name__ == "__main__":
    asyncio.run(test_userportal_downloads())