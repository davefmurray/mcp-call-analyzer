"""
Hybrid Pipeline: API + Browser Automation

This combines the best of both approaches:
1. ✅ API to fetch call metadata efficiently
2. ✅ Store call info in Supabase
3. ✅ Browser automation to download audio using DC call ID
4. ✅ Deepgram transcription
5. ✅ GPT-4 analysis
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
from deepgram import DeepgramClient, PrerecordedOptions
from openai import AsyncOpenAI
from supabase import create_client

load_dotenv()

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


class HybridPipeline:
    def __init__(self):
        self.base_url = "https://autoservice.api.digitalconcierge.io"
        self.dashboard_url = "https://autoservice.digitalconcierge.io"
        self.username = os.getenv("DASHBOARD_USERNAME")
        self.password = os.getenv("DASHBOARD_PASSWORD")
        self.token = None
        self.client = httpx.AsyncClient(timeout=60.0)
        
    def _parse_duration(self, duration) -> int:
        """Parse duration - can be int (seconds) or string like '1:23'"""
        if isinstance(duration, int):
            return duration
        
        if not duration or duration == '0:00':
            return 0
        
        if isinstance(duration, str):
            parts = duration.split(':')
            if len(parts) == 2:
                minutes, seconds = parts
                return int(minutes) * 60 + int(seconds)
            elif len(parts) == 3:
                hours, minutes, seconds = parts
                return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        
        return 0
    
    def parse_sentiment(self, sentiment_text):
        """Convert sentiment text to numeric value for database"""
        sentiment_map = {
            "positive": 0.8,
            "negative": -0.8,
            "neutral": 0.0
        }
        return sentiment_map.get(sentiment_text.lower(), 0.0)
    
    async def authenticate_api(self) -> str:
        """Authenticate with API and get JWT token"""
        print("🔐 Authenticating with DC API...")
        
        response = await self.client.post(
            f"{self.base_url}/auth/authenticate",
            json={
                "username": self.username,
                "password": self.password
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            self.token = result.get("token")
            print("✅ API authentication successful!")
            return self.token
        else:
            raise Exception(f"API authentication failed: {response.status_code}")
    
    async def fetch_calls_from_api(self, limit: int = 50, days_back: int = 30) -> List[Dict]:
        """Fetch calls using API and store in Supabase"""
        if not self.token:
            await self.authenticate_api()
        
        print(f"\n📞 Fetching calls from API (last {days_back} days)...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        payload = {
            "query": {
                "$and": [
                    {"date_created": {"$gte": start_date.strftime("%Y-%m-%dT00:00:00-04:00")}},
                    {"date_created": {"$lte": end_date.strftime("%Y-%m-%dT23:59:59-04:00")}}
                ]
            },
            "searchText": "",
            "page": 1,
            "limit": limit,
            "sort": {"date_created": -1}
        }
        
        headers = {
            "x-access-token": self.token,
            "Content-Type": "application/json"
        }
        
        response = await self.client.post(
            f"{self.base_url}/call/list",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            calls = data.get("docs", [])
            
            # Filter for calls with recordings
            calls_with_recordings = []
            stored_count = 0
            
            for call in calls:
                duration = self._parse_duration(call.get('convertedDuration', 0))
                
                if duration > 0:  # Calls with duration likely have recordings
                    # Store in Supabase
                    call_record = {
                        'call_id': call.get('CallSid'),
                        'dc_call_id': call.get('_id'),  # This is what we'll use for the review URL
                        'customer_name': call.get('name', ''),
                        'customer_number': call.get('From', ''),
                        'call_direction': call.get('Direction', 'inbound'),
                        'duration_seconds': duration,
                        'date_created': call.get('date_created', ''),
                        'has_recording': True,
                        'status': 'pending_download',
                        'extension': call.get('ext', '')
                    }
                    
                    try:
                        result = supabase.table('calls').upsert(call_record, on_conflict='call_id').execute()
                        stored_count += 1
                        calls_with_recordings.append(call_record)
                    except Exception as e:
                        print(f"⚠️  Error storing call: {e}")
            
            print(f"✅ Stored {stored_count} calls in database")
            return calls_with_recordings
        else:
            raise Exception(f"Failed to fetch calls: {response.status_code}")
    
    async def download_audio_via_browser(self, dc_call_id: str, call_sid: str) -> Optional[str]:
        """Use browser automation to download audio for a specific call"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            audio_url = None
            download_path = f"downloads/{call_sid}.mp3"
            
            # Monitor network for audio URLs
            async def handle_response(response):
                nonlocal audio_url
                if 'cloudfront' in response.url and '.mp3' in response.url:
                    audio_url = response.url
                    print(f"   🎵 Found audio URL: {audio_url}")
            
            page.on("response", handle_response)
            
            try:
                # Login
                print(f"   🔐 Logging into dashboard...")
                await page.goto(self.dashboard_url)
                await page.wait_for_timeout(2000)
                
                await page.fill('input[placeholder="User Name"]', self.username)
                await page.fill('input[placeholder="Password"]', self.password)
                await page.click('button:has-text("Sign in")')
                await page.wait_for_timeout(3000)
                
                # Navigate directly to call review page
                review_url = f"{self.dashboard_url}/userPortal/calls/review?callId={dc_call_id}"
                print(f"   📞 Navigating to: {review_url}")
                await page.goto(review_url)
                await page.wait_for_timeout(5000)
                
                # Wait for page to load completely
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Try multiple approaches to trigger audio load
                try:
                    # Look for play button with various selectors
                    play_selectors = [
                        'button:has-text("Play")',
                        'button[aria-label*="play" i]',
                        'button[title*="play" i]',
                        '.play-button',
                        '[class*="play"]',
                        'svg[class*="play"]',
                        'i[class*="play"]',
                        'button svg',
                        'button i'
                    ]
                    
                    for selector in play_selectors:
                        try:
                            if await page.locator(selector).count() > 0:
                                await page.click(selector, timeout=2000)
                                print(f"   ▶️  Clicked play button: {selector}")
                                break
                        except:
                            continue
                except:
                    pass
                
                # Also try to find audio element directly
                try:
                    if await page.locator('audio').count() > 0:
                        # Get audio source
                        audio_src = await page.locator('audio').get_attribute('src')
                        if audio_src and not audio_url:
                            audio_url = audio_src
                            print(f"   🎵 Found audio src: {audio_url}")
                except:
                    pass
                
                # Wait for potential lazy loading
                await page.wait_for_timeout(5000)
                
                # Scroll to trigger any lazy loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # Download audio if URL was found
                if audio_url:
                    print(f"   📥 Downloading audio...")
                    
                    # Download with browser's session cookies
                    async with page.context.request as request:
                        response = await request.get(audio_url)
                        if response.status == 200:
                            os.makedirs('downloads', exist_ok=True)
                            with open(download_path, 'wb') as f:
                                f.write(await response.body())
                            print(f"   ✅ Audio saved to: {download_path}")
                            return download_path
                else:
                    print(f"   ⚠️  No audio URL found for call {call_sid}")
                    
            except Exception as e:
                print(f"   ❌ Browser error: {e}")
            finally:
                await browser.close()
            
            return None
    
    async def transcribe_with_deepgram(self, audio_file: str) -> Dict:
        """Transcribe audio using Deepgram"""
        print("🎙️ Transcribing with Deepgram...")
        
        try:
            with open(audio_file, "rb") as audio:
                buffer_data = audio.read()
            
            payload = {"buffer": buffer_data}
            
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                punctuate=True,
                diarize=True,
                language="en-US"
            )
            
            response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
            
            transcript = response.results.channels[0].alternatives[0].transcript
            
            return {
                'transcript': transcript,
                'success': True
            }
            
        except Exception as e:
            print(f"⚠️  Deepgram error: {e}")
            return {
                'transcript': "Transcription failed",
                'success': False
            }
    
    async def analyze_with_gpt4(self, transcript: str, call_info: Dict) -> Dict:
        """Analyze call with GPT-4"""
        print("🤖 Analyzing with GPT-4...")
        
        analysis_prompt = f"""Analyze this auto service call transcript and provide:

1. summary - Brief 2-3 sentence summary
2. customer_intent - Why the customer called
3. outcome - What was resolved or agreed upon
4. follow_up_needed - Any actions the business needs to take
5. sentiment - Customer sentiment (positive/neutral/negative)
6. category - One of: appointment_scheduling, ride_request, service_inquiry, parts_inquiry, status_check, complaint, other
7. missed_opportunity - Any potential missed sales or service opportunities

Call Context:
- Customer: {call_info.get('customer_name', 'Unknown')}
- Duration: {call_info.get('duration_seconds', 0)} seconds

Transcript:
{transcript}

Respond in JSON format."""

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an automotive service call analyst."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"⚠️  GPT-4 error: {e}")
            return {"error": str(e)}
    
    async def process_pending_calls(self, batch_size: int = 5):
        """Process calls that are pending download"""
        print("\n🔄 Processing pending calls...")
        
        # Get pending calls from Supabase
        result = supabase.table('calls').select("*").eq('status', 'pending_download').limit(batch_size).execute()
        pending_calls = result.data
        
        print(f"📋 Found {len(pending_calls)} pending calls")
        
        for call in pending_calls:
            print(f"\n{'='*60}")
            print(f"Processing: {call['call_id']} ({call['customer_name']})")
            
            try:
                # Download audio via browser
                audio_path = await self.download_audio_via_browser(
                    call['dc_call_id'],  # Use DC's internal ID for the review URL
                    call['call_id']      # Use CallSid for filename
                )
                
                if audio_path and os.path.exists(audio_path):
                    # Upload to Supabase storage
                    with open(audio_path, 'rb') as f:
                        file_data = f.read()
                    
                    storage_path = f"call-recordings/{call['call_id']}.mp3"
                    
                    try:
                        response = supabase.storage.from_('call-recordings').upload(
                            storage_path,
                            file_data,
                            {"content-type": "audio/mpeg"}
                        )
                        storage_url = supabase.storage.from_('call-recordings').get_public_url(storage_path)
                        print(f"☁️  Uploaded to Supabase")
                    except:
                        storage_url = audio_path
                    
                    # Transcribe
                    transcript_data = await self.transcribe_with_deepgram(audio_path)
                    
                    if transcript_data['success']:
                        # Analyze
                        analysis = await self.analyze_with_gpt4(transcript_data['transcript'], call)
                        
                        # Update call record
                        update_data = {
                            'status': 'analyzed',
                            'dc_transcript': transcript_data['transcript'],
                            'dc_sentiment': self.parse_sentiment(analysis.get('sentiment', 'neutral'))
                        }
                        
                        supabase.table('calls').update(update_data).eq('call_id', call['call_id']).execute()
                        
                        # Store analysis
                        analysis_record = {
                            'call_id': call['call_id'],
                            'analysis_data': analysis,
                            'created_at': datetime.now().isoformat()
                        }
                        
                        try:
                            supabase.table('call_analysis').insert(analysis_record).execute()
                        except:
                            pass
                        
                        print(f"✅ Successfully processed call {call['call_id']}")
                        print(f"   Category: {analysis.get('category')}")
                        print(f"   Sentiment: {analysis.get('sentiment')}")
                    else:
                        # Mark as transcription failed
                        supabase.table('calls').update({'status': 'transcription_failed'}).eq('call_id', call['call_id']).execute()
                else:
                    # Mark as download failed
                    supabase.table('calls').update({'status': 'download_failed'}).eq('call_id', call['call_id']).execute()
                    
            except Exception as e:
                print(f"❌ Error processing call: {e}")
                supabase.table('calls').update({'status': 'error'}).eq('call_id', call['call_id']).execute()
    
    async def run_complete_pipeline(self):
        """Run the complete hybrid pipeline"""
        print("🚀 STARTING HYBRID PIPELINE")
        print("=" * 60)
        
        try:
            # Step 1: Fetch calls via API and populate database
            calls = await self.fetch_calls_from_api(limit=50, days_back=7)
            
            # Step 2: Process pending calls with browser automation
            await self.process_pending_calls(batch_size=5)
            
            # Summary
            result = supabase.table('calls').select("status", count="exact").execute()
            
            print(f"\n\n📊 PIPELINE SUMMARY")
            print("=" * 60)
            print(f"Total calls in database: {result.count}")
            
            # Get status breakdown
            status_counts = {}
            for record in result.data:
                status = record['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            for status, count in status_counts.items():
                print(f"{status}: {count}")
                
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
        finally:
            await self.client.aclose()


async def main():
    """Run the hybrid pipeline"""
    pipeline = HybridPipeline()
    await pipeline.run_complete_pipeline()


if __name__ == "__main__":
    asyncio.run(main())