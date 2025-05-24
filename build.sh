#!/bin/bash

# Install Python deps
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install
