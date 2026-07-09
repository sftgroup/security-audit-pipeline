# Security Audit Pipeline — 安全审计流水线

> 一个 Skill + 一个 MCP Server，Agent 只需调 3 个入口工具即可完成全量安全审计。

---

## 这是什么

一套标准化的 **Skill + Tool + MCP** 安全审计产品，覆盖三类场景：

- 🔷 **智能合约** — Solidity/Foundry 项目安全审计
- 🏢 **中心化应用** — Node.js/React/Python/Go 项目安全审计
- 🌐 **生产环境** — 已上线 Web 应用 + 移动 App + API + 基础设施

Agent 加载 Skill 后通过 MCP 协议调用入口工具，无需安装任何扫描软件。所有扫描工具（Slither/Nuclei/sqlmap/MobSF 等 36+ 种）预装在测试服务器上。

---

## 怎么用（Agent 视角）

### Step 1: 判断项目类型 → 选入口工具

| 项目特征 | 调用 |
|----------|------|
| 有 `contracts/src/*.sol` + `foundry.toml` | `contract_audit` |
| Node.js/React/Python/Go 没有合约文件 | `centralized_audit` |
| 已经上线，有 URL / APK | 上面 + `production_audit` |

### Step 2: 调 MCP 工具

```json
// 合约审计
contract_audit({
  "project_path": "/path/to/project",
  "scope": "all"
})

// 中心化应用审计
centralized_audit({
  "project_path": "/path/to/project",
  "target_url": "https://app.example.com",
  "scope": "all"
})

// 上线后安全检测
production_audit({
  "target_url": "https://app.example.com",
  "domain": "all",
  "apk_path": "/tmp/app.apk"
})
```

### Step 3: 读返回 → 修 → 回归

每个工具返回归一化报告：

```json
{
  "sections": {
    "slither": { "total": 15, "severity": { "High": 3, "Medium": 8 } },
    "npm_audit": { "critical": 2, "high": 5 },
    ...
  },
  "summary": {
    "risk_level": "HIGH",
    "critical": 2,
    "high": 8,
    "medium": 10
  }
}
```

---

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                 security-audit-pipeline                  │
│                                                         │
│  SKILL.md          ← Agent 加载，知道怎么用              │
│  assets/           ← 代码模板 (Echidna ×3, Slither ×5)  │
│  references/       ← 参考文档 (SCSVS, OWASP, 情报源)     │
│  templates/        ← spawn 模板                         │
│                                                         │
│  ┌─── MCP Server ───────────────────────────────────┐   │
│  │  3 个入口工具 (Agent 调这 3 个)                    │   │
│  │                                                   │   │
│  │  contract_audit      → 16 个子工具自动编排         │   │
│  │  centralized_audit   → 20 个子工具自动编排         │   │
│  │  production_audit    → 5 个域自动编排              │   │
│  └───────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─── 知识库 ───────────────────────────────────────┐   │
│  │  cron 每天 06:00 → 14 源自动更新                  │   │
│  │  ~/.openclaw/security-kb/                         │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
security-audit-pipeline/
│
├── SKILL.md                        # Skill 入口文档
│
├── assets/                         # 安全扫描资产（子 Agent 按需读取）
│   ├── echidna-harnesses/          # 3 套 Fuzzing 模板 (.sol)
│   ├── slither-detectors/          # 5 个自定义检测器 (.py)
│   └── nuclei-templates/           # 5 个 OWASP DAST 模板 (.yaml)
│
├── mcp/security-tools-server/      # MCP Server（部署在测试服务器）
│   ├── server.py                   # Stdio 入口
│   ├── install.sh                  # 36 工具一键安装
│   ├── tools/
│   │   ├── contract.py             # 合约审计（1 入口 + 16 原子）
│   │   ├── centralized.py          # 中心化审计（1 入口 + 20 原子）
│   │   ├── production.py           # 生产安全审计（1 入口 + 全自动编排）
│   │   ├── intel.py                # 威胁情报查询（6 工具）
│   │   └── shared.py               # 共享工具函数
│   └── requirements.txt
│
├── scripts/
│   └── update-security-kb.sh       # 14 源 → 本地知识库
│
├── references/                     # 参考文档
│   ├── scsvs-matrix-v2.md          # 85 项 SCSVS 检查表
│   ├── attack-sources.md           # 14 个威胁情报源详情
│   ├── owasp-mapping.md            # OWASP Top 10 工具覆盖
│   └── tool-install.md             # 20+ 工具安装命令
│
└── templates/                      # Spawn 模板
    ├── contract-spawn.md
    └── centralized-spawn.md
```

---

## 三个入口工具覆盖

### contract_audit

```
编译 → 测试 → 静态分析 → Fuzzing → 密钥泄露 → 依赖漏洞
forge   forge   slither     echidna    grep        npm
                aderyn
                mythril
                semgrep
                solhint
```

### centralized_audit

```
SAST              DAST         SCA          基础设施     合规
semgrep           nuclei       npm audit     nmap        testssl
bandit (Python)   ZAP          pip-audit     lynis       CORS 检查
gosec (Go)        nikto        cargo audit   docker-bench   Headers
eslint (JS)       ffuf         trivy         kube-bench     WhatWeb
gitleaks
```

### production_audit

```
Web                          API               移动
sqlmap (SQL注入)             CORS 检查         APK 分析
XSSer (XSS)                  Headers 检查      硬编码密钥
Wapiti (全量Web扫描)          SSL 评级         MobSF
wfuzz (目录爆破)              Cookie 审计
子域名枚举                   JWT 检查
                             Rate Limit 测试
基础设施                    合规
nmap (端口扫描)              OWASP ZAP Baseline
SSH 加固
WhatWeb (指纹)
```

---

## 严重度标准

| 级别 | 合约 (Immunefi) | 中心化/生产 (OWASP) |
|------|-------------------|-----------------------|
| 🔴 Critical | ≥$100K 损失 | RCE, 数据泄露 |
| 🟠 High | 单点突破 | XSS/SSRF/认证绕过 |
| 🟡 Medium | 条件组合利用 | 配置不当, 信息泄露 |
| 🟢 Low | 最佳实践 | Headers, Cookie 配置 |

---

## 部署

```bash
# 1. 安装 MCP Server 上的 36 个工具
sudo bash mcp/security-tools-server/install.sh

# 2. 启动 MCP Server (Stdio)
python3 mcp/security-tools-server/server.py

# 3. 设置知识库自动更新
crontab -e
# 添加: 0 6 * * * /path/to/scripts/update-security-kb.sh
```

---

## 文件统计

| 组件 | 数量 |
|------|:--:|
| 总文件 | 30 |
| MCP 工具 | 3 入口 + 43 原子 + 6 情报 = 52 |
| Python 代码 | ~2,800 行 |
| Echidna Harness | 3 套 |
| Slither Detector | 5 个 |
| Nuclei 模板 | 5 个 |
| 威胁情报源 | 14 个 |
