"""Capture actual headers used by the DC dashboard"""

import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def capture_headers():
    """Capture the actual headers sent to the API"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        captured_headers = {}
        
        # Intercept requests to capture headers
        async def handle_request(request):
            if 'call/list' in request.url:
                captured_headers['call_list'] = dict(request.headers)
                print(f"\n🎯 Found call/list request!")
                print(f"URL: {request.url}")
                print(f"Method: {request.method}")
                print(f"Headers:")
                for key, value in request.headers.items():
                    if 'auth' in key.lower() or 'token' in key.lower() or key.lower() in ['authorization', 'cookie']:
                        print(f"  {key}: {value[:50]}...")
                    else:
                        print(f"  {key}: {value}")
                
                if request.post_data:
                    print(f"Body: {request.post_data}")
        
        page.on("request", handle_request)
        
        # Login
        print("🔐 Logging in...")
        await page.goto(os.getenv("DASHBOARD_URL"))
        await page.wait_for_timeout(2000)
        
        # Login
        await page.fill('input[placeholder="User Name"]', os.getenv("DASHBOARD_USERNAME"))
        await page.fill('input[placeholder="Password"]', os.getenv("DASHBOARD_PASSWORD"))
        await page.click('button:has-text("Sign in")')
        
        print("⏳ Waiting for login...")
        await page.wait_for_timeout(3000)
        
        # Navigate to calls page to trigger API call
        print("📞 Navigating to calls page...")
        await page.goto("https://autoservice.digitalconcierge.io/userPortal/admin/calls")
        
        # Wait for API calls
        await page.wait_for_timeout(5000)
        
        # Save captured headers
        if captured_headers:
            with open('captured_headers.json', 'w') as f:
                json.dump(captured_headers, f, indent=2)
            print(f"\n💾 Headers saved to captured_headers.json")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_headers())