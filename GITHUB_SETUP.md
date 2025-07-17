# GitHub Repository Setup

## Quick Setup (Run These Commands)

### 1. Authenticate GitHub CLI

```bash
# Run this and follow the prompts:
gh auth login
```

Choose:
- GitHub.com
- HTTPS
- Login with web browser

### 2. Create Repository and Push

```bash
# Create the repository
gh repo create mcp-call-analyzer --public --source=. --push

# The above command will:
# - Create the repo on GitHub
# - Set up the remote
# - Push all your code
```

### 3. Connect to Railway

Your Railway service is already waiting at:
- Service ID: `10d8dbf5-b629-4ab1-bed7-0a8201786b8b`
- URL: https://mcp-call-analyzer-production.up.railway.app

To connect:
1. Go to: https://railway.app/project/b4887af6-4cdb-402d-9287-aabb19804db8/service/10d8dbf5-b629-4ab1-bed7-0a8201786b8b
2. Click Settings → Source
3. Connect your new `mcp-call-analyzer` GitHub repo
4. Railway will auto-deploy!

### 4. Update API Keys in Railway

Go to the Variables tab and update:
- `OPENAI_API_KEY`: Your real OpenAI key
- `DEEPGRAM_API_KEY`: Your real Deepgram key

## Alternative: Manual GitHub Creation

If you prefer the web interface:

1. Go to: https://github.com/new
2. Name: `mcp-call-analyzer`
3. Create repository
4. Run locally:
```bash
git remote add origin https://github.com/YOUR_USERNAME/mcp-call-analyzer.git
git push -u origin main
```

## Your App is Ready!

Once connected, your app will be live at:
**https://mcp-call-analyzer-production.up.railway.app**

All environment variables are already configured in Railway!