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
    version="2.2.0"
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

def get_deepgram():
    """Get or create Deepgram client"""
    if _clients["deepgram"] is None:
        try:
            # Try multiple import methods for compatibility
            api_key = os.getenv("DEEPGRAM_API_KEY")
            if api_key:
                try:
                    # v3.x style
                    from deepgram import DeepgramClient
                    _clients["deepgram"] = DeepgramClient(api_key)
                except ImportError:
                    # v2.x style
                    from deepgram import Deepgram
                    _clients["deepgram"] = Deepgram(api_key)
                logger.info("Deepgram client initialized")
        except Exception as e:
            logger.warning(f"Deepgram init failed (will use mock): {e}")
    return _clients["deepgram"]

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "MCP Call Analyzer",
        "message": "Call processing API with AI capabilities",
        "version": "2.2.0",
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
        
    if get_deepgram():
        health["services"]["deepgram"] = "configured"
    else:
        health["services"]["deepgram"] = "mock mode"
    
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
            
        # Deepgram is optional - we can use mock transcription
        deepgram = get_deepgram()
        
        # Create initial record - use only fields that exist
        call_data = {
            "call_id": request.call_id,
            "status": "queued",
            "customer_name": request.customer_name,
            "customer_number": request.customer_number
        }
        
        # Add recording_url only if provided
        if request.recording_url:
            # Try to map to the correct column
            # The table might use mp3_url or storage_url instead
            call_data["mp3_url"] = request.recording_url
        
        # Try to store in database
        db_success = False
        db_error = None
        
        try:
            result = supabase.table("calls").insert(call_data).execute()
            logger.info(f"Call {request.call_id} stored in database")
            db_success = True
        except Exception as e:
            db_error = str(e)
            logger.error(f"Database insert failed: {e}")
            
            # Try with upsert instead
            try:
                result = supabase.table("calls").upsert(call_data).execute()
                logger.info(f"Call {request.call_id} upserted in database")
                db_success = True
                db_error = None
            except Exception as e2:
                db_error = f"Insert: {e}, Upsert: {e2}"
                logger.error(f"Both insert and upsert failed: {db_error}")
        
        # If database failed, return error
        if not db_success:
            raise HTTPException(
                status_code=500, 
                detail=f"Database operation failed: {db_error}"
            )
        
        # Queue background processing only if DB succeeded
        background_tasks.add_task(
            process_call_with_ai,
            request.dict(),
            supabase,
            openai,
            deepgram
        )
        
        # Add created_at for response
        call_data["created_at"] = datetime.now().isoformat()
        
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

async def process_call_with_ai(call_data: dict, supabase, openai, deepgram):
    """Process call with AI in background"""
    call_id = call_data.get("call_id")
    logger.info(f"Starting AI processing for call {call_id}")
    
    try:
        # Update status to processing
        if supabase:
            try:
                supabase.table("calls").update({
                    "status": "processing",
                    "updated_at": datetime.now().isoformat()
                }).eq("call_id", call_id).execute()
            except Exception as e:
                logger.warning(f"Could not update status: {e}")
        
        # Process recording if provided
        recording_url = call_data.get("recording_url")
        transcript = "No recording provided"
        
        if recording_url:
            # 1. Transcribe with Deepgram (or mock)
            transcript = await transcribe_audio(recording_url, deepgram)
            
        # 2. Always analyze with OpenAI
        analysis = await analyze_transcript(transcript, call_data, openai)
        
        # 3. Update database with results
        if supabase:
            try:
                supabase.table("calls").update({
                    "status": "completed",
                    "transcript": transcript,
                    "analysis": analysis,
                    "updated_at": datetime.now().isoformat()
                }).eq("call_id", call_id).execute()
                
                logger.info(f"Call {call_id} processing completed successfully")
            except Exception as e:
                logger.error(f"Could not update results: {e}")
            
    except Exception as e:
        logger.error(f"Error in AI processing for {call_id}: {e}")
        # Try to update status to failed
        if supabase:
            try:
                supabase.table("calls").update({
                    "status": "failed",
                    "analysis": {"error": str(e)},
                    "updated_at": datetime.now().isoformat()
                }).eq("call_id", call_id).execute()
            except:
                pass

async def transcribe_audio(audio_url: str, deepgram) -> str:
    """Transcribe audio using Deepgram or mock"""
    try:
        if deepgram:
            # TODO: Implement actual Deepgram transcription
            logger.info(f"Would transcribe audio from {audio_url} with Deepgram")
            return f"[Mock transcript] Customer calling about service for their vehicle. Audio URL: {audio_url}"
        else:
            logger.info(f"Using mock transcription for {audio_url}")
            return f"[Mock transcript] Customer calling about service appointment. Audio URL: {audio_url}"
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return f"[Transcription failed] Audio URL: {audio_url}"

async def analyze_transcript(transcript: str, call_data: dict, openai) -> dict:
    """Analyze transcript using OpenAI"""
    try:
        if not openai:
            return {"error": "OpenAI not available", "transcript": transcript}
            
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
            "analyzed_at": datetime.now().isoformat(),
            "transcript_length": len(transcript)
        }
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return {
            "error": str(e),
            "transcript": transcript,
            "analyzed_at": datetime.now().isoformat()
        }

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
        "version": "2.2.0",
        "capabilities": [
            "call_processing",
            "deepgram_transcription",
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
                stats["total_calls"] = len(result.data)
                
                # Count by status
                status_counts = {}
                for call in result.data:
                    status = call.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                stats["calls_by_status"] = status_counts
    except Exception as e:
        logger.warning(f"Could not get stats: {e}")
        stats["stats_error"] = str(e)
    
    return stats

@app.post("/api/test")
async def test_endpoint():
    """Test endpoint to verify everything works"""
    return {
        "message": "Test successful",
        "services": {
            "supabase": bool(get_supabase()),
            "openai": bool(get_openai()),
            "deepgram": bool(get_deepgram())
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/debug/test-db")
def debug_database():
    """Debug database connection and insert"""
    try:
        supabase = get_supabase()
        if not supabase:
            return {"error": "Supabase client not initialized"}
            
        # Test insert with minimal data
        test_id = f"debug-{datetime.now().strftime('%H%M%S')}"
        test_data = {
            "call_id": test_id,
            "status": "queued",
            "customer_name": "Debug Test"
        }
        
        # Try insert
        insert_result = None
        insert_error = None
        try:
            result = supabase.table("calls").insert(test_data).execute()
            insert_result = "Success"
        except Exception as e:
            insert_error = str(e)
            
        # Try to read back
        read_result = None
        try:
            check = supabase.table("calls").select("*").eq("call_id", test_id).execute()
            if check.data:
                read_result = "Found"
            else:
                read_result = "Not found"
        except Exception as e:
            read_result = f"Error: {e}"
            
        return {
            "test_id": test_id,
            "insert_result": insert_result,
            "insert_error": insert_error,
            "read_result": read_result,
            "supabase_url": os.getenv("SUPABASE_URL"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "type": type(e).__name__
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting MCP Call Analyzer v2.2 on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)