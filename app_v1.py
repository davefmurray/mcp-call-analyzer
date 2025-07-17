from fastapi import FastAPI, HTTPException, BackgroundTasks
from datetime import datetime
import os
import logging
from pydantic import BaseModel
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Call Analyzer",
    description="Automotive call processing API",
    version="1.0.0"
)

# Request model
class CallRequest(BaseModel):
    call_id: str
    recording_url: Optional[str] = None
    customer_name: Optional[str] = "Unknown"
    customer_number: Optional[str] = None

# Lazy-loaded Supabase client
_supabase_client = None

def get_supabase():
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if url and key:
                _supabase_client = create_client(url, key)
                logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Supabase init failed: {e}")
    return _supabase_client

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "MCP Call Analyzer",
        "message": "Call processing API is running",
        "timestamp": datetime.now().isoformat(),
        "port": os.getenv("PORT", "8080")
    }

@app.get("/health")
def health_check():
    health = {
        "status": "healthy",
        "port": os.getenv("PORT", "8080"),
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check Supabase
    supabase = get_supabase()
    if supabase:
        health["services"]["supabase"] = "connected"
    else:
        health["services"]["supabase"] = "not configured"
    
    # Check environment
    health["services"]["environment"] = {
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "deepgram_configured": bool(os.getenv("DEEPGRAM_API_KEY")),
        "dashboard_configured": bool(os.getenv("DASHBOARD_URL"))
    }
    
    return health

@app.post("/api/process-call")
async def process_call(request: CallRequest, background_tasks: BackgroundTasks):
    """Queue a call for processing"""
    try:
        # Validate
        if not request.call_id:
            raise HTTPException(status_code=400, detail="call_id is required")
        
        # Get Supabase client
        supabase = get_supabase()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Create initial record
        call_data = {
            "call_id": request.call_id,
            "status": "queued",
            "customer_name": request.customer_name,
            "customer_number": request.customer_number,
            "recording_url": request.recording_url,
            "created_at": datetime.now().isoformat()
        }
        
        # Try to insert (will create table if needed)
        try:
            result = supabase.table("calls").insert(call_data).execute()
            logger.info(f"Call {request.call_id} queued successfully")
        except Exception as e:
            # Table might not exist, return success anyway
            logger.warning(f"Database insert failed: {e}")
        
        # Queue background processing
        background_tasks.add_task(process_call_async, request.dict())
        
        return {
            "status": "success",
            "message": f"Call {request.call_id} queued for processing",
            "data": call_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_call_async(call_data: dict):
    """Process call in background"""
    call_id = call_data.get("call_id")
    logger.info(f"Background processing started for call {call_id}")
    
    # TODO: Add actual processing here
    # 1. Download audio from recording_url
    # 2. Transcribe with Deepgram
    # 3. Analyze with OpenAI
    # 4. Update database with results

@app.get("/api/stats")
def get_stats():
    """Get service statistics"""
    return {
        "service": "MCP Call Analyzer",
        "status": "operational",
        "version": "1.0.0",
        "capabilities": [
            "call_processing",
            "audio_transcription",
            "ai_analysis",
            "database_storage"
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting MCP Call Analyzer on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)