# Deployment Steps

## 1. Push to GitHub

### Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `mcp-call-analyzer`
3. Keep it public or private as you prefer
4. Don't initialize with README (we already have one)

### Push Local Repository

```bash
# Add GitHub remote (replace with your username)
git remote add origin https://github.com/YOUR_USERNAME/mcp-call-analyzer.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 2. Deploy to Railway

### Option A: Using Railway CLI

```bash
# Install Railway CLI
brew install railway

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

### Option B: Using Railway Dashboard

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Connect your GitHub account if needed
4. Select `mcp-call-analyzer` repository
5. Railway will auto-detect the Python app

### Configure Environment Variables

In Railway dashboard, add these environment variables:

```
# Digital Concierge
DASHBOARD_URL=https://autoservice.digitalconcierge.io
DASHBOARD_USERNAME=dev
DASHBOARD_PASSWORD=DFMdev12
DC_API_URL=https://autoservice.api.digitalconcierge.io

# AI Services
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Post-Deployment

1. Railway will provide a URL like `https://mcp-call-analyzer.up.railway.app`
2. Test the health endpoint: `https://your-app.railway.app/health`
3. Process calls via API:

```bash
curl -X POST https://your-app.railway.app/process-calls \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 7,
    "limit": 25
  }'
```

## 3. Additional Setup

### Install Playwright on Railway

Railway should automatically install Playwright browsers, but if needed, add to `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt && playwright install chromium"
  }
}
```

### Monitor Logs

```bash
railway logs
```

## 4. Testing Production

1. Check health: `GET /health`
2. Process a small batch: `POST /process-calls` with `limit: 5`
3. Check stats: `GET /stats`

## Notes

- Railway provides automatic HTTPS
- Scales automatically based on load
- Environment variables are encrypted
- Logs are available in Railway dashboard
- Supports custom domains if needed