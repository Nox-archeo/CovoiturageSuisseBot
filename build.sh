#!/bin/bash

# Build script for Render deployment
set -e  # Exit on any error

echo "Starting build process..."
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"

# Upgrade pip first
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Set environment variables for compilation
export PYCAIRO_NO_PKG_CONFIG=1
export PYTHONPATH="/opt/render/project/src:$PYTHONPATH"

# Install dependencies with specific options to avoid compilation issues
echo "Installing dependencies..."
pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

echo "Build completed successfully!"
