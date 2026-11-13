"""Original 56-second paper-book score, aligned to the v11 curved page timeline.

Run with Blender's bundled Python (NumPy included):
    blender --background --factory-startup --python create_audio.py
No recorded music, sampled instrument, downloaded Foley or voice-over is used.
"""
from pathlib import Path
import json
import wave
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Art" / "开场机关书_v11_20261113" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
RATE, SECONDS = 44100, 56
rng = np.random.default_rng(20261111)
audio = np.zeros((RATE * SECONDS, 2), dtype=np.float64)
TURN_STARTS = (6.30, 14.30, 22.30, 30.30, 44.30)
PULL_STARTS = (0.15, 8.15, 16.15, 24.15, 32.15, 46.15)
SEAL_TIMES = (42.0,)


def add(signal, start, gain=1.0, pan=0.0):
    """Constant-power stereo positioning, clamped inside the film."""
    first = int(round(start * RATE))
    if first < 0 or first >= len(audio):
        raise ValueError(f"Invalid audio event time: {start}")
    signal = signal[:min(len(signal), len(audio) - first)] * gain
    gains = np.array([np.cos((pan + 1) * np.pi / 4),
                      np.sin((pan + 1) * np.pi / 4)])
    audio[first:first + len(signal)] += signal[:, None] * gains


def pluck(midi, start, strength=0.10, pan=0.0, duration=3.6):
    """Soft zither-like additive pluck with lightly inharmonic upper strings."""
    t = np.arange(int(RATE * duration)) / RATE
    freq = 440.0 * 2 ** ((midi - 69) / 12)
    signal = np.zeros_like(t)
    for harmonic, amount in [(1, 1.0), (2, .30), (3, .14), (4, .07), (5, .025)]:
        decay = np.exp(-t * (1.5 + harmonic * .39))
        vibrato = .0008 * np.sin(2 * np.pi * 4.3 * t) * np.minimum(t, 1)
        phase = 2 * np.pi * freq * harmonic * (1 + .00017 * harmonic**2) * t
        signal += amount * decay * np.sin(phase + vibrato * freq)
    signal *= (1 - np.exp(-t * 550)) * np.minimum(1.0, (duration - t) * 8)
    add(signal, start, strength, pan)
    add(signal, start + .133, strength * .12, -pan * .7)
    add(signal, start + .267, strength * .055, pan * .2)


# D-gong pentatonic: D, E, F#, A, B. Six warm, restrained phrases.
phrases = [
    [(0.6, 62), (2.0, 66), (3.4, 69), (5.0, 73), (6.5, 69)],
    [(0.4, 69), (1.8, 73), (3.1, 74), (4.8, 73), (6.3, 69)],
    [(0.5, 66), (1.6, 69), (3.1, 71), (4.5, 69), (6.1, 66)],
    [(0.3, 64), (1.7, 66), (3.0, 69), (4.4, 66), (6.1, 64)],
    [(0.5, 66), (1.9, 69), (3.4, 74), (5.2, 73), (6.5, 69), (8.7, 66), (10.4, 69), (12.0, 73)],
    [(0.5, 69), (1.8, 66), (3.0, 64), (4.8, 62)],
]
for section, notes in enumerate(phrases):
    base = (0, 8, 16, 24, 32, 46)[section]
    for index, (offset, midi) in enumerate(notes):
        pluck(midi, base + offset, .093 + .012 * (index % 2),
              -.25 if index % 2 == 0 else .25)
    pluck(38 if section != 3 else 45, base + .15, .085, -.3, 5.0)
    pluck(57, base + 3.7, .052, .35, 4.0)


def paper_turn(start, duration=1.65):
    """One continuous broad page sweep finishing exactly at the next section."""
    t = np.arange(int(round(RATE * duration))) / RATE
    white = rng.normal(0, 1, len(t))
    low = np.convolve(white, np.ones(11) / 11, mode="same")
    mid = np.convolve(white, np.ones(3) / 3, mode="same") - low
    envelope = np.sin(np.pi * np.minimum(t / duration, 1)) ** 1.4
    movement = .7 + .3 * np.sin(2 * np.pi * 9.5 * t) ** 2
    add((low * .7 + mid * .3) * envelope * movement, start, .049, -.15)


def paper_pull(start, duration=.85):
    """Quieter card sliding in a paper sleeve, distinct from the page sweep."""
    t = np.arange(int(round(RATE * duration))) / RATE
    white = rng.normal(0, 1, len(t))
    smooth = np.convolve(white, np.ones(17) / 17, mode="same")
    fine = np.convolve(white, np.ones(5) / 5, mode="same") - smooth
    envelope = np.sin(np.pi * np.minimum(t / duration, 1)) ** 1.8
    friction = .55 + .45 * np.sin(2 * np.pi * 16 * t) ** 2
    add((smooth * .8 + fine * .2) * envelope * friction, start, .028, .2)


def stamp(start, gain):
    """Rounded wooden stamp impact, not a startling high-frequency crack."""
    t = np.arange(int(RATE * .45)) / RATE
    thump = (.8 * np.sin(2 * np.pi * 135 * t) * np.exp(-t * 35)
             + .22 * rng.normal(0, 1, len(t)) * np.exp(-t * 100))
    thump *= 1 - np.exp(-t * 1600)
    add(thump, start, gain, .15)


for second in TURN_STARTS:
    paper_turn(second)
for second in PULL_STARTS:
    paper_pull(second)
stamp(SEAL_TIMES[0], .15)

pluck(74, 52.8, .055, .15, 3.2)
pluck(62, 52.8, .07, -.15, 3.2)
fade_in = np.minimum(np.arange(len(audio)) / (RATE * .7), 1)
fade_out = np.minimum((len(audio) - 1 - np.arange(len(audio))) / (RATE * 2), 1)
audio *= (fade_in * fade_out)[:, None]
peak = float(np.max(np.abs(audio)))
rms = float(np.sqrt(np.mean(audio**2)))
# Audible underscore with conservative headroom: -25 dBFS RMS, -6 dBFS ceiling.
audio *= min(10 ** (-25 / 20) / max(rms, 1e-12), .501 / max(peak, 1e-12))
assert np.isfinite(audio).all() and np.max(np.abs(audio)) < 1
pcm = np.round(audio * 32767).astype("<i2")
target = OUT / "开场配乐与纸声_v11.wav"
with wave.open(str(target), "wb") as handle:
    handle.setnchannels(2)
    handle.setsampwidth(2)
    handle.setframerate(RATE)
    handle.writeframes(pcm.tobytes())
with wave.open(str(target), "rb") as handle:
    assert handle.getnframes() == RATE * SECONDS
    assert handle.getnchannels() == 2 and handle.getframerate() == RATE

report = {
    "asset": target.name,
    "version": "v11_20261113",
    "duration_seconds": SECONDS,
    "sample_rate": RATE,
    "channels": 2,
    "bits_per_sample": 16,
    "sample_count_per_channel": len(pcm),
    "peak_dbfs": float(20 * np.log10(np.max(np.abs(audio)) + 1e-12)),
    "rms_dbfs": float(20 * np.log10(np.sqrt(np.mean(audio**2)) + 1e-12)),
    "music": "Original additive pentatonic plucked-string synthesis; D E F# A B",
    "foley": "Original filtered-noise page turns and card pulls, synthesized wood-seal impacts",
    "paper_turn_seconds": list(TURN_STARTS),
    "paper_turn_duration_seconds": 1.65,
    "card_pull_seconds": list(PULL_STARTS),
    "card_pull_duration_seconds": .85,
    "seal_seconds": list(SEAL_TIMES),
    "voice_over": False,
    "external_audio_sources": [],
    "random_seed": 20261111,
    "timeline": "Six double-page book sections (8,8,8,8,14,10 seconds): history 1-3, transition 4, workshop 5, delivery 6",
}
(OUT / "开场音轨来源_v11.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
