#!/usr/bin/env python3
"""
MCP Call Analyzer - Fixed Main Application
"""

import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Call Analyzer",
    description="Automated call processing for automotive service centers",
    version="2.0.0"
)

# Lazy-loaded instances
_supabase_client = None
_openai_client = None

def get_supabase():
    """Get or create Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Supabase credentials not configured")
        _supabase_client = create_client(url, key)
    return _supabase_client

def get_openai():
    """Get or create OpenAI client"""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client

class ProcessCallRequest(BaseModel):
    call_id: str
    recording_url: Optional[str] = None
    customer_name: Optional[str] = "Unknown"
    customer_number: Optional[str] = "Unknown"

class ProcessResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MCP Call Analyzer",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "message": "Call processing service is operational"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check Supabase
    try:
        supabase = get_supabase()
        # Simple query to verify connection
        supabase.table("calls").select("id").limit(1).execute()
        health_status["components"]["supabase"] = "connected"
    except Exception as e:
        health_status["components"]["supabase"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check OpenAI
    try:
        client = get_openai()
        health_status["components"]["openai"] = "configured"
    except Exception as e:
        health_status["components"]["openai"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check environment
    health_status["components"]["environment"] = {
        "dashboard_url": bool(os.getenv("DASHBOARD_URL")),
        "deepgram_configured": bool(os.getenv("DEEPGRAM_API_KEY")),
        "port": os.getenv("PORT", "8080")
    }
    
    return health_status

@app.post("/api/process-call")
async def process_call(request: ProcessCallRequest, background_tasks: BackgroundTasks):
    """Process a single call"""
    try:
        # For now, just validate and queue
        if not request.call_id:
            raise HTTPException(status_code=400, detail="call_id is required")
        
        # Queue for background processing
        background_tasks.add_task(
            process_call_background,
            request.dict()
        )
        
        return ProcessResponse(
            status="queued",
            message=f"Call {request.call_id} queued for processing",
            data={"call_id": request.call_id}
        )
        
    except Exception as e:
        logger.error(f"Error processing call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_call_background(call_data: dict):
    """Background task to process a call"""
    call_id = call_data.get("call_id")
    logger.info(f"Processing call {call_id} in background")
    
    try:
        # Get clients
        supabase = get_supabase()
        
        # Store initial record
        result = supabase.table("calls").upsert({
            "call_id": call_id,
            "status": "processing",
            "customer_name": call_data.get("customer_name"),
            "customer_number": call_data.get("customer_number"),
            "created_at": datetime.now().isoformat()
        }).execute()
        
        logger.info(f"Call {call_id} record created in database")
        
        # TODO: Add actual processing logic here
        # - Download audio
        # - Transcribe with Deepgram
        # - Analyze with GPT-4
        # - Update database
        
    except Exception as e:
        logger.error(f"Background processing failed for {call_id}: {e}")

@app.get("/api/stats")
async def get_stats():
    """Get processing statistics"""
    try:
        supabase = get_supabase()
        
        # Get call counts
        total_result = supabase.table("calls").select("id", count="exact").execute()
        total_calls = len(total_result.data) if total_result.data else 0
        
        return {
            "total_calls": total_calls,
            "status": "operational",
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "error": str(e),
            "status": "error",
            "last_check": datetime.now().isoformat()
        }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for debugging"""
    return {
        "message": "API is working",
        "environment": {
            "python_version": "3.11",
            "has_supabase": bool(os.getenv("SUPABASE_URL")),
            "has_openai": bool(os.getenv("OPENAI_API_KEY")),
            "has_deepgram": bool(os.getenv("DEEPGRAM_API_KEY"))
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting MCP Call Analyzer on port {port}")
    uvicorn.run("main_fixed:app", host="0.0.0.0", port=port, reload=False)