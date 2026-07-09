---
name: security-audit-pipeline
description: "三层AI安全审计流水线：原子工具驱动(atomic-first)，agent主控决策，零自动猜测。46 MCP tools覆盖85项SCSVS+OWASP。v3.1"
---

# Security Audit Pipeline — Atomic-First

三层 AI Agent 安全审计流水线 — 合约 / 中心化 / 上线后 — 全栈覆盖。

**当前版本: v3.1** — 原子化工具签名。Agent 决策，MCP 执行。禁止工具内部自动猜测。

## 核心哲学：Agent 决策，Tool 执行

```
❌ v3.0 (旧): contract_audit(path) → 内部猜 forge/hardhat → 猜错就炸
✅ v3.1 (新): agent 读项目 → 判断 build_system → 逐个调原子工具 → agent 汇总报告
```

**每个 tool 只做一件事。** Agent 负责读项目、判断类型、选择工具链、编排顺序。

---

## 架构师自检清单（apply 后必做）

- [ ] Skill 已安装：`openclaw skills list | grep security-audit`
- [ ] security-tools MCP 已注册：`openclaw mcp list | grep security-tools`
- [ ] MCP probe 有 46 tools：`openclaw mcp probe security-tools`
- [ ] 3 安全子代理 AGENTS.md 已更新到 v10.4/v10.4/v2.4
- [ ] security 子代理 model = `zhipu/glm-5.2`，两个 check 用 `deepseek-v4-pro`
- [ ] Gateway 已重启

---

## MCP 服务器

| MCP Server | 端口 | Tools | 前缀 | 使用者 |
|-----------|------|-------|------|--------|
| **security-tools** | 3000 | 46 | `security-tools__` | security, security-check, centralized |
| **code-review** | 9001 | 7 | `code-review__` | qa |
| **git** | 3082 | 19 | `git__` | team2 (架构师) |

---

## 原子工具速查（Agent 逐个调用）

### 合约审计 — Agent 决策流

```
1. 读项目根目录 → 判断 foundry.toml (forge) 还是 hardhat.config.js (hardhat)
2. 读 src/ 和 test/ → 确认合约文件 + harness 文件
3. 按需调用以下原子工具：
```

| 工具 | 必填参数 | 调用前提 |
|------|----------|----------|
| `forge_build` | `project_path` | 始终第一步 |
| `forge_test` | `project_path`, `match?` | build 通过后 |
| `forge_coverage` | `project_path` | test 通过后 |
| `slither_scan` | `project_path`, `detect?` | 始终跑 |
| `slither_custom` | `project_path`, `detector_path` | 有自定义 detector 时 |
| `aderyn_scan` | `project_path` | 始终跑 |
| `mythril_analyze` | `project_path`, **`build_system`** | agent 先判断 forge/hardhat |
| `echidna_fuzz` | `project_path`, **`harness_path`**, **`contract_name`** | agent 先确认 harness 存在+合约名 |
| `semgrep_solidity` | `project_path`, `src_dir?` | 始终跑 |
| `solhint_lint` | `project_path`, `src_pattern?` | 始终跑 |
| `grep_secrets` | `project_path`, `patterns?` | 始终跑 |
| `npm_audit` | `project_path`, `package_manager?` | 有 package.json 时 |

### ⚠️ mythril_analyze — build_system 必填

```
agent 先判断：
  有 foundry.toml → build_system="forge"
  有 hardhat.config.js/typescript → build_system="hardhat"

调用：
  security-tools__mythril_analyze({
    project_path="/opt/mcp/repos/team3",
    build_system="forge",        ← REQUIRED
    solc_version="0.8.19"        ← 可选，从 foundry.toml 或 hardhat.config 读取
  })
```

### ⚠️ echidna_fuzz — harness_path + contract_name 必填

```
agent 先读项目：
  ls test/fuzz/ 或 test/invariants/ → 确认 .sol harness 文件存在
  read harness 文件 → 确认 contract 名称

调用：
  security-tools__echidna_fuzz({
    project_path="/opt/mcp/repos/team3",
    harness_path="test/fuzz/Invariants.sol",   ← REQUIRED
    contract_name="EchidnaInvariants",          ← REQUIRED
    test_limit=100000,                          ← 可选
    rpc_url="https://...",                      ← fork 模式需要
    block_number=12345678                       ← fork 模式需要
  })
```

如果项目没有 harness → 跳过 echidna，报告中注明原因。

---

### 中心化审计

| 工具 | 用途 | 必填参数 |
|------|------|----------|
| `semgrep_auto` | SAST (JS/TS/Python/Go) | `project_path`, `exclude?` |
| `bandit_scan` | Python security lint | `project_path` |
| `gosec_scan` | Go security scan | `project_path` |
| `eslint_security` | JS/TS security rules | `project_path` |
| `gitleaks_scan` | Hardcoded secrets | `project_path` |
| `trivy_scan` | Container + filesystem | `project_path` |
| `npm_audit` / `pip_audit` / `cargo_audit` | 依赖 CVE | `project_path` |
| `nmap_scan` | Port scan | `target`, `ports?` |
| `nuclei_scan` | Vulnerability scan | `target_url`, `severity?` |
| `zap_scan` | OWASP ZAP web scan | `target_url`, `scan_type?` |
| `check_security_headers` | HTTP headers | `target_url` |
| `check_cors` | CORS config | `target_url` |

**复合入口工具仍可用但不再推荐内部自动判断：**
```
security-tools__centralized_audit({project_path="/opt/mcp/repos/team2", scope="all"})
security-tools__production_audit({target_url="https://app.example.com", domain="all"})
```

---

### 威胁情报（始终可用）

```
security-tools__query_intelligence({category:"defi"})  // defi/web/cve/exploit/compliance
security-tools__update_knowledge_base({sources:"all"})
security-tools__compare_snapshots({category:"all"})
```

---

## 项目类型 → 路由决策

| 特征 | 必须 spawn（安全） |
|------|-------------------|
| `contracts/src/*.sol` + `foundry.toml` | security + security-check |
| 无合约文件 (Node.js/React/Python/Go) | security-check-centralized |
| 两者都有（混合项目） | security + security-check + centralized |
| 已上线（有 URL） | 上述 + production_audit |

---

## 审计流程（7 步）

| Step | 角色 | 动作 |
|:--:|------|------|
| 1 | 架构师 | 判断项目类型 → rsync 到 MCP 服务器 `/opt/mcp/repos/{team}` |
| 2 | 架构师 | 并行 spawn security + security-check + centralized（按类型） |
| 3 | 子代理 | **先读项目结构** → 判断 forge/hardhat + harness 有无 → 逐个调原子 MCP 工具 |
| 4 | 子代理 | 分批 write 报告到 `{项目}/test-reports/` |
| 5 | 架构师 | 汇总 3 份安全报告 → 修 Critical + High |
| 6 | 架构师 | 部署测服 → 回归测试 |
| 7 | 架构师 | 汇报上级 |

---

## Spawn 模板（v3.1 原子工具方式）

### 合约/混合项目

```
sessions_spawn security "模型=zhipu/glm-5.2:
1. 先读 /opt/mcp/repos/{team} 项目结构，判断 forge/hardhat、harness 文件
2. 按顺序调原子工具: forge_build → forge_test → slither_scan → aderyn_scan
3. 判断 build_system 后调 mythril_analyze
4. 确认 harness 存在后调 echidna_fuzz
5. 调 semgrep_solidity + solhint_lint + grep_secrets
6. 调 query_intelligence(category='defi')
7. 威胁建模 + 钱流 + SCSVS 85项
产出: {项目}/test-reports/SECURITY_REVIEW_REPORT.md"

sessions_spawn security-check "模型=deepseek-v4-pro:
同上原子工具流程，SCSVS 映射 + Immunefi 对标
产出: {项目}/test-reports/SECURITY_SCAN_REPORT.md"

sessions_spawn security-check-centralized "模型=deepseek-v4-pro:
security-tools__centralized_audit(project_path='/opt/mcp/repos/{team}', scope='all')
OWASP 映射
产出: {项目}/test-reports/SECURITY_SCAN_REPORT_CENTRALIZED.md"
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
| security-check | `deepseek-v4-pro` | 扫描汇总 + SCSVS 映射（不超 32K） |
| security-check-centralized | `deepseek-v4-pro` | OWASP 映射（不超 32K） |
