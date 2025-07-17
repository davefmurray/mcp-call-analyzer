import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Get sample call to see structure
result = supabase.table('calls').select('*').limit(1).execute()

if result.data:
    print("Calls table columns:")
    for key in result.data[0].keys():
        print(f"  - {key}")
else:
    print("No data in calls table")