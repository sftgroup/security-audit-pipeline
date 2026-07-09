"""
Centralized Scanning Tools (20 atomic tools + 1 composite)
===========================================================
SAST: semgrep, bandit, gosec, eslint-security, gitleaks
DAST: nuclei, ZAP, nikto, ffuf
SCA: npm audit, pip-audit, cargo audit, trivy
Infra: nmap, lynis, docker-bench, kube-bench
Compliance: testssl, check_cors, check_headers, whatweb

Composite: centralized_audit — orchestrates all 20 sub-tools, returns unified report.
"""

import mcp.types as types
from .shared import run_npm_audit, run_nmap, run_nuclei, run_zap, run_semgrep

CENTRALIZED_TOOLS = [
    # === Composite Entry Tool ===
    types.Tool(
        name="centralized_audit",
        description="Run full centralized application security audit (SAST + DAST + SCA + Infra + Compliance)",
        inputSchema={
            "type": "object",
            "required": ["project_path"],
            "properties": {
                "project_path": {"type": "string", "description": "Path to project root"},
                "target_url": {"type": "string", "description": "Target URL for DAST scans (optional)"},
                "scope": {"type": "string", "description": "Audit scope: sast, dast, sca, infra, compliance, all (default: all)"},
                "language": {"type": "string", "description": "Project language: js, python, go, rust, multi (auto-detect if omitted)"},
                "skip": {"type": "string", "description": "Comma-separated tools to skip"}
            }
        }
    ),
    # === SAST ===
    types.Tool(
        name="semgrep_auto",
        description="Run Semgrep multi-language SAST (JS/TS/Python/Go)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "exclude": {"type": "string", "description": "Comma-separated dirs to exclude"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="bandit_scan",
        description="Run Bandit Python security linter",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "severity": {"type": "string", "description": "Min severity: low, medium, high (default: low)"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="gosec_scan",
        description="Run gosec Go security scanner",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "include_rules": {"type": "string", "description": "Comma-separated rule IDs"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="eslint_security",
        description="Run ESLint with security plugin for JS/TS",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "extensions": {"type": "string", "description": "File extensions (default: .js,.ts,.tsx,.jsx)"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="gitleaks_scan",
        description="Run Gitleaks to detect hardcoded secrets and API keys",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "verbose": {"type": "boolean", "description": "Show all findings including masked"}
            },
            "required": ["project_path"]
        }
    ),
    # === DAST ===
    types.Tool(
        name="nuclei_web",
        description="Run Nuclei web vulnerability scanner with OWASP templates",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string"},
                "severity": {"type": "string"},
                "custom_templates": {"type": "string"}
            },
            "required": ["target_url"]
        }
    ),
    types.Tool(
        name="zap_web",
        description="Run OWASP ZAP full/API web vulnerability scan",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string"},
                "scan_type": {"type": "string", "description": "baseline, full, or api"}
            },
            "required": ["target_url"]
        }
    ),
    types.Tool(
        name="nikto_scan",
        description="Run Nikto web server vulnerability scanner",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string"},
                "tuning": {"type": "string", "description": "Tuning options (1-9, default: 123)"}
            },
            "required": ["target_url"]
        }
    ),
    types.Tool(
        name="ffuf_fuzz",
        description="Run ffuf API fuzzing / directory brute-force",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string", "description": "URL with FUZZ placeholder"},
                "wordlist": {"type": "string", "description": "Path to wordlist file"},
                "extensions": {"type": "string", "description": "Comma-separated extensions"}
            },
            "required": ["target_url", "wordlist"]
        }
    ),
    # === SCA ===
    types.Tool(
        name="npm_audit_full",
        description="Run npm/pnpm audit with full JSON output",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "package_manager": {"type": "string"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="pip_audit",
        description="Run pip-audit for Python dependency CVEs",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "requirements_file": {"type": "string", "description": "Path to requirements.txt"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="cargo_audit",
        description="Run cargo-audit for Rust dependency CVEs",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="trivy_scan",
        description="Run Trivy comprehensive vulnerability scanner (fs + container)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "scan_type": {"type": "string", "description": "filesystem, image, or repo"},
                "severity": {"type": "string", "description": "Min severity: CRITICAL,HIGH,MEDIUM,LOW"}
            },
            "required": ["project_path"]
        }
    ),
    # === Infrastructure ===
    types.Tool(
        name="nmap_full",
        description="Full port scan with service detection",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "ports": {"type": "string", "description": "Port range (default: 1-65535)"}
            },
            "required": ["target"]
        }
    ),
    types.Tool(
        name="lynis_audit",
        description="Run Lynis host security audit",
        inputSchema={
            "type": "object",
            "properties": {
                "quick": {"type": "boolean", "description": "Quick scan (skip extended tests)"}
            }
        }
    ),
    types.Tool(
        name="docker_bench",
        description="Run Docker Bench Security for container hardening",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    ),
    types.Tool(
        name="kube_bench",
        description="Run kube-bench for Kubernetes cluster security",
        inputSchema={
            "type": "object",
            "properties": {
                "version": {"type": "string", "description": "Kubernetes version (e.g. 1.28)"}
            }
        }
    ),
    # === Compliance ===
    types.Tool(
        name="testssl_scan",
        description="Run testssl.sh for SSL/TLS configuration audit",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string"},
                "protocols": {"type": "string", "description": "Protocols to test (default: all)"}
            },
            "required": ["target_url"]
        }
    ),
    types.Tool(
        name="check_cors",
        description="Check CORS configuration for security issues",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string"},
                "origin": {"type": "string", "description": "Test origin (default: https://evil.com)"}
            },
            "required": ["target_url"]
        }
    ),
    types.Tool(
        name="check_security_headers",
        description="Check HTTP security headers (CSP, HSTS, X-Frame-Options, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string"}
            },
            "required": ["target_url"]
        }
    ),
    types.Tool(
        name="whatweb_fingerprint",
        description="Run WhatWeb for technology fingerprinting",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string"},
                "aggression": {"type": "integer", "description": "Aggression level 1-4 (default: 1)"}
            },
            "required": ["target_url"]
        }
    ),
]

# ============================================================
# Tool Handlers
# ============================================================

import subprocess
import json
import re
import os
import glob
import subprocess

def register_centralized_tools(server):
    for tool in CENTRALIZED_TOOLS:
        if server is not None:
            server._tool_schemas[tool.name] = tool
    return CENTRALIZED_TOOLS

async def handle_centralized_tool(name: str, args: dict) -> str | None:
    handlers = {
        "centralized_audit": _centralized_audit,
        "semgrep_auto": _semgrep_auto,
        "bandit_scan": _bandit_scan,
        "gosec_scan": _gosec_scan,
        "eslint_security": _eslint_security,
        "gitleaks_scan": _gitleaks_scan,
        "nuclei_web": _nuclei_web,
        "zap_web": _zap_web,
        "nikto_scan": _nikto_scan,
        "ffuf_fuzz": _ffuf_fuzz,
        "npm_audit_full": _npm_audit_full,
        "pip_audit": _pip_audit,
        "cargo_audit": _cargo_audit,
        "trivy_scan": _trivy_scan,
        "nmap_full": _nmap_full,
        "lynis_audit": _lynis_audit,
        "docker_bench": _docker_bench,
        "kube_bench": _kube_bench,
        "testssl_scan": _testssl_scan,
        "check_cors": _check_cors,
        "check_security_headers": _check_security_headers,
        "whatweb_fingerprint": _whatweb_fingerprint,
    }
    if name in handlers:
        result = await handlers[name](args)
        return json.dumps(result, indent=2)
    return None

# === SAST Handlers ===

async def _semgrep_auto(args: dict) -> dict:
    return await run_semgrep(args["project_path"], config="auto",
        exclude=args.get("exclude", "node_modules,dist,build,.git"))

async def _bandit_scan(args: dict) -> dict:
    project = args["project_path"]
    severity = args.get("severity", "low")
    try:
        r = subprocess.run(
            ["bandit", "-r", project, "-ll", "-f", "json"],
            capture_output=True, text=True, timeout=120
        )
        try:
            data = json.loads(r.stdout)
            results = data.get("results", [])
            sevs = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            for r2 in results:
                s = r2.get("issue_severity", "LOW")
                sevs[s.upper()] = sevs.get(s.upper(), 0) + 1
            return {"tool": "bandit", "total": len(results), "severity": sevs}
        except:
            return {"tool": "bandit", "raw": r.stdout[-2000:]}
    except FileNotFoundError:
        return {"tool": "bandit", "error": "bandit not installed"}
    except Exception as e:
        return {"tool": "bandit", "error": str(e)}

async def _gosec_scan(args: dict) -> dict:
    project = args["project_path"]
    try:
        r = subprocess.run(
            ["gosec", "-fmt", "json", "./..."],
            cwd=project, capture_output=True, text=True, timeout=120
        )
        try:
            data = json.loads(r.stdout)
            issues = data.get("Issues", [])
            sevs = {}
            for i in issues:
                s = i.get("severity", "LOW")
                sevs[s] = sevs.get(s, 0) + 1
            return {"tool": "gosec", "total": len(issues), "severity": sevs}
        except:
            return {"tool": "gosec", "raw": r.stdout[-2000:]}
    except FileNotFoundError:
        return {"tool": "gosec", "error": "gosec not installed"}
    except Exception as e:
        return {"tool": "gosec", "error": str(e)}

async def _eslint_security(args: dict) -> dict:
    project = args["project_path"]
    exts = args.get("extensions", ".js,.ts,.tsx,.jsx")
    try:
        r = subprocess.run(
            ["npx", "eslint", ".", "--ext", exts, "--plugin", "security", "--format", "json"],
            cwd=project, capture_output=True, text=True, timeout=120
        )
        try:
            data = json.loads(r.stdout)
            total_issues = sum(len(f.get("messages", [])) for f in data)
            files_with_issues = len([f for f in data if f.get("messages")])
            return {"tool": "eslint-security", "total": total_issues, "files": files_with_issues}
        except:
            return {"tool": "eslint-security", "raw": r.stdout[-2000:]}
    except Exception as e:
        return {"tool": "eslint-security", "error": str(e)}

async def _gitleaks_scan(args: dict) -> dict:
    project = args["project_path"]
    verbose = args.get("verbose", False)
    try:
        r = subprocess.run(
            ["gitleaks", "detect", "--source", project, "--report-format", "json", "-v" if verbose else ""],
            capture_output=True, text=True, timeout=120
        )
        try:
            data = json.loads(r.stdout) if r.stdout.strip() else []
            findings = data if isinstance(data, list) else []
            rules = set(f.get("RuleID", "unknown") for f in findings)
            return {"tool": "gitleaks", "secrets_found": len(findings), "rule_types": list(rules)}
        except:
            return {"tool": "gitleaks", "raw": r.stdout[-2000:]}
    except FileNotFoundError:
        return {"tool": "gitleaks", "error": "gitleaks not installed"}
    except Exception as e:
        return {"tool": "gitleaks", "error": str(e)}

# === DAST Handlers ===

async def _nuclei_web(args: dict) -> dict:
    return await run_nuclei(args["target_url"],
        severity=args.get("severity", "low,medium,high,critical"),
        custom_templates=args.get("custom_templates", ""))

async def _zap_web(args: dict) -> dict:
    return await run_zap(args["target_url"], args.get("scan_type", "baseline"))

async def _nikto_scan(args: dict) -> dict:
    target = args["target_url"]
    tuning = args.get("tuning", "123")
    try:
        r = subprocess.run(
            ["nikto", "-h", target, "-Tuning", tuning],
            capture_output=True, text=True, timeout=180
        )
        findings = re.findall(r'\+ .+?: (.+)', r.stdout)
        return {"tool": "nikto", "total": len(findings), "findings": findings[:20]}
    except FileNotFoundError:
        return {"tool": "nikto", "error": "nikto not installed"}
    except Exception as e:
        return {"tool": "nikto", "error": str(e)}

async def _ffuf_fuzz(args: dict) -> dict:
    target = args["target_url"]
    wordlist = args["wordlist"]
    exts = args.get("extensions", "")
    cmd = ["ffuf", "-u", target, "-w", wordlist, "-json"]
    if exts:
        cmd += ["-e", exts]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        results = [json.loads(line) for line in r.stdout.strip().split("\n") if line.strip()]
        statuses = {}
        for r2 in results:
            s = r2.get("status", 0)
            statuses[str(s)] = statuses.get(str(s), 0) + 1
        return {"tool": "ffuf", "total_hits": len(results), "status_codes": statuses}
    except FileNotFoundError:
        return {"tool": "ffuf", "error": "ffuf not installed"}
    except Exception as e:
        return {"tool": "ffuf", "error": str(e)}

# === SCA Handlers ===

async def _npm_audit_full(args: dict) -> dict:
    return await run_npm_audit(args["project_path"], args.get("package_manager", "pnpm"))

async def _pip_audit(args: dict) -> dict:
    project = args["project_path"]
    req_file = args.get("requirements_file", "requirements.txt")
    try:
        r = subprocess.run(
            ["pip-audit", "-r", req_file, "-f", "json"],
            cwd=project, capture_output=True, text=True, timeout=120
        )
        try:
            data = json.loads(r.stdout)
            vulns = data.get("dependencies", []) if isinstance(data, dict) else []
            total = sum(len(v.get("vulns", [])) for v in vulns)
            return {"tool": "pip-audit", "total_vulns": total, "packages_affected": len(vulns)}
        except:
            return {"tool": "pip-audit", "raw": r.stdout[-1000:]}
    except FileNotFoundError:
        return {"tool": "pip-audit", "error": "pip-audit not installed"}
    except Exception as e:
        return {"tool": "pip-audit", "error": str(e)}

async def _cargo_audit(args: dict) -> dict:
    project = args["project_path"]
    try:
        r = subprocess.run(
            ["cargo", "audit", "--json"],
            cwd=project, capture_output=True, text=True, timeout=120
        )
        try:
            data = json.loads(r.stdout)
            vulns = data.get("vulnerabilities", {}).get("list", [])
            critical = sum(1 for v in vulns if isinstance(v, dict) and v.get("advisory", {}).get("severity") == "critical")
            return {"tool": "cargo-audit", "total": len(vulns), "critical": critical}
        except:
            return {"tool": "cargo-audit", "raw": r.stdout[-1000:]}
    except FileNotFoundError:
        return {"tool": "cargo-audit", "error": "cargo-audit not installed"}
    except Exception as e:
        return {"tool": "cargo-audit", "error": str(e)}

async def _trivy_scan(args: dict) -> dict:
    project = args["project_path"]
    scan_type = args.get("scan_type", "filesystem")
    sev = args.get("severity", "CRITICAL,HIGH,MEDIUM")
    try:
        cmd = ["trivy", scan_type, project, "--severity", sev, "--format", "json"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        try:
            data = json.loads(r.stdout)
            results = data.get("Results", [])
            total = sum(len(r2.get("Vulnerabilities", [])) for r2 in results)
            return {"tool": "trivy", "scan_type": scan_type, "total_vulns": total}
        except:
            return {"tool": "trivy", "raw_kb": len(r.stdout)}
    except FileNotFoundError:
        return {"tool": "trivy", "error": "trivy not installed"}
    except Exception as e:
        return {"tool": "trivy", "error": str(e)}

# === Infrastructure Handlers ===

async def _nmap_full(args: dict) -> dict:
    return await run_nmap(args["target"],
        ports=args.get("ports", "1-65535"), scan_type="full")

async def _lynis_audit(args: dict) -> dict:
    quick = args.get("quick", False)
    cmd = ["sudo", "lynis", "audit", "system"]
    if quick:
        cmd.append("--quick")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        hardened = re.findall(r'Hardening index\s*:\s*(\d+)', r.stdout)
        warnings = re.findall(r'Warning', r.stdout, re.IGNORECASE)
        suggestions = re.findall(r'Suggestion', r.stdout, re.IGNORECASE)
        return {
            "tool": "lynis",
            "hardening_index": hardened[0] if hardened else "unknown",
            "warnings": len(warnings),
            "suggestions": len(suggestions)
        }
    except Exception as e:
        return {"tool": "lynis", "error": str(e)}

async def _docker_bench(args: dict) -> dict:
    try:
        r = subprocess.run(
            ["docker", "run", "--rm", "--net", "host", "--pid", "host",
             "--userns", "host", "--cap-add", "audit_control",
             "-v", "/etc:/etc:ro", "-v", "/usr/bin/docker:/usr/bin/docker:ro",
             "-v", "/var/run/docker.sock:/var/run/docker.sock:ro",
             "-v", "/usr/lib/systemd:/usr/lib/systemd:ro",
             "-v", "/var/lib:/var/lib:ro",
             "docker/docker-bench-security"],
            capture_output=True, text=True, timeout=120
        )
        warn = len(re.findall(r'\[WARN\]', r.stdout))
        info = len(re.findall(r'\[INFO\]', r.stdout))
        passed = len(re.findall(r'\[PASS\]', r.stdout))
        return {"tool": "docker-bench", "warn": warn, "pass": passed, "info": info}
    except Exception as e:
        return {"tool": "docker-bench", "error": str(e)}

async def _kube_bench(args: dict) -> dict:
    version = args.get("version", "")
    cmd = ["kube-bench"]
    if version:
        cmd += ["--version", version]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        fail = len(re.findall(r'\[FAIL\]', r.stdout))
        warn = len(re.findall(r'\[WARN\]', r.stdout))
        passed = len(re.findall(r'\[PASS\]', r.stdout))
        return {"tool": "kube-bench", "fail": fail, "warn": warn, "pass": passed}
    except FileNotFoundError:
        return {"tool": "kube-bench", "error": "kube-bench not installed"}
    except Exception as e:
        return {"tool": "kube-bench", "error": str(e)}

# === Compliance Handlers ===

async def _testssl_scan(args: dict) -> dict:
    target = args["target_url"]
    try:
        r = subprocess.run(
            ["/opt/testssl/testssl.sh", "--jsonfile", "/tmp/testssl.json", target],
            capture_output=True, text=True, timeout=180
        )
        try:
            with open("/tmp/testssl.json") as f:
                data = json.load(f)
            findings = data.get("scanResult", [])
            sevs = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "OK": 0}
            for f2 in findings:
                s = f2.get("severity", "OK")
                sevs[s] = sevs.get(s, 0) + 1
            return {"tool": "testssl", "findings": sevs}
        except:
            return {"tool": "testssl", "raw": r.stdout[-2000:]}
    except Exception as e:
        return {"tool": "testssl", "error": str(e)}

async def _check_cors(args: dict) -> dict:
    target = args["target_url"]
    origin = args.get("origin", "https://evil.com")
    try:
        r = subprocess.run(
            ["curl", "-sI", "-H", f"Origin: {origin}", target],
            capture_output=True, text=True, timeout=30
        )
        acao = re.findall(r'Access-Control-Allow-Origin:\s*(.+)', r.stdout, re.IGNORECASE)
        acac = "Access-Control-Allow-Credentials: true" in r.stdout
        is_vulnerable = any(
            o.strip() == "*" or o.strip() == origin
            for o in acao
        ) and acac
        return {
            "tool": "cors-check",
            "allow_origin": acao,
            "allow_credentials": acac,
            "vulnerable": is_vulnerable,
            "recommendation": "Use explicit origin whitelist, not wildcard with credentials"
        }
    except Exception as e:
        return {"tool": "cors-check", "error": str(e)}

async def _check_security_headers(args: dict) -> dict:
    target = args["target_url"]
    required_headers = [
        "X-Frame-Options", "X-Content-Type-Options",
        "Content-Security-Policy", "Strict-Transport-Security",
        "Referrer-Policy", "Permissions-Policy"
    ]
    try:
        r = subprocess.run(["curl", "-sI", target], capture_output=True, text=True, timeout=30)
        headers = {}
        for h in required_headers:
            m = re.search(rf'{h}:\s*(.+)', r.stdout, re.IGNORECASE)
            headers[h] = m.group(1).strip() if m else "MISSING"
        missing = [h for h, v in headers.items() if v == "MISSING"]
        return {
            "tool": "security-headers",
            "headers": headers,
            "missing": missing,
            "grade": "A" if len(missing) == 0 else "B" if len(missing) <= 2 else "C" if len(missing) <= 4 else "F"
        }
    except Exception as e:
        return {"tool": "security-headers", "error": str(e)}

async def _whatweb_fingerprint(args: dict) -> dict:
    target = args["target_url"]
    aggression = str(args.get("aggression", 1))
    try:
        r = subprocess.run(
            ["whatweb", "-a", aggression, "--log-json=/tmp/whatweb.json", target],
            capture_output=True, text=True, timeout=60
        )
        try:
            with open("/tmp/whatweb.json") as f:
                data = json.load(f)
            plugins = data[0].get("plugins", {}) if data else {}
            techs = {k: v.get("string", [""])[0][:50] for k, v in plugins.items()}
            return {"tool": "whatweb", "technologies": techs, "total": len(techs)}
        except:
            return {"tool": "whatweb", "raw": r.stdout[-1000:]}
    except FileNotFoundError:
        return {"tool": "whatweb", "error": "whatweb not installed"}
    except Exception as e:
        return {"tool": "whatweb", "error": str(e)}

# ============================================================
# Composite Tool: centralized_audit
# ============================================================

async def _centralized_audit(args: dict) -> dict:
    """Orchestrate full centralized application security audit."""
    project = args["project_path"]
    target_url = args.get("target_url", "")
    scope = args.get("scope", "all")
    lang = args.get("language", "multi")
    skip_list = (args.get("skip", "") or "").split(",")
    skip = set(s.strip() for s in skip_list if s.strip())

    results = {
        "tool": "centralized_audit",
        "project": project,
        "target_url": target_url,
        "scope": scope,
        "language": lang,
        "sections": {}
    }

    # === SAST ===
    if scope in ("sast", "all"):
        if "semgrep" not in skip:
            results["sections"]["semgrep"] = await _semgrep_auto(args)
        if "bandit" not in skip and lang in ("python", "multi"):
            results["sections"]["bandit"] = await _bandit_scan(args)
        if "gosec" not in skip and lang in ("go", "multi"):
            results["sections"]["gosec"] = await _gosec_scan(args)
        if "eslint" not in skip and lang in ("js", "multi"):
            results["sections"]["eslint"] = await _eslint_security(args)
        if "gitleaks" not in skip:
            results["sections"]["gitleaks"] = await _gitleaks_scan(args)

    # === DAST ===
    if scope in ("dast", "all") and target_url:
        if "nuclei" not in skip:
            results["sections"]["nuclei"] = await _nuclei_web({"target_url": target_url})
        if "nikto" not in skip:
            results["sections"]["nikto"] = await _nikto_scan({"target_url": target_url})

    # === SCA ===
    if scope in ("sca", "all"):
        if "npm" not in skip:
            results["sections"]["npm_audit"] = await _npm_audit_full(args)
        if "pip" not in skip and lang in ("python", "multi"):
            results["sections"]["pip_audit"] = await _pip_audit(args)
        if "cargo" not in skip and lang in ("rust", "multi"):
            results["sections"]["cargo_audit"] = await _cargo_audit(args)
        if "trivy" not in skip:
            try:
                results["sections"]["trivy"] = await _trivy_scan(args)
            except: pass

    # === Infrastructure ===
    if scope in ("infra", "all") and target_url:
        host = re.sub(r'https?://', '', target_url).split('/')[0].split(':')[0]
        if "nmap" not in skip:
            results["sections"]["nmap"] = await _nmap_full({"target": host})
        if "lynis" not in skip:
            try:
                results["sections"]["lynis"] = await _lynis_audit({"quick": True})
            except: pass

    # === Compliance ===
    if scope in ("compliance", "all") and target_url:
        if "testssl" not in skip:
            results["sections"]["testssl"] = await _testssl_scan({"target": target_url})
        if "cors" not in skip:
            results["sections"]["cors"] = await _check_cors({"target_url": target_url})
        if "headers" not in skip:
            results["sections"]["headers"] = await _check_security_headers({"target_url": target_url})
        if "whatweb" not in skip:
            results["sections"]["whatweb"] = await _whatweb_fingerprint({"target_url": target_url})

    # === Summary ===
    results["summary"] = _centralized_summary(results["sections"])
    return results


def _centralized_summary(sections: dict) -> dict:
    critical, high, medium, low = 0, 0, 0, 0

    for name, section in sections.items():
        if not isinstance(section, dict):
            continue
        sevs = section if "severity" not in section else section.get("severity", {})

        if name == "gitleaks":
            found = section.get("total_leaks", 0)
            if found > 0:
                critical += found
        elif name == "npm_audit":
            critical += section.get("critical", 0)
            high += section.get("high", 0)
        elif name == "pip_audit":
            high += section.get("total_vulns", 0)
        elif name == "trivy":
            high += section.get("total_vulns", 0)
        elif name == "nuclei":
            sevs = section.get("severity", {})
            critical += sevs.get("critical", 0)
            high += sevs.get("high", 0)
            medium += sevs.get("medium", 0)
        elif name == "nikto":
            total = section.get("total", 0)
            if total > 0:
                medium += total
        elif name == "testssl":
            sevs = section.get("findings", {})
            critical += sevs.get("CRITICAL", 0)
            high += sevs.get("HIGH", 0)
        elif name == "cors" and section.get("vulnerable"):
            high += 1
        elif name == "headers":
            missing = len(section.get("missing", []))
            if missing > 2:
                medium += missing
        elif name == "semgrep":
            high += section.get("severity", {}).get("ERROR", 0)
            medium += section.get("severity", {}).get("WARNING", 0)

    risk = "CRITICAL" if critical > 0 else "HIGH" if high > 5 else "MEDIUM" if high > 0 or medium > 5 else "LOW"
    return {
        "risk_level": risk,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low
    }

