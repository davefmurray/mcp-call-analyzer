#!/usr/bin/env python3
"""
Inspect Call Structure
Deep dive into the call data to find audio URLs
"""

import asyncio
import os
import sys
from pathlib import Path
import json
from pprint import pprint

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.scraper_api import DCAPIScraper
from dotenv import load_dotenv

load_dotenv()


async def inspect_call_structure():
    """Inspect the full structure of call data"""
    
    print("🔍 INSPECTING CALL DATA STRUCTURE")
    print("=" * 80)
    
    # Initialize API scraper
    api_scraper = DCAPIScraper()
    
    # Authenticate
    await api_scraper.authenticate()
    
    # Get one call with recording
    calls = await api_scraper.get_calls(limit=5, days_back=1)
    
    # Find a call with recording
    call_with_recording = None
    for call in calls:
        if call.get('RecordingSid'):
            call_with_recording = call
            break
    
    if not call_with_recording:
        print("❌ No calls with recordings found!")
        return
    
    print("\n📞 FULL CALL DATA STRUCTURE")
    print("-" * 60)
    
    # Pretty print the entire call object
    print(json.dumps(call_with_recording, indent=2, default=str))
    
    print("\n\n🔑 LOOKING FOR URL-LIKE VALUES")
    print("-" * 60)
    
    # Recursively search for URL-like values
    def find_urls(obj, path=""):
        urls = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                if isinstance(value, str) and ('http' in value or 'cloudfront' in value or '.mp3' in value):
                    urls.append((new_path, value))
                else:
                    urls.extend(find_urls(value, new_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                urls.extend(find_urls(item, f"{path}[{i}]"))
        return urls
    
    found_urls = find_urls(call_with_recording)
    
    if found_urls:
        print("\n✅ Found URL-like values:")
        for path, url in found_urls:
            print(f"\n  Path: {path}")
            print(f"  URL: {url}")
    else:
        print("\n❌ No URL-like values found in call data")
    
    # Save for reference
    with open('call_structure_inspection.json', 'w') as f:
        json.dump({
            'call_data': call_with_recording,
            'found_urls': found_urls
        }, f, indent=2, default=str)
    
    print(f"\n📄 Full inspection saved to: call_structure_inspection.json")
    
    await api_scraper.client.aclose()
    print("\n✅ Inspection complete!")


if __name__ == "__main__":
    asyncio.run(inspect_call_structure())