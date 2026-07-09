---
name: security-audit-pipeline
description: "三层AI安全审计流水线:qa+security+security-check(合约/中心化)。14源威胁情报+MCP入口工具。"
---

# Security Audit Pipeline

三层 AI Agent 安全审计流水线，覆盖合约安全审计 + 中心化应用安全审计 + 上线后生产环境安全检测。

Agent 加载此 Skill 后通过 MCP 调用 3 个入口工具完成全量审计，无需自己安装任何扫描工具。

## 核心：MCP 入口工具（Agent 只需调这 3 个）

MCP Server 部署在 43.156.46.187:3000 (HTTP SSE)，systemd 守护。

### 1. `contract_audit` — 智能合约安全审计

```json
{ "project_path": "/path/to/foundry/project", "scope": "all", "deployed_address": "0x..." }
```

内部自动编排：`forge build → forge test → slither → aderyn → mythril → echidna → semgrep → solhint → grep secrets → npm audit`

返回归一化报告含 `summary.risk_level` (CRITICAL/HIGH/MEDIUM/LOW) + 各子工具详细结果。

### 2. `centralized_audit` — 中心化应用安全审计

```json
{ "project_path": "/path/to/project", "target_url": "https://app.example.com", "scope": "all", "language": "js" }
```

内部自动编排：SAST (semgrep/bandit/gosec/eslint/gitleaks) + DAST (nuclei/nikto/ZAP) + SCA (npm/pip/cargo/trivy) + Infra (nmap/lynis) + Compliance (testssl/cors/headers/whatweb)

### 3. `production_audit` — 上线后生产安全审计

```json
{ "target_url": "https://app.example.com", "domain": "all", "apk_path": "/tmp/app.apk", "deep": false }
```

内部自动编排：SQL注入/XSS/Wapiti/目录爆破/子域名 + CORS/Headers/SSL/Cookie/JWT/RateLimit + APK分析/密钥扫描 + 端口扫描/SSH/指纹 + OWASP ZAP

### 可选：威胁情报查询 (intel, 6 tools)

`update_knowledge_base` / `query_intelligence` / `get_latest_attacks` / `check_cve` / `compare_snapshots` / `search_ttp`

审计前建议先调 `query_intelligence(category="defi")` 获取最新攻击情报注入上下文。

## 项目类型 → 路由

| 特征 | 审计入口 |
|------|---------|
| `contracts/src/*.sol` + `foundry.toml` | `contract_audit` |
| 无合约文件 (Node.js/React/Python/Go) | `centralized_audit` |
| 两者都有 | `contract_audit` + `centralized_audit` |
| 已上线(有 URL/APK) | 上述 + `production_audit` |

## 审计流程

1. 判断项目类型 → 选入口工具
2. 调 `query_intelligence` 加载最新攻击情报
3. 调 `contract_audit` / `centralized_audit` / `production_audit`
4. 读返回的 `summary.risk_level` + 各子工具详细结果
5. `CRITICAL`/`HIGH` → 修复 → 重新审计回归
6. 将最终报告写入 `test-reports/SECURITY_AUDIT_REPORT.md`

## 知识库（14源，每天自动更新）

```
Knowledge Base: ~/.openclaw/security-kb/
  attack-matrix-{DATE}.json  — 最新威胁快照 (JSON)
  attack-matrix-{DATE}.md    — 最新威胁快照 (Markdown)
```

cron: `0 6 * * * {SKILL_DIR}/scripts/update-security-kb.sh`

## 资产（子 Agent 按需读取）

| 资产 | 路径 | 用途 |
|------|------|------|
| Echidna Harness ×3 | `assets/echidna-harnesses/` | DeFi/AMM/Lending Fuzzing 模板 |
| Slither Detector ×5 | `assets/slither-detectors/` | SCSVS 对齐的自定义检测器 |
| Nuclei 模板 ×5 | `assets/nuclei-templates/` | OWASP 对齐的 DAST 模板 |
| SCSVS 85项矩阵 | `references/scsvs-matrix-v2.md` | 完整检查表 |
| 14源详情 | `references/attack-sources.md` | 情报源清单 |
| OWASP 工具覆盖 | `references/owasp-mapping.md` | ~80% 覆盖映射 |
| 工具安装命令 | `references/tool-install.md` | 20+ 工具安装 |

## 严重度标准 (Immunefi + OWASP)

| Level | 合约 (Immunefi) | 中心化 (OWASP) |
|-------|-------------------|-------------------|
| 🔴 Critical | ≥$100K loss, unrestricted fund drain | RCE, 数据泄露, 认证绕过 |
| 🟠 High | Single-point breach, privileged exploit | XSS/SSRF/IDOR, 逻辑绕过 |
| 🟡 Medium | Conditional combo, gas griefing | 配置不当, 信息泄露 |
| 🟢 Low | Best practice, style | Headers, cookies, 指纹 |
