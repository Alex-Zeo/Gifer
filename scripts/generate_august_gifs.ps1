# PowerShell script to generate GIFs for all days in August 2025
# Run this from the project root directory
# Features enhanced page load waiting for reliable map screenshots
# Uses large 60pt watermarks with black stroke for maximum visibility

param(
    [switch]$OverwriteScreenshots = $false,
    [switch]$UploadToDrive = $false,
    [string]$DriveFolderId = "",
    [switch]$MakePublic = $false,
    [double]$SecondsPerImage = 0.5
)

Write-Host "Starting August 2025 GIF generation process..." -ForegroundColor Green

# Check if Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found in PATH. Please install Python or add it to PATH."
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "scripts/scrape_screenshots.py")) {
    Write-Error "Please run this script from the project root directory."
    exit 1
}

# Create output directories
$converterDir = "converter/images"
$resultsDir = "results/gifs"
New-Item -ItemType Directory -Force -Path $converterDir | Out-Null
New-Item -ItemType Directory -Force -Path $resultsDir | Out-Null

Write-Host "Output directories created." -ForegroundColor Yellow

# Step 1: Scrape screenshots for August 2025
Write-Host "Step 1: Scraping screenshots for August 2025..." -ForegroundColor Cyan

$screenshotArgs = @(
    "scripts/scrape_screenshots.py",
    "--start-date", "2025-08-01",
    "--end-date", "2025-08-31",
    "--output-dir", $converterDir
)

if ($OverwriteScreenshots) {
    $screenshotArgs += "--overwrite"
}

Write-Host "Running: python $($screenshotArgs -join ' ')" -ForegroundColor Gray
& python @screenshotArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Screenshot scraping failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "Screenshots completed successfully!" -ForegroundColor Green

# Step 2: Generate GIF from all screenshots
Write-Host "Step 2: Generating GIF from all August 2025 screenshots..." -ForegroundColor Cyan

$inputPath = Join-Path $converterDir "gpsjam-2025-08"
$outputPath = Join-Path $resultsDir "gpsjam-august-2025-large-stroke.gif"

if (-not (Test-Path $inputPath)) {
    Write-Error "Screenshot directory not found: $inputPath"
    exit 1
}

# Count images in the directory
$imageCount = (Get-ChildItem -Path $inputPath -File -Include "*.png", "*.jpg", "*.jpeg" | Measure-Object).Count
if ($imageCount -eq 0) {
    Write-Error "No images found in $inputPath"
    exit 1
}

Write-Host "Found $imageCount images to process." -ForegroundColor Yellow
Write-Host "Processing screenshots from $inputPath..." -ForegroundColor Yellow

$gifArgs = @(
    "scripts/make_gif.py",
    "--input-dir", $inputPath,
    "--output-path", $outputPath,
    "--seconds-per-image", $SecondsPerImage,
    "--order-strategy", "date",
    "--watermark-prefix", "GPSJAM",
    "--watermark-position", "top-left",
    "--compress",
    "--max-size-mb", "14.99",
    "--rename-output", "GPSJAM_AUG_2025"
)

if ($UploadToDrive) {
    $gifArgs += "--upload-to-drive"
    if ($DriveFolderId) {
        $gifArgs += "--drive-folder-id", $DriveFolderId
    }
    if ($MakePublic) {
        $gifArgs += "--make-public"
    }
}

Write-Host "Running: python $($gifArgs -join ' ')" -ForegroundColor Gray
& python @gifArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== SUCCESS ===" -ForegroundColor Green
    Write-Host "✓ Successfully created GIF with $imageCount frames" -ForegroundColor Green
    Write-Host "GIF location: $outputPath" -ForegroundColor Yellow
    
    if ($UploadToDrive) {
        Write-Host "GIF has been uploaded to Google Drive" -ForegroundColor Cyan
    }
    
    Write-Host "`nAugust 2025 GIF generation completed! 🎉" -ForegroundColor Green
} else {
    Write-Host "`n=== FAILED ===" -ForegroundColor Red
    Write-Host "✗ Failed to create GIF (exit code: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}
