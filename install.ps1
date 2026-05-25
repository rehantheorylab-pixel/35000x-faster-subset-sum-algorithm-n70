param([switch]$NoBuild)

Write-Host "=== Z++ Ultra Subset Sum Solver Installer ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Rust binary
if (-not $NoBuild) {
    Write-Host "[1/3] Building Rust engine (release mode)..." -ForegroundColor Yellow
    $rustDir = Join-Path $PSScriptRoot "zpp_rust"
    if (-not (Test-Path $rustDir)) {
        Write-Host "Error: zpp_rust directory not found at $rustDir" -ForegroundColor Red
        exit 1
    }
    Push-Location $rustDir
    cargo build --release 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Rust build failed. Try: install.ps1 -NoBuild" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "Rust engine built successfully!" -ForegroundColor Green
} else {
    Write-Host "[1/3] Skipping Rust build (-NoBuild flag)" -ForegroundColor Yellow
}

# Step 2: Add to PATH
Write-Host "[2/3] Adding Z++ to system PATH..." -ForegroundColor Yellow
$algPath = $PSScriptRoot
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$algPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$algPath", "User")
    Write-Host "Added '$algPath' to user PATH" -ForegroundColor Green
} else {
    Write-Host "Already in PATH" -ForegroundColor Gray
}

# Step 3: Add PowerShell function
Write-Host "[3/3] Adding 'algorithm' PowerShell command..." -ForegroundColor Yellow
$profilePath = $PROFILE.CurrentUserAllHosts
$profileDir = Split-Path $profilePath -Parent
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }

$funcDef = @"

function algorithm {
    param([string[]]`$args)
    Push-Location "$algPath"
    if (`$args.Count -eq 0) {
        python Z++.py
    } else {
        & python Z++.py @args
    }
    Pop-Location
}
"@

$existing = Get-Content $profilePath -ErrorAction SilentlyContinue
if ($existing -notlike "*function algorithm*") {
    Add-Content -Path $profilePath -Value $funcDef
    Write-Host "Added 'algorithm' function to PowerShell profile" -ForegroundColor Green
} else {
    Write-Host "'algorithm' function already exists in profile" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Installation Complete ===" -ForegroundColor Cyan
Write-Host "Open a NEW PowerShell window and type: algorithm" -ForegroundColor White
Write-Host "Or run directly: python Z++.py" -ForegroundColor Gray
