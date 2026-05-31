#!/usr/bin/env bash
# Z++ Ultra - Universal Single-Command Installer (Linux/macOS)
# Usage: chmod +x scripts/setup.sh && ./scripts/setup.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "========================================"
echo "  Z++ Ultra Subset Sum Solver Installer"
echo "  Repository: $REPO_ROOT"
echo "========================================"
echo ""

# Step 1: Check Rust
if ! command -v rustc &> /dev/null; then
    echo "[1/4] Rust not found. Installing via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
    echo "  Rust installed."
else
    echo "[1/4] Rust found: $(rustc --version)"
fi

# Step 2: Build
echo "[2/4] Building Z++ engine..."
cd "$REPO_ROOT/zpp_rust"
cargo build --release
cp target/release/zpp "$REPO_ROOT/zpp" 2>/dev/null || cp target/release/zpp.exe "$REPO_ROOT/zpp" 2>/dev/null || true
echo "  Build complete."

# Step 3: Install Python deps
echo "[3/4] Python dependencies..."
pip3 install numpy psutil 2>/dev/null || true

# Step 4: Set up command
echo "[4/4] Creating 'algorithm' command..."
ALG_CMD="$REPO_ROOT/algorithm"
cat > "$ALG_CMD" << 'SCRIPT'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
if [ -f "$DIR/zpp" ]; then
    "$DIR/zpp" "$@"
elif [ -f "$DIR/zpp.exe" ]; then
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
        echo "  Added to $SHELL_RC"
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
echo "    algorithm 1,3,5,7,9 15"
echo ""
echo "  Location: $REPO_ROOT"
