---
name: security-audit-pipeline
description: "三层AI安全审计流水线:qa+security+security-check(合约/中心化)。14源威胁情报+REST API多MCP入口。v2.2分层取模式"
---

# Security Audit Pipeline

三层 AI Agent 安全审计流水线，覆盖合约安全审计 + 中心化应用安全审计 + 上线后生产环境安全检测。

Agent 加载此 Skill 后通过 REST API 调用 MCP 入口工具完成全量审计，无需自己安装任何扫描工具。

**当前版本: v2.2** — 分层取模式（MCP 返回摘要 + result_file，子代理按需 read 文件，省 ~95% token）

## 核心：多 MCP REST API 入口（v2.2 分层取模式）⭐

3 个 MCP 服务器，统一通过 `curl POST` REST API 调用。**v2.2 起 MCP 返回摘要 + 全量结果写入文件系统，子代理分两步走。**

### ⚠️ 分层取流程（子代理必须遵守）

```
Step 1: curl MCP → 拿到摘要 (~200字节) + result_file 路径 + sections 列表
Step 2: 看 summary — risk_level 不为 LOW 时，按需 read result_file 中有问题的 section（不是整个文件！）
```

| MCP Server | 端口 | 协议 | 用途 |
|-----------|------|------|------|
| **security-tools** | 3000 | REST `/api/tools/` | 合约+中心化+上线后审计 (46 tools, 3 entry) |
| **code-review** | 9001 | JSON-RPC `/mcp` | 代码质量机械检查 (QA L0) |
| **git** | 3082 | — | 版本控制 (当前不可用，用 md5sum 替代) |

### security-tools MCP (3000) — 3 个入口工具

```bash
curl -s -X POST http://43.156.46.187:3000/api/tools/{tool_name} \
  -H 'Content-Type: application/json' \
  -d '{"key":"value"}'
```

**注意：-d 用单引号包裹 JSON。所有工具统一此语法。**

#### `contract_audit`

```bash
curl -s -X POST http://43.156.46.187:3000/api/tools/contract_audit \
  -H 'Content-Type: application/json' \
  -d '{"project_path":"/opt/mcp/repos/team2","scope":"full"}'
```

内部编排：`forge build → forge test → slither(106) → aderyn → mythril → echidna → semgrep → solhint → grep secrets → npm audit`

**返回格式（v2.1+）：**
```json
{
  "ok": true,
  "summary": {"risk_level": "LOW", "critical": 0, "high": 0},
  "sections": ["build", "test", "slither", "aderyn", ...],
  "result_file": "/opt/mcp/repos/team2/mcp-output/contract_audit_latest.json",
  "hint": "Full result saved. Read result_file for details."
}
```

#### `centralized_audit`

```bash
curl -s -X POST http://43.156.46.187:3000/api/tools/centralized_audit \
  -H 'Content-Type: application/json' \
  -d '{"project_path":"/opt/mcp/repos/team2","scope":"all","language":"auto"}'
```

内部编排：SAST (semgrep/bandit/gosec/eslint/gitleaks) + DAST (nuclei/zap/nikto) + SCA (npm/pip/cargo/trivy) + Infra (nmap/lynis) + Compliance (testssl/cors/headers)

#### `production_audit`

```bash
curl -s -X POST http://43.156.46.187:3000/api/tools/production_audit \
  -H 'Content-Type: application/json' \
  -d '{"target_url":"https://app.example.com","domain":"all"}'
```

24 项上线后检测。

#### 威胁情报

```bash
curl -s -X POST http://43.156.46.187:3000/api/tools/query_intelligence \
  -H 'Content-Type: application/json' \
  -d '{"category":"defi"}'
```

### code-review MCP (9001) — QA L0 机械检查

```bash
curl -s -X POST http://43.156.46.187:9001/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"review_all","arguments":{"project_path":"/opt/mcp/repos/team2","language":"all"}},"id":1}'
```

覆盖：lint (solhint/eslint/ruff/shellcheck) + format (prettier/black/shfmt) + types (tsc/mypy) + complexity + deps audit

---

## 项目类型 → 路由

| 特征 | 子代理 | 入口工具 | MCP |
|------|--------|---------|-----|
| `contracts/src/*.sol` + `foundry.toml` | qa + security + security-check | contract_audit | 3000 |
| 无合约文件 (Node.js/React/Python/Go) | qa + security-check-centralized | centralized_audit | 3000 |
| 两者都有 | qa + security + security-check + centralized | contract_audit + centralized_audit | 3000 |
| 已上线(有 URL) | 上述 + production_audit | production_audit | 3000 |

---

## 审计流程（7步）

| Step | 角色 | 动作 |
|:--:|------|------|
| 1 | 架构师 | 判断项目类型 → rsync 到 MCP 服务器 `/opt/mcp/repos/{team}` |
| 2 | 架构师 | 并行 spawn qa + security + security-check (+ centralized) |
| 3 | 子代理 | **分层取**: curl MCP → 拿摘要 → 按需 read result_file → 读源码分析 |
| 4 | 子代理 | 分批 write 报告到 `{项目}/test-reports/` |
| 5 | 架构师 | 汇总报告 → 判定严重度 → 修复 Critical+High |
| 6 | 架构师 | 部署测服 → autotest run |
| 7 | 架构师 | 汇报上级 |

---

## Spawn 模板（v2.2 分层取）

### 合约项目
```
qa agent:
  Step 1: exec curl POST http://43.156.46.187:9001/mcp → review_all → 拿结果
  Step 2: read 源码 L1+L2+L3 审查
  Step 3: 分批 write 追加 → QA_REVIEW_REPORT.md
  → 产出: {项目}/test-reports/QA_REVIEW_REPORT.md

security agent (model=zhipu/glm-5.2):  ⬅️ 注意：必须 GLM-5.2！
  Step 1: exec curl POST http://43.156.46.187:3000/api/tools/contract_audit -d '{"project_path":"/opt/mcp/repos/{team}","scope":"full"}' → 拿摘要+result_file
  Step 2: exec curl POST http://43.156.46.187:3000/api/tools/query_intelligence -d '{"category":"defi"}' → 拿情报
  Step 3: 按需 read result_file 中有问题的 section（只读有发现的部分！）
  Step 4: read 源码 → 威胁建模+钱流+SCSVS 85项 → 分批 write 追加
  → 产出: {项目}/test-reports/SECURITY_REVIEW_REPORT.md

security-check agent:
  Step 1: exec curl POST http://43.156.46.187:3000/api/tools/contract_audit -d '{"project_path":"/opt/mcp/repos/{team}","scope":"full"}' → 拿摘要+result_file
  Step 2: 按需 read result_file → SCSVS 映射 + Immunefi 对标
  → 产出: {项目}/test-reports/SECURITY_SCAN_REPORT.md
```

### 中心化项目
```
qa agent: (同上)
security-check-centralized agent:
  Step 1: exec curl POST http://43.156.46.187:3000/api/tools/centralized_audit -d '{"project_path":"/opt/mcp/repos/{team}","scope":"all","language":"auto"}' → 拿摘要+result_file
  Step 2: 按需 read result_file → OWASP 映射
  → 产出: {项目}/test-reports/SECURITY_SCAN_REPORT_CENTRALIZED.md
```

---

## 知识库（14源，每天自动更新）

```
~/.openclaw/security-kb/
  attack-matrix-{DATE}.md  — 最新威胁快照
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
| Spawn 模板 | `templates/` | 合约/中心化 spawn 指令 |

## 严重度标准 (Immunefi + OWASP)

| Level | 合约 (Immunefi) | 中心化 (OWASP) |
|-------|-------------------|-------------------|
| 🔴 Critical | ≥$100K loss, unrestricted fund drain | RCE, 数据泄露, 认证绕过 |
| 🟠 High | Single-point breach, privileged exploit | XSS/SSRF/IDOR, 逻辑绕过 |
| 🟡 Medium | Conditional combo, gas griefing | 配置不当, 信息泄露 |
| 🟢 Low | Best practice, style | Headers, cookies, 指纹 |
