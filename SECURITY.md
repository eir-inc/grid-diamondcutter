# Security policy

## Reporting a vulnerability

If you believe you have found a security issue in `diamondcutter-grid` — whether it affects the substrate model, the cycle-walk measurement protocol, the route-adaptive search, the cryptographic signing helpers, or any documentation that could mislead a downstream user — please report it to Eir's security team rather than opening a public GitHub issue.

Email: **security@eir.inc**

For sensitive disclosures, you may encrypt with the team's PGP key, fingerprint published at `https://eir.inc/.well-known/pgp.asc` (placeholder pending public-key infrastructure).

## What to include

A useful disclosure typically includes:

- Affected file(s) and line number(s), or a minimal reproducing script.
- A description of the impact (what an attacker could do, who is affected).
- Any suggested mitigation or patch, if you have one.
- Your preferred name for attribution in the eventual fix advisory, or a request for anonymity.

We accept reports from anyone, including anonymous tips. Bug bounty terms are not currently published; we will coordinate with serious reporters in good faith.

## Response timeline

We commit to:

- **Acknowledgement of receipt within 3 business days.**
- An initial triage and severity assessment within 7 days.
- A fix or mitigation plan within 30 days for high-severity issues affecting the reference implementation, with status updates if more time is needed for cross-domain validation.
- A public advisory after the fix is shipped, crediting the reporter unless they have requested anonymity.

If we need more than 30 days for a structural fix, we will communicate clearly and provide interim mitigation guidance.

## Scope

In scope:

- Vulnerabilities in any code in this repository.
- Vulnerabilities in published artifacts (`reproducibility_hashes.json`, signed measurement summaries, etc.).
- Documentation issues that could mislead a downstream user into deploying a vulnerable configuration.

Out of scope:

- The proprietary `eirmath` package — please report `eirmath` issues directly via Eir's commercial support channel.
- Third-party dependencies (`numpy` and optional `pypower` / `pandapower`). Report those to their respective projects; we will track upstream fixes.

## Coordinated disclosure

We follow standard coordinated-disclosure practice: a 90-day private window for fixes, followed by public advisory + patched release. We will negotiate the window with the reporter for issues that require coordinated patching across multiple parties (utilities, grid operators, regulators) before public disclosure is safe.

## Production grid disclaimer

The reference implementation in this repository is an evaluation artifact, not production grid control software. Any security analysis should account for the boundary: a vulnerability in the OSS sim does not, by itself, affect a customer's production grid. We treat reports against production-coupled use cases (e.g. a utility that has imported this code into a control room without modification) as the same severity as a reference-implementation issue and respond accordingly.

## Cryptographic primitives

The reference implementation uses Python's standard library `hmac` over canonical JSON for measurement-artifact signing. We have not designed our own cryptography. If you find a misuse of standard primitives (HMAC key derivation, JSON canonicalization edge cases, signature verification flow), please report — that is in scope.

The proprietary `eirmath` package handles customer-facing signing and lineage submission; its security policy is published separately with the package.
