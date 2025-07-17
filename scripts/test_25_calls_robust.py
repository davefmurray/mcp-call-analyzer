#!/usr/bin/env python3
"""
Robust Test: Process 25+ Calls with 100% Download Success
Includes retry logic, progress tracking, and comprehensive reporting
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from src.scrapers.mcp_browser_scraper import MCPBrowserScraper
from dotenv import load_dotenv

load_dotenv()


class RobustCallProcessor:
    """Robust call processor with retry logic and progress tracking"""
    
    def __init__(self):
        self.pipeline = EnhancedHybridPipeline()
        self.browser_scraper = MCPBrowserScraper()
        self.results = []
        self.download_success = 0
        self.download_failures = 0
        self.processing_success = 0
        self.processing_failures = 0
        self.start_time = None
        self.failed_downloads = []
        
    async def process_calls_with_retry(self, target_count: int = 25, days_back: int = 30):
        """Process calls with retry logic for failed downloads"""
        
        self.start_time = datetime.now()
        
        print("🚀 ROBUST 25+ CALL TEST")
        print("=" * 80)
        print(f"Target: {target_count} calls")
        print(f"Goal: 100% download success")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Step 1: Fetch calls
        print("\n📞 STEP 1: Fetching calls...")
        calls = await self.pipeline.fetch_calls_batch(limit=target_count * 2, days_back=days_back)
        
        if not calls:
            print("❌ No calls found!")
            return
        
        print(f"✅ Found {len(calls)} calls")
        
        # Take the target number of calls
        calls_to_process = calls[:target_count]
        print(f"🎯 Processing {len(calls_to_process)} calls")
        
        # Step 2: Download audio with retry logic
        print("\n📥 STEP 2: Downloading audio files...")
        print("-" * 60)
        
        for i, call in enumerate(calls_to_process, 1):
            success = await self.download_with_retry(call, i, len(calls_to_process))
            
            if not success:
                self.failed_downloads.append(call)
        
        # Step 3: Retry failed downloads with browser automation
        if self.failed_downloads:
            print(f"\n🔄 STEP 3: Retrying {len(self.failed_downloads)} failed downloads...")
            print("-" * 60)
            
            # Login to dashboard once
            await self.browser_scraper.login_to_dashboard()
            
            for i, call in enumerate(self.failed_downloads, 1):
                print(f"\n[{i}/{len(self.failed_downloads)}] Retrying {call['call_id']}...")
                
                audio_path = await self.browser_scraper.download_audio_for_call(call)
                
                if audio_path and os.path.exists(audio_path):
                    self.download_success += 1
                    print(f"✅ Browser download successful: {audio_path}")
                else:
                    self.download_failures += 1
                    print(f"❌ Browser download failed")
        
        # Step 4: Process all downloaded audio files
        print(f"\n🎯 STEP 4: Processing {self.download_success} audio files...")
        print("-" * 60)
        
        processed_count = 0
        for i, call in enumerate(calls_to_process, 1):
            audio_path = f"downloads/{call['call_id']}.mp3"
            
            if os.path.exists(audio_path):
                processed_count += 1
                print(f"\n[{processed_count}/{self.download_success}] Processing {call['call_id']}...")
                
                # Process with enhanced features
                result = await self.process_call_enhanced(call, audio_path)
                self.results.append(result)
                
                # Show quick summary
                if result['success']:
                    self.processing_success += 1
                    self.display_quick_summary(result)
                else:
                    self.processing_failures += 1
                    print(f"❌ Processing failed: {result.get('error', 'Unknown')}")
        
        # Step 5: Generate comprehensive report
        await self.generate_report()
    
    async def download_with_retry(self, call: Dict, index: int, total: int, max_retries: int = 3) -> bool:
        """Download audio with retry logic"""
        
        call_id = call['call_id']
        audio_path = f"downloads/{call_id}.mp3"
        
        # Check if already downloaded
        if os.path.exists(audio_path):
            print(f"[{index}/{total}] ✅ Already downloaded: {call_id}")
            self.download_success += 1
            return True
        
        print(f"\n[{index}/{total}] Downloading {call_id}...")
        
        # Try standard download first
        for attempt in range(max_retries):
            try:
                result_path = await self.pipeline.download_call_audio_mcp(call)
                
                if result_path and os.path.exists(result_path):
                    self.download_success += 1
                    print(f"✅ Download successful (attempt {attempt + 1})")
                    return True
                
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        print(f"❌ Download failed after {max_retries} attempts")
        return False
    
    async def process_call_enhanced(self, call: Dict, audio_path: str) -> Dict:
        """Process call with enhanced features"""
        
        try:
            # Enhanced transcription
            transcription = await self.pipeline.transcribe_audio(audio_path, call)
            
            if not transcription.get('success'):
                return {
                    'success': False,
                    'call_id': call['call_id'],
                    'error': 'Transcription failed'
                }
            
            # Analysis
            analysis = await self.pipeline.analyze_call(
                transcription['transcript'],
                call,
                transcription
            )
            
            return {
                'success': True,
                'call_id': call['call_id'],
                'call_info': call,
                'transcription': transcription,
                'analysis': analysis
            }
            
        except Exception as e:
            return {
                'success': False,
                'call_id': call['call_id'],
                'error': str(e)
            }
    
    def display_quick_summary(self, result: Dict):
        """Display quick summary of processed call"""
        
        trans = result['transcription']
        
        # Basic info
        print(f"  Customer: {result['call_info'].get('customer_name', 'Unknown')}")
        print(f"  Duration: {result['call_info'].get('duration_seconds', 0)}s")
        
        # Quality metrics
        if 'quality_metrics' in trans:
            quality = trans['quality_metrics']
            print(f"  Talk Ratio: Employee {quality['talk_ratio'].get('employee', 0):.0f}%, Customer {quality['talk_ratio'].get('customer', 0):.0f}%")
        
        # Compliance
        if 'script_compliance' in trans:
            print(f"  Script Compliance: {trans['script_compliance']['score']:.0f}%")
        
        # Sales
        if 'sales_metrics' in trans:
            sales = trans['sales_metrics']
            print(f"  Outcome: {sales['outcome'].replace('_', ' ').title()}")
            if sales['appointment_scheduled']:
                print(f"  ✅ Appointment Scheduled")
    
    async def generate_report(self):
        """Generate comprehensive test report"""
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        # Download statistics
        total_attempts = self.download_success + self.download_failures
        download_rate = (self.download_success / total_attempts * 100) if total_attempts > 0 else 0
        
        print(f"\n📥 DOWNLOAD STATISTICS")
        print(f"  Total Attempts: {total_attempts}")
        print(f"  Successful: {self.download_success}")
        print(f"  Failed: {self.download_failures}")
        print(f"  Success Rate: {download_rate:.1f}%")
        
        if download_rate == 100:
            print(f"  🎉 ACHIEVED 100% DOWNLOAD SUCCESS!")
        
        # Processing statistics
        print(f"\n🔧 PROCESSING STATISTICS")
        print(f"  Processed: {self.processing_success + self.processing_failures}")
        print(f"  Successful: {self.processing_success}")
        print(f"  Failed: {self.processing_failures}")
        
        # Performance metrics
        print(f"\n⚡ PERFORMANCE METRICS")
        print(f"  Total Duration: {duration:.1f} seconds")
        print(f"  Average per Call: {duration / total_attempts:.1f} seconds")
        
        # Call insights
        if self.results:
            successful_results = [r for r in self.results if r['success']]
            
            if successful_results:
                print(f"\n📈 CALL INSIGHTS")
                
                # Script compliance
                avg_compliance = sum(
                    r['transcription'].get('script_compliance', {}).get('score', 0)
                    for r in successful_results
                ) / len(successful_results)
                print(f"  Average Script Compliance: {avg_compliance:.0f}%")
                
                # Appointments
                appointments = sum(
                    1 for r in successful_results
                    if r['transcription'].get('sales_metrics', {}).get('appointment_scheduled')
                )
                print(f"  Appointments Scheduled: {appointments}/{len(successful_results)}")
                
                # Call types
                outcomes = {}
                for r in successful_results:
                    outcome = r['transcription'].get('sales_metrics', {}).get('outcome', 'unknown')
                    outcomes[outcome] = outcomes.get(outcome, 0) + 1
                
                print(f"\n  Call Outcomes:")
                for outcome, count in outcomes.items():
                    print(f"    • {outcome.replace('_', ' ').title()}: {count}")
        
        # Save detailed results
        report_data = {
            'test_date': self.start_time.isoformat(),
            'duration_seconds': duration,
            'download_statistics': {
                'total_attempts': total_attempts,
                'successful': self.download_success,
                'failed': self.download_failures,
                'success_rate': download_rate
            },
            'processing_statistics': {
                'successful': self.processing_success,
                'failed': self.processing_failures
            },
            'results': self.results
        }
        
        report_file = f"test_report_25_calls_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Final summary
        print("\n" + "=" * 80)
        if download_rate == 100 and self.processing_success >= 25:
            print("🎉 TEST PASSED! 100% download success achieved!")
            print(f"✅ Successfully processed {self.processing_success} calls")
        else:
            print("⚠️ TEST INCOMPLETE")
            if download_rate < 100:
                print(f"  - Download success rate: {download_rate:.1f}% (target: 100%)")
            if self.processing_success < 25:
                print(f"  - Calls processed: {self.processing_success} (target: 25+)")
        print("=" * 80)


async def main():
    """Run the robust 25+ call test"""
    
    processor = RobustCallProcessor()
    await processor.process_calls_with_retry(target_count=25, days_back=30)


if __name__ == "__main__":
    asyncio.run(main())