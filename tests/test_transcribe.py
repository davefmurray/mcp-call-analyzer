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

async def transcribe_audio():
    """Test transcribing the downloaded audio file"""
    
    audio_file = "downloads/test_call_20250716_082821.mp3"
    call_id = "test_call_20250716_082821"
    
    print(f"Transcribing {audio_file}...")
    
    try:
        # Open and transcribe the audio file
        with open(audio_file, "rb") as f:
            transcript = await openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
        
        print(f"\n✅ Transcription successful!")
        print(f"\nTranscript:\n{transcript}")
        
        # Update call record with transcript
        update_data = {
            'transcript': transcript,
            'status': 'transcribed',
            'transcribed_at': datetime.now().isoformat()
        }
        
        result = supabase.table('calls').update(update_data).eq('call_id', call_id).execute()
        
        if result.data:
            print(f"\n✅ Updated call record with transcript")
        
        # Now analyze with AI
        print("\n📊 Analyzing call with AI...")
        
        analysis_prompt = f"""Analyze this phone call transcript and provide:
1. Call summary (2-3 sentences)
2. Customer intent/reason for calling
3. Call outcome
4. Any follow-up actions needed
5. Sentiment (positive/neutral/negative)
6. Call category (appointment, sales_inquiry, service_issue, general_inquiry, missed_opportunity)

Transcript:
{transcript}
"""
        
        response = await openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a call center analyst. Analyze the call transcript and provide insights."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3
        )
        
        analysis = response.choices[0].message.content
        print(f"\nAI Analysis:\n{analysis}")
        
        # Update with analysis
        update_data = {
            'ai_analysis': analysis,
            'status': 'analyzed',
            'analyzed_at': datetime.now().isoformat()
        }
        
        result = supabase.table('calls').update(update_data).eq('call_id', call_id).execute()
        
        print(f"\n✅ Complete! Call {call_id} has been fully processed.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check if it's an API key issue
        if "401" in str(e) or "api_key" in str(e).lower():
            print("\n⚠️  OpenAI API key appears to be invalid. Please check your OPENAI_API_KEY environment variable.")

if __name__ == "__main__":
    asyncio.run(transcribe_audio())