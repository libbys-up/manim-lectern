"""Compare two renders of the same lectures, slide by slide.

    python tools/compare_slides.py BEFORE AFTER [--save DIFF_DIR]

BEFORE and AFTER are folders you ran `manim-slides render` in (each has a slides/
folder with <Scene>.json). For every scene rendered in both, this takes the last
frame of each slide and prints how different the two renders are: the mean
difference per pixel, from 0 (identical) to 255. With --save, slides that differ get
a before/after image in DIFF_DIR, so you can look at them.

Use it to check that a change to lectern doesn't alter lectures it shouldn't:
render some lectures, make the change, render them again in a second folder, compare.
Needs ffmpeg, numpy, and Pillow (manim already installs the last two).
"""

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

THRESHOLD = 0.5  # mean pixel difference below this counts as the same


def last_frames(folder, scene, tmp):
    """The last frame of each slide of `scene`, as images."""
    deck = json.loads((folder / "slides" / f"{scene}.json").read_text())
    frames = []
    for i, slide in enumerate(deck["slides"]):
        out = Path(tmp) / f"{folder.name}_{scene}_{i:03d}.png"
        # -update 1 keeps overwriting one image, so what's left is the last frame.
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-sseof", "-0.5", "-i", str(folder / slide["file"]),
                        "-update", "1", str(out)], check=True)
        frames.append(Image.open(out).convert("RGB"))
    return frames


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--save", type=Path, help="write before/after images of slides that differ here")
    args = ap.parse_args()
    scenes = sorted({p.stem for p in (args.before / "slides").glob("*.json")}
                    & {p.stem for p in (args.after / "slides").glob("*.json")})
    if not scenes:
        raise SystemExit("no scene was rendered in both folders")
    if args.save:
        args.save.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for scene in scenes:
            a, b = last_frames(args.before, scene, tmp), last_frames(args.after, scene, tmp)
            if len(a) != len(b):
                print(f"{scene}: {len(a)} slides before, {len(b)} after")
            diffs = []
            for i, (x, y) in enumerate(zip(a, b)):
                d = np.abs(np.asarray(x, float) - np.asarray(y, float)).mean() if x.size == y.size else 255.0
                diffs.append(d)
                if d > THRESHOLD and args.save:
                    pair = Image.new("RGB", (x.width, x.height * 2))
                    pair.paste(x, (0, 0))
                    pair.paste(y.resize(x.size), (0, x.height))
                    pair.save(args.save / f"{scene}_{i:03d}.png")
            changed = [i for i, d in enumerate(diffs) if d > THRESHOLD]
            status = "same" if not changed else f"{len(changed)} slides differ: {changed}"
            print(f"{scene}: {len(diffs)} slides compared, max difference {max(diffs, default=0):.2f}, {status}")


if __name__ == "__main__":
    main()
