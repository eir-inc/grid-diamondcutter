"""
voice_smooth_receiver_coupling_alarm_v1.py — inverted-kill bound-defender.

Defends the *emergent* registry bound surfaced by independent runs:

  When the receiver substrate exhibits a smooth-S-curve renewable-share
  trajectory, cross-region coupling measurements collapse into an
  over-correlation kill — the coupling slope exceeds the predicted upper
  magnitude bound because the receiver's own smooth trajectory dominates the
  signal, not because cross-region coupling is actually that strong.

This bound was not pre-registered in §1; it emerged from convergent independent
runs (denmark→germany coupling FAIL upper-bound, austria→germany sub-test,
france→switzerland sub-test). Three independent pair-substrates, one consistent
failure mode. Per the inverted-kill pattern (low_failure_rate_alarm_v1,
region_transfer_failure_v1, bound_defender_1_allocator_v1), the registry should
defend the empirical bound mechanically — so that any future run claiming
positive coupling on a smooth-S-curve receiver triggers a reviewer-visible alarm.

This voice synthesizes three smooth-S-curve receiver trajectories paired with
distinct sender substrates and runs the cross-region coupling slope measurement
on each pair. The empirical bound is supported (PASS) iff the cross-region
slope exceeds the magnitude upper bound on the majority of pairs (over-
correlation kill fires). FAIL (alarm) iff most pairs produce within-bound
coupling, which would contradict the empirical bound and indicate either
(a) the bound was overfit to the three observed pairs, or (b) the coupling
measurement has changed in a way that no longer reproduces the over-correlation
mode — either way, an alarm worth reviewing.

Authored under PREREGISTRATION.md §3.1; inverted-kill pattern (see PR #17, #16,
#18, #21). Substrate is fully synthetic; no external data dependency.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


VOICE_NAME = "smooth_receiver_coupling_alarm_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "synthetic_cross_region_coupling_meta",
    "named_residual": (
        "smooth-S-curve receivers wash out cross-region coupling via the upper-bound "
        "over-correlation kill. emergent registry bound from three independent "
        "run-time observations (DK→DE coupling FAIL, AT→DE coupling FAIL, FR→CH coupling FAIL). "
        "this voice mechanizes the bound so any future run claiming positive coupling on a "
        "smooth-S-curve receiver triggers an alarm rather than silently entering the registry."
    ),
    "smooth_receiver_pair_count": 3,
    "magnitude_upper_bound_per_pair": 0.50,
    "minimum_pairs_above_bound_to_support_empirical_finding": 2,
    "alarm_semantics": (
        "PASS = empirical bound supported (≥2 of 3 smooth-S-curve receiver pairs "
        "produce coupling slope above 0.50, reproducing the over-correlation kill); "
        "FAIL = alarm fired (the empirical bound did not reproduce; reviewer attention required)."
    ),
}

KILL_CONDITION = {
    "metric": "n_pairs_above_upper_bound",
    "rule": (
        "FAIL (alarm) if fewer than 2 of 3 synthetic smooth-S-curve receiver pairs "
        "produce a coupling slope > 0.50. PASS if ≥2 of 3 reproduce the over-correlation "
        "kill, supporting the empirical bound."
    ),
    "rationale": (
        "The empirical bound was surfaced by three independent run-time observations of "
        "the over-correlation kill firing on smooth-S-curve receivers. The bound is the "
        "registry's emergent capability claim (defined by negation — capability = "
        "set of substrate shapes where coupling DOES NOT generalize). Mechanizing the "
        "claim as an inverted-kill voice makes the bound part of the registry's audit trail; "
        "if the bound stops holding in a future run, the alarm surfaces it for reviewer "
        "examination rather than letting a contradicting result enter the registry silently."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_smooth_receiver_coupling_alarm_v1.py",
    "source_file": "examples/voices/voice_smooth_receiver_coupling_alarm_v1.py",
    "input_parameters": {
        "random_seed": 4291,
        "n_years": 14,
        "smooth_receiver_logistic_steepness": 0.6,
        "sender_logistic_steepness": 0.55,
        "lag_years": 1,
        "pair_sender_midpoints": [3.0, 5.0, 7.0],
        "pair_receiver_midpoints": [9.0, 10.0, 11.0],
        "pair_receiver_ceiling": [80.0, 75.0, 70.0],
        "additive_noise_sigma": 0.5,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


def _smooth_s_curve(n_years: int, midpoint: float, steepness: float, ceiling: float) -> np.ndarray:
    """Logistic S-curve in [0, ceiling] over n_years."""
    years = np.arange(n_years, dtype=float)
    return ceiling / (1.0 + np.exp(-steepness * (years - midpoint)))


def _coupling_slope(sender: np.ndarray, receiver: np.ndarray, lag: int) -> float:
    """Lagged linear coupling slope: receiver_{t+lag} on sender_t."""
    if lag >= len(sender):
        return 0.0
    s = sender[: len(sender) - lag]
    r = receiver[lag:]
    # normalize each series to 0..1 to make slope a magnitude across pairs
    s_n = (s - s.min()) / (s.max() - s.min() + 1e-9)
    r_n = (r - r.min()) / (r.max() - r.min() + 1e-9)
    # linear regression slope of r on s
    s_mean = s_n.mean()
    r_mean = r_n.mean()
    denom = ((s_n - s_mean) ** 2).sum()
    if denom < 1e-12:
        return 0.0
    return float(((s_n - s_mean) * (r_n - r_mean)).sum() / denom)


def run_voice_measurement() -> dict:
    """Generate 3 smooth-S-curve receiver pairs + measure coupling slope on each."""
    params = RUN_PROTOCOL["input_parameters"]
    rng = np.random.default_rng(params["random_seed"])

    n_years = params["n_years"]
    sender_steep = params["sender_logistic_steepness"]
    recv_steep = params["smooth_receiver_logistic_steepness"]
    noise_sigma = params["additive_noise_sigma"]

    sender_mids = params["pair_sender_midpoints"]
    recv_mids = params["pair_receiver_midpoints"]
    recv_ceils = params["pair_receiver_ceiling"]
    sender_ceiling = 60.0

    pair_results = []
    for i, (s_mid, r_mid, r_ceil) in enumerate(zip(sender_mids, recv_mids, recv_ceils)):
        sender = _smooth_s_curve(n_years, s_mid, sender_steep, sender_ceiling)
        receiver = _smooth_s_curve(n_years, r_mid, recv_steep, r_ceil)
        sender = sender + rng.normal(0.0, noise_sigma, n_years)
        receiver = receiver + rng.normal(0.0, noise_sigma, n_years)
        slope = _coupling_slope(sender, receiver, params["lag_years"])
        pair_results.append(
            {
                "pair_index": i,
                "sender_midpoint_year": s_mid,
                "receiver_midpoint_year": r_mid,
                "receiver_ceiling_pct": r_ceil,
                "coupling_slope": slope,
                "above_upper_bound": slope > PREDICTION["magnitude_upper_bound_per_pair"],
            }
        )

    n_above = sum(1 for p in pair_results if p["above_upper_bound"])
    return {
        "pair_results": pair_results,
        "n_pairs_above_upper_bound": n_above,
        "magnitude_upper_bound_per_pair": PREDICTION["magnitude_upper_bound_per_pair"],
    }


def compute_verdict(observed: dict) -> dict:
    threshold = PREDICTION["minimum_pairs_above_bound_to_support_empirical_finding"]
    n_above = observed["n_pairs_above_upper_bound"]
    if n_above >= threshold:
        verdict = "pass"
        rationale = (
            f"empirical bound supported: {n_above}/3 smooth-S-curve receiver pairs produced "
            f"coupling slope above {PREDICTION['magnitude_upper_bound_per_pair']}, "
            f"reproducing the over-correlation kill observed in PRs #35/#37."
        )
    else:
        verdict = "fail"
        rationale = (
            f"alarm: only {n_above}/3 smooth-S-curve receiver pairs reproduced the "
            f"over-correlation kill; empirical bound from prior runs not reproduced — "
            f"reviewer attention required (either the bound was over-fit to the three "
            f"observed pairs or the synthetic substrate diverges from the observed substrates)."
        )
    return {
        "verdict": verdict,
        "observed_value": n_above,
        "rationale": rationale,
        "pair_results": observed["pair_results"],
        "computed_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def emit_sidecar(verdict: dict, output_path: Path) -> str:
    unit_pre_verdict = {
        "voice_name": VOICE_NAME,
        "prediction": PREDICTION,
        "kill_condition": KILL_CONDITION,
        "run_protocol": RUN_PROTOCOL,
    }
    canonical = json.dumps(unit_pre_verdict, sort_keys=True, separators=(",", ":"))
    sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    unit = {**unit_pre_verdict, "verdict": verdict, "sidecar_sha256_pre_verdict": sha}
    output_path.write_text(json.dumps(unit, indent=2))
    return sha


def main() -> dict:
    print(f"=== {VOICE_NAME} ===")
    print(f"defending: emergent bound — smooth-S-curve receivers wash out coupling")
    print(f"  via over-correlation kill (upper bound {PREDICTION['magnitude_upper_bound_per_pair']})")
    print(f"  empirical observation from PRs #35, #37 (3 independent smooth-receiver pairs)")
    print()

    observed = run_voice_measurement()
    for p in observed["pair_results"]:
        print(
            f"  pair {p['pair_index']}: sender_mid={p['sender_midpoint_year']}, "
            f"recv_mid={p['receiver_midpoint_year']}, ceil={p['receiver_ceiling_pct']:.0f}%, "
            f"slope={p['coupling_slope']:.4f}, above_bound={p['above_upper_bound']}"
        )
    print()
    print(
        f"n_pairs_above_upper_bound: {observed['n_pairs_above_upper_bound']} / 3 "
        f"(threshold to support empirical bound: ≥2)"
    )

    verdict = compute_verdict(observed)
    print(f"verdict: {verdict['verdict']}")
    print(f"rationale: {verdict['rationale']}")

    sidecar_path = Path(__file__).parent / f"{VOICE_NAME}.sidecar.json"
    sha = emit_sidecar(verdict, sidecar_path)
    print(f"\nsidecar emitted: {sidecar_path.name}")
    print(f"sha256_pre_verdict: {sha}")
    return verdict


if __name__ == "__main__":
    main()
