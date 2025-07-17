#!/usr/bin/env python3
"""Test database connection and inserts"""

import os
import asyncio
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

async def test_database():
    # Get credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_KEY")
        return
        
    print(f"🔄 Connecting to Supabase...")
    print(f"   URL: {url}")
    print(f"   Key: {key[:20]}...")
    
    supabase = create_client(url, key)
    
    # First, let's see what columns exist
    print("\n📊 Checking table structure...")
    try:
        # Get one row to see structure
        sample = supabase.table("calls").select("*").limit(1).execute()
        if sample.data:
            print(f"   Available columns: {list(sample.data[0].keys())}")
    except Exception as e:
        print(f"   Could not check structure: {e}")
    
    # Test data - use minimal fields that should exist
    test_call = {
        "call_id": f"test-local-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "status": "queued",
        "customer_name": "Local Test Customer",
        "customer_number": "555-1111"
    }
    
    print(f"\n📝 Attempting to insert: {test_call['call_id']}")
    
    try:
        # Try insert
        result = supabase.table("calls").insert(test_call).execute()
        print(f"✅ Insert successful!")
        print(f"   Response: {result}")
        
        # Verify by reading back
        print(f"\n🔍 Verifying insert...")
        check = supabase.table("calls").select("*").eq("call_id", test_call["call_id"]).execute()
        if check.data:
            print(f"✅ Call found in database!")
            print(f"   Data: {check.data[0]}")
        else:
            print(f"❌ Call not found after insert!")
            
    except Exception as e:
        print(f"❌ Insert failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Try upsert instead
        print(f"\n🔄 Trying upsert instead...")
        try:
            result = supabase.table("calls").upsert(test_call).execute()
            print(f"✅ Upsert successful!")
            print(f"   Response: {result}")
        except Exception as e2:
            print(f"❌ Upsert also failed: {e2}")

if __name__ == "__main__":
    asyncio.run(test_database())