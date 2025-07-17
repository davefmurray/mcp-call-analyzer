# API Reference - MCP Call Analyzer

## Overview

The MCP Call Analyzer provides a comprehensive API for processing automotive service calls. This reference covers all classes, methods, and integration points.

## Table of Contents

- [Core Classes](#core-classes)
- [Scraper APIs](#scraper-apis)
- [Pipeline APIs](#pipeline-apis)
- [Utility Functions](#utility-functions)
- [Database Models](#database-models)
- [External APIs](#external-apis)

---

## Core Classes

### `FinalHybridPipeline`

Main orchestrator for the complete call processing pipeline.

```python
from src.pipelines.final_hybrid_pipeline import FinalHybridPipeline

pipeline = FinalHybridPipeline()
```

#### Methods

##### `authenticate() -> str`
Authenticates with Digital Concierge API.

**Returns:**
- `str`: JWT authentication token

**Raises:**
- `Exception`: If authentication fails

**Example:**
```python
token = await pipeline.authenticate()
print(f"Authenticated with token: {token[:20]}...")
```

---

##### `fetch_calls_batch(limit: int = 100, days_back: int = 30) -> List[Dict]`
Fetches call records from the API.

**Parameters:**
- `limit` (int): Maximum number of calls to fetch
- `days_back` (int): Number of days to look back

**Returns:**
- `List[Dict]`: List of call records with metadata

**Example:**
```python
calls = await pipeline.fetch_calls_batch(limit=50, days_back=7)
for call in calls:
    print(f"Call {call['call_id']}: {call['customer_name']} ({call['duration_seconds']}s)")
```

---

##### `download_call_audio_mcp(call_data: Dict) -> Optional[str]`
Downloads audio file using MCP browser automation.

**Parameters:**
- `call_data` (Dict): Call information including `call_id` and `dc_call_id`

**Returns:**
- `Optional[str]`: Path to downloaded audio file or None if failed

**Example:**
```python
audio_path = await pipeline.download_call_audio_mcp({
    'call_id': 'CAxxxxx',
    'dc_call_id': '68780a43d84270fd7280e818'
})
```

---

##### `transcribe_audio(audio_path: str) -> Dict`
Transcribes audio using Deepgram.

**Parameters:**
- `audio_path` (str): Path to audio file

**Returns:**
- `Dict`: Transcription result with `transcript` and `success` fields

**Example:**
```python
result = await pipeline.transcribe_audio("downloads/call_audio.mp3")
if result['success']:
    print(f"Transcript: {result['transcript']}")
```

---

##### `analyze_call(transcript: str, call_info: Dict) -> Dict`
Analyzes call transcript with GPT-4.

**Parameters:**
- `transcript` (str): Call transcript text
- `call_info` (Dict): Call metadata

**Returns:**
- `Dict`: Analysis results including sentiment, category, intent, etc.

**Example:**
```python
analysis = await pipeline.analyze_call(
    transcript="Customer called about oil change...",
    call_info={'customer_name': 'John Doe', 'duration_seconds': 180}
)
print(f"Sentiment: {analysis['sentiment']}")
print(f"Category: {analysis['category']}")
```

---

##### `process_call_complete(call_data: Dict) -> Dict`
Processes a single call through the complete pipeline.

**Parameters:**
- `call_data` (Dict): Complete call information

**Returns:**
- `Dict`: Processing result with success status and analysis

**Example:**
```python
result = await pipeline.process_call_complete({
    'call_id': 'CAxxxxx',
    'dc_call_id': '68780a43d84270fd7280e818',
    'customer_name': 'Jane Smith',
    'duration_seconds': 240
})

if result['success']:
    print(f"Analysis: {result['analysis']}")
```

---

##### `run_pipeline(batch_size: int = 10, days_back: int = 7)`
Runs the complete pipeline for multiple calls.

**Parameters:**
- `batch_size` (int): Number of calls to process in batch
- `days_back` (int): Days to look back for calls

**Example:**
```python
await pipeline.run_pipeline(batch_size=20, days_back=14)
```

---

## Scraper APIs

### `MCPBrowserScraper`

Browser automation for authenticated audio downloads.

```python
from src.scrapers.mcp_browser_scraper import MCPBrowserScraper

scraper = MCPBrowserScraper()
```

#### Methods

##### `login_to_dashboard()`
Logs into Digital Concierge dashboard.

**Example:**
```python
await scraper.login_to_dashboard()
```

---

##### `navigate_to_call(call_sid: str, dc_call_id: str) -> Optional[str]`
Navigates to specific call and captures audio URL.

**Parameters:**
- `call_sid` (str): Twilio call SID
- `dc_call_id` (str): Digital Concierge internal ID

**Returns:**
- `Optional[str]`: Audio URL if found

---

##### `download_audio_for_call(call_data: Dict) -> Optional[str]`
Downloads audio for a specific call.

**Parameters:**
- `call_data` (Dict): Call information

**Returns:**
- `Optional[str]`: Path to downloaded file

---

### `APIScraper`

Direct API integration for call metadata.

```python
from src.scrapers.scraper_api import APIScraper

scraper = APIScraper()
```

#### Methods

##### `get_calls(start_date: datetime, end_date: datetime, limit: int = 100) -> List[Dict]`
Fetches calls within date range.

**Parameters:**
- `start_date` (datetime): Start date for search
- `end_date` (datetime): End date for search
- `limit` (int): Maximum results

**Returns:**
- `List[Dict]`: Call records

---

## Pipeline APIs

### `BatchProcessor`

Handles batch processing of calls.

```python
from src.pipelines.batch_processor import BatchProcessor

processor = BatchProcessor()
```

#### Methods

##### `process_pending_calls(batch_size: int = 10, parallel_downloads: int = 3)`
Processes pending calls in batches.

**Parameters:**
- `batch_size` (int): Calls per batch
- `parallel_downloads` (int): Concurrent downloads

---

## Utility Functions

### Audio Processing

```python
from src.utils.audio_utils import (
    convert_audio_format,
    get_audio_duration,
    split_audio_channels
)
```

#### `convert_audio_format(input_path: str, output_format: str = "mp3") -> str`
Converts audio to specified format.

#### `get_audio_duration(audio_path: str) -> float`
Returns audio duration in seconds.

#### `split_audio_channels(audio_path: str) -> Tuple[str, str]`
Splits stereo audio into separate channels.

---

### Database Utilities

```python
from src.utils.db_utils import (
    upsert_call,
    get_pending_calls,
    update_call_status
)
```

#### `upsert_call(call_data: Dict) -> Dict`
Inserts or updates call record.

#### `get_pending_calls(limit: int = 10) -> List[Dict]`
Fetches calls pending processing.

#### `update_call_status(call_id: str, status: str) -> bool`
Updates call processing status.

---

## Database Models

### Call Model

```python
@dataclass
class Call:
    call_id: str
    dc_call_id: str
    customer_name: str
    customer_number: str
    call_direction: str
    duration_seconds: int
    date_created: datetime
    has_recording: bool
    status: str
    dc_transcript: Optional[str] = None
    dc_sentiment: Optional[float] = None
    extension: Optional[str] = None
```

### Recording Model

```python
@dataclass
class Recording:
    id: int
    call_id: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    storage_path: str
    storage_url: str
    upload_status: str
    uploaded_at: datetime
```

### Analysis Model

```python
@dataclass
class CallAnalysis:
    id: int
    call_id: str
    analysis_data: Dict
    created_at: datetime
```

---

## External APIs

### Digital Concierge API

Base URL: `https://autoservice.api.digitalconcierge.io`

#### Authentication
```http
POST /auth/authenticate
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

**Response:**
```json
{
    "token": "eyJ...",
    "user": {
        "id": "user123",
        "username": "your_username"
    }
}
```

#### List Calls
```http
POST /call/list
x-access-token: eyJ...
Content-Type: application/json

{
    "query": {
        "$and": [
            {"date_created": {"$gte": "2024-01-01T00:00:00-04:00"}},
            {"date_created": {"$lte": "2024-01-31T23:59:59-04:00"}}
        ]
    },
    "page": 1,
    "limit": 100,
    "sort": {"date_created": -1}
}
```

---

### Deepgram API

#### Transcription Request
```python
from deepgram import DeepgramClient, PrerecordedOptions

deepgram = DeepgramClient(api_key)

options = PrerecordedOptions(
    model="nova-2",
    smart_format=True,
    utterances=True,
    punctuate=True,
    paragraphs=True,
    diarize=True,
    language="en-US"
)

response = deepgram.listen.rest.v("1").transcribe_file(
    {"buffer": audio_data}, 
    options
)
```

---

### OpenAI API

#### Analysis Request
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key)

response = await client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {
            "role": "system", 
            "content": "You are an automotive service call analyst."
        },
        {
            "role": "user", 
            "content": analysis_prompt
        }
    ],
    temperature=0.3,
    response_format={"type": "json_object"}
)
```

---

## Error Handling

### Common Exceptions

```python
class AuthenticationError(Exception):
    """Raised when API authentication fails"""
    pass

class TranscriptionError(Exception):
    """Raised when audio transcription fails"""
    pass

class AnalysisError(Exception):
    """Raised when call analysis fails"""
    pass

class DownloadError(Exception):
    """Raised when audio download fails"""
    pass
```

### Error Handling Example

```python
try:
    result = await pipeline.process_call_complete(call_data)
except AuthenticationError as e:
    logger.error(f"Auth failed: {e}")
    # Retry authentication
except TranscriptionError as e:
    logger.error(f"Transcription failed: {e}")
    # Mark call for manual review
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Log and continue with next call
```

---

## Rate Limiting

### API Limits
- Digital Concierge: 100 requests/minute
- Deepgram: 1000 minutes/month (free tier)
- OpenAI: Based on tier (typically 10,000 requests/minute)

### Rate Limiting Implementation

```python
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, calls_per_minute: int):
        self.semaphore = Semaphore(calls_per_minute)
        self.period = 60.0 / calls_per_minute
    
    async def acquire(self):
        async with self.semaphore:
            await asyncio.sleep(self.period)
```

---

## Webhooks

### Setting Up Webhooks

```python
@app.post("/webhook/call-completed")
async def handle_call_completed(request: Request):
    data = await request.json()
    
    # Queue for processing
    await queue.put({
        'call_id': data['CallSid'],
        'duration': data['CallDuration'],
        'timestamp': datetime.now()
    })
    
    return {"status": "queued"}
```

---

## Testing

### Unit Tests

```python
import pytest
from src.pipelines.final_hybrid_pipeline import FinalHybridPipeline

@pytest.mark.asyncio
async def test_authentication():
    pipeline = FinalHybridPipeline()
    token = await pipeline.authenticate()
    assert token is not None
    assert len(token) > 20

@pytest.mark.asyncio
async def test_transcription():
    pipeline = FinalHybridPipeline()
    result = await pipeline.transcribe_audio("test_audio.mp3")
    assert result['success'] is True
    assert len(result['transcript']) > 0
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_pipeline():
    pipeline = FinalHybridPipeline()
    
    # Test with real call
    test_call = {
        'call_id': 'CAtest123',
        'dc_call_id': 'dc123',
        'customer_name': 'Test Customer',
        'duration_seconds': 120
    }
    
    result = await pipeline.process_call_complete(test_call)
    
    assert result['success'] is True
    assert 'analysis' in result
    assert result['analysis']['sentiment'] in ['positive', 'neutral', 'negative']
```

---

## Performance Optimization

### Batch Processing

```python
async def process_calls_optimized(calls: List[Dict], max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(call):
        async with semaphore:
            return await pipeline.process_call_complete(call)
    
    tasks = [process_with_limit(call) for call in calls]
    return await asyncio.gather(*tasks)
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_analysis(transcript_hash: str) -> Optional[Dict]:
    """Cache analysis results by transcript hash"""
    return cache.get(transcript_hash)
```

---

## Monitoring

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_analyzer.log'),
        logging.StreamHandler()
    ]
)
```

### Metrics

```python
from prometheus_client import Counter, Histogram

calls_processed = Counter('calls_processed_total', 'Total calls processed')
processing_duration = Histogram('processing_duration_seconds', 'Time to process call')

@processing_duration.time()
async def process_call_with_metrics(call_data):
    result = await pipeline.process_call_complete(call_data)
    calls_processed.inc()
    return result
```