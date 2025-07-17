-- MCP Call Analyzer Database Schema
-- Database: PostgreSQL (Supabase)
-- Version: 1.0.0

-- =====================================================
-- CALLS TABLE
-- Stores call metadata and processing status
-- =====================================================
CREATE TABLE IF NOT EXISTS calls (
    -- Primary identifier from Twilio
    call_id VARCHAR(50) PRIMARY KEY,
    
    -- Digital Concierge internal ID
    dc_call_id VARCHAR(50) UNIQUE,
    
    -- Customer information
    customer_name VARCHAR(255),
    customer_number VARCHAR(20),
    
    -- Call details
    call_direction VARCHAR(20) CHECK (call_direction IN ('inbound', 'outbound')),
    duration_seconds INTEGER CHECK (duration_seconds >= 0),
    date_created TIMESTAMP WITH TIME ZONE,
    
    -- Recording status
    has_recording BOOLEAN DEFAULT false,
    
    -- Processing status
    status VARCHAR(50) DEFAULT 'pending_download' 
        CHECK (status IN (
            'pending_download', 
            'downloading', 
            'downloaded',
            'transcribing',
            'transcribed',
            'analyzing',
            'analyzed',
            'error',
            'download_failed',
            'transcription_failed',
            'analysis_failed'
        )),
    
    -- Transcription data
    dc_transcript TEXT,
    dc_sentiment NUMERIC(3,2) CHECK (dc_sentiment >= -1 AND dc_sentiment <= 1),
    
    -- Additional metadata
    extension VARCHAR(10),
    error_message TEXT,
    download_status VARCHAR(50),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_calls_status ON calls(status);
CREATE INDEX idx_calls_date_created ON calls(date_created);
CREATE INDEX idx_calls_customer_number ON calls(customer_number);
CREATE INDEX idx_calls_dc_call_id ON calls(dc_call_id);

-- =====================================================
-- RECORDINGS TABLE
-- Stores audio file information
-- =====================================================
CREATE TABLE IF NOT EXISTS recordings (
    id SERIAL PRIMARY KEY,
    
    -- Foreign key to calls table
    call_id VARCHAR(50) REFERENCES calls(call_id) ON DELETE CASCADE,
    
    -- File information
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT,
    mime_type VARCHAR(50) DEFAULT 'audio/mpeg',
    
    -- Storage information
    storage_path VARCHAR(500),
    storage_url TEXT,
    
    -- Upload status
    upload_status VARCHAR(50) DEFAULT 'pending'
        CHECK (upload_status IN ('pending', 'uploading', 'completed', 'failed')),
    
    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one recording per call
    UNIQUE(call_id)
);

-- Index for foreign key
CREATE INDEX idx_recordings_call_id ON recordings(call_id);

-- =====================================================
-- TRANSCRIPTIONS TABLE
-- Stores detailed transcription data
-- =====================================================
CREATE TABLE IF NOT EXISTS transcriptions (
    id SERIAL PRIMARY KEY,
    
    -- Foreign key to calls table
    call_id VARCHAR(50) REFERENCES calls(call_id) ON DELETE CASCADE,
    
    -- Full transcript
    transcript TEXT NOT NULL,
    
    -- Speaker diarization data (JSON array)
    speaker_segments JSONB,
    
    -- Transcription metadata
    confidence_score NUMERIC(3,2),
    language_code VARCHAR(10) DEFAULT 'en-US',
    model_used VARCHAR(50) DEFAULT 'nova-2',
    
    -- Processing information
    processing_time_ms INTEGER,
    word_count INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one transcription per call
    UNIQUE(call_id)
);

-- Index for foreign key
CREATE INDEX idx_transcriptions_call_id ON transcriptions(call_id);

-- =====================================================
-- CALL_ANALYSIS TABLE
-- Stores AI analysis results
-- =====================================================
CREATE TABLE IF NOT EXISTS call_analysis (
    id SERIAL PRIMARY KEY,
    
    -- Foreign key to calls table
    call_id VARCHAR(50) REFERENCES calls(call_id) ON DELETE CASCADE,
    
    -- Analysis data (JSON)
    analysis_data JSONB NOT NULL,
    
    -- Extracted key fields for easier querying
    category VARCHAR(50) GENERATED ALWAYS AS (analysis_data->>'category') STORED,
    sentiment VARCHAR(20) GENERATED ALWAYS AS (analysis_data->>'sentiment') STORED,
    customer_intent TEXT GENERATED ALWAYS AS (analysis_data->>'customer_intent') STORED,
    follow_up_needed BOOLEAN GENERATED ALWAYS AS ((analysis_data->>'follow_up_needed')::boolean) STORED,
    
    -- Analysis metadata
    model_used VARCHAR(50) DEFAULT 'gpt-4-turbo-preview',
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_analysis_call_id ON call_analysis(call_id);
CREATE INDEX idx_analysis_category ON call_analysis(category);
CREATE INDEX idx_analysis_sentiment ON call_analysis(sentiment);
CREATE INDEX idx_analysis_follow_up ON call_analysis(follow_up_needed);

-- GIN index for JSONB queries
CREATE INDEX idx_analysis_data_gin ON call_analysis USING GIN (analysis_data);

-- =====================================================
-- PROCESSING_QUEUE TABLE
-- Manages call processing queue
-- =====================================================
CREATE TABLE IF NOT EXISTS processing_queue (
    id SERIAL PRIMARY KEY,
    
    -- Call reference
    call_id VARCHAR(50) REFERENCES calls(call_id) ON DELETE CASCADE,
    
    -- Queue management
    priority INTEGER DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    status VARCHAR(50) DEFAULT 'queued'
        CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')),
    
    -- Processing details
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Worker information
    worker_id VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for queue management
CREATE INDEX idx_queue_status_priority ON processing_queue(status, priority DESC);
CREATE INDEX idx_queue_call_id ON processing_queue(call_id);

-- =====================================================
-- ANALYTICS_SUMMARY TABLE
-- Pre-computed analytics for dashboard
-- =====================================================
CREATE TABLE IF NOT EXISTS analytics_summary (
    id SERIAL PRIMARY KEY,
    
    -- Time period
    date DATE NOT NULL,
    hour INTEGER CHECK (hour >= 0 AND hour <= 23),
    
    -- Call metrics
    total_calls INTEGER DEFAULT 0,
    total_duration_seconds INTEGER DEFAULT 0,
    avg_duration_seconds NUMERIC(10,2),
    
    -- Direction breakdown
    inbound_calls INTEGER DEFAULT 0,
    outbound_calls INTEGER DEFAULT 0,
    
    -- Sentiment breakdown
    positive_calls INTEGER DEFAULT 0,
    neutral_calls INTEGER DEFAULT 0,
    negative_calls INTEGER DEFAULT 0,
    
    -- Category breakdown (JSON)
    category_counts JSONB DEFAULT '{}',
    
    -- Processing metrics
    successfully_processed INTEGER DEFAULT 0,
    failed_processing INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint for time period
    UNIQUE(date, hour)
);

-- Indexes for analytics queries
CREATE INDEX idx_analytics_date ON analytics_summary(date);
CREATE INDEX idx_analytics_date_hour ON analytics_summary(date, hour);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at columns
CREATE TRIGGER update_calls_updated_at BEFORE UPDATE ON calls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_queue_updated_at BEFORE UPDATE ON processing_queue
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_updated_at BEFORE UPDATE ON analytics_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update analytics summary
CREATE OR REPLACE FUNCTION update_analytics_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Update analytics when a call is analyzed
    IF NEW.status = 'analyzed' AND OLD.status != 'analyzed' THEN
        INSERT INTO analytics_summary (
            date,
            hour,
            total_calls,
            total_duration_seconds,
            inbound_calls,
            outbound_calls
        )
        VALUES (
            DATE(NEW.date_created),
            EXTRACT(HOUR FROM NEW.date_created),
            1,
            NEW.duration_seconds,
            CASE WHEN NEW.call_direction = 'inbound' THEN 1 ELSE 0 END,
            CASE WHEN NEW.call_direction = 'outbound' THEN 1 ELSE 0 END
        )
        ON CONFLICT (date, hour) DO UPDATE SET
            total_calls = analytics_summary.total_calls + 1,
            total_duration_seconds = analytics_summary.total_duration_seconds + NEW.duration_seconds,
            inbound_calls = analytics_summary.inbound_calls + 
                CASE WHEN NEW.call_direction = 'inbound' THEN 1 ELSE 0 END,
            outbound_calls = analytics_summary.outbound_calls + 
                CASE WHEN NEW.call_direction = 'outbound' THEN 1 ELSE 0 END;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for analytics updates
CREATE TRIGGER update_analytics_on_call_analyzed
    AFTER UPDATE ON calls
    FOR EACH ROW
    WHEN (NEW.status = 'analyzed' AND OLD.status != 'analyzed')
    EXECUTE FUNCTION update_analytics_summary();

-- =====================================================
-- VIEWS
-- =====================================================

-- View for call details with all related data
CREATE OR REPLACE VIEW v_call_details AS
SELECT 
    c.*,
    r.file_name,
    r.storage_url,
    r.upload_status,
    t.transcript,
    t.confidence_score,
    t.word_count,
    a.analysis_data,
    a.category,
    a.sentiment,
    a.customer_intent,
    a.follow_up_needed
FROM calls c
LEFT JOIN recordings r ON c.call_id = r.call_id
LEFT JOIN transcriptions t ON c.call_id = t.call_id
LEFT JOIN call_analysis a ON c.call_id = a.call_id;

-- View for pending calls
CREATE OR REPLACE VIEW v_pending_calls AS
SELECT 
    c.*,
    CASE 
        WHEN c.status = 'pending_download' THEN 1
        WHEN c.status = 'download_failed' THEN 2
        WHEN c.status = 'transcription_failed' THEN 3
        WHEN c.status = 'analysis_failed' THEN 4
        ELSE 5
    END as priority_order
FROM calls c
WHERE c.status IN ('pending_download', 'download_failed', 'transcription_failed', 'analysis_failed')
ORDER BY priority_order, c.date_created DESC;

-- View for daily analytics
CREATE OR REPLACE VIEW v_daily_analytics AS
SELECT 
    date,
    SUM(total_calls) as total_calls,
    SUM(total_duration_seconds) as total_duration_seconds,
    AVG(total_duration_seconds::numeric / NULLIF(total_calls, 0)) as avg_duration_seconds,
    SUM(inbound_calls) as inbound_calls,
    SUM(outbound_calls) as outbound_calls,
    SUM(positive_calls) as positive_calls,
    SUM(neutral_calls) as neutral_calls,
    SUM(negative_calls) as negative_calls,
    SUM(successfully_processed) as successfully_processed,
    SUM(failed_processing) as failed_processing
FROM analytics_summary
GROUP BY date
ORDER BY date DESC;

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable if using Supabase Auth
-- =====================================================

-- Enable RLS on tables
-- ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE recordings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transcriptions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE call_analysis ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- PERMISSIONS
-- Grant permissions to service role
-- =====================================================

-- Grant all permissions to service role
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
-- GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO service_role;