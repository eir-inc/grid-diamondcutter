"""sonify.py — render a three-channel substrate trajectory as a 30-second .ogg.

This is the audio render side of the listen-not-read mode for §4.2 historical
events. Input: three normalized [0,1] trajectories (primary / response / divergence)
+ a regime-shift step index. Output: 30-second .ogg at 22050 Hz mono.

Mapping (apoha-defined, not literal-instrument-substitution):
  - channel-1 (primary)    → sub-bass drone; amplitude tracks 1-primary
                              (collapse audible as amplitude growth, not loss)
  - channel-2 (response)   → mid-band tone; log-frequency tracks response
                              (collapse audible as pitch descent)
  - channel-3 (divergence) → tremolo LFO speed on the drone
                              (instability audible as wobble rate)
  - regime-shift step      → low-pass cutoff opens at the shift; harmonic
                              content widens (the timbre-shift signature)

Honest framing: the audio renders the SUBSTRATE-CALIBRATED MODEL'S trajectory,
not the real-grid event. §1 honesty-bound preserved. Hover metadata states
"sonification of substrate trajectory from voice <id>, sha256 of voice +
sidecar at render time."
"""
from __future__ import annotations
import json
import hashlib
import sys
from pathlib import Path

import numpy as np
import soundfile as sf


SAMPLE_RATE = 22050
DURATION_S = 30.0


def _resample_linear(trajectory: np.ndarray, target_len: int) -> np.ndarray:
    """Linear-interpolate a trajectory of any length onto target_len samples."""
    src_x = np.linspace(0.0, 1.0, len(trajectory))
    tgt_x = np.linspace(0.0, 1.0, target_len)
    return np.interp(tgt_x, src_x, trajectory)


def render_three_channel(
    primary: np.ndarray,
    response: np.ndarray,
    divergence: np.ndarray,
    regime_shift_step: int,
    primary_steps: int,
) -> np.ndarray:
    """Render 30s of audio from three normalized [0,1] trajectories.

    primary, response, divergence: 1D arrays. Lengths may differ; each is
    resampled to the audio length independently.
    regime_shift_step: step index in the PRIMARY trajectory where the
    regime-shift onset occurs. primary_steps: total steps in primary.
    """
    n_samples = int(DURATION_S * SAMPLE_RATE)
    t = np.arange(n_samples) / SAMPLE_RATE

    # Resample all three onto audio sample-rate
    p = np.clip(_resample_linear(primary, n_samples), 0.0, 1.0)
    r = np.clip(_resample_linear(response, n_samples), 0.0, 1.0)
    d = np.clip(_resample_linear(np.abs(divergence), n_samples), 0.0, 1.0)

    # Channel-1: sub-bass drone @ 55 Hz, amplitude = (1 - primary) so collapse → louder
    bass_freq = 55.0  # A1
    bass_phase = 2.0 * np.pi * bass_freq * t
    bass_amp = 0.4 * (1.0 - p)  # quiet baseline, grows as primary collapses

    # Channel-3: tremolo LFO on the bass. Speed ramps with divergence.
    # baseline 2 Hz, peaks at ~12 Hz at max divergence
    lfo_speed = 2.0 + 10.0 * d
    lfo_phase = 2.0 * np.pi * np.cumsum(lfo_speed) / SAMPLE_RATE
    tremolo = 0.5 + 0.5 * np.sin(lfo_phase)
    bass = bass_amp * tremolo * np.sin(bass_phase)

    # Channel-2: mid-band tone with log-pitch tracking response.
    # response=1.0 → 440 Hz (A4); response=0.05 → 110 Hz (A2, two octaves down)
    # collapse-to-zero audible as pitch descent.
    pitch_low_log = np.log2(110.0)
    pitch_high_log = np.log2(440.0)
    response_clipped = np.maximum(r, 0.05)
    pitch_log = pitch_low_log + (pitch_high_log - pitch_low_log) * response_clipped
    mid_freq = 2.0 ** pitch_log
    mid_phase = 2.0 * np.pi * np.cumsum(mid_freq) / SAMPLE_RATE
    mid_amp = 0.18 * response_clipped  # quieter when collapsed
    mid = mid_amp * np.sin(mid_phase)

    # Low-pass cutoff effect via post-shift harmonic richness:
    # before regime-shift, mid layer is a pure sine; after the shift, a slow
    # crossfade adds the third harmonic (timbre opens up).
    shift_sample = int((regime_shift_step / max(primary_steps - 1, 1)) * n_samples)
    crossfade_len = int(0.5 * SAMPLE_RATE)  # 0.5s fade-in
    harmonic_gain = np.zeros(n_samples)
    fade_end = min(shift_sample + crossfade_len, n_samples)
    if shift_sample < n_samples:
        ramp = np.linspace(0.0, 1.0, fade_end - shift_sample)
        harmonic_gain[shift_sample:fade_end] = ramp
        harmonic_gain[fade_end:] = 1.0
    harmonic = 0.08 * harmonic_gain * mid_amp * np.sin(3.0 * mid_phase)

    audio = bass + mid + harmonic

    # Apply a brief envelope on the whole thing (attack 0.05s, release 0.5s)
    n_attack = int(0.05 * SAMPLE_RATE)
    n_release = int(0.5 * SAMPLE_RATE)
    env = np.ones(n_samples)
    env[:n_attack] = np.linspace(0.0, 1.0, n_attack)
    env[-n_release:] = np.linspace(1.0, 0.0, n_release)
    audio = audio * env

    # Final peak-normalize to -3 dBFS (avoid clipping in lossy codecs)
    peak = float(np.max(np.abs(audio))) or 1.0
    audio = audio * (0.707 / peak)

    return audio.astype(np.float32)


def sha256_of_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def write_ogg(audio: np.ndarray, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_path), audio, SAMPLE_RATE, format="OGG", subtype="VORBIS")


if __name__ == "__main__":
    # Smoke test: render a 30s file with a synthetic collapse.
    n = 60
    primary = np.concatenate([np.ones(20), np.linspace(1.0, 0.2, 20), np.ones(20) * 0.2])
    response = np.concatenate([np.ones(20), np.linspace(1.0, 0.15, 25), np.ones(15) * 0.15])
    divergence = np.abs(primary - response)
    regime_shift_idx = 20
    audio = render_three_channel(primary, response, divergence, regime_shift_idx, n)
    out = Path("/tmp/sonify_smoke.ogg")
    write_ogg(audio, out)
    print(f"smoke render: {out} ({out.stat().st_size} bytes)")
