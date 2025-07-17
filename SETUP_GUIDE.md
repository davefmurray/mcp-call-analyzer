# MCP Call Analyzer - Complete Setup Guide

This guide will walk you through setting up the MCP Call Analyzer from scratch.

## 📋 Prerequisites

Before starting, ensure you have:

- **Python 3.9+** installed
- **Git** for version control
- **Chrome/Chromium** browser
- **PostgreSQL** database (we'll use Supabase)
- **API Keys** from:
  - OpenAI (GPT-4 access)
  - Deepgram (for transcription)
  - Digital Concierge dashboard credentials

## 🚀 Step 1: Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-call-analyzer.git
cd mcp-call-analyzer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Step 2: Clean and Organize Repository

Run the cleanup script to organize the repository:

```bash
# Preview what will be changed (dry run)
python cleanup_repo.py

# Execute cleanup
python cleanup_repo.py --execute
```

This will:
- ✅ Create organized folder structure
- ✅ Move files to appropriate directories
- ✅ Remove redundant files
- ✅ Handle sensitive configuration files
- ✅ Create backup of important files

## 🗄️ Step 3: Set Up Database (Supabase)

### 3.1 Create Supabase Project

1. Go to [Supabase](https://supabase.com)
2. Create a new project
3. Note your:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **Anon Key**: `eyJ...`

### 3.2 Create Database Schema

1. Open Supabase SQL Editor
2. Copy and run the schema from `docs/database/schema.sql`
3. Verify tables are created:
   - `calls`
   - `recordings`
   - `transcriptions`
   - `call_analysis`
   - `processing_queue`
   - `analytics_summary`

### 3.3 Enable Storage Bucket

1. Go to Storage in Supabase dashboard
2. Create a new bucket named `call-recordings`
3. Set it to **Private** (authenticated access only)

## 🔑 Step 4: Configure Environment Variables

### 4.1 Create .env File

```bash
cp .env.example .env
```

### 4.2 Edit .env File

```env
# Digital Concierge Credentials
DASHBOARD_USERNAME=your_dc_username
DASHBOARD_PASSWORD=your_dc_password

# API Keys
OPENAI_API_KEY=sk-proj-xxxxx
DEEPGRAM_API_KEY=xxxxx

# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJ.....

# Optional: Set log level
LOG_LEVEL=INFO
```

## 🧪 Step 5: Verify Installation

### 5.1 Test Database Connection

```bash
python scripts/check_calls_table.py
```

Expected output:
```
✅ Successfully connected to Supabase
📊 Calls table has X records
```

### 5.2 Test API Authentication

```python
python -c "
from src.pipelines.final_hybrid_pipeline import FinalHybridPipeline
import asyncio

async def test():
    pipeline = FinalHybridPipeline()
    token = await pipeline.authenticate()
    print(f'✅ Authentication successful!')

asyncio.run(test())
"
```

### 5.3 Test Audio Processing

```bash
# Test with sample audio
python tests/test_transcription.py
```

## 📊 Step 6: Initial Data Collection

### 6.1 Fetch Recent Calls

```python
from src.pipelines.final_hybrid_pipeline import FinalHybridPipeline
import asyncio

async def fetch_initial_calls():
    pipeline = FinalHybridPipeline()
    
    # Fetch calls from last 7 days
    calls = await pipeline.fetch_calls_batch(limit=50, days_back=7)
    
    print(f"✅ Found {len(calls)} calls with recordings")
    
    # Process first 5 calls as test
    await pipeline.run_pipeline(batch_size=5, days_back=7)

asyncio.run(fetch_initial_calls())
```

### 6.2 Monitor Progress

Check processing status:

```sql
-- In Supabase SQL Editor
SELECT status, COUNT(*) 
FROM calls 
GROUP BY status;
```

## 🖥️ Step 7: Run Complete Pipeline

### 7.1 Process Pending Calls

```bash
python src/pipelines/final_hybrid_pipeline.py
```

### 7.2 Batch Processing

For large volumes:

```python
from src.pipelines.batch_processor import BatchProcessor
import asyncio

async def process_batch():
    processor = BatchProcessor()
    await processor.process_pending_calls(
        batch_size=20,
        parallel_downloads=3
    )

asyncio.run(process_batch())
```

## 📈 Step 8: View Results

### 8.1 Check Database

```sql
-- View analyzed calls
SELECT 
    c.call_id,
    c.customer_name,
    c.duration_seconds,
    a.sentiment,
    a.category,
    a.follow_up_needed
FROM calls c
JOIN call_analysis a ON c.call_id = a.call_id
WHERE c.status = 'analyzed'
ORDER BY c.date_created DESC
LIMIT 10;
```

### 8.2 Export Results

```bash
python scripts/export_results.py --format csv --output results.csv
```

## 🔄 Step 9: Set Up Automation (Optional)

### 9.1 Create Cron Job

```bash
# Edit crontab
crontab -e

# Add daily processing at 2 AM
0 2 * * * cd /path/to/mcp-call-analyzer && /path/to/venv/bin/python src/pipelines/final_hybrid_pipeline.py >> logs/daily_processing.log 2>&1
```

### 9.2 Set Up Systemd Service

Create `/etc/systemd/system/mcp-analyzer.service`:

```ini
[Unit]
Description=MCP Call Analyzer Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/mcp-call-analyzer
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python src/pipelines/batch_processor.py --daemon
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mcp-analyzer
sudo systemctl start mcp-analyzer
```

## 🐛 Step 10: Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Fails
```
Error: Authentication failed: 401
```
**Solution**: 
- Verify DC credentials in `.env`
- Check if account is active
- Try logging into dashboard manually

#### 2. Database Connection Error
```
Error: connection to server at "db.xxx.supabase.co"
```
**Solution**:
- Check SUPABASE_URL format
- Verify API key is correct
- Check network connectivity

#### 3. Audio Download Fails
```
Error: 403 Forbidden - CloudFront
```
**Solution**:
- Ensure browser automation is enabled
- Check if MCP tools are configured
- Verify dashboard session is active

#### 4. Transcription Errors
```
Error: Deepgram quota exceeded
```
**Solution**:
- Check Deepgram usage limits
- Verify API key is valid
- Consider upgrading plan

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
python src/pipelines/final_hybrid_pipeline.py
```

### Check Logs

```bash
# View recent logs
tail -f logs/mcp_analyzer.log

# Search for errors
grep ERROR logs/mcp_analyzer.log

# View today's processing
grep "$(date +%Y-%m-%d)" logs/mcp_analyzer.log
```

## 🎉 Success Checklist

- [ ] Repository cloned and dependencies installed
- [ ] Environment variables configured
- [ ] Database schema created in Supabase
- [ ] Authentication working with DC API
- [ ] Test audio file processed successfully
- [ ] First batch of calls analyzed
- [ ] Results visible in database
- [ ] Automation configured (optional)

## 📚 Next Steps

1. **Explore the API**: See `docs/api/API_REFERENCE.md`
2. **Customize Analysis**: Modify prompts in `src/pipelines/final_hybrid_pipeline.py`
3. **Build Dashboard**: Create frontend to visualize results
4. **Add Webhooks**: Real-time processing of new calls
5. **Enhance Analytics**: Custom reports and insights

## 🆘 Getting Help

- **Documentation**: Check `docs/` folder
- **Issues**: Open issue on GitHub
- **Logs**: Always check logs first
- **Database**: Use Supabase dashboard for debugging

---

Congratulations! Your MCP Call Analyzer is now set up and ready to process calls. 🎊