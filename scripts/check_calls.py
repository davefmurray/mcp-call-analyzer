from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Get recent calls
print("Fetching recent calls from Supabase...")
result = supabase.table('calls').select('call_id, customer_name, date_created, status, has_recording').order('date_created', desc=True).limit(10).execute()

if result.data:
    print(f"\nFound {len(result.data)} recent calls:\n")
    for call in result.data:
        status = call.get('status', 'unknown')
        has_recording = call.get('has_recording', False)
        print(f"Call ID: {call['call_id']}")
        print(f"  Customer: {call.get('customer_name', 'N/A')}")
        print(f"  Date: {call.get('date_created', 'N/A')}")
        print(f"  Status: {status}")
        print(f"  Has Recording: {'Yes' if has_recording else 'No'}")
        print()
else:
    print("No calls found in the database.")