# 子 Agent AGENTS.md 优化指南

> 目标：让三个子 Agent 从"手动装工具+跑命令"切换到"调 MCP 入口工具自动完成"

---

## 现状问题

三个 AGENTS.md（v9.0 / v9.0 / v1.0）都有同样的问题：

| 问题 | 严重度 | 说明 |
|------|:--:|------|
| **不知道 MCP Server 存在** | 🔴 | 完全没有提及 MCP，Agent 不知道可以调工具 |
| **手动安装工具** | 🔴 | 每个 Agent 启动时先跑 20+ 行安装命令，浪费 token 和时间 |
| **手动跑命令行** | 🔴 | `slither . --detect all` / `nuclei -u URL` 等需 Agent 手写命令，容易出错 |
| **工具可用性检查冗余** | 🟠 | 每个 Agent 自己做 `which slither` 等，MCP 已经集中管理 |
| **结果格式不统一** | 🟠 | slither 原始输出 vs MCP 归一化 JSON，不一致 |
| **重复劳动** | 🟡 | security-check 的 14 工具和 centralized 的 15 工具大半重叠 |

---

## 优化方案：三句话

**Agent 不再手动装工具、不手写命令行。—— 只需调 MCP 入口工具。**

| 删掉 | 替换为 |
|------|--------|
| 环境准备脚本 (20-30行) | 无（MCP Server 上的工具已预装） |
| 手动 `slither . --detect all` | `contract_audit(project_path, scope="static")` |
| 手动 `nuclei -u URL` | `production_audit(target_url, domain="web")` |
| 手动 `npm audit / bandit / gosec / trivy` 等 | `centralized_audit(project_path, target_url)` |
| 工具可用性检查表格 | 无（调 MCP 失败=工具不可用，自动标注在返回中） |
| SCSVS 映射表/OWASP 对照表 | 无（MCP 返回的 summary 已含 risk_level） |

---

## 三个 AGENTS.md 分别怎么写

### security AGENTS.md — 最小化

保留：身份、职责、核心约束、审查方法论（威胁建模/钱流分析/逐类 SCSVS）、报告结构。

```markdown
# AGENTS.md — security

## MCP 集成

所有扫描工具通过 MCP Server 调用（43.156.46.187:3000），无需手动安装或运行命令。

**入口工具：** `contract_audit(project_path, scope)` 完成 forge/slither/aderyn/mythril/echidna/semgrep/solhint/npm audit/密钥扫描。
不需要你写 `slither . --detect all` 或 `forge build`，MCP 帮你做完。

**每次审查开始前：** 调 `query_intelligence(category="defi")` 加载最新攻击情报。

## 职责（不变）
架构安全分析 + 威胁建模 + 攻击场景模拟 + 钱流分析 + SCSVS 标准对齐

## 核心约束（不变）
1. 只做安全+架构审查不做功能测试
2. 必须先调 MCP contract_audit 获取自动化扫描结果，在此基础上做深层分析
3. 威胁建模先行 → 读 MCP 返回的扫描结果 → 逐类 SCSVS 补充人工分析
4. 每个发现标注 SCSVS 类别 + Immunefi 严重度

## 工作流程
1. 调 MCP `contract_audit(project_path, scope="static")` → 获得 slither/aderyn/semgrep/solhint 结果
2. 调 MCP `contract_audit(project_path, scope="fuzz")` → 获得 echidna/forge coverage 结果
3. 基于 MCP 返回结果 + 自己读代码 → 威胁建模 + 钱流分析 + SCSVS 逐类审查
4. 生成 SECURITY_REVIEW_REPORT.md
```

删除：
- ❌ 完整的 SCSVS 85 项表格（读 `references/scsvs-matrix-v2.md` 即可）
- ❌ 环境准备脚本
- ❌ P0 必查项的工具命令
- ❌ SSH 隧道配置
- ❌ Infura RPC 环境变量（MCP 服务器上有）

### security-check AGENTS.md — 最小化

```markdown
# AGENTS.md — security-check

## MCP 集成

**入口工具：** `contract_audit(project_path, scope)` 完成全部合约扫描，无需手动安装任何工具或手写命令行。

**流程：**
1. 调 `contract_audit(project_path, scope="all", deployed_address="0x...")`
2. 读返回的 sections：build/test/slither/aderyn/semgrep/solhint/mythril/echidna/secrets/npm_audit
3. 汇总为 SECURITY_SCAN_REPORT.md

## 职责
自动化安全扫描结果汇总 + SCSVS 映射 + Immunefi 对标

## 核心约束
1. 只扫描汇总不修复
2. MCP 返回的工具失败必须标注在报告中
3. 不确定的标注「待人工确认」

## 报告结构
```markdown
# SECURITY_SCAN_REPORT
## 1. 代码版本指纹
## 2. 编译 & 测试 (来自 contract_audit.sections.build/test)
## 3. 静态分析 (来自 contract_audit.sections.slither/aderyn/semgrep/solhint)
## 4. 自定义 Detector (来自 contract_audit.sections.slither_custom)
## 5. 符号执行 + Fuzzing (来自 contract_audit.sections.mythril/echidna)
## 6. 依赖漏洞 (来自 contract_audit.sections.npm_audit)
## 7. 密钥扫描 (来自 contract_audit.sections.secrets)
## 8. SCSVS 映射表
## 9. 汇总 (来自 contract_audit.summary / Immunefi 对标)
```
```

删除：
- ❌ 14 项检测维度的手动命令
- ❌ 7 步标准流水线的手动命令
- ❌ 自定义 Slither Detector 的使用方式（MCP 自动加载）
- ❌ Echidna Harness 的 cp/echidna 命令
- ❌ 环境准备脚本
- ❌ SSH 隧道
- ❌ Infura RPC 变量

### security-check-centralized AGENTS.md — 最小化

```markdown
# AGENTS.md — security-check-centralized

## MCP 集成

**入口工具：** `centralized_audit(project_path, target_url, scope, language)` 完成 SAST+DAST+SCA+Infra+Compliance 全部扫描。
如果项目已上线，追加 `production_audit(target_url, domain)` 做上线后安全检测。

## 流程
1. 调 `centralized_audit(project_path, target_url, scope="all")`
2. 如果有 URL/APK：调 `production_audit(target_url, domain="all")`
3. 读返回 → 汇总为 SECURITY_SCAN_REPORT.md

## 职责
中心化项目安全扫描结果汇总 + OWASP 对标

## 核心约束
1. 只扫描汇总不修复
2. MCP 返回的工具失败必须标注
3. 不确定的标注「待人工确认」

## 报告结构
```markdown
# CENTRALIZED_SECURITY_SCAN_REPORT
## 1. 版本指纹
## 2. SAST (来自 centralized_audit.sections.semgrep/bandit/gosec/eslint/gitleaks)
## 3. DAST (来自 centralized_audit.sections.nuclei/nikto)
## 4. SCA (来自 centralized_audit.sections.npm_audit/pip_audit/trivy)
## 5. 基础设施 (来自 centralized_audit.sections.nmap/lynis)
## 6. 合规 (来自 centralized_audit.sections.testssl/cors/headers/whatweb)
## 7. OWASP Top 10 映射
## 8. 汇总 (来自 centralized_audit.summary / OWASP 严重度)
```
```

删除：
- ❌ 5 层扫描模型的全部手动命令
- ❌ 15 个工具的安装脚本
- ❌ OWASP Top 10 覆盖表（MCP 返回已有）
- ❌ 环境准备脚本
- ❌ SSH 隧道

---

## 删除清单（三个 AGENTS.md 总计）

| 删除内容 | security | security-check | centralized | 原因 |
|----------|:--:|:--:|:--:|------|
| 工具安装命令 | 🟠 无 | ❌ 30行 | ❌ 30行 | MCP 服务器已安装 |
| 手动跑工具命令 | 🟠 P0部分 | ❌ 50行 | ❌ 40行 | 入口工具自动编排 |
| 工具可用性检查 | — | ❌ 15行 | ❌ 10行 | MCP 返回自带状态 |
| SSH 隧道配置 | — | ❌ 5行 | ❌ 5行 | 不经过 sandbox |
| Infura RPC 变量 | ❌ 3行 | ❌ 3行 | — | MCP 服务器上有 |
| 完整 SCSVS 85项 | 保留但删表格 | — | — | 太长，改引用 |
| OWASP 对照表 | — | — | 🟠 5行 | MCP summary 已有 |

---

## 优化后效果

| 指标 | 优化前 | 优化后 |
|------|:--:|:--:|
| security AGENTS.md | ~295 行 | ~161 行 |
| security-check AGENTS.md | ~262 行 | ~140 行 |
| security-check-centralized AGENTS.md | ~197 行 | ~120 行 |
| **总计** | **754 行** | **421 行 (-44%)** |
| 工具安装次数 | 每次 spawn 装一次 | 0（MCP 预装） |
| Agent 手写命令行 | 40+ 条 | 0 |
| 结果格式 | 各工具原始输出 | 统一 JSON |

---

## 不删的内容（子 Agent 的核心价值）

- ✅ 身份 + 职责 + 核心约束
- ✅ 审查方法论（security 的威胁建模/钱流分析/SCSVS 逐个审查方法）
- ✅ 报告结构模板
- ✅ 严重度标准
- ✅ 强制分批读取 + 分步写报告的流程
- ✅ 禁止行为和铁律
