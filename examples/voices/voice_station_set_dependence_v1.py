"""
voice_station_set_dependence_v1.py — registry voice.

Tests whether the cycle_residual depends on the order of stations in the
rotating-load circle, given a fixed multiset of load-profile stations. If the
methodology is order-independent at the multiset level, the cycle_residual
should be approximately the same across all permutations of the same station
multiset. If it depends on order, that fact is a structural finding the
methodology must account for in interpretation.

Authored under PREREGISTRATION.md §3.1.
"""
from __future__ import annotations
import json
import hashlib
import itertools
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np


VOICE_NAME = "station_set_dependence_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "8node_dc_grid",
    "named_residual": (
        "order-dependence of cycle_residual under permutations of a fixed station "
        "multiset. The methodology is interpretable as multiset-invariant only if "
        "the unsigned cycle_residual varies by less than 20% relative to its mean "
        "across all 4! = 24 permutations of a 4-station closure (with a fixed "
        "return-to-start convention)."
    ),
    "baseline_station_set_unsigned_cycle_residual": 0.0465,
    "predicted_max_relative_spread": 0.20,
    "n_permutations_tested": 24,
}

KILL_CONDITION = {
    "metric": "max_unsigned_relative_spread_across_permutations",
    "rule": (
        "fail if (max_residual - min_residual) / mean_residual > 0.20 across "
        "the 24 permutations of the 4 distinct profile-transitions in the "
        "canonical station set"
    ),
    "rationale": (
        "Cross-region interpretation of cycle_residual assumes the measurement "
        "is order-independent at the multiset level: two regions with the same "
        "set of load-profile transitions, in different orders, should report "
        "comparable cycle_residuals. If order matters more than 20% relative, "
        "any cross-region comparison must control for ordering, and the "
        "methodology's interpretation tightens."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_station_set_dependence_v1.py",
    "source_file": "examples/voices/voice_station_set_dependence_v1.py",
    "input_parameters": {
        "random_seed": 42,
        "profile_transitions": [
            ("peak", "off_peak"),
            ("off_peak", "mixed"),
            ("mixed", "spike"),
            ("spike", "peak"),
        ],
        "mix": 0.3,
        "close_at": "first_transition",
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


def cycle_residual_for_ordering(transitions: list[tuple[str, str]], mix: float) -> float:
    from power_grid_sim import power_flow

    fingerprints = []
    for profile_a, profile_b in transitions:
        flows = power_flow(profile_a, profile_b, mix)
        bins = np.histogram(flows, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
        fingerprints.append((*[int(b) for b in bins], round(float(flows.max()), 3)))
    # close back to first station
    first_flows = power_flow(transitions[0][0], transitions[0][1], mix)
    first_bins = np.histogram(first_flows, bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.5])[0]
    first_fp = (*[int(b) for b in first_bins], round(float(first_flows.max()), 3))
    fingerprints.append(first_fp)

    step_distances = [
        float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fingerprints[i], fingerprints[i + 1]))))
        for i in range(len(fingerprints) - 1)
    ]
    home_step = float(np.sqrt(sum((a - b) ** 2 for a, b in zip(fingerprints[-1], fingerprints[0]))))
    mean_step = float(np.mean(step_distances)) if step_distances else 0.0
    return abs(home_step - mean_step)


def run_permutation_sweep() -> dict:
    transitions = RUN_PROTOCOL["input_parameters"]["profile_transitions"]
    mix = RUN_PROTOCOL["input_parameters"]["mix"]
    residuals_by_order = []
    for perm in itertools.permutations(transitions):
        r = cycle_residual_for_ordering(list(perm), mix)
        residuals_by_order.append({"order": [list(t) for t in perm], "unsigned_cycle_residual": r})
    residual_values = np.array([r["unsigned_cycle_residual"] for r in residuals_by_order])
    mean_r = float(residual_values.mean())
    spread = float((residual_values.max() - residual_values.min()) / max(mean_r, 1e-9))
    return {
        "n_permutations": len(residuals_by_order),
        "per_order": residuals_by_order,
        "min_residual": float(residual_values.min()),
        "max_residual": float(residual_values.max()),
        "mean_residual": mean_r,
        "std_residual": float(residual_values.std()),
        "relative_spread": spread,
    }


def compute_verdict(trial: dict) -> dict:
    threshold = PREDICTION["predicted_max_relative_spread"]
    spread = trial["relative_spread"]
    if spread <= threshold:
        verdict = "pass"
        rationale = (
            f"Relative spread across {trial['n_permutations']} permutations = {spread:.1%}, "
            f"at or below the predicted {threshold:.0%} threshold. cycle_residual is "
            f"approximately multiset-invariant at this scope; cross-region interpretation "
            f"that relies on multiset-invariance is supported by this measurement."
        )
    else:
        verdict = "fail"
        rationale = (
            f"Relative spread across {trial['n_permutations']} permutations = {spread:.1%}, "
            f"exceeds predicted {threshold:.0%} threshold. cycle_residual is order-dependent "
            f"at the multiset level. Voice enters the null-voice ledger per §3.4. Any "
            f"cross-region interpretation must control for ordering."
        )
    return {
        "verdict": verdict,
        "relative_spread_observed": spread,
        "min_residual": trial["min_residual"],
        "max_residual": trial["max_residual"],
        "mean_residual": trial["mean_residual"],
        "std_residual": trial["std_residual"],
        "threshold": threshold,
        "n_permutations": trial["n_permutations"],
        "rationale": rationale,
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def emit_sidecar(verdict: dict, output_path: str) -> str:
    unit = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
        "verdict": verdict,
    }
    canonical = json.dumps(
        {k: v for k, v in unit.items() if k != "verdict"},
        sort_keys=True,
        separators=(",", ":"),
    )
    unit["sidecar_sha256_pre_verdict"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with open(output_path, "w") as f:
        json.dump(unit, f, indent=2)
    return output_path


def main():
    print("=" * 72)
    print(f"voice unit: {VOICE_NAME}")
    print("=" * 72)
    print(f"prediction: relative spread ≤ {PREDICTION['predicted_max_relative_spread']:.0%} "
          f"across {PREDICTION['n_permutations_tested']} permutations")
    print("running sweep...")
    trial = run_permutation_sweep()
    verdict = compute_verdict(trial)
    print(f"  min residual:       {verdict['min_residual']:.4f}")
    print(f"  max residual:       {verdict['max_residual']:.4f}")
    print(f"  mean residual:      {verdict['mean_residual']:.4f}")
    print(f"  std residual:       {verdict['std_residual']:.4f}")
    print(f"  relative spread:    {verdict['relative_spread_observed']:.1%}")
    print(f"  threshold:          {verdict['threshold']:.0%}")
    print(f"  verdict:            {verdict['verdict'].upper()}")
    print(f"  {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"\nsidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
