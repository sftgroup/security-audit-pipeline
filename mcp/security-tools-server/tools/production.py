"""
Production Security Audit Tools
================================
Post-deployment security: Web App, Mobile App, API, Infrastructure, Compliance.
Contains 1 composite entry tool (production_audit) plus atomic sub-tools.

Agent usage: just call production_audit(target_url, domain) — it orchestrates everything.
"""

import mcp.types as types

PRODUCTION_TOOLS = [
    # ============================================================
    # Composite Entry Tool (Agent calls this ONE tool)
    # ============================================================
    types.Tool(
        name="production_audit",
        description="Run full post-deployment security audit on a live web/app deployment",
        inputSchema={
            "type": "object",
            "required": ["target_url"],
            "properties": {
                "target_url": {"type": "string", "description": "Target URL or IP (e.g. https://app.example.com or 192.168.1.1)"},
                "domain": {"type": "string", "description": "Audit scope: web, mobile, api, infra, all (default: all)"},
                "apk_path": {"type": "string", "description": "Path to APK/IPA for mobile audit"},
                "wordlist_path": {"type": "string", "description": "Path to fuzzing wordlist directory"},
                "deep": {"type": "boolean", "description": "Deep scan mode (slower, comprehensive)"},
                "timeout_minutes": {"type": "integer", "description": "Max runtime in minutes (default: 30)"}
            }
        }
    ),
]

# ============================================================
# Export
# ============================================================

def register_production_tools(server):
    for tool in PRODUCTION_TOOLS:
        if server is not None:
            server._tool_schemas[tool.name] = tool
    return PRODUCTION_TOOLS

# ============================================================
# Handler
# ============================================================

import subprocess
import json
import re
import os
import glob
import tempfile
import shutil
from typing import Any

async def handle_production_tool(name: str, args: dict) -> str | None:
    if name == "production_audit":
        result = await _production_audit(args)
        return json.dumps(result, indent=2, ensure_ascii=False)
    return None

async def _production_audit(args: dict) -> dict:
    """Orchestrate full post-deployment security audit."""
    target = args["target_url"]
    scope = args.get("domain", "all")
    deep = args.get("deep", False)
    apk_path = args.get("apk_path", "")

    results = {
        "tool": "production_audit",
        "target": target,
        "scope": scope,
        "timestamp": subprocess.run(["date", "-Iseconds"], capture_output=True, text=True).stdout.strip(),
        "sections": {}
    }

    # === Web App Security ===
    if scope in ("web", "all"):
        results["sections"]["web"] = await _scan_web_app(target, deep)

    # === API Security ===
    if scope in ("api", "all"):
        results["sections"]["api"] = await _scan_api(target, deep)

    # === Mobile App Security ===
    if scope in ("mobile", "all") and apk_path:
        results["sections"]["mobile"] = await _scan_mobile(apk_path, deep)

    # === Infrastructure Security ===
    if scope in ("infra", "all"):
        results["sections"]["infra"] = await _scan_infra(target, deep)

    # === Compliance & Hardening ===
    if scope in ("compliance", "infra", "all"):
        results["sections"]["compliance"] = await _scan_compliance(target, deep)

    # === Summary ===
    results["summary"] = _build_summary(results["sections"])
    return results


# ============================================================
# Web App Scanning
# ============================================================

async def _scan_web_app(target: str, deep: bool) -> dict:
    """Run all web app security scanners."""
    web = {}

    # SQL Injection
    web["sql_injection"] = await _sqlmap(target, deep)
    # XSS
    web["xss"] = await _xsser(target, deep)
    # Wapiti (full web scan)
    if deep:
        web["wapiti"] = await _wapiti(target)
    # Directory brute-force
    if deep:
        web["directory_brute"] = await _wfuzz_dir(target)
    # Subdomain enumeration
    web["subdomains"] = await _subdomain_enum(target)

    return web


async def _sqlmap(target: str, deep: bool) -> dict:
    level = "3" if deep else "2"
    risk = "2" if deep else "1"
    try:
        r = subprocess.run(
            ["sqlmap", "-u", target, "--level", level, "--risk", risk, "--batch", "--random-agent"],
            capture_output=True, text=True, timeout=600
        )
        vuln_params = len(re.findall(r'Parameter .+ is vulnerable', r.stdout))
        db_info = re.findall(r'back-end DBMS:\s*(.+)', r.stdout)
        return {"injectable": vuln_params > 0, "vuln_params": vuln_params,
                "dbms": db_info[0].strip() if db_info else "unknown"}
    except FileNotFoundError:
        return {"error": "sqlmap not installed"}
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "result": "partial"}
    except Exception as e:
        return {"error": str(e)}


async def _xsser(target: str, deep: bool) -> dict:
    cmd = ["xsser", "--url", target, "--auto"]
    if deep:
        cmd.append("--Fuzz")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        count = len(re.findall(r'XSS FOUND', r.stdout))
        return {"xss_found": count}
    except FileNotFoundError:
        return {"error": "xsser not installed"}
    except Exception as e:
        return {"error": str(e)}


async def _wapiti(target: str) -> dict:
    try:
        os.makedirs("/tmp/wapiti_report/", exist_ok=True)
        r = subprocess.run(
            ["wapiti", "-u", target, "--format", "json", "-o", "/tmp/wapiti_report/", "--scope", "folder"],
            capture_output=True, text=True, timeout=600
        )
        json_files = glob.glob("/tmp/wapiti_report/*.json")
        if json_files:
            with open(json_files[0]) as f:
                report = json.load(f)
            vulns = report.get("vulnerabilities", {})
            total = sum(len(v.get("vulnerabilities", [])) for v in vulns.values())
            return {"vulnerabilities": total}
        return {"vulnerabilities": 0, "note": "no report generated"}
    except FileNotFoundError:
        return {"error": "wapiti not installed"}
    except Exception as e:
        return {"error": str(e)}


async def _wfuzz_dir(target: str) -> dict:
    base_url = target.rstrip("/")
    # Use common wordlist
    wordlist = "/usr/share/wordlists/dirb/common.txt"
    if not os.path.exists(wordlist):
        wordlist = "/usr/share/seclists/Discovery/Web-Content/common.txt"
    if not os.path.exists(wordlist):
        return {"error": "no wordlist found. Install: apt install wordlists"}
    try:
        r = subprocess.run(
            ["wfuzz", "-z", f"file,{wordlist}", "--hc", "404", f"{base_url}/FUZZ", "-f", "json"],
            capture_output=True, text=True, timeout=300
        )
        results = [json.loads(l) for l in r.stdout.strip().split("\n") if l.strip() and l[0] == '{']
        return {"total_hits": len(results)}
    except FileNotFoundError:
        return {"error": "wfuzz not installed"}
    except Exception as e:
        return {"error": str(e)}


async def _subdomain_enum(domain: str) -> dict:
    # Extract domain from URL
    m = re.search(r'https?://([^/:]+)', domain)
    if m:
        domain = m.group(1)
    # Strip www
    domain = re.sub(r'^www\.', '', domain)

    subdomains = set()
    # crt.sh
    try:
        r = subprocess.run(
            ["curl", "-s", f"https://crt.sh/?q=%25.{domain}&output=json"],
            capture_output=True, text=True, timeout=30
        )
        for entry in json.loads(r.stdout or "[]"):
            for name in entry.get("name_value", "").lower().split("\n"):
                name = name.strip().lstrip("*.")
                if name.endswith(domain):
                    subdomains.add(name)
    except: pass

    return {"total": len(subdomains), "sample": sorted(list(subdomains))[:50]}


# ============================================================
# API Security Scanning
# ============================================================

async def _scan_api(target: str, deep: bool) -> dict:
    """Run API security checks."""
    api = {}

    # CORS misconfiguration
    api["cors"] = await _check_cors(target)
    # Security headers
    api["headers"] = await _check_security_headers(target)
    # SSL/TLS audit
    api["ssl"] = await _ssl_audit(target)
    # Cookie audit
    api["cookies"] = await _cookie_audit(target)

    if deep:
        # JWT analysis (if target exposes common endpoints)
        api["jwt_check"] = await _jwt_check(target)
        # Rate limiting test
        api["rate_limit"] = await _rate_limit_test(target)

    return api


async def _check_cors(target: str) -> dict:
    origin = "https://evil.com"
    try:
        r = subprocess.run(
            ["curl", "-sI", "-H", f"Origin: {origin}", target],
            capture_output=True, text=True, timeout=30
        )
        acao = re.findall(r'Access-Control-Allow-Origin:\s*(.+)', r.stdout, re.IGNORECASE)
        acac = "Access-Control-Allow-Credentials: true" in r.stdout
        is_vuln = any(o.strip() in ("*", origin) for o in acao) and acac
        return {
            "allow_origin": acao,
            "allow_credentials": acac,
            "vulnerable": is_vuln,
            "recommendation": "Use explicit origin whitelist" if is_vuln else None
        }
    except Exception as e:
        return {"error": str(e)}


async def _check_security_headers(target: str) -> dict:
    required = [
        "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options",
        "Strict-Transport-Security", "Referrer-Policy", "Permissions-Policy"
    ]
    try:
        r = subprocess.run(["curl", "-sI", target], capture_output=True, text=True, timeout=30)
        headers = {}
        for h in required:
            m = re.search(rf'{h}:\s*(.+)', r.stdout, re.IGNORECASE)
            headers[h] = m.group(1).strip() if m else "MISSING"
        missing = [h for h, v in headers.items() if v == "MISSING"]
        grade = "A" if len(missing) == 0 else "B" if len(missing) <= 2 else "C" if len(missing) <= 4 else "F"
        return {"headers": headers, "missing": missing, "grade": grade}
    except Exception as e:
        return {"error": str(e)}


async def _ssl_audit(target: str) -> dict:
    host = re.sub(r'https?://', '', target).split('/')[0].split(':')[0]
    cmd = ["testssl", "--jsonfile", "/tmp/testssl.json", f"{host}:443"]
    # Fallback
    if subprocess.run(["which", "testssl"], capture_output=True).returncode != 0:
        cmd[0] = "/opt/testssl/testssl.sh"
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        try:
            with open("/tmp/testssl.json") as f:
                data = json.load(f)
            findings = data.get("scanResult", [])
            sevs = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "OK": 0}
            for item in findings:
                s = item.get("severity", "OK")
                sevs[s] = sevs.get(s, 0) + 1
            grade = "F" if sevs["CRITICAL"] > 0 else "C" if sevs["HIGH"] > 0 else "B" if sevs["MEDIUM"] > 2 else "A"
            return {"grade": grade, "findings": sevs}
        except:
            return {"error": "could not parse report"}
    except FileNotFoundError:
        return {"error": "testssl.sh not found"}
    except Exception as e:
        return {"error": str(e)}


async def _cookie_audit(target: str) -> dict:
    try:
        r = subprocess.run(["curl", "-sI", target], capture_output=True, text=True, timeout=30)
        cookies = re.findall(r'Set-Cookie:\s*(.+?);', r.stdout, re.IGNORECASE)
        results = []
        for c in cookies:
            results.append({
                "name": c.split("=")[0][:30],
                "secure": "Secure" in c,
                "httponly": "HttpOnly" in c,
                "samesite": (re.findall(r'SameSite=(\w+)', c) or ["NOT_SET"])[0]
            })
        issues = sum(1 for c in results if not c["secure"] or not c["httponly"] or c["samesite"] == "NOT_SET")
        return {"cookies": results, "issues": issues}
    except Exception as e:
        return {"error": str(e)}


async def _jwt_check(target: str) -> dict:
    """Quick JWT configuration check on common endpoints."""
    endpoints = ["/api/auth", "/auth", "/login", "/api/v1"]
    results = []
    for ep in endpoints:
        try:
            r = subprocess.run(
                ["curl", "-sI", f"{target.rstrip('/')}{ep}"],
                capture_output=True, text=True, timeout=10
            )
            auth_header = re.findall(r'(?i)(www-authenticate|authorization):\s*(.+)', r.stdout)
            if auth_header:
                results.append({"endpoint": ep, "auth_headers": auth_header})
        except: pass
    return {"endpoints_checked": len(endpoints), "auth_detected": results}


async def _rate_limit_test(target: str) -> dict:
    """Test basic rate limiting by sending rapid requests."""
    try:
        # 20 requests in 5 seconds
        r = subprocess.run(
            ["bash", "-c", f"for i in $(seq 1 20); do curl -sI {target} -o /dev/null -w '%{{http_code}}\n' & done; wait"],
            capture_output=True, text=True, timeout=30
        )
        codes = r.stdout.strip().split("\n")
        rate_limited = sum(1 for c in codes if c.strip() == "429")
        return {
            "requests_sent": 20,
            "rate_limited_429": rate_limited,
            "vulnerable": rate_limited == 0,
            "recommendation": "Implement rate limiting" if rate_limited == 0 else None
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Mobile App Scanning
# ============================================================

async def _scan_mobile(apk_path: str, deep: bool) -> dict:
    if not apk_path or not os.path.exists(apk_path):
        return {"error": "no APK path provided or file not found"}

    mobile = {}

    # APK static analysis
    mobile["apk_analysis"] = await _apk_analyze(apk_path)
    # Hardcoded secrets
    mobile["secrets"] = await _android_secrets(apk_path, deep)

    if deep:
        # MobSF scan
        mobile["mobsf"] = await _mobsf_scan(apk_path)

    return mobile


async def _apk_analyze(apk_path: str) -> dict:
    result = {"file": apk_path}
    try:
        r = subprocess.run(["aapt", "dump", "badging", apk_path], capture_output=True, text=True, timeout=30)
        result["package"] = re.findall(r"package:\s*name='([^']+)'", r.stdout)
        result["version"] = re.findall(r"versionName='([^']+)'", r.stdout)
        result["min_sdk"] = re.findall(r"sdkVersion:'(\d+)'", r.stdout)

        perms = re.findall(r"uses-permission:'([^']+)'", r.stdout)
        result["permissions_total"] = len(perms)
        # Flag dangerous permissions
        dangerous_patterns = ["CAMERA", "LOCATION", "CONTACTS", "RECORD_AUDIO", "SMS", "STORAGE", "READ_PHONE_STATE"]
        dangerous = []
        for p in perms:
            for dp in dangerous_patterns:
                if dp in p:
                    dangerous.append({"permission": p, "risk": dp})
                    break
        result["dangerous_permissions"] = dangerous
    except FileNotFoundError:
        result["aapt"] = "not available"
    except Exception as e:
        result["aapt_error"] = str(e)
    return result


async def _android_secrets(apk_path: str, deep: bool) -> dict:
    result = {}
    try:
        r = subprocess.run(["strings", apk_path], capture_output=True, text=True, timeout=60)
        patterns = {
            "google_api": r'AIza[0-9A-Za-z\-_]{35}',
            "aws_key": r'AKIA[0-9A-Z]{16}',
            "private_key": r'-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----',
            "jwt_secret": r'(?i)(jwt|jws)["\s:=]+["\s]?([A-Za-z0-9\-_+/]{20,})',
            "generic_secret": r'(?i)(secret|password|passwd)["\s:=]+["\s]?([^"\s]{6,})',
        }
        found = {}
        for name, pat in patterns.items():
            matches = re.findall(pat, r.stdout)
            if matches:
                found[name] = len(matches)
        result["surface_scan"] = found
    except: pass

    if deep:
        try:
            tmpdir = tempfile.mkdtemp(prefix="apk_deep_")
            r = subprocess.run(["apktool", "d", apk_path, "-o", tmpdir, "-f"],
                               capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                r2 = subprocess.run(
                    ["grep", "-rI", "-E",
                     r'const-string.*"(AIza|sk-|AKIA|pk_live|sk_live|eyJ|-----BEGIN)"'],
                    capture_output=True, text=True, timeout=30, cwd=tmpdir
                )
                result["deep_scan"] = {
                    "decompiled": True,
                    "hardcoded_in_smali": len(r2.stdout.strip().split("\n")) if r2.stdout.strip() else 0
                }
            shutil.rmtree(tmpdir, ignore_errors=True)
        except FileNotFoundError:
            result["deep_scan"] = "apktool not installed"
        except: pass
    return result


async def _mobsf_scan(apk_path: str) -> dict:
    basename = os.path.basename(apk_path)
    cmd = [
        "docker", "run", "--rm", "-v", f"{os.path.abspath(apk_path)}:/app/{basename}",
        "opensecurity/mobile-security-framework-mobsf:latest",
        "python3", "manage.py", "static_analyzer", "-f", f"/app/{basename}"
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        try:
            data = json.loads(r.stdout)
            return {"score": data.get("security_score", "N/A"), "total_findings": data.get("total_count", len(data.get("results", [])))}
        except:
            return {"output_tail": r.stdout[-3000:]}
    except FileNotFoundError:
        return {"error": "Docker/MobSF not available"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Infrastructure Scanning
# ============================================================

async def _scan_infra(target: str, deep: bool) -> dict:
    infra = {}

    host = re.sub(r'https?://', '', target).split('/')[0].split(':')[0]

    # Port scan
    ports = "1-65535" if deep else "1-1000"
    infra["ports"] = await _nmap_port_scan(host, ports)

    if deep:
        # SSH hardening check
        infra["ssh_hardening"] = await _ssh_check(host)
        # WhatWeb fingerprinting
        infra["fingerprint"] = await _whatweb_fingerprint(target)

    return infra


async def _nmap_port_scan(host: str, ports: str) -> dict:
    try:
        r = subprocess.run(
            ["nmap", "-sV", "-p", ports, host, "-oX", "-"],
            capture_output=True, text=True, timeout=600
        )
        port_data = re.findall(
            r'portid="(\d+)".*?<state state="open".*?<service name="([^"]*)".*?product="([^"]*)"',
            r.stdout
        )
        return {
            "total_open": len(port_data),
            "open_ports": [{"port": p[0], "service": p[1], "product": p[2]} for p in port_data]
        }
    except FileNotFoundError:
        return {"error": "nmap not installed"}
    except Exception as e:
        return {"error": str(e)}


async def _ssh_check(host: str) -> dict:
    """Quick SSH hardening audit using ssh-audit."""
    try:
        r = subprocess.run(["ssh-audit", host], capture_output=True, text=True, timeout=30)
        # Extract grade
        grade = re.findall(r'overall result:\s*(.+)', r.stdout, re.IGNORECASE)
        warnings = re.findall(r'warn.*\n', r.stdout, re.IGNORECASE)
        return {
            "grade": grade[0].strip() if grade else "unknown",
            "warnings": len(warnings),
            "detail": r.stdout[-500:] if r.stdout else ""
        }
    except FileNotFoundError:
        # Fallback: basic ssh check
        try:
            r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "PasswordAuthentication=no",
                                "-o", "ConnectTimeout=5", f"nonexistent@{host}", "exit"],
                               capture_output=True, text=True, timeout=15)
            return {"basic_check": "ssh port open", "note": "ssh-audit not installed for full audit"}
        except:
            return {"error": "ssh-audit not installed"}
    except Exception as e:
        return {"error": str(e)}


async def _whatweb_fingerprint(target: str) -> dict:
    try:
        r = subprocess.run(
            ["whatweb", "-a", "1", "--log-json=/tmp/whatweb.json", target],
            capture_output=True, text=True, timeout=60
        )
        try:
            with open("/tmp/whatweb.json") as f:
                data = json.load(f)
            plugins = data[0].get("plugins", {}) if data else {}
            techs = {k: str(v.get("string", [""])[0])[:50] for k, v in plugins.items()}
            return {"technologies": list(techs.keys())}
        except:
            return {}
    except FileNotFoundError:
        return {"error": "whatweb not installed"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Compliance Scanning
# ============================================================

async def _scan_compliance(target: str, deep: bool) -> dict:
    host = re.sub(r'https?://', '', target).split('/')[0].split(':')[0]
    comp = {}

    # SSL/TLS full audit
    comp["ssl"] = await _ssl_audit(target)
    # Cookie audit (cross-listed)
    comp["cookies"] = await _cookie_audit(target)
    # CORS check
    comp["cors"] = await _check_cors(target)
    # Security headers
    comp["headers"] = await _check_security_headers(target)

    if deep:
        # OWASP ZAP baseline
        comp["zap_baseline"] = await _zap_baseline(target)

    # Compute overall grade
    grades = []
    if isinstance(comp.get("ssl"), dict):
        grades.append(comp["ssl"].get("grade", "B"))
    if isinstance(comp.get("headers"), dict):
        grades.append(comp["headers"].get("grade", "B"))
    comp["overall_grade"] = _min_grade(grades)
    return comp


async def _zap_baseline(target: str) -> dict:
    try:
        r = subprocess.run(
            ["docker", "run", "--rm", "owasp/zap2docker-stable",
             "zap-baseline-scan.py", "-t", target, "-r", "/tmp/zap_baseline.html"],
            capture_output=True, text=True, timeout=600
        )
        alerts = re.findall(r'(\d+)\s+alerts?\s*[\(:]\s*(High|Medium|Low|Informational)', r.stdout, re.IGNORECASE)
        sevs = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
        for count, sev in alerts:
            sevs[sev] = sevs.get(sev, 0) + int(count)
        return {"zap_alerts": sevs}
    except FileNotFoundError:
        return {"error": "Docker/ZAP not available"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Summary
# ============================================================

def _build_summary(sections: dict) -> dict:
    criticals = 0
    highs = 0
    mediums = 0
    total_issues = 0

    for section_name, section in sections.items():
        if section_name == "web":
            for key in ("sql_injection", "xss", "wapiti"):
                sub = section.get(key, {})
                if isinstance(sub, dict):
                    total_issues += sub.get("vuln_params", 0) + sub.get("xss_found", 0) + sub.get("vulnerabilities", 0)

        elif section_name == "api":
            for key in ("cors", "headers", "cookies"):
                sub = section.get(key, {})
                if isinstance(sub, dict) and sub.get("vulnerable"):
                    highs += 1
            h = section.get("headers", {})
            if isinstance(h, dict):
                missing = len(h.get("missing", []))
                if missing > 2: highs += missing

        elif section_name == "mobile":
            for key in ("apk_analysis", "secrets"):
                sub = section.get(key, {})
                if isinstance(sub, dict):
                    dang = sub.get("dangerous_permissions", [])
                    highs += len(dang)
                    sf = sub.get("surface_scan", {})
                    if isinstance(sf, dict):
                        criticals += sum(sf.values())

        elif section_name == "infra":
            ports = section.get("ports", {})
            if isinstance(ports, dict):
                open_count = ports.get("total_open", 0)
                if open_count > 10: mediums += open_count
                elif open_count > 5: highs += open_count // 2

    risk_level = "CRITICAL" if criticals > 0 else "HIGH" if highs > 5 else "MEDIUM" if highs > 0 or mediums > 5 else "LOW"
    return {
        "risk_level": risk_level,
        "critical": criticals,
        "high": highs,
        "medium": mediums,
        "total_issues": total_issues + criticals + highs + mediums
    }


def _min_grade(grades: list) -> str:
    order = {"A": 0, "B": 1, "C": 2, "F": 3}
    return max(grades, key=lambda g: order.get(g, 3)) if grades else "B"
