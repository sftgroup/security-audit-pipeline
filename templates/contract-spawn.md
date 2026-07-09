# Contract Security Audit Spawn Templates

> 架构师判断项目类型后，按此模板下发 spawn 任务

## qa Agent

```
任务: L1+L2 功能逻辑审查
代码范围: {PROJECT_ROOT}/contracts/src/*.sol
PRD文档: {PROJECT_ROOT}/PRD.md (if exists)
产出: {PROJECT_ROOT}/test-reports/QA_REVIEW_REPORT.md

审查:
- L1: 代码格式、命名规范、注释完整度、import顺序
- L2: 边界条件、错误处理、空值/null检查、输入校验
- 功能完整性: 对照PRD逐项检查
- 每个发现标注严重度 (Critical/High/Medium/Low)
- 包含复现步骤
```

## security Agent (model=zhipu/glm-5.2)

```
任务: L3 深度安全审查 (3批串行)
代码范围: {PROJECT_ROOT}/contracts/src/
威胁情报: {SKILL_DIR}/references/scsvs-matrix-v2.md (加载为上下文)
最新攻击: ~/.openclaw/security-kb/attack-matrix-{DATE}.json (如有)

SEC-1: 威胁建模 + V1架构(15项)
  - 信任边界、升级安全、时间锁、治理模型
  - 攻击者分析: 谁能调用? 能改变什么? 能获利什么?
  - write: SECURITY_REVIEW_P1.md

SEC-2: 钱流分析 + V2/V5/V8/V9/V10/V13/V14/D1-D8
  - 钱流完整性、重入保护、闪电贷、MEV
  - 逐类SCSVS矩阵检查
  - write: SECURITY_REVIEW_P2.md (追加)

SEC-3: EIP-712 + 跨链 + Relayer + 升级安全 + P0必查
  - 签名验证、跨链桥、Permit2、ERC-4626
  - P0: 认证/授权/输入验证/密钥管理/密码学/并发安全
  - write: SECURITY_REVIEW_P3.md (追加)

严重度: Immunefi对齐 (Critical/High/Medium/Low)
最终: 架构师合并P1+P2+P3 → SECURITY_REVIEW_REPORT.md
```

## security-check Agent

```
任务: 合约自动工具扫描 (3批串行)
代码路径: {PROJECT_ROOT}/contracts/

SC-1: 静态分析
  - slither . --detect all --filter-paths "lib|test"
  - 加载自定义Detector: {SKILL_DIR}/assets/slither-detectors/
  - aderyn . (88 detectors)
  - semgrep --config solidity src/
  - npx solhint 'src/**/*.sol'
  - write: SECURITY_SCAN_P1.md

SC-2: 动态+符号执行
  - cp {SKILL_DIR}/assets/echidna-harnesses/*.sol test/fuzz/
  - myth analyze src/<target>.sol
  - echidna test/fuzz/DeFiInvariants.sol --contract DeFiInvariants --test-limit 100000
  - echidna test/fuzz/AMMInvariants.sol --contract AMMInvariants --test-limit 100000
  - echidna test/fuzz/LendingInvariants.sol --contract LendingInvariants --test-limit 100000
  - forge coverage && forge test -vvv
  - write: SECURITY_SCAN_P2.md (追加)

SC-3: 周边安全
  - npm/pnpm audit
  - nmap -sV {TARGET_IP}
  - nuclei -u {TARGET_URL} -severity low,medium,high,critical
  - 硬编码密钥检查: grep -rE '0x[a-fA-F0-9]{64}|private_key|password|secret|api_key'
  - SCSVS映射表
  - write: SECURITY_SCAN_P3.md (追加)

最终: 架构师合并P1+P2+P3 → SECURITY_SCAN_REPORT.md
```
