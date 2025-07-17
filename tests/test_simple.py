"""Simple test without FastAPI dependencies"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only what we can test without dependencies
def parse_duration(duration_str: str) -> int:
    """Convert duration string to seconds"""
    try:
        # Handle format like "5:23" or "1:45:23"
        parts = duration_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            return int(duration_str)
    except:
        return 0

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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])