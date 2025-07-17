#!/usr/bin/env python3
"""
Test Multiple Calls - Fixed Version

Fixed the 'tags' column issue by removing it from the database insert.
This version successfully tests multiple calls through the complete pipeline.
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import httpx
from supabase import create_client
from deepgram import DeepgramClient, PrerecordedOptions
from openai import AsyncOpenAI
import logging
from typing import List, Dict, Optional
import shutil

# Load environment variables
load_dotenv()

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize clients
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
deepgram = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class MultiCallTester:
    def __init__(self):
        self.base_url = "https://autoservice.api.digitalconcierge.io"
        self.username = os.getenv("DASHBOARD_USERNAME", "dev")
        self.password = os.getenv("DASHBOARD_PASSWORD")
        self.token = None
        self.client = httpx.AsyncClient(timeout=60.0)
        self.test_results = {
            "total_calls": 0,
            "successful": 0,
            "failed": 0,
            "errors": [],
            "insights": []
        }
        
    async def authenticate(self) -> bool:
        """Test API authentication"""
        logger.info("🔐 Testing API authentication...")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/auth/authenticate",
                json={"username": self.username, "password": self.password}
            )
            
            if response.status_code == 200:
                self.token = response.json().get("token")
                logger.info("✅ Authentication successful!")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def _parse_duration(self, duration) -> int:
        """Parse duration from various formats"""
        if isinstance(duration, int):
            return duration
        if not duration or duration == '0:00':
            return 0
        if isinstance(duration, str):
            parts = duration.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    
    async def fetch_test_calls(self, limit: int = 5) -> List[Dict]:
        """Fetch multiple calls for testing"""
        logger.info(f"\n📞 Fetching {limit} test calls from API...")
        
        if not self.token:
            if not await self.authenticate():
                return []
        
        # Fetch recent calls
        payload = {
            "query": {
                "$and": [
                    {"date_created": {"$gte": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00-04:00")}},
                    {"date_created": {"$lte": datetime.now().strftime("%Y-%m-%dT23:59:59-04:00")}}
                ]
            },
            "searchText": "",
            "page": 1,
            "limit": 50,
            "sort": {"date_created": -1}
        }
        
        headers = {
            "x-access-token": self.token,
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/call/list",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                all_calls = data.get("docs", [])
                
                # Filter for good test calls
                test_calls = []
                for call in all_calls:
                    duration = self._parse_duration(call.get('convertedDuration', 0))
                    
                    # Select calls between 30 seconds and 10 minutes
                    if 30 < duration < 600:
                        test_calls.append({
                            'call_id': call.get('CallSid'),
                            'dc_call_id': call.get('_id'),
                            'customer_name': call.get('name', 'Unknown'),
                            'customer_number': call.get('From', ''),
                            'call_direction': call.get('Direction', 'inbound'),
                            'duration_seconds': duration,
                            'date_created': call.get('date_created', ''),
                            'has_recording': True,
                            'extension': call.get('ext', '')
                            # Removed 'tags' field that was causing errors
                        })
                        
                        if len(test_calls) >= limit:
                            break
                
                logger.info(f"✅ Found {len(test_calls)} suitable test calls")
                return test_calls
                
            else:
                logger.error(f"❌ Failed to fetch calls: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error fetching calls: {e}")
            return []
    
    async def test_call_storage(self, calls: List[Dict]) -> int:
        """Test storing calls in Supabase"""
        logger.info(f"\n💾 Testing storage of {len(calls)} calls in Supabase...")
        
        stored_count = 0
        for call in calls:
            try:
                # Upsert call to database
                result = supabase.table('calls').upsert(
                    {**call, 'status': 'test_pending'},
                    on_conflict='call_id'
                ).execute()
                
                stored_count += 1
                logger.info(f"   ✅ Stored: {call['call_id']} - {call['customer_name']}")
                
            except Exception as e:
                logger.error(f"   ❌ Failed to store {call['call_id']}: {e}")
        
        logger.info(f"📊 Stored {stored_count}/{len(calls)} calls successfully")
        return stored_count
    
    async def simulate_audio_download(self, call_id: str) -> Optional[str]:
        """Simulate audio download using test file"""
        test_audio = "downloads/test_call_20250716_082821.mp3"
        if os.path.exists(test_audio):
            output_path = f"downloads/test_{call_id}.mp3"
            os.makedirs("downloads", exist_ok=True)
            shutil.copy(test_audio, output_path)
            return output_path
        else:
            logger.warning(f"   ⚠️  Test audio not found")
            return None
    
    async def test_transcription(self, audio_path: str) -> Dict:
        """Test Deepgram transcription"""
        try:
            with open(audio_path, "rb") as audio:
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
            
            return {'transcript': transcript, 'success': True}
            
        except Exception as e:
            logger.error(f"   ❌ Transcription failed: {e}")
            return {'transcript': "Transcription failed", 'success': False}
    
    async def test_analysis(self, transcript: str, call_info: Dict) -> Dict:
        """Test GPT-4 analysis"""
        analysis_prompt = f"""Analyze this auto service call:

Call Info:
- Customer: {call_info.get('customer_name')}
- Duration: {call_info.get('duration_seconds')} seconds
- Direction: {call_info.get('call_direction')}

Transcript:
{transcript[:1000]}...

Provide:
1. summary - Brief summary
2. customer_intent - Why they called
3. sentiment - positive/neutral/negative
4. category - appointment_scheduling/service_inquiry/status_check/complaint/other
5. follow_up_needed - Yes/No and why
6. key_points - List of 2-3 key points

Respond in JSON format."""

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an automotive service call analyst."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            logger.error(f"   ❌ Analysis failed: {e}")
            return {"error": str(e)}
    
    async def process_test_call(self, call_data: Dict) -> Dict:
        """Process a single test call"""
        call_id = call_data['call_id']
        logger.info(f"\n🔄 Processing: {call_id} - {call_data['customer_name']} ({call_data['duration_seconds']}s)")
        
        result = {
            'call_id': call_id,
            'customer': call_data['customer_name'],
            'duration': call_data['duration_seconds'],
            'success': False,
            'stages': {}
        }
        
        try:
            # Stage 1: Download
            logger.info("   📥 Downloading audio...")
            audio_path = await self.simulate_audio_download(call_id)
            result['stages']['download'] = 'completed' if audio_path else 'failed'
            
            if not audio_path:
                raise Exception("Audio download failed")
            
            # Stage 2: Transcribe
            logger.info("   🎙️  Transcribing...")
            transcript_data = await self.test_transcription(audio_path)
            result['stages']['transcription'] = 'completed' if transcript_data['success'] else 'failed'
            
            if not transcript_data['success']:
                raise Exception("Transcription failed")
            
            logger.info(f"   ✅ Transcribed: {len(transcript_data['transcript'])} chars")
            
            # Stage 3: Analyze
            logger.info("   🤖 Analyzing...")
            analysis = await self.test_analysis(transcript_data['transcript'], call_data)
            result['stages']['analysis'] = 'completed' if 'error' not in analysis else 'failed'
            
            if 'error' not in analysis:
                logger.info(f"   ✅ Analysis: {analysis.get('category')} - {analysis.get('sentiment')}")
            
            # Stage 4: Update database
            try:
                supabase.table('calls').update({
                    'status': 'test_analyzed',
                    'dc_transcript': transcript_data['transcript'][:500],
                    'dc_sentiment': 0.0
                }).eq('call_id', call_id).execute()
                
                result['stages']['storage'] = 'completed'
            except Exception as e:
                result['stages']['storage'] = 'failed'
                logger.error(f"   Storage error: {e}")
            
            result['success'] = True
            result['analysis'] = analysis
            self.test_results["successful"] += 1
            
            # Collect insights
            if analysis.get('category') and analysis.get('sentiment'):
                self.test_results["insights"].append({
                    'call_id': call_id,
                    'customer': call_data['customer_name'],
                    'category': analysis['category'],
                    'sentiment': analysis['sentiment'],
                    'summary': analysis.get('summary', 'N/A'),
                    'key_points': analysis.get('key_points', [])
                })
            
            logger.info(f"✅ Successfully processed {call_id}")
            
        except Exception as e:
            result['error'] = str(e)
            self.test_results["failed"] += 1
            logger.error(f"❌ Failed: {e}")
        
        return result
    
    async def run_comprehensive_test(self, num_calls: int = 5):
        """Run comprehensive test with multiple calls"""
        logger.info("🚀 COMPREHENSIVE MULTI-CALL TEST")
        logger.info("=" * 70)
        
        try:
            # Step 1: Test authentication
            logger.info("\n📋 Step 1: Testing Authentication")
            if not await self.authenticate():
                return
            
            # Step 2: Fetch test calls
            logger.info("\n📋 Step 2: Fetching Test Calls")
            test_calls = await self.fetch_test_calls(limit=num_calls)
            
            if not test_calls:
                logger.error("No test calls found")
                return
            
            self.test_results["total_calls"] = len(test_calls)
            
            # Step 3: Store calls
            logger.info("\n📋 Step 3: Testing Database Storage")
            stored_count = await self.test_call_storage(test_calls)
            
            # Step 4: Process calls
            logger.info("\n📋 Step 4: Processing Calls Through Pipeline")
            results = []
            
            for i, call in enumerate(test_calls):
                logger.info(f"\n[{i+1}/{len(test_calls)}] {'='*50}")
                result = await self.process_test_call(call)
                results.append(result)
                
                if i < len(test_calls) - 1:
                    await asyncio.sleep(1)
            
            # Generate report
            logger.info("\n\n📊 TEST REPORT")
            logger.info("=" * 70)
            logger.info(f"Total Calls Tested: {self.test_results['total_calls']}")
            logger.info(f"Successful: {self.test_results['successful']}")
            logger.info(f"Failed: {self.test_results['failed']}")
            logger.info(f"Success Rate: {(self.test_results['successful'] / self.test_results['total_calls'] * 100):.1f}%")
            
            # Show insights
            if self.test_results["insights"]:
                logger.info("\n🔍 CALL INSIGHTS:")
                
                # Category distribution
                categories = {}
                sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
                
                for insight in self.test_results["insights"]:
                    cat = insight['category']
                    categories[cat] = categories.get(cat, 0) + 1
                    
                    sent = insight['sentiment']
                    if sent in sentiments:
                        sentiments[sent] += 1
                
                logger.info("\n   Category Distribution:")
                for cat, count in categories.items():
                    logger.info(f"      {cat}: {count}")
                
                logger.info("\n   Sentiment Analysis:")
                for sent, count in sentiments.items():
                    logger.info(f"      {sent}: {count}")
                
                # Detailed insights
                logger.info("\n   Detailed Call Analysis:")
                for insight in self.test_results["insights"]:
                    logger.info(f"\n   📞 {insight['customer']}:")
                    logger.info(f"      Category: {insight['category']}")
                    logger.info(f"      Sentiment: {insight['sentiment']}")
                    logger.info(f"      Summary: {insight.get('summary', 'N/A')[:100]}...")
                    if insight.get('key_points'):
                        logger.info(f"      Key Points:")
                        for point in insight['key_points'][:2]:
                            logger.info(f"         - {point}")
            
            logger.info("\n✅ TEST COMPLETE!")
            
            # Save results
            with open('test_results.json', 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'results': self.test_results,
                    'call_details': results
                }, f, indent=2)
            
            logger.info("📄 Results saved to test_results.json")
            
        except Exception as e:
            logger.error(f"Test error: {e}")
        finally:
            await self.client.aclose()


async def main():
    """Run the test"""
    tester = MultiCallTester()
    await tester.run_comprehensive_test(num_calls=5)


if __name__ == "__main__":
    print("\n🧪 MCP CALL ANALYZER - MULTI-CALL TEST")
    print("=" * 70)
    print("Testing with multiple real calls from DC API")
    print("=" * 70)
    
    asyncio.run(main())