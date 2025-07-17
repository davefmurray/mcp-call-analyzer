# MCP Call Analyzer 🚗📞

A powerful automotive call processing system that automatically transcribes, analyzes, and stores service calls using AI.

## 🚀 Live Production
- **URL**: https://mcp-call-analyzer-production.up.railway.app
- **Version**: 2.2.0
- **Status**: ✅ Fully Operational

## 🎯 Features

### Current Capabilities
- ✅ **Call Processing API** - Accept and queue calls for AI analysis
- ✅ **Supabase Integration** - Store call data and analysis results  
- ✅ **GPT-4 Analysis** - Extract key information from transcripts
- ✅ **Mock Transcription** - Fallback when audio processing unavailable
- ✅ **Railway Deployment** - Production-ready cloud hosting
- ✅ **Error Handling** - Comprehensive error reporting and recovery

### Coming Soon
- 🔄 **Deepgram Transcription** - Real audio-to-text conversion
- 🔄 **Digital Concierge Scraper** - Automated call ingestion
- 🔄 **Real-time Processing** - Live call analysis pipeline

## 📊 System Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│  Digital Concierge  │────▶│   MCP Call Analyzer │
│   (Call Source)     │     │    (FastAPI v2.2)   │
└─────────────────────┘     └──────────┬──────────┘
                                       │
                ┌──────────────────────┼──────────────────────┐
                │                      │                      │
                ▼                      ▼                      ▼
        ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
        │   Deepgram    │    │    OpenAI     │    │   Supabase    │
        │ Transcription │    │  GPT-4 API    │    │   Database    │
        └───────────────┘    └───────────────┘    └───────────────┘
```

## 🛠️ API Endpoints

### Core Endpoints

#### `GET /` - Health Check
```bash
curl https://mcp-call-analyzer-production.up.railway.app/
```

#### `GET /health` - Service Status
```bash
curl https://mcp-call-analyzer-production.up.railway.app/health
```

#### `POST /api/process-call` - Process New Call
```bash
curl -X POST https://mcp-call-analyzer-production.up.railway.app/api/process-call \
  -H "Content-Type: application/json" \
  -d '{
    "call_id": "unique-call-id",
    "customer_name": "John Doe",
    "customer_number": "555-1234",
    "recording_url": "https://example.com/call-audio.mp3"
  }'
```

#### `GET /api/calls/{call_id}` - Get Call Status
```bash
curl https://mcp-call-analyzer-production.up.railway.app/api/calls/unique-call-id
```

#### `GET /api/stats` - Service Statistics
```bash
curl https://mcp-call-analyzer-production.up.railway.app/api/stats
```

### Debug Endpoints

#### `GET /api/debug/test-db` - Test Database Connection
```bash
curl https://mcp-call-analyzer-production.up.railway.app/api/debug/test-db
```

## 🗄️ Database Schema

### `calls` Table
| Column | Type | Description |
|--------|------|-------------|
| `call_id` | TEXT (PK) | Unique identifier for the call |
| `status` | TEXT | Call processing status: queued, processing, completed, failed |
| `customer_name` | TEXT | Customer's name |
| `customer_number` | TEXT | Customer's phone number |
| `recording_url` | TEXT | URL to call recording |
| `transcript` | TEXT | Transcribed text from call |
| `analysis` | JSONB | GPT-4 analysis results |
| `created_at` | TIMESTAMP | When the call was received |
| `updated_at` | TIMESTAMP | Last update time |

### Analysis JSON Structure
```json
{
  "call_reason": "Main reason for the call",
  "vehicle_info": "Any vehicle details mentioned",
  "service_requested": "Specific services requested",
  "sentiment": "positive/neutral/negative",
  "follow_up_required": "Yes/No and why",
  "priority": "High/Medium/Low",
  "summary": "Brief 1-2 sentence summary"
}
```

## 🔧 Local Development

### Prerequisites
- Python 3.11+
- Supabase account
- OpenAI API key
- Deepgram API key (optional)
- Railway CLI (for deployment)

### Setup
```bash
# Clone repository
git clone https://github.com/davefmurray/mcp-call-analyzer.git
cd mcp-call-analyzer

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials

# Run locally
python app.py
```

### Environment Variables
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
OPENAI_API_KEY=your_openai_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
PORT=8080
```

## 🚀 Deployment

### Railway Deployment (Production)

1. **Important**: Always use FULL commit hash for deployments
```bash
# Get full commit hash
git rev-parse HEAD

# Deploy via Railway API/CLI
railway deploy --commit-sha=FULL_HASH_HERE
```

2. **Environment Setup**: Configure all required environment variables in Railway dashboard

3. **Database Migration**: Run SQL migrations in Supabase before first deployment

### Critical Deployment Notes
- ⚠️ **ALWAYS use full Git commit hash** (40 chars) not short hash (7 chars)
- ⚠️ **Supabase schema cache** may take 5-10 minutes to refresh after migrations
- ⚠️ **Check deployment logs** if builds fail - Railway provides detailed error messages

## 📈 Current Statistics
- **Total Calls Processed**: 92+
- **Call Statuses**: 
  - Analyzed: 26
  - Pending Download: 66
- **Success Rate**: 100% (with mock transcription)

## 🐛 Troubleshooting

### Common Issues

1. **"Deepgram not configured" error**
   - Solution: v2.2.0+ uses mock transcription as fallback
   
2. **Database insert failures**
   - Check Supabase RLS policies
   - Verify schema migrations applied
   - Wait for schema cache refresh

3. **Railway deployment failures**
   - Use full commit hash (see RAILWAY_DEPLOYMENT_FIX.md)
   - Check environment variables
   - Review build logs

## 🔮 Roadmap

### Phase 1: Core Infrastructure ✅
- [x] FastAPI server setup
- [x] Supabase database integration
- [x] OpenAI GPT-4 integration
- [x] Railway deployment
- [x] Error handling and logging

### Phase 2: Audio Processing (Current)
- [ ] Implement Deepgram transcription
- [ ] Audio file download and processing
- [ ] Transcription accuracy improvements
- [ ] Multiple audio format support

### Phase 3: Digital Concierge Integration
- [ ] API authentication
- [ ] Call scraping automation
- [ ] Real-time call monitoring
- [ ] Webhook integration

### Phase 4: Advanced Features
- [ ] Real-time dashboards
- [ ] Analytics and reporting
- [ ] Multi-tenant support
- [ ] Advanced AI insights

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is proprietary software. All rights reserved.

## 🙏 Acknowledgments

- Built with FastAPI, Supabase, OpenAI, and Deepgram
- Deployed on Railway
- Developed with Claude Code

---

**Version**: 2.2.0 | **Last Updated**: July 17, 2025