# Historical Port Agency Fee Research - Download Script
# Execute this PowerShell script to download all free sources automatically
# Estimated time: 30-45 minutes (depending on connection speed)
# Total download size: ~210 MB

Write-Host "Starting Historical Fee Research Downloads..." -ForegroundColor Green
Write-Host "Total size: ~210 MB | Estimated time: 30-45 minutes" -ForegroundColor Yellow
Write-Host ""

# Set download directory
$downloadDir = "G:\My Drive\LLM\task_usace_entrance_clearance\00_DATA\00.04_ARCHIVAL_SOURCES"
$fmbDir = "$downloadDir\FMB_Reports"

# Verify directories exist
if (-not (Test-Path $downloadDir)) {
    New-Item -ItemType Directory -Force -Path $downloadDir | Out-Null
}
if (-not (Test-Path $fmbDir)) {
    New-Item -ItemType Directory -Force -Path $fmbDir | Out-Null
}

Write-Host "[1/13] Downloading 1910 'Dues and Charges on Shipping' (166.5 MB)..." -ForegroundColor Cyan
Write-Host "This is the largest file and will take 10-20 minutes..." -ForegroundColor Yellow
try {
    $url1910 = "https://archive.org/download/dueschargesonsh00urqugoog/dueschargesonsh00urqugoog.pdf"
    $out1910 = "$downloadDir\1910_Dues_and_Charges_on_Shipping.pdf"

    if (Test-Path $out1910) {
        Write-Host "File already exists, skipping..." -ForegroundColor Gray
    } else {
        Invoke-WebRequest -Uri $url1910 -OutFile $out1910 -UseBasicParsing
        Write-Host "✓ Downloaded successfully: 1910_Dues_and_Charges_on_Shipping.pdf" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Error downloading 1910 book: $_" -ForegroundColor Red
    Write-Host "  Manual download: $url1910" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Downloading Federal Maritime Board Annual Reports (1951-1961)..." -ForegroundColor Cyan

# Download Federal Maritime Board reports
$years = 1951..1961
$reportNum = 2
foreach ($year in $years) {
    Write-Host "[$reportNum/13] Downloading FMB Annual Report $year..." -ForegroundColor Cyan

    $url = "https://www.fmc.gov/wp-content/uploads/2021/09/FMB-$year-Annual-Report.pdf"
    $outFile = "$fmbDir\FMB_Annual_Report_$year.pdf"

    try {
        if (Test-Path $outFile) {
            Write-Host "  Already exists, skipping..." -ForegroundColor Gray
        } else {
            Invoke-WebRequest -Uri $url -OutFile $outFile -UseBasicParsing
            Write-Host "  ✓ Downloaded: FMB_Annual_Report_$year.pdf" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✗ Error downloading $year report: $_" -ForegroundColor Red
        Write-Host "  Manual download: $url" -ForegroundColor Yellow
    }

    $reportNum++
}

Write-Host ""
Write-Host "[13/13] Downloading Dallas Fed Freight Rate Study (2020)..." -ForegroundColor Cyan
try {
    $urlDallas = "https://www.dallasfed.org/-/media/documents/research/papers/2020/wp2008.pdf"
    $outDallas = "$downloadDir\Dallas_Fed_Freight_Rates_2020.pdf"

    if (Test-Path $outDallas) {
        Write-Host "File already exists, skipping..." -ForegroundColor Gray
    } else {
        Invoke-WebRequest -Uri $urlDallas -OutFile $outDallas -UseBasicParsing
        Write-Host "✓ Downloaded successfully: Dallas_Fed_Freight_Rates_2020.pdf" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Error downloading Dallas Fed paper: $_" -ForegroundColor Red
    Write-Host "  Manual download: $urlDallas" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DOWNLOAD COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check what was downloaded
Write-Host "Verifying downloads..." -ForegroundColor Cyan
Write-Host ""

$files = @(
    "$downloadDir\1910_Dues_and_Charges_on_Shipping.pdf",
    "$downloadDir\Dallas_Fed_Freight_Rates_2020.pdf"
)

$fmbFiles = Get-ChildItem "$fmbDir\*.pdf" -ErrorAction SilentlyContinue

Write-Host "Downloaded files:" -ForegroundColor Yellow
$totalSize = 0

foreach ($file in $files) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length / 1MB
        $totalSize += $size
        Write-Host "  ✓ $(Split-Path $file -Leaf) - $([math]::Round($size, 1)) MB" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $(Split-Path $file -Leaf) - MISSING" -ForegroundColor Red
    }
}

Write-Host "  ✓ FMB Reports: $($fmbFiles.Count) files" -ForegroundColor Green
foreach ($fmbFile in $fmbFiles) {
    $size = $fmbFile.Length / 1MB
    $totalSize += $size
}

Write-Host ""
Write-Host "Total downloaded: $([math]::Round($totalSize, 1)) MB" -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Review downloaded files in:" -ForegroundColor White
Write-Host "   $downloadDir" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Search 1910 book for 'agent' + US port names" -ForegroundColor White
Write-Host "3. Search FMB reports for 'agency' keywords" -ForegroundColor White
Write-Host "4. Extract any fee data found" -ForegroundColor White
Write-Host ""
Write-Host "5. Next: Submit FOIA request and send archive emails" -ForegroundColor Yellow
Write-Host "   See: IMMEDIATE_ACTIONS_START_HERE.md" -ForegroundColor Gray
Write-Host ""

# Optional: Open the directory
$openDir = Read-Host "Open download directory now? (y/n)"
if ($openDir -eq 'y') {
    Invoke-Item $downloadDir
}
