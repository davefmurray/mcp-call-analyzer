import httpx
import asyncio
import sys

async def test_process_call(call_id: str):
    """Test processing a single call"""
    async with httpx.AsyncClient() as client:
        print(f"Testing with call ID: {call_id}")
        
        try:
            response = await client.post(
                "http://localhost:8000/process-single-call",
                json={"call_id": call_id},
                timeout=300.0  # 5 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ Success!")
                print(f"Call ID: {result['call_id']}")
                print(f"Audio URL: {result['audio_url']}")
                print(f"\nTranscription Preview:")
                print(result['transcription_preview'])
            else:
                print(f"\n❌ Error: {response.status_code}")
                print(response.json())
                
        except Exception as e:
            print(f"\n❌ Exception: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_call.py <call_id>")
        print("Example: python test_call.py 123456")
        sys.exit(1)
        
    call_id = sys.argv[1]
    asyncio.run(test_process_call(call_id))