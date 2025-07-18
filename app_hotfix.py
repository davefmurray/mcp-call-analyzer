from fastapi import FastAPI, HTTPException, BackgroundTasks
from datetime import datetime
import os
import logging
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Call Analyzer",
    description="Automotive call processing API",
    version="2.0.1-hotfix"
)

# Request model
class CallRequest(BaseModel):
    call_id: str
    recording_url: Optional[str] = None
    customer_name: Optional[str] = "Unknown"
    customer_number: Optional[str] = None

# Response model
class ProcessResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None

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

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "MCP Call Analyzer",
        "message": "Call processing API with AI capabilities",
        "version": "2.0.1-hotfix",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
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
        
    health["services"]["deepgram"] = "disabled in hotfix"
    
    return health

@app.post("/api/process-call", response_model=ProcessResponse)
async def process_call(request: CallRequest, background_tasks: BackgroundTasks):
    """Queue a call for AI processing"""
    try:
        # Validate
        if not request.call_id:
            raise HTTPException(status_code=400, detail="call_id is required")
        
        # Check services
        supabase = get_supabase()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
            
        openai = get_openai()
        if not openai:
            raise HTTPException(status_code=503, detail="OpenAI not configured")
        
        # Create initial record
        call_data = {
            "call_id": request.call_id,
            "status": "queued",
            "customer_name": request.customer_name,
            "customer_number": request.customer_number,
            "recording_url": request.recording_url,
            "created_at": datetime.now().isoformat()
        }
        
        # Store in database
        try:
            result = supabase.table("calls").upsert(call_data).execute()
            logger.info(f"Call {request.call_id} stored in database")
        except Exception as e:
            logger.warning(f"Database error (will continue): {e}")
        
        # Queue background processing
        background_tasks.add_task(
            process_call_with_ai,
            request.dict(),
            supabase,
            openai
        )
        
        return ProcessResponse(
            status="success",
            message=f"Call {request.call_id} queued for AI processing",
            data=call_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_call_with_ai(call_data: dict, supabase, openai):
    """Process call with AI in background"""
    call_id = call_data.get("call_id")
    logger.info(f"Starting AI processing for call {call_id}")
    
    try:
        # Update status
        if supabase:
            try:
                supabase.table("calls").update({
                    "status": "processing"
                }).eq("call_id", call_id).execute()
            except:
                pass
        
        # Process recording if provided
        recording_url = call_data.get("recording_url")
        transcript = "[Hotfix] Transcription disabled - using mock data"
        
        if recording_url:
            transcript = f"[Hotfix Mock] Customer calling about service. Recording: {recording_url}"
            
        # Analyze with OpenAI
        analysis = await analyze_transcript(transcript, call_data, openai)
        
        # Update database
        if supabase:
            try:
                supabase.table("calls").update({
                    "status": "completed",
                    "transcript": transcript,
                    "analysis": analysis,
                    "updated_at": datetime.now().isoformat()
                }).eq("call_id", call_id).execute()
                
                logger.info(f"Call {call_id} processing completed")
            except:
                pass
            
    except Exception as e:
        logger.error(f"Error in AI processing for {call_id}: {e}")
        # Update status to failed
        if supabase:
            try:
                supabase.table("calls").update({
                    "status": "failed",
                    "analysis": {"error": str(e)},
                    "updated_at": datetime.now().isoformat()
                }).eq("call_id", call_id).execute()
            except:
                pass

async def analyze_transcript(transcript: str, call_data: dict, openai) -> dict:
    """Analyze transcript using OpenAI"""
    try:
        if not openai:
            return {"error": "OpenAI not available"}
            
        logger.info("Analyzing transcript with GPT-4")
        
        prompt = f"""
        Analyze this automotive service call transcript:
        
        Customer: {call_data.get('customer_name', 'Unknown')}
        Phone: {call_data.get('customer_number', 'Unknown')}
        Transcript: {transcript}
        
        Extract and format as JSON:
        1. call_reason: Main reason for the call
        2. vehicle_info: Any vehicle details mentioned
        3. service_requested: Specific services requested
        4. sentiment: Customer sentiment (positive/neutral/negative)
        5. follow_up_required: Yes/No and why
        6. priority: High/Medium/Low
        7. summary: Brief 1-2 sentence summary
        """
        
        response = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an automotive service advisor assistant. Analyze calls and extract key information in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return {
            "gpt_response": response.choices[0].message.content,
            "model": "gpt-4-turbo-preview",
            "analyzed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return {"error": str(e)}

@app.get("/api/calls/{call_id}")
async def get_call_status(call_id: str):
    """Get status of a specific call"""
    try:
        supabase = get_supabase()
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        result = supabase.table("calls").select("*").eq("call_id", call_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        else:
            raise HTTPException(status_code=404, detail="Call not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
def get_stats():
    """Get service statistics"""
    stats = {
        "service": "MCP Call Analyzer",
        "status": "operational",
        "version": "2.0.1-hotfix",
        "capabilities": [
            "call_processing",
            "mock_transcription",
            "gpt4_analysis",
            "supabase_storage"
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    # Try to get call counts
    try:
        supabase = get_supabase()
        if supabase:
            result = supabase.table("calls").select("status", count="exact").execute()
            if result.data:
                stats["calls_processed"] = len(result.data)
    except:
        pass
    
    return stats

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting MCP Call Analyzer v2.0.1-hotfix on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)