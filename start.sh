#!/bin/bash

echo "Installing Playwright browsers using Python..."
python -m playwright install chromium

echo "Starting Flask app..."
python app.py
