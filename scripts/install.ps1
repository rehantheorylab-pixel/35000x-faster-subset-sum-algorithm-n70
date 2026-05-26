Write-Host "=== Z++ Ultra Subset Sum Solver Installer ===" -ForegroundColor Cyan
Write-Host ""

$ALG_PATH = $PSScriptRoot

# ----- STEP 1: Optional - Install Rust -----
Write-Host "Rust 1.85+ is recommended for building from source." -ForegroundColor Gray
Write-Host "If you already have Rust or want to download the pre-built EXE, skip this step."
Write-Host "To install Rust, run: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
Write-Host ""
Write-Host "Press Enter to continue (or Ctrl+C to install Rust first)..."
Read-Host | Out-Null

# ----- STEP 2: Check for pre-built EXE or build from source -----
$EXE_PATH = Join-Path $ALG_PATH "zpp.exe"
if (Test-Path $EXE_PATH) {
    Write-Host "[OK] Pre-built zpp.exe found at $EXE_PATH" -ForegroundColor Green
    Write-Host "     Size: $((Get-Item $EXE_PATH).Length) bytes"
} else {
    Write-Host "[BUILD] No pre-built EXE found. Building from source..." -ForegroundColor Yellow
    $RUST_DIR = Join-Path $ALG_PATH "zpp_rust"
    if (-not (Test-Path $RUST_DIR)) {
        Write-Host "Error: zpp_rust directory not found" -ForegroundColor Red
        exit 1
    }
    Push-Location $RUST_DIR
    cargo build --release
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Build failed. Make sure Rust is installed." -ForegroundColor Red
        Write-Host "Install Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        Pop-Location
        exit 1
    }
    Pop-Location
    $BUILT_EXE = Join-Path $RUST_DIR "target\release\zpp.exe"
    if (Test-Path $BUILT_EXE) {
        Copy-Item $BUILT_EXE $EXE_PATH -Force
        Write-Host "[OK] Built and copied zpp.exe" -ForegroundColor Green
    }
}

# ----- STEP 3: Add to PATH -----
Write-Host "[PATH] Adding to system PATH..." -ForegroundColor Yellow
$CURRENT = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CURRENT -notlike "*$ALG_PATH*") {
    [Environment]::SetEnvironmentVariable("Path", "$CURRENT;$ALG_PATH", "User")
    $env:Path += ";$ALG_PATH"
    Write-Host "[OK] Added to user PATH" -ForegroundColor Green
} else {
    Write-Host "[OK] Already in PATH" -ForegroundColor Green
}

# ----- STEP 4: Add PowerShell function -----
Write-Host "[PROFILE] Adding 'algorithm' command..." -ForegroundColor Yellow
$ALG_CMD = Join-Path $ALG_PATH "algorithm.cmd"
if (Test-Path $ALG_CMD) {
    Write-Host "[OK] algorithm.cmd found" -ForegroundColor Green
} else {
    Write-Host "Warning: algorithm.cmd not found" -ForegroundColor Red
}

$PROFILE_DIR = Split-Path $PROFILE.CurrentUserAllHosts -Parent
if (-not (Test-Path $PROFILE_DIR)) {
    New-Item -ItemType Directory -Path $PROFILE_DIR -Force | Out-Null
}

$FUNC = @"

function algorithm {
    param([string[]]`$args)
    Push-Location "$ALG_PATH"
    if (Test-Path "$ALG_PATH\zpp.exe") {
        & "$ALG_PATH\zpp.exe" @args
    } elseif (Test-Path "$ALG_PATH\Z++.py") {
        & python "$ALG_PATH\Z++.py" @args
    } else {
        Write-Host "Error: Neither zpp.exe nor Z++.py found"
    }
    Pop-Location
}
"@

$EXISTING = Get-Content $PROFILE.CurrentUserAllHosts -ErrorAction SilentlyContinue
if ($EXISTING -notlike "*function algorithm*") {
    Add-Content -Path $PROFILE.CurrentUserAllHosts -Value $FUNC
    Write-Host "[OK] Added to PowerShell profile" -ForegroundColor Green
} else {
    Write-Host "[OK] Already in profile" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host "Open a NEW terminal and type: algorithm" -ForegroundColor White
Write-Host "Or double-click: zpp.exe" -ForegroundColor Gray
