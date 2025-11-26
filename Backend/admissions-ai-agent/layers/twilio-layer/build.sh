#!/bin/bash
set -e

# Build script for Twilio Lambda Layer
# Creates a layer-compatible directory structure with dependencies

echo "Building Twilio Lambda Layer..."

# Clean previous build
rm -rf python
rm -f twilio-layer.zip

# Create layer directory structure
mkdir -p python

# Install dependencies
pip install -r requirements.txt -t python/ --upgrade

# Create zip file for layer
zip -r twilio-layer.zip python/

echo "Layer built successfully: twilio-layer.zip"
echo "Size: $(du -h twilio-layer.zip | cut -f1)"
