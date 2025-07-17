#!/usr/bin/env python3
"""
Test API Signed URLs
Get actual signed URLs from the API
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import json
import httpx

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


async def test_api_signed_urls():
    """Test getting signed URLs from API"""
    
    print("🚀 API SIGNED URLS TEST")
    print("=" * 80)
    
    # Initialize API scraper
    api_scraper = DCAPIScraper()
    
    # Authenticate
    print("\n🔑 Authenticating...")
    await api_scraper.authenticate()
    
    # Get recent calls
    print("\n📞 Fetching recent calls...")
    calls = await api_scraper.get_calls(limit=10, days_back=1)
    
    print(f"✅ Found {len(calls)} calls")
    
    # Test getting call details with audio URLs
    print("\n🔍 Testing call details API...")
    print("-" * 60)
    
    results = []
    
    for i, call in enumerate(calls[:5], 1):
        if not call.get('RecordingSid'):
            continue
            
        call_sid = call.get('CallSid')
        dc_call_id = call.get('_id')
        
        print(f"\n[{i}] Call: {call_sid}")
        print(f"  DC ID: {dc_call_id}")
        print(f"  Customer: {call.get('name', 'Unknown')}")
        print(f"  RecordingSid: {call.get('RecordingSid')}")
        
        # Try different API endpoints
        endpoints = [
            f"/call/{dc_call_id}",
            f"/call/{dc_call_id}/recording",
            f"/call/{dc_call_id}/audio",
            f"/recording/{call.get('RecordingSid')}",
            f"/calls/{call_sid}/recording"
        ]
        
        for endpoint in endpoints:
            try:
                print(f"\n  Testing endpoint: {endpoint}")
                
                response = await api_scraper.client.get(
                    f"{api_scraper.base_url}{endpoint}",
                    headers={"x-access-token": api_scraper.token}
                )
                
                print(f"    Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"    Response keys: {list(data.keys())[:10]}")
                    
                    # Look for audio URLs
                    for key in ['recordingUrl', 'audioUrl', 'url', 'signedUrl', 'downloadUrl']:
                        if key in data:
                            print(f"    ✅ Found {key}: {data[key][:80]}...")
                            results.append({
                                'call_id': call_sid,
                                'endpoint': endpoint,
                                'url_key': key,
                                'url': data[key]
                            })
                
            except Exception as e:
                print(f"    Error: {e}")
    
    # Test direct recording endpoint
    print("\n\n🎵 Testing direct recording endpoints...")
    print("-" * 60)
    
    # Try to get recording list
    try:
        response = await api_scraper.client.get(
            f"{api_scraper.base_url}/recordings",
            headers={"x-access-token": api_scraper.token}
        )
        print(f"\n/recordings endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response type: {type(data)}")
            if isinstance(data, list):
                print(f"Found {len(data)} recordings")
            elif isinstance(data, dict):
                print(f"Response keys: {list(data.keys())}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Summary
    print("\n\n📊 SUMMARY")
    print("=" * 80)
    
    if results:
        print(f"\n✅ Found {len(results)} audio URLs:")
        for r in results:
            print(f"\n  Call: {r['call_id']}")
            print(f"  Endpoint: {r['endpoint']}")
            print(f"  URL: {r['url'][:100]}...")
            
            # Test downloading
            print(f"  Testing download...")
            try:
                download_response = await api_scraper.client.get(
                    r['url'],
                    headers={"x-access-token": api_scraper.token},
                    follow_redirects=True
                )
                print(f"    Download status: {download_response.status_code}")
                if download_response.status_code == 200:
                    print(f"    ✅ Download successful! Size: {len(download_response.content):,} bytes")
                else:
                    print(f"    ❌ Download failed")
            except Exception as e:
                print(f"    Error: {e}")
    else:
        print("\n❌ No audio URLs found")
    
    # Save results
    report_file = f"api_signed_urls_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'results': results,
            'total_calls': len(calls)
        }, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")
    
    await api_scraper.client.aclose()
    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_api_signed_urls())