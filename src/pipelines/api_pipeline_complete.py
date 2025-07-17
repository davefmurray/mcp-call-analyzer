"""
Complete MCP Call Analyzer Pipeline with API Integration

This combines:
1. ✅ API-based call fetching (faster than web scraping)
2. ✅ Audio download from CloudFront
3. ✅ Audio upload to Supabase storage
4. ✅ Deepgram transcription with speaker diarization
5. ✅ GPT-4 analysis for insights
6. ✅ Results stored in Supabase
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional
from deepgram import DeepgramClient, PrerecordedOptions
from openai import AsyncOpenAI
from supabase import create_client
import hashlib

load_dotenv()

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


class CompletePipeline:
    def __init__(self):
        self.base_url = "https://autoservice.api.digitalconcierge.io"
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
    
    async def authenticate(self) -> str:
        """Authenticate and get JWT token"""
        print("🔐 Authenticating with DC API...")
        
        auth_data = {
            "username": self.username,
            "password": self.password
        }
        
        response = await self.client.post(
            f"{self.base_url}/auth/authenticate",
            json=auth_data
        )
        
        if response.status_code == 200:
            result = response.json()
            self.token = result.get("token")
            print("✅ Authentication successful!")
            return self.token
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
    async def get_calls_with_recordings(self, limit: int = 100, days_back: int = 30) -> List[Dict]:
        """Fetch calls that have recordings"""
        if not self.token:
            await self.authenticate()
        
        print(f"📞 Fetching calls with recordings from the last {days_back} days...")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # API request payload
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
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = await self.client.post(
            f"{self.base_url}/call/list",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            all_calls = data.get("docs", [])
            
            # Filter for calls with recordings or labels that indicate recording
            calls_with_recordings = []
            for idx, call in enumerate(all_calls):
                if idx == 0:
                    print(f"\n🔍 Sample call data: {json.dumps(call, indent=2)[:500]}...")
                
                # Check various indicators of recording
                duration = call.get('convertedDuration', 0)
                duration_seconds = self._parse_duration(duration) if duration else 0
                
                has_recording = (
                    call.get('recordingId') or 
                    call.get('recordingUrl') or
                    (call.get('labels') and '🎙' in str(call.get('labels', []))) or
                    duration_seconds > 0  # Calls with duration likely have recordings
                )
                
                if has_recording:
                    calls_with_recordings.append(call)
            
            print(f"✅ Found {len(calls_with_recordings)} calls with recordings out of {len(all_calls)} total")
            return calls_with_recordings
        else:
            raise Exception(f"Failed to fetch calls: {response.status_code} - {response.text}")
    
    def extract_audio_url(self, call_data: Dict) -> Optional[str]:
        """Extract or construct audio URL from call data"""
        # Check if recording URL is provided directly
        recording_url = call_data.get("recordingUrl")
        if recording_url:
            return recording_url
        
        # Check if there's a specific recording ID
        recording_id = call_data.get("recordingId")
        if recording_id:
            # Try different URL patterns
            return f"https://d3vneafawyd5u6.cloudfront.net/Recordings/{recording_id}.mp3"
        
        # Construct CloudFront URL from CallSid
        call_sid = call_data.get("CallSid")
        if call_sid:
            # Remove 'CA' prefix if present and use the rest as recording ID
            recording_id = call_sid[2:] if call_sid.startswith('CA') else call_sid
            return f"https://d3vneafawyd5u6.cloudfront.net/Recordings/RE{recording_id}.mp3"
        
        return None
    
    async def download_audio(self, url: str, output_path: str) -> bool:
        """Download audio file from URL"""
        try:
            print(f"📥 Downloading audio from: {url}")
            response = await self.client.get(url, follow_redirects=True)
            
            if response.status_code == 200:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Audio saved to: {output_path}")
                return True
            else:
                print(f"⚠️  Failed to download audio: {response.status_code}")
                # Try alternative URL patterns
                alt_url = url.replace('/RE', '/').replace('Recordings/', 'recordings/')
                response = await self.client.get(alt_url, follow_redirects=True)
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ Audio saved using alternative URL")
                    return True
                return False
        except Exception as e:
            print(f"⚠️  Error downloading audio: {e}")
            return False
    
    async def upload_to_supabase(self, file_path: str, call_id: str) -> Optional[str]:
        """Upload audio file to Supabase storage"""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Create unique filename
            file_name = f"{call_id}.mp3"
            storage_path = f"call-recordings/{file_name}"
            
            # Upload to Supabase
            response = supabase.storage.from_('call-recordings').upload(
                storage_path,
                file_data,
                {"content-type": "audio/mpeg"}
            )
            
            # Get public URL
            public_url = supabase.storage.from_('call-recordings').get_public_url(storage_path)
            print(f"☁️  Uploaded to Supabase: {public_url}")
            
            return public_url
        except Exception as e:
            print(f"⚠️  Failed to upload to Supabase: {e}")
            return None
    
    async def transcribe_with_deepgram(self, audio_file: str) -> Dict:
        """Transcribe audio using Deepgram with speaker diarization"""
        print("🎙️ Transcribing with Deepgram...")
        
        try:
            with open(audio_file, "rb") as audio:
                buffer_data = audio.read()
            
            payload = {"buffer": buffer_data}
            
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                utterances=True,
                punctuate=True,
                paragraphs=True,
                diarize=True,
                language="en-US"
            )
            
            response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
            
            # Extract transcript and diarization
            result = {
                'transcript': response.results.channels[0].alternatives[0].transcript,
                'speakers': []
            }
            
            # Extract speaker segments if available
            if hasattr(response.results.channels[0].alternatives[0], 'paragraphs'):
                paragraphs = response.results.channels[0].alternatives[0].paragraphs
                if paragraphs and hasattr(paragraphs, 'paragraphs'):
                    for para in paragraphs.paragraphs:
                        speaker_id = getattr(para, 'speaker', 'Unknown')
                        text = ' '.join([s.text for s in para.sentences])
                        result['speakers'].append({
                            'speaker': f"Speaker {speaker_id}",
                            'text': text
                        })
            
            return result
            
        except Exception as e:
            print(f"⚠️  Deepgram error: {e}")
            # Fallback transcript
            return {
                'transcript': "Transcription failed",
                'speakers': []
            }
    
    async def analyze_with_gpt4(self, transcript: str, call_info: Dict) -> Dict:
        """Analyze call transcript with GPT-4"""
        print("🤖 Analyzing with GPT-4...")
        
        analysis_prompt = f"""Analyze this auto service call transcript and provide:

1. summary - Brief 2-3 sentence summary
2. customer_intent - Why the customer called
3. outcome - What was resolved or agreed upon
4. follow_up_needed - Any actions the business needs to take
5. sentiment - Customer sentiment (positive/neutral/negative)
6. category - One of: appointment_scheduling, ride_request, service_inquiry, parts_inquiry, status_check, complaint, other
7. missed_opportunity - Any potential missed sales or service opportunities
8. key_topics - List of main topics discussed
9. urgency_level - high/medium/low

Call Context:
- Customer: {call_info.get('customer_name', 'Unknown')}
- Duration: {call_info.get('duration_seconds', 0)} seconds
- Direction: {call_info.get('call_direction', 'Unknown')}

Transcript:
{transcript}

Respond in JSON format."""

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an automotive service call analyst. Analyze calls for insights and opportunities."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"⚠️  GPT-4 analysis error: {e}")
            return {
                "summary": "Analysis failed",
                "sentiment": "neutral",
                "category": "other"
            }
    
    async def store_results(self, call_data: Dict, transcript_data: Dict, analysis: Dict, storage_url: str):
        """Store all results in Supabase"""
        print("💾 Storing results in Supabase...")
        
        # Prepare call record
        call_record = {
            'call_id': call_data.get('CallSid'),
            'dc_call_id': call_data.get('_id'),
            'customer_name': call_data.get('name', ''),
            'customer_number': call_data.get('From', ''),
            'call_direction': call_data.get('Direction', 'inbound'),
            'duration_seconds': self._parse_duration(call_data.get('convertedDuration', 0)),
            'date_created': call_data.get('date_created', ''),
            'has_recording': True,
            'dc_transcript': transcript_data['transcript'],
            'dc_sentiment': self.parse_sentiment(analysis.get('sentiment', 'neutral')),
            'status': 'analyzed',
            'extension': call_data.get('ext', '')
        }
        
        # Store in calls table
        try:
            result = supabase.table('calls').upsert(call_record, on_conflict='call_id').execute()
            print("✅ Stored in calls table")
        except Exception as e:
            print(f"⚠️  Error with calls table: {e}")
        
        # Store recording info
        recording_record = {
            'call_id': call_data.get('CallSid'),
            'file_name': f"{call_data.get('CallSid')}.mp3",
            'file_size_bytes': os.path.getsize(f"downloads/{call_data.get('CallSid')}.mp3") if os.path.exists(f"downloads/{call_data.get('CallSid')}.mp3") else 0,
            'mime_type': 'audio/mpeg',
            'storage_path': f"call-recordings/{call_data.get('CallSid')}.mp3",
            'storage_url': storage_url,
            'upload_status': 'completed',
            'uploaded_at': datetime.now().isoformat()
        }
        
        try:
            # Check if exists
            existing = supabase.table('recordings').select("*").eq('call_id', call_data.get('CallSid')).execute()
            if existing.data:
                result = supabase.table('recordings').update(recording_record).eq('call_id', call_data.get('CallSid')).execute()
            else:
                result = supabase.table('recordings').insert(recording_record).execute()
            print("✅ Stored in recordings table")
        except Exception as e:
            print(f"⚠️  Error with recordings table: {e}")
        
        # Store transcription with speaker diarization
        transcription_record = {
            'call_id': call_data.get('CallSid'),
            'transcript': transcript_data['transcript'],
            'speaker_segments': transcript_data.get('speakers', []),
            'created_at': datetime.now().isoformat()
        }
        
        try:
            result = supabase.table('transcriptions').upsert(transcription_record, on_conflict='call_id').execute()
            print("✅ Stored transcription with speakers")
        except:
            pass
        
        # Store analysis
        analysis_record = {
            'call_id': call_data.get('CallSid'),
            'analysis_data': analysis,
            'created_at': datetime.now().isoformat()
        }
        
        try:
            result = supabase.table('call_analysis').insert(analysis_record).execute()
            print("✅ Stored analysis data")
        except:
            pass
    
    async def process_single_call(self, call_data: Dict) -> Dict:
        """Process a single call through the complete pipeline"""
        call_id = call_data.get('CallSid')
        print(f"\n{'='*60}")
        print(f"📞 Processing call: {call_id}")
        print(f"   Customer: {call_data.get('name', 'Unknown')} ({call_data.get('From', '')})")
        print(f"   Duration: {self._parse_duration(call_data.get('convertedDuration', 0))}s")
        print(f"   Date: {call_data.get('date_created', '')}")
        
        result = {
            'call_id': call_id,
            'success': False,
            'error': None
        }
        
        try:
            # Step 1: Download audio
            audio_url = self.extract_audio_url(call_data)
            if not audio_url:
                raise Exception("No audio URL found")
            
            audio_path = f"downloads/{call_id}.mp3"
            if not await self.download_audio(audio_url, audio_path):
                raise Exception("Failed to download audio")
            
            # Step 2: Upload to Supabase
            storage_url = await self.upload_to_supabase(audio_path, call_id)
            if not storage_url:
                storage_url = audio_url  # Fallback to original URL
            
            # Step 3: Transcribe with Deepgram
            transcript_data = await self.transcribe_with_deepgram(audio_path)
            
            # Step 4: Analyze with GPT-4
            analysis = await self.analyze_with_gpt4(transcript_data['transcript'], call_data)
            
            # Step 5: Store results
            await self.store_results(call_data, transcript_data, analysis, storage_url)
            
            result['success'] = True
            result['transcript'] = transcript_data['transcript'][:200] + "..."
            result['analysis'] = analysis
            
            print(f"✅ Successfully processed call {call_id}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error processing call {call_id}: {e}")
        
        return result
    
    async def run_pipeline(self, limit: int = 5, days_back: int = 30):
        """Run the complete pipeline"""
        print("🚀 STARTING COMPLETE PIPELINE")
        print("=" * 60)
        
        try:
            # Get calls with recordings
            calls = await self.get_calls_with_recordings(limit=limit, days_back=days_back)
            
            if not calls:
                print("⚠️  No calls with recordings found")
                return
            
            # Process each call
            results = []
            for call in calls:
                result = await self.process_single_call(call)
                results.append(result)
            
            # Summary
            print(f"\n\n📊 PIPELINE SUMMARY")
            print("=" * 60)
            successful = sum(1 for r in results if r['success'])
            print(f"Total calls processed: {len(results)}")
            print(f"Successful: {successful}")
            print(f"Failed: {len(results) - successful}")
            
            # Show insights from successful calls
            print("\n🔍 KEY INSIGHTS:")
            for result in results:
                if result['success'] and result.get('analysis'):
                    analysis = result['analysis']
                    print(f"\n📞 Call {result['call_id']}:")
                    print(f"   Category: {analysis.get('category', 'N/A')}")
                    print(f"   Sentiment: {analysis.get('sentiment', 'N/A')}")
                    print(f"   Intent: {analysis.get('customer_intent', 'N/A')}")
                    if analysis.get('missed_opportunity'):
                        print(f"   ⚠️  Missed Opportunity: {analysis['missed_opportunity']}")
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
        finally:
            await self.client.aclose()


async def main():
    """Run the complete pipeline"""
    pipeline = CompletePipeline()
    
    # Process recent calls with recordings
    await pipeline.run_pipeline(limit=10, days_back=30)


if __name__ == "__main__":
    asyncio.run(main())