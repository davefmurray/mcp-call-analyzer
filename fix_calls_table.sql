-- Fix the existing calls table to work with MCP Call Analyzer v2.1.0
-- This adds the missing columns and constraints our app expects

-- First, let's check what columns are missing
-- The app expects: call_id (unique), status, customer_name, customer_number, 
-- recording_url, transcript, analysis, created_at, updated_at

-- Add missing columns if they don't exist
ALTER TABLE calls 
ADD COLUMN IF NOT EXISTS transcript TEXT;

ALTER TABLE calls 
ADD COLUMN IF NOT EXISTS analysis JSONB DEFAULT '{}';

ALTER TABLE calls 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- The status column exists but might not have constraints
-- First drop any existing constraint
ALTER TABLE calls 
DROP CONSTRAINT IF EXISTS valid_status;

-- Add the constraint our app expects
ALTER TABLE calls 
ADD CONSTRAINT valid_status CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'pending_download', 'analyzed'));

-- Make call_id unique if it isn't already
-- First check if constraint exists, then add if needed
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'calls_call_id_key' 
        AND conrelid = 'calls'::regclass
    ) THEN
        ALTER TABLE calls ADD CONSTRAINT calls_call_id_key UNIQUE (call_id);
    END IF;
END $$;

-- Create or update the trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_calls_updated_at ON calls;
CREATE TRIGGER update_calls_updated_at 
    BEFORE UPDATE ON calls 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status);
CREATE INDEX IF NOT EXISTS idx_calls_created_at ON calls(created_at);
CREATE INDEX IF NOT EXISTS idx_calls_call_id ON calls(call_id);

-- Test that our app can now insert data
-- This is what the app tries to insert:
/*
INSERT INTO calls (
    call_id, 
    status, 
    customer_name, 
    customer_number, 
    recording_url, 
    created_at
) VALUES (
    'test-schema-fix', 
    'queued', 
    'Test Customer', 
    '555-1234', 
    'https://example.com/test.mp3', 
    NOW()
);
*/

-- Verify the fix worked
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'calls' 
AND column_name IN ('call_id', 'status', 'customer_name', 'customer_number', 
                    'recording_url', 'transcript', 'analysis', 'created_at', 'updated_at')
ORDER BY column_name;