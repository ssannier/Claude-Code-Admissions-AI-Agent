# Build script for Twilio Lambda Layer (Windows PowerShell)
# Creates a layer-compatible directory structure with dependencies
# Uses Python zipfile to handle long path names on Windows

Write-Host "Building Twilio Lambda Layer..." -ForegroundColor Green

# Clean previous build
if (Test-Path "python") {
    Write-Host "Cleaning old build..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force python -ErrorAction SilentlyContinue
}
if (Test-Path "twilio-layer.zip") {
    Remove-Item -Force twilio-layer.zip -ErrorAction SilentlyContinue
}

# Create layer directory structure
New-Item -ItemType Directory -Path "python" -Force | Out-Null

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt -t python/ --upgrade --no-cache-dir

# Create zip file using Python (handles long paths better than PowerShell)
Write-Host "Creating zip archive..." -ForegroundColor Yellow
python -c "import zipfile; import os; zf = zipfile.ZipFile('twilio-layer.zip', 'w', zipfile.ZIP_DEFLATED); count = 0; [count := count + 1 or zf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), '.')) for root, dirs, files in os.walk('python') if '__pycache__' not in root for file in files]; zf.close(); print(f'Added {count} files'); print(f'Size: {os.path.getsize(\"twilio-layer.zip\")/1024/1024:.2f} MB')"

Write-Host "Layer built successfully: twilio-layer.zip" -ForegroundColor Green
