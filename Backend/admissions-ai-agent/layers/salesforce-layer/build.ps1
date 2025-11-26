# Build script for Salesforce Lambda Layer (Windows PowerShell)
# Creates a layer-compatible directory structure with dependencies

Write-Host "Building Salesforce Lambda Layer..." -ForegroundColor Green

# Clean previous build
if (Test-Path "python") {
    Remove-Item -Recurse -Force python
}
if (Test-Path "salesforce-layer.zip") {
    Remove-Item -Force salesforce-layer.zip
}

# Create layer directory structure
New-Item -ItemType Directory -Path "python" -Force | Out-Null

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt -t python/ --upgrade

# Create zip file for layer
Write-Host "Creating zip archive..." -ForegroundColor Yellow
Compress-Archive -Path python/* -DestinationPath salesforce-layer.zip -Force

Write-Host "Layer built successfully: salesforce-layer.zip" -ForegroundColor Green
$size = (Get-Item salesforce-layer.zip).Length / 1MB
Write-Host "Size: $([math]::Round($size, 2)) MB" -ForegroundColor Green
