"""
Contract Scanning Tools (16 atomic tools + 1 composite)
========================================================
Slither, Aderyn, Mythril, Semgrep, Solhint, Echidna, Forge,
nmap, nuclei, ZAP, npm audit, cast, grep

Composite: contract_audit — orchestrates all 16 sub-tools, returns unified report.
"""

import mcp.types as types
from .shared import run_npm_audit, run_nmap, run_nuclei, run_zap

# ============================================================
# Tool Definitions
# ============================================================

CONTRACT_TOOLS = [
    # === Composite Entry Tool ===
    types.Tool(
        name="contract_audit",
        description="Run full smart contract security audit (build + test + slither + aderyn + mythril + echidna + semgrep + solhint)",
        inputSchema={
            "type": "object",
            "required": ["project_path"],
            "properties": {
                "project_path": {"type": "string", "description": "Path to Foundry project root"},
                "scope": {"type": "string", "description": "Audit scope: static, fuzz, secrets, all (default: all)"},
                "rpc_url": {"type": "string", "description": "RPC URL for fork-based fuzzing (optional)"},
                "block_number": {"type": "integer", "description": "Block number for fork testing (optional)"},
                "deployed_address": {"type": "string", "description": "Deployed contract address for verification (optional)"},
                "skip": {"type": "string", "description": "Comma-separated tools to skip (e.g. echidna,mythril)"}
            }
        }
    ),
    types.Tool(
        name="forge_build",
        description="Compile Solidity contracts with forge build",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to Foundry project root"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="forge_test",
        description="Run Foundry unit tests (forge test -vvv)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to Foundry project root"},
                "match": {"type": "string", "description": "Optional test name pattern filter"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="forge_coverage",
        description="Generate forge test coverage report",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to Foundry project root"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="slither_scan",
        description="Run Slither static analysis (106 built-in detectors)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to contract project"},
                "detect": {"type": "string", "description": "Comma-separated detector names or 'all'"},
                "solc_version": {"type": "string", "description": "Solidity compiler version"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="slither_custom",
        description="Run custom Slither detectors (v2-unprotected-initializer, v3-storage-layout, v4-unchecked-delegatecall, v10-approve-race, v14-flashloan-callback)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to contract project"},
                "detector_path": {"type": "string", "description": "Path to slither-detectors/ directory"}
            },
            "required": ["project_path", "detector_path"]
        }
    ),
    types.Tool(
        name="aderyn_scan",
        description="Run Aderyn static analysis (88 Rust-based detectors)",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to contract project"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="mythril_analyze",
        description="Run Mythril symbolic execution on a contract",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to contract project"},
                "target_contract": {"type": "string", "description": "Target .sol file path relative to project"}
            },
            "required": ["project_path", "target_contract"]
        }
    ),
    types.Tool(
        name="echidna_fuzz",
        description="Run Echidna fuzzing with a harness",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to contract project"},
                "harness_path": {"type": "string", "description": "Path to .sol harness file"},
                "contract_name": {"type": "string", "description": "Contract name in harness"},
                "test_limit": {"type": "integer", "description": "Max test sequences (default: 100000)"}
            },
            "required": ["project_path", "harness_path", "contract_name"]
        }
    ),
    types.Tool(
        name="semgrep_solidity",
        description="Run Semgrep with Solidity rules",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to contract project"},
                "src_dir": {"type": "string", "description": "Source directory (default: src/)"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="solhint_lint",
        description="Run Solhint linter on Solidity files",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to contract project"},
                "src_pattern": {"type": "string", "description": "File pattern (default: src/**/*.sol)"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="npm_audit",
        description="Run npm/pnpm audit for dependency CVEs",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to project with package.json"},
                "package_manager": {"type": "string", "description": "'npm' or 'pnpm' (default: pnpm)"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="nmap_scan",
        description="Port scan target host",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target IP or hostname"},
                "ports": {"type": "string", "description": "Port range (default: 1-65535)"},
                "scan_type": {"type": "string", "description": "Scan type: quick(1-1000), full(1-65535), custom"}
            },
            "required": ["target"]
        }
    ),
    types.Tool(
        name="nuclei_scan",
        description="Run Nuclei vulnerability template scan",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string", "description": "Target URL or IP:port"},
                "severity": {"type": "string", "description": "Min severity: low, medium, high, critical"},
                "templates": {"type": "string", "description": "Template path or tag (e.g. owasp-top-10)"},
                "custom_templates": {"type": "string", "description": "Path to custom nuclei templates directory"}
            },
            "required": ["target_url"]
        }
    ),
    types.Tool(
        name="zap_scan",
        description="Run OWASP ZAP baseline web vulnerability scan",
        inputSchema={
            "type": "object",
            "properties": {
                "target_url": {"type": "string", "description": "Target web application URL"},
                "scan_type": {"type": "string", "description": "baseline, full, or api (default: baseline)"}
            },
            "required": ["target_url"]
        }
    ),
    types.Tool(
        name="grep_secrets",
        description="Scan for hardcoded secrets and sensitive patterns",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "Path to scan"},
                "patterns": {"type": "string", "description": "Custom grep pattern (default: private_key|password|secret|api_key|0x[a-fA-F0-9]{64})"}
            },
            "required": ["project_path"]
        }
    ),
    types.Tool(
        name="cast_verify",
        description="Verify on-chain contract deployment with cast",
        inputSchema={
            "type": "object",
            "properties": {
                "contract_address": {"type": "string", "description": "Deployed contract address"},
                "rpc_url": {"type": "string", "description": "RPC endpoint URL"},
                "chain_id": {"type": "integer", "description": "Chain ID"}
            },
            "required": ["contract_address", "rpc_url"]
        }
    ),
]

# ============================================================
# Tool Handlers
# ============================================================

import subprocess
import json
import os
import re

def register_contract_tools(server):
    """Register all contract scanning tools on the MCP server."""
    for tool in CONTRACT_TOOLS:
        if server is not None:
            server._tool_schemas[tool.name] = tool
    return CONTRACT_TOOLS

async def handle_contract_tool(name: str, args: dict) -> str | None:
    """Handle contract scanning tool calls. Returns None if not a contract tool."""
    handlers = {
        "contract_audit": _contract_audit,
        "forge_build": _forge_build,
        "forge_test": _forge_test,
        "forge_coverage": _forge_coverage,
        "slither_scan": _slither_scan,
        "slither_custom": _slither_custom,
        "aderyn_scan": _aderyn_scan,
        "mythril_analyze": _mythril_analyze,
        "echidna_fuzz": _echidna_fuzz,
        "semgrep_solidity": _semgrep_solidity,
        "solhint_lint": _solhint_lint,
        "npm_audit": _npm_audit,
        "nmap_scan": _nmap_scan,
        "nuclei_scan": _nuclei_scan,
        "zap_scan": _zap_scan,
        "grep_secrets": _grep_secrets,
        "cast_verify": _cast_verify,
    }
    if name in handlers:
        result = await handlers[name](args)
        return json.dumps(result, indent=2)
    return None

async def _forge_build(args: dict) -> dict:
    project = args["project_path"]
    try:
        r = subprocess.run(["forge", "build"], cwd=project, capture_output=True, text=True, timeout=120)
        return {
            "tool": "forge build",
            "success": r.returncode == 0,
            "exit_code": r.returncode,
            "output": r.stdout[-5000:] if r.stdout else "",
            "errors": r.stderr[-2000:] if r.stderr else ""
        }
    except FileNotFoundError:
        return {"tool": "forge build", "error": "forge not installed"}
    except Exception as e:
        return {"tool": "forge build", "error": str(e)}

async def _forge_test(args: dict) -> dict:
    project = args["project_path"]
    match = args.get("match", "")
    cmd = ["forge", "test", "-vvv"]
    if match:
        cmd += ["--match-test", match]
    try:
        r = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=300)
        # Parse test results
        passed = len(re.findall(r'\[PASS\]', r.stdout))
        failed = len(re.findall(r'\[FAIL', r.stdout))
        return {
            "tool": "forge test",
            "success": r.returncode == 0,
            "passed": passed,
            "failed": failed,
            "output_tail": r.stdout[-3000:] if r.stdout else ""
        }
    except FileNotFoundError:
        return {"tool": "forge test", "error": "forge not installed"}
    except Exception as e:
        return {"tool": "forge test", "error": str(e)}

async def _forge_coverage(args: dict) -> dict:
    project = args["project_path"]
    try:
        r = subprocess.run(["forge", "coverage"], cwd=project, capture_output=True, text=True, timeout=120)
        # Extract coverage percentage
        cov_match = re.findall(r'(\d+\.?\d*)%', r.stdout)
        coverage = cov_match[-1] if cov_match else "unknown"
        return {
            "tool": "forge coverage",
            "coverage_pct": coverage,
            "output_tail": r.stdout[-2000:] if r.stdout else ""
        }
    except FileNotFoundError:
        return {"tool": "forge coverage", "error": "forge not installed"}
    except Exception as e:
        return {"tool": "forge coverage", "error": str(e)}

async def _slither_scan(args: dict) -> dict:
    project = args["project_path"]
    detect = args.get("detect", "all")
    cmd = ["slither", ".", "--filter-paths", "lib|test"]
    if detect != "all":
        cmd += ["--detect", detect]
    try:
        r = subprocess.run(cmd, cwd=project, capture_output=True, text=True, timeout=300)
        # Parse findings
        findings = re.findall(r'(\w+)\.(\w+) \(([^)]+)\)', r.stdout)
        high = len([f for f in findings if 'High' in str(f)])
        med = len([f for f in findings if 'Medium' in str(f)])
        low = len([f for f in findings if 'Low' in str(f)])
        return {
            "tool": "slither",
            "success": True,
            "total_findings": len(findings),
            "high": high, "medium": med, "low": low,
            "output_tail": r.stdout[-5000:] if r.stdout else r.stderr[-2000:]
        }
    except FileNotFoundError:
        return {"tool": "slither", "error": "slither not installed"}
    except Exception as e:
        return {"tool": "slither", "error": str(e)}

async def _slither_custom(args: dict) -> dict:
    project = args["project_path"]
    detector_path = args["detector_path"]
    detectors = "v2-unprotected-initializer,v3-storage-layout,v4-unchecked-delegatecall,v10-approve-race,v14-flashloan-callback"
    env = {**os.environ, "SLITHER_PLUGINS": detector_path}
    try:
        r = subprocess.run(
            ["slither", ".", "--detect", detectors, "--filter-paths", "lib|test"],
            cwd=project, capture_output=True, text=True, timeout=300, env=env
        )
        findings = re.findall(r'(\w+)\.(\w+) \(([^)]+)\)', r.stdout)
        return {
            "tool": "slither-custom",
            "detectors": detectors.split(","),
            "total_findings": len(findings),
            "output": r.stdout[-3000:] if r.stdout else r.stderr[-1000:]
        }
    except Exception as e:
        return {"tool": "slither-custom", "error": str(e)}

async def _aderyn_scan(args: dict) -> dict:
    project = args["project_path"]
    try:
        r = subprocess.run(["aderyn", "."], cwd=project, capture_output=True, text=True, timeout=300)
        # Parse aderyn findings
        issues = re.findall(r'(\w+-\d+):\s*(.+)', r.stdout)
        critical = len([i for i in issues if 'Critical' in i[1] or 'critical' in i[1]])
        high = len([i for i in issues if 'High' in i[1] or 'high' in i[1]])
        return {
            "tool": "aderyn",
            "total_issues": len(issues),
            "critical": critical, "high": high,
            "output_tail": r.stdout[-4000:] if r.stdout else r.stderr[-2000:]
        }
    except FileNotFoundError:
        return {"tool": "aderyn", "error": "aderyn not installed"}
    except Exception as e:
        return {"tool": "aderyn", "error": str(e)}

async def _mythril_analyze(args: dict) -> dict:
    project = args["project_path"]
    target = args["target_contract"]
    try:
        r = subprocess.run(
            ["myth", "analyze", target, "--execution-timeout", "120"],
            cwd=project, capture_output=True, text=True, timeout=300
        )
        # Parse mythril output for SWC IDs
        swc_ids = re.findall(r'SWC-(\d+)', r.stdout)
        issues = re.findall(r'(High|Medium|Low)', r.stdout)
        return {
            "tool": "mythril",
            "swc_ids": list(set(swc_ids)),
            "high": issues.count("High"),
            "medium": issues.count("Medium"),
            "low": issues.count("Low"),
            "output_tail": r.stdout[-3000:] if r.stdout else r.stderr[-2000:]
        }
    except FileNotFoundError:
        return {"tool": "mythril", "error": "mythril not installed"}
    except Exception as e:
        return {"tool": "mythril", "error": str(e)}

async def _echidna_fuzz(args: dict) -> dict:
    project = args["project_path"]
    harness = args["harness_path"]
    contract = args["contract_name"]
    limit = str(args.get("test_limit", 100000))
    try:
        r = subprocess.run(
            ["echidna-test", harness, "--contract", contract, "--test-limit", limit],
            cwd=project, capture_output=True, text=True, timeout=600
        )
        # Parse results
        passed = re.findall(r'\[PASSED\]', r.stdout)
        failed = re.findall(r'\[FAILED\]', r.stdout)
        return {
            "tool": "echidna",
            "contract": contract,
            "test_limit": limit,
            "passed": len(passed),
            "failed": len(failed),
            "output_tail": r.stdout[-3000:] if r.stdout else r.stderr[-2000:]
        }
    except FileNotFoundError:
        return {"tool": "echidna", "error": "echidna not installed"}
    except Exception as e:
        return {"tool": "echidna", "error": str(e)}

async def _semgrep_solidity(args: dict) -> dict:
    project = args["project_path"]
    src = args.get("src_dir", "src/")
    try:
        r = subprocess.run(
            ["semgrep", "--config", "solidity", src, "--json"],
            cwd=project, capture_output=True, text=True, timeout=120
        )
        try:
            data = json.loads(r.stdout)
            return {
                "tool": "semgrep",
                "total_findings": len(data.get("results", [])),
                "severity_breakdown": {
                    sev: len([x for x in data.get("results", [])
                             if x.get("extra", {}).get("severity") == sev])
                    for sev in ["ERROR", "WARNING", "INFO"]
                }
            }
        except json.JSONDecodeError:
            return {"tool": "semgrep", "raw_output": r.stdout[-2000:]}
    except FileNotFoundError:
        return {"tool": "semgrep", "error": "semgrep not installed"}
    except Exception as e:
        return {"tool": "semgrep", "error": str(e)}

async def _solhint_lint(args: dict) -> dict:
    project = args["project_path"]
    pattern = args.get("src_pattern", "src/**/*.sol")
    try:
        r = subprocess.run(
            ["npx", "solhint", pattern],
            cwd=project, capture_output=True, text=True, timeout=60
        )
        # Count issues by type
        errors = len(re.findall(r'error', r.stdout.lower()))
        warnings = len(re.findall(r'warn', r.stdout.lower()))
        return {
            "tool": "solhint",
            "errors": errors,
            "warnings": warnings,
            "output_tail": r.stdout[-2000:] if r.stdout else ""
        }
    except Exception as e:
        return {"tool": "solhint", "error": str(e)}

async def _npm_audit(args: dict) -> dict:
    return await run_npm_audit(args["project_path"], args.get("package_manager", "pnpm"))

async def _nmap_scan(args: dict) -> dict:
    scan_type = args.get("scan_type", "quick")
    return await run_nmap(args["target"],
        ports=args.get("ports", "1-1000" if scan_type == "quick" else "1-65535"),
        scan_type=scan_type)

async def _nuclei_scan(args: dict) -> dict:
    return await run_nuclei(args["target_url"],
        severity=args.get("severity", "low,medium,high,critical"),
        templates=args.get("templates", ""),
        custom_templates=args.get("custom_templates", ""))

async def _zap_scan(args: dict) -> dict:
    return await run_zap(args["target_url"], args.get("scan_type", "baseline"))

async def _grep_secrets(args: dict) -> dict:
    project = args["project_path"]
    pattern = args.get("patterns", r'0x[a-fA-F0-9]{64}|private_key|password\s*=|secret\s*=|api_key\s*=|sk-[a-zA-Z0-9]{32,}')
    try:
        r = subprocess.run(
            ["grep", "-rInE", pattern, project, "--exclude-dir=node_modules", "--exclude-dir=.git", "--exclude-dir=lib"],
            capture_output=True, text=True, timeout=60
        )
        lines = r.stdout.strip().split("\n") if r.stdout.strip() else []
        return {
            "tool": "grep-secrets",
            "matches": len(lines),
            "files_affected": len(set(l.split(":")[0] for l in lines if ":" in l)),
            "samples": lines[:20]
        }
    except Exception as e:
        return {"tool": "grep-secrets", "error": str(e)}

async def _cast_verify(args: dict) -> dict:
    address = args["contract_address"]
    rpc = args["rpc_url"]
    try:
        # Check if contract is deployed
        r = subprocess.run(
            ["cast", "codesize", address, "--rpc-url", rpc],
            capture_output=True, text=True, timeout=30
        )
        codesize = r.stdout.strip()
        # Get admin/owner if possible
        r2 = subprocess.run(
            ["cast", "call", address, "owner()(address)", "--rpc-url", rpc],
            capture_output=True, text=True, timeout=30
        )
        owner = r2.stdout.strip() if r2.returncode == 0 else "N/A"
        return {
            "tool": "cast verify",
            "address": address,
            "codesize": codesize,
            "is_deployed": codesize != "0" and codesize != "0x",
            "owner": owner
        }
    except FileNotFoundError:
        return {"tool": "cast verify", "error": "cast not installed"}
    except Exception as e:
        return {"tool": "cast verify", "error": str(e)}

# ============================================================
# Composite Tool: contract_audit
# ============================================================

async def _contract_audit(args: dict) -> dict:
    """Orchestrate full smart contract security audit."""
    project = args["project_path"]
    scope = args.get("scope", "all")
    skip_list = (args.get("skip", "") or "").split(",")
    skip = set(s.strip() for s in skip_list if s.strip())

    results = {
        "tool": "contract_audit",
        "project": project,
        "scope": scope,
        "sections": {}
    }

    # === Build & Test (always first) ===
    if "forge_build" not in skip:
        results["sections"]["build"] = await _forge_build(args)
    if "forge_test" not in skip:
        results["sections"]["test"] = await _forge_test(args)

    # === Static Analysis ===
    if scope in ("static", "all"):
        if "slither" not in skip:
            results["sections"]["slither"] = await _slither_scan(args)
        if "aderyn" not in skip:
            results["sections"]["aderyn"] = await _aderyn_scan(args)
        if "semgrep" not in skip:
            results["sections"]["semgrep"] = await _semgrep_solidity(args)
        if "solhint" not in skip:
            results["sections"]["solhint"] = await _solhint_lint(args)
        if "mythril" not in skip:
            results["sections"]["mythril"] = await _mythril_analyze(args)

    # === Fuzzing ===
    if scope in ("fuzz", "all"):
        if "echidna" not in skip:
            results["sections"]["echidna"] = await _echidna_fuzz(args)

    # === Secrets & Dependency ===
    if scope in ("secrets", "all"):
        if "grep" not in skip:
            results["sections"]["secrets"] = await _grep_secrets(args)
        if "npm" not in skip:
            results["sections"]["npm_audit"] = await _npm_audit(args)

    # === Verification ===
    deployed = args.get("deployed_address", "")
    if deployed and scope in ("verify", "all"):
        results["sections"]["contract_verification"] = await _cast_verify(args)

    # === Summary ===
    results["summary"] = _contract_summary(results["sections"])
    return results


def _contract_summary(sections: dict) -> dict:
    critical, high, medium, low = 0, 0, 0, 0

    for name, section in sections.items():
        if not isinstance(section, dict):
            continue
        if name == "slither":
            sevs = section.get("severity", {})
            high += sevs.get("High", 0)
            medium += sevs.get("Medium", 0)
            low += sevs.get("Low", 0)
        elif name == "aderyn":
            total = section.get("total_findings", 0) or len(section.get("findings", []))
            high += total
        elif name == "mythril":
            sevs = section.get("severity", {})
            high += sevs.get("High", 0)
            medium += sevs.get("Medium", 0)
        elif name == "semgrep":
            sevs = section.get("severity", {})
            high += sevs.get("ERROR", 0)
            medium += sevs.get("WARNING", 0)
        elif name == "solhint":
            total = section.get("total_issues", 0) or len(section.get("issues", []))
            medium += total
        elif name == "echidna":
            failed = section.get("failed", 0)
            if failed > 0:
                critical += 1
        elif name == "secrets":
            found = section.get("total_found", 0) or section.get("matches", 0)
            if found > 0:
                critical += found
        elif name == "npm_audit":
            critical += section.get("critical", 0)
            high += section.get("high", 0)
        elif name == "test":
            if section.get("failed", 0) > 0:
                high += 1

    risk = "CRITICAL" if critical > 0 else "HIGH" if high > 5 else "MEDIUM" if high > 0 or medium > 5 else "LOW"
    return {
        "risk_level": risk,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low
    }
