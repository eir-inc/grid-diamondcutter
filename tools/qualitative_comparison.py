"""
tools/qualitative_comparison.py — §4.3 qualitative-trajectory comparison harness.

§4.3 commits the project to *qualitative-trajectory recovery* as the criterion
against documented historical events. This module is the mechanical
implementation of that criterion. It does NOT produce point estimates; it
produces a binary recover / no-recover output traceable to a documented
event-report fragment named in a fixture file.

Usage (CLI):

  python tools/qualitative_comparison.py \\
      --sidecar examples/voices/texas_feb_2021_uri_v1.sidecar.json \\
      --fixture tools/qualitative_fixtures/texas_feb_2021_uri_v1.fixture.json

Returns exit 0 if the fixture's expected-recovery rules are all satisfied by
the sidecar's verdict + observable-fields, 1 otherwise. Prints the audit
trail (which rule passed / failed against which fixture line) regardless.

The harness compares against fixtures only — never against private data or
the operating grid. Each fixture cites the public source by full citation
string in its `citation` field. Per §1, no harness pass constitutes a
real-grid claim; it constitutes a claim that the voice's run output is
consistent with the documented fragment named in the fixture.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any


# ===========================================================================
# Fixture schema
# ===========================================================================
# A fixture is a JSON file with the following required top-level fields:
#
# {
#   "voice_name": str,                       # must match sidecar's voice_name
#   "citation": str,                         # full public-source citation
#   "expected_recovery_rules": [             # list; ALL must pass for harness pass
#     {
#       "rule_id": str,                      # human-readable id
#       "rule_kind": str,                    # one of: verdict_equals,
#                                            #   slope_within_range, scenario_field_within_range
#       "spec": dict,                        # rule-kind-specific spec (see below)
#       "rationale": str,                    # short text — what this rule encodes
#       "citation_anchor": str               # the fixture's pointer into the
#                                            #   public source (e.g., "FERC-NERC
#                                            #   Final Report §3.2 page 87")
#     }
#   ]
# }
#
# rule_kind = "verdict_equals":
#   spec = {"value": "pass" | "fail" | "partial"}
#   passes if sidecar.verdict.verdict == spec.value
#
# rule_kind = "slope_within_range":
#   spec = {"low": float, "high": float}
#   passes if sidecar.verdict.observed_slope ∈ [low, high]
#
# rule_kind = "scenario_field_within_range":
#   spec = {"scenario_index": int, "field": str, "low": float, "high": float}
#   passes if scenario_summaries[scenario_index][field] ∈ [low, high]


# ===========================================================================
# Rule evaluators
# ===========================================================================

def _eval_verdict_equals(sidecar: dict, spec: dict) -> tuple[bool, str]:
    expected = spec["value"]
    observed = sidecar.get("verdict", {}).get("verdict")
    ok = observed == expected
    return ok, (
        f"expected verdict={expected!r}; observed={observed!r}; "
        f"{'PASS' if ok else 'FAIL'}"
    )


def _eval_slope_within_range(sidecar: dict, spec: dict) -> tuple[bool, str]:
    low, high = float(spec["low"]), float(spec["high"])
    slope = sidecar.get("verdict", {}).get("observed_slope")
    if slope is None:
        return False, f"FAIL: sidecar has no verdict.observed_slope (expected ∈ [{low}, {high}])"
    ok = low <= float(slope) <= high
    return ok, (
        f"observed_slope={slope:.4f}; required ∈ [{low}, {high}]; "
        f"{'PASS' if ok else 'FAIL'}"
    )


def _eval_scenario_field_within_range(sidecar: dict, spec: dict) -> tuple[bool, str]:
    idx = int(spec["scenario_index"])
    field = spec["field"]
    low, high = float(spec["low"]), float(spec["high"])
    summaries = sidecar.get("verdict", {}).get("scenario_summaries", [])
    if idx >= len(summaries):
        return False, (
            f"FAIL: scenario_index {idx} out of range (n_scenarios={len(summaries)})"
        )
    value = summaries[idx].get(field)
    if value is None:
        return False, f"FAIL: scenario[{idx}] has no field {field!r}"
    ok = low <= float(value) <= high
    return ok, (
        f"scenario[{idx}].{field}={value:.4f}; required ∈ [{low}, {high}]; "
        f"{'PASS' if ok else 'FAIL'}"
    )


_EVALUATORS = {
    "verdict_equals": _eval_verdict_equals,
    "slope_within_range": _eval_slope_within_range,
    "scenario_field_within_range": _eval_scenario_field_within_range,
}


# ===========================================================================
# Harness
# ===========================================================================

def compare(sidecar_path: Path, fixture_path: Path) -> dict:
    sidecar = json.loads(sidecar_path.read_text())
    fixture = json.loads(fixture_path.read_text())

    if fixture.get("voice_name") != sidecar.get("voice_name"):
        return {
            "harness_verdict": "fail",
            "sidecar_voice_name": sidecar.get("voice_name"),
            "fixture_voice_name": fixture.get("voice_name"),
            "rule_outcomes": [],
            "rationale": (
                "Fixture's voice_name does not match sidecar's voice_name. "
                "Pairing is invalid; refusing to compare. (Did you point the "
                "harness at the wrong fixture or sidecar?)"
            ),
        }

    rule_outcomes = []
    all_passed = True
    for rule in fixture.get("expected_recovery_rules", []):
        kind = rule.get("rule_kind")
        evaluator = _EVALUATORS.get(kind)
        if evaluator is None:
            rule_outcomes.append({
                "rule_id": rule.get("rule_id", "<unnamed>"),
                "rule_kind": kind,
                "passed": False,
                "audit": f"FAIL: unknown rule_kind {kind!r}",
                "citation_anchor": rule.get("citation_anchor"),
            })
            all_passed = False
            continue

        passed, audit = evaluator(sidecar, rule.get("spec", {}))
        rule_outcomes.append({
            "rule_id": rule.get("rule_id", "<unnamed>"),
            "rule_kind": kind,
            "passed": passed,
            "audit": audit,
            "rationale": rule.get("rationale", ""),
            "citation_anchor": rule.get("citation_anchor"),
        })
        if not passed:
            all_passed = False

    return {
        "harness_verdict": "recover" if all_passed else "no_recover",
        "sidecar_voice_name": sidecar.get("voice_name"),
        "fixture_voice_name": fixture.get("voice_name"),
        "fixture_citation": fixture.get("citation"),
        "rule_outcomes": rule_outcomes,
        "n_rules": len(rule_outcomes),
        "n_passed": sum(1 for r in rule_outcomes if r["passed"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1] if __doc__ else None)
    parser.add_argument("--sidecar", required=True, type=Path,
                        help="path to a voice sidecar JSON")
    parser.add_argument("--fixture", required=True, type=Path,
                        help="path to a §4.3 qualitative-recovery fixture JSON")
    parser.add_argument("--json", action="store_true",
                        help="print the comparison report as JSON instead of audit text")
    args = parser.parse_args()

    report = compare(args.sidecar, args.fixture)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 72)
        print(f"§4.3 qualitative-trajectory comparison harness")
        print("=" * 72)
        print(f"voice:    {report['sidecar_voice_name']}")
        print(f"fixture:  {args.fixture}")
        if report.get("fixture_citation"):
            print(f"citation: {report['fixture_citation']}")
        print(f"verdict:  {report['harness_verdict'].upper()}")
        print(f"rules:    {report.get('n_passed', 0)} / {report.get('n_rules', 0)} passed")
        print("-" * 72)
        for outcome in report.get("rule_outcomes", []):
            mark = "✓" if outcome["passed"] else "✗"
            print(f"  [{mark}] {outcome['rule_id']}:")
            print(f"        kind: {outcome['rule_kind']}")
            print(f"        anchor: {outcome.get('citation_anchor', '')}")
            print(f"        audit: {outcome['audit']}")

    return 0 if report["harness_verdict"] == "recover" else 1


if __name__ == "__main__":
    sys.exit(main())
