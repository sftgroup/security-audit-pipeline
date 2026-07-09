#!/bin/bash
# ============================================================================
# Security Tools Server — 42 Tools One-Click Install
# ============================================================================
# Run on target server (43.156.78.59) to install all security tools.
# After install, the MCP server can call any tool via subprocess.
#
# Usage: sudo bash install.sh
# ============================================================================

set -euo pipefail

log() { echo "[$(date +%H:%M:%S)] $*"; }
error() { echo "[$(date +%H:%M:%S)] ❌ $*" >&2; }

log "=== Security Tools Server Install ==="
log "Target: $(hostname) | OS: $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY | cut -d'"' -f2)"

# ============================================================
# Prerequisites
# ============================================================
log "Installing prerequisites..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    curl wget unzip tar git python3 python3-pip \
    nodejs npm golang-go build-essential cmake \
    nmap nikto whatweb lynis openssl \
    apt-transport-https ca-certificates gnupg lsb-release 2>&1 | tail -3

# Docker (for ZAP, docker-bench)
if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -qq && sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
fi

# ============================================================
# Contract Scanning Tools (16)
# ============================================================
log "=== Contract Scanning Tools ==="

# Foundry (forge, cast)
log "[1/16] Foundry..."
if ! command -v forge &>/dev/null; then
    curl -L https://foundry.paradigm.xyz | bash 2>&1 | tail -1
    export PATH="$HOME/.foundry/bin:$PATH"
    foundryup 2>&1 | tail -1
fi

# Slither
log "[2/16] Slither..."
pip3 install --break-system-packages slither-analyzer crytic-compile 2>&1 | tail -1

# Aderyn
log "[3/16] Aderyn..."
if ! command -v aderyn &>/dev/null; then
    curl -L https://raw.githubusercontent.com/Cyfrin/aderyn/dev/cyfrinup/install | bash 2>&1 | tail -1
    export PATH="$HOME/.cyfrin/bin:$PATH"
    cyfrinup 2>&1 | tail -1
fi

# Mythril
log "[4/16] Mythril..."
pip3 install --break-system-packages mythril 2>&1 | tail -1

# Semgrep
log "[5/16] Semgrep..."
pip3 install --break-system-packages semgrep 2>&1 | tail -1

# Solhint
log "[6/16] Solhint..."
npm install -g solhint 2>&1 | tail -1

# Echidna
log "[7/16] Echidna..."
if ! command -v echidna-test &>/dev/null; then
    curl -sL https://github.com/crytic/echidna/releases/latest/download/echidna-test-ubuntu-latest.tar.gz -o /tmp/echidna.tar.gz
    sudo tar xzf /tmp/echidna.tar.gz -C /usr/local/bin/
    sudo chmod +x /usr/local/bin/echidna-test
fi

# npm/pnpm
log "[8/16] npm/pnpm..."
if ! command -v pnpm &>/dev/null; then
    npm install -g pnpm 2>&1 | tail -1
fi

# nmap (already installed from prerequisites)
log "[9/16] nmap..."
nmap --version | head -1

# Nuclei
log "[10/16] Nuclei..."
if ! command -v nuclei &>/dev/null; then
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest 2>&1 | tail -1
    export PATH="$HOME/go/bin:$PATH"
fi

# ZAP
log "[11/16] OWASP ZAP..."
docker pull owasp/zap2docker-stable 2>&1 | tail -1 || log "   ZAP docker pull skipped"

# cast (with forge)
log "[12/16] cast..."
forge --version 2>/dev/null && cast --version 2>/dev/null

# ============================================================
# Additional Centralized Tools (20 more)
# ============================================================
log "=== Centralized Scanning Tools ==="

# Bandit
log "[13] Bandit..."
pip3 install --break-system-packages bandit 2>&1 | tail -1

# gosec
log "[14] gosec..."
if ! command -v gosec &>/dev/null; then
    curl -sfL https://raw.githubusercontent.com/securego/gosec/master/install.sh | sh -s -- -b /usr/local/bin latest 2>&1 | tail -1
fi

# ESLint + security plugin
log "[15] eslint-plugin-security..."
npm install -g eslint eslint-plugin-security 2>&1 | tail -1

# Gitleaks
log "[16] Gitleaks..."
if ! command -v gitleaks &>/dev/null; then
    GITLEAKS_VER=$(curl -s https://api.github.com/repos/gitleaks/gitleaks/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
    curl -sL "https://github.com/gitleaks/gitleaks/releases/download/${GITLEAKS_VER}/gitleaks_${GITLEAKS_VER#v}_linux_amd64.tar.gz" -o /tmp/gitleaks.tar.gz
    sudo tar xzf /tmp/gitleaks.tar.gz -C /usr/local/bin/ gitleaks
    sudo chmod +x /usr/local/bin/gitleaks
fi

# Trivy
log "[17] Trivy..."
if ! command -v trivy &>/dev/null; then
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh -s -- -b /usr/local/bin latest 2>&1 | tail -1
fi

# pip-audit
log "[18] pip-audit..."
pip3 install --break-system-packages pip-audit 2>&1 | tail -1

# cargo-audit
log "[19] cargo-audit..."
if command -v cargo &>/dev/null; then
    cargo install cargo-audit 2>&1 | tail -1 || true
fi

# ffuf
log "[20] ffuf..."
if ! command -v ffuf &>/dev/null; then
    go install -v github.com/ffuf/ffuf/v2@latest 2>&1 | tail -1
fi

# testssl.sh
log "[21] testssl.sh..."
if [ ! -d /opt/testssl ]; then
    sudo git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl 2>&1 | tail -1
    sudo ln -sf /opt/testssl/testssl.sh /usr/local/bin/testssl
fi

# whatweb (prerequisites)
log "[22] whatweb..."
whatweb --version 2>/dev/null | head -1 || true

# nikto (prerequisites)
log "[23] nikto..."
nikto -Version 2>/dev/null | head -1 || true

# lynis (prerequisites)
log "[24] lynis..."
lynis --version 2>/dev/null | head -1 || true

# Python MCP SDK
log "[25] mcp SDK..."
pip3 install --break-system-packages mcp>=1.0.0 httpx 2>&1 | tail -1

# ============================================================
# Verify
# ============================================================
log "=== Verification ==="

TOOLS=(
    "forge" "cast" "slither" "aderyn" "myth" "semgrep" "solhint"
    "echidna-test" "npm" "pnpm" "nmap" "nuclei" "bandit" "gosec"
    "eslint" "gitleaks" "trivy" "pip-audit" "ffuf" "testssl"
    "whatweb" "nikto" "lynis" "python3"
)

PASS=0
FAIL=0
for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &>/dev/null; then
        echo "  ✅ $tool"
        PASS=$((PASS + 1))
    else
        echo "  ⚠️  $tool (not found, may still work via alternate path)"
        FAIL=$((FAIL + 1))
    fi
done

log ""
log "=== Install Complete ==="
log "  ✅ $PASS tools verified"
log "  ⚠️  $FAIL tools may need manual install"
log ""
log "  Deploy MCP Server:"
log "    python3 server.py   # stdio mode"
log "    # Or via systemd for persistent mode"
