# SCSVS v2 Attack Matrix — Complete Checklist

> Ref: https://github.com/ComposableSecurity/SCSVS
> 85 items aligned with Security Agent v9.0

## V1 — Architecture & Threat Modeling (15 items)
1.1 Complete architecture diagram with all components + data flows + trust boundaries
1.2 Attack surface identified (all external/public functions + ETH-receiving fallbacks)
1.3 Threat model covers all actors: users, admins, miners, MEV searchers, cross-chain relays
1.4 Complete delegatecall chain documented (all proxy/upgrade paths)
1.5 External dependencies (oracles, bridges, third-party) assessed for trust
1.6 Emergency pause mechanism is complete (pause/unpause + access control)
1.7 Upgrade mechanism is secure (proxy admin + timelock + multisig)
1.8 Cross-chain messages are validated (relay verification + replay protection)
1.9 Off-chain components (keeper, relayer, indexer) are secured
1.10 Frontend security considered (CSP, HTTPS, input validation)
1.11 Inter-contract trust relationships explicitly defined
1.12 Data flow is traceable (event completeness + on-chain auditability)
1.13 No unused contracts/functions (selfdestruct, deprecated code)
1.14 No unnecessary approve/allowance (principle of least privilege)
1.15 Regulatory risks considered (OFAC, sanctions, Tornado Cash interactions)

## V2 — Access Control (13 items)
2.1 Correct access control pattern used (Ownable, AccessControl, RBAC)
2.2 onlyOwner/onlyRole covers all sensitive functions
2.3 No privilege escalation path (grantRole only by admin)
2.4 No backdoor/super-admin (no single point of bypass)
2.5 msg.sender checked, not tx.origin
2.6 Signature verification is complete (EIP-712: nonce, chainId, verifier)
2.7 Multisig/DAO governance is secure (timelock, proposal thresholds)
2.8 Initializer function has protection (initializer modifier)
2.9 No unprotected selfdestruct (owner or multisig only)
2.10 Flashloan callback has access control (only expected caller)
2.11 fallback/receive has access control
2.12 No unverified external calls
2.13 Proxy admin is secure (timelock + multisig)

## V5 — Arithmetic (6 items)
5.1 Solidity ≥ 0.8.x (built-in overflow checks)
5.2 unchecked blocks have safety justification comments
5.3 Precision calculations handle decimals (multiply before divide)
5.4 Division-by-zero protection
5.5 Rounding direction clearly defined (favor protocol or user)
5.6 No type-cast overflow (downcast from uint256→uint128 checked)

## V8 — Business Logic (11 items)
8.1 Funds cannot be permanently locked (all paths have withdraw)
8.2 Money flow is complete and traceable (in→out path clear)
8.3 No unexpected fund mint/burn (total conservation)
8.4 No price manipulation possible (TWAP, multi-oracle, slippage)
8.5 No front-running possible (commit-reveal, slippage, deadline)
8.6 No sandwich attack surface (slippage protection)
8.7 No race condition in open/close position (clear state machine)
8.8 Liquidation logic has no dead-loops/incompleteness
8.9 Fee calculation is accurate (no precision loss)
8.10 Limit/stop order execution is guaranteed (keeper incentives)
8.11 TP/SL is atomic (openPositionWithAutoOrders in one tx)

## V9 — DOS (8 items)
9.1 No unbounded loops (arrays capped or paginated)
9.2 External call failure doesn't cause revert (try/catch or pull-over-push)
9.3 No dependency on external contracts not reverting
9.4 Gas limit won't cause partial execution (loops have caps)
9.5 Rate limiting/cool-down on critical operations
9.6 Storage can't be filled causing OOG (no infinite growth)
9.7 No block stuffing attack surface
9.8 No dust attack surface (minimum trade amount)

## V10 — Token (6 items)
10.1 No ERC20 approve race condition (increaseAllowance/decreaseAllowance)
10.2 Transfer return value checked (safeTransfer)
10.3 Fee-on-transfer token compatibility (check actual received amount)
10.4 Rebase token compatibility (balance change handling)
10.5 Blacklist token compatibility (transfer may fail)
10.6 No permit signature replay (nonce + deadline)

## V13 — Known Attacks (6 categories, 20+ sub-items)
13.1 Reentrancy: CEI pattern, ReentrancyGuard, cross-function, cross-contract, read-only reentrancy
13.2 Integer Overflow: Solidity 0.8+, SafeMath, unchecked block review
13.3 Signature Replay: EIP-712 nonce+chainId+deadline, ERC-1271, permit replay
13.4 Flash Loan: Oracle manipulation, transient balance dependency, TWAP protection
13.5 Oracle Manipulation: Decentralization level, staleness check, multi-source aggregation
13.6 MEV: Front-running, sandwich, slippage protection

## V14 — DeFi Specific (12 items)
14.1 AMM constant product K-value protected (K doesn't decrease post-swap)
14.2 LP add/remove protected (single-sided manipulation prevention)
14.3 Margin calculation uses oracle price (not spot price)
14.4 Liquidation mechanism has protection (no excessive arbitrage)
14.5 Funding rate is reasonable (no extreme values)
14.6 Insurance fund adequacy (covers extreme markets)
14.7 Leverage multiplier has cap
14.8 Impermanent loss protection (LP risk disclosed)
14.9 Yield aggregation is correct (compound calculation)
14.10 Flashloan callback has reentrancy protection (CEI + ReentrancyGuard)
14.11 Lending LTV ≤ 80%
14.12 ERC-4626 inflation attack protection (virtual liquidity + minimum shares)

## D1-D8 — DeFiHackLabs 2023-2025 New Attack Patterns (8 items)
D1 Cross-chain Bridge: message validation, relay security, replay protection
D2 ERC-4626 Inflation: initial share manipulation, donate attack
D3 Read-Only Reentrancy: view function data stale within same tx
D4 ERC-2771 Metatx Fraud: Forwarder verification, signer validation
D5 Permit2 Front-run: nonce management, deadline enforcement
D6 Uniswap V4 Hook: hook permissions, before/after swap security
D7 EIP-712 Typehash Collision: complete typeHash, dynamic type handling
D8 MEV Boost Relay Censorship: transaction ordering dependencies, anti-censorship

## Severity Rating (Immunefi Aligned)
| Level | Definition | Bounty Reference | Response |
|-------|-----------|------------------|----------|
| 🔴 Critical | Direct fund loss ≥$100K or complete permission bypass | $50K-$10M+ | Immediate |
| 🟠 High | Single-point breach → large loss | $5K-$50K | 24h |
| 🟡 Medium | Specific condition combination required | $1K-$5K | This sprint |
| 🟢 Low | Best practice improvement, no direct attack path | Informational | Tech debt |
| 🔵 Info | Informational only | — | Ignore |
