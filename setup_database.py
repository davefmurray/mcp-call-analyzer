#!/usr/bin/env python3
"""
Setup database schema for MCP Call Analyzer
Run this script to create the calls table in Supabase
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Create the calls table and related database objects"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        sys.exit(1)
    
    print("🔄 Connecting to Supabase...")
    supabase = create_client(supabase_url, supabase_key)
    
    # SQL to create the calls table
    create_table_sql = """
    -- Create calls table for MCP Call Analyzer
    CREATE TABLE IF NOT EXISTS calls (
        id SERIAL PRIMARY KEY,
        call_id TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
        
        -- Customer information
        customer_name TEXT,
        customer_number TEXT,
        
        -- Call data
        recording_url TEXT,
        transcript TEXT,
        
        -- AI Analysis (JSONB for flexibility)
        analysis JSONB DEFAULT '{}',
        
        -- Timestamps
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
    CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at);
    CREATE INDEX IF NOT EXISTS idx_calls_call_id ON calls(call_id);
    
    -- Create updated_at trigger
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    DROP TRIGGER IF EXISTS update_calls_updated_at ON calls;
    CREATE TRIGGER update_calls_updated_at BEFORE UPDATE
        ON calls FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    -- Add RLS (Row Level Security) policies
    ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
    
    -- Drop existing policy if it exists
    DROP POLICY IF EXISTS "Service role can do everything" ON calls;
    
    -- Policy for service role (your API)
    CREATE POLICY "Service role can do everything" ON calls
        FOR ALL USING (true);
    
    -- Create or replace view for call statistics
    CREATE OR REPLACE VIEW call_statistics AS
    SELECT 
        status,
        COUNT(*) as count,
        DATE(created_at) as date
    FROM calls
    GROUP BY status, DATE(created_at)
    ORDER BY date DESC, status;
    
    -- Add comments for documentation
    COMMENT ON TABLE calls IS 'Stores automotive service call records with transcriptions and AI analysis';
    COMMENT ON COLUMN calls.analysis IS 'JSON object containing GPT-4 analysis results';
    """
    
    try:
        print("📦 Creating calls table...")
        # Note: Supabase Python client doesn't have direct SQL execution
        # You'll need to run this SQL in Supabase dashboard
        
        print("\n⚠️  IMPORTANT: The Supabase Python client doesn't support direct SQL execution.")
        print("Please run the following SQL in your Supabase SQL Editor:\n")
        print("1. Go to: https://app.supabase.com/project/xvfsqlcaqfmesuukolda/editor")
        print("2. Copy and paste the SQL from: supabase/migrations/001_create_calls_table.sql")
        print("3. Click 'Run' to execute\n")
        
        # Test if table exists by trying to query it
        print("🔍 Checking if calls table exists...")
        result = supabase.table("calls").select("*").limit(1).execute()
        print("✅ Calls table exists and is accessible!")
        
        # Show current stats
        stats = supabase.table("calls").select("status", count="exact").execute()
        if stats.data:
            print(f"\n📊 Current database stats:")
            print(f"   Total calls: {len(stats.data)}")
            status_counts = {}
            for call in stats.data:
                status = call.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            for status, count in status_counts.items():
                print(f"   - {status}: {count}")
                
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            print("\n❌ Table 'calls' does not exist yet.")
            print("📋 Please create it using the SQL above in Supabase dashboard.")
            
            # Save SQL to file for easy access
            sql_file = "create_calls_table.sql"
            with open(sql_file, "w") as f:
                f.write(create_table_sql)
            print(f"\n💾 SQL saved to: {sql_file}")
            print("   You can copy this file's contents to Supabase SQL Editor")
        else:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    setup_database()