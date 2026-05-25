# =============================================================
#  Z++ Ultimate Engine — One-Line Installer (Windows PowerShell)
#
#  Usage:
#    iwr -useb https://raw.githubusercontent.com/<USER>/zpp/main/install.ps1 | iex
#
#  What this does:
#    1. Verifies (or installs) Rust toolchain via rustup
#    2. Clones the repo to %LOCALAPPDATA%\zpp
#    3. Builds the release binary
#    4. Adds an `algorithm` function to your PowerShell profile
#       so you can launch from anywhere just by typing: algorithm
# =============================================================

$ErrorActionPreference = "Stop"

# IMPORTANT: edit this to your GitHub username after first push.
$RepoUrl = "https://github.com/REPLACE_USERNAME/zpp.git"
$InstallRoot = Join-Path $env:LOCALAPPDATA "zpp"
$BinaryPath = Join-Path $InstallRoot "target\release\zpp.exe"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

Write-Step "Checking prerequisites"

# Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "git not found. Install Git for Windows from https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

# Rust / Cargo
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host "Rust not found. Installing via rustup..." -ForegroundColor Yellow
    $rustup = Join-Path $env:TEMP "rustup-init.exe"
    Invoke-WebRequest -UseBasicParsing -Uri "https://win.rustup.rs/" -OutFile $rustup
    & $rustup -y --default-toolchain stable
    $env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
    if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
        Write-Host "Rust install failed. Aborting." -ForegroundColor Red
        exit 1
    }
}

Write-Step "Fetching source ($RepoUrl)"
if (Test-Path $InstallRoot) {
    Push-Location $InstallRoot
    try { git pull --ff-only } finally { Pop-Location }
} else {
    git clone --depth 1 $RepoUrl $InstallRoot
}

Write-Step "Building release binary (this may take ~1 minute)"
Push-Location $InstallRoot
try {
    cargo build --release
} finally {
    Pop-Location
}

if (-not (Test-Path $BinaryPath)) {
    Write-Host "Build failed. Binary not found at $BinaryPath" -ForegroundColor Red
    exit 1
}

Write-Step "Wiring up the 'algorithm' command"
if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

$marker    = "# ZPP_ALGORITHM_COMMAND"
$endMarker = "# END_ZPP_ALGORITHM_COMMAND"
$content   = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($content -and $content.Contains($marker)) {
    $pattern = "(?s)" + [regex]::Escape($marker) + ".*?" + [regex]::Escape($endMarker)
    $content = [regex]::Replace($content, $pattern, "")
    Set-Content -Path $PROFILE -Value $content
}

$func = @"

$marker
function algorithm {
    & "$BinaryPath" @args
}
$endMarker
"@
Add-Content -Path $PROFILE -Value $func

Write-Step "Installed."
Write-Host ""
Write-Host "  Binary  : $BinaryPath" -ForegroundColor Green
Write-Host "  Source  : $InstallRoot" -ForegroundColor Green
Write-Host "  Profile : $PROFILE" -ForegroundColor Green
Write-Host ""
Write-Host "  Open a new PowerShell window, then type:" -ForegroundColor White
Write-Host "      algorithm" -ForegroundColor Yellow
Write-Host ""
