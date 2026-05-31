# Z++ Ultra - Universal Single-Command Installer
# Usage: powershell -ExecutionPolicy Bypass -File setup.ps1
# Or after git clone: .\setup.ps1

$REPO_ROOT = Split-Path -Parent $PSScriptRoot
if (-not $REPO_ROOT) { $REPO_ROOT = (Get-Location).Path }

$HAS_EXE = Test-Path (Join-Path $REPO_ROOT "zpp.exe")
$HAS_RUST = $null -ne (Get-Command "rustc" -ErrorAction SilentlyContinue)
$HAS_PYTHON = $null -ne (Get-Command "python" -ErrorAction SilentlyContinue)
$HAS_CARGO = $null -ne (Get-Command "cargo" -ErrorAction SilentlyContinue)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Z++ Ultra Subset Sum Solver Installer" -ForegroundColor Cyan
Write-Host "  Repository: $REPO_ROOT" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Install Rust (if not present)
if (-not $HAS_RUST) {
    Write-Host "[1/5] Rust not found. Installing via rustup..." -ForegroundColor Yellow
    $installer = Join-Path $env:TEMP "rustup-init.exe"
    try {
        Invoke-WebRequest -Uri "https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe" -OutFile $installer -UseBasicParsing
        & $installer -y --default-toolchain stable
        $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:Path"
        $HAS_RUST = $true
        $HAS_CARGO = $true
        Write-Host "  Rust installed." -ForegroundColor Green
    } catch {
        Write-Host "  Could not install Rust automatically." -ForegroundColor Red
        Write-Host "  Download from: https://rustup.rs" -ForegroundColor Yellow
    }
} else {
    Write-Host "[1/5] Rust found: $(rustc --version)" -ForegroundColor Green
}

# Step 2: Install VS Build Tools (Windows only, needed for Rust)
if ($HAS_RUST -and (-not $HAS_CARGO)) {
    Write-Host "[2/5] Installing VS 2022 Build Tools (needed for Rust on Windows)..." -ForegroundColor Yellow
    $vsInstaller = Join-Path $env:TEMP "vs_BuildTools.exe"
    try {
        Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vs_BuildTools.exe" -OutFile $vsInstaller -UseBasicParsing
        $args = "--quiet --wait --norestart --installPath `"$env:ProgramFiles\Microsoft Visual Studio\2022\BuildTools`" --add Microsoft.VisualStudio.Workload.VCTools"
        Start-Process -Wait -FilePath $vsInstaller -ArgumentList $args
        Write-Host "  VS Build Tools installed." -ForegroundColor Green
    } catch {
        Write-Host "  Could not install VS Build Tools automatically." -ForegroundColor Yellow
        Write-Host "  You may need them: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022" -ForegroundColor Gray
    }
} else {
    Write-Host "[2/5] Cargo available: $(cargo --version 2>$null)" -ForegroundColor Green
}

# Step 3: Build or verify the binary
Write-Host "[3/5] Building Z++ engine..." -ForegroundColor Yellow
$RUST_DIR = Join-Path $REPO_ROOT "zpp_rust"
$TARGET_EXE = Join-Path $RUST_DIR "target\release\zpp.exe"
$REPO_EXE = Join-Path $REPO_ROOT "zpp.exe"

if ($HAS_CARGO -and (Test-Path $RUST_DIR)) {
    Push-Location $RUST_DIR
    cargo build --release 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $TARGET_EXE)) {
        Copy-Item $TARGET_EXE $REPO_EXE -Force
        Write-Host "  Z++ built from source (maximum performance)." -ForegroundColor Green
    } else {
        Write-Host "  Build failed. Will use Python fallback." -ForegroundColor Yellow
    }
    Pop-Location
} elseif ($HAS_EXE) {
    Write-Host "  Pre-built zpp.exe found." -ForegroundColor Green
} else {
    Write-Host "  No Rust compiler found. Installing Python fallback..." -ForegroundColor Yellow
}

# Step 4: Install Python packages
Write-Host "[4/5] Installing Python dependencies..." -ForegroundColor Yellow
if ($HAS_PYTHON) {
    pip install numpy psutil 2>&1 | Out-Null
    Write-Host "  Python dependencies ready." -ForegroundColor Green
}

# Step 5: Set up the 'algorithm' command
Write-Host "[5/5] Setting up 'algorithm' command..." -ForegroundColor Yellow

# Create algorithm.cmd at repo root
$cmdContent = @"
@echo off
cd /d "%~dp0"
if exist "%~dp0zpp.exe" (
    "%~dp0zpp.exe" %*
    exit /b %ERRORLEVEL%
)
python "%~dp0Z++.py" %*
"@
$cmdContent | Out-File -FilePath (Join-Path $REPO_ROOT "algorithm.cmd") -Encoding ascii

# Add to PATH
$CURRENT_PATH = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CURRENT_PATH -notlike "*$REPO_ROOT*") {
    [Environment]::SetEnvironmentVariable("Path", "$CURRENT_PATH;$REPO_ROOT", "User")
    $env:Path += ";$REPO_ROOT"
}

# Add PowerShell function
$func = @"

function algorithm {
    param([string[]]`$args)
    Push-Location "$REPO_ROOT"
    if (Test-Path "$REPO_ROOT\zpp.exe") {
        & "$REPO_ROOT\zpp.exe" @args
    } else {
        python "$REPO_ROOT\Z++.py" @args
    }
    Pop-Location
}
"@
$PROFILE_CONTENT = Get-Content $PROFILE.CurrentUserAllHosts -ErrorAction SilentlyContinue
if ($PROFILE_CONTENT -notlike "*function algorithm*") {
    Add-Content -Path $PROFILE.CurrentUserAllHosts -Value $func
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Open a NEW terminal and type: algorithm" -ForegroundColor White
Write-Host ""
Write-Host "  Quick test:"
Write-Host "    algorithm 1,3,5,7,9 15" -ForegroundColor Gray
Write-Host ""
Write-Host "  Or run the full benchmark:"
Write-Host "    python benchmarks\bench_n80_n140.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  Location: $REPO_ROOT" -ForegroundColor Gray

pause
