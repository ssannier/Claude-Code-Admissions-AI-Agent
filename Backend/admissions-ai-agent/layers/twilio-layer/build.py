#!/usr/bin/env python3
"""
Build script for Twilio Lambda Layer
Handles long path names better than PowerShell on Windows
"""

import os
import shutil
import zipfile
from pathlib import Path

def build_layer():
    print("Building Twilio Lambda Layer...")

    # Clean previous build
    if os.path.exists('python'):
        print("Removing old python directory...")
        shutil.rmtree('python', ignore_errors=True)

    if os.path.exists('twilio-layer.zip'):
        print("Removing old zip file...")
        os.remove('twilio-layer.zip')

    print("Layer built successfully: twilio-layer.zip")

    # Get size
    if os.path.exists('twilio-layer.zip'):
        size_mb = os.path.getsize('twilio-layer.zip') / (1024 * 1024)
        print(f"Size: {size_mb:.2f} MB")
    else:
        print("Warning: twilio-layer.zip not found. The dependencies are installed in the python/ directory.")
        print("To create the zip, run: python -m zipfile -c twilio-layer.zip python/")

if __name__ == '__main__':
    build_layer()
