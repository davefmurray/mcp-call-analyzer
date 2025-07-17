#!/usr/bin/env python3
"""
Browser Download with Selenium
Download audio files from Digital Concierge User Portal
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from src.scrapers.scraper_api import DCAPIScraper
from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BrowserDownloader:
    """Download audio files using Selenium browser automation"""
    
    def __init__(self):
        self.base_url = "https://autoservice.digitalconcierge.io/"
        self.username = os.getenv("DASHBOARD_USERNAME", "dev")
        self.password = os.getenv("DASHBOARD_PASSWORD", "DFMdev12")
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with download preferences"""
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": str(self.downloads_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        # Add headless option for server environments
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Chrome driver initialized")
        
    def login(self):
        """Login to Digital Concierge"""
        logger.info("🔐 Logging in to Digital Concierge...")
        
        # Navigate to login page
        self.driver.get(self.base_url)
        time.sleep(2)
        
        # Check if redirected to app.digitalconcierge.io
        current_url = self.driver.current_url
        logger.info(f"Current URL: {current_url}")
        
        try:
            # Find and fill username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Find and fill password
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            logger.info("✅ Login successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False
    
    def download_call_audio(self, dc_call_id: str, call_sid: str) -> Optional[str]:
        """Download audio for a specific call"""
        
        logger.info(f"\n📥 Downloading audio for {call_sid}")
        
        # Navigate to call review page
        review_url = f"{self.base_url}userPortal/calls/review?callId={dc_call_id}"
        logger.info(f"   Navigating to: {review_url}")
        
        self.driver.get(review_url)
        time.sleep(3)
        
        try:
            # Wait for page to load and find the call row
            # The exact selector will depend on the page structure
            call_row = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "tr[data-call-id], .call-row, tbody tr"))
            )
            
            logger.info("   Clicking on call row...")
            call_row.click()
            time.sleep(2)
            
            # Wait for modal to appear
            modal = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".modal, .dialog, [role='dialog']"))
            )
            
            # Find and click download button
            download_button = modal.find_element(By.CSS_SELECTOR, 
                "button[download], a[download], .download-btn, [title*='Download']")
            
            logger.info("   Clicking download button...")
            download_button.click()
            
            # Wait for download to complete
            time.sleep(5)
            
            # Check if file was downloaded
            expected_file = self.downloads_dir / f"{call_sid}.mp3"
            if expected_file.exists():
                logger.info(f"   ✅ Downloaded: {expected_file}")
                return str(expected_file)
            else:
                # Check for any new mp3 files
                mp3_files = list(self.downloads_dir.glob("*.mp3"))
                if mp3_files:
                    latest_file = max(mp3_files, key=os.path.getctime)
                    # Rename to correct name
                    new_path = self.downloads_dir / f"{call_sid}.mp3"
                    latest_file.rename(new_path)
                    logger.info(f"   ✅ Downloaded and renamed: {new_path}")
                    return str(new_path)
                    
        except Exception as e:
            logger.error(f"   ❌ Download failed: {e}")
            
        return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("✅ Browser closed")


async def test_browser_downloads():
    """Test browser automation downloads"""
    
    print("🚀 BROWSER AUTOMATION DOWNLOAD TEST")
    print("=" * 80)
    print("Using Selenium to download from User Portal")
    print("=" * 80)
    
    # Initialize components
    api_scraper = DCAPIScraper()
    downloader = BrowserDownloader()
    pipeline = EnhancedHybridPipeline()
    
    # Setup browser
    downloader.setup_driver()
    
    # Login
    if not downloader.login():
        print("❌ Login failed!")
        downloader.close()
        return
    
    # Get calls from API
    print("\n📞 Getting call data from API...")
    await api_scraper.authenticate()
    calls = await api_scraper.get_calls(limit=25, days_back=30)
    
    # Filter calls with recordings
    calls_with_recordings = []
    for call in calls:
        if call.get('RecordingSid'):
            calls_with_recordings.append({
                'call_id': call.get('CallSid'),
                'dc_call_id': call.get('_id'),
                'customer_name': call.get('name', 'Unknown'),
                'recording_sid': call.get('RecordingSid')
            })
    
    print(f"✅ Found {len(calls_with_recordings)} calls with recordings")
    
    # Download audio files
    print("\n📥 Downloading audio files...")
    print("-" * 60)
    
    download_results = []
    
    for i, call in enumerate(calls_with_recordings[:5], 1):  # Test with first 5
        print(f"\n[{i}/5] Processing {call['call_id']}")
        print(f"    Customer: {call['customer_name']}")
        
        audio_path = downloader.download_call_audio(call['dc_call_id'], call['call_id'])
        
        if audio_path:
            download_results.append({
                'call': call,
                'audio_path': audio_path,
                'status': 'success'
            })
        else:
            download_results.append({
                'call': call,
                'status': 'failed'
            })
    
    # Close browser
    downloader.close()
    
    # Process downloaded files
    print("\n🔧 Processing downloaded files...")
    print("-" * 60)
    
    successful_downloads = [r for r in download_results if r['status'] == 'success']
    
    for result in successful_downloads:
        call_data = result['call']
        audio_path = result['audio_path']
        
        print(f"\nProcessing {call_data['call_id']}...")
        
        try:
            # Add audio path to call data
            call_data['audio_file'] = audio_path
            
            # Process with enhanced pipeline
            process_result = await pipeline.process_call_complete(call_data)
            
            if process_result['success']:
                trans = process_result['transcription']
                print(f"  ✅ Processed successfully!")
                print(f"  • Speakers: {len(trans.get('utterances', []))} utterances")
                print(f"  • Script Compliance: {trans.get('script_compliance', {}).get('score', 0):.0f}%")
                
        except Exception as e:
            logger.error(f"  ❌ Processing error: {e}")
    
    # Final report
    print("\n" + "=" * 80)
    print("📊 BROWSER DOWNLOAD REPORT")
    print("=" * 80)
    
    success_count = len([r for r in download_results if r['status'] == 'success'])
    total_count = len(download_results)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\n📥 DOWNLOAD RESULTS")
    print(f"  Total Attempts: {total_count}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {total_count - success_count}")
    print(f"  Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print(f"\n  🎉 ACHIEVED 100% DOWNLOAD SUCCESS!")
    
    # Cleanup
    await api_scraper.client.aclose()
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    # Check if Selenium is installed
    try:
        import selenium
        print(f"✅ Selenium version: {selenium.__version__}")
    except ImportError:
        print("❌ Selenium not installed. Run: pip install selenium")
        sys.exit(1)
    
    asyncio.run(test_browser_downloads())