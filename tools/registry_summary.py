"""
tools/registry_summary.py — aggregate all voice sidecars into a registry summary.

§3.4 of PREREGISTRATION.md commits the project to making the base rate (failures ÷
total voices committed) computable at any commit hash. This tool computes it
mechanically by reading every `*.sidecar.json` in `examples/voices/` and producing
a single-file summary that aggregates voices by verdict, kind, and outcome category.

Usage:

  python tools/registry_summary.py                                # print summary to stdout
  python tools/registry_summary.py --output REGISTRY_STATUS.md    # also write a markdown report
  python tools/registry_summary.py --json registry_summary.json   # also write a JSON artifact

The output is reproducible from any commit hash. Read it directly to see the current
state of the registry; cross-check the base rate against the §3.4 null-ledger
discipline at the time of any prior commit by checking out that commit + running
this tool.
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
VOICES_DIR = REPO_ROOT / "examples" / "voices"


def collect_sidecars() -> list[dict]:
    """Read every *.sidecar.json in examples/voices/ and return the loaded dicts."""
    sidecars = []
    if not VOICES_DIR.exists():
        return sidecars
    for path in sorted(VOICES_DIR.glob("*.sidecar.json")):
        try:
            with open(path) as f:
                sidecar = json.load(f)
            sidecar["_sidecar_path"] = str(path.relative_to(REPO_ROOT))
            sidecars.append(sidecar)
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARN: could not read {path}: {e}", file=sys.stderr)
    return sidecars


def _extract_verdict(s: dict) -> str:
    """Get the verdict label. Tolerates both {verdict: {verdict: 'pass'}} (the
    template/contract shape) and {verdict: 'pass'} (some early voices used a
    bare string at the top level)."""
    v = s.get("verdict")
    if isinstance(v, dict):
        return v.get("verdict", "unknown")
    if isinstance(v, str):
        return v
    return "unknown"


def _extract_rationale(s: dict) -> str:
    v = s.get("verdict")
    if isinstance(v, dict):
        return v.get("rationale", "")
    return ""


def summarize(sidecars: list[dict]) -> dict:
    """Aggregate sidecars into the registry summary §3.4 calls for."""
    total = len(sidecars)
    verdicts = Counter(_extract_verdict(s) for s in sidecars)
    kinds = Counter(s.get("prediction", {}).get("kind", "unknown") for s in sidecars)

    pass_count = verdicts.get("pass", 0)
    fail_count = verdicts.get("fail", 0)
    partial_count = verdicts.get("partial", 0)
    base_rate_failure = fail_count / total if total > 0 else 0.0
    base_rate_pass = pass_count / total if total > 0 else 0.0

    per_voice = []
    for s in sidecars:
        per_voice.append({
            "voice_name": s.get("voice_name", "<unknown>"),
            "kind": s.get("prediction", {}).get("kind", "unknown"),
            "verdict": _extract_verdict(s),
            "rationale": _extract_rationale(s),
            "sidecar_path": s.get("_sidecar_path", ""),
            "sha256_anchor": s.get("sidecar_sha256_pre_verdict", ""),
        })

    return {
        "registry_summary_generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_voices_committed": total,
        "verdict_counts": dict(verdicts),
        "kind_counts": dict(kinds),
        "base_rate_failure": base_rate_failure,
        "base_rate_pass": base_rate_pass,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "partial_count": partial_count,
        "voices": per_voice,
    }


def render_markdown(summary: dict) -> str:
    """Render the summary as a markdown report suitable for `REGISTRY_STATUS.md`."""
    lines = []
    lines.append("# Registry status — `grid-diamondcutter` voice ledger")
    lines.append("")
    lines.append(f"Generated: {summary['registry_summary_generated_at_utc']}")
    lines.append("")
    lines.append("This report aggregates the per-voice sidecars committed to the registry under")
    lines.append("the protocol in `PREREGISTRATION.md` §3. The base rate of failures is the")
    lines.append("project's audit-defense against forking-paths critique per §3.4: every framing")
    lines.append("that was committed and ran is visible here, with the failures named alongside")
    lines.append("the successes.")
    lines.append("")
    lines.append("## Aggregates")
    lines.append("")
    lines.append(f"- **Total voices committed**: {summary['total_voices_committed']}")
    lines.append(f"- **Pass**: {summary['pass_count']}")
    lines.append(f"- **Fail (null-voice ledger)**: {summary['fail_count']}")
    lines.append(f"- **Partial**: {summary['partial_count']}")
    lines.append(f"- **Base rate of failure**: {summary['base_rate_failure']:.1%}")
    lines.append("")
    lines.append("### By kind (§3.2)")
    lines.append("")
    for kind, count in summary["kind_counts"].items():
        lines.append(f"- {kind}: {count}")
    lines.append("")
    lines.append("## Per-voice")
    lines.append("")
    lines.append("| Voice | Kind | Verdict | Sidecar |")
    lines.append("|---|---|---|---|")
    for v in summary["voices"]:
        kind_short = v["kind"].replace("_within_substrate", "").replace("_cross_substrate", "")
        lines.append(f"| `{v['voice_name']}` | {kind_short} | **{v['verdict']}** | `{v['sidecar_path']}` |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("To regenerate: `python tools/registry_summary.py --output REGISTRY_STATUS.md`")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    p.add_argument("--output", default=None,
                   help="path for the markdown registry summary (default: stdout-only)")
    p.add_argument("--json", default=None,
                   help="path for the JSON summary artifact (default: not written)")
    args = p.parse_args()

    sidecars = collect_sidecars()
    summary = summarize(sidecars)

    md = render_markdown(summary)
    print(md)

    if args.output:
        with open(args.output, "w") as f:
            f.write(md)
        print(f"# markdown summary written: {args.output}", file=sys.stderr)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"# JSON summary written: {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()
