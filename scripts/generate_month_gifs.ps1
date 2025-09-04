# PowerShell script to generate GIFs for any month
# Run this from the project root directory
# Features enhanced page load waiting and large watermarks with black stroke

param(
    [Parameter(Mandatory=$true)]
    [string]$StartDate,    # Format: YYYY-MM-DD (e.g., "2025-09-01")
    
    [Parameter(Mandatory=$true)]
    [string]$EndDate,      # Format: YYYY-MM-DD (e.g., "2025-09-30")
    
    [switch]$OverwriteScreenshots = $false,
    [switch]$UploadToDrive = $false,
    [string]$DriveFolderId = "",
    [switch]$MakePublic = $false,
    [double]$SecondsPerImage = 0.3,
    [double]$Lat = 57.48042,
    [double]$Lon = 21.30953,
    [double]$Zoom = 5.0
)

Write-Host "Starting GPS JAM GIF generation process..." -ForegroundColor Green
Write-Host "Date Range: $StartDate to $EndDate" -ForegroundColor Yellow
Write-Host "Location: Lat $Lat, Lon $Lon, Zoom $Zoom" -ForegroundColor Yellow

# Determine output directory and file names based on date range
$startDateObj = [DateTime]::ParseExact($StartDate, "yyyy-MM-dd", $null)
$endDateObj = [DateTime]::ParseExact($EndDate, "yyyy-MM-dd", $null)

$yearMonth = $startDateObj.ToString("yyyy-MM")
$monthName = $startDateObj.ToString("MMMM-yyyy")

# Ensure required directories exist
$converterDir = "converter\images"
$resultsDir = "results\gifs"

if (-not (Test-Path $converterDir)) {
    New-Item -ItemType Directory -Path $converterDir -Force | Out-Null
}

if (-not (Test-Path $resultsDir)) {
    New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null
}

Write-Host "Step 1: Capturing screenshots for $monthName..." -ForegroundColor Green

# Run screenshot capture
$screenshotArgs = @(
    "scripts/scrape_screenshots.py",
    "--start-date", $StartDate,
    "--end-date", $EndDate,
    "--output-dir", $converterDir,
    "--lat", $Lat,
    "--lon", $Lon,
    "--zoom", $Zoom
)

if ($OverwriteScreenshots) {
    $screenshotArgs += "--overwrite"
}

Write-Host "Running: python $($screenshotArgs -join ' ')" -ForegroundColor Gray
& python @screenshotArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Screenshot capture failed with exit code $LASTEXITCODE"
    exit 1
}

Write-Host "Screenshot capture completed!" -ForegroundColor Green

# Step 2: Generate GIF from all screenshots
Write-Host "Step 2: Generating GIF from $monthName screenshots..." -ForegroundColor Cyan

$inputPath = Join-Path $converterDir "gpsjam-$yearMonth"
$outputPath = Join-Path $resultsDir "gpsjam-$monthName-watermarked.gif"

if (-not (Test-Path $inputPath)) {
    Write-Error "Screenshot directory not found: $inputPath"
    exit 1
}

$imageCount = (Get-ChildItem -Path $inputPath -Filter "*.png").Count
if ($imageCount -eq 0) {
    Write-Error "No images found in $inputPath"
    exit 1
}

Write-Host "Found $imageCount images to process." -ForegroundColor Yellow
Write-Host "Processing screenshots from $inputPath..." -ForegroundColor Yellow

# Generate GIF with large watermarks and black stroke (new defaults)
$gifArgs = @(
    "scripts/make_gif.py",
    "--input-dir", $inputPath,
    "--output-path", $outputPath,
    "--seconds-per-image", $SecondsPerImage,
    "--order-strategy", "date",
    "--watermark-prefix", "GPSJAM",
    "--watermark-position", "center",
    "--compress",
    "--max-size-mb", "14.99"
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

if ($LASTEXITCODE -ne 0) {
    Write-Error "GIF generation failed with exit code $LASTEXITCODE"
    exit 1
}

Write-Host "SUCCESS!" -ForegroundColor Green
Write-Host "Generated: $outputPath" -ForegroundColor Green

if (Test-Path $outputPath) {
    $fileInfo = Get-Item $outputPath
    $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    Write-Host "File size: $sizeMB MB" -ForegroundColor Green
    Write-Host "Features: Large 60pt watermarks with 2px black stroke for maximum visibility" -ForegroundColor Yellow
    Write-Host "Format: Infinite loop GIF with GPSJAM MM-DD-YY date tracking" -ForegroundColor Yellow
}

Write-Host "GPS JAM GIF generation completed successfully!" -ForegroundColor Green
