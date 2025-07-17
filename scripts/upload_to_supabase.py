import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

def upload_audio_to_supabase():
    """Upload audio file to the correct Supabase storage bucket"""
    
    # The correct bucket name based on existing recordings
    bucket_name = "call-recordings"
    
    audio_file = "downloads/test_call_20250716_082821.mp3"
    call_id = "test_call_20250716_082821"
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file not found: {audio_file}")
        return
    
    print(f"📤 Uploading {audio_file} to Supabase...")
    
    with open(audio_file, "rb") as f:
        file_data = f.read()
        file_size = len(file_data)
        print(f"File size: {file_size:,} bytes")
        
        # Create storage path similar to existing recordings
        # Pattern: recordings/YYYY/MM/callid_callid_recordingid.mp3
        now = datetime.now()
        storage_path = f"recordings/{now.year}/{now.month:02d}/{call_id}_{call_id}_RE{call_id}.mp3"
        
        try:
            # Upload file
            result = supabase.storage.from_(bucket_name).upload(
                storage_path,
                file_data,
                {"content-type": "audio/mpeg"}
            )
            
            # Get public URL
            public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)
            
            print(f"\n✅ Upload successful!")
            print(f"Storage path: {storage_path}")
            print(f"Public URL: {public_url}")
            
            # Update or insert into recordings table
            recording_data = {
                'call_id': call_id,
                'dc_call_id': call_id,
                'storage_url': public_url,
                'storage_path': storage_path,
                'bucket_name': bucket_name,
                'file_size': file_size,
                'duration_seconds': 27,
                'created_at': now.isoformat()
            }
            
            # Insert into recordings table
            try:
                # First check if record exists
                existing = supabase.table('recordings').select("*").eq('call_id', call_id).execute()
                
                if existing.data:
                    # Update existing record
                    result = supabase.table('recordings').update(recording_data).eq('call_id', call_id).execute()
                    print("✅ Updated recordings table")
                else:
                    # Insert new record
                    result = supabase.table('recordings').insert(recording_data).execute()
                    print("✅ Inserted into recordings table")
            except Exception as e:
                print(f"⚠️  Error with recordings table: {e}")
            
            # Also update calls table
            update_result = supabase.table('calls').update({
                'storage_url': public_url,
                'has_recording': True,
                'status': 'uploaded'
            }).eq('call_id', call_id).execute()
            
            if update_result.data:
                print("✅ Updated calls table")
            
            print(f"\n🎉 SUCCESS! Audio uploaded and ready for transcription")
            print(f"   Call ID: {call_id}")
            print(f"   URL: {public_url}")
            
        except Exception as e:
            print(f"❌ Error uploading: {e}")
            
            # Try alternative approach - direct to bucket root
            try:
                simple_path = f"{call_id}.mp3"
                result = supabase.storage.from_(bucket_name).upload(
                    simple_path,
                    file_data,
                    {"content-type": "audio/mpeg"}
                )
                
                public_url = supabase.storage.from_(bucket_name).get_public_url(simple_path)
                print(f"\n✅ Uploaded with simple path: {simple_path}")
                print(f"Public URL: {public_url}")
                
            except Exception as e2:
                print(f"❌ Alternative upload also failed: {e2}")

if __name__ == "__main__":
    upload_audio_to_supabase()