# ============================================================
#  Z++ Algorithm — Universal PowerShell Installer
#
#  This script wires up the `algorithm` command for your LOCAL
#  copy of Z++.  Run this ONCE after cloning the repo:
#
#      git clone https://github.com/rehantheorylab-pixel/35000x-faster-subset-sum-algorithm-n70.git
#      cd 35000x-faster-subset-sum-algorithm-n70
#      .\install.ps1
#
#  After that, type "algorithm" from any PowerShell window.
# ============================================================

$ScriptDir   = Split-Path -Parent $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = (Get-Location).Path }

$PyScript    = Join-Path $ScriptDir "Z_plus_plus_gui.py"
$RustBinary  = Join-Path $ScriptDir "zpp_rust\target\release\zpp.exe"
$RustProject = Join-Path $ScriptDir "zpp_rust"
$RepoExe     = Join-Path $ScriptDir "zpp.exe"

if (-not (Test-Path $PyScript)) {
    Write-Host "ERROR: Z_plus_plus_gui.py not found at $PyScript" -ForegroundColor Red
    Write-Host "Run this script from the repo root directory." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
    Write-Host "Created PowerShell profile at $PROFILE" -ForegroundColor Yellow
}

# Strip prior install of the function so we can rewrite it cleanly.
$marker    = "# ZPP_ALGORITHM_COMMAND"
$endMarker = "# END_ZPP_ALGORITHM_COMMAND"
if (Test-Path $PROFILE) {
    $content = Get-Content $PROFILE -Raw
    if ($content -and $content.Contains($marker)) {
        $pattern = "(?s)" + [regex]::Escape($marker) + ".*?" + [regex]::Escape($endMarker)
        $content = [regex]::Replace($content, $pattern, "")
        Set-Content -Path $PROFILE -Value $content
    }
}

$func = @"

$marker
function algorithm {
    `$script_dir = Split-Path -Parent (Split-Path -Parent (Get-Command algorithm).Source)
    `$rust_bin = Join-Path "`$script_dir" "zpp_rust\target\release\zpp.exe"
    `$exe_bin = Join-Path "`$script_dir" "zpp.exe"
    `$rust_proj = Join-Path "`$script_dir" "zpp_rust"
    `$py_script = Join-Path "`$script_dir" "Z_plus_plus_gui.py"

    if (Test-Path `$exe_bin) {
        & `$exe_bin @args
    } elseif (Test-Path `$rust_bin) {
        & `$rust_bin @args
    } elseif (Test-Path `$rust_proj) {
        Write-Host "Building Z++ engine (one-time, ~1 minute)..." -ForegroundColor Yellow
        Push-Location `$rust_proj
        try {
            cargo build --release
            if (Test-Path `$rust_bin) {
                Write-Host "Built. Launching." -ForegroundColor Green
                & `$rust_bin @args
            } else {
                Write-Host "Build failed. Falling back to Python version." -ForegroundColor Yellow
                python "`$py_script" @args
            }
        } finally { Pop-Location }
    } else {
        Push-Location "`$script_dir"
        try { python "`$py_script" @args }
        finally { Pop-Location }
    }
}
$endMarker
"@

Add-Content -Path $PROFILE -Value $func
Write-Host "Installed 'algorithm' command into $PROFILE" -ForegroundColor Green

if ((Get-ExecutionPolicy -Scope CurrentUser) -in @('Restricted','Undefined')) {
    Write-Host ""
    Write-Host "NOTE: PowerShell may block profile loading by default." -ForegroundColor Yellow
    Write-Host "If 'algorithm' does not work after restart, run this once:" -ForegroundColor Yellow
    Write-Host "  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor White
}

Write-Host ""
if (Test-Path $RepoExe) {
    Write-Host "Pre-built binary found: algorithm will use zpp.exe (no Rust needed)." -ForegroundColor Green
} elseif (Test-Path $RustBinary) {
    Write-Host "Built binary found at: $RustBinary" -ForegroundColor Green
} else {
    Write-Host "Binary NOT YET BUILT." -ForegroundColor Yellow
    Write-Host "On first 'algorithm' run, it will auto-build (~1 minute)." -ForegroundColor Yellow
    Write-Host "Or download pre-built zpp.exe from GitHub Releases." -ForegroundColor Gray
}

Write-Host ""
Write-Host "DONE. Reload your profile in this window with:" -ForegroundColor Green
Write-Host "    . `$PROFILE" -ForegroundColor Yellow
Write-Host "Or open a NEW PowerShell window, then type:  algorithm" -ForegroundColor White
Write-Host ""
