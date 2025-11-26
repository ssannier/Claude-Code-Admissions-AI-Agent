#!/bin/bash
set -e

# Build script for Salesforce Lambda Layer
# Creates a layer-compatible directory structure with dependencies

echo "Building Salesforce Lambda Layer..."

# Clean previous build
rm -rf python
rm -f salesforce-layer.zip

# Create layer directory structure
mkdir -p python

# Install dependencies
pip install -r requirements.txt -t python/ --upgrade

# Create zip file for layer
zip -r salesforce-layer.zip python/

echo "Layer built successfully: salesforce-layer.zip"
echo "Size: $(du -h salesforce-layer.zip | cut -f1)"
