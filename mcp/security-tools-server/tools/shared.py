"""
Shared tool implementations used by both contract and centralized scanners.
Avoids code duplication for cross-domain tools like nmap, nuclei, ZAP, npm audit.
"""

import subprocess
import json
import re
import os

# Build a PATH-enhanced environment for subprocess calls
# systemd Environment= may not propagate to subprocess children
_FULL_PATH = os.pathsep.join([
    os.path.expanduser("~/.foundry/bin"),
    os.path.expanduser("~/go/bin"),
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/.cyfrin/bin"),
    "/usr/local/go/bin",
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
])
_ENV = dict(os.environ)
_ENV["PATH"] = _FULL_PATH


def run(cmd, **kwargs):
    """Run a command with full PATH, returning CompletedProcess."""
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("timeout", 120)
    kwargs.setdefault("env", _ENV)
    return subprocess.run(cmd, **kwargs)


# ============================================================
# Path helpers
# ============================================================

def find_contract_dir(project_path: str) -> str:
    """Auto-detect Foundry/Hardhat project directory.
    
    If project_path itself contains foundry.toml, return it.
    Otherwise search subdirectories (contracts/, hardhat/, solidity/).
    """
    if os.path.exists(os.path.join(project_path, "foundry.toml")):
        return project_path
    for sub in ("contracts", "hardhat", "solidity"):
        sub_path = os.path.join(project_path, sub)
        if os.path.exists(os.path.join(sub_path, "foundry.toml")):
            return sub_path
    return project_path


# ============================================================
# npm/pnpm audit (shared)
# ============================================================

async def run_npm_audit(project_path: str, package_manager: str = "pnpm") -> dict:
    """Run npm/pnpm audit and return structured results."""
    try:
        r = subprocess.run(
            [package_manager, "audit", "--json"],
            cwd=project_path, capture_output=True, text=True, timeout=120
        )
        try:
            data = json.loads(r.stdout)
            vulns = data.get("vulnerabilities", data.get("advisories", {}))
            if isinstance(vulns, dict):
                total = len(vulns)
                critical = sum(1 for v in vulns.values() if isinstance(v, dict) and v.get("severity") == "critical")
                high = sum(1 for v in vulns.values() if isinstance(v, dict) and v.get("severity") == "high")
            else:
                total = 0
                critical = high = 0
            return {
                "tool": f"{package_manager} audit",
                "total_vulns": total, "critical": critical, "high": high,
                "manager": package_manager
            }
        except json.JSONDecodeError:
            return {"tool": f"{package_manager} audit", "raw_tail": r.stdout[-2000:] or r.stderr[-2000:]}
    except FileNotFoundError:
        return {"tool": f"{package_manager} audit", "error": f"{package_manager} not installed"}
    except subprocess.TimeoutExpired:
        return {"tool": f"{package_manager} audit", "error": "timeout after 120s"}
    except Exception as e:
        return {"tool": f"{package_manager} audit", "error": str(e)}


# ============================================================
# nmap port scan (shared)
# ============================================================

async def run_nmap(target: str, ports: str = "1-1000", scan_type: str = "quick") -> dict:
    """Run nmap port scan and return structured open ports."""
    try:
        r = subprocess.run(
            ["nmap", "-sV", "-p", ports, target, "-oX", "-"],
            capture_output=True, text=True, timeout=600
        )
        ports_found = re.findall(
            r'portid="(\d+)".*?<state state="open".*?<service name="([^"]*)".*?product="([^"]*)"',
            r.stdout
        )
        return {
            "tool": "nmap",
            "target": target,
            "scan_type": scan_type,
            "port_range": ports,
            "open_ports": [
                {"port": p[0], "service": p[1], "product": p[2]} for p in ports_found
            ]
        }
    except FileNotFoundError:
        return {"tool": "nmap", "error": "nmap not installed"}
    except Exception as e:
        return {"tool": "nmap", "error": str(e)}


# ============================================================
# Nuclei vulnerability scan (shared)
# ============================================================

async def run_nuclei(target_url: str, severity: str = "low,medium,high,critical",
                     templates: str = "", custom_templates: str = "") -> dict:
    """Run nuclei vulnerability scan and return severity breakdown."""
    cmd = ["nuclei", "-u", target_url, "-severity", severity, "-json", "-silent"]
    if templates:
        cmd += ["-t", templates]
    if custom_templates:
        cmd += ["-t", custom_templates]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        findings = []
        for line in r.stdout.strip().split("\n"):
            if not line.strip():
                continue
            try:
                f = json.loads(line)
                findings.append({
                    "name": f.get("info", {}).get("name", ""),
                    "severity": f.get("info", {}).get("severity", ""),
                    "matched": f.get("matched-at", "")
                })
            except json.JSONDecodeError:
                continue
        sev_count = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            s = f["severity"].lower()
            if s in sev_count:
                sev_count[s] += 1
        return {
            "tool": "nuclei",
            "target": target_url,
            "total_findings": len(findings),
            "severity": sev_count
        }
    except FileNotFoundError:
        return {"tool": "nuclei", "error": "nuclei not installed"}
    except Exception as e:
        return {"tool": "nuclei", "error": str(e)}


# ============================================================
# OWASP ZAP scan (shared)
# ============================================================

async def run_zap(target_url: str, scan_type: str = "baseline") -> dict:
    """Run OWASP ZAP web vulnerability scan via Docker."""
    cmd = [
        "docker", "run", "--rm", "owasp/zap2docker-stable",
        f"zap-{scan_type}-scan.py", "-t", target_url, "-r", f"/tmp/zap_{scan_type}.html"
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        alerts = re.findall(r'(\d+)\s+alerts?\s*[\(:]\s*(High|Medium|Low|Informational)', r.stdout, re.IGNORECASE)
        return {
            "tool": "zap",
            "target": target_url,
            "scan_type": scan_type,
            "output_tail": r.stdout[-3000:],
            "note": "See HTML report for full details"
        }
    except FileNotFoundError:
        return {"tool": "zap", "error": "Docker or ZAP not available. Install: docker pull owasp/zap2docker-stable"}
    except Exception as e:
        return {"tool": "zap", "error": str(e)}


# ============================================================
# semgrep (shared — different config per domain)
# ============================================================

async def run_semgrep(project_path: str, config: str = "auto",
                      exclude: str = "node_modules,dist,build,.git",
                      src_dir: str = "") -> dict:
    """Run semgrep with given config and return structured findings."""
    cmd = ["semgrep", "--config", config, "--json", "--exclude", exclude]
    target = project_path
    if src_dir:
        target = os.path.join(project_path, src_dir)
    cmd.append(target)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        try:
            data = json.loads(r.stdout)
            results = data.get("results", [])
            sevs = {}
            for r2 in results:
                s = r2.get("extra", {}).get("severity", "INFO")
                sevs[s] = sevs.get(s, 0) + 1
            return {
                "tool": "semgrep",
                "config": config,
                "total": len(results),
                "severity": sevs
            }
        except json.JSONDecodeError:
            return {"tool": "semgrep", "raw_tail": r.stdout[-2000:] or r.stderr[-2000:]}
    except FileNotFoundError:
        return {"tool": "semgrep", "error": "semgrep not installed"}
    except Exception as e:
        return {"tool": "semgrep", "error": str(e)}


# ============================================================
# Helper: run subprocess safely
# ============================================================

def run_shell(cmd: list, timeout: int = 120, cwd: str = None, env: dict = None) -> tuple[int, str, str]:
    """Run a shell command safely, returning (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=cwd, env=env or os.environ)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, "", f"Timeout after {timeout}s"
    except Exception as e:
        return -3, "", str(e)
