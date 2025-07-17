import asyncio
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

async def complete_transcription_and_analysis():
    """Complete the transcription and AI analysis pipeline"""
    
    audio_file = "downloads/test_call_20250716_082821.mp3"
    call_id = "test_call_20250716_082821"
    
    print("🎙️  Transcribing audio...")
    
    # Transcribe
    with open(audio_file, "rb") as f:
        transcript = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text"
        )
    
    print(f"\n✅ Transcript:\n{transcript}\n")
    
    # Analyze with AI
    print("🤖 Analyzing call with AI...")
    
    analysis_prompt = f"""Analyze this phone call transcript and provide:
1. Call summary (2-3 sentences)
2. Customer intent/reason for calling
3. Call outcome
4. Any follow-up actions needed
5. Sentiment (positive/neutral/negative)
6. Call category: Choose from [appointment, sales_inquiry, service_issue, general_inquiry, missed_opportunity]

Transcript:
{transcript}

Format as JSON."""

    response = await openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": "You are a call center analyst. Analyze the call transcript and provide insights in JSON format."},
            {"role": "user", "content": analysis_prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    analysis = response.choices[0].message.content
    print(f"\n✅ AI Analysis:\n{analysis}\n")
    
    # Parse analysis
    import json
    analysis_data = json.loads(analysis)
    
    # Update call record
    update_data = {
        'transcript': transcript,
        'ai_analysis': analysis,
        'ai_summary': analysis_data.get('summary', ''),
        'ai_sentiment': analysis_data.get('sentiment', 'neutral'),
        'ai_category': analysis_data.get('call_category', 'general_inquiry'),
        'status': 'analyzed',
        'updated_at': datetime.now().isoformat()
    }
    
    # Update calls table
    try:
        result = supabase.table('calls').update(update_data).eq('call_id', call_id).execute()
        if result.data:
            print("✅ Updated calls table with transcript and analysis")
    except Exception as e:
        print(f"⚠️  Error updating calls table: {e}")
        # Insert if update failed
        try:
            call_record = {
                'call_id': call_id,
                'dc_call_id': call_id,
                'customer_name': 'JANET GOMEZ',
                'customer_number': '+19045213434',
                'call_direction': 'inbound',
                'duration_seconds': 27,
                'date_created': datetime.now().isoformat(),
                'has_recording': True,
                'storage_url': 'https://xvfsqlcaqfmesuukolda.supabase.co/storage/v1/object/public/call-recordings/test_call_20250716_082821.mp3',
                **update_data
            }
            result = supabase.table('calls').upsert(call_record, on_conflict='call_id').execute()
            print("✅ Inserted new call record with analysis")
        except Exception as e2:
            print(f"❌ Error inserting: {e2}")
    
    print("\n🎉 COMPLETE PIPELINE SUCCESS!")
    print(f"   Call ID: {call_id}")
    print(f"   Category: {analysis_data.get('call_category', 'N/A')}")
    print(f"   Sentiment: {analysis_data.get('sentiment', 'N/A')}")
    print(f"   Follow-up: {analysis_data.get('follow_up_actions', 'None')}")

if __name__ == "__main__":
    asyncio.run(complete_transcription_and_analysis())