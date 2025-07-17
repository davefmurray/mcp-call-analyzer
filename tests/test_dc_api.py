"""Test Digital Concierge API authentication and calls endpoint"""

import httpx
import asyncio
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def test_api():
    """Test API authentication and call list"""
    
    # Test authentication
    print("🔐 Testing authentication...")
    async with httpx.AsyncClient() as client:
        auth_response = await client.post(
            "https://autoservice.api.digitalconcierge.io/auth/authenticate",
            json={
                "username": os.getenv("DASHBOARD_USERNAME"),
                "password": os.getenv("DASHBOARD_PASSWORD")
            }
        )
        
        print(f"Auth status: {auth_response.status_code}")
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            print(f"Auth response keys: {list(auth_data.keys())}")
            token = auth_data.get("token")
            print(f"Token received: {token[:50]}...")
            
            # Test different header formats
            print("\n📞 Testing call list endpoint...")
            
            # Test 1: Bearer token
            print("\n1. Testing with Bearer token...")
            headers1 = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response1 = await client.post(
                "https://autoservice.api.digitalconcierge.io/call/list",
                json={"limit": 1},
                headers=headers1
            )
            print(f"   Status: {response1.status_code}")
            print(f"   Response: {response1.text[:200]}")
            
            # Test 2: Just token
            print("\n2. Testing with just token...")
            headers2 = {
                "Authorization": token,
                "Content-Type": "application/json"
            }
            
            response2 = await client.post(
                "https://autoservice.api.digitalconcierge.io/call/list",
                json={"limit": 1},
                headers=headers2
            )
            print(f"   Status: {response2.status_code}")
            print(f"   Response: {response2.text[:200]}")
            
            # Test 3: x-auth-token header
            print("\n3. Testing with x-auth-token...")
            headers3 = {
                "x-auth-token": token,
                "Content-Type": "application/json"
            }
            
            response3 = await client.post(
                "https://autoservice.api.digitalconcierge.io/call/list",
                json={"limit": 1},
                headers=headers3
            )
            print(f"   Status: {response3.status_code}")
            print(f"   Response: {response3.text[:200]}")
            
            # Test 4: Cookie
            print("\n4. Testing with cookie...")
            headers4 = {
                "Content-Type": "application/json",
                "Cookie": f"token={token}"
            }
            
            response4 = await client.post(
                "https://autoservice.api.digitalconcierge.io/call/list",
                json={"limit": 1},
                headers=headers4
            )
            print(f"   Status: {response4.status_code}")
            print(f"   Response: {response4.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_api())