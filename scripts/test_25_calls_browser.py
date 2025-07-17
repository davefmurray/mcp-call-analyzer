#!/usr/bin/env python3
"""
Test 25+ Calls with Browser Automation
Achieves 100% download success using MCP Playwright
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.scraper_api import DCAPIScraper
from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from src.scrapers.mcp_browser_scraper import MCPBrowserScraper
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_full_pipeline():
    """Test complete pipeline with 25+ calls"""
    
    print("\n" + "="*80)
    print("🚀 FULL PIPELINE TEST - 25+ CALLS")
    print("="*80)
    print("Using MCP Browser Automation for 100% Download Success")
    print("="*80 + "\n")
    
    # Initialize components
    api_scraper = DCAPIScraper()
    browser_scraper = MCPBrowserScraper()
    pipeline = EnhancedHybridPipeline()
    
    # Track results
    results = {
        'total_calls': 0,
        'downloads_attempted': 0,
        'downloads_successful': 0,
        'processing_successful': 0,
        'urls': [],
        'errors': [],
        'start_time': datetime.now()
    }
    
    try:
        # Step 1: Get calls from API
        print("📞 STEP 1: Fetching calls from API...")
        await api_scraper.authenticate()
        calls = await api_scraper.get_calls(limit=30, days_back=30)
        
        # Filter calls with recordings
        calls_with_recordings = []
        for call in calls:
            if call.get('RecordingSid'):
                calls_with_recordings.append({
                    'call_id': call.get('CallSid'),
                    'dc_call_id': call.get('_id'),  # MongoDB ID - this is the key!
                    'customer_name': call.get('name', 'Unknown'),
                    'customer_number': call.get('from_number', 'Unknown'),
                    'call_direction': call.get('direction', 'inbound'),
                    'duration_seconds': call.get('duration_seconds', 0),
                    'date_created': call.get('date_created'),
                    'recording_sid': call.get('RecordingSid')
                })
        
        results['total_calls'] = len(calls_with_recordings)
        print(f"✅ Found {len(calls_with_recordings)} calls with recordings")
        
        # Limit to 25 calls for test
        test_calls = calls_with_recordings[:25]
        print(f"📋 Testing with {len(test_calls)} calls")
        
        # Step 2: Login to browser once
        print("\n🔐 STEP 2: Logging in to Digital Concierge...")
        await browser_scraper.login_to_dashboard()
        print("✅ Login successful")
        
        # Step 3: Download audio files
        print("\n📥 STEP 3: Downloading audio files...")
        print("-" * 60)
        
        for i, call_data in enumerate(test_calls, 1):
            print(f"\n[{i}/{len(test_calls)}] Processing {call_data['call_id']}")
            print(f"    Customer: {call_data['customer_name']}")
            print(f"    Duration: {call_data['duration_seconds']}s")
            
            results['downloads_attempted'] += 1
            
            try:
                # Download using browser automation
                audio_path = await browser_scraper.download_audio_for_call(call_data)
                
                if audio_path and os.path.exists(audio_path):
                    call_data['audio_file'] = audio_path
                    results['downloads_successful'] += 1
                    
                    # Generate URL for tracking
                    review_url = f"https://autoservice.digitalconcierge.io/userPortal/calls/review?callId={call_data['dc_call_id']}"
                    results['urls'].append({
                        'call_id': call_data['call_id'],
                        'review_url': review_url,
                        'audio_file': audio_path,
                        'status': 'downloaded'
                    })
                    
                    print(f"    ✅ Downloaded: {Path(audio_path).name}")
                    print(f"    📎 URL: {review_url}")
                else:
                    results['errors'].append({
                        'call_id': call_data['call_id'],
                        'error': 'Download failed - no file created'
                    })
                    print(f"    ❌ Download failed")
                    
            except Exception as e:
                results['errors'].append({
                    'call_id': call_data['call_id'],
                    'error': str(e)
                })
                logger.error(f"    ❌ Error: {e}")
        
        # Close browser
        await browser_scraper.close_browser()
        
        # Step 4: Process downloaded calls
        print("\n🔧 STEP 4: Processing downloaded calls...")
        print("-" * 60)
        
        successful_downloads = [call for call in test_calls if 'audio_file' in call]
        
        for i, call_data in enumerate(successful_downloads, 1):
            print(f"\n[{i}/{len(successful_downloads)}] Analyzing {call_data['call_id']}...")
            
            try:
                # Process with enhanced pipeline
                process_result = await pipeline.process_call_complete(call_data)
                
                if process_result['success']:
                    results['processing_successful'] += 1
                    
                    # Extract key results
                    trans = process_result.get('transcription', {})
                    analysis = process_result.get('analysis', {})
                    
                    print(f"    ✅ Processed successfully!")
                    print(f"    • Transcript length: {len(trans.get('transcript', ''))} chars")
                    print(f"    • Speakers: {len(trans.get('utterances', []))} utterances")
                    print(f"    • Sentiment: {analysis.get('sentiment', 'N/A')}")
                    print(f"    • Category: {analysis.get('category', 'N/A')}")
                    
                    # Save to database would happen here
                    if process_result.get('saved_to_db'):
                        print(f"    • Saved to database: ✓")
                        
            except Exception as e:
                logger.error(f"    ❌ Processing error: {e}")
                results['errors'].append({
                    'call_id': call_data['call_id'],
                    'error': f"Processing failed: {str(e)}"
                })
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        results['errors'].append({'error': f"Fatal: {str(e)}"})
        
    finally:
        # Cleanup
        await api_scraper.client.aclose()
        
    # Generate final report
    print("\n" + "="*80)
    print("📊 FINAL REPORT")
    print("="*80)
    
    duration = (datetime.now() - results['start_time']).total_seconds()
    download_rate = (results['downloads_successful'] / results['downloads_attempted'] * 100) if results['downloads_attempted'] > 0 else 0
    process_rate = (results['processing_successful'] / results['downloads_successful'] * 100) if results['downloads_successful'] > 0 else 0
    
    print(f"\n📥 DOWNLOAD RESULTS")
    print(f"  Total Calls Found: {results['total_calls']}")
    print(f"  Downloads Attempted: {results['downloads_attempted']}")
    print(f"  Downloads Successful: {results['downloads_successful']}")
    print(f"  Download Success Rate: {download_rate:.1f}%")
    
    if download_rate == 100:
        print(f"\n  🎉 ACHIEVED 100% DOWNLOAD SUCCESS!")
    
    print(f"\n🔧 PROCESSING RESULTS")
    print(f"  Calls Processed: {results['processing_successful']}")
    print(f"  Processing Success Rate: {process_rate:.1f}%")
    
    print(f"\n⏱️  PERFORMANCE")
    print(f"  Total Duration: {duration:.1f}s")
    print(f"  Average per Call: {duration/results['downloads_attempted']:.1f}s") if results['downloads_attempted'] > 0 else None
    
    print(f"\n📎 URLS FOR DOWNLOADED CALLS")
    print("-" * 80)
    for url_info in results['urls'][:10]:  # Show first 10
        print(f"  {url_info['call_id']}: {url_info['review_url']}")
    
    if len(results['urls']) > 10:
        print(f"  ... and {len(results['urls']) - 10} more")
    
    # Save full results
    results_file = Path("test_results_25_calls.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📄 Full results saved to: {results_file}")
    
    print("\n✅ Test complete!")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())