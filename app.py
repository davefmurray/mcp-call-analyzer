#!/usr/bin/env python3
"""
MCP Call Analyzer - Production Ready
Built for Railway deployment
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MCP Call Analyzer",
    description="Automotive call processing service",
    version="3.0.0"
)

# Lazy-loaded clients
_clients = {
    "supabase": None,
    "openai": None,
    "deepgram": None
}

def get_supabase():
    """Get or create Supabase client"""
    if _clients["supabase"] is None:
        try:
            from supabase import create_client
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if url and key:
                _clients["supabase"] = create_client(url, key)
                logger.info("Supabase client initialized")
        except Exception as e:
            logger.error(f"Supabase init failed: {e}")
    return _clients["supabase"]

def get_openai():
    """Get or create OpenAI client"""
    if _clients["openai"] is None:
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                _clients["openai"] = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
    return _clients["openai"]

def get_deepgram():
    """Get or create Deepgram client"""
    if _clients["deepgram"] is None:
        try:
            # deepgram-sdk v2.x uses different import
            from deepgram import DeepgramClient
            api_key = os.getenv("DEEPGRAM_API_KEY")
            if api_key:
                _clients["deepgram"] = DeepgramClient(api_key)
                logger.info("Deepgram client initialized")
        except Exception as e:
            logger.error(f"Deepgram init failed: {e}")
    return _clients["deepgram"]

# Request/Response models
class CallRequest(BaseModel):
    call_id: str
    recording_url: Optional[str] = None
    customer_name: Optional[str] = "Unknown"
    customer_number: Optional[str] = None

class ApiResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

# Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MCP Call Analyzer",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "port": os.getenv("PORT", "8080")
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "railway": bool(os.getenv("RAILWAY_ENVIRONMENT")),
            "port": os.getenv("PORT", "8080")
        },
        "services": {}
    }
    
    # Check each service
    if get_supabase():
        health["services"]["supabase"] = "connected"
    else:
        health["services"]["supabase"] = "not configured"
        
    if get_openai():
        health["services"]["openai"] = "configured"
    else:
        health["services"]["openai"] = "not configured"
        
    if get_deepgram():
        health["services"]["deepgram"] = "configured"
    else:
        health["services"]["deepgram"] = "not configured"
    
    return health

@app.post("/api/process-call", response_model=ApiResponse)
async def process_call(request: CallRequest, background_tasks: BackgroundTasks):
    """Queue a call for processing"""
    try:
        # Validate request
        if not request.call_id:
            raise HTTPException(status_code=400, detail="call_id required")
        
        # Check if services are available
        supabase = get_supabase()
        if not supabase:
            raise HTTPException(status_code=503, detail="Supabase not configured")
        
        # Add to background processing
        background_tasks.add_task(
            process_call_async,
            request.dict()
        )
        
        return ApiResponse(
            status="success",
            message=f"Call {request.call_id} queued for processing",
            data={"call_id": request.call_id, "queued_at": datetime.now().isoformat()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queuing call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_call_async(call_data: dict):
    """Process call in background"""
    call_id = call_data.get("call_id")
    logger.info(f"Processing call {call_id}")
    
    try:
        supabase = get_supabase()
        if supabase:
            # Store initial record
            supabase.table("calls").upsert({
                "call_id": call_id,
                "status": "processing",
                "customer_name": call_data.get("customer_name"),
                "customer_number": call_data.get("customer_number"),
                "created_at": datetime.now().isoformat()
            }).execute()
            
            # TODO: Add actual processing
            # 1. Download audio if URL provided
            # 2. Transcribe with Deepgram
            # 3. Analyze with OpenAI
            # 4. Update database
            
            logger.info(f"Call {call_id} processing started")
            
    except Exception as e:
        logger.error(f"Error processing call {call_id}: {e}")

@app.get("/api/stats")
async def get_stats():
    """Get service statistics"""
    stats = {
        "service": "MCP Call Analyzer",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        supabase = get_supabase()
        if supabase:
            result = supabase.table("calls").select("id", count="exact").execute()
            stats["total_calls"] = result.count if hasattr(result, 'count') else 0
    except Exception as e:
        logger.error(f"Stats error: {e}")
        stats["error"] = str(e)
    
    return stats

# Run the app
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting MCP Call Analyzer on port {port}")
    uvicorn.run("app:app", host="0.0.0.0", port=port)