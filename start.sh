#!/bin/bash

echo "Installing Playwright dependencies..."
npx playwright install --with-deps

echo "Starting Flask app..."
python app.py
