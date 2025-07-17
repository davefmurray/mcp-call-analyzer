import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import httpx
import re

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class CallBatchProcessor:
    """Process multiple calls from Digital Concierge dashboard"""
    
    def __init__(self):
        self.audio_urls = {}
        self.processed_calls = []
        
    async def process_batch(self, max_calls=10):
        """Process a batch of calls with recordings"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Monitor network for audio URLs
            def on_response(response):
                url = response.url
                if '.mp3' in url and 'cloudfront' in url:
                    print(f"📡 Captured audio URL: {url[:80]}...")
                    self.audio_urls[url] = True
            
            page.on("response", on_response)
            
            # Login
            print("🔐 Logging in...")
            await page.goto(os.getenv("DASHBOARD_URL"))
            await page.wait_for_timeout(2000)
            
            await page.fill('input[placeholder="User Name"]', os.getenv("DASHBOARD_USERNAME"))
            await page.fill('input[placeholder="Password"]', os.getenv("DASHBOARD_PASSWORD"))
            await page.click('button:has-text("Sign in")')
            await page.wait_for_timeout(3000)
            
            # Go to calls page
            print("📞 Navigating to calls page...")
            await page.goto("https://autoservice.digitalconcierge.io/userPortal/admin/calls")
            await page.wait_for_timeout(5000)
            
            # Get all rows
            all_rows = await page.query_selector_all('.ag-center-cols-container .ag-row')
            print(f"📊 Found {len(all_rows)} call rows")
            
            calls_processed = 0
            
            # Process each row
            for i in range(min(len(all_rows), max_calls)):
                if calls_processed >= max_calls:
                    break
                    
                print(f"\n{'='*50}")
                print(f"Processing row {i+1}/{min(len(all_rows), max_calls)}...")
                
                # Clear captured URLs for this call
                self.audio_urls.clear()
                
                # Click on the row
                await all_rows[i].click()
                await page.wait_for_timeout(2000)
                
                # Check if modal opened
                modal = await page.query_selector('.modal.show')
                if not modal:
                    print("❌ No modal opened, skipping...")
                    continue
                
                # Extract call details
                call_data = await self.extract_call_details(page)
                
                # Check if we captured an audio URL
                if self.audio_urls:
                    audio_url = list(self.audio_urls.keys())[0]
                    call_data['audio_url'] = audio_url
                    
                    # Download and upload audio
                    success = await self.process_audio(call_data)
                    
                    if success:
                        calls_processed += 1
                        self.processed_calls.append(call_data)
                        print(f"✅ Successfully processed call {call_data['call_id']}")
                else:
                    print("❌ No audio URL captured")
                
                # Close modal
                close_btn = await page.query_selector('button[aria-label="Close"], .modal-header button.close')
                if close_btn:
                    await close_btn.click()
                    await page.wait_for_timeout(1000)
            
            await browser.close()
            
            # Summary
            print(f"\n\n{'='*50}")
            print(f"📊 BATCH PROCESSING COMPLETE")
            print(f"✅ Processed {calls_processed} calls with recordings")
            print(f"📁 Audio files saved to: downloads/")
            print(f"☁️  Uploaded to Supabase storage")
            
            return self.processed_calls
    
    async def extract_call_details(self, page):
        """Extract call details from the modal"""
        
        # Generate unique call ID
        call_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.processed_calls)}"
        
        # Try to extract details from modal
        details = {
            'call_id': call_id,
            'customer_name': 'Unknown',
            'customer_number': '',
            'advisor': '',
            'duration': 0,
            'direction': 'inbound',
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract text from modal
        try:
            modal_text = await page.text_content('.modal-body')
            if modal_text:
                # Extract phone number
                phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', modal_text)
                if phone_match:
                    details['customer_number'] = f"+1{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
                
                # Extract name (look for capitalized words)
                name_match = re.search(r'([A-Z][A-Z\s]+[A-Z])', modal_text)
                if name_match:
                    details['customer_name'] = name_match.group(1).strip()
                
                # Extract duration
                duration_match = re.search(r'(\d{2}):(\d{2}):(\d{2})', modal_text)
                if duration_match:
                    details['duration'] = int(duration_match.group(1)) * 3600 + \
                                         int(duration_match.group(2)) * 60 + \
                                         int(duration_match.group(3))
        except:
            pass
        
        return details
    
    async def process_audio(self, call_data):
        """Download audio and upload to Supabase"""
        
        call_id = call_data['call_id']
        audio_url = call_data['audio_url']
        
        print(f"\n📥 Downloading audio for {call_id}...")
        
        try:
            # Download audio
            async with httpx.AsyncClient() as client:
                response = await client.get(audio_url, follow_redirects=True, timeout=30.0)
                
                if response.status_code == 200:
                    # Save locally
                    os.makedirs("downloads", exist_ok=True)
                    audio_path = f"downloads/{call_id}.mp3"
                    
                    with open(audio_path, "wb") as f:
                        f.write(response.content)
                    
                    file_size = len(response.content)
                    print(f"✅ Downloaded: {audio_path} ({file_size:,} bytes)")
                    
                    # Upload to Supabase
                    storage_path = f"{call_id}.mp3"
                    
                    with open(audio_path, "rb") as f:
                        result = supabase.storage.from_("call-recordings").upload(
                            storage_path,
                            f.read(),
                            {"content-type": "audio/mpeg"}
                        )
                    
                    public_url = supabase.storage.from_("call-recordings").get_public_url(storage_path)
                    print(f"☁️  Uploaded to: {public_url}")
                    
                    # Insert/update call record
                    call_record = {
                        'call_id': call_id,
                        'dc_call_id': call_id,
                        'customer_name': call_data['customer_name'],
                        'customer_number': call_data['customer_number'],
                        'call_direction': call_data['direction'],
                        'duration_seconds': call_data['duration'],
                        'date_created': call_data['timestamp'],
                        'has_recording': True,
                        'storage_url': public_url,
                        'audio_url': audio_url,
                        'status': 'downloaded'
                    }
                    
                    result = supabase.table('calls').upsert(call_record, on_conflict='call_id').execute()
                    
                    return True
                else:
                    print(f"❌ Download failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error processing audio: {e}")
            return False

async def main():
    """Run batch processor"""
    processor = CallBatchProcessor()
    
    # Process first 5 calls
    results = await processor.process_batch(max_calls=5)
    
    print(f"\n\n📋 PROCESSED CALLS:")
    for call in results:
        print(f"- {call['call_id']}: {call['customer_name']} ({call['customer_number']})")

if __name__ == "__main__":
    asyncio.run(main())