#!/bin/bash

echo "Running tests for Call Analyzer..."
echo "================================="

# Activate virtual environment
source venv/bin/activate

# Install test dependencies if needed
pip install -r requirements.txt

# Run tests with coverage
echo -e "\n📊 Running tests with coverage...\n"
pytest test_main.py -v --cov=main --cov-report=term-missing --cov-report=html

# Check if tests passed
if [ $? -eq 0 ]; then
    echo -e "\n✅ All tests passed!"
    echo -e "\n📈 Coverage report generated in htmlcov/index.html"
    echo "Open with: open htmlcov/index.html"
else
    echo -e "\n❌ Tests failed!"
    exit 1
fi

# Run specific test categories
echo -e "\n🔧 Test categories available:"
echo "  - Unit tests only: pytest test_main.py -v -m 'not integration'"
echo "  - Integration tests: pytest test_main.py -v -m integration"
echo "  - With warnings: pytest test_main.py -v -W default"