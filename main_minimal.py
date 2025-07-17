#!/usr/bin/env python3
"""
MCP Call Analyzer - Minimal Working Version
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
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
    version="1.0.0"
)

class ProcessCallsRequest(BaseModel):
    days_back: int = 7
    limit: int = 10
    
class CallProcessingResponse(BaseModel):
    status: str
    message: str
    calls_queued: int
    job_id: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MCP Call Analyzer",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "api": "ready",
            "database": "configured" if os.getenv("SUPABASE_URL") else "not configured",
            "deepgram": "configured" if os.getenv("DEEPGRAM_API_KEY") else "not configured",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not configured"
        },
        "environment": {
            "dashboard_url": os.getenv("DASHBOARD_URL", "not set"),
            "dashboard_username": "***" if os.getenv("DASHBOARD_USERNAME") else "not set"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/process-calls")
async def process_calls(request: ProcessCallsRequest):
    """Queue calls for processing"""
    try:
        # For now, just return a success message
        # The actual processing will be added once deployment is stable
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return CallProcessingResponse(
            status="success",
            message=f"Feature temporarily disabled - deployment testing in progress",
            calls_queued=0,
            job_id=job_id
        )
        
    except Exception as e:
        logger.error(f"Error in process_calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """Get processing statistics"""
    return {
        "status": "deployment_testing",
        "message": "Statistics will be available once deployment is stable",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting MCP Call Analyzer (Minimal) on port {port}")
    uvicorn.run(
        "main_minimal:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )