#!/usr/bin/env bash
set -e

echo -e "\033[36m=== Z++ Ultra Subset Sum Solver Installer ===\033[0m"
echo ""

# Step 1: Build Rust binary
if [ "$1" != "--no-build" ]; then
    echo -e "\033[33m[1/4] Building Rust engine (release mode)...\033[0m"
    RUST_DIR="$(cd "$(dirname "$0")" && pwd)/zpp_rust"
    if [ ! -d "$RUST_DIR" ]; then
        echo -e "\033[31mError: zpp_rust directory not found at $RUST_DIR\033[0m"
        exit 1
    fi
    cd "$RUST_DIR"
    cargo build --release
    echo -e "\033[32mRust engine built successfully!\033[0m"
    cd "$(dirname "$0")"
else
    echo -e "\033[33m[1/4] Skipping Rust build (--no-build flag)\033[0m"
fi

# Step 2: Check Python
echo -e "\033[33m[2/4] Checking Python...\033[0m"
if command -v python3 &> /dev/null; then
    echo -e "\033[32mPython 3 found: $(python3 --version)\033[0m"
elif command -v python &> /dev/null; then
    echo -e "\033[32mPython found: $(python --version)\033[0m"
else
    echo -e "\033[31mPython 3 is required. Install it first.\033[0m"
    exit 1
fi

# Step 3: Add to PATH
echo -e "\033[33m[3/4] Adding Z++ to PATH...\033[0m"
ALG_PATH="$(cd "$(dirname "$0")" && pwd)"
SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then SHELL_RC="$HOME/.bashrc"; fi
if [ -f "$HOME/.zshrc" ]; then SHELL_RC="$HOME/.zshrc"; fi
if [ -n "$SHELL_RC" ]; then
    if ! grep -q "$ALG_PATH" "$SHELL_RC" 2>/dev/null; then
        echo "export PATH=\"$ALG_PATH:\$PATH\"" >> "$SHELL_RC"
        echo -e "\033[32mAdded to $SHELL_RC\033[0m"
    else
        echo -e "\033[90mAlready in PATH\033[0m"
    fi
else
    echo -e "\033[33mCould not find .bashrc or .zshrc. Add this directory to your PATH manually:\033[0m"
    echo "  $ALG_PATH"
fi

# Step 4: Create algorithm symlink
echo -e "\033[33m[4/4] Creating 'algorithm' command...\033[0m"
ALG_CMD="$ALG_PATH/algorithm"
cat > "$ALG_CMD" << 'SCRIPT'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
if command -v python3 &> /dev/null; then
    python3 Z++.py "$@"
else
    python Z++.py "$@"
fi
SCRIPT
chmod +x "$ALG_CMD"
echo -e "\033[32mCreated '$ALG_CMD'\033[0m"

echo ""
echo -e "\033[36m=== Installation Complete ===\033[0m"
echo -e "\033[37mOpen a NEW terminal and type: algorithm\033[0m"
echo -e "\033[90mOr run directly: python3 Z++.py\033[0m"
