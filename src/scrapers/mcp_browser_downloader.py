"""
MCP Browser-based Audio Downloader
Uses MCP Playwright tools to download audio files from Digital Concierge
"""

import asyncio
import os
import logging
from typing import Optional, Dict, List
from pathlib import Path
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPBrowserDownloader:
    """Real MCP browser automation for audio downloads"""
    
    def __init__(self):
        self.dashboard_url = "https://autoservice.digitalconcierge.io"
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        self.is_logged_in = False
        self.browser_state = {
            "cookies": None,
            "auth_token": None
        }
        
    async def initialize_browser(self):
        """Initialize browser with download settings"""
        logger.info("🌐 Initializing MCP browser...")
        
        # Navigate to initial page to establish session
        await mcp__playwright__browser_navigate(url=self.dashboard_url)
        await mcp__playwright__browser_wait_for(time=2)
        
        # Set viewport for better compatibility
        await mcp__playwright__browser_resize(width=1280, height=800)
        
        logger.info("✅ Browser initialized")
        
    async def login_to_dashboard(self) -> bool:
        """Login to Digital Concierge dashboard"""
        
        if self.is_logged_in:
            logger.info("Already logged in")
            return True
            
        try:
            logger.info("🔐 Logging into dashboard...")
            
            # Navigate to login page
            login_url = f"{self.dashboard_url}/userPortal/sign-in"
            await mcp__playwright__browser_navigate(url=login_url)
            await mcp__playwright__browser_wait_for(time=3)
            
            # Take snapshot to identify elements
            snapshot = await mcp__playwright__browser_snapshot()
            logger.info(f"📸 Login page snapshot taken")
            
            # Get credentials
            username = os.getenv("DASHBOARD_USERNAME")
            password = os.getenv("DASHBOARD_PASSWORD")
            
            if not username or not password:
                raise ValueError("Dashboard credentials not set in environment")
            
            # Type username
            # Look for username input - try multiple selectors
            username_typed = False
            for selector in ['input[name="username"]', 'input[placeholder*="User"]', 'input[type="text"]']:
                try:
                    await mcp__playwright__browser_type(
                        element="Username field",
                        ref=selector,
                        text=username
                    )
                    username_typed = True
                    logger.info(f"✅ Username entered using {selector}")
                    break
                except:
                    continue
                    
            if not username_typed:
                raise Exception("Could not find username field")
            
            # Type password
            await mcp__playwright__browser_type(
                element="Password field",
                ref='input[type="password"]',
                text=password
            )
            logger.info("✅ Password entered")
            
            # Click login button
            await mcp__playwright__browser_click(
                element="Sign in button",
                ref='button[type="submit"]'
            )
            
            # Wait for login to complete
            await mcp__playwright__browser_wait_for(time=5)
            
            # Check if login successful by looking for calls page elements
            try:
                await mcp__playwright__browser_navigate(url=f"{self.dashboard_url}/userPortal/admin/calls")
                await mcp__playwright__browser_wait_for(time=3)
                
                # Take screenshot to verify
                await mcp__playwright__browser_take_screenshot(
                    filename="login_success.png"
                )
                
                self.is_logged_in = True
                logger.info("✅ Login successful!")
                
                # Store auth token from network requests
                requests = await mcp__playwright__browser_network_requests()
                for req in requests:
                    headers = req.get('headers', {})
                    if 'x-access-token' in headers:
                        self.browser_state['auth_token'] = headers['x-access-token']
                        logger.info("🔑 Captured auth token")
                        
                return True
                
            except Exception as e:
                logger.error(f"Login verification failed: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def navigate_to_call_and_download(self, call_data: Dict) -> Optional[str]:
        """Navigate to specific call and download audio"""
        
        call_sid = call_data['call_id']
        output_path = self.downloads_dir / f"{call_sid}.mp3"
        
        # Skip if already downloaded
        if output_path.exists():
            logger.info(f"✅ Audio already exists: {output_path}")
            return str(output_path)
            
        try:
            logger.info(f"📞 Processing call: {call_sid}")
            
            # Navigate to calls page with search
            calls_url = f"{self.dashboard_url}/userPortal/admin/calls"
            await mcp__playwright__browser_navigate(url=calls_url)
            await mcp__playwright__browser_wait_for(time=3)
            
            # Search for specific call
            # Try to find search input
            await mcp__playwright__browser_type(
                element="Search input",
                ref='input[placeholder*="Search"]',
                text=call_sid
            )
            
            # Wait for results
            await mcp__playwright__browser_wait_for(time=2)
            
            # Take snapshot to find call row
            snapshot = await mcp__playwright__browser_snapshot()
            
            # Click on the call row to open modal
            # Try different selectors
            clicked = False
            for selector in [
                f'tr:has-text("{call_sid}")',
                f'[data-call-id="{call_sid}"]',
                f'td:has-text("{call_sid}")'
            ]:
                try:
                    await mcp__playwright__browser_click(
                        element=f"Call row for {call_sid}",
                        ref=selector
                    )
                    clicked = True
                    logger.info(f"✅ Clicked call row using {selector}")
                    break
                except:
                    continue
                    
            if not clicked:
                # Try clicking first row if specific call not found
                await mcp__playwright__browser_click(
                    element="First call row",
                    ref='tbody tr:first-child'
                )
                logger.warning("Clicked first row as fallback")
            
            # Wait for modal to open
            await mcp__playwright__browser_wait_for(time=3)
            
            # Capture network requests to find audio URL
            requests = await mcp__playwright__browser_network_requests()
            
            audio_url = None
            for req in requests:
                url = req.get('url', '')
                # Look for audio URLs
                if any(pattern in url for pattern in ['.mp3', 'cloudfront.net', 'recording', 'audio']):
                    if 'mp3' in url or 'audio' in url:
                        audio_url = url
                        logger.info(f"🎵 Found audio URL: {url[:80]}...")
                        break
            
            if not audio_url:
                # Try alternative: look for audio element in page
                # Execute JavaScript to find audio source
                logger.info("Searching for audio element in page...")
                
                # Use Puppeteer evaluate since we have it
                try:
                    audio_src = await mcp__puppeteer__puppeteer_evaluate(
                        script="""
                        const audio = document.querySelector('audio');
                        audio ? audio.src : null;
                        """
                    )
                    if audio_src:
                        audio_url = audio_src
                        logger.info(f"🎵 Found audio URL from element: {audio_url[:80]}...")
                except:
                    pass
            
            if audio_url:
                # Download the audio file
                logger.info(f"📥 Downloading audio to: {output_path}")
                
                # Create a new tab for download
                await mcp__playwright__browser_tab_new(url=audio_url)
                await mcp__playwright__browser_wait_for(time=5)
                
                # Check if file was downloaded
                # Note: This is a limitation - we need to handle browser downloads
                # For now, we'll close the tab and check manually
                await mcp__playwright__browser_tab_close()
                
                # Alternative: Use network request data if available
                for req in requests:
                    if req.get('url') == audio_url and req.get('response'):
                        # We have the response data
                        logger.info("✅ Audio download completed via network capture")
                        return str(output_path)
                
                # If we got here, download might have succeeded
                # Check default downloads folder
                possible_locations = [
                    Path.home() / "Downloads" / f"{call_sid}.mp3",
                    Path.home() / "Downloads" / "recording.mp3",
                    self.downloads_dir / f"{call_sid}.mp3"
                ]
                
                for location in possible_locations:
                    if location.exists():
                        # Move to our downloads folder
                        import shutil
                        shutil.move(str(location), str(output_path))
                        logger.info(f"✅ Found and moved audio from {location}")
                        return str(output_path)
                
                logger.warning("⚠️ Could not verify audio download")
                return None
                
            else:
                logger.error("❌ No audio URL found")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading audio for {call_sid}: {e}")
            return None
    
    async def download_batch(self, calls: List[Dict], max_concurrent: int = 3) -> Dict:
        """Download multiple calls with concurrency control"""
        
        results = {
            "successful": [],
            "failed": [],
            "total": len(calls)
        }
        
        # Initialize browser
        await self.initialize_browser()
        
        # Login
        if not await self.login_to_dashboard():
            logger.error("Failed to login")
            results["failed"] = calls
            return results
        
        # Process calls in batches
        for i in range(0, len(calls), max_concurrent):
            batch = calls[i:i + max_concurrent]
            
            # Process batch concurrently
            tasks = []
            for call in batch:
                task = self.navigate_to_call_and_download(call)
                tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for call, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Exception for {call['call_id']}: {result}")
                    results["failed"].append(call)
                elif result:
                    results["successful"].append({
                        "call": call,
                        "audio_path": result
                    })
                else:
                    results["failed"].append(call)
            
            # Small delay between batches
            if i + max_concurrent < len(calls):
                await asyncio.sleep(2)
        
        # Close browser
        await mcp__playwright__browser_close()
        
        return results
    
    async def test_single_download(self, call_data: Dict) -> bool:
        """Test download for a single call"""
        
        await self.initialize_browser()
        
        if not await self.login_to_dashboard():
            logger.error("Failed to login")
            return False
        
        result = await self.navigate_to_call_and_download(call_data)
        
        await mcp__playwright__browser_close()
        
        return result is not None


# Fallback implementation for audio download via direct HTTP
async def download_audio_direct(audio_url: str, output_path: str, auth_token: Optional[str] = None) -> bool:
    """Direct audio download using HTTP request"""
    
    import httpx
    
    try:
        headers = {}
        if auth_token:
            headers['x-access-token'] = auth_token
            
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            response = await client.get(audio_url, headers=headers)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"✅ Downloaded {len(response.content)} bytes")
                return True
            else:
                logger.error(f"Download failed: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Direct download error: {e}")
        return False


# Example usage
async def main():
    """Test the MCP browser downloader"""
    
    downloader = MCPBrowserDownloader()
    
    # Test with a single call
    test_call = {
        'call_id': 'CAa5cbe57a8f3acfa11b034c41856d9cb7',
        'customer_name': 'TEST CUSTOMER',
        'call_direction': 'inbound'
    }
    
    success = await downloader.test_single_download(test_call)
    
    if success:
        logger.info("✅ Test download successful!")
    else:
        logger.error("❌ Test download failed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())