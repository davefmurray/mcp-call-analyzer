#!/usr/bin/env python3
"""
Test Downloads with Correct MongoDB IDs
This will fetch fresh data and download audio files
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.scraper_api import DCAPIScraper
from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_downloads():
    """Test downloads with correct MongoDB IDs"""
    
    print("🚀 TESTING DOWNLOADS WITH CORRECT IDs")
    print("=" * 80)
    
    # Initialize components
    api_scraper = DCAPIScraper()
    pipeline = EnhancedHybridPipeline()
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # Step 1: Get fresh calls from API
    print("\n📞 Step 1: Fetching fresh calls from API...")
    await api_scraper.authenticate()
    calls = await api_scraper.get_calls(limit=10, days_back=1)
    
    print(f"✅ Found {len(calls)} calls")
    
    # Step 2: Store calls with correct IDs
    print("\n💾 Step 2: Storing calls with correct MongoDB IDs...")
    
    stored_calls = []
    for call in calls[:5]:  # Process first 5
        if call.get('RecordingSid'):  # Only calls with recordings
            call_data = {
                'call_id': call.get('CallSid'),
                'dc_call_id': call.get('_id'),  # CORRECT MongoDB ID
                'customer_name': call.get('name', 'Unknown'),
                'customer_number': call.get('From') or call.get('Caller'),
                'call_direction': 'inbound' if call.get('Direction') == 'inbound' else 'outbound',
                'duration_seconds': call.get('CallDuration', 0),
                'date_created': call.get('date_created'),
                'has_recording': True,
                'status': 'pending_download',
                'extension': call.get('ext', '')
            }
            
            # Upsert to database
            result = supabase.table('calls').upsert(call_data).execute()
            stored_calls.append(call_data)
            
            print(f"  ✅ Stored: {call_data['call_id']} with DC ID: {call_data['dc_call_id']}")
    
    print(f"\n✅ Stored {len(stored_calls)} calls with correct IDs")
    
    # Step 3: Test downloads
    print("\n📥 Step 3: Testing audio downloads...")
    print("-" * 60)
    
    download_results = []
    
    for call in stored_calls:
        print(f"\nDownloading {call['call_id']}...")
        print(f"  DC ID: {call['dc_call_id']}")
        print(f"  Customer: {call['customer_name']}")
        
        try:
            # Get call details using correct ID
            call_details = await api_scraper.get_call_details(call['dc_call_id'])
            
            if call_details:
                # Extract audio URL
                audio_url = api_scraper.extract_audio_url(call_details)
                
                if audio_url:
                    print(f"  🎵 Audio URL: {audio_url[:80]}...")
                    
                    # Download audio
                    output_path = f"downloads/{call['call_id']}.mp3"
                    success = await api_scraper.download_audio(audio_url, output_path)
                    
                    if success:
                        download_results.append({
                            'call_id': call['call_id'],
                            'status': 'success',
                            'path': output_path
                        })
                        print(f"  ✅ Downloaded successfully!")
                    else:
                        download_results.append({
                            'call_id': call['call_id'],
                            'status': 'failed',
                            'reason': 'Download failed'
                        })
                        print(f"  ❌ Download failed")
                else:
                    download_results.append({
                        'call_id': call['call_id'],
                        'status': 'failed',
                        'reason': 'No audio URL'
                    })
                    print(f"  ❌ No audio URL found")
            else:
                download_results.append({
                    'call_id': call['call_id'],
                    'status': 'failed',
                    'reason': 'No call details'
                })
                print(f"  ❌ Could not get call details")
                
        except Exception as e:
            download_results.append({
                'call_id': call['call_id'],
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ Error: {e}")
    
    # Step 4: Process downloaded files
    print("\n🔧 Step 4: Processing downloaded files...")
    print("-" * 60)
    
    successful_downloads = [r for r in download_results if r['status'] == 'success']
    
    for result in successful_downloads:
        call_data = next(c for c in stored_calls if c['call_id'] == result['call_id'])
        
        print(f"\nProcessing {call_data['call_id']}...")
        
        try:
            # Process with enhanced pipeline
            process_result = await pipeline.process_call_complete(call_data)
            
            if process_result['success']:
                trans = process_result['transcription']
                print(f"  ✅ Processed successfully!")
                print(f"  • Speakers: {len(trans.get('utterances', []))} utterances")
                print(f"  • Script Compliance: {trans.get('script_compliance', {}).get('score', 0):.0f}%")
                print(f"  • Talk Ratio: Employee {trans.get('quality_metrics', {}).get('talk_ratio', {}).get('employee', 0):.0f}%, Customer {trans.get('quality_metrics', {}).get('talk_ratio', {}).get('customer', 0):.0f}%")
        except Exception as e:
            print(f"  ❌ Processing error: {e}")
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 DOWNLOAD TEST REPORT")
    print("=" * 80)
    
    successful = len([r for r in download_results if r['status'] == 'success'])
    failed = len([r for r in download_results if r['status'] in ['failed', 'error']])
    
    print(f"\nTotal Attempts: {len(download_results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {successful/len(download_results)*100:.1f}%")
    
    if successful == len(download_results):
        print("\n🎉 ACHIEVED 100% DOWNLOAD SUCCESS!")
    else:
        print("\n❌ Failed downloads:")
        for result in download_results:
            if result['status'] != 'success':
                print(f"  • {result['call_id']}: {result.get('reason', result.get('error', 'Unknown'))}")
    
    # Clean up httpx client
    await api_scraper.client.aclose()
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_downloads())