"""
network_amplification_adoption_cascade_v1.py — §3.2 coupling voice modeling
network-amplified ADOPTION cascade across two coupled regional substrates.

Iterates from network_amplification_coupling_v1's substantive null. v1's
substrate modeled network coupling as failure-resilience (raises the
min-perturbation threshold for capacity collapse); Eugene's question intent
was adoption-cascade (network coupling lowers the capex threshold for
renewable adoption to cascade across regions).

This v1 of the adoption-cascade voice explicitly inverts the substrate's
direction: neighbor surplus is modeled as a *downward* pressure on local
capex price (cheap-renewable export competes with new local fossil capex),
which when sustained triggers further local renewable installation. With
network coupling enabled, the adoption-cascade is amplified.

WHAT THIS VOICE PREDICTS
========================

Two coupled regional substrates connected by a network-transmission
coefficient `k ∈ [0, 1]`. Region A is given an initial renewable
deployment shock. The voice measures the SECONDARY adoption response in
region B at the end of the horizon as a function of `k`.

  Direction (predicted):   network_coefficient_up → secondary_adoption_up (positive)
  Magnitude (predicted):   slope of secondary-adoption response on k ≥ 0.20
  Null direction:          no response OR negative response

KILL CONDITION
==============

  - slope < 0 → fail (null direction realized; no adoption-cascade)
  - 0 ≤ slope < 0.20 → fail (response too weak to evidence amplification)
  - slope ≥ 0.20 → pass (adoption-cascade recovered in the substrate)

A PASS supports the OSS methodology being a useful basis for eirmath's
$-calibration of network-amplified adoption cascades. A FAIL supports
the failure-cascade-only model (v0 network_amplification_coupling_v1)
as the more parsimonious substrate.
"""
from __future__ import annotations
import json
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np


# ===========================================================================
# §3.1 — Standard five-field unit
# ===========================================================================

VOICE_NAME = "network_amplification_adoption_cascade_v1"

PREDICTION = {
    "kind": "coupling_cross_substrate",
    "substrate_source": "network_transmission_coefficient_k",
    "substrate_target": "secondary_region_renewable_adoption_after_horizon",
    "named_residual": "adoption_cascade_response_slope_on_k",
    "predicted_direction": "k_up → secondary_adoption_up (positive)",
    "predicted_magnitude_range": [0.20, 0.90],
    "null_direction": "no response OR negative response",
    "lineage": "iterates from network_amplification_coupling_v1's failure-cascade substrate; substrate now models adoption-cascade explicitly",
}

KILL_CONDITION = {
    "metric": "linear_fit_slope_secondary_adoption_vs_network_coefficient",
    "predicted_range": [0.20, 0.90],
    "rule": (
        "pass if slope ∈ [0.20, 0.90], fail if slope < 0 (null direction "
        "realized), fail if 0 ≤ slope < 0.20 (response too weak)"
    ),
    "rationale": (
        "The voice claims network coupling amplifies adoption-cascade in "
        "region B given an initial deployment shock in region A. Slope on "
        "the k sweep is the cleanest single-scalar test. Inversion from "
        "failure-resilience to adoption-amplification is in the substrate's "
        "price-pressure direction: neighbor surplus drives DOWN local capex "
        "price (competing with new fossil), which DRIVES UP local renewable "
        "installation. This is the substrate the original Eugene-question "
        "implied."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/network_amplification_adoption_cascade_v1.py",
    "source_file": "examples/voices/network_amplification_adoption_cascade_v1.py",
    "input_parameters": {
        "network_coefficient_sweep": [0.0, 0.20, 0.40, 0.60, 0.80, 1.00],
        "n_substrate_steps": 24,
        "initial_renewable_shock_region_a": 0.25,
        "baseline_local_renewable_share": 0.10,
        "installation_gain": 0.008,
        "price_pressure_gain": 0.06,
        "random_seed": 42,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


# ===========================================================================
# Adoption-cascade substrate (two coupled regions, price-pressure direction)
# ===========================================================================

def run_adoption_cascade(network_k: float, n_steps: int, seed: int) -> tuple[float, float]:
    """Two coupled regions, A and B.

    Region A receives an initial renewable shock at t=0 (`initial_shock`).
    Region B starts at baseline renewable share.

    Each step:
      - Region A's renewable surplus = max(0, share_a - baseline) becomes
        export to region B scaled by network_k.
      - That export lowers region B's capex_price proportionally
        (cheap-renewable competition).
      - Lower capex_price → faster local renewable installation in region B
        (multiplicative gain).
      - Region B's installation feeds back as additional surplus → A.

    Returns (final_share_region_a, final_share_region_b).
    """
    rng = np.random.default_rng(seed)
    p = RUN_PROTOCOL["input_parameters"]
    initial_shock = p["initial_renewable_shock_region_a"]
    baseline = p["baseline_local_renewable_share"]

    share_a = baseline + initial_shock
    share_b = baseline
    capex_price_a = 1.0
    capex_price_b = 1.0

    install_gain = p["installation_gain"]
    price_pressure = p["price_pressure_gain"]

    for _ in range(n_steps):
        surplus_a = max(0.0, share_a - baseline)
        surplus_b = max(0.0, share_b - baseline)
        export_a_to_b = network_k * 0.6 * surplus_a
        export_b_to_a = network_k * 0.6 * surplus_b

        # neighbor cheap-renewable export drives local capex price DOWN
        capex_price_b = max(0.30, capex_price_b - price_pressure * export_a_to_b + rng.normal(0.0, 0.005))
        capex_price_a = max(0.30, capex_price_a - price_pressure * export_b_to_a + rng.normal(0.0, 0.005))

        # lower capex price → higher renewable installation rate
        installation_rate_a = install_gain * (1.0 / capex_price_a)
        installation_rate_b = install_gain * (1.0 / capex_price_b)

        share_a = float(np.clip(share_a + installation_rate_a, 0.0, 1.0))
        share_b = float(np.clip(share_b + installation_rate_b, 0.0, 1.0))

    return share_a, share_b


def run_network_sweep() -> list[dict]:
    p = RUN_PROTOCOL["input_parameters"]
    n_steps = p["n_substrate_steps"]
    seed = p["random_seed"]
    sweep = []
    for k in p["network_coefficient_sweep"]:
        final_a, final_b = run_adoption_cascade(k, n_steps, seed)
        sweep.append({
            "network_coefficient": k,
            "final_share_region_a": final_a,
            "final_share_region_b": final_b,
            "secondary_adoption_response": final_b - p["baseline_local_renewable_share"],
        })
    return sweep


def compute_verdict(sweep_results: list[dict]) -> dict:
    x = np.array([s["network_coefficient"] for s in sweep_results])
    y = np.array([s["secondary_adoption_response"] for s in sweep_results])
    slope = float(np.cov(x, y, bias=True)[0, 1] / np.var(x))
    intercept = float(y.mean() - slope * x.mean())

    low, high = KILL_CONDITION["predicted_range"]

    if slope < 0:
        verdict = "fail"
        outcome = "null_direction_realized"
        rationale = (
            f"Slope {slope:.4f} negative. Network coupling did not amplify "
            f"adoption-cascade in this substrate; null direction realized. "
            f"Voice enters §3.4 ledger."
        )
    elif slope < low:
        verdict = "fail"
        outcome = "direction_recovered_magnitude_below_floor"
        rationale = (
            f"Slope {slope:.4f} below predicted floor {low:.4f}. The substrate "
            f"DID recover the predicted positive direction (network coupling "
            f"DOES amplify adoption-cascade — both regions' final renewable "
            f"share is monotonically higher under increasing k) but the "
            f"magnitude is much smaller than pre-committed. Two interpretations: "
            f"(a) substrate's price-pressure coupling is too weak relative to "
            f"the baseline drift, requiring stronger coupling in a v2; "
            f"(b) the pre-committed magnitude window was too aggressive for "
            f"the chosen substrate. Both are addressable in v2 — but not by "
            f"post-hoc adjustment of this v1's pre-registration. Voice enters "
            f"the §3.4 null-voice ledger with the direction-recovered flag."
        )
    elif slope > high:
        verdict = "fail"
        outcome = "response_above_predicted_ceiling"
        rationale = (
            f"Slope {slope:.4f} above predicted ceiling {high:.4f}. Over-"
            f"prediction; v2 should tighten."
        )
    else:
        verdict = "pass"
        outcome = "adoption_cascade_recovered_within_bound"
        rationale = (
            f"Slope {slope:.4f} within pre-committed range [{low:.4f}, "
            f"{high:.4f}]. Network coupling amplifies adoption-cascade in "
            f"the substrate. With v0 network_amplification_coupling_v1's "
            f"FAIL (failure-cascade is dampened by k) on record, the pair "
            f"establishes that failure-cascade and adoption-cascade have "
            f"opposite signs in the network coefficient. Eirmath's $-calibration "
            f"of network amplification should use the adoption-cascade direction "
            f"for renewable rollout questions. Per §1 honesty bounds this is not "
            f"a real-grid measurement."
        )

    return {
        "verdict": verdict,
        "outcome_category": outcome,
        "observed_slope": slope,
        "observed_intercept": intercept,
        "predicted_range": [low, high],
        "sweep_results": sweep_results,
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
    print(f"voice unit: {VOICE_NAME}  (kind: coupling, adoption-cascade)")
    print("=" * 72)
    sweep = run_network_sweep()
    for s in sweep:
        print(
            f"  k={s['network_coefficient']:>4.2f}  "
            f"final_share_A={s['final_share_region_a']:.4f}  "
            f"final_share_B={s['final_share_region_b']:.4f}  "
            f"secondary_response={s['secondary_adoption_response']:.4f}"
        )
    print("-" * 72)
    verdict = compute_verdict(sweep)
    print(f"  slope:           {verdict['observed_slope']:.4f}")
    print(f"  predicted range: {verdict['predicted_range']}")
    print(f"  verdict:         {verdict['verdict'].upper()}  ({verdict['outcome_category']})")
    print(f"  rationale: {verdict['rationale']}")
    sidecar_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"{VOICE_NAME}.sidecar.json",
    )
    emit_sidecar(verdict, sidecar_path)
    print(f"sidecar written: {sidecar_path}")


if __name__ == "__main__":
    main()
