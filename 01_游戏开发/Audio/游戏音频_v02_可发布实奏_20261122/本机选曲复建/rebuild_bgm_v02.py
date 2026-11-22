"""Rebuild the eight local listening cues using the owner's source MP3s.

Requires Python 3.9+, NumPy and an FFmpeg executable with libvorbis.
Example:
    python rebuild_bgm_v02.py --source "G:/音乐" --output "./BGM"
Use --only workshop to rebuild a single cue, or --ffmpeg PATH to select FFmpeg.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np


def execute(ffmpeg, args, audio=None):
    return subprocess.run(
        [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", *map(str, args)],
        input=audio, stdout=subprocess.PIPE, check=True,
    ).stdout


def rebuild(args, cue):
    rate = 48000
    source = args.source / cue["source_file"]
    dest = args.output / ("bgm_" + cue["id"] + ".ogg")
    if dest.exists() and not args.force:
        raise FileExistsError(f"{dest} already exists. Use --force to replace it.")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != cue["source_sha256"]:
        print(f"Warning: {source.name} differs from the source used for these cut points.")
    # At 48 kHz, every integer millisecond falls exactly on a sample.
    start = cue["start_ms"] * 48
    end = cue["end_ms"] * 48
    overlap = cue["blend_ms"] * 48
    if not 0 < overlap < start < end or overlap >= end - start:
        raise ValueError(f"Invalid edit range for {cue['id']}")
    clip = execute(args.ffmpeg, [
        "-i", source, "-map", "0:a:0", "-af",
        f"aresample={rate},atrim=start_sample={start-overlap}:end_sample={end}",
        "-ar", rate, "-ac", "2", "-f", "f32le", "pipe:1",
    ])
    samples = np.frombuffer(clip, dtype="<f4").reshape(-1, 2)
    if len(samples) != end - start + overlap:
        raise ValueError(f"{source.name} does not cover the selected time range.")
    loop = samples[overlap:].copy()
    weight = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, overlap)))[:, None]
    loop[-overlap:] = (1 - weight) * loop[-overlap:] + samples[:overlap] * weight
    loop *= 10 ** (cue["gain_db"] / 20)
    # Write and verify beside the destination before replacing an earlier render.
    args.output.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(dir=args.output, suffix=".ogg", delete=False)
    temp = Path(handle.name)
    handle.close()
    try:
        execute(args.ffmpeg, [
            "-y", "-f", "f32le", "-ar", rate, "-ac", "2", "-i", "pipe:0",
            "-c:a", "libvorbis", "-q:a", "7", "-metadata", "artist=" + cue["artist"],
            "-metadata", "title=" + cue["title"], "-metadata", "album=" + cue["album"],
            "-metadata", "LOOPSTART=0", "-metadata", "LOOPEND=" + str(len(loop)),
            "-metadata", "comment=本地审听剪辑", temp,
        ], audio=loop.astype("<f4").tobytes())
        data = temp.read_bytes()
        final_page = data.rfind(b"OggS")
        if final_page < 0 or int.from_bytes(data[final_page+6:final_page+14], "little") != len(loop):
            raise ValueError(f"Unexpected loop duration in {temp.name}")
        os.replace(temp, dest)
    finally:
        temp.unlink(missing_ok=True)
    print(f"{cue['id']}: {len(loop)/rate:.3f}s -> {dest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", type=Path, default=Path("G:/音乐"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recipe", type=Path, default=Path(__file__).with_name("bgm_edits_v02.json"))
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--only", action="append", default=[], help="Cue ID; repeat for multiple cues")
    parser.add_argument("--force", action="store_true", help="Replace existing rendered tracks")
    args = parser.parse_args()
    cues = json.loads(args.recipe.read_text(encoding="utf-8"))["cues"]
    unknown = set(args.only) - {cue["id"] for cue in cues}
    if unknown:
        parser.error("Unknown cue ID: " + ", ".join(sorted(unknown)))
    for cue in cues:
        if not args.only or cue["id"] in args.only:
            rebuild(args, cue)


if __name__ == "__main__":
    main()
