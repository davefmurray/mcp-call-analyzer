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

async def download_and_process_call():
    """Download audio for one call and process it through the pipeline"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track audio URLs and network requests
        audio_urls = {}
        def on_response(response):
            url = response.url
            if any(x in url.lower() for x in ['.mp3', 'audio', 'recording', 'cloudfront']):
                print(f"Found potential audio URL: {url[:100]}...")
                if '.mp3' in url:
                    audio_urls[url] = True
        
        def on_request(request):
            url = request.url
            if 'recording' in url.lower() or '.mp3' in url.lower():
                print(f"Audio request: {url[:100]}...")
        
        page.on("response", on_response)
        page.on("request", on_request)
        
        # Login
        print("Logging in...")
        await page.goto(os.getenv("DASHBOARD_URL"))
        await page.wait_for_timeout(2000)
        
        await page.fill('input[placeholder="User Name"]', os.getenv("DASHBOARD_USERNAME"))
        await page.fill('input[placeholder="Password"]', os.getenv("DASHBOARD_PASSWORD"))
        await page.click('button:has-text("Sign in")')
        await page.wait_for_timeout(3000)
        
        # Go to calls page
        print("Going to calls page...")
        await page.goto("https://autoservice.digitalconcierge.io/userPortal/admin/calls")
        await page.wait_for_timeout(5000)
        
        # Find a row with recording (based on screenshot, first row has recording)
        print("\nLooking for rows with recordings...")
        all_rows = await page.query_selector_all('.ag-center-cols-container .ag-row')
        
        if not all_rows:
            print("No rows found!")
            return
        
        # Click on first row (JACKSON) which has a recording
        print("Clicking on first row (JACKSON)...")
        await all_rows[0].click()
        await page.wait_for_timeout(3000)
        
        # Wait for modal to appear
        modal = await page.wait_for_selector('.modal.show', timeout=5000)
        print("Modal opened!")
        
        # Extract call details from modal
        # Based on screenshot, the name is in the "Caller Information" section
        caller_info_elements = await page.query_selector_all('.modal-body div')
        caller_name = "Unknown"
        phone_number = ""
        
        # Look for the name and phone in the modal
        for elem in caller_info_elements:
            text = await elem.text_content()
            if text:
                # Look for name pattern (e.g., "JANET GOMEZ")
                if text.strip() and not any(x in text for x in ['Caller Information', 'Advisor', 'Shop Number', 'Tags']):
                    name_match = re.match(r'^[A-Z][A-Z\s]+[A-Z]$', text.strip())
                    if name_match:
                        caller_name = text.strip()
                # Look for phone pattern
                phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', text)
                if phone_match:
                    phone_number = f"+1{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
        
        print(f"Caller: {caller_name}")
        print(f"Phone: {phone_number}")
        
        # Wait a bit for any audio to load
        await page.wait_for_timeout(2000)
        
        # Get the audio URL from our tracking
        if audio_urls:
            audio_url = list(audio_urls.keys())[0]
            print(f"\nAudio URL captured: {audio_url}")
            
            # Generate call ID
            call_id = f"call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Download the audio file
            print(f"\nDownloading audio for call {call_id}...")
            async with httpx.AsyncClient() as client:
                response = await client.get(audio_url, follow_redirects=True)
                
                if response.status_code == 200:
                    # Save locally
                    audio_path = f"downloads/{call_id}.mp3"
                    os.makedirs("downloads", exist_ok=True)
                    
                    with open(audio_path, "wb") as f:
                        f.write(response.content)
                    
                    print(f"✅ Audio downloaded: {audio_path}")
                    
                    # Upload to Supabase storage
                    print("\nUploading to Supabase storage...")
                    with open(audio_path, "rb") as f:
                        storage_path = f"recordings/{call_id}.mp3"
                        result = supabase.storage.from_("audio-recordings").upload(
                            storage_path,
                            f.read(),
                            {"content-type": "audio/mpeg"}
                        )
                        
                        if result:
                            storage_url = supabase.storage.from_("audio-recordings").get_public_url(storage_path)
                            print(f"✅ Uploaded to Supabase: {storage_url}")
                            
                            # Insert call record
                            call_record = {
                                'call_id': call_id,
                                'dc_call_id': call_id,
                                'customer_name': caller_name.strip(),
                                'customer_number': phone_number,
                                'call_direction': 'inbound',
                                'date_created': datetime.now().isoformat(),
                                'has_recording': True,
                                'storage_url': storage_url,
                                'status': 'downloaded'
                            }
                            
                            result = supabase.table('calls').upsert(call_record, on_conflict='call_id').execute()
                            print(f"✅ Call record inserted: {call_id}")
                            
                            # Now we're ready to transcribe!
                            print(f"\n✅ SUCCESS! Call {call_id} is ready for transcription")
                            print(f"   Audio file: {audio_path}")
                            print(f"   Storage URL: {storage_url}")
                            print("\nNext step: Run transcription with OpenAI Whisper")
                            
                else:
                    print(f"❌ Failed to download audio: {response.status_code}")
        else:
            print("❌ No audio URL captured")
        
        # Close modal
        close_btn = await page.query_selector('button[aria-label="Close"], .modal-header button.close')
        if close_btn:
            await close_btn.click()
        
        await page.wait_for_timeout(2000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_and_process_call())