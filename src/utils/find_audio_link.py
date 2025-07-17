import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

async def find_audio_for_call(call_id: str):
    """Find and extract audio download link for a specific call"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser for debugging
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"Looking for call ID: {call_id}")
        
        # Navigate and login
        await page.goto(os.getenv("DASHBOARD_URL"))
        await page.wait_for_timeout(2000)
        
        # Login
        print("Logging in...")
        await page.fill('input[placeholder="User Name"]', os.getenv("DASHBOARD_USERNAME"))
        await page.fill('input[placeholder="Password"]', os.getenv("DASHBOARD_PASSWORD"))
        await page.click('button:has-text("Sign in")')
        await page.wait_for_timeout(3000)
        
        # Go to calls page
        print("Navigating to calls...")
        await page.goto("https://autoservice.digitalconcierge.io/userPortal/admin/calls")
        await page.wait_for_timeout(3000)
        
        # Search for the specific call ID
        print(f"Searching for call {call_id}...")
        search_input = await page.query_selector('input[placeholder="Search"]')
        if search_input:
            await search_input.fill(call_id)
            # Press Enter to search
            await search_input.press('Enter')
            await page.wait_for_timeout(2000)
        
        # Look for the recording icon or download button
        print("Looking for recording/download options...")
        
        # Try clicking the recording icon
        recording_icons = await page.query_selector_all('td:has-text("🎙")')
        if recording_icons:
            print(f"Found {len(recording_icons)} recording icons")
            # Click the first one
            await recording_icons[0].click()
            await page.wait_for_timeout(2000)
            
            # Look for download button/link in modal or new content
            download_selectors = [
                'a[href*=".mp3"]',
                'a[href*="download"]',
                'button:has-text("Download")',
                'a:has-text("Download")',
                '[download]',
                'audio source',
                'audio'
            ]
            
            for selector in download_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"Found {len(elements)} elements matching '{selector}'")
                    for el in elements[:3]:
                        if selector == 'audio':
                            src = await el.get_attribute('src')
                            print(f"  Audio src: {src}")
                        elif selector == 'audio source':
                            src = await el.get_attribute('src')
                            print(f"  Audio source src: {src}")
                        else:
                            href = await el.get_attribute('href')
                            text = await el.text_content()
                            print(f"  {text}: {href}")
        
        # Check page source for any MP3 URLs
        content = await page.content()
        import re
        mp3_urls = re.findall(r'https?://[^\s<>"]+\.mp3', content)
        if mp3_urls:
            print(f"\nFound MP3 URLs in page source:")
            for url in mp3_urls:
                print(f"  - {url}")
        
        # Check for API calls in network
        print("\nChecking network requests...")
        
        await page.wait_for_timeout(5000)
        
        print("\nPress Enter to close browser...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    # Use a call ID we know has a recording
    call_id = "687641b0d84270fd72808ef2"  # RENEE NENSTIL call
    asyncio.run(find_audio_for_call(call_id))