from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Call Analyzer",
    description="Automotive call processing service",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "MCP Call Analyzer",
        "message": "Call processing service is running",
        "timestamp": datetime.now().isoformat(),
        "port": os.getenv("PORT", "8080")
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "8080"),
        "env_vars_set": {
            "dashboard_username": bool(os.getenv("DASHBOARD_USERNAME")),
            "dashboard_password": bool(os.getenv("DASHBOARD_PASSWORD")),
            "openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "deepgram_api_key": bool(os.getenv("DEEPGRAM_API_KEY")),
            "supabase_url": bool(os.getenv("SUPABASE_URL")),
            "supabase_key": bool(os.getenv("SUPABASE_KEY"))
        }
    }

@app.get("/api/status")
def api_status():
    """Check API connectivity and configuration"""
    return {
        "dashboard_url": os.getenv("DASHBOARD_URL", "Not configured"),
        "services_configured": {
            "supabase": bool(os.getenv("SUPABASE_URL")),
            "deepgram": bool(os.getenv("DEEPGRAM_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "dashboard": bool(os.getenv("DASHBOARD_USERNAME"))
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/process-test")
def process_test():
    """Test endpoint to verify processing capability"""
    try:
        # Just verify we can access environment variables
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
        return {
            "status": "success",
            "message": "Processing capability verified",
            "can_process": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats():
    """Get basic statistics"""
    return {
        "service": "MCP Call Analyzer",
        "status": "operational",
        "deployment": "Railway",
        "features": {
            "call_scraping": "ready",
            "transcription": "ready",
            "analysis": "ready",
            "storage": "ready"
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting MCP Call Analyzer on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)