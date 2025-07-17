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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_calls_status (status),
    INDEX idx_calls_created_at (created_at),
    INDEX idx_calls_call_id (call_id)
);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_calls_updated_at BEFORE UPDATE
    ON calls FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add RLS (Row Level Security) policies
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;

-- Policy for service role (your API)
CREATE POLICY "Service role can do everything" ON calls
    FOR ALL USING (true);

-- Optional: Add a view for call statistics
CREATE OR REPLACE VIEW call_statistics AS
SELECT 
    status,
    COUNT(*) as count,
    DATE(created_at) as date
FROM calls
GROUP BY status, DATE(created_at)
ORDER BY date DESC, status;

-- Add comment for documentation
COMMENT ON TABLE calls IS 'Stores automotive service call records with transcriptions and AI analysis';
COMMENT ON COLUMN calls.analysis IS 'JSON object containing GPT-4 analysis results including call_reason, vehicle_info, service_requested, sentiment, follow_up_required, priority, and summary';