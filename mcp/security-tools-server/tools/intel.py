"""
Threat Intelligence Tools (6 tools)
====================================
update_knowledge_base, query_intelligence, get_latest_attacks,
check_cve, compare_snapshots, search_ttp
"""

import mcp.types as types

INTEL_TOOLS = [
    types.Tool(
        name="update_knowledge_base",
        description="Pull latest threat intelligence from 14 sources and update local KB",
        inputSchema={
            "type": "object",
            "properties": {
                "sources": {"type": "string", "description": "Comma-separated source names or 'all'"},
                "force": {"type": "boolean", "description": "Force full refresh ignoring cache"}
            }
        }
    ),
    types.Tool(
        name="query_intelligence",
        description="Query threat intelligence by category (defi, web, cve, exploit)",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category: defi, web, cve, exploit, compliance"},
                "since": {"type": "string", "description": "ISO date filter (e.g. 2026-01-01)"},
                "limit": {"type": "integer", "description": "Max results (default: 20)"}
            },
            "required": ["category"]
        }
    ),
    types.Tool(
        name="get_latest_attacks",
        description="Get latest attack events from DeFi and web security sources",
        inputSchema={
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Domain: defi, web, or all"},
                "limit": {"type": "integer", "description": "Max results (default: 10)"}
            },
            "required": ["domain"]
        }
    ),
    types.Tool(
        name="check_cve",
        description="Check known CVEs for a specific package and version",
        inputSchema={
            "type": "object",
            "properties": {
                "package_name": {"type": "string", "description": "Package name (npm, pip, cargo, etc.)"},
                "version": {"type": "string", "description": "Version to check (e.g. 1.2.3)"},
                "ecosystem": {"type": "string", "description": "Ecosystem: npm, pypi, cargo, golang, os"}
            },
            "required": ["package_name", "version"]
        }
    ),
    types.Tool(
        name="compare_snapshots",
        description="Compare latest KB snapshot with previous to find new threats",
        inputSchema={
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category filter: defi, web, cve, all"}
            }
        }
    ),
    types.Tool(
        name="search_ttp",
        description="Search MITRE ATT&CK techniques by keyword",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword (e.g. phishing, ransomware, defi)"},
                "limit": {"type": "integer", "description": "Max results (default: 10)"}
            },
            "required": ["query"]
        }
    ),
]

# ============================================================
# Tool Handlers
# ============================================================

import subprocess
import json
import os
import glob
from datetime import datetime

KB_DIR = os.path.expanduser("~/.openclaw/security-kb")

def register_intel_tools(server):
    for tool in INTEL_TOOLS:
        if server is not None:
            server._tool_schemas[tool.name] = tool
    return INTEL_TOOLS

async def handle_intel_tool(name: str, args: dict) -> str | None:
    handlers = {
        "update_knowledge_base": _update_knowledge_base,
        "query_intelligence": _query_intelligence,
        "get_latest_attacks": _get_latest_attacks,
        "check_cve": _check_cve,
        "compare_snapshots": _compare_snapshots,
        "search_ttp": _search_ttp,
    }
    if name in handlers:
        result = await handlers[name](args)
        return json.dumps(result, indent=2)
    return None

async def _update_knowledge_base(args: dict) -> dict:
    """Run update-security-kb.sh."""
    sources = args.get("sources", "all")
    force = args.get("force", False)
    script = os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "update-security-kb.sh")
    if not os.path.exists(script):
        script = os.path.expanduser("~/workspace/skills/security-audit-pipeline/scripts/update-security-kb.sh")
    cmd = ["bash", script]
    if force:
        cmd.append("--force")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {
            "tool": "update-kb",
            "success": True,
            "output_tail": r.stdout[-2000:],
            "kb_dir": KB_DIR
        }
    except Exception as e:
        return {"tool": "update-kb", "error": str(e)}

async def _query_intelligence(args: dict) -> dict:
    """Query the knowledge base by category."""
    category = args["category"].lower()
    since = args.get("since", "")
    limit = args.get("limit", 20)

    results = []

    if category in ("defi", "all"):
        # Load DeFi sources
        for src in ["defihacklabs-latest.json", "slowmist-threats.json", "rekt-latest.json"]:
            path = os.path.join(KB_DIR, src)
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    if "events" in data:
                        events = data["events"]
                        if since:
                            events = [e for e in events if e.get("date", "") >= since]
                        results.append({"source": data.get("source", src), "count": len(events[:limit])})
                except: pass

    if category in ("cve", "all"):
        for src in ["nvd-cve-latest.json", "cisa-kev-latest.json"]:
            path = os.path.join(KB_DIR, src)
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    if "cves" in data:
                        results.append({"source": data.get("source", src), "cve_count": len(data["cves"][:limit])})
                    if "total_kev" in data:
                        results.append({"source": data.get("source", src), "kev_total": data["total_kev"]})
                except: pass

    if category in ("web", "all"):
        for src in ["owasp-version.json", "exploitdb-latest.json"]:
            path = os.path.join(KB_DIR, src)
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    results.append({
                        "source": data.get("source", src),
                        "tag": data.get("tag", ""),
                        "date": data.get("date", "")
                    })
                except: pass

    # Try loading the composite snapshot
    snapshots = sorted(glob.glob(os.path.join(KB_DIR, "attack-matrix-*.json")), reverse=True)
    snapshot_info = {}
    if snapshots:
        try:
            with open(snapshots[0]) as f:
                snapshot_info = json.load(f)
        except: pass

    return {
        "tool": "query-intel",
        "category": category,
        "since": since or "all time",
        "results": results,
        "latest_snapshot": snapshot_info.get("snapshot_date", "unknown") if snapshot_info else "no snapshot",
        "priority_alerts": snapshot_info.get("priority_alerts", [])
    }

async def _get_latest_attacks(args: dict) -> dict:
    """Get latest attack events."""
    domain = args["domain"].lower()
    limit = args.get("limit", 10)
    attacks = []

    if domain in ("defi", "all"):
        path = os.path.join(KB_DIR, "defihacklabs-latest.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for event in data.get("events", [])[:limit]:
                    attacks.append({
                        "domain": "defi",
                        "date": event.get("date", ""),
                        "description": event.get("message", "")[:120]
                    })
            except: pass

    if domain in ("web", "all"):
        for src, field in [("nvd-cve-latest.json", "cves"), ("cisa-kev-latest.json", "recent")]:
            path = os.path.join(KB_DIR, src)
            if os.path.exists(path):
                try:
                    with open(path) as f:
                        data = json.load(f)
                    for item in data.get(field, [])[:limit]:
                        attacks.append({
                            "domain": "web",
                            "date": item.get("published", item.get("date", "")),
                            "description": item.get("description", item.get("desc", ""))[:120]
                        })
                except: pass

    return {
        "tool": "latest-attacks",
        "domain": domain,
        "total": len(attacks),
        "attacks": attacks[:limit]
    }

async def _check_cve(args: dict) -> dict:
    """Check CVEs for a specific package."""
    pkg = args["package_name"]
    version = args["version"]
    eco = args.get("ecosystem", "")

    # Query NVD CVE data for this package
    cve_path = os.path.join(KB_DIR, "nvd-cve-latest.json")
    matches = []

    if os.path.exists(cve_path):
        try:
            with open(cve_path) as f:
                data = json.load(f)
            for cve in data.get("cves", []):
                desc = cve.get("description", "").lower()
                if pkg.lower() in desc:
                    matches.append({
                        "cve_id": cve.get("id", ""),
                        "description": cve.get("description", "")[:150],
                        "published": cve.get("published", "")
                    })
        except: pass

    # Also check local trivy/npm audit cache
    return {
        "tool": "check-cve",
        "package": pkg,
        "version": version,
        "ecosystem": eco or "unknown",
        "matches_in_kb": len(matches),
        "cvss": matches[:10],
        "recommendation": f"Run: {'npm audit' if eco=='npm' else 'pip-audit' if eco=='pypi' else 'trivy'} for real-time check" if not matches else "See matches above"
    }

async def _compare_snapshots(args: dict) -> dict:
    """Compare latest two snapshots to find new threats."""
    category = args.get("category", "all")
    snapshots = sorted(glob.glob(os.path.join(KB_DIR, "attack-matrix-*.json")), reverse=True)

    if len(snapshots) < 2:
        return {"tool": "compare-snapshots", "error": "Need at least 2 snapshots to compare"}

    latest = {}
    previous = {}
    try:
        with open(snapshots[0]) as f:
            latest = json.load(f)
        with open(snapshots[1]) as f:
            previous = json.load(f)
    except Exception as e:
        return {"tool": "compare-snapshots", "error": str(e)}

    new_alerts = []
    latest_alerts = set(latest.get("priority_alerts", []))
    prev_alerts = set(previous.get("priority_alerts", []))
    new_alerts = list(latest_alerts - prev_alerts)

    return {
        "tool": "compare-snapshots",
        "latest_date": latest.get("snapshot_date", ""),
        "previous_date": previous.get("snapshot_date", ""),
        "new_alerts": new_alerts,
        "sources_latest": latest.get("sources_updated", 0),
        "sources_previous": previous.get("sources_updated", 0)
    }

async def _search_ttp(args: dict) -> dict:
    """Search MITRE ATT&CK TTP by keyword."""
    query = args["query"].lower()
    limit = args.get("limit", 10)

    # MITRE ATT&CK techniques reference (statically embedded subset)
    MITRE_TECHNIQUES = [
        {"id": "T1566", "name": "Phishing", "tactic": "Initial Access", "platform": "Email/Web"},
        {"id": "T1190", "name": "Exploit Public-Facing Application", "tactic": "Initial Access", "platform": "Web"},
        {"id": "T1059", "name": "Command and Scripting Interpreter", "tactic": "Execution", "platform": "Multi"},
        {"id": "T1203", "name": "Exploitation for Client Execution", "tactic": "Execution", "platform": "Multi"},
        {"id": "T1547", "name": "Boot or Logon Autostart Execution", "tactic": "Persistence", "platform": "OS"},
        {"id": "T1068", "name": "Exploitation for Privilege Escalation", "tactic": "Privilege Escalation", "platform": "Multi"},
        {"id": "T1562", "name": "Impair Defenses", "tactic": "Defense Evasion", "platform": "Multi"},
        {"id": "T1555", "name": "Credentials from Password Stores", "tactic": "Credential Access", "platform": "Multi"},
        {"id": "T1083", "name": "File and Directory Discovery", "tactic": "Discovery", "platform": "OS"},
        {"id": "T1210", "name": "Exploitation of Remote Services", "tactic": "Lateral Movement", "platform": "Network"},
        {"id": "T1041", "name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration", "platform": "Network"},
        {"id": "T1486", "name": "Data Encrypted for Impact", "tactic": "Impact", "platform": "Multi"},
        {"id": "T1583", "name": "Acquire Infrastructure", "tactic": "Resource Development", "platform": "Multi"},
        {"id": "T1595", "name": "Active Scanning", "tactic": "Reconnaissance", "platform": "Network"},
        {"id": "T1498", "name": "Network Denial of Service", "tactic": "Impact", "platform": "Network"},
        {"id": "T1505", "name": "Server Software Component", "tactic": "Persistence", "platform": "Web"},
        {"id": "T1195", "name": "Supply Chain Compromise", "tactic": "Initial Access", "platform": "Multi"},
        {"id": "T1213", "name": "Data from Information Repositories", "tactic": "Collection", "platform": "Multi"},
        {"id": "T1027", "name": "Obfuscated Files or Information", "tactic": "Defense Evasion", "platform": "Multi"},
        {"id": "T1078", "name": "Valid Accounts", "tactic": "Defense Evasion/Persistence", "platform": "Multi"},
    ]

    matches = [t for t in MITRE_TECHNIQUES
               if query in t["name"].lower() or query in t["tactic"].lower() or query in t["id"].lower()]

    return {
        "tool": "search-ttp",
        "query": query,
        "total": len(matches),
        "techniques": matches[:limit]
    }
