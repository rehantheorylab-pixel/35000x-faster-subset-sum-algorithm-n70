# ============================================================
#  Z++ Algorithm — Local PowerShell Installer
#
#  This script wires up the `algorithm` command for the LOCAL copy
#  of Z++ at C:\Users\rehan\algorithm.  For the GitHub one-liner,
#  see zpp_rust/install.ps1 instead.
#
#  Run this ONCE in PowerShell:
#      cd C:\Users\rehan\algorithm
#      .\install_command.ps1
#
#  After that, type "algorithm" from any PowerShell window.
# ============================================================

$ScriptDir   = "C:\Users\rehan\algorithm"
$PyScript    = Join-Path $ScriptDir "Z_plus_plus_gui.py"
$RustBinary  = Join-Path $ScriptDir "zpp_rust\target\release\zpp.exe"
$RustProject = Join-Path $ScriptDir "zpp_rust"

if (-not (Test-Path $PyScript)) {
    Write-Host "ERROR: $PyScript not found." -ForegroundColor Red
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
    `$rust_bin = "$RustBinary"
    `$py_script = "$PyScript"
    `$rust_proj = "$RustProject"

    if (Test-Path `$rust_bin) {
        & `$rust_bin @args
    } elseif (Test-Path `$rust_proj) {
        Write-Host "Rust binary not found.  Building (one-time, ~1 minute)..." -ForegroundColor Yellow
        Push-Location `$rust_proj
        try {
            cargo build --release
            if (Test-Path `$rust_bin) {
                Write-Host "Built. Launching." -ForegroundColor Green
                & `$rust_bin @args
            } else {
                Write-Host "Build failed.  Falling back to Python version." -ForegroundColor Yellow
                python `$py_script @args
            }
        } finally { Pop-Location }
    } else {
        Push-Location "$ScriptDir"
        try { python `$py_script @args }
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
if (Test-Path $RustBinary) {
    Write-Host "Rust binary found: $RustBinary" -ForegroundColor Green
    Write-Host "The 'algorithm' command will use the Rust version." -ForegroundColor Green
} else {
    Write-Host "Rust binary NOT YET BUILT." -ForegroundColor Yellow
    Write-Host "On first 'algorithm' run, it will auto-build (1-minute one-time)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "DONE.  Reload your profile in this window with:" -ForegroundColor Green
Write-Host "    . `$PROFILE" -ForegroundColor Yellow
Write-Host "Or close + open a new PowerShell window, then type:  algorithm" -ForegroundColor White
Write-Host ""
Write-Host "----- To publish on GitHub later -----" -ForegroundColor Cyan
Write-Host "    cd $RustProject" -ForegroundColor Gray
Write-Host "    git init && git add . && git commit -m ""Initial release""" -ForegroundColor Gray
Write-Host "    git branch -M main" -ForegroundColor Gray
Write-Host "    git remote add origin https://github.com/<YOUR_USERNAME>/zpp.git" -ForegroundColor Gray
Write-Host "    git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "Then update REPLACE_USERNAME inside install.ps1 / install.sh." -ForegroundColor Gray
Write-Host ""
