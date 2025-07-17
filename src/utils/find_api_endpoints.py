import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def capture_api_calls():
    """Capture all API calls made by the dashboard"""
    api_calls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Intercept all requests
        async def handle_request(request):
            if 'api' in request.url or 'digitalconcierge' in request.url:
                api_calls.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data
                })
                print(f"{request.method} {request.url}")
        
        # Intercept responses too
        async def handle_response(response):
            if 'api' in response.url and 'call' in response.url:
                try:
                    body = await response.text()
                    print(f"\nResponse from {response.url}:")
                    # Parse and pretty print if JSON
                    try:
                        data = json.loads(body)
                        print(json.dumps(data, indent=2)[:500] + "...")
                    except:
                        print(body[:500] + "...")
                except:
                    pass
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # Login
        await page.goto(os.getenv("DASHBOARD_URL"))
        await page.wait_for_timeout(2000)
        
        print("=== Logging in ===")
        await page.fill('input[placeholder="User Name"]', os.getenv("DASHBOARD_USERNAME"))
        await page.fill('input[placeholder="Password"]', os.getenv("DASHBOARD_PASSWORD"))
        await page.click('button:has-text("Sign in")')
        await page.wait_for_timeout(3000)
        
        print("\n=== Navigating to calls ===")
        await page.goto("https://autoservice.digitalconcierge.io/userPortal/admin/calls")
        await page.wait_for_timeout(3000)
        
        print("\n=== Clicking on a call with recording ===")
        # Click on a row that has recording icon
        recording_rows = await page.query_selector_all('tr:has(td:has-text("🎙"))')
        if recording_rows:
            # Get the first row with recording
            first_row = recording_rows[0]
            
            # Get the call ID from the row
            call_id_cell = await first_row.query_selector('td:nth-child(1)')
            if call_id_cell:
                call_id_text = await call_id_cell.text_content()
                print(f"Clicking on call: {call_id_text}")
            
            # Click the row
            await first_row.click()
            await page.wait_for_timeout(3000)
            
            # Look for any modals or popups
            modals = await page.query_selector_all('.modal, [role="dialog"], .popup')
            print(f"Found {len(modals)} modals/popups")
            
            # Try clicking the recording icon directly
            recording_icon = await first_row.query_selector('td:has-text("🎙")')
            if recording_icon:
                print("\nClicking recording icon directly...")
                await recording_icon.click()
                await page.wait_for_timeout(3000)
            
            # Check for audio player
            audio_players = await page.query_selector_all('audio, .audio-player, [class*="player"]')
            print(f"Found {len(audio_players)} audio players")
        
        print("\n=== All API endpoints captured ===")
        unique_endpoints = {}
        for call in api_calls:
            endpoint = f"{call['method']} {call['url'].split('?')[0]}"
            if endpoint not in unique_endpoints:
                unique_endpoints[endpoint] = call
        
        for endpoint, call in unique_endpoints.items():
            print(f"\n{endpoint}")
            if call['post_data']:
                print(f"  POST data: {call['post_data']}")
        
        # Save to file
        with open('api_endpoints.json', 'w') as f:
            json.dump(list(unique_endpoints.values()), f, indent=2)
        
        print("\n\nPress Enter to close browser...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_api_calls())