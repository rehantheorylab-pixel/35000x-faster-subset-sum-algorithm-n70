#!/usr/bin/env bash
# ============================================================
#  Z++ Ultimate Engine — One-Line Installer (Linux / macOS)
#
#  curl -fsSL https://raw.githubusercontent.com/<USER>/zpp/main/install.sh | bash
#
#  What this does:
#    1. Verifies (or installs) Rust toolchain via rustup
#    2. Clones the repo to ~/.local/share/zpp
#    3. Builds the release binary
#    4. Adds an `algorithm` shell function to ~/.bashrc and ~/.zshrc
# ============================================================

set -euo pipefail

# IMPORTANT: edit this to your GitHub username after first push.
REPO_URL="https://github.com/REPLACE_USERNAME/zpp.git"

INSTALL_ROOT="${HOME}/.local/share/zpp"
BIN_PATH="${INSTALL_ROOT}/target/release/zpp"

step() { printf "\n==> %s\n" "$1"; }

step "Checking prerequisites"
command -v git >/dev/null 2>&1 || {
    echo "Error: 'git' not found. Install it first." >&2
    exit 1
}

if ! command -v cargo >/dev/null 2>&1; then
    step "Rust not found. Installing via rustup"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
    # shellcheck disable=SC1091
    . "${HOME}/.cargo/env"
fi

step "Fetching source (${REPO_URL})"
if [ -d "${INSTALL_ROOT}" ]; then
    git -C "${INSTALL_ROOT}" pull --ff-only
else
    git clone --depth 1 "${REPO_URL}" "${INSTALL_ROOT}"
fi

step "Building release binary (~1 minute)"
( cd "${INSTALL_ROOT}" && cargo build --release )

if [ ! -x "${BIN_PATH}" ]; then
    echo "Error: build finished but ${BIN_PATH} missing" >&2
    exit 1
fi

step "Adding 'algorithm' shell function"
ZPP_BLOCK_START="# ZPP_ALGORITHM_COMMAND_START"
ZPP_BLOCK_END="# ZPP_ALGORITHM_COMMAND_END"
ZPP_BLOCK="
${ZPP_BLOCK_START}
algorithm() {
    \"${BIN_PATH}\" \"\$@\"
}
${ZPP_BLOCK_END}
"

inject_block() {
    local rcfile="$1"
    [ -f "${rcfile}" ] || return 0
    if grep -q "${ZPP_BLOCK_START}" "${rcfile}"; then
        # Strip prior block, then re-append fresh.
        local tmp
        tmp="$(mktemp)"
        awk -v s="${ZPP_BLOCK_START}" -v e="${ZPP_BLOCK_END}" '
            $0 == s {skip=1; next}
            $0 == e {skip=0; next}
            !skip {print}
        ' "${rcfile}" > "${tmp}"
        mv "${tmp}" "${rcfile}"
    fi
    printf "%s" "${ZPP_BLOCK}" >> "${rcfile}"
    echo "  + updated ${rcfile}"
}

inject_block "${HOME}/.bashrc"
inject_block "${HOME}/.zshrc"
[ -f "${HOME}/.profile" ] || true

step "Installed."
cat <<EOF

  Binary : ${BIN_PATH}
  Source : ${INSTALL_ROOT}

  Open a new shell, or run:
      source ~/.bashrc      # or ~/.zshrc

  Then type:
      algorithm

EOF
