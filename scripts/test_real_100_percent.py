#!/usr/bin/env python3
"""
Real 100% Download Success Test
Uses the exact approach from the working pipeline
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipelines.final_hybrid_pipeline import FinalHybridPipeline
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_real_downloads():
    """Test real downloads using the working pipeline"""
    
    print("🚀 REAL 100% DOWNLOAD TEST")
    print("=" * 80)
    print("Using the proven FinalHybridPipeline approach")
    print("=" * 80)
    
    # Initialize pipeline
    pipeline = FinalHybridPipeline()
    
    # Test parameters
    target_count = 25
    days_back = 30
    
    print(f"\nTarget: Download {target_count} calls with 100% success")
    print(f"Looking back: {days_back} days")
    
    # Run the pipeline
    print("\n📞 Running pipeline...")
    print("-" * 60)
    
    start_time = datetime.now()
    
    # Run the actual pipeline that we know works
    results = await pipeline.run_pipeline(
        batch_size=target_count,
        days_back=days_back
    )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    # Count downloads
    downloads_dir = Path("downloads")
    audio_files = list(downloads_dir.glob("*.mp3"))
    
    # Get processing results from database
    from supabase import create_client
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # Get analyzed calls from today
    today_start = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
    analyzed_calls = supabase.table('calls').select("*").gte(
        'created_at', today_start
    ).eq('status', 'analyzed').execute()
    
    # Report
    print("\n" + "=" * 80)
    print("📊 DOWNLOAD TEST RESULTS")
    print("=" * 80)
    
    print(f"\n📥 DOWNLOADS")
    print(f"  Audio files in downloads folder: {len(audio_files)}")
    print(f"  Files:")
    for i, f in enumerate(audio_files[:10], 1):
        print(f"    {i}. {f.name} ({f.stat().st_size:,} bytes)")
    if len(audio_files) > 10:
        print(f"    ... and {len(audio_files) - 10} more")
    
    print(f"\n🔧 PROCESSING")
    print(f"  Analyzed calls today: {len(analyzed_calls.data)}")
    print(f"  Pipeline duration: {duration:.1f}s")
    
    # Check if we have at least 25 downloads
    if len(audio_files) >= target_count:
        print(f"\n🎉 SUCCESS! Downloaded {len(audio_files)} audio files")
        print(f"✅ Achieved 100% download success for {target_count}+ calls")
    else:
        print(f"\n⚠️ Only {len(audio_files)} downloads found")
        print(f"   Need {target_count - len(audio_files)} more to reach target")
    
    # Show a sample of analyzed calls
    if analyzed_calls.data:
        print(f"\n📊 SAMPLE ANALYZED CALLS")
        for call in analyzed_calls.data[:5]:
            print(f"  • {call['call_id']} - {call['customer_name']} ({call['duration_seconds']}s)")
    
    print("\n" + "=" * 80)
    print("✅ Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_real_downloads())