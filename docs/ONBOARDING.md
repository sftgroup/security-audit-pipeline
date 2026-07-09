# Security Audit Pipeline — 接入指南

> 其他 OpenClaw 实例/其他团队接入三层安全审计能力的完整步骤。
> 最后更新: 2026-07-10

---

## 总览

| 仓库 | 内容 | 版本 |
|------|------|------|
| `sftgroup/security-audit-pipeline` | Skill (SKILL.md + MCP Server 源码 + 资产) | v2.0 |
| `sftgroup/agent` | 4 个子代理 AGENTS.md | v10.1/v2.1 |
| `sftgroup/agent-team2` | 架构师 team2 AGENTS.md | v13.4 |

| MCP Server | 端口 | 协议 | 用途 |
|-----------|------|------|------|
| security-tools (合约+中心化审计) | `43.156.46.187:3000` | REST `/api/tools/` | 46 tools, 3 入口 |
| code-review (代码质量检查) | `43.156.46.187:9001` | JSON-RPC `/mcp` | lint/format/types/deps |

---

## 接入步骤

### Step 1: 拉取 Skill

```bash
mkdir -p ~/.openclaw/skills/sftgroup-agent/skills/
cd ~/.openclaw/skills/sftgroup-agent/skills/
git clone https://github.com/sftgroup/security-audit-pipeline.git security-audit-pipeline
```

### Step 2: 注册 MCP Server（可选 — 主 session 用）

编辑 `~/.openclaw/openclaw.json`，在 `plugins.entries.mcp-remote.config.servers` 下添加：

```json
{
  "security-tools": {
    "url": "http://43.156.46.187:3000/sse",
    "transport": "sse"
  },
  "code-review": {
    "url": "http://43.156.46.187:9001/sse",
    "transport": "sse"
  }
}
```

**注意：** 注册后主 session 可以直接调 MCP 工具。但 **spawn 子代理时子代理看不到 MCP 前缀工具**，子代理应直接用 curl REST API（见 Step 4）。

### Step 3: 更新子代理 AGENTS.md

```bash
cd ~/.openclaw/workspace/
# 如果有独立子代理目录
cp ~/.openclaw/skills/sftgroup-agent/skills/security-audit-pipeline/templates/qa-AGENTS.md ~/.openclaw/workspace/qa/AGENTS.md
cp ~/.openclaw/skills/sftgroup-agent/skills/security-audit-pipeline/templates/security-AGENTS.md ~/.openclaw/workspace/security/AGENTS.md
cp ~/.openclaw/skills/sftgroup-agent/skills/security-audit-pipeline/templates/security-check-AGENTS.md ~/.openclaw/workspace/security-check/AGENTS.md
cp ~/.openclaw/skills/sftgroup-agent/skills/security-audit-pipeline/templates/centralized-AGENTS.md ~/.openclaw/workspace/security-check-centralized/AGENTS.md
```

**或者直接从 GitHub 拉取最新版：**

```bash
cd ~/.openclaw/workspace/
# qa + security 子代理
curl -o qa/AGENTS.md https://raw.githubusercontent.com/sftgroup/agent/master/qa/AGENTS.md
curl -o security/AGENTS.md https://raw.githubusercontent.com/sftgroup/agent/master/security/AGENTS.md
curl -o security-check/AGENTS.md https://raw.githubusercontent.com/sftgroup/agent/master/security-check/AGENTS.md
curl -o security-check-centralized/AGENTS.md https://raw.githubusercontent.com/sftgroup/agent/master/security-check-centralized/AGENTS.md
```

### Step 4: Spawn 子代理模板

#### 合约项目
```
qa agent:
  exec curl POST http://43.156.46.187:9001/mcp → review_all + L1+L2 审查
  → {项目}/test-reports/QA_REVIEW_REPORT.md

security agent (model=zhipu/glm-5.2):
  exec curl POST http://43.156.46.187:3000/api/tools/contract_audit -d '{"project_path":"/opt/mcp/repos/{team}","scope":"full"}'
  + query_intelligence + SCSVS 85项
  → {项目}/test-reports/SECURITY_REVIEW_REPORT.md

security-check agent:
  exec curl POST http://43.156.46.187:3000/api/tools/contract_audit -d '{"project_path":"/opt/mcp/repos/{team}","scope":"full"}'
  → {项目}/test-reports/SECURITY_SCAN_REPORT.md
```

#### 中心化项目
```
qa agent: (同上)

security-check-centralized agent:
  exec curl POST http://43.156.46.187:3000/api/tools/centralized_audit -d '{"project_path":"/opt/mcp/repos/{team}","scope":"all","language":"auto"}'
  → {项目}/test-reports/SECURITY_SCAN_REPORT_CENTRALIZED.md
```

### Step 5: rsync 项目到 MCP 服务器（spawn 前）

```bash
sshpass -p 'Asdf1234!' ssh ubuntu@43.156.46.187 "mkdir -p /opt/mcp/repos/{team_name}"
rsync -avz --delete {项目路径}/ ubuntu@43.156.46.187:/opt/mcp/repos/{team_name}/
```

### Step 6: 重启 OpenClaw

```bash
openclaw gateway restart
```

---

## 子代理 AGENTS.md 核心改动说明

对比旧版，v10.1/v2.1 的核心变化：

| 改动 | 旧版 (v10.0) | 新版 (v10.1/v2.1) |
|------|-------------|-------------------|
| MCP 调用方式 | SSE 协议 `mcp__contract_audit()` | **curl REST API** `curl -s -X POST URL -d '{...}'` |
| 工具安装 | 需要手动 `pip install slither` | **不需要**，MCP 服务器已安装全部工具 |
| 代码机械检查 | 调 `mcp__review_all` | **curl POST 9001/mcp** JSON-RPC |
| 铁律 | 禁止虚假汇报 | 新增"永远不允许虚假汇报" |
| token 截断 | 无保护 | 强制分步写入文件 |

**为什么改？** `sessions_spawn` 创建的子代理看不到 `mcp__` 前缀工具名，回退到 exec 本地命令导致空跑。REST API 方式用 `exec curl` 直接调 MCP 服务器，绕过前缀问题。

---

## 验证连通性

```bash
# security-tools MCP (3000)
curl -s http://43.156.46.187:3000/health
# → {"status":"ok","server":"security-tools-mcp","tools":46,...}

# code-review MCP (9001)
curl -s -X POST http://43.156.46.187:9001/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
# → 返回工具列表

# 测试 contract_audit
curl -s -X POST http://43.156.46.187:3000/api/tools/contract_audit \
  -H 'Content-Type: application/json' \
  -d '{"project_path":"/opt/mcp/repos/team2","scope":"quick"}'
# → 返回 audit 结果
```

---

## 常见问题

**Q: MCP Server 请求超时？**
防火墙开 3000 和 9001 端口。MCP 服务器 IP: `43.156.46.187`。

**Q: `sshpass: command not found`？**
```bash
sudo apt-get install sshpass -y
```

**Q: code-review MCP 返回空？**
code-review MCP 走 JSON-RPC 协议，不是 REST。必须是 `POST /mcp` + JSON-RPC body，不能用 `/api/tools/` 路径。

**Q: 子代理 spawn 后仍然没用 MCP？**
确保 spawn task 里明确写了 curl 命令（带完整 URL + 参数），子代理不认识 `mcp__` 前缀，只能用 exec curl。
