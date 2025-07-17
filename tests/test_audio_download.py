import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import httpx
import re

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

async def test_download():
    """Test downloading audio from a known URL"""
    
    # The audio URL we captured earlier
    audio_url = "https://d3vneafawyd5u6.cloudfront.net/Recordings/RE85041f093ee6e183671ab3314e7cf63d.mp3?Expires=1752754964&Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9kM3ZuZWFmYXd5ZDV1Ni5jbG91ZGZyb250Lm5ldC9SZWNvcmRpbmdzL1JFODUwNDFmMDkzZWU2ZTE4MzY3MWFiMzMxNGU3Y2Y2M2QubXAzIiwiQ29uZGl0aW9uIjp7IkRhdGVMZXNzVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzUyNzU0OTY0fX19XX0_&Signature=D-ntvGtqizg4rXQNhFgbSnM2oqU14ty4VfQP-ClswWPOpXXkoLwlty1iar5qwdY-DA643vvN0SxtFBsa2fuidiiT3vVA7kykK11a0OHxcoIOumu2ikirJQIdY-kfCYc4ZxzKDMz6mNVLnQzI0w-dFRPE29P7sce7UE3RsfJpQK9S~E-1tobYafdVwx~RBSaxO4TK9ArXUxnCchtK7H-DA~fZwmHAU8qIYk9JdZ4NGyS0ChNPaEXwHoba0D4eiHwolk0DnpYpBnNx1QjXUy0eM-qqkV~02N6PFouP8hn~wM2t40wBOtGdw9iWkKZ~AkIFBrtpRmJBtJh5rGIf1j4iZQ__&Key-Pair-Id=APKAI5363VKSN7NBGP5A"
    
    call_id = f"test_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"Testing download for call {call_id}...")
    print(f"Audio URL: {audio_url[:100]}...")
    
    # Download the audio
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(audio_url, follow_redirects=True, timeout=30.0)
            
            if response.status_code == 200:
                # Save locally
                audio_path = f"downloads/{call_id}.mp3"
                os.makedirs("downloads", exist_ok=True)
                
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                
                file_size = len(response.content)
                print(f"✅ Audio downloaded: {audio_path}")
                print(f"   File size: {file_size:,} bytes")
                
                # Upload to Supabase storage
                print("\nUploading to Supabase storage...")
                with open(audio_path, "rb") as f:
                    storage_path = f"recordings/{call_id}.mp3"
                    
                    # Check if bucket exists
                    try:
                        # Try to create bucket if it doesn't exist
                        supabase.storage.create_bucket("audio-recordings", {"public": True})
                        print("Created audio-recordings bucket")
                    except:
                        print("Bucket already exists or couldn't be created")
                    
                    # Upload file
                    try:
                        result = supabase.storage.from_("audio-recordings").upload(
                            storage_path,
                            f.read(),
                            {"content-type": "audio/mpeg"}
                        )
                        
                        storage_url = supabase.storage.from_("audio-recordings").get_public_url(storage_path)
                        print(f"✅ Uploaded to Supabase: {storage_url}")
                        
                        # Insert call record
                        call_record = {
                            'call_id': call_id,
                            'dc_call_id': call_id,
                            'customer_name': 'JANET GOMEZ',
                            'customer_number': '+19045213434',
                            'call_direction': 'inbound',
                            'duration_seconds': 27,
                            'date_created': datetime.now().isoformat(),
                            'has_recording': True,
                            'storage_url': storage_url,
                            'audio_url': audio_url,
                            'status': 'downloaded'
                        }
                        
                        result = supabase.table('calls').upsert(call_record, on_conflict='call_id').execute()
                        print(f"✅ Call record inserted: {call_id}")
                        
                        print(f"\n✅ SUCCESS! Call {call_id} is ready for transcription")
                        print(f"   Local file: {audio_path}")
                        print(f"   Storage URL: {storage_url}")
                        
                    except Exception as e:
                        print(f"❌ Error uploading to Supabase: {e}")
                        
            else:
                print(f"❌ Failed to download audio: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error downloading: {e}")

if __name__ == "__main__":
    asyncio.run(test_download())