import os
from dotenv import load_dotenv
from supabase import create_client
import asyncio

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

async def setup_storage_and_upload():
    """Set up Supabase storage bucket and upload test audio"""
    
    print("🔧 Setting up Supabase storage...")
    
    # List existing buckets
    try:
        buckets = supabase.storage.list_buckets()
        print(f"\nExisting buckets: {[b['name'] for b in buckets]}")
    except Exception as e:
        print(f"Error listing buckets: {e}")
        buckets = []
    
    # Check if audio-recordings bucket exists
    bucket_exists = any(b['name'] == 'audio-recordings' for b in buckets)
    
    if not bucket_exists:
        print("\nCreating 'audio-recordings' bucket...")
        try:
            result = supabase.storage.create_bucket(
                "audio-recordings",
                {
                    "public": True,
                    "file_size_limit": 52428800,  # 50MB
                    "allowed_mime_types": ["audio/mpeg", "audio/mp3", "audio/wav", "audio/m4a"]
                }
            )
            print("✅ Bucket created successfully!")
        except Exception as e:
            print(f"❌ Error creating bucket: {e}")
            # Try with recordings bucket (from the table structure)
            try:
                result = supabase.storage.create_bucket("recordings", {"public": True})
                print("✅ Created 'recordings' bucket instead")
                bucket_name = "recordings"
            except:
                print("Using existing bucket")
                bucket_name = "recordings"
    else:
        print("✅ Bucket already exists")
        bucket_name = "audio-recordings"
    
    # Upload test audio file
    audio_file = "downloads/test_call_20250716_082821.mp3"
    
    if os.path.exists(audio_file):
        print(f"\n📤 Uploading {audio_file}...")
        
        with open(audio_file, "rb") as f:
            file_data = f.read()
            file_size = len(file_data)
            print(f"File size: {file_size:,} bytes")
            
            # Try uploading to the appropriate bucket
            for bucket in ["recordings", "audio-recordings"]:
                try:
                    storage_path = f"calls/test_call_20250716_082821.mp3"
                    
                    # Check if file already exists and delete it
                    try:
                        supabase.storage.from_(bucket).remove([storage_path])
                        print(f"Removed existing file from {bucket}")
                    except:
                        pass
                    
                    # Upload new file
                    result = supabase.storage.from_(bucket).upload(
                        storage_path,
                        file_data,
                        {"content-type": "audio/mpeg", "upsert": "true"}
                    )
                    
                    # Get public URL
                    public_url = supabase.storage.from_(bucket).get_public_url(storage_path)
                    
                    print(f"\n✅ Upload successful to '{bucket}' bucket!")
                    print(f"Storage path: {storage_path}")
                    print(f"Public URL: {public_url}")
                    
                    # Update the call record with storage URL
                    update_result = supabase.table('calls').update({
                        'storage_url': public_url,
                        'storage_bucket': bucket,
                        'storage_path': storage_path
                    }).eq('call_id', 'test_call_20250716_082821').execute()
                    
                    if update_result.data:
                        print("✅ Updated call record with storage URL")
                    
                    break
                    
                except Exception as e:
                    print(f"❌ Error uploading to {bucket}: {e}")
    else:
        print(f"❌ Audio file not found: {audio_file}")
    
    print("\n📊 Storage setup complete!")
    
    # Show what's in the recordings table
    print("\n📋 Current recordings in database:")
    try:
        recordings = supabase.table('recordings').select('*').limit(5).execute()
        if recordings.data:
            for rec in recordings.data:
                print(f"- {rec.get('call_id', 'N/A')}: {rec.get('storage_url', 'No URL')}")
        else:
            print("No recordings found in recordings table")
    except Exception as e:
        print(f"Error querying recordings: {e}")

if __name__ == "__main__":
    asyncio.run(setup_storage_and_upload())