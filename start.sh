#!/bin/bash
# Install Playwright browsers if not already installed
if [ ! -d "$HOME/.cache/ms-playwright" ]; then
    echo "Installing Playwright browsers..."
    playwright install chromium
fi

# Start the application
python main.py