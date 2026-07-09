# 14 Industrial Security Intelligence Sources

## Contract / DeFi

### S1: DeFiHackLabs (SunWeb3Sec)
- **URL**: https://github.com/SunWeb3Sec/DeFiHackLabs
- **Content**: 250+ DeFi attack reproductions with Foundry PoC
- **Update API**: GitHub Commits API → watch for new `src/test/*Exp*.sol` files
- **Relevance**: Real-world attack patterns for SCSVS V13/D1-D8
- **Frequency**: On every attack discovery (weekly avg 2-5 new)

### S2: SCSVS (ComposableSecurity)
- **URL**: https://github.com/ComposableSecurity/SCSVS
- **Content**: Smart Contract Security Verification Standard v2
- **Update API**: GitHub Releases API → version bumps
- **Relevance**: Foundation of the 85-item attack matrix
- **Frequency**: Minor revisions quarterly, major yearly

### S3: SlowMist DeFi Threat Intelligence
- **URL**: https://www.slowmist.com/
- **Content**: Attack statistics, blockchain security reports
- **Update API**: Web scrape statistics.json
- **Relevance**: Chinese-language threat intelligence, APT tracking
- **Frequency**: Weekly updates

### S4: Immunefi Bug Bounty Platform
- **URL**: https://immunefi.com/bug-bounty/
- **Content**: Active bug bounties, top rewards, vulnerability trends
- **Update API**: Web scrape for bounty amounts and trends
- **Relevance**: Bug bounty amounts directly inform severity ratings
- **Frequency**: Real-time

### S5: Rekt News
- **URL**: https://rekt.news/
- **Content**: Deep-dive hack analysis articles
- **Update API**: RSS / HTML scrape for article titles
- **Relevance**: Detailed post-mortems of major exploits
- **Frequency**: Weekly

### S6: Solodit
- **URL**: https://solodit.xyz/
- **Content**: Aggregated security audit findings from top firms
- **Update API**: Requires web browsing (dynamic content)
- **Relevance**: Cross-firm vulnerability patterns
- **Frequency**: Continuous

### S7: OpenZeppelin Security Advisories
- **URL**: https://github.com/OpenZeppelin/openzeppelin-contracts/security/advisories
- **Content**: Official vulnerability disclosures for OZ contracts
- **Update API**: GitHub Security Advisories API
- **Relevance**: Direct impact on contracts using OZ libraries
- **Frequency**: As needed

---

## Centralized / Web Application

### S8: OWASP Top 10
- **URL**: https://owasp.org/www-project-top-ten/
- **Content**: Web application security risk standard
- **Update API**: GitHub Releases (https://github.com/OWASP/Top10)
- **Relevance**: Primary framework for centralized security scanning
- **Frequency**: Major update every 3-4 years

### S9: NVD CVE Database (NIST)
- **URL**: https://nvd.nist.gov/developers/vulnerabilities
- **Content**: National Vulnerability Database — all public CVEs
- **Update API**: NVD API 2.0 (JSON, 50 req/30s rolling)
- **Relevance**: CVE-to-tool mapping for SCA (trivy/npm audit)
- **Frequency**: ~2,000 new CVEs/month

### S10: Exploit-DB (Offensive Security)
- **URL**: https://www.exploit-db.com/
- **Content**: Public exploit code repository
- **Update API**: GitHub mirror (offensive-security/exploitdb)
- **Relevance**: Working PoC for pentesting
- **Frequency**: Daily

### S11: CISA Known Exploited Vulnerabilities (KEV)
- **URL**: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **Content**: Vulnerabilities actively exploited in the wild
- **Update API**: Direct JSON feed (cisa.gov/feeds/known_exploited_vulnerabilities.json)
- **Relevance**: Must-patch list for infrastructure scanning
- **Frequency**: Updated as new exploits emerge

### S12: Nuclei Templates (ProjectDiscovery)
- **URL**: https://github.com/projectdiscovery/nuclei-templates
- **Content**: 8,500+ vulnerability detection templates
- **Update API**: GitHub Commits API (filter http/cves path)
- **Relevance**: Direct feed into DAST scanning pipeline
- **Frequency**: 10-50 new templates/week

### S13: HackerOne Hacktivity
- **URL**: https://hackerone.com/hacktivity
- **Content**: Publicly disclosed bug bounty reports
- **Update API**: HackerOne Hacktivity API (JSON)
- **Relevance**: Real-world exploitation patterns
- **Frequency**: Continuous

### S14: MITRE ATT&CK Framework
- **URL**: https://github.com/mitre/cti
- **Content**: Adversary Tactics, Techniques, and Procedures (TTP)
- **Update API**: GitHub Releases API + STIX bundles
- **Relevance**: Threat modeling framework
- **Frequency**: Major version every 6 months, technique updates monthly
