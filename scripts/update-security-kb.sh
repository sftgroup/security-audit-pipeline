#!/bin/bash
# ============================================================================
# Security Knowledge Base Auto-Update Script
# ============================================================================
# 从14个工业级安全源拉取最新威胁情报，生成结构化知识库快照
# 供 security / security-check / security-check-centralized Agent 使用
#
# 用法:
#   ./update-security-kb.sh              # 增量更新
#   ./update-security-kb.sh --force      # 强制全量更新
#   ./update-security-kb.sh --dry-run    # 仅检查，不写入
# ============================================================================

set -euo pipefail

KB_DIR="${KB_DIR:-${HOME}/.openclaw/security-kb}"
CACHE_DIR="${KB_DIR}/cache"
DATE=$(date +%Y%m%d_%H%M)
FORCE=false
DRY_RUN=false

for arg in "$@"; do
    case $arg in
        --force) FORCE=true ;;
        --dry-run) DRY_RUN=true ;;
    esac
done

mkdir -p "$KB_DIR" "$CACHE_DIR"

log() { echo "[$(date +%H:%M:%S)] $*"; }
warn() { echo "[$(date +%H:%M:%S)] ⚠️  $*" >&2; }

# ============================================================================
# 合约/DeFi 安全源 (7 sources)
# ============================================================================

# S1: DeFiHackLabs — 最新攻击事件 + PoC
fetch_defihacklabs() {
    log "S1: DeFiHackLabs (SunWeb3Sec)..."
    local out="$KB_DIR/defihacklabs-latest.json"
    local cache="$CACHE_DIR/defihacklabs-etag.txt"

    # 获取最近 commit
    local commits
    commits=$(curl -sf -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/SunWeb3Sec/DeFiHackLabs/commits?per_page=10&path=src/test" 2>/dev/null || echo "[]")

    # 提取新的攻击事件文件名
    echo "$commits" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    events = []
    for c in data:
        msg = c.get('commit',{}).get('message','')
        date = c.get('commit',{}).get('committer',{}).get('date','')[:10]
        sha = c.get('sha','')[:7]
        # 提取攻击合约名称
        if 'exp' in msg.lower() or 'hack' in msg.lower() or 'attack' in msg.lower():
            events.append({'date':date,'sha':sha,'message':msg[:120]})
    print(json.dumps({'source':'DeFiHackLabs','updated':'$DATE','events':events},indent=2))
except Exception as e:
    print(json.dumps({'source':'DeFiHackLabs','error':str(e)}))
" > "$out" 2>/dev/null || echo '{"source":"DeFiHackLabs","error":"fetch failed"}' > "$out"
}

# S2: SCSVS — 标准版本检查
fetch_scsvs() {
    log "S2: SCSVS (ComposableSecurity)..."
    local out="$KB_DIR/scsvs-version.json"

    curl -sf -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/ComposableSecurity/SCSVS/releases/latest" 2>/dev/null | python3 -c "
import json, sys
try:
    r = json.load(sys.stdin)
    v = {'source':'SCSVS','tag':r.get('tag_name',''),'date':r.get('published_at','')[:10],
         'url':r.get('html_url',''),'body':r.get('body','')[:500]}
    print(json.dumps(v,indent=2))
except:
    print(json.dumps({'source':'SCSVS','error':'fetch failed'}))
" > "$out" 2>/dev/null || echo '{"source":"SCSVS","error":"fetch failed"}' > "$out"
}

# S3: DeFi Threat Matrix (SlowMist)
fetch_slowmist() {
    log "S3: SlowMist DeFi Threat Matrix..."
    local out="$KB_DIR/slowmist-threats.json"

    # SlowMist public threat intelligence
    curl -sf "https://www.slowmist.com/statistics.json" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    # Extract recent attack stats
    print(json.dumps({'source':'SlowMist','updated':'$DATE','data_keys':list(data.keys())[:20]},indent=2))
except Exception as e:
    print(json.dumps({'source':'SlowMist','error':str(e)}))
" > "$out" 2>/dev/null || echo '{"source":"SlowMist","error":"fetch failed"}' > "$out"
}

# S4: Immunefi — Bug Bounty 趋势
fetch_immunefi() {
    log "S4: Immunefi Bug Bounty..."
    local out="$KB_DIR/immunefi-trends.json"

    # Fetch immunefi bounties page for top rewards
    curl -sf "https://immunefi.com/bug-bounty/" 2>/dev/null | python3 -c "
import re, sys, json
try:
    text = sys.stdin.read()
    # Extract dollar amounts
    amounts = re.findall(r'\\$[\\d,]+[KMB]?', text)
    unique = list(set(amounts))[:15]
    print(json.dumps({'source':'Immunefi','updated':'$DATE','top_bounties':unique},indent=2))
except Exception as e:
    print(json.dumps({'source':'Immunefi','error':str(e)}))
" > "$out" 2>/dev/null || echo '{"source":"Immunefi","error":"fetch failed"}' > "$out"
}

# S5: Rekt News — 最新黑客事件
fetch_rekt() {
    log "S5: Rekt News..."
    local out="$KB_DIR/rekt-latest.json"

    curl -sf "https://rekt.news/" 2>/dev/null | python3 -c "
import re, sys, json
try:
    text = sys.stdin.read()
    # Extract article titles
    titles = re.findall(r'<h[23][^>]*>([^<]+)</h[23]>', text)
    # Filter for hack-related
    hacks = [t.strip() for t in titles if any(k in t.lower() for k in ['hack','exploit','attack','drain','breach','$'])]
    print(json.dumps({'source':'RektNews','updated':'$DATE','latest_hacks':hacks[:10]},indent=2))
except Exception as e:
    print(json.dumps({'source':'RektNews','error':str(e)}))
" > "$out" 2>/dev/null || echo '{"source":"RektNews","error":"fetch failed"}' > "$out"
}

# S6: Solodit — 审计报告聚合
fetch_solodit() {
    log "S6: Solodit..."
    local out="$KB_DIR/solodit-latest.json"
    echo "{\"source\":\"Solodit\",\"updated\":\"$DATE\",\"note\":\"Requires web browsing — check https://solodit.xyz/ for latest audit findings\"}" > "$out"
}

# S7: OpenZeppelin — 安全审计公告
fetch_openzeppelin() {
    log "S7: OpenZeppelin Security Audits..."
    local out="$KB_DIR/openzeppelin-audits.json"

    curl -sf -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/OpenZeppelin/openzeppelin-contracts/security-advisories?per_page=5" 2>/dev/null | python3 -c "
import json, sys
try:
    advisories = json.load(sys.stdin)
    items = []
    for a in advisories[:5]:
        items.append({'id':a.get('ghsa_id',''),'severity':a.get('severity',''),
                       'summary':a.get('summary','')[:150],'date':a.get('published_at','')[:10]})
    print(json.dumps({'source':'OpenZeppelin','updated':'$DATE','advisories':items},indent=2))
except Exception as e:
    print(json.dumps({'source':'OpenZeppelin','error':str(e)}))
" > "$out" 2>/dev/null || echo '{"source":"OpenZeppelin","error":"fetch failed"}' > "$out"
}

# ============================================================================
# 中心化/Web 安全源 (7 sources)
# ============================================================================

# S8: OWASP Top 10
fetch_owasp() {
    log "S8: OWASP Top 10..."
    local out="$KB_DIR/owasp-version.json"

    curl -sf -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/OWASP/Top10/releases/latest" 2>/dev/null | python3 -c "
import json, sys
try:
    r = json.load(sys.stdin)
    print(json.dumps({'source':'OWASP','tag':r.get('tag_name',''),'date':r.get('published_at','')[:10]},indent=2))
except:
    print(json.dumps({'source':'OWASP','note':'Current: OWASP Top 10 (2021). Check https://owasp.org/Top10/'}))
" > "$out" 2>/dev/null || echo '{"source":"OWASP","error":"fetch failed"}' > "$out"
}

# S9: NVD CVE Feed (via NVD API 2.0)
fetch_nvd() {
    log "S9: NVD CVE Feed..."
    local out="$KB_DIR/nvd-cve-latest.json"

    # Fetch CVEs from last 7 days, filtered by critical/high
    local pubEndDate pubStartDate
    pubEndDate=$(date -u +%Y-%m-%dT%H:%M:%S.000)
    if [[ "$(uname -s)" == "Darwin" ]]; then
        pubStartDate=$(date -u -v-7d +%Y-%m-%dT%H:%M:%S.000)
    else
        pubStartDate=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S.000)
    fi

    curl -sf "https://services.nvd.nist.gov/rest/json/cves/2.0?pubStartDate=${pubStartDate}&pubEndDate=${pubEndDate}&severity=CRITICAL&resultsPerPage=20" \
        2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    cves = []
    for vuln in data.get('vulnerabilities',[]):
        cve = vuln.get('cve',{})
        cves.append({
            'id': cve.get('id',''),
            'description': cve.get('descriptions',[{}])[0].get('value','')[:200],
            'published': cve.get('published','')[:10]
        })
    print(json.dumps({'source':'NVD','updated':'$DATE','critical_cves_7d':len(cves),'cves':cves[:10]},indent=2))
except Exception as e:
    print(json.dumps({'source':'NVD','error':str(e)}))
" > "$out" 2>/dev/null || echo '{"source":"NVD","error":"fetch failed"}' > "$out"
}

# S10: Exploit-DB (via offsec GitHub mirror)
fetch_exploitdb() {
    log "S10: Exploit-DB..."
    local out="$KB_DIR/exploitdb-latest.json"

    curl -sf -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/offensive-security/exploitdb/commits?per_page=5" 2>/dev/null | python3 -c "
import json, sys
try:
    commits = json.load(sys.stdin)
    items = []
    for c in commits[:5]:
        items.append({'date':c.get('commit',{}).get('committer',{}).get('date','')[:10],
                       'message':c.get('commit',{}).get('message','')[:120]})
    print(json.dumps({'source':'ExploitDB','updated':'$DATE','latest_commits':items},indent=2))
except:
    print(json.dumps({'source':'ExploitDB','error':'fetch failed'}))
" > "$out" 2>/dev/null || echo '{"source":"ExploitDB","error":"fetch failed"}' > "$out"
}

# S11: CISA Known Exploited Vulnerabilities
fetch_cisa_kev() {
    log "S11: CISA KEV..."
    local out="$KB_DIR/cisa-kev-latest.json"

    curl -sf "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    vulns = data.get('vulnerabilities',[])
    # Most recent 10
    recent = sorted(vulns, key=lambda x: x.get('dateAdded',''), reverse=True)[:10]
    items = [{'cve':v.get('cveID',''),'vendor':v.get('vendorProject',''),
              'product':v.get('product',''),'date':v.get('dateAdded',''),
              'desc':v.get('shortDescription','')[:100]} for v in recent]
    print(json.dumps({'source':'CISA-KEV','updated':'$DATE','total_kev':len(vulns),'recent':items},indent=2))
except Exception as e:
    print(json.dumps({'source':'CISA-KEV','error':str(e)}))
" > "$out" 2>/dev/null || echo '{"source":"CISA-KEV","error":"fetch failed"}' > "$out"
}

# S12: Nuclei Templates (新增模板检测)
fetch_nuclei_templates() {
    log "S12: Nuclei Templates..."
    local out="$KB_DIR/nuclei-templates-update.json"

    curl -sf -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/projectdiscovery/nuclei-templates/commits?per_page=10&path=http/cves" 2>/dev/null | python3 -c "
import json, sys
try:
    commits = json.load(sys.stdin)
    items = []
    for c in commits[:10]:
        items.append({'date':c.get('commit',{}).get('committer',{}).get('date','')[:10],
                       'message':c.get('commit',{}).get('message','')[:120]})
    print(json.dumps({'source':'NucleiTemplates','updated':'$DATE','latest_cve_templates':items},indent=2))
except:
    print(json.dumps({'source':'NucleiTemplates','error':'fetch failed'}))
" > "$out" 2>/dev/null || echo '{"source":"NucleiTemplates","error":"fetch failed"}' > "$out"
}

# S13: HackerOne Hacktivity
fetch_hackerone() {
    log "S13: HackerOne Hacktivity..."
    local out="$KB_DIR/hackerone-latest.json"

    curl -sf "https://hackerone.com/hacktivity/overview.json" 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    reports = data.get('reports',[])[:10]
    items = [{'title':r.get('title','')[:100],'severity':r.get('severity_rating',''),
              'bounty':r.get('total_awarded_amount','')} for r in reports if r.get('public')]
    print(json.dumps({'source':'HackerOne','updated':'$DATE','recent_public':items},indent=2))
except Exception as e:
    print(json.dumps({'source':'HackerOne','error':str(e)}))
" > "$out" 2>/dev/null || echo '{"source":"HackerOne","error":"fetch failed"}' > "$out"
}

# S14: MITRE ATT&CK
fetch_mitre_attack() {
    log "S14: MITRE ATT&CK..."
    local out="$KB_DIR/mitre-attack-version.json"

    curl -sf -H "Accept: application/vnd.github+json" \
        "https://api.github.com/repos/mitre/cti/releases/latest" 2>/dev/null | python3 -c "
import json, sys
try:
    r = json.load(sys.stdin)
    print(json.dumps({'source':'MITRE-ATT&CK','tag':r.get('tag_name',''),'date':r.get('published_at','')[:10]},indent=2))
except:
    print(json.dumps({'source':'MITRE-ATT&CK','error':'fetch failed'}))
" > "$out" 2>/dev/null || echo '{"source":"MITRE-ATT&CK","error":"fetch failed"}' > "$out"
}

# ============================================================================
# 汇总 + 快照生成
# ============================================================================
generate_snapshot() {
    log "Generating composite snapshot..."
    local snapshot="$KB_DIR/attack-matrix-${DATE}.md"
    local json_snapshot="$KB_DIR/attack-matrix-${DATE}.json"

    # Generate JSON summary for Agent consumption
    python3 -c "
import json, os, glob

kb = '$KB_DIR'
sources = {}
for f in sorted(glob.glob(f'{kb}/*-latest*.json')):
    try:
        with open(f) as fh:
            data = json.load(fh)
            src = data.pop('source', os.path.basename(f))
            sources[src] = data
    except: pass

summary = {
    'snapshot_date': '$DATE',
    'sources_updated': len(sources),
    'sources': sources,
    'priority_alerts': []
}

# Add priority alerts
for src_name, data in sources.items():
    if 'critical_cves_7d' in data and data['critical_cves_7d'] > 0:
        summary['priority_alerts'].append(f'CISA/NVD: {data[\"critical_cves_7d\"]} new critical CVEs this week')
    if 'advisories' in data and data['advisories']:
        summary['priority_alerts'].append(f'OpenZeppelin: {len(data[\"advisories\"])} new security advisories')
    if 'total_kev' in data:
        summary['priority_alerts'].append(f'CISA KEV: {data[\"total_kev\"]} known exploited vulns total')

with open('$json_snapshot', 'w') as f:
    json.dump(summary, f, indent=2)

print(f'JSON snapshot: $json_snapshot')
print(f'Sources: {len(sources)} updated')
if summary['priority_alerts']:
    print('\\n🔴 Priority Alerts:')
    for alert in summary['priority_alerts']:
        print(f'  • {alert}')
"

    # Generate Markdown report
    cat > "$snapshot" << MDEOF
# 🛡️ Security Knowledge Base Snapshot
**Generated**: $(date '+%Y-%m-%d %H:%M:%S %Z')
**Sources**: 14 industrial-grade security intelligence feeds

---

## 📊 Source Status

| # | Source | Status |
|---|--------|--------|
| S1 | DeFiHackLabs | $(cat "$KB_DIR/defihacklabs-latest.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('✅' if 'events' in d else '❌')" 2>/dev/null || echo '❌') |
| S2 | SCSVS | $(cat "$KB_DIR/scsvs-version.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('✅' if 'tag' in d else '❌')" 2>/dev/null || echo '❌') |
| S3 | SlowMist | $(cat "$KB_DIR/slowmist-threats.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('⚠️' if 'error' not in d else '❌')" 2>/dev/null || echo '❌') |
| S4 | Immunefi | $(cat "$KB_DIR/immunefi-trends.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('⚠️' if 'error' not in d else '❌')" 2>/dev/null || echo '❌') |
| S5 | Rekt News | $(cat "$KB_DIR/rekt-latest.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('⚠️' if 'error' not in d else '❌')" 2>/dev/null || echo '❌') |
| S6 | Solodit | Manual |
| S7 | OpenZeppelin | $(cat "$KB_DIR/openzeppelin-audits.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('✅' if 'advisories' in d else '❌')" 2>/dev/null || echo '❌') |
| S8 | OWASP Top 10 | $(cat "$KB_DIR/owasp-version.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('⚠️' if 'error' not in d else '❌')" 2>/dev/null || echo '❌') |
| S9 | NVD CVE | $(cat "$KB_DIR/nvd-cve-latest.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('✅' if 'cves' in d else '❌')" 2>/dev/null || echo '❌') |
| S10 | Exploit-DB | $(cat "$KB_DIR/exploitdb-latest.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('⚠️' if 'error' not in d else '❌')" 2>/dev/null || echo '❌') |
| S11 | CISA KEV | $(cat "$KB_DIR/cisa-kev-latest.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('✅' if 'recent' in d else '❌')" 2>/dev/null || echo '❌') |
| S12 | Nuclei Templates | $(cat "$KB_DIR/nuclei-templates-update.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('⚠️' if 'error' not in d else '❌')" 2>/dev/null || echo '❌') |
| S13 | HackerOne | $(cat "$KB_DIR/hackerone-latest.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('⚠️' if 'error' not in d else '❌')" 2>/dev/null || echo '❌') |
| S14 | MITRE ATT&CK | $(cat "$KB_DIR/mitre-attack-version.json" 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('⚠️' if 'error' not in d else '❌')" 2>/dev/null || echo '❌') |

---

## 🔴 Latest DeFi Attacks (S1: DeFiHackLabs)
\`\`\`
$(cat "$KB_DIR/defihacklabs-latest.json" 2>/dev/null | python3 -c "
import json,sys;d=json.load(sys.stdin)
if 'events' in d:
    for e in d['events'][:5]: print(f'- [{e[\"date\"]}] {e[\"sha\"]} {e[\"message\"]}')
else: print(d.get('error','no data'))
")
\`\`\`

## 🟠 Critical CVEs This Week (S9: NVD + S11: CISA KEV)
\`\`\`
$(cat "$KB_DIR/nvd-cve-latest.json" 2>/dev/null | python3 -c "
import json,sys;d=json.load(sys.stdin)
if 'cves' in d:
    for c in d['cves'][:5]: print(f'- {c[\"id\"]}: {c[\"description\"][:120]}')
else: print(d.get('error','no data'))
")
\`\`\`

## 🟡 Latest Security Advisories (S7 + S8)
\`\`\`
$(cat "$KB_DIR/openzeppelin-audits.json" 2>/dev/null | python3 -c "
import json,sys;d=json.load(sys.stdin)
if 'advisories' in d:
    for a in d['advisories'][:5]: print(f'- [{a[\"severity\"]}] {a[\"id\"]}: {a[\"summary\"][:100]}')
else: print(d.get('error','no data'))
")
\`\`\`

---
**Next update**: $(date -d '+1 day' '+%Y-%m-%d' 2>/dev/null || date '+%Y-%m-%d')
**Snapshot path**: $KB_DIR/attack-matrix-${DATE}.json
MDEOF

    echo "  Markdown: $snapshot"
    echo "  JSON:     $json_snapshot"
}

# ============================================================================
# Main
# ============================================================================
main() {
    echo "=== 🛡️ Security Knowledge Base Update ==="
    echo "Date: $DATE | Dir: $KB_DIR"
    echo ""

    # Contract/DeFi sources
    fetch_defihacklabs
    fetch_scsvs
    fetch_slowmist
    fetch_immunefi
    fetch_rekt
    fetch_solodit
    fetch_openzeppelin

    # Centralized/Web sources
    fetch_owasp
    fetch_nvd
    fetch_exploitdb
    fetch_cisa_kev
    fetch_nuclei_templates
    fetch_hackerone
    fetch_mitre_attack

    # Generate composite
    generate_snapshot

    echo ""
    echo "=== ✅ Done ==="
    echo "Knowledge base: $KB_DIR"
    ls -la "$KB_DIR"/attack-matrix-"${DATE}".* 2>/dev/null
}

if $DRY_RUN; then
    echo "[DRY RUN] Would update knowledge base at $KB_DIR"
else
    main
fi
