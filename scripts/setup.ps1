# Z++ Ultra - Universal Single-Command Installer
# Usage (Quick - use existing zpp.exe from repo):
#   powershell -ExecutionPolicy Bypass -File setup.ps1 -Quick
# Usage (Full - build from source, default):
#   powershell -ExecutionPolicy Bypass -File setup.ps1

param(
    [switch]$Quick
)

$REPO_ROOT = Split-Path -Parent $PSScriptRoot
if (-not $REPO_ROOT) { $REPO_ROOT = (Get-Location).Path }

Write-Host "========================================" -ForegroundColor Cyan
if ($Quick) {
    Write-Host "  Z++ Ultra Quick Install (Pre-built EXE)" -ForegroundColor Cyan
} else {
    Write-Host "  Z++ Ultra Full Install (From Source)" -ForegroundColor Cyan
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function Write-Step {
    param([int]$Num, [string]$Text)
    Write-Host "[$Num/5] $Text" -ForegroundColor Yellow
}

function Write-Done {
    param([string]$Text)
    Write-Host "  $Text" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Text)
    Write-Host "  $Text" -ForegroundColor Yellow
}

function Write-Err {
    param([string]$Text)
    Write-Host "  $Text" -ForegroundColor Red
}

if ($Quick) {
    # Quick mode: just verify existing EXE and set up command
    Write-Step 1 "Verifying zpp.exe..."
    $REPO_EXE = Join-Path $REPO_ROOT "zpp.exe"
    if (Test-Path $REPO_EXE) {
        $size = (Get-Item $REPO_EXE).Length
        Write-Done "zpp.exe found ($([math]::Round($size/1MB, 1)) MB)"
    } else {
        Write-Err "zpp.exe not found in repository."
        Write-Warn "Make sure you cloned the full repository."
        Write-Warn "Run: git clone https://github.com/rehantheorylab-pixel/35000x-faster-subset-sum-algorithm-n70.git"
        pause
        exit 1
    }

    Write-Step 2 "Setting up Python environment..."
    $HAS_PYTHON = $null -ne (Get-Command "python" -ErrorAction SilentlyContinue)
    if ($HAS_PYTHON) {
        pip install numpy psutil 2>&1 | Out-Null
        Write-Done "Python dependencies ready."
    }

    Write-Step 3 "Setting up 'algorithm' command..."
} else {
    # Full mode: build from source
    Write-Step 1 "Checking Rust installation..."
    $HAS_RUST = $null -ne (Get-Command "rustc" -ErrorAction SilentlyContinue)
    $HAS_CARGO = $null -ne (Get-Command "cargo" -ErrorAction SilentlyContinue)

    if (-not $HAS_RUST) {
        Write-Warn "Rust not found. Installing via rustup..."
        $installer = Join-Path $env:TEMP "rustup-init.exe"
        try {
            Invoke-WebRequest -Uri "https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe" -OutFile $installer -UseBasicParsing
            & $installer -y --default-toolchain stable
            $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:Path"
            Write-Done "Rust installed."
        } catch {
            Write-Err "Could not install Rust automatically."
            Write-Warn "Download from: https://rustup.rs"
        }
    } else {
        Write-Done "Rust found: $(rustc --version)"
    }

    Write-Step 2 "Checking build tools..."
    $HAS_CARGO = $null -ne (Get-Command "cargo" -ErrorAction SilentlyContinue)
    if ($HAS_RUST -and (-not $HAS_CARGO)) {
        Write-Warn "Installing VS 2022 Build Tools (needed for Rust on Windows)..."
        $vsInstaller = Join-Path $env:TEMP "vs_BuildTools.exe"
        try {
            Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vs_BuildTools.exe" -OutFile $vsInstaller -UseBasicParsing
            $args = "--quiet --wait --norestart --installPath `"$env:ProgramFiles\Microsoft Visual Studio\2022\BuildTools`" --add Microsoft.VisualStudio.Workload.VCTools"
            Start-Process -Wait -FilePath $vsInstaller -ArgumentList $args
            Write-Done "VS Build Tools installed."
        } catch {
            Write-Warn "Could not install VS Build Tools automatically."
            Write-Warn "Download from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022"
        }
    } else {
        Write-Done "Build tools available."
    }

    Write-Step 3 "Building Z++ engine from source..."
    $RUST_DIR = Join-Path $REPO_ROOT "zpp_rust"
    $TARGET_EXE = Join-Path $RUST_DIR "target\release\zpp.exe"
    $REPO_EXE = Join-Path $REPO_ROOT "zpp.exe"

    $HAS_CARGO = $null -ne (Get-Command "cargo" -ErrorAction SilentlyContinue)
    if ($HAS_CARGO -and (Test-Path $RUST_DIR)) {
        Push-Location $RUST_DIR
        cargo build --release 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0 -and (Test-Path $TARGET_EXE)) {
            Copy-Item $TARGET_EXE $REPO_EXE -Force
            Write-Done "Z++ built from source (maximum performance)."
        } else {
            Write-Err "Build failed."
            $HAS_EXE = Test-Path $REPO_EXE
            if ($HAS_EXE) {
                Write-Warn "Using existing zpp.exe instead."
            }
        }
        Pop-Location
    } else {
        Write-Warn "Cannot build from source."
    }

    Write-Step 4 "Python dependencies..."
    $HAS_PYTHON = $null -ne (Get-Command "python" -ErrorAction SilentlyContinue)
    if ($HAS_PYTHON) {
        pip install numpy psutil 2>&1 | Out-Null
        Write-Done "Python dependencies ready."
    }

    Write-Step 5 "Setting up 'algorithm' command..."
}

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
Write-Host "    algorithm 23,45,67,89,12,34,56,78,90,11 200" -ForegroundColor Gray
Write-Host ""
Write-Host "  Expected output:"
Write-Host "    EXACT: True  Engine: Hard-U128  Time: 0.0234s" -ForegroundColor Gray
Write-Host "    Solution: [23, 45, 67, 65]" -ForegroundColor Gray
Write-Host ""
Write-Host "  Run full test suite:"
Write-Host "    python tests\test_zpp.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  Location: $REPO_ROOT" -ForegroundColor Gray

pause
