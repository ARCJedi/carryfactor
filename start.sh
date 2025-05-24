#!/bin/bash

echo "Installing required system dependencies..."
apt-get update && apt-get install -y \
  libnss3 \
  libnspr4 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcairo2 \
  libxext6 \
  libxdamage1 \
  libxrandr2 \
  libxcb1 \
  libasound2t64 \
  libxcomposite1 \
  libxfixes3 \
  libx11-xcb1 \
  libxrender1 \
  libdbus-1-3 \
  libatspi2.0-0

echo "Installing Playwright (Python)..."
python -m playwright install chromium

echo "Starting Flask app..."
python app.py
