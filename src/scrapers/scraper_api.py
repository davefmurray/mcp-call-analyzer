"""
Digital Concierge API-based Call Scraper

This scraper uses the DC API endpoints directly instead of web scraping.
Much more reliable and faster than browser automation.

Process:
1. Authenticate to get JWT token
2. Use token to call /call/list endpoint
3. Process the structured data
4. Download audio files from CloudFront URLs
"""

import httpx
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
from urllib.parse import urlparse

load_dotenv()

class DCAPIScraper:
    def __init__(self):
        self.base_url = "https://autoservice.api.digitalconcierge.io"
        self.username = os.getenv("DASHBOARD_USERNAME")
        self.password = os.getenv("DASHBOARD_PASSWORD")
        self.token = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _parse_duration(self, duration) -> int:
        """Parse duration - can be int (seconds) or string like '1:23'"""
        if isinstance(duration, int):
            return duration
        
        if not duration or duration == '0:00':
            return 0
        
        if isinstance(duration, str):
            parts = duration.split(':')
            if len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + int(seconds)
            elif len(parts) == 3:
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        
        return 0
        
    async def authenticate(self) -> str:
        """Authenticate and get JWT token"""
        print("🔐 Authenticating with DC API...")
        
        auth_data = {
            "username": self.username,
            "password": self.password
        }
        
        response = await self.client.post(
            f"{self.base_url}/auth/authenticate",
            json=auth_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 Auth response keys: {list(result.keys())}")
            
            # Try different possible token field names
            self.token = result.get("token") or result.get("access_token") or result.get("accessToken") or result.get("jwt")
            
            if not self.token and isinstance(result, str):
                # Sometimes the token is returned directly as a string
                self.token = result
            
            print(f"✅ Authentication successful! Token: {self.token[:20]}..." if self.token else "❌ No token found")
            return self.token
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
    async def get_calls(self, limit: int = 100, days_back: int = 30) -> List[Dict]:
        """Fetch calls from the API"""
        if not self.token:
            await self.authenticate()
        
        print(f"📞 Fetching calls from the last {days_back} days...")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # API request payload - matching browser format
        payload = {
            "query": {
                "$and": [
                    {"date_created": {"$gte": start_date.strftime("%Y-%m-%dT00:00:00-04:00")}},
                    {"date_created": {"$lte": end_date.strftime("%Y-%m-%dT23:59:59-04:00")}}
                ]
            },
            "searchText": "",
            "page": 1,
            "limit": limit,
            "sort": {"date_created": -1}  # -1 for descending order
        }
        
        headers = {
            "x-access-token": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"🔍 Using x-access-token header")
        
        response = await self.client.post(
            f"{self.base_url}/call/list",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Response keys: {list(data.keys())}")
            
            # Try different possible field names for the calls array
            calls = data.get("docs") or data.get("calls") or data.get("data") or data.get("results") or data.get("items") or []
            
            # If data is the array directly
            if isinstance(data, list):
                calls = data
            
            print(f"✅ Found {len(calls)} calls")
            return calls
        else:
            raise Exception(f"Failed to fetch calls: {response.status_code} - {response.text}")
    
    async def get_call_details(self, call_sid: str) -> Optional[Dict]:
        """Get detailed information about a specific call"""
        if not self.token:
            await self.authenticate()
        
        headers = {
            "x-access-token": self.token
        }
        
        response = await self.client.get(
            f"{self.base_url}/call/{call_sid}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  Could not get details for call {call_sid}")
            return None
    
    def extract_audio_url(self, call_data: Dict) -> Optional[str]:
        """Extract audio URL from call data"""
        # Check various possible fields for audio URL
        recording_url = call_data.get("recordingUrl")
        if recording_url:
            return recording_url
        
        # Check if there's a recording ID to construct URL
        recording_id = call_data.get("recordingId") or call_data.get("CallSid")
        if recording_id:
            # Construct CloudFront URL based on pattern
            return f"https://d3vneafawyd5u6.cloudfront.net/Recordings/{recording_id}.mp3"
        
        return None
    
    async def download_audio(self, url: str, output_path: str) -> bool:
        """Download audio file from URL"""
        try:
            print(f"📥 Downloading audio from: {url}")
            response = await self.client.get(url, follow_redirects=True)
            
            if response.status_code == 200:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Audio saved to: {output_path}")
                return True
            else:
                print(f"⚠️  Failed to download audio: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️  Error downloading audio: {e}")
            return False
    
    async def process_calls(self, limit: int = 10):
        """Main process to fetch and process calls"""
        try:
            # Get calls from API
            calls = await self.get_calls(limit=limit)
            
            processed_calls = []
            
            for idx, call in enumerate(calls):
                if idx == 0:
                    print(f"\n🔍 First call keys: {list(call.keys())}")
                
                print(f"\n{'='*60}")
                print(f"Processing call: {call.get('call_sid') or call.get('CallSid', 'Unknown')}")
                
                # Extract call data - using actual field names from API
                call_info = {
                    'call_id': call.get('CallSid'),
                    'dc_call_id': call.get('_id'),
                    'customer_name': call.get('name', ''),
                    'customer_number': call.get('From', ''),
                    'to_number': call.get('To', ''),
                    'call_direction': call.get('Direction', 'inbound'),
                    'duration_seconds': self._parse_duration(call.get('convertedDuration', '0:00')),
                    'date_created': call.get('date_created', ''),
                    'tenant_id': call.get('tenantId', ''),
                    'status': call.get('status', ''),
                    'has_recording': bool(call.get('recordingId') or call.get('recordingUrl')),
                    'extension': call.get('ext', ''),
                    'entry_point': call.get('entryPoint', ''),
                    'site_info': call.get('siteInfo', {})
                }
                
                print(f"📋 Call Info:")
                print(f"   Customer: {call_info['customer_name']} ({call_info['customer_number']})")
                print(f"   Duration: {call_info['duration_seconds']}s")
                print(f"   Date: {call_info['date_created']}")
                print(f"   Has Recording: {call_info['has_recording']}")
                
                # Download audio if available
                if call_info['has_recording']:
                    audio_url = self.extract_audio_url(call)
                    if audio_url:
                        filename = f"downloads/{call_info['call_id']}.mp3"
                        success = await self.download_audio(audio_url, filename)
                        if success:
                            call_info['audio_file'] = filename
                            call_info['audio_url'] = audio_url
                
                processed_calls.append(call_info)
            
            return processed_calls
            
        except Exception as e:
            print(f"❌ Error processing calls: {e}")
            raise
        finally:
            await self.client.aclose()


async def main():
    """Run the API scraper"""
    scraper = DCAPIScraper()
    
    # Process recent calls
    calls = await scraper.process_calls(limit=5)
    
    print(f"\n\n📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total calls processed: {len(calls)}")
    print(f"Calls with recordings: {sum(1 for c in calls if c.get('has_recording'))}")
    
    # Save results to JSON for reference
    with open('api_scraped_calls.json', 'w') as f:
        json.dump(calls, f, indent=2)
    print(f"\n💾 Results saved to api_scraped_calls.json")


if __name__ == "__main__":
    asyncio.run(main())