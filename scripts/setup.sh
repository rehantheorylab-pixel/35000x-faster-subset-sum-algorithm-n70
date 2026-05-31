#!/usr/bin/env bash
# Z++ Ultra - Universal Installer (Linux/macOS)
# Usage (Quick - Python mode, no Rust needed):
#   chmod +x scripts/setup.sh && ./scripts/setup.sh --quick
# Usage (Full - build from source, default):
#   chmod +x scripts/setup.sh && ./scripts/setup.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

QUICK=false
if [ "$1" = "--quick" ] || [ "$1" = "-q" ]; then
    QUICK=true
fi

echo "========================================"
if [ "$QUICK" = true ]; then
    echo "  Z++ Ultra Quick Install (Python mode)"
else
    echo "  Z++ Ultra Full Install (From Source)"
fi
echo "  Repository: $REPO_ROOT"
echo "========================================"
echo ""

echo_step() {
    echo "  [$1/4] $2"
}

echo_done() {
    echo "    $1"
}

if [ "$QUICK" = true ]; then
    # Quick mode: check for existing binary or use Python
    echo_step 1 "Checking for existing binary..."

    if [ -f "$REPO_ROOT/zpp" ]; then
        chmod +x "$REPO_ROOT/zpp"
        echo_done "Binary found: $REPO_ROOT/zpp"
    elif [ -f "$REPO_ROOT/zpp.exe" ]; then
        chmod +x "$REPO_ROOT/zpp.exe" 2>/dev/null || true
        echo_done "Binary found: $REPO_ROOT/zpp.exe (Windows binary, use Python instead)"
    else
        echo_done "No binary found. Will use Python mode (slower but works)."
    fi

    echo_step 2 "Python dependencies..."
    pip3 install numpy psutil 2>/dev/null || pip install numpy psutil 2>/dev/null || true

    echo_step 3 "Setting up 'algorithm' command..."
else
    # Full mode: build from source
    echo_step 1 "Checking Rust installation..."
    if ! command -v rustc &> /dev/null; then
        echo "  Rust not found. Installing via rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source "$HOME/.cargo/env"
        echo_done "Rust installed."
    else
        echo_done "Rust found: $(rustc --version)"
    fi

    echo_step 2 "Building Z++ engine from source..."
    cd "$REPO_ROOT/zpp_rust"
    cargo build --release
    cp target/release/zpp "$REPO_ROOT/zpp" 2>/dev/null || cp target/release/zpp.exe "$REPO_ROOT/zpp" 2>/dev/null || true
    echo_done "Build complete (maximum performance)."

    echo_step 3 "Python dependencies..."
    pip3 install numpy psutil 2>/dev/null || pip install numpy psutil 2>/dev/null || true

    echo_step 4 "Setting up 'algorithm' command..."
fi

# Create algorithm script
ALG_CMD="$REPO_ROOT/algorithm"
cat > "$ALG_CMD" << 'SCRIPT'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
if [ -f "$DIR/zpp" ] && [ -x "$DIR/zpp" ]; then
    "$DIR/zpp" "$@"
elif [ -f "$DIR/zpp.exe" ] && [ -x "$DIR/zpp.exe" ]; then
    "$DIR/zpp.exe" "$@"
elif command -v python3 &> /dev/null; then
    python3 Z++.py "$@"
else
    python Z++.py "$@"
fi
SCRIPT
chmod +x "$ALG_CMD"

# Add to PATH
SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then SHELL_RC="$HOME/.bashrc"; fi
if [ -f "$HOME/.zshrc" ]; then SHELL_RC="$HOME/.zshrc"; fi
if [ -n "$SHELL_RC" ]; then
    if ! grep -q "$REPO_ROOT" "$SHELL_RC" 2>/dev/null; then
        echo "export PATH=\"$REPO_ROOT:\$PATH\"" >> "$SHELL_RC"
        echo_done "Added to $SHELL_RC"
    fi
fi

echo ""
echo "========================================"
echo "  INSTALLATION COMPLETE!"
echo "========================================"
echo ""
echo "  Open a new terminal and type: algorithm"
echo ""
echo "  Quick test:"
echo "    algorithm 23,45,67,89,12,34,56,78,90,11 200"
echo ""
echo "  Expected output:"
echo "    EXACT: True  Engine: Hard-U128  Time: 0.0234s"
echo "    Solution: [23, 45, 67, 65]"
echo ""
echo "  Run full test suite:"
echo "    python3 tests/test_zpp.py"
echo ""
echo "  Location: $REPO_ROOT"
