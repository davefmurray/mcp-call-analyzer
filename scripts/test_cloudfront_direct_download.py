#!/usr/bin/env python3
"""
Direct CloudFront Download Test
Uses RecordingSid to construct direct URLs for 100% download success
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import httpx
from typing import Dict, List, Optional
import json

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


class CloudFrontDirectDownloader:
    """Downloads audio files directly from CloudFront using RecordingSid"""
    
    def __init__(self):
        self.cloudfront_base = "https://d3vneafawyd5u6.cloudfront.net/Recordings"
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        self.client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        
    async def download_from_recording_sid(self, recording_sid: str, call_id: str) -> Optional[str]:
        """Download audio using RecordingSid to construct direct URL"""
        
        output_path = self.downloads_dir / f"{call_id}.mp3"
        
        # Skip if already exists
        if output_path.exists():
            logger.info(f"✅ Audio already exists: {output_path.name}")
            return str(output_path)
        
        # Construct direct CloudFront URL
        url = f"{self.cloudfront_base}/{recording_sid}.mp3"
        logger.info(f"📥 Downloading from: {url}")
        
        try:
            # Download with retries
            for attempt in range(3):
                try:
                    response = await self.client.get(url)
                    
                    if response.status_code == 200:
                        # Save audio file
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                        
                        file_size = len(response.content)
                        logger.info(f"✅ Downloaded {file_size:,} bytes to {output_path.name}")
                        return str(output_path)
                    else:
                        logger.warning(f"Attempt {attempt + 1} failed: HTTP {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} error: {e}")
                    
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            logger.error(f"Failed to download {recording_sid} after 3 attempts")
            return None
            
        except Exception as e:
            logger.error(f"Download error for {recording_sid}: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


async def test_cloudfront_downloads():
    """Test direct CloudFront downloads for 100% success"""
    
    print("🚀 CLOUDFRONT DIRECT DOWNLOAD TEST")
    print("=" * 80)
    print("Using RecordingSid to construct direct CloudFront URLs")
    print("=" * 80)
    
    # Initialize components
    api_scraper = DCAPIScraper()
    downloader = CloudFrontDirectDownloader()
    pipeline = EnhancedHybridPipeline()
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # Step 1: Get fresh calls from API
    print("\n📞 Step 1: Fetching recent calls with recordings...")
    await api_scraper.authenticate()
    calls = await api_scraper.get_calls(limit=50, days_back=30)
    
    # Filter calls with RecordingSid
    calls_with_recordings = []
    for call in calls:
        if call.get('RecordingSid'):
            calls_with_recordings.append(call)
    
    print(f"✅ Found {len(calls_with_recordings)} calls with recordings")
    
    if not calls_with_recordings:
        print("❌ No calls with RecordingSid found!")
        await api_scraper.client.aclose()
        await downloader.close()
        return
    
    # Step 2: Download audio files
    print(f"\n📥 Step 2: Downloading {min(25, len(calls_with_recordings))} audio files...")
    print("-" * 60)
    
    download_results = {
        "successful": [],
        "failed": [],
        "total": 0
    }
    
    start_time = datetime.now()
    
    for i, call in enumerate(calls_with_recordings[:25], 1):
        recording_sid = call.get('RecordingSid')
        call_sid = call.get('CallSid')
        
        print(f"\n[{i}/25] Processing {call_sid}")
        print(f"  Customer: {call.get('name', 'Unknown')}")
        print(f"  RecordingSid: {recording_sid}")
        
        # Prepare call data for storage
        call_data = {
            'call_id': call_sid,
            'dc_call_id': call.get('_id'),
            'customer_name': call.get('name', 'Unknown'),
            'customer_number': call.get('From') or call.get('Caller'),
            'call_direction': 'inbound' if call.get('Direction') == 'inbound' else 'outbound',
            'duration_seconds': call.get('CallDuration', 0),
            'date_created': call.get('date_created'),
            'has_recording': True,
            'status': 'pending_download',
            'extension': call.get('ext', ''),
            'recording_sid': recording_sid
        }
        
        # Store in database
        result = supabase.table('calls').upsert(call_data).execute()
        
        # Download audio
        audio_path = await downloader.download_from_recording_sid(recording_sid, call_sid)
        
        download_results["total"] += 1
        
        if audio_path:
            download_results["successful"].append({
                "call": call_data,
                "audio_path": audio_path
            })
            
            # Update status
            supabase.table('calls').update({
                'status': 'downloaded',
                'audio_file_path': audio_path
            }).eq('call_id', call_sid).execute()
        else:
            download_results["failed"].append(call_data)
    
    download_time = (datetime.now() - start_time).total_seconds()
    
    # Step 3: Process downloaded files
    print("\n🔧 Step 3: Processing downloaded audio files...")
    print("-" * 60)
    
    process_results = []
    
    for result in download_results["successful"][:5]:  # Process first 5 for demo
        call = result["call"]
        audio_path = result["audio_path"]
        
        print(f"\nProcessing {call['call_id']}...")
        
        try:
            # Process with enhanced pipeline
            process_result = await pipeline.process_call_complete(call)
            
            if process_result['success']:
                process_results.append(process_result)
                
                trans = process_result['transcription']
                print(f"  ✅ Processed successfully!")
                print(f"  • Speakers: {len(trans.get('utterances', []))} utterances")
                print(f"  • Script Compliance: {trans.get('script_compliance', {}).get('score', 0):.0f}%")
                print(f"  • Talk Ratio: Employee {trans.get('quality_metrics', {}).get('talk_ratio', {}).get('employee', 0):.0f}%, Customer {trans.get('quality_metrics', {}).get('talk_ratio', {}).get('customer', 0):.0f}%")
                
        except Exception as e:
            logger.error(f"  ❌ Processing error: {e}")
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 CLOUDFRONT DIRECT DOWNLOAD REPORT")
    print("=" * 80)
    
    download_rate = len(download_results["successful"]) / download_results["total"] * 100 if download_results["total"] > 0 else 0
    
    print(f"\n📥 DOWNLOAD RESULTS")
    print(f"  Total Attempts: {download_results['total']}")
    print(f"  Successful: {len(download_results['successful'])}")
    print(f"  Failed: {len(download_results['failed'])}")
    print(f"  Success Rate: {download_rate:.1f}%")
    print(f"  Download Time: {download_time:.1f}s")
    
    if download_rate == 100:
        print(f"\n  🎉 ACHIEVED 100% DOWNLOAD SUCCESS!")
    
    # List downloaded files
    print(f"\n📁 DOWNLOADED FILES")
    downloads_dir = Path("downloads")
    audio_files = list(downloads_dir.glob("*.mp3"))
    print(f"  Total files in downloads folder: {len(audio_files)}")
    
    for i, f in enumerate(sorted(audio_files)[-10:], 1):
        print(f"    {i}. {f.name} ({f.stat().st_size:,} bytes)")
    
    # Processing summary
    if process_results:
        print(f"\n🔧 PROCESSING SUMMARY")
        print(f"  Processed: {len(process_results)} calls")
        
        # Average metrics
        avg_compliance = sum(
            r['transcription'].get('script_compliance', {}).get('score', 0)
            for r in process_results
        ) / len(process_results)
        print(f"  Average Script Compliance: {avg_compliance:.0f}%")
    
    # Save report
    report_data = {
        'test_date': datetime.now().isoformat(),
        'download_results': download_results,
        'process_results': process_results,
        'statistics': {
            'download_rate': download_rate,
            'download_time': download_time,
            'processing_success': len(process_results)
        }
    }
    
    report_file = f"cloudfront_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n📄 Report saved to: {report_file}")
    
    # Cleanup
    await api_scraper.client.aclose()
    await downloader.close()
    
    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_cloudfront_downloads())