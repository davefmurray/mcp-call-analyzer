#!/bin/bash

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

echo "Setup complete! Now run:"
echo "source venv/bin/activate"
echo "python main.py"