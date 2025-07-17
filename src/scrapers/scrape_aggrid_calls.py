import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import json

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

async def scrape_calls_with_aggrid():
    """Scrape calls from AG-Grid table"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging for debugging
        page.on("console", lambda msg: print(f"Console: {msg.text}") if "error" in msg.text.lower() else None)
        
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
        
        # Wait for AG-Grid to load
        print("Waiting for AG-Grid to load...")
        await page.wait_for_selector('.ag-root-wrapper', timeout=10000)
        await page.wait_for_timeout(3000)  # Give it time to populate
        
        # Get calls data from AG-Grid
        print("Extracting call data from AG-Grid...")
        calls_data = await page.evaluate('''
            () => {
                // Find all row elements in AG-Grid
                const rows = document.querySelectorAll('.ag-center-cols-container .ag-row');
                console.log(`Found ${rows.length} rows`);
                
                const calls = [];
                
                rows.forEach((row, index) => {
                    // Get all cells in the row
                    const cells = row.querySelectorAll('.ag-cell');
                    const cellData = Array.from(cells).map(cell => cell.textContent?.trim() || '');
                    
                    if (cellData.length > 0 && cellData.some(c => c)) {
                        // Extract data based on column position
                        const call = {
                            rowIndex: index,
                            date: cellData[0] || '',
                            direction: cellData[1] || '',
                            name: cellData[2] || '',
                            from: cellData[3] || '',
                            to: cellData[4] || '',
                            length: cellData[5] || '',
                            tags: cellData[6] || '',
                            advisor: cellData[7] || '',
                            reviewScore: cellData[8] || '',
                            hasRecording: cellData.some(cell => cell.includes('🎙')),
                            rawData: cellData
                        };
                        
                        calls.push(call);
                    }
                });
                
                return calls;
            }
        ''')
        
        print(f"Found {len(calls_data)} calls")
        
        if len(calls_data) == 0:
            print("No calls found! Trying alternative extraction...")
            # Try to get data via AG-Grid API
            calls_data = await page.evaluate('''
                () => {
                    // Look for AG-Grid instance
                    const gridWrapper = document.querySelector('.ag-root-wrapper');
                    if (gridWrapper && gridWrapper.__agComponent) {
                        const api = gridWrapper.__agComponent.gridOptions.api;
                        if (api) {
                            const rowData = [];
                            api.forEachNode(node => {
                                if (node.data) {
                                    rowData.push(node.data);
                                }
                            });
                            return rowData;
                        }
                    }
                    return [];
                }
            ''')
            print(f"Found {len(calls_data)} calls via AG-Grid API")
        
        # Process calls
        for i, call in enumerate(calls_data[:5]):  # Process first 5
            print(f"\n--- Processing call {i+1} ---")
            print(f"Call data: {json.dumps(call, indent=2)}")
            
            if not call.get('hasRecording', False) and '🎙' not in str(call):
                print("No recording, skipping...")
                continue
            
            # Click on the row to see if we can get more details
            try:
                await page.click(f'.ag-center-cols-container .ag-row:nth-child({i+1})')
                await page.wait_for_timeout(2000)
                
                # Check for any modal or expanded view
                modal = await page.query_selector('.modal-content, [role="dialog"], .call-details')
                if modal:
                    print("Found modal/details view")
                    
                    # Look for download link
                    download_links = await page.query_selector_all('a[href*="download"], a[href*=".mp3"], button:has-text("Download")')
                    for link in download_links:
                        href = await link.get_attribute('href')
                        text = await link.text_content()
                        print(f"Found download link: {text} -> {href}")
                    
                    # Close modal
                    close_btn = await page.query_selector('button[aria-label="Close"], button:has-text("Close"), .close')
                    if close_btn:
                        await close_btn.click()
                        await page.wait_for_timeout(500)
            except Exception as e:
                print(f"Error clicking row: {e}")
            
            # Extract call ID if possible
            call_id = None
            if isinstance(call, dict):
                # Look for ID in various fields
                call_id = call.get('id') or call.get('callId') or call.get('call_id')
                
                # If no ID, generate one
                if not call_id:
                    call_id = f"scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
            
            # Insert into Supabase
            try:
                call_record = {
                    'call_id': call_id,
                    'dc_call_id': call_id,
                    'customer_name': call.get('name', ''),
                    'customer_number': call.get('from', '') or call.get('to', ''),
                    'call_direction': 'inbound' if 'in' in str(call.get('direction', '')).lower() else 'outbound',
                    'duration_seconds': parse_duration(call.get('length', '0')),
                    'date_created': datetime.now().isoformat(),
                    'has_recording': call.get('hasRecording', False),
                    'status': 'scraped'
                }
                
                result = supabase.table('calls').insert(call_record).execute()
                print(f"✅ Inserted call {call_id}")
                
            except Exception as e:
                print(f"❌ Error inserting call: {e}")
        
        print("\n\nPress Enter to close browser...")
        input()
        
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

if __name__ == "__main__":
    asyncio.run(scrape_calls_with_aggrid())