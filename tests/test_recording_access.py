"""Test different methods to access call recordings"""

import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_recording_access():
    """Test various approaches to access recordings"""
    
    # First authenticate
    async with httpx.AsyncClient() as client:
        auth_response = await client.post(
            "https://autoservice.api.digitalconcierge.io/auth/authenticate",
            json={
                "username": os.getenv("DASHBOARD_USERNAME"),
                "password": os.getenv("DASHBOARD_PASSWORD")
            }
        )
        
        if auth_response.status_code == 200:
            token = auth_response.json()["token"]
            print(f"✅ Authenticated successfully")
            
            # Try different recording URL patterns
            call_sid = "CAa5cbe57a8f3acfa11b034c41856d9cb7"
            recording_patterns = [
                f"https://d3vneafawyd5u6.cloudfront.net/Recordings/{call_sid}.mp3",
                f"https://d3vneafawyd5u6.cloudfront.net/Recordings/RE{call_sid[2:]}.mp3",
                f"https://d3vneafawyd5u6.cloudfront.net/recordings/{call_sid}.mp3",
                f"https://autoservice.api.digitalconcierge.io/recordings/{call_sid}",
                f"https://autoservice.api.digitalconcierge.io/call/{call_sid}/recording"
            ]
            
            headers_options = [
                {"x-access-token": token},
                {"Authorization": f"Bearer {token}"},
                {"Cookie": f"token={token}"},
                {}
            ]
            
            for url in recording_patterns:
                for headers in headers_options:
                    try:
                        print(f"\n🔍 Testing: {url}")
                        print(f"   Headers: {list(headers.keys())}")
                        
                        response = await client.get(url, headers=headers, follow_redirects=True)
                        print(f"   Status: {response.status_code}")
                        
                        if response.status_code == 200:
                            print(f"   ✅ SUCCESS! Content-Type: {response.headers.get('content-type')}")
                            print(f"   Size: {len(response.content)} bytes")
                            return
                        else:
                            print(f"   ❌ Failed: {response.text[:100]}")
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
            
            # Also try to get recording info from the call details
            print("\n📞 Checking call details endpoint...")
            call_response = await client.get(
                f"https://autoservice.api.digitalconcierge.io/call/{call_sid}",
                headers={"x-access-token": token}
            )
            
            if call_response.status_code == 200:
                call_data = call_response.json()
                print(f"Call data keys: {list(call_data.keys())}")
                if 'recording' in str(call_data).lower():
                    print(f"Recording-related fields found: {[k for k in call_data.keys() if 'recording' in k.lower()]}")

if __name__ == "__main__":
    asyncio.run(test_recording_access())