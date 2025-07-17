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
        "timestamp": datetime.now().isoformat(),
        "port": os.getenv("PORT", "8000")
    }

@app.get("/health")
def health_check():
    health = {
        "status": "healthy",
        "port": os.getenv("PORT", "8000"),
        "env_vars_set": {
            "dashboard_username": bool(os.getenv("DASHBOARD_USERNAME")),
            "dashboard_password": bool(os.getenv("DASHBOARD_PASSWORD")),
            "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "deepgram_api_key": bool(os.getenv("DEEPGRAM_API_KEY")),
            "supabase_url": bool(os.getenv("SUPABASE_URL")),
            "supabase_key": bool(os.getenv("SUPABASE_KEY"))
        }
    }
    
    # Test Supabase connection
    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if url and key:
            client = create_client(url, key)
            # Simple test query
            client.table("calls").select("id").limit(1).execute()
            health["supabase_connected"] = True
    except Exception as e:
        health["supabase_connected"] = False
        health["supabase_error"] = str(e)
    
    return health

if __name__ == "__main__":
    import uvicorn
    # Railway sets PORT env var
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)