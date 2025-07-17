import httpx
import asyncio
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

async def test_audio_download():
    """Test downloading audio directly from Supabase storage"""
    
    # The URL we found
    audio_url = "https://xvfsqlcaqfmesuukolda.supabase.co/storage/v1/object/public/call-recordings/recordings/2025/07/687641b0d84270fd72808ef2_687641b0d84270fd72808ef2_REf2fb16e13e910ce0af19fd85ec3f8a38.mp3"
    
    print(f"Testing download from: {audio_url}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(audio_url, follow_redirects=True)
            response.raise_for_status()
            
            # Save the file
            filename = "test_download.mp3"
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ Successfully downloaded {file_size / 1024 / 1024:.2f} MB")
            print(f"✅ Saved as: {filename}")
            
            # Verify it's an MP3
            if response.content[:3] == b'ID3' or response.content[:2] == b'\xff\xfb':
                print("✅ File appears to be a valid MP3")
            else:
                print("⚠️  File may not be a valid MP3")
                
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False

async def get_audio_url_from_supabase(call_id: str):
    """Get audio URL for a call from Supabase"""
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # Query for the audio URL
    result = supabase.table('recordings').select('storage_url').eq('call_id', call_id).execute()
    
    if result.data and result.data[0].get('storage_url'):
        return result.data[0]['storage_url']
    
    # If not in recordings table, check if we can construct it
    call_result = supabase.table('calls').select('dc_call_id').eq('call_id', call_id).execute()
    if call_result.data:
        dc_call_id = call_result.data[0].get('dc_call_id')
        if dc_call_id:
            # Try the storage pattern we found
            base_url = "https://xvfsqlcaqfmesuukolda.supabase.co/storage/v1/object/public/call-recordings"
            # This is a guess based on the pattern
            potential_url = f"{base_url}/recordings/2025/07/{dc_call_id}_{dc_call_id}_*.mp3"
            return potential_url
    
    return None

if __name__ == "__main__":
    # Test direct download
    asyncio.run(test_audio_download())
    
    # Test getting URL for a different call
    print("\n=== Testing URL retrieval for another call ===")
    test_call_id = "6876427ad84270fd72808f2a"  # Jasper Camacho
    url = asyncio.run(get_audio_url_from_supabase(test_call_id))
    if url:
        print(f"Found URL: {url}")
    else:
        print("No URL found")