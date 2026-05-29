"""
voice_receiver_shape_distinguishability_v1.py — peer-check on the receiver-shape
axis claim that smooth_receiver_coupling_alarm_v1 (PR #42) and the cajal/miles
convergence (PR #35 / PR #37) rest on.

The prior pattern claims: smooth-S-curve receivers produce DIFFERENT coupling
behavior than step-function receivers — specifically, smooth receivers reproduce
the over-correlation kill, step receivers do not. If that distinction does not
actually exist mechanically, then "receiver shape matters" is a name without a
discriminator behind it, and the apoha-capability framing built on top is
overfit to the small number of observed pairs.

This voice generates N synthetic pairs of each receiver class (smooth vs step),
measures the coupling slope on each, and runs a permutation-style separability
check on the two slope distributions. PASS iff the distributions are mechanically
distinguishable at a tight margin (mean-of-smooth − mean-of-step ≥ separation_min);
FAIL iff they overlap enough that the receiver-shape axis is not actually
discriminative. FAIL is informative — it would invalidate the framing my PR #42
contributed and require the bound to be re-described in different terms.

This is a chain-keeper voice (subhuti lane): the registry should peer-check its
own emergent axes before accepting them as registry capabilities. Self-audit on
the same commit as the framing it tests.

Authored under PREREGISTRATION.md §3.1.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


VOICE_NAME = "receiver_shape_distinguishability_v1"

PREDICTION = {
    "kind": "polyphony_within_substrate",
    "substrate": "synthetic_cross_region_coupling_meta",
    "named_residual": (
        "receiver-shape axis discriminability — claim that smooth-S-curve and "
        "step-function receivers produce statistically distinguishable coupling-slope "
        "distributions. peer-checks the framing that smooth_receiver_coupling_alarm_v1 "
        "(PR #42) + cajal/miles PR #35 / #37 convergence rest on."
    ),
    "n_smooth_pairs": 12,
    "n_step_pairs": 12,
    "minimum_mean_separation": 0.15,
    "minimum_smooth_above_step_quantile": 0.75,
    "alarm_semantics": (
        "PASS = receiver-shape axis is mechanically discriminative "
        "(mean(smooth_slopes) − mean(step_slopes) ≥ 0.15 AND ≥75% of smooth slopes "
        "exceed the step-class median); FAIL = distributions overlap, framing not "
        "supported by the substrate."
    ),
}

KILL_CONDITION = {
    "metric": "smooth_step_mean_separation_and_quantile_dominance",
    "rule": (
        "PASS iff mean(smooth_slopes) − mean(step_slopes) ≥ 0.15 AND ≥75% of "
        "smooth pair slopes exceed median(step_slopes); FAIL otherwise. The voice "
        "treats the receiver-shape axis as falsified if either criterion does not hold."
    ),
    "rationale": (
        "If the receiver-shape distinction is real, smooth-S-curve pairs should "
        "concentrate at high slope values (over-correlation kill region) while "
        "step-function pairs should not. Requiring BOTH a mean separation AND a "
        "quantile-level dominance check guards against the distributions having "
        "similar means but heavy overlap, or being separated by outliers. If either "
        "criterion fails, the receiver-shape framing is a name without mechanical "
        "discriminator and the PR #42 alarm is operating on an over-fit axis."
    ),
}

RUN_PROTOCOL = {
    "entry_point": "python examples/voices/voice_receiver_shape_distinguishability_v1.py",
    "source_file": "examples/voices/voice_receiver_shape_distinguishability_v1.py",
    "input_parameters": {
        "random_seed": 7723,
        "n_years": 14,
        "n_smooth_pairs": 12,
        "n_step_pairs": 12,
        "smooth_logistic_steepness": 0.6,
        "step_function_transition_sharpness": 5.0,
        "sender_logistic_steepness": 0.55,
        "lag_years": 1,
        "additive_noise_sigma": 0.5,
    },
    "environment": {
        "python": "3.10+",
        "dependencies": ["numpy>=1.24"],
    },
}


def _smooth_s_curve(n_years: int, midpoint: float, steepness: float, ceiling: float) -> np.ndarray:
    years = np.arange(n_years, dtype=float)
    return ceiling / (1.0 + np.exp(-steepness * (years - midpoint)))


def _step_function(n_years: int, midpoint: float, sharpness: float, ceiling: float) -> np.ndarray:
    """Sharp-transition step function in [0, ceiling]; sharpness controls edge steepness."""
    years = np.arange(n_years, dtype=float)
    return ceiling / (1.0 + np.exp(-sharpness * (years - midpoint)))


def _coupling_slope(sender: np.ndarray, receiver: np.ndarray, lag: int) -> float:
    if lag >= len(sender):
        return 0.0
    s = sender[: len(sender) - lag]
    r = receiver[lag:]
    s_n = (s - s.min()) / (s.max() - s.min() + 1e-9)
    r_n = (r - r.min()) / (r.max() - r.min() + 1e-9)
    s_mean = s_n.mean()
    r_mean = r_n.mean()
    denom = ((s_n - s_mean) ** 2).sum()
    if denom < 1e-12:
        return 0.0
    return float(((s_n - s_mean) * (r_n - r_mean)).sum() / denom)


def _make_pair(
    rng: np.random.Generator,
    receiver_shape: str,
    params: dict,
) -> tuple[np.ndarray, np.ndarray]:
    n_years = params["n_years"]
    sender_mid = float(rng.uniform(3.0, 8.0))
    recv_mid = float(rng.uniform(7.0, 11.0))
    recv_ceiling = float(rng.uniform(55.0, 85.0))
    sender_ceiling = 60.0
    sender = _smooth_s_curve(
        n_years, sender_mid, params["sender_logistic_steepness"], sender_ceiling
    )
    if receiver_shape == "smooth":
        receiver = _smooth_s_curve(
            n_years, recv_mid, params["smooth_logistic_steepness"], recv_ceiling
        )
    elif receiver_shape == "step":
        receiver = _step_function(
            n_years, recv_mid, params["step_function_transition_sharpness"], recv_ceiling
        )
    else:
        raise ValueError(f"unknown receiver_shape {receiver_shape!r}")
    sender = sender + rng.normal(0.0, params["additive_noise_sigma"], n_years)
    receiver = receiver + rng.normal(0.0, params["additive_noise_sigma"], n_years)
    return sender, receiver


def run_voice_measurement() -> dict:
    params = RUN_PROTOCOL["input_parameters"]
    rng = np.random.default_rng(params["random_seed"])

    smooth_slopes = []
    for _ in range(params["n_smooth_pairs"]):
        s, r = _make_pair(rng, "smooth", params)
        smooth_slopes.append(_coupling_slope(s, r, params["lag_years"]))
    step_slopes = []
    for _ in range(params["n_step_pairs"]):
        s, r = _make_pair(rng, "step", params)
        step_slopes.append(_coupling_slope(s, r, params["lag_years"]))

    smooth_arr = np.array(smooth_slopes)
    step_arr = np.array(step_slopes)
    smooth_mean = float(smooth_arr.mean())
    step_mean = float(step_arr.mean())
    mean_separation = smooth_mean - step_mean
    step_median = float(np.median(step_arr))
    n_smooth_above_step_median = int((smooth_arr > step_median).sum())
    smooth_above_step_median_frac = n_smooth_above_step_median / len(smooth_arr)

    return {
        "smooth_slopes": [float(x) for x in smooth_slopes],
        "step_slopes": [float(x) for x in step_slopes],
        "smooth_mean": smooth_mean,
        "step_mean": step_mean,
        "mean_separation": mean_separation,
        "step_median": step_median,
        "smooth_above_step_median_frac": smooth_above_step_median_frac,
    }


def compute_verdict(observed: dict) -> dict:
    sep_min = PREDICTION["minimum_mean_separation"]
    quant_min = PREDICTION["minimum_smooth_above_step_quantile"]
    sep_ok = observed["mean_separation"] >= sep_min
    quant_ok = observed["smooth_above_step_median_frac"] >= quant_min
    if sep_ok and quant_ok:
        verdict = "pass"
        rationale = (
            f"receiver-shape axis discriminative: mean separation "
            f"{observed['mean_separation']:.4f} ≥ {sep_min}, AND "
            f"{observed['smooth_above_step_median_frac']:.2%} of smooth slopes exceed "
            f"step-class median ≥ {quant_min:.0%}. PR #42 framing has substrate support."
        )
    else:
        failed = []
        if not sep_ok:
            failed.append(
                f"mean_separation {observed['mean_separation']:.4f} < {sep_min}"
            )
        if not quant_ok:
            failed.append(
                f"smooth_above_step_median_frac {observed['smooth_above_step_median_frac']:.2%} "
                f"< {quant_min:.0%}"
            )
        verdict = "fail"
        rationale = (
            f"receiver-shape axis NOT mechanically discriminative; failed: "
            f"{'; '.join(failed)}. PR #42's framing is over-fit to the small "
            f"observed-pair set — the receiver-shape claim needs re-description "
            f"or the synthetic substrate is missing the distinguishing dynamic."
        )
    return {
        "verdict": verdict,
        "observed_mean_separation": observed["mean_separation"],
        "observed_quantile_dominance": observed["smooth_above_step_median_frac"],
        "rationale": rationale,
        "smooth_slopes_summary": {
            "mean": observed["smooth_mean"],
            "min": float(min(observed["smooth_slopes"])),
            "max": float(max(observed["smooth_slopes"])),
        },
        "step_slopes_summary": {
            "mean": observed["step_mean"],
            "min": float(min(observed["step_slopes"])),
            "max": float(max(observed["step_slopes"])),
        },
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
    print(f"peer-checking PR #42 framing: do smooth-S-curve and step-function")
    print(f"receivers produce mechanically distinguishable coupling-slope distributions?")
    print()
    observed = run_voice_measurement()
    print(
        f"smooth slopes (n={len(observed['smooth_slopes'])}): "
        f"mean={observed['smooth_mean']:.4f}, "
        f"range=[{min(observed['smooth_slopes']):.4f}, {max(observed['smooth_slopes']):.4f}]"
    )
    print(
        f"step slopes   (n={len(observed['step_slopes'])}): "
        f"mean={observed['step_mean']:.4f}, "
        f"range=[{min(observed['step_slopes']):.4f}, {max(observed['step_slopes']):.4f}]"
    )
    print(f"mean separation (smooth − step): {observed['mean_separation']:.4f}")
    print(
        f"smooth above step-median: {observed['smooth_above_step_median_frac']:.2%} "
        f"(step median = {observed['step_median']:.4f})"
    )
    print()
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
