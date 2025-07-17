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

async def find_recordings():
    """Find rows with recording icons"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Monitor network requests
        audio_urls = []
        def on_response(response):
            url = response.url
            if any(ext in url for ext in ['.mp3', '.wav', '.m4a', 'audio', 'recording']):
                print(f"Audio URL detected: {url}")
                audio_urls.append(url)
        
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
        
        # Look for recording icons in different ways
        print("\n1. Looking for recording icons as text...")
        recording_elements = await page.query_selector_all('text=🎙')
        print(f"   Found {len(recording_elements)} elements with recording icon text")
        
        print("\n2. Looking in cells containing recording icon...")
        cells_with_mic = await page.query_selector_all('.ag-cell:has-text("🎙")')
        print(f"   Found {len(cells_with_mic)} cells containing recording icon")
        
        print("\n3. Checking all cells in tags column...")
        # Tags column is usually the 7th column (index 6)
        tags_cells = await page.query_selector_all('.ag-center-cols-container .ag-row .ag-cell[col-id="tags"]')
        print(f"   Found {len(tags_cells)} tags cells")
        
        # If no col-id, try by position
        if len(tags_cells) == 0:
            all_rows = await page.query_selector_all('.ag-center-cols-container .ag-row')
            print(f"   Found {len(all_rows)} rows total")
            
            for i, row in enumerate(all_rows[:10]):
                cells = await row.query_selector_all('.ag-cell')
                if len(cells) > 6:
                    tags_cell = cells[6]
                    text = await tags_cell.text_content()
                    if text:
                        print(f"   Row {i+1} tags: {text!r}")
                        if '🎙' in text or 'recording' in text.lower():
                            print(f"      ✓ HAS RECORDING!")
        
        # Get actual visible content
        print("\n4. Extracting visible content from rows...")
        rows_data = await page.evaluate('''
            () => {
                const rows = document.querySelectorAll('.ag-center-cols-container .ag-row');
                return Array.from(rows).slice(0, 10).map((row, i) => {
                    const cells = row.querySelectorAll('.ag-cell');
                    const cellData = Array.from(cells).map(cell => {
                        return {
                            text: cell.textContent || '',
                            html: cell.innerHTML.substring(0, 200)
                        };
                    });
                    return {
                        rowIndex: i,
                        cells: cellData
                    };
                });
            }
        ''')
        
        # Print what we found
        for row in rows_data[:5]:
            print(f"\nRow {row['rowIndex'] + 1}:")
            for j, cell in enumerate(row['cells']):
                if j == 6:  # Tags column
                    print(f"  Tags cell HTML: {cell['html'][:100]}...")
                    print(f"  Tags cell text: {cell['text']!r}")
        
        # Click on first row with recording if found
        if cells_with_mic:
            print("\n5. Clicking on a row with recording...")
            parent_row = await cells_with_mic[0].query_selector('xpath=ancestor::div[@role="row"][1]')
            if parent_row:
                await parent_row.click()
                await page.wait_for_timeout(3000)
                
                # Check what happened
                current_url = page.url
                print(f"   Current URL: {current_url}")
                
                # Look for audio elements
                audio_elements = await page.query_selector_all('audio, video, iframe[src*="audio"], a[href*=".mp3"]')
                print(f"   Found {len(audio_elements)} media elements")
                
                for elem in audio_elements:
                    tag = await elem.evaluate('el => el.tagName')
                    if tag == 'AUDIO' or tag == 'VIDEO':
                        src = await elem.get_attribute('src')
                        print(f"   {tag} src: {src}")
        
        print(f"\n\nTotal audio URLs captured: {len(audio_urls)}")
        for url in audio_urls[:5]:
            print(f"  - {url}")
        
        print("\nKeeping browser open for 10 seconds...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_recordings())