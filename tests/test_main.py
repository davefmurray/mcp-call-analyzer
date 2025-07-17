import pytest
from unittest.mock import AsyncMock, Mock, patch, mock_open
from fastapi.testclient import TestClient
import httpx
from datetime import datetime

from main import (
    app, 
    scrape_call_details, 
    download_audio, 
    transcribe_audio,
    store_results,
    parse_duration
)

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch('main.supabase') as mock:
        yield mock

@pytest.fixture
def mock_openai():
    with patch('main.openai_client') as mock:
        yield mock

@pytest.fixture
def mock_playwright():
    with patch('main.async_playwright') as mock:
        yield mock

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_parse_duration_minutes_seconds(self):
        assert parse_duration("5:23") == 323
        assert parse_duration("10:00") == 600
        assert parse_duration("0:45") == 45
    
    def test_parse_duration_hours_minutes_seconds(self):
        assert parse_duration("1:30:45") == 5445
        assert parse_duration("2:00:00") == 7200
    
    def test_parse_duration_seconds_only(self):
        assert parse_duration("60") == 60
        assert parse_duration("3600") == 3600
    
    def test_parse_duration_invalid(self):
        assert parse_duration("invalid") == 0
        assert parse_duration("") == 0

class TestScraper:
    """Test the dashboard scraper"""
    
    @pytest.mark.asyncio
    async def test_scrape_call_details_success(self, mock_playwright):
        # Mock playwright behavior
        mock_page = AsyncMock()
        mock_page.evaluate.return_value = {
            'audio_url': 'https://example.com/audio.mp3',
            'phone': '555-1234',
            'duration': '5:30'
        }
        
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        result = await scrape_call_details("test123")
        
        assert result['audio_url'] == 'https://example.com/audio.mp3'
        assert result['phone'] == '555-1234'
        assert result['duration'] == '5:30'
        mock_page.goto.assert_called()
        mock_browser.close.assert_called()
    
    @pytest.mark.asyncio
    async def test_scrape_call_details_no_audio(self, mock_playwright):
        # Mock playwright behavior with no audio URL
        mock_page = AsyncMock()
        mock_page.evaluate.return_value = {
            'audio_url': None,
            'phone': '555-1234',
            'duration': '5:30'
        }
        
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        with pytest.raises(Exception, match="No audio URL found"):
            await scrape_call_details("test123")

class TestAudioDownload:
    """Test audio download functionality"""
    
    @pytest.mark.asyncio
    async def test_download_audio_success(self):
        with patch('httpx.AsyncClient') as mock_client:
            # Mock response
            mock_response = Mock()
            mock_response.content = b"fake audio data"
            mock_response.raise_for_status = Mock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with patch('builtins.open', mock_open()) as mock_file:
                result = await download_audio("https://example.com/audio.mp3")
                
                assert result.startswith("/tmp/call_audio_")
                assert result.endswith(".mp3")
                mock_file.assert_called_once()
                mock_file().write.assert_called_with(b"fake audio data")

class TestTranscription:
    """Test audio transcription"""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, mock_openai):
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.text = "This is a test transcription"
        mock_openai.audio.transcriptions.create.return_value = mock_response
        
        with patch('builtins.open', mock_open(read_data=b"audio data")):
            with patch('os.remove') as mock_remove:
                result = await transcribe_audio("/tmp/test.mp3")
                
                assert result == "This is a test transcription"
                mock_openai.audio.transcriptions.create.assert_called_once()
                mock_remove.assert_called_with("/tmp/test.mp3")

class TestStoreResults:
    """Test Supabase storage"""
    
    @pytest.mark.asyncio
    async def test_store_results_success(self, mock_supabase):
        # Mock Supabase responses
        mock_update_response = Mock()
        mock_update_response.data = [{'call_id': 'test123'}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response
        
        mock_insert_response = Mock()
        mock_insert_response.data = [{'id': 1}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_response
        
        call_data = {'audio_url': 'https://example.com/audio.mp3'}
        result = await store_results('test123', call_data, 'Test transcription')
        
        assert result['call_id'] == 'test123'
        assert mock_supabase.table.call_count == 2  # calls and transcriptions

class TestAPI:
    """Test API endpoints"""
    
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Call Analyzer MVP" in response.json()["message"]
    
    @pytest.mark.asyncio
    async def test_process_single_call_success(self, mock_playwright, mock_openai, mock_supabase):
        # Mock all dependencies
        with patch('main.scrape_call_details') as mock_scrape:
            mock_scrape.return_value = {
                'audio_url': 'https://example.com/audio.mp3',
                'phone': '555-1234',
                'duration': '5:30'
            }
            
            with patch('main.download_audio') as mock_download:
                mock_download.return_value = '/tmp/test.mp3'
                
                with patch('main.transcribe_audio') as mock_transcribe:
                    mock_transcribe.return_value = "This is a test transcription that is longer than 200 characters. " * 5
                    
                    with patch('main.store_results') as mock_store:
                        mock_store.return_value = {'call_id': 'test123'}
                        
                        response = client.post("/process-single-call", json={"call_id": "test123"})
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data['status'] == 'success'
                        assert data['call_id'] == 'test123'
                        assert len(data['transcription_preview']) == 203  # 200 + "..."
                        assert data['processed'] == True

# Integration test
@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_pipeline_integration():
    """Test the complete pipeline with mocked external services"""
    with patch('main.async_playwright') as mock_playwright, \
         patch('main.openai_client') as mock_openai, \
         patch('main.supabase') as mock_supabase, \
         patch('httpx.AsyncClient') as mock_httpx:
        
        # Setup all mocks for complete flow
        # ... (setup code similar to individual tests)
        
        # This would test the entire flow end-to-end
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])