from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "MCP Call Analyzer",
        "message": "Deployment working! Now we can add features.",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "env_vars_set": {
            "dashboard_username": bool(os.getenv("DASHBOARD_USERNAME")),
            "dashboard_password": bool(os.getenv("DASHBOARD_PASSWORD")),
            "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "deepgram_api_key": bool(os.getenv("DEEPGRAM_API_KEY")),
            "supabase_url": bool(os.getenv("SUPABASE_URL")),
            "supabase_key": bool(os.getenv("SUPABASE_KEY"))
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)