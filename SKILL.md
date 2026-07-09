---
name: security-audit-pipeline
description: "三层AI安全审计流水线：3个入口MCP工具(contract/centralized/production)覆盖85项SCSVS+OWASP，14源威胁情报。子代理原生MCP调用，零安装。v3.0"
---

# Security Audit Pipeline

三层 AI Agent 安全审计流水线 — 合约 (contract_audit) / 中心化 (centralized_audit) / 上线后 (production_audit) — 全栈覆盖。

**当前版本: v3.0** — MCP Native Tools（子代理直接调 `security-tools__*()` 函数，不 curl）。

## 架构师自检清单（apply 后必做）

- [ ] Skill 已安装：`openclaw skills list | grep security-audit`
- [ ] security-tools MCP 已注册：`openclaw mcp list | grep security-tools`
- [ ] MCP probe 有 46 tools：`openclaw mcp probe security-tools`
- [ ] 4 子代理 AGENTS.md 已更新（security/security-check/centralized/qa）
- [ ] security 子代理 model = `zhipu/glm-5.2`（SCSVS 85 项需要 128K context）
- [ ] Gateway 已重启
- [ ] 测试：`security-tools__contract_audit({"project_path":"/opt/mcp/repos/team2","scope":"static"})`

---

## 核心：多 MCP Native Tools 入口

3 个 MCP 服务器通过 OpenClaw 原生工具调用：

| MCP Server | 端口 | Tools | 前缀 | 使用者 |
|-----------|------|-------|------|--------|
| **security-tools** | 3000 | 46 | `security-tools__` | security, security-check, centralized |
| **code-review** | 9001 | 7 | `code-review__` | qa |
| **git** | 3082 | 19 | `git__` | team2 (架构师) |

### security-tools — 3 个入口工具（子代理直接调）

#### 1. `security-tools__contract_audit()` — 合约全量审计

```
security-tools__contract_audit({"project_path":"/opt/mcp/repos/team2","scope":"full"})
```

| scope | 覆盖 |
|-------|------|
| `"static"` | forge build + test + slither(106) + aderyn + semgrep + solhint |
| `"full"` | static + mythril + echidna + gitleaks + npm/pip audit |
| `"secrets"` | 仅 gitleaks + npm/pip audit |

内部编排 14 个原子子工具，自动执行。

#### 2. `security-tools__centralized_audit()` — 中心化全量审计

```
security-tools__centralized_audit({"project_path":"/opt/mcp/repos/team2","scope":"all","language":"auto"})
```

内部编排：SAST (semgrep/bandit/gosec/eslint/gitleaks) + DAST (nuclei/zap/nikto) + SCA (npm/pip/cargo/trivy) + Infra (nmap/lynis) + Compliance (testssl/cors/headers)

#### 3. `security-tools__production_audit()` — 上线后安全检测

```
security-tools__production_audit({"target_url":"https://app.example.com","domain":"all"})
```

24 项上线后检测。

#### 威胁情报

```
security-tools__query_intelligence({"category":"defi"})  // defi/web/cve/exploit
```

---

## 项目类型 → 路由决策

| 特征 | 需 spawn 的子代理 |
|------|------------------|
| `contracts/src/*.sol` + `foundry.toml` | tester + qa + security-security + security-check |
| 无合约文件 (Node.js/React/Python/Go) | tester + qa + security-check-centralized |
| 两者都有（混合项目） | tester + qa + security-security + security-check + security-check-centralized |
| 已上线（有 URL） | 上述 + 补调 production_audit |

---

## 审计流程（7 步）

| Step | 角色 | 动作 |
|:--:|------|------|
| 1 | 架构师 | 判断项目类型 → rsync 到 MCP 服务器 `/opt/mcp/repos/{team}` |
| 2 | 架构师 | 并行 spawn tester + qa + security + security-check + security-check-centralized |
| 3 | 子代理 | 直接调 `security-tools__*()` / `code-review__review_all()` 原生工具 |
| 4 | 子代理 | 分批 write 报告到 `{项目}/test-reports/` |
| 5 | 架构师 | 汇总报告 → 修 Critical + High |
| 6 | 架构师 | 部署测服 → spawn tester 回归 |
| 7 | 架构师 | 汇报上级（附 4 份报告链接） |

---

## Spawn 模板（v3.0 MCP Native）

### 合约/混合项目 — 完整 spawn

```
sessions_spawn tester "对项目执行测试:
- 项目: {项目根目录}
- MCP路径: /opt/mcp/repos/{team}
- 读: {项目}/test-reports/TEST_SCENARIOS_*.md
- 产出: {项目}/test-reports/E2E_TEST_REPORT.md"

sessions_spawn qa "对项目执行代码审查:
- 项目: {项目根目录}
- MCP路径: /opt/mcp/repos/{team}
- L0: code-review__review_all(project_path='/opt/mcp/repos/{team}', language='all')
- L1+L2: 读源码审查
- 产出: {项目}/test-reports/QA_REVIEW_REPORT.md"

sessions_spawn security "对项目执行深度安全审计:
- 项目: {项目根目录}
- MCP路径: /opt/mcp/repos/{team}
- security-tools__contract_audit(project_path='/opt/mcp/repos/{team}', scope='full')
- security-tools__query_intelligence(category='defi')
- 源码分析: 威胁建模+钱流+SCSVS 85项
- 模型: zhipu/glm-5.2 (128K context required for 85-item SCSVS)
- 产出: {项目}/test-reports/SECURITY_REVIEW_REPORT.md"

sessions_spawn security-check "对项目执行合约安全扫描:
- 项目: {项目根目录}
- MCP路径: /opt/mcp/repos/{team}
- security-tools__contract_audit(project_path='/opt/mcp/repos/{team}', scope='full')
- SCSVS 映射 + Immunefi 对标
- 产出: {项目}/test-reports/SECURITY_SCAN_REPORT.md"

sessions_spawn security-check-centralized "对项目执行中心化安全扫描:
- 项目: {项目根目录}
- MCP路径: /opt/mcp/repos/{team}
- security-tools__centralized_audit(project_path='/opt/mcp/repos/{team}', scope='all', language='auto')
- OWASP 映射
- 产出: {项目}/test-reports/SECURITY_SCAN_REPORT_CENTRALIZED.md"
```

### 纯中心化项目 — 精简 spawn

```
sessions_spawn tester → (同上)
sessions_spawn qa → (同上)
sessions_spawn security-check-centralized → (同上)
```

---

## 知识库（14源威胁情报）

```
~/.openclaw/security-kb/
  attack-matrix-{DATE}.md  — 最新威胁快照
```

cron: `0 6 * * * bash {SKILL_DIR}/scripts/update-security-kb.sh`

## Skill 资产（子代理按需读取）

| 资产 | 路径 | 用途 |
|------|------|------|
| Echidna Harness ×3 | `assets/echidna-harnesses/` | DeFi/AMM/Lending Fuzzing 模板 |
| Slither Detector ×5 | `assets/slither-detectors/` | SCSVS 对齐的自定义检测器 |
| Nuclei 模板 ×5 | `assets/nuclei-templates/` | OWASP 对齐的 DAST 模板 |
| SCSVS 85项矩阵 | `references/scsvs-matrix-v2.md` | 完整检查表 |
| 14源详情 | `references/attack-sources.md` | 情报源清单 |
| OWASP 工具覆盖 | `references/owasp-mapping.md` | ~80% 覆盖映射 |
| 工具安装命令 | `references/tool-install.md` | 20+ 工具安装到 MCP 服务器 |
| Spawn 模板 | `templates/` | 合约/中心化 spawn 指令 |

---

## 严重度标准 (Immunefi + OWASP)

| Level | 合约 (Immunefi) | 中心化 (OWASP) | 响应 |
|-------|-------------------|-------------------|------|
| 🔴 Critical | ≥$100K loss, unrestricted fund drain | RCE, 数据泄露, 认证绕过 | 🚨 立即 |
| 🟠 High | Single-point breach, privileged exploit | XSS/SSRF/IDOR, 逻辑绕过 | 🔴 24h |
| 🟡 Medium | Conditional combo, gas griefing | 配置不当, 信息泄露 | 🟠 本次迭代 |
| 🟢 Low | Best practice, style | Headers, cookies, 指纹 | 🟡 技术债 |

---

## 子代理模型要求

| 子代理 | 模型 | 原因 |
|--------|------|------|
| security | `zhipu/glm-5.2` | SCSVS 85 项 + 源码分析需要 128K context |
| security-check | `deepseek-v4-pro` | 扫描汇总 + SCSVS 映射 |
| security-check-centralized | `deepseek-v4-pro` | OWASP 映射 |
| qa | `deepseek-v4-pro` | 代码审查 L1+L2 |
| tester | `deepseek-v4-pro` | 自动化测试 |
