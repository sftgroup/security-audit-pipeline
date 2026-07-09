# 安全工具安装指南

## 合约扫描工具

```bash
# 核心工具
pip3 install --break-system-packages slither-analyzer crytic-compile mythril semgrep 2>&1 || true
npm install -g solhint 2>&1 || true

# Aderyn (Cyfrin Rust)
curl -L https://raw.githubusercontent.com/Cyfrin/aderyn/dev/cyfrinup/install | bash 2>&1 && cyfrinup 2>&1 || true

# Echidna
curl -sL https://github.com/crytic/echidna/releases/latest/download/echidna-test-ubuntu-latest.tar.gz -o /tmp/echidna.tar.gz
tar xzf /tmp/echidna.tar.gz -C /usr/local/bin/ 2>&1 || true
chmod +x /usr/local/bin/echidna-test 2>/dev/null || true

# Foundry
curl -L https://foundry.paradigm.xyz | bash 2>&1 && foundryup 2>&1 || true

# 网络扫描
sudo apt-get install -y nmap 2>&1 || true
curl -sL https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip -o /tmp/nuclei.zip
unzip -o /tmp/nuclei.zip -d /usr/local/bin/ 2>&1 || true
chmod +x /usr/local/bin/nuclei 2>/dev/null || true
```

## 中心化扫描工具

```bash
# SAST
pip3 install --break-system-packages semgrep bandit pip-audit 2>&1 || true
npm install -g eslint eslint-plugin-security 2>&1 || true

# gosec (Go)
curl -sfL https://raw.githubusercontent.com/securego/gosec/master/install.sh | sh -s -- -b /usr/local/bin latest 2>&1 || true

# gitleaks
GITLEAKS_VER=$(curl -s https://api.github.com/repos/gitleaks/gitleaks/releases/latest | grep tag_name | cut -d'"' -f4)
curl -sL "https://github.com/gitleaks/gitleaks/releases/download/${GITLEAKS_VER}/gitleaks_${GITLEAKS_VER#v}_linux_amd64.tar.gz" -o /tmp/gitleaks.tar.gz
tar xzf /tmp/gitleaks.tar.gz -C /usr/local/bin/ gitleaks 2>&1 || true
chmod +x /usr/local/bin/gitleaks 2>/dev/null || true

# trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin latest 2>&1 || true

# DAST
sudo apt-get install -y nmap nikto whatweb lynis 2>&1 || true

# nuclei
curl -sL https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip -o /tmp/nuclei.zip
unzip -o /tmp/nuclei.zip -d /usr/local/bin/ 2>&1 || true
chmod +x /usr/local/bin/nuclei 2>/dev/null || true

# ffuf
go install -v github.com/ffuf/ffuf/v2@latest 2>&1 || true

# ZAP (optional, requires Docker)
# docker pull owasp/zap2docker-stable

# testssl.sh
git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl 2>&1 || true
```

## Custom Assets (from this Skill)

```bash
# Slither custom detectors
export SLITHER_PLUGINS="{SKILL_DIR}/assets/slither-detectors"

# Echidna harnesses
cp {SKILL_DIR}/assets/echidna-harnesses/*.sol test/fuzz/

# Nuclei custom templates
nuclei -t {SKILL_DIR}/assets/nuclei-templates/ -u TARGET_URL
```

## 防火墙端口验证

```bash
nc -zv {TARGET_IP} {PORT} || echo "WARN: port unreachable"
```

## 工具可用性检查

```bash
for tool in forge slither aderyn myth solhint semgrep echidna-test nmap nuclei; do
    if command -v $tool &>/dev/null; then
        echo "✅ $tool: $(which $tool)"
    else
        echo "❌ $tool: NOT INSTALLED"
    fi
done
```
