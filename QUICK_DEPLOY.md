# Quick Deployment Guide

## Current Status

✅ **Railway Service Created**: `mcp-call-analyzer-production.up.railway.app`
✅ **Environment Variables Set**: All configured in Railway
⚠️ **GitHub Repo**: Needs to be created manually

## Next Steps

### 1. Create GitHub Repository

Since the `gh` CLI is not available, create the repo manually:

1. Go to: https://github.com/new
2. Repository name: `mcp-call-analyzer`
3. Set as Public or Private
4. **DON'T** initialize with README
5. Click "Create repository"

### 2. Push Your Code

```bash
# Add the remote
git remote add origin https://github.com/YOUR_USERNAME/mcp-call-analyzer.git

# Push to GitHub
git push -u origin main
```

### 3. Connect to Railway

The Railway service is already created (`mcp-call-analyzer`) but needs to be connected to your GitHub repo:

1. Go to: https://railway.app/project/b4887af6-4cdb-402d-9287-aabb19804db8/service/10d8dbf5-b629-4ab1-bed7-0a8201786b8b
2. Click on the service settings
3. Under "Source", click "Connect GitHub repo"
4. Select your `mcp-call-analyzer` repository
5. Railway will automatically redeploy

### 4. Update API Keys

The following placeholder keys need to be updated in Railway:

1. Go to the Variables tab in Railway
2. Update these values:
   - `OPENAI_API_KEY`: Replace with your actual OpenAI key
   - `DEEPGRAM_API_KEY`: Replace with your actual Deepgram key

### 5. Access Your App

Your app is available at:
**https://mcp-call-analyzer-production.up.railway.app**

Test endpoints:
- Health check: https://mcp-call-analyzer-production.up.railway.app/health
- API docs: https://mcp-call-analyzer-production.up.railway.app/docs

### 6. Process Calls

```bash
curl -X POST https://mcp-call-analyzer-production.up.railway.app/process-calls \
  -H "Content-Type: application/json" \
  -d '{
    "days_back": 7,
    "limit": 5
  }'
```

## Environment Variables Already Set

✅ `DASHBOARD_URL`: https://autoservice.digitalconcierge.io
✅ `DASHBOARD_USERNAME`: dev
✅ `DASHBOARD_PASSWORD`: DFMdev12
✅ `DC_API_URL`: https://autoservice.api.digitalconcierge.io
✅ `PORT`: 8000
✅ `SUPABASE_URL`: Configured
✅ `SUPABASE_KEY`: Configured
⚠️ `OPENAI_API_KEY`: Needs real key
⚠️ `DEEPGRAM_API_KEY`: Needs real key

## Monitoring

- Logs: https://railway.app/project/b4887af6-4cdb-402d-9287-aabb19804db8/service/10d8dbf5-b629-4ab1-bed7-0a8201786b8b/logs
- Metrics: Available in Railway dashboard
- Deployments: Automatic on git push

## Troubleshooting

If the deployment fails:
1. Check logs in Railway dashboard
2. Ensure all requirements are in `requirements.txt`
3. Verify environment variables are set correctly
4. Check that Playwright installation succeeds