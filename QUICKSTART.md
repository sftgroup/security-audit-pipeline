# Security Audit Pipeline — Quick Start

全栈三层安全审计流水线接入指南。**10 分钟从零到跑通。**

---

## 前置条件

- OpenClaw Gateway 已运行（`openclaw gateway status`）
- 能访问 MCP 服务器 `43.156.46.187`（端口 3000/9001）
- 需要审计的项目已 rsync 到 MCP 服务器

---

## 架构概览

```
你的 Agent (team2)
  │
  │  下发任务：spawn security / security-check / centralized / qa
  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  43.156.46.187                                                        │
│                                                                      │
│  :3000  security-tools  合约+中心化+上线后审计 (46 tools, 3 entry)   │
│  :9001  code-review     代码质量机械检查 (7 tools)                   │
│  :3082  git             代码提交/同步 (19 tools)                     │
└──────────────────────────────────────────────────────────────────────┘
```

子代理不需要安装任何工具，直接调原生 MCP 函数即可。

---

## Step 1: 安装 Skill

```bash
# Clone agent 仓库（如果还没 clone）
git clone https://github.com/sftgroup/agent.git /tmp/agent-skills

# 安装 Skill
openclaw skills install /tmp/agent-skills/skills/security-audit-pipeline
```

验证：

```bash
openclaw skills list | grep security-audit
# 应显示 ✓ ready
```

---

## Step 2: 注册 MCP Server

> ⚠️ 注册前确认端口可达：`curl -s http://43.156.46.187:3000/ | head -1`

```bash
# security-tools — 合约+中心化+上线后 (46 tools)
openclaw mcp add security-tools \
  --url http://43.156.46.187:3000/sse \
  --transport sse \
  --timeout 300

# code-review — 代码质量检查 (7 tools)
openclaw mcp add code-review \
  --url http://43.156.46.187:9001/mcp \
  --transport streamable-http \
  --timeout 30
```

验证：

```bash
openclaw mcp probe security-tools --json
# 应看到 "tools": 46 以及 security-tools__contract_audit 等工具

openclaw mcp probe code-review --json
# 应看到 "tools": 7 以及 code-review__review_all 等工具
```

---

## Step 3: 更新子代理 AGENTS.md

### 3.1 复制 AGENTS.md 模板

```bash
mkdir -p ~/.openclaw/workspace/security
cp /tmp/agent-skills/agents/security/AGENTS.md ~/.openclaw/workspace/security/AGENTS.md

mkdir -p ~/.openclaw/workspace/security-check
cp /tmp/agent-skills/agents/security-check/AGENTS.md ~/.openclaw/workspace/security-check/AGENTS.md

mkdir -p ~/.openclaw/workspace/security-check-centralized
cp /tmp/agent-skills/agents/security-check-centralized/AGENTS.md ~/.openclaw/workspace/security-check-centralized/AGENTS.md
```

### 3.2 确保子代理注册到 openclaw.json

在你的 `~/.openclaw/openclaw.json` 的 `agents.list` 中确保以下入口存在：

```json
{
  "agents": {
    "list": [
      {
        "id": "security",
        "workspace": "workspace/security",
        "description": "L3 深度安全审计",
        "model": "zhipu/glm-5.2"
      },
      {
        "id": "security-check",
        "workspace": "workspace/security-check",
        "description": "合约安全扫描"
      },
      {
        "id": "security-check-centralized",
        "workspace": "workspace/security-check-centralized",
        "description": "中心化项目扫描"
      },
      {
        "id": "qa",
        "workspace": "workspace/qa",
        "description": "L1+L2 代码审查"
      }
    ]
  }
}
```

> ⚠️ **安全审计（security）必须用 `zhipu/glm-5.2`** — SCSVS 85 项深度审计需要 128K context，deepseek-v4-pro (32K) 会截断。

### 3.3 定制 AGENTS.md（按项目类型）

| 项目类型 | 需要 spawn | 用到哪些 MCP 工具 |
|----------|-----------|-------------------|
| 纯合约 | qa + security + security-check | security-tools__contract_audit() + code-review__review_all() |
| 纯中心化 | qa + centralized | security-tools__centralized_audit() + code-review__review_all() |
| 混合 | 全部 | 上面两种都要 |

打开 AGENTS.md → 删掉不需要的项目类型说明 → 5 分钟搞定。

---

## Step 4: 修改主 Agent AGENTS.md

在你的主 agent（team2 / team4 / team5 等）的 AGENTS.md 中加入：

```markdown
### 5.1 子代理 MCP 调用速查

| 子代理 | 核心 MCP 入口 |
|--------|--------------|
| qa | `code-review__review_all()` / `code-review__report()` |
| security | `security-tools__contract_audit()` / `security-tools__query_intelligence()` |
| security-check | `security-tools__contract_audit()` |
| centralized | `security-tools__centralized_audit()` / `security-tools__production_audit()` |

### 审计流程

① 判断项目类型 → rsync 到 MCP 服务器 `/opt/mcp/repos/{team}`
② 并行 spawn qa + security + security-check + centralized
③ 子代理调 MCP 原生工具 → 分批 write 报告
④ 架构师汇总 → 修 Critical+High → 汇报
```

完整模板参考：[sftgroup/agent](https://github.com/sftgroup/agent/blob/master/docs/team2-AGENTS.md)

---

## Step 5: 重启 Gateway

```bash
openclaw gateway restart
```

⚠️ **必须重启**，否则 tool 列表为空。

---

## Step 6: rsync 项目到 MCP 服务器

```bash
# 所有子代理扫描都需要 MCP 服务器上的项目路径
sshpass -p 'Asdf1234!' ssh ubuntu@43.156.46.187 "mkdir -p /opt/mcp/repos/{team}"
rsync -avz --delete {你的项目根目录}/ ubuntu@43.156.46.187:/opt/mcp/repos/{team}/
```

---

## Step 7: 验证 — 跑一次完整审计

### 快速测试（30秒）

```bash
# 在当前 session 直接调 MCP 工具确认连通
security-tools__contract_audit({"project_path":"/opt/mcp/repos/team2","scope":"static"})
# 应返回 build + test + slither 的摘要
```

### 完整审计（spawn 子代理）

```bash
# 并行 spawn 4 个子代理
sessions_spawn security "对项目执行深度安全审计:
- 项目: /opt/mcp/repos/team2
- security-tools__contract_audit(project_path='/opt/mcp/repos/team2', scope='full')
- security-tools__query_intelligence(category='defi')
- 威胁建模 + 钱流分析 + SCSVS 85项
- 产出: /opt/mcp/repos/team2/test-reports/SECURITY_REVIEW_REPORT.md"

sessions_spawn security-check "对项目执行合约扫描:
- security-tools__contract_audit(project_path='/opt/mcp/repos/team2', scope='full')
- SCSVS 映射 + Immunefi 对标
- 产出: /opt/mcp/repos/team2/test-reports/SECURITY_SCAN_REPORT.md"

sessions_spawn qa "对项目执行代码审查:
- code-review__review_all(project_path='/opt/mcp/repos/team2', language='all')
- L1+L2+L3 代码审查
- 产出: /opt/mcp/repos/team2/test-reports/QA_REVIEW_REPORT.md"

sessions_spawn security-check-centralized "对项目执行中心化扫描:
- security-tools__centralized_audit(project_path='/opt/mcp/repos/team2', scope='all', language='auto')
- OWASP 映射
- 产出: /opt/mcp/repos/team2/test-reports/SECURITY_SCAN_REPORT_CENTRALIZED.md"
```

全部完成后，架构师汇总 4 份报告 → 修 Critical+High → 部署 → 回归测试 → 汇报。

---

## 关键词速查

| 关键词 | 含义 |
|--------|------|
| `contract_audit` | 46 个工具中最重要的入口 — 合约全量审计（forge build + test + slither + aderyn + mythril + echidna + semgrep + solhint + gitleaks + npm audit） |
| `centralized_audit` | 中心化项目全量审计 — SAST + DAST + SCA + Infra + Compliance |
| `production_audit` | 上线后安全检测 — 24 项（TLS/headers/CORS/端口/漏洞扫描） |
| `security-tools__` | security-tools MCP 的前缀，46 个工具都有此前缀 |
| `code-review__` | code-review MCP 的前缀，7 个工具都有此前缀 |
| `scope="full"` | 跑全部检测（static + symbolic + secrets + deps） |
| `scope="static"` | 仅静态分析（build + test + slither + aderyn + semgrep + solhint） |
| `SCSVS` | Smart Contract Security Verification Standard — 85 项检查清单 |
| `Immunefi` | DeFi Bug Bounty 标准严重度分级 |
| `/opt/mcp/repos/{team}` | MCP 服务器上的项目路径，所有扫描依赖此路径 |

---

## 排错

| 现象 | 原因 | 解决 |
|------|------|------|
| `security-tools__contract_audit not found` | 没注册 MCP 或没重启 | Step 2 → Step 5 |
| 子代理 spawn 后没有 MCP 工具 | openclaw.json 里 agent 没注册 | Step 3.2 |
| security 子代理输出被截断 | 用了 deepseek-v4-pro (32K) | 改为 `"model": "zhipu/glm-5.2"` |
| probe 0 tools | transport 配错 | security-tools 用 `sse` + `/sse`，code-review 用 `streamable-http` + `/mcp` |
| MCP 返回 "tool not found" | 工具名没加前缀 | 必须是 `security-tools__contract_audit`，不能写成 `contract_audit` |
| forge build 失败 | 项目没 rsync 或 foundry.toml 不在根目录 | 确认 rsync 后再试 |
| slither/aderyn/mythril 结果为空 | MCP 服务器上工具未安装 | 参考 `references/tool-install.md` 安装 |
| QA 报告只有 L0 没 L1/L2 | QA 子代理只调了 code-review 没读源码 | AGENTS.md 里强调必须先 L0 再 L1/L2 |
| 子代理用了 `exec curl` 而不是 MCP 工具 | AGENTS.md 里还有旧版 curl 指令 | 检查 AGENTS.md 没有 `exec curl` 字样 |

---

## 完整审计交付物

| 报告 | 产出路径 | 审查者 |
|------|---------|--------|
| E2E_TEST_REPORT.md | test-reports/ | tester |
| QA_REVIEW_REPORT.md | test-reports/ | qa |
| SECURITY_REVIEW_REPORT.md | test-reports/ | security (GLM-5.2) |
| SECURITY_SCAN_REPORT.md | test-reports/ | security-check |
| SECURITY_SCAN_REPORT_CENTRALIZED.md | test-reports/ | security-check-centralized |

---

## 下一步

- 设置 cron 自动更新知识库：`cron add` 每天 06:00 执行 `scripts/update-security-kb.sh`
- 定期同步 agent repo 获取最新 AGENTS.md：`git pull` + `openclaw skills install`
- 查看 SCSVS 85 项完整清单：`references/scsvs-matrix-v2.md`
- 查看已安装工具：`ssh ubuntu@43.156.46.187 "which slither aderyn mythril semgrep solhint bandit gitleaks trivy nuclei nmap nikto whatweb lynis testssl"`

---

**版本: v3.0** — MCP Native Tools（`security-tools__*()` / `code-review__review_all()` / `git__*()`），子代理零安装，全栈覆盖 85 项 SCSVS + OWASP Top 10。
