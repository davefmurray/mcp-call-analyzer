from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
from supabase import create_client
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Debug API", version="1.0.0")

@app.get("/")
def root():
    return {"status": "debug mode", "time": datetime.now().isoformat()}

@app.get("/test-db")
def test_database():
    """Test database connection and insert"""
    try:
        # Get Supabase client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            return {"error": "Missing SUPABASE credentials"}
            
        supabase = create_client(url, key)
        
        # Test data
        test_id = f"debug-{datetime.now().strftime('%H%M%S')}"
        test_data = {
            "call_id": test_id,
            "status": "queued",
            "customer_name": "Debug Test",
            "customer_number": "555-DEBUG"
        }
        
        # Try insert
        try:
            result = supabase.table("calls").insert(test_data).execute()
            
            # Verify
            check = supabase.table("calls").select("*").eq("call_id", test_id).execute()
            
            return {
                "success": True,
                "insert_result": str(result.data) if result.data else "No data",
                "verify_result": check.data[0] if check.data else "Not found",
                "test_id": test_id
            }
        except Exception as e:
            # Try without recording_url
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "test_id": test_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stage": "connection"
        }

@app.get("/check-env")
def check_environment():
    """Check environment variables"""
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL", "Not set"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY", "Not set")[:20] + "..." if os.getenv("SUPABASE_KEY") else "Not set",
        "OPENAI_KEY": "Set" if os.getenv("OPENAI_API_KEY") else "Not set",
        "DEEPGRAM_KEY": "Set" if os.getenv("DEEPGRAM_API_KEY") else "Not set",
        "PORT": os.getenv("PORT", "8080")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)