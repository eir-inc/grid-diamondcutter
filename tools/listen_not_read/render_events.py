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
        "what_was_modeled": (
            f"The most extreme cold snap in the February 2021 Texas storm — a "
            f"{int(-coldest)}°C temperature drop. The model traces natural-gas "
            "pipeline throughput collapsing, then electricity generation "
            "collapsing behind it."
        ),
        "model_kind": "two-coupled-system simulation",
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
        "what_was_modeled": (
            "The European Commission's May 2022 plan to wean off Russian gas "
            "(REPowerEU). The model traces the regulatory push, then capital "
            "flowing into alternative-energy projects in response."
        ),
        "model_kind": "two-coupled-system simulation",
        "direction_note": (
            "This event is growth, not collapse. The audio is inverted so the "
            "same listening shape applies — louder = more change underway."
        ),
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
        "what_was_modeled": (
            "Japan after the March 2011 Fukushima accident, with most of the "
            f"nuclear fleet ({int(largest * 100)}%) taken offline. The model "
            "traces nuclear capacity dropping, then fossil-fuel imports "
            "rising to fill the gap."
        ),
        "model_kind": "two-coupled-system simulation",
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
        "what_was_modeled": (
            "Germany 2022 — hours of negative wholesale electricity prices, "
            "month by month. Renewables generated so much power that the grid "
            "paid customers to take it. Source: Germany's federal regulator "
            "(BNetzA) annual monitoring report."
        ),
        "model_kind": "publicly-reported monthly counts",
        "direction_note": (
            "This event is excess, not shortage. The audio is calibrated so "
            "louder = more hours of negative prices."
        ),
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
        "what_was_modeled": (
            "The California electricity crisis of 2000-2001 — three years of "
            "monthly wholesale prices, from the pre-crisis baseline through "
            "the peak (over $370/MWh, more than 12× normal) and back. Source: "
            "FERC's 2003 Final Report on the crisis."
        ),
        "model_kind": "publicly-reported monthly prices",
        "direction_note": (
            "Louder = prices further from normal. The spike that hits in "
            "mid-2000 is audible."
        ),
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
        "what_was_modeled": (
            "Texas February 2021, viewed through the price lens — four months "
            "of average wholesale electricity prices that bracket the Uri "
            "storm. February's price was roughly 66× the surrounding months "
            "after prices hit the $9000/MWh cap. Source: ERCOT post-event "
            "report + the FERC/NERC inquiry."
        ),
        "model_kind": "publicly-reported monthly prices",
        "direction_note": (
            "Louder = prices further from normal. The February spike "
            "dominates the 30 seconds."
        ),
    }


# ---------------------------------------------------------------------------
# Event registry
# ---------------------------------------------------------------------------

EVENTS = [
    ("texas_uri_feb_2021",
     "Texas, February 2021 — winter storm Uri. Natural gas froze, then "
     "electricity generation collapsed.",
     extract_texas_uri),
    ("eu_repowereu_may_2022",
     "European Union, May 2022 — REPowerEU. The bloc's plan to wean off "
     "Russian gas, pushing capital into alternative energy.",
     extract_eu_repowereu),
    ("japan_fukushima_mar_2011",
     "Japan, March 2011 — Fukushima accident. Nuclear plants went offline; "
     "fossil-fuel imports filled the gap.",
     extract_japan_fukushima),
    ("germany_2022_negative_spot",
     "Germany, 2022 — hours of negative wholesale electricity prices. "
     "Renewables overshot demand, so the grid paid customers to consume.",
     extract_germany_2022),
    ("california_2000_2001",
     "California, 2000-2001 — the electricity crisis. Wholesale prices "
     "spiked over twelve times above their pre-crisis level.",
     extract_california_2000_01),
    ("texas_feb_2021_monetary",
     "Texas, February 2021 — the price view of winter storm Uri. Monthly "
     "wholesale electricity prices spiked sixty-six times normal.",
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
            "what_was_modeled": attribution["what_was_modeled"],
            "model_kind": attribution["model_kind"],
            "direction_note": attribution.get("direction_note"),
            "caveat": (
                "This is the sound of a computer model, not a recording of "
                "the actual event. The model uses numbers taken from public "
                "reports about each event. It is not a measurement of any "
                "real power grid."
            ),
            "source_code": {
                "voice_id": attribution["voice_id"],
                "voice_path": attribution["voice_path"],
                "voice_sha256": sha256_of_file(voice_path),
                "sidecar_path": str(sidecar_path.relative_to(REPO_ROOT)) if sidecar_path.exists() else None,
                "sidecar_sha256": sha256_of_file(sidecar_path) if sidecar_path.exists() else None,
            },
            "audio_render_internals": {
                "regime_shift_step": regime_shift,
                "n_steps": int(n_primary),
            },
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
