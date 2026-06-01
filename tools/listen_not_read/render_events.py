"""render_events.py — render all 6 §4.2 historical events as listen-not-read .ogg.

Inputs:
  - Three Phase-A coupling voices (substrate trajectories from substrate simulation):
      texas_uri          (texas_feb_2021_uri_v1)
      eu_repowereu       (eu_may_2022_repowereu_v1)
      japan_fukushima    (japan_march_2011_fukushima_v1)
  - Three Phase-2 recognition voices (public-fixture monthly time-series):
      germany_2022       (germany_2022_recognition_criterion_v1)
      california_2000_01 (california_2000_2001_recognition_v1)
      texas_feb_2021_$   (texas_feb_2021_recognition_v1)

Outputs:
  - <output_dir>/<event_key>.ogg            audio render
  - <output_dir>/audio_manifest.json        metadata sidecar (attribution + anchors)

Run:
  python -m tools.listen_not_read.render_events \\
    [--output-dir /Users/eugenestuckless/eir/grids-eir-sh/public/audio]

§1 honesty bound: each render is OF the substrate-calibrated model trajectory,
not OF the real grid event. metadata captures the voice-script + sidecar
sha256 at render time so a hover-bubble can state the provenance honestly.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path("/Users/eugenestuckless/grid-diamondcutter-groove")
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from sonify import render_three_channel, write_ogg, sha256_of_file


# ---------------------------------------------------------------------------
# Helper: import a voice module from path so we can call its substrate fns
# ---------------------------------------------------------------------------

def _import_voice(rel_path: str):
    p = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(p.stem, str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, p


# ---------------------------------------------------------------------------
# Per-event extractors — each returns (primary, response, divergence,
#   regime_shift_step, n_primary, attribution_dict)
# ---------------------------------------------------------------------------

def extract_texas_uri():
    mod, p = _import_voice("examples/voices/texas_feb_2021_uri_v1.py")
    # Use the deepest cold-anomaly scenario (most dramatic substrate response)
    scenarios = mod.RUN_PROTOCOL["input_parameters"]["temperature_anomaly_scenarios_degC"]
    n_steps = mod.RUN_PROTOCOL["input_parameters"]["n_substrate_steps_per_scenario"]
    seed = mod.RUN_PROTOCOL["input_parameters"]["random_seed"]
    coldest = min(scenarios)
    gas = mod.gas_throughput_response(coldest, n_steps, seed)
    dispatch = mod.generation_dispatch_response(gas, coldest, seed)
    primary = gas  # collapses → louder bass
    response = dispatch  # collapses → pitch descent
    divergence = np.abs(gas - dispatch)  # propagation gap → wobble
    regime_shift = int(np.argmin(np.gradient(gas)))  # steepest gas decline
    return primary, response, divergence, regime_shift, len(primary), {
        "voice_id": "texas_feb_2021_uri_v1",
        "voice_path": str(p.relative_to(REPO_ROOT)),
        "scenario_descriptor": f"deepest cold-anomaly scenario: {coldest}°C",
        "substrate_kind": "phase_a_coupling_substrate_trajectory",
    }


def extract_eu_repowereu():
    mod, p = _import_voice("examples/voices/eu_may_2022_repowereu_v1.py")
    scenarios = mod.RUN_PROTOCOL["input_parameters"]["regulatory_signal_scenarios"]
    n_steps = mod.RUN_PROTOCOL["input_parameters"]["n_capital_steps_per_scenario"]
    seed = mod.RUN_PROTOCOL["input_parameters"]["random_seed"]
    # Use the strongest regulatory-signal scenario (full plan-target ambition)
    strongest = max(scenarios)
    signal = mod.regulatory_signal_trajectory(strongest, n_steps, seed)
    reallocation = mod.capital_reallocation_response(signal, strongest, seed)
    # EU is a POSITIVE-direction event (signal grows, response grows) — invert
    # both so the audio shape matches "collapse → louder" semantics: bass grows
    # as alternative-energy share grows.
    primary = 1.0 - signal
    response = 1.0 - reallocation
    divergence = np.abs(signal - reallocation)
    regime_shift = int(np.argmax(np.gradient(signal)))  # steepest signal rise
    return primary, response, divergence, regime_shift, len(primary), {
        "voice_id": "eu_may_2022_repowereu_v1",
        "voice_path": str(p.relative_to(REPO_ROOT)),
        "scenario_descriptor": f"strongest regulatory-signal scenario: {strongest}",
        "substrate_kind": "phase_a_coupling_substrate_trajectory",
        "polarity_note": "positive-direction event; audio inverted so growth → louder",
    }


def extract_japan_fukushima():
    mod, p = _import_voice("examples/voices/japan_march_2011_fukushima_v1.py")
    scenarios = mod.RUN_PROTOCOL["input_parameters"]["nuclear_capacity_loss_scenarios"]
    n_steps = mod.RUN_PROTOCOL["input_parameters"]["n_chain_steps_per_scenario"]
    seed = mod.RUN_PROTOCOL["input_parameters"]["random_seed"]
    # Use the largest nuclear-capacity-loss scenario
    largest = max(scenarios)
    nuclear = mod.nuclear_capacity_trajectory(largest, n_steps, seed)
    imports = mod.fossil_import_response(nuclear, seed)
    primary = nuclear  # collapses → louder bass
    response = 1.0 - imports  # imports grow → pitch descent
    divergence = np.abs((1.0 - nuclear) - imports)  # substitution incompleteness
    regime_shift = int(np.argmin(np.gradient(nuclear)))
    return primary, response, divergence, regime_shift, len(primary), {
        "voice_id": "japan_march_2011_fukushima_v1",
        "voice_path": str(p.relative_to(REPO_ROOT)),
        "scenario_descriptor": f"largest nuclear-capacity-loss scenario: {largest}",
        "substrate_kind": "phase_a_coupling_substrate_trajectory",
    }


def _series_from_dict(d: dict, value_key: str | None = None) -> np.ndarray:
    """Sort dict keys (YYYY-MM strings) and return values as array."""
    if value_key:
        items = sorted([(k, v[value_key]) for k, v in d.items()])
    else:
        items = sorted(d.items())
    return np.array([float(v) for _, v in items])


def _norm_inverse_price(prices: np.ndarray) -> np.ndarray:
    """Map a price series to a [0,1] inverse-affordability trajectory.

    Returns 1.0 at the cheapest point and approaches 0.0 at the most expensive.
    Audible semantic: collapse-of-affordability → primary → 0 → bass-loud.
    """
    return float(prices.min()) / np.maximum(prices, prices.min())


def extract_germany_2022():
    mod, p = _import_voice("phase_2/examples/voices/germany_2022_recognition_criterion_v1.py")
    # GERMANY_2022_NEGATIVE_HOURS_FIXTURE is a list of dicts with monthly hours
    fixture = mod.GERMANY_2022_NEGATIVE_HOURS_FIXTURE
    hours = np.array([float(m["n_negative_spot_hours"]) for m in fixture])
    # Germany 2022 is an EXCESS event (negative prices = excess supply). Audio
    # semantic: bass grows with excess-hours. Invert hours/max → 0=peak.
    peak = max(float(hours.max()), 1.0)
    primary = 1.0 - hours / peak
    response = primary.copy()  # same series; mid-band tracks intensity
    divergence = np.abs(np.diff(np.concatenate([[hours[0]], hours]))) / peak
    regime_shift = int(np.argmax(hours))
    return primary, response, divergence, regime_shift, len(primary), {
        "voice_id": "germany_2022_recognition_criterion_v1",
        "voice_path": str(p.relative_to(REPO_ROOT)),
        "scenario_descriptor": "BNetzA Monitoring 2022 §2.4.3 monthly negative-spot-hours fixture",
        "substrate_kind": "phase_2_recognition_public_fixture",
        "polarity_note": "excess-direction event; bass grows as negative-spot-hours grow",
    }


def extract_california_2000_01():
    mod, p = _import_voice("phase_2/examples/voices/california_2000_2001_recognition_v1.py")
    series_dict = mod.RUN_PROTOCOL["input_parameters"]["california_monthly_spot_price_usd_mwh"]
    prices = _series_from_dict(series_dict)
    primary = _norm_inverse_price(prices)  # 1=cheap, 0=expensive
    response = primary.copy()
    baseline_median = float(np.median(prices[:12]))  # 1999 baseline
    divergence = np.abs(prices - baseline_median) / max(prices.max(), 1.0)
    regime_shift = int(np.argmax(prices))
    return primary, response, divergence, regime_shift, len(primary), {
        "voice_id": "california_2000_2001_recognition_v1",
        "voice_path": str(p.relative_to(REPO_ROOT)),
        "scenario_descriptor": "synthetic v1 from FERC Final Report 2003 monthly wholesale spot (36 months)",
        "substrate_kind": "phase_2_recognition_public_fixture",
        "polarity_note": "spike-direction event; bass grows as affordability collapses",
    }


def extract_texas_feb_2021_monetary():
    mod, p = _import_voice("phase_2/examples/voices/texas_feb_2021_recognition_v1.py")
    series_dict = mod.RUN_PROTOCOL["input_parameters"]["texas_monthly_spot_price_usd_mwh"]
    prices = _series_from_dict(series_dict)
    primary = _norm_inverse_price(prices)
    response = primary.copy()
    baseline_median = float(np.median(prices))
    divergence = np.abs(prices - baseline_median) / max(prices.max(), 1.0)
    regime_shift = int(np.argmax(prices))
    return primary, response, divergence, regime_shift, len(primary), {
        "voice_id": "texas_feb_2021_recognition_v1",
        "voice_path": str(p.relative_to(REPO_ROOT)),
        "scenario_descriptor": "synthetic v1 from ERCOT post-event report + FERC/NERC Nov 2021 Inquiry (4 monthly points)",
        "substrate_kind": "phase_2_recognition_public_fixture",
        "polarity_note": "spike-direction event; bass grows as affordability collapses",
    }


# ---------------------------------------------------------------------------
# Event registry
# ---------------------------------------------------------------------------

EVENTS = [
    ("texas_uri_feb_2021", "Texas Uri (Feb 2021) — gas-throughput → generation-dispatch collapse",
     extract_texas_uri),
    ("eu_repowereu_may_2022", "EU REPowerEU (May 2022) — regulatory-signal → capital-reallocation lift",
     extract_eu_repowereu),
    ("japan_fukushima_mar_2011", "Japan Fukushima (Mar 2011) — nuclear-capacity loss → fossil-import substitution",
     extract_japan_fukushima),
    ("germany_2022_negative_spot", "Germany 2022 — negative-spot-price hours (excess-supply recognition)",
     extract_germany_2022),
    ("california_2000_2001", "California 2000-01 — wholesale-spot price instability (crisis-spike recognition)",
     extract_california_2000_01),
    ("texas_feb_2021_monetary", "Texas Feb 2021 monetary — ERCOT spot-price spike (crisis-spike recognition)",
     extract_texas_feb_2021_monetary),
]


def render_all(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_entries = []
    for event_key, title, extractor in EVENTS:
        print(f"[render] {event_key} ...", flush=True)
        primary, response, divergence, regime_shift, n_primary, attribution = extractor()
        audio = render_three_channel(primary, response, divergence, regime_shift, n_primary)
        out_path = output_dir / f"{event_key}.ogg"
        write_ogg(audio, out_path)
        # Capture provenance: voice + sidecar hashes for honest attribution
        voice_path = REPO_ROOT / attribution["voice_path"]
        sidecar_path = voice_path.with_suffix(".sidecar.json")
        entry = {
            "event_key": event_key,
            "title": title,
            "audio_file": f"{event_key}.ogg",
            "audio_bytes": out_path.stat().st_size,
            "audio_sha256": sha256_of_file(out_path),
            "voice_id": attribution["voice_id"],
            "voice_path": attribution["voice_path"],
            "voice_sha256": sha256_of_file(voice_path),
            "sidecar_path": str(sidecar_path.relative_to(REPO_ROOT)) if sidecar_path.exists() else None,
            "sidecar_sha256": sha256_of_file(sidecar_path) if sidecar_path.exists() else None,
            "scenario_descriptor": attribution["scenario_descriptor"],
            "substrate_kind": attribution["substrate_kind"],
            "polarity_note": attribution.get("polarity_note"),
            "regime_shift_step": regime_shift,
            "n_steps": int(n_primary),
            "honesty_note": (
                "This audio sonifies the substrate-calibrated model's trajectory, "
                "not a measurement of the real-grid event. The substrate's "
                "parameters are calibrated from cited public reports; the "
                "substrate is not the grid. Per §1 honesty bounds."
            ),
        }
        manifest_entries.append(entry)
        print(f"  → {out_path.name} ({entry['audio_bytes']} bytes)", flush=True)

    manifest = {
        "manifest_version": "1.0",
        "rendered_at_utc": datetime.now(timezone.utc).isoformat(),
        "renderer": "tools/listen_not_read/render_events.py + sonify.py (groove)",
        "sample_rate_hz": 22050,
        "duration_seconds": 30.0,
        "format": "OGG Vorbis",
        "n_events": len(manifest_entries),
        "events": manifest_entries,
    }
    manifest_path = output_dir / "audio_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"[manifest] {manifest_path}")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="/Users/eugenestuckless/grid-diamondcutter-groove/web_assets/audio",
        help="Where to write .ogg + audio_manifest.json",
    )
    args = parser.parse_args()
    render_all(Path(args.output_dir))


if __name__ == "__main__":
    main()
