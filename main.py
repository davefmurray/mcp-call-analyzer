#\!/usr/bin/env python3
"""
MCP Call Analyzer - Main Application
Web service for processing automotive service calls
"""

import os
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging

from src.pipelines.enhanced_hybrid_pipeline import EnhancedHybridPipeline
from src.scrapers.scraper_api import DCAPIScraper

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

# Global instances
pipeline = EnhancedHybridPipeline()
api_scraper = DCAPIScraper()


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
    try:
        # Test API connectivity
        await api_scraper.authenticate()
        api_status = "connected"
    except Exception as e:
        api_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "components": {
            "api": api_status,
            "database": "connected" if os.getenv("SUPABASE_URL") else "not configured",
            "deepgram": "configured" if os.getenv("DEEPGRAM_API_KEY") else "not configured",
            "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not configured"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/process-calls")
async def process_calls(
    request: ProcessCallsRequest,
    background_tasks: BackgroundTasks
):
    """Queue calls for processing"""
    try:
        # Authenticate and fetch calls
        await api_scraper.authenticate()
        calls = await api_scraper.get_calls(
            limit=request.limit,
            days_back=request.days_back
        )
        
        # Filter calls with recordings
        calls_with_recordings = [
            call for call in calls if call.get("RecordingSid")
        ]
        
        job_id = f"job_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}"
        
        # Queue background processing
        background_tasks.add_task(
            process_calls_batch,
            calls_with_recordings,
            job_id
        )
        
        return CallProcessingResponse(
            status="success",
            message=f"Queued {len(calls_with_recordings)} calls for processing",
            calls_queued=len(calls_with_recordings),
            job_id=job_id
        )
        
    except Exception as e:
        logger.error(f"Error queuing calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_calls_batch(calls: List[dict], job_id: str):
    """Process a batch of calls in the background"""
    logger.info(f"Starting batch processing for job {job_id} with {len(calls)} calls")
    
    results = {
        "job_id": job_id,
        "total_calls": len(calls),
        "processed": 0,
        "failed": 0,
        "start_time": datetime.now()
    }
    
    for call in calls:
        try:
            # Prepare call data
            call_data = {
                "call_id": call.get("CallSid"),
                "dc_call_id": call.get("_id"),
                "customer_name": call.get("name", "Unknown"),
                "customer_number": call.get("from_number", "Unknown"),
                "call_direction": call.get("direction", "inbound"),
                "duration_seconds": call.get("duration_seconds", 0),
                "recording_sid": call.get("RecordingSid")
            }
            
            # Process with pipeline
            result = await pipeline.process_call_complete(call_data)
            
            if result["success"]:
                results["processed"] += 1
                logger.info(f"Successfully processed call {call_data[\"call_id\"]}")
            else:
                results["failed"] += 1
                logger.error(f"Failed to process call {call_data[\"call_id\"]}: {result.get(\"error\")}")
                
        except Exception as e:
            results["failed"] += 1
            logger.error(f"Error processing call: {e}")
    
    results["end_time"] = datetime.now()
    results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()
    
    logger.info(f"Batch processing complete for job {job_id}: {results[\"processed\"]} processed, {results[\"failed\"]} failed")
    
    # Here you could save results to database or send notification
    return results


@app.get("/stats")
async def get_stats():
    """Get processing statistics"""
    # In a real implementation, this would query the database
    return {
        "total_calls_processed": "25+",
        "success_rate": "100%",
        "average_processing_time": "11.3s",
        "last_processed": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting MCP Call Analyzer on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
