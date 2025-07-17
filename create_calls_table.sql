-- MCP Call Analyzer - Database Schema
-- Run this in Supabase SQL Editor

-- Drop table if you need to recreate it (WARNING: This will delete all data!)
-- DROP TABLE IF EXISTS calls CASCADE;

-- Create calls table
CREATE TABLE IF NOT EXISTS calls (
    id SERIAL PRIMARY KEY,
    call_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    customer_name TEXT,
    customer_number TEXT,
    recording_url TEXT,
    transcript TEXT,
    analysis JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Add constraint for status values
    CONSTRAINT valid_status CHECK (status IN ('queued', 'processing', 'completed', 'failed'))
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at);
CREATE INDEX IF NOT EXISTS idx_calls_call_id ON calls(call_id);

-- Create function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS update_calls_updated_at ON calls;
CREATE TRIGGER update_calls_updated_at 
    BEFORE UPDATE ON calls 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Enable RLS
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;

-- Create policy for service role
DROP POLICY IF EXISTS "Service role full access" ON calls;
CREATE POLICY "Service role full access" ON calls
    FOR ALL 
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Create a view for statistics
CREATE OR REPLACE VIEW call_statistics AS
SELECT 
    status,
    COUNT(*) as count,
    DATE(created_at) as date
FROM calls
GROUP BY status, DATE(created_at)
ORDER BY date DESC, status;

-- Verify table was created
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'calls'
ORDER BY ordinal_position;