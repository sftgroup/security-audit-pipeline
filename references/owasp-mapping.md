# OWASP Top 10 Tool Coverage Mapping

> For centralized projects (security-check-centralized)
> Weighted average coverage: ~80%

| # | Category | Coverage | Tools | Notes |
|---|----------|:--:|-------|-------|
| A1 | Broken Access Control | 85% | semgrep + nuclei + ZAP + manual | IDOR detection requires manual review |
| A2 | Cryptographic Failures | 90% | gitleaks + nuclei + SSL/TLS | TLS config automated; weak cipher detection good |
| A3 | Injection | 95% | semgrep + bandit + nuclei + ZAP | SQL/NoSQL/OS command injection well covered |
| A4 | Insecure Design | 70% | Manual review | Architecture-level issues need human analysis |
| A5 | Security Misconfiguration | 85% | nuclei + ZAP + nikto + lynis | Missing headers, default configs covered |
| A6 | Vulnerable Components | 95% | npm/pip/cargo audit + trivy | SCA tools provide near-complete coverage |
| A7 | Auth Failures | 75% | semgrep + nuclei + ZAP | JWT/session issues partially automated |
| A8 | Software Integrity Failures | 70% | trivy + npm audit | Supply chain covered, CI/CD integrity needs manual |
| A9 | Logging & Monitoring Failures | 50% | semgrep | Heavily dependent on manual review |
| A10 | SSRF | 85% | semgrep + nuclei | Modern tools have good SSRF detection |

## OWASP Risk Rating

| Level | Definition | Response |
|-------|-----------|----------|
| 🔴 Critical | RCE, SQL injection, data breach | Immediate |
| 🟠 High | XSS, CSRF, SSRF, permission bypass | 24h |
| 🟡 Medium | Config defect, info leak | This sprint |
| 🟢 Low | Security headers, cookies, logging | Tech debt |

## Scanner to OWASP Cross-Reference

| Scanner | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | A9 | A10 |
|---------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| semgrep | ✓ | ✓ | ✓ | - | ✓ | - | ✓ | - | ✓ | ✓ |
| bandit | - | ✓ | ✓ | - | - | - | - | - | - | - |
| gosec | - | ✓ | ✓ | - | - | - | - | - | - | - |
| eslint-security | ✓ | - | ✓ | - | - | - | - | - | - | - |
| gitleaks | - | ✓ | - | - | - | - | - | - | - | - |
| nuclei | ✓ | ✓ | ✓ | - | ✓ | - | ✓ | - | - | ✓ |
| ZAP | ✓ | - | ✓ | - | ✓ | - | ✓ | - | - | - |
| nikto | - | ✓ | - | - | ✓ | - | - | - | - | - |
| ffuf | ✓ | - | - | - | - | - | - | - | - | - |
| trivy | - | - | - | - | - | ✓ | - | ✓ | - | - |
| npm audit | - | - | - | - | - | ✓ | - | - | - | - |
| nmap | - | - | - | - | ✓ | - | - | - | - | - |
| lynis | - | - | - | - | ✓ | - | - | - | - | - |
| testssl.sh | - | ✓ | - | - | ✓ | - | - | - | - | - |
| curl (security headers) | - | - | - | - | ✓ | - | - | - | - | - |
