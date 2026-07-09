# Centralized Security Audit Spawn Templates

> 架构师判断为非合约项目后，按此模板下发 spawn 任务

## qa Agent

```
任务: L1+L2 功能逻辑审查
代码范围: {PROJECT_ROOT}
PRD文档: {PROJECT_ROOT}/PRD.md (if exists)
产出: {PROJECT_ROOT}/test-reports/QA_REVIEW_REPORT.md

审查:
- L1: 代码格式、命名规范、注释完整度
- L2: 边界条件、错误处理、空值/null、输入校验
- API逻辑审查、业务逻辑审查、错误处理审查
- 每个发现标注严重度 (Critical/High/Medium/Low)
```

## security Agent (model=zhipu/glm-5.2)

```
任务: L3 深度安全审查 (3批串行)
目标: {TARGET_IP}:{PORT}
代码范围: {PROJECT_ROOT}
威胁情报: {SKILL_DIR}/references/owasp-mapping.md (加载)
最新CVE: ~/.openclaw/security-kb/nvd-cve-latest.json + cisa-kev-latest.json (如有)

SEC-1: 认证授权
  - JWT/session机制、RBAC/ABAC权限模型
  - 密钥管理 (环境变量、vault、HSM)
  - 密码策略: bcrypt/argon2、最少8字符、锁定策略
  - write: SECURITY_REVIEW_P1.md

SEC-2: 输入验证 + 业务安全
  - SQL注入/XSS/SSRF/SSTI/LFI/RFI
  - 并发安全、竞态条件、幂等性
  - 权限绕过、IDOR
  - write: SECURITY_REVIEW_P2.md (追加)

SEC-3: 数据安全 + 合规
  - 敏感数据加密(at-rest+in-transit)、日志脱敏
  - 会话管理: Secure/HttpOnly/SameSite Cookie
  - CSRF token、CORS白名单
  - write: SECURITY_REVIEW_P3.md (追加)

严重度: OWASP Risk Rating
最终: 架构师合并P1+P2+P3 → SECURITY_REVIEW_REPORT.md
```

## security-check-centralized Agent

```
任务: 中心化自动工具扫描 (3批串行)
目标: {TARGET_IP}:{PORT}
代码路径: {PROJECT_ROOT}
自定义模板: {SKILL_DIR}/assets/nuclei-templates/

CSC-1 SAST (静态代码分析):
  - semgrep --config auto --exclude node_modules
  - bandit -r src/ (Python项目)
  - gosec ./... (Go项目)
  - npx eslint . --plugin security (JS/TS项目)
  - gitleaks detect --source .
  - write: SECURITY_SCAN_P1.md

CSC-2 DAST+SCA (动态+依赖):
  - nuclei -u {TARGET_URL} -t {SKILL_DIR}/assets/nuclei-templates/ -severity low,medium,high,critical
  - nuclei -u {TARGET_URL} -t owasp-top-10/ -severity high,critical
  - nikto -h {TARGET_URL} -Tuning 123
  - ffuf 模糊测试 (如有wordlist)
  - npm/pip/cargo audit
  - trivy fs .
  - write: SECURITY_SCAN_P2.md (追加)

CSC-3 基础设施+合规:
  - nmap -sV -p 1-65535 {TARGET_IP}
  - lynis audit system --quick
  - testssl.sh {TARGET_URL}
  - CORS: curl -H "Origin: evil.com" -I {TARGET_URL}/api/
  - Cookie: 检查 Secure/HttpOnly/SameSite
  - 安全头: CSP/HSTS/X-Frame-Options/X-Content-Type-Options
  - curl {TARGET_URL}/api/ | grep -iE 'stack trace|internal error|secret|token|password'
  - OWASP映射表
  - write: SECURITY_SCAN_P3.md (追加)

最终: 架构师合并P1+P2+P3 → SECURITY_SCAN_REPORT_CENTRALIZED.md
```
