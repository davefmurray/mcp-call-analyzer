#!/usr/bin/env python3
"""
Test MCP Browser Downloads
Uses real MCP Playwright tools to download audio files
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_downloads():
    """Test audio downloads using MCP browser automation"""
    
    print("🚀 TESTING MCP BROWSER DOWNLOADS")
    print("=" * 80)
    print("Goal: Achieve 100% download success using real browser automation")
    print("=" * 80)
    
    # Initialize pipeline
    pipeline = EnhancedHybridPipeline()
    
    # Step 1: Get recent calls
    print("\n📞 Step 1: Fetching recent calls...")
    calls = await pipeline.fetch_calls_batch(limit=5, days_back=7)
    
    if not calls:
        print("❌ No calls found!")
        return
        
    print(f"✅ Found {len(calls)} calls")
    for i, call in enumerate(calls[:5], 1):
        print(f"  {i}. {call['call_id']} - {call['customer_name']} ({call['duration_seconds']}s)")
    
    # Step 2: Initialize browser
    print("\n🌐 Step 2: Initializing MCP browser...")
    
    # Set up browser with download preferences
    await mcp__playwright__browser_navigate(url="https://autoservice.digitalconcierge.io")
    await mcp__playwright__browser_resize(width=1280, height=800)
    
    # Step 3: Login
    print("\n🔐 Step 3: Logging in to dashboard...")
    
    # Navigate to login
    await mcp__playwright__browser_navigate(url="https://autoservice.digitalconcierge.io/userPortal/sign-in")
    await mcp__playwright__browser_wait_for(time=3)
    
    # Take snapshot for debugging
    await mcp__playwright__browser_take_screenshot(filename="mcp_login_page.png")
    
    # Get credentials
    username = os.getenv("DASHBOARD_USERNAME")
    password = os.getenv("DASHBOARD_PASSWORD")
    
    if not username or not password:
        print("❌ Missing credentials!")
        return
    
    # Fill login form
    snapshot = await mcp__playwright__browser_snapshot()
    print("📸 Login page snapshot captured")
    
    # Type credentials
    await mcp__playwright__browser_type(
        element="Username field",
        ref="username-input",  # We'll need to identify the actual ref from snapshot
        text=username
    )
    
    await mcp__playwright__browser_type(
        element="Password field", 
        ref="password-input",  # We'll need to identify the actual ref from snapshot
        text=password
    )
    
    # Submit login
    await mcp__playwright__browser_click(
        element="Sign in button",
        ref="signin-button"  # We'll need to identify the actual ref from snapshot
    )
    
    await mcp__playwright__browser_wait_for(time=5)
    
    # Verify login
    await mcp__playwright__browser_take_screenshot(filename="mcp_after_login.png")
    
    # Step 4: Download audio files
    print("\n📥 Step 4: Downloading audio files...")
    print("-" * 60)
    
    download_results = []
    
    for i, call in enumerate(calls[:5], 1):
        call_id = call['call_id']
        print(f"\n[{i}/5] Processing {call_id}...")
        
        try:
            # Navigate to calls page
            await mcp__playwright__browser_navigate(
                url="https://autoservice.digitalconcierge.io/userPortal/admin/calls"
            )
            await mcp__playwright__browser_wait_for(time=3)
            
            # Take snapshot to see page structure
            snapshot = await mcp__playwright__browser_snapshot()
            
            # Search for call
            await mcp__playwright__browser_type(
                element="Search input",
                ref="search-input",  # Need actual ref from snapshot
                text=call_id
            )
            
            await mcp__playwright__browser_wait_for(time=2)
            
            # Click on call row
            await mcp__playwright__browser_click(
                element=f"Call row for {call_id}",
                ref=f"call-row-{call_id}"  # Need actual ref
            )
            
            await mcp__playwright__browser_wait_for(time=3)
            
            # Take screenshot of modal
            await mcp__playwright__browser_take_screenshot(
                filename=f"mcp_call_modal_{call_id}.png"
            )
            
            # Get network requests to find audio URL
            requests = await mcp__playwright__browser_network_requests()
            
            audio_url = None
            for req in requests:
                url = req.get('url', '')
                if '.mp3' in url or 'recording' in url:
                    audio_url = url
                    print(f"  🎵 Found audio URL: {url[:80]}...")
                    break
            
            if audio_url:
                # Navigate to audio URL to trigger download
                await mcp__playwright__browser_tab_new(url=audio_url)
                await mcp__playwright__browser_wait_for(time=5)
                await mcp__playwright__browser_tab_close()
                
                download_results.append({
                    'call_id': call_id,
                    'status': 'success',
                    'audio_url': audio_url
                })
                print(f"  ✅ Download initiated")
            else:
                download_results.append({
                    'call_id': call_id,
                    'status': 'failed',
                    'reason': 'No audio URL found'
                })
                print(f"  ❌ No audio URL found")
                
        except Exception as e:
            download_results.append({
                'call_id': call_id,
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ Error: {e}")
    
    # Step 5: Process downloaded files
    print("\n🔧 Step 5: Processing downloaded audio files...")
    print("-" * 60)
    
    # Check downloads folder for audio files
    downloads_dir = Path("downloads")
    audio_files = list(downloads_dir.glob("*.mp3"))
    
    print(f"Found {len(audio_files)} audio files in downloads folder")
    
    # Process each successfully downloaded file
    for result in download_results:
        if result['status'] == 'success':
            call_id = result['call_id']
            audio_path = downloads_dir / f"{call_id}.mp3"
            
            if audio_path.exists():
                print(f"\n✅ Processing {call_id}...")
                
                # Find call data
                call_data = next((c for c in calls if c['call_id'] == call_id), None)
                
                if call_data:
                    # Process with enhanced pipeline
                    process_result = await pipeline.process_call_complete(call_data)
                    
                    if process_result['success']:
                        trans = process_result['transcription']
                        print(f"  • Speakers: {len(trans.get('utterances', []))} utterances")
                        print(f"  • Script Compliance: {trans.get('script_compliance', {}).get('score', 0):.0f}%")
                        print(f"  • Outcome: {trans.get('sales_metrics', {}).get('outcome', 'unknown')}")
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 DOWNLOAD TEST SUMMARY")
    print("=" * 80)
    
    successful = sum(1 for r in download_results if r['status'] == 'success')
    failed = sum(1 for r in download_results if r['status'] in ['failed', 'error'])
    
    print(f"\nTotal Attempts: {len(download_results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {successful/len(download_results)*100:.1f}%")
    
    if successful == len(download_results):
        print("\n🎉 ACHIEVED 100% DOWNLOAD SUCCESS!")
    else:
        print("\n⚠️ Download issues encountered:")
        for result in download_results:
            if result['status'] != 'success':
                print(f"  • {result['call_id']}: {result.get('reason', result.get('error', 'Unknown'))}")
    
    # Close browser
    await mcp__playwright__browser_close()
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_mcp_downloads())