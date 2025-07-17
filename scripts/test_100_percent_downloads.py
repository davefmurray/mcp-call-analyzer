#!/usr/bin/env python3
"""
Achieve 100% Download Success Rate
Uses the proven API + signed URL approach
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import httpx
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from src.scrapers.scraper_api import DCAPIScraper
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RobustDownloader:
    """Robust downloader using API + direct download approach"""
    
    def __init__(self):
        self.api_scraper = DCAPIScraper()
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        self.auth_headers = None
        
    async def initialize(self) -> bool:
        """Initialize and authenticate"""
        logger.info("🔑 Authenticating with API...")
        
        auth_result = await self.api_scraper.authenticate()
        if auth_result:
            self.auth_headers = {
                'x-access-token': self.api_scraper.token,
                'Authorization': f'Bearer {self.api_scraper.token}'
            }
            logger.info("✅ Authentication successful")
            return True
        else:
            logger.error("❌ Authentication failed")
            return False
    
    async def download_audio_direct(self, call_data: Dict) -> Optional[str]:
        """Download audio using direct HTTP request with auth"""
        
        call_id = call_data['call_id']
        output_path = self.downloads_dir / f"{call_id}.mp3"
        
        # Skip if already exists
        if output_path.exists():
            logger.info(f"✅ Audio already exists: {output_path}")
            return str(output_path)
        
        try:
            # Get call details with recording URL
            call_details = await self.api_scraper.get_call_details(call_data['dc_call_id'])
            
            if not call_details or 'recordingUrl' not in call_details:
                logger.error(f"No recording URL for {call_id}")
                return None
            
            recording_url = call_details['recordingUrl']
            logger.info(f"📥 Downloading from: {recording_url[:80]}...")
            
            # Download with auth headers and retries
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                for attempt in range(3):
                    try:
                        response = await client.get(
                            recording_url,
                            headers=self.auth_headers
                        )
                        
                        if response.status_code == 200:
                            # Save audio file
                            with open(output_path, 'wb') as f:
                                f.write(response.content)
                            
                            file_size = len(response.content)
                            logger.info(f"✅ Downloaded {file_size:,} bytes to {output_path}")
                            return str(output_path)
                        else:
                            logger.warning(f"Attempt {attempt + 1} failed: {response.status_code}")
                            
                    except Exception as e:
                        logger.warning(f"Attempt {attempt + 1} error: {e}")
                        
                    if attempt < 2:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            logger.error(f"Failed to download after 3 attempts")
            return None
            
        except Exception as e:
            logger.error(f"Download error for {call_id}: {e}")
            return None
    
    async def download_batch(self, calls: List[Dict]) -> Dict:
        """Download multiple calls with high reliability"""
        
        results = {
            "successful": [],
            "failed": [],
            "total": len(calls)
        }
        
        # Process calls
        for i, call in enumerate(calls, 1):
            logger.info(f"\n[{i}/{len(calls)}] Processing {call['call_id']}...")
            
            audio_path = await self.download_audio_direct(call)
            
            if audio_path:
                results["successful"].append({
                    "call": call,
                    "audio_path": audio_path
                })
            else:
                results["failed"].append(call)
        
        return results


async def test_100_percent_downloads():
    """Test to achieve 100% download success"""
    
    print("🚀 100% DOWNLOAD SUCCESS TEST")
    print("=" * 80)
    print("Using proven API + direct download approach")
    print("=" * 80)
    
    # Initialize components
    pipeline = EnhancedHybridPipeline()
    downloader = RobustDownloader()
    
    # Initialize downloader
    if not await downloader.initialize():
        print("❌ Failed to initialize downloader")
        return
    
    # Step 1: Get recent calls
    print("\n📞 Step 1: Fetching recent calls...")
    calls = await pipeline.fetch_calls_batch(limit=25, days_back=30)
    
    if not calls:
        print("❌ No calls found!")
        return
    
    print(f"✅ Found {len(calls)} calls")
    
    # Step 2: Download audio files
    print("\n📥 Step 2: Downloading audio files...")
    print("-" * 60)
    
    start_time = datetime.now()
    download_results = await downloader.download_batch(calls[:25])
    download_time = (datetime.now() - start_time).total_seconds()
    
    # Step 3: Process downloaded files
    print("\n🔧 Step 3: Processing downloaded audio...")
    print("-" * 60)
    
    process_results = []
    
    for result in download_results["successful"]:
        call = result["call"]
        audio_path = result["audio_path"]
        
        print(f"\nProcessing {call['call_id']}...")
        
        try:
            # Process with enhanced pipeline
            process_result = await pipeline.process_call_complete(call)
            
            if process_result['success']:
                process_results.append(process_result)
                
                trans = process_result['transcription']
                print(f"  • Speakers: {len(trans.get('utterances', []))} utterances")
                print(f"  • Script Compliance: {trans.get('script_compliance', {}).get('score', 0):.0f}%")
                print(f"  • Talk Ratio: Employee {trans.get('quality_metrics', {}).get('talk_ratio', {}).get('employee', 0):.0f}%, Customer {trans.get('quality_metrics', {}).get('talk_ratio', {}).get('customer', 0):.0f}%")
                print(f"  • Outcome: {trans.get('sales_metrics', {}).get('outcome', 'unknown')}")
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("=" * 80)
    
    # Download statistics
    download_rate = len(download_results["successful"]) / download_results["total"] * 100
    
    print(f"\n📥 DOWNLOAD STATISTICS")
    print(f"  Total Attempts: {download_results['total']}")
    print(f"  Successful: {len(download_results['successful'])}")
    print(f"  Failed: {len(download_results['failed'])}")
    print(f"  Success Rate: {download_rate:.1f}%")
    print(f"  Download Time: {download_time:.1f}s ({download_time/download_results['total']:.1f}s per call)")
    
    if download_rate == 100:
        print(f"\n  🎉 ACHIEVED 100% DOWNLOAD SUCCESS!")
    
    # Processing statistics
    print(f"\n🔧 PROCESSING STATISTICS")
    print(f"  Processed: {len(process_results)}")
    print(f"  Success Rate: {len(process_results)/len(download_results['successful'])*100:.1f}%")
    
    # Enhanced features summary
    if process_results:
        print(f"\n✨ ENHANCED FEATURES SUMMARY")
        
        # Average script compliance
        avg_compliance = sum(
            r['transcription'].get('script_compliance', {}).get('score', 0)
            for r in process_results
        ) / len(process_results)
        print(f"  Average Script Compliance: {avg_compliance:.0f}%")
        
        # Talk ratios
        avg_employee_talk = sum(
            r['transcription'].get('quality_metrics', {}).get('talk_ratio', {}).get('employee', 0)
            for r in process_results
        ) / len(process_results)
        print(f"  Average Employee Talk Time: {avg_employee_talk:.0f}%")
        
        # Appointments scheduled
        appointments = sum(
            1 for r in process_results
            if r['transcription'].get('sales_metrics', {}).get('appointment_scheduled')
        )
        print(f"  Appointments Scheduled: {appointments}/{len(process_results)}")
    
    # Save detailed report
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
    
    report_file = f"test_report_100_percent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        import json
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_file}")
    
    print("\n" + "=" * 80)
    if download_rate == 100:
        print("🎉 SUCCESS! Achieved 100% download rate!")
        print(f"✅ Downloaded all {len(download_results['successful'])} audio files successfully")
        print(f"✅ Processed {len(process_results)} calls with enhanced features")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_100_percent_downloads())