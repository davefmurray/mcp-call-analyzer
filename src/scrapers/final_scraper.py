import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import re

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

async def scrape_and_download_calls():
    """Final scraper that properly handles the dashboard"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Monitor network requests for audio URLs
        audio_urls = {}
        def on_response(response):
            if '.mp3' in response.url or 'audio' in response.url:
                print(f"Found audio URL: {response.url}")
                audio_urls[response.url] = True
        
        page.on("response", on_response)
        
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
        
        # Find all rows in the AG-Grid
        rows = await page.query_selector_all('.ag-center-cols-container .ag-row')
        print(f"Found {len(rows)} call rows")
        
        calls_processed = 0
        
        for i, row in enumerate(rows[:10]):  # Process first 10
            # Get all cells in the row
            cells = await row.query_selector_all('.ag-cell')
            
            # Extract cell texts
            cell_texts = []
            for cell in cells:
                text = await cell.text_content()
                cell_texts.append(text.strip() if text else '')
            
            if len(cell_texts) < 7:
                continue
            
            # Check if this row has a recording (look in tags column - usually index 6)
            tags_text = cell_texts[6] if len(cell_texts) > 6 else ''
            has_recording = '🎙' in tags_text or '\U0001F399' in tags_text
            
            # Debug: print all cells to understand structure
            if i < 5:  # Print first 5 rows
                print(f"\nRow {i+1} cells:")
                for j, text in enumerate(cell_texts):
                    print(f"  Cell {j}: {text!r}")
            
            if not has_recording:
                continue
            
            print(f"\n--- Processing row {i+1} with recording ---")
            print(f"Name: {cell_texts[2]}")
            print(f"Tags: {tags_text}")
            
            # Click on the row
            await row.click()
            await page.wait_for_timeout(2000)
            
            # Try different ways to find the audio
            # 1. Check if a modal opened
            modal = await page.query_selector('.modal-content, [role="dialog"], .MuiDialog-root')
            if modal:
                print("Modal opened")
                
                # Look for audio player or download button
                audio_player = await modal.query_selector('audio')
                if audio_player:
                    src = await audio_player.get_attribute('src')
                    print(f"Found audio src in modal: {src}")
                
                download_btn = await modal.query_selector('a[href*="download"], button:has-text("Download")')
                if download_btn:
                    href = await download_btn.get_attribute('href')
                    print(f"Found download button: {href}")
                
                # Close modal
                close_btn = await modal.query_selector('[aria-label="Close"], button:has-text("Close"), .close')
                if close_btn:
                    await close_btn.click()
                    await page.wait_for_timeout(500)
            
            # 2. Check if URL changed (detail view)
            current_url = page.url
            if '/calls/' in current_url and current_url != "https://autoservice.digitalconcierge.io/userPortal/admin/calls":
                print(f"Navigated to detail page: {current_url}")
                
                # Extract call ID from URL
                call_id_match = re.search(r'/calls/([a-f0-9]+)', current_url)
                call_id = call_id_match.group(1) if call_id_match else f"unknown_{i}"
                
                # Look for audio on the detail page
                audio_elements = await page.query_selector_all('audio, a[href*=".mp3"], button:has-text("Download")')
                for elem in audio_elements:
                    if await elem.evaluate('el => el.tagName') == 'AUDIO':
                        src = await elem.get_attribute('src')
                        if src:
                            print(f"Found audio src: {src}")
                            audio_urls[src] = True
                
                # Go back to list
                await page.go_back()
                await page.wait_for_timeout(2000)
            else:
                # Generate a call ID from row data
                call_id = f"call_{datetime.now().strftime('%Y%m%d')}_{i}"
            
            # Insert call into Supabase
            try:
                call_record = {
                    'call_id': call_id,
                    'dc_call_id': call_id,
                    'customer_name': cell_texts[2] if len(cell_texts) > 2 else '',
                    'customer_number': cell_texts[3] if len(cell_texts) > 3 else '',
                    'call_direction': 'inbound' if 'In' in cell_texts[1] else 'outbound',
                    'duration_seconds': parse_duration(cell_texts[5] if len(cell_texts) > 5 else '0'),
                    'date_created': datetime.now().isoformat(),
                    'has_recording': True,
                    'dc_sentiment': parse_sentiment(cell_texts[7] if len(cell_texts) > 7 else ''),
                    'status': 'scraped'
                }
                
                result = supabase.table('calls').upsert(call_record, on_conflict='call_id').execute()
                print(f"✅ Upserted call {call_id}")
                calls_processed += 1
                
            except Exception as e:
                print(f"❌ Error inserting call: {e}")
        
        print(f"\n\n✅ Processed {calls_processed} calls with recordings")
        print(f"Found {len(audio_urls)} audio URLs:")
        for url in list(audio_urls.keys())[:5]:
            print(f"  - {url}")
        
        print("\n\nKeeping browser open for 10 seconds...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

def parse_duration(duration_str):
    """Convert duration string to seconds"""
    if not duration_str:
        return 0
    try:
        parts = duration_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            return int(duration_str)
    except:
        return 0

def parse_sentiment(sentiment_str):
    """Parse sentiment string to numeric value"""
    if not sentiment_str:
        return 0.0
    sentiment_str = sentiment_str.lower()
    if 'positive' in sentiment_str:
        return 0.8
    elif 'negative' in sentiment_str:
        return -0.8
    else:
        return 0.0

if __name__ == "__main__":
    asyncio.run(scrape_and_download_calls())