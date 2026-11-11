"""Slice v04 sprite atlases into single cut-paper parts for the v05 HTML book.
Source atlases are read-only; outputs go to Art/开场纸书_v05_20261111/parts/."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
DEV = HERE.parents[1]
SRC = DEV / "Art/开场纸书_v04_20261111/assets"
OUT = DEV / "Art/开场纸书_v05_20261111/parts"
OUT.mkdir(parents=True, exist_ok=True)
atlases = {"chars": "扁平纸团印桃_v02.png", "build": "扁平纸艺建筑_v02.png",
           "plant": "扁平纸艺植物云纹_v02.png", "note": "组合交子_纸团印桃_引用_v01.png"}
report = {}
for key, name in atlases.items():
    im = Image.open(SRC / name).convert("RGBA")
    a = np.asarray(im)[:, :, 3] > 40
    report[key] = {"size": im.size, "parts": []}
    if key == "note":
        bb = Image.fromarray(a.astype(np.uint8) * 255).getbbox()
        im.crop(bb).save(OUT / "note.png")
        report[key]["parts"].append({"file": "note.png", "box": bb})
        continue
    closed = ndimage.binary_closing(a, iterations=6)
    lab, n = ndimage.label(closed)
    objs = ndimage.find_objects(lab)
    items = []
    for i, sl in enumerate(objs):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if w * h < 2500:
            continue
        items.append((sl[0].start, sl[1].start, sl[1].stop, sl[0].stop, i + 1))
    items.sort(key=lambda t: (t[0] // 150, t[1]))
    for k, (top, left, right, bottom, lid) in enumerate(items):
        crop = np.asarray(im)[top:bottom, left:right].copy()
        mask = lab[top:bottom, left:right] == lid
        crop[~mask] = 0
        fn = f"{key}_{k:02d}.png"
        Image.fromarray(crop).save(OUT / fn)
        report[key]["parts"].append({"file": fn, "box": [left, top, right, bottom]})
(OUT / "parts_index.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
for k, v in report.items():
    print(k, v["size"], len(v["parts"]))
    for p in v["parts"]:
        print("  ", p["file"], p["box"])
