#!/usr/bin/env python3
"""
Production Monitoring Script
Monitor and test the live MCP Call Analyzer
"""

import asyncio
import httpx
import json
from datetime import datetime
import sys

BASE_URL = "https://mcp-call-analyzer-production.up.railway.app"

async def check_health():
    """Check health endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=10.0)
            data = response.json()
            
            print("\n🏥 HEALTH CHECK")
            print("-" * 50)
            print(f"Status: {data.get('status', 'unknown')}")
            print(f"Timestamp: {data.get('timestamp', 'N/A')}")
            
            components = data.get('components', {})
            print("\nComponents:")
            for component, status in components.items():
                emoji = "✅" if "connected" in str(status) or "configured" in str(status) else "❌"
                print(f"  {emoji} {component}: {status}")
                
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

async def test_process_calls():
    """Test call processing endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            print("\n📞 TESTING CALL PROCESSING")
            print("-" * 50)
            
            # Test with small batch
            payload = {
                "days_back": 1,
                "limit": 3
            }
            
            response = await client.post(
                f"{BASE_URL}/process-calls",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success!")
                print(f"  Status: {data.get('status')}")
                print(f"  Message: {data.get('message')}")
                print(f"  Calls Queued: {data.get('calls_queued')}")
                print(f"  Job ID: {data.get('job_id')}")
                return True
            else:
                print(f"❌ Failed with status {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Process calls test failed: {e}")
            return False

async def check_stats():
    """Check statistics endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/stats", timeout=10.0)
            data = response.json()
            
            print("\n📊 STATISTICS")
            print("-" * 50)
            for key, value in data.items():
                print(f"  {key}: {value}")
                
            return True
            
        except Exception as e:
            print(f"❌ Stats check failed: {e}")
            return False

async def monitor_continuous():
    """Continuous monitoring mode"""
    print("🔄 Starting continuous monitoring (Ctrl+C to stop)")
    
    while True:
        print(f"\n{'='*60}")
        print(f"⏰ Check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Run all checks
        health_ok = await check_health()
        stats_ok = await check_stats()
        
        # Summary
        print("\n📋 SUMMARY")
        print("-" * 50)
        print(f"  Health: {'✅ OK' if health_ok else '❌ FAILED'}")
        print(f"  Stats: {'✅ OK' if stats_ok else '❌ FAILED'}")
        
        if not health_ok:
            print("\n⚠️  App may be down or deploying. Check Railway logs.")
        
        # Wait 30 seconds before next check
        print("\n💤 Next check in 30 seconds...")
        await asyncio.sleep(30)

async def main():
    """Main function"""
    print("🚀 MCP Call Analyzer Production Monitor")
    print(f"📍 URL: {BASE_URL}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        await monitor_continuous()
    else:
        # Single check
        health_ok = await check_health()
        stats_ok = await check_stats()
        
        if health_ok and stats_ok:
            # If healthy, test processing
            await test_process_calls()
        
        print("\n💡 Tip: Run with --continuous for ongoing monitoring")

if __name__ == "__main__":
    asyncio.run(main())