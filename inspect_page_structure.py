import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

async def inspect_page():
    """Inspect the page structure to understand how calls are displayed"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        
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
        
        # Inspect page structure
        print("\nInspecting page structure...")
        
        structure = await page.evaluate('''
            () => {
                // Find all elements that might contain call data
                const selectors = [
                    'table',
                    'tbody',
                    'tr',
                    '[role="row"]',
                    '[role="table"]',
                    '[class*="table"]',
                    '[class*="grid"]',
                    '[class*="list"]',
                    '[class*="call"]',
                    '.MuiDataGrid-root',
                    '.MuiTable-root',
                    '.rt-table',
                    '[data-testid*="table"]',
                    '[data-testid*="call"]'
                ];
                
                const results = {};
                
                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        results[selector] = {
                            count: elements.length,
                            firstClass: elements[0].className,
                            firstTag: elements[0].tagName,
                            sample: elements[0].outerHTML.substring(0, 200)
                        };
                    }
                });
                
                // Look for any text that looks like phone numbers
                const phonePattern = /\+1\d{10}|\d{3}-\d{3}-\d{4}|\(\d{3}\)\s?\d{3}-\d{4}/g;
                const allText = document.body.innerText;
                const phones = allText.match(phonePattern) || [];
                
                // Look for recording icons
                const recordingIcons = document.body.innerText.match(/🎙/g) || [];
                
                return {
                    selectors: results,
                    phoneNumbers: phones.slice(0, 5),
                    recordingIconCount: recordingIcons.length,
                    pageTitle: document.title,
                    url: window.location.href
                };
            }
        ''')
        
        print(f"\nPage URL: {structure['url']}")
        print(f"Page Title: {structure['pageTitle']}")
        print(f"Recording icons found: {structure['recordingIconCount']}")
        print(f"Phone numbers found: {len(structure['phoneNumbers'])}")
        
        print("\nElements found:")
        for selector, info in structure['selectors'].items():
            print(f"\n{selector}: {info['count']} elements")
            print(f"  Tag: {info['firstTag']}")
            print(f"  Class: {info['firstClass']}")
            print(f"  Sample: {info['sample'][:100]}...")
        
        # Try to click on an element with recording icon
        print("\n\nLooking for clickable call elements...")
        clickable = await page.evaluate('''
            () => {
                // Find elements containing recording icon
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                const recordingElements = [];
                let node;
                while (node = walker.nextNode()) {
                    if (node.nodeValue && node.nodeValue.includes('🎙')) {
                        let parent = node.parentElement;
                        while (parent && parent !== document.body) {
                            if (parent.tagName === 'TR' || parent.tagName === 'DIV') {
                                recordingElements.push({
                                    tag: parent.tagName,
                                    class: parent.className,
                                    text: parent.innerText.substring(0, 100)
                                });
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                }
                return recordingElements.slice(0, 3);
            }
        ''')
        
        print(f"\nFound {len(clickable)} elements with recordings:")
        for i, elem in enumerate(clickable):
            print(f"\n{i+1}. {elem['tag']} - {elem['class']}")
            print(f"   Text: {elem['text']}")
        
        print("\n\nPress Enter to close browser...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_page())