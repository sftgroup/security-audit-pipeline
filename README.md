# Security Audit Pipeline (v3.0)

三层 AI Agent 安全审计流水线 — 合约 (contract_audit) / 中心化 (centralized_audit) / 上线后 (production_audit)。**3 个安全子代理，46 个 MCP 工具，24+ 扫描引擎，零安装。**

## 快速接入

```bash
git clone https://github.com/sftgroup/agent.git /tmp/agent-skills
openclaw skills install /tmp/agent-skills/skills/security-audit-pipeline
openclaw mcp add security-tools --url http://43.156.46.187:3000/sse --transport sse --timeout 300
openclaw gateway restart
```

## 3 个入口工具（子代理直接调）

| 入口 | 调用方式 | 覆盖 |
|------|---------|------|
| `contract_audit` | `security-tools__contract_audit({"project_path":"...","scope":"full"})` | forge build+test+slither+aderyn+mythril+echidna+semgrep+solhint+gitleaks+npm audit |
| `centralized_audit` | `security-tools__centralized_audit({"project_path":"...","scope":"all","language":"auto"})` | SAST+DAST+SCA+Infra+Compliance |
| `production_audit` | `security-tools__production_audit({"target_url":"..."})` | 24 项上线后安全检测 |

## 3 个安全子代理

| 子代理 | MCP 入口 | 模型 | 产出 |
|--------|---------|------|------|
| security | `security-tools__contract_audit()` | **zhipu/glm-5.2** (128K) | SECURITY_REVIEW_REPORT.md |
| security-check | `security-tools__contract_audit()` | deepseek-v4-pro | SECURITY_SCAN_REPORT.md |
| security-check-centralized | `security-tools__centralized_audit()` | deepseek-v4-pro | SECURITY_SCAN_REPORT_CENTRALIZED.md |

> ⚠️ security 必须用 GLM-5.2！SCSVS 85 项 depth 审计 deepseek 32K 会截断。

## 子代理接入

在 `~/.openclaw/openclaw.json` 里注册：

```json
{
  "agents": { "list": [
    {"id": "security", "workspace": "workspace/security", "model": "zhipu/glm-5.2"},
    {"id": "security-check", "workspace": "workspace/security-check", "model": "deepseek/deepseek-v4-pro"},
    {"id": "security-check-centralized", "workspace": "workspace/security-check-centralized", "model": "deepseek/deepseek-v4-pro"}
  ]}
}
```

复制 AGENTS.md：

```bash
mkdir -p ~/.openclaw/workspace/security ~/.openclaw/workspace/security-check ~/.openclaw/workspace/security-check-centralized
cp /tmp/agent-skills/agents/security/AGENTS.md ~/.openclaw/workspace/security/
cp /tmp/agent-skills/agents/security-check/AGENTS.md ~/.openclaw/workspace/security-check/
cp /tmp/agent-skills/agents/security-check-centralized/AGENTS.md ~/.openclaw/workspace/security-check-centralized/
```

---

## 文档

| 文档 | 内容 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 7 步接入指南（含排错） |
| [SKILL.md](SKILL.md) | Skill 规范（OpenClaw 可读） |
| [ONBOARDING.md](docs/ONBOARDING.md) | 完整接入流程 |
| [SCSVS 85项矩阵](references/scsvs-matrix-v2.md) | 完整检查表 |
| [14源情报详情](references/attack-sources.md) | 威胁情报源 |
| [工具安装](references/tool-install.md) | MCP 服务器端工具安装 |

## 目录结构

```
security-audit-pipeline/
├── SKILL.md              # Skill 规范
├── QUICKSTART.md         # 接入指南
├── README.md             # 本文件
├── assets/               # 审计资产
│   ├── echidna-harnesses/  # 3 套 Fuzzing 模板
│   ├── slither-detectors/  # 5 个自定义检测器
│   └── nuclei-templates/   # 5 个 DAST 模板
├── mcp/                    # MCP Server 源码
│   └── security-tools-server/
├── references/             # 参考文档
├── scripts/                # 工具脚本
└── templates/              # Spawn 模板
```

## 维护者

Wayne (stevenwang) — Team2
# v3.0.1 test

## git-mcp push test
