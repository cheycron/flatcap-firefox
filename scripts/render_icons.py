#!/usr/bin/env python3
"""Derive the extension icons from the core logo (images/logo.png, the Mineral mark).

    python3 scripts/render_icons.py          # write icons/icon-48.png, icon-96.png, icon-128.png
    python3 scripts/render_icons.py --check  # fail if an icon differs from a fresh render

Requires Pillow. PNG files are derived artifacts; never edit them by hand.
"""
import argparse
import io
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SIZES = (48, 96, 128)


def render(size: int) -> bytes:
    src = Image.open(ROOT / "images" / "logo.png").convert("RGBA")
    out = io.BytesIO()
    src.resize((size, size), Image.Resampling.LANCZOS).save(out, "PNG", optimize=True)
    return out.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    bad = 0
    for s in SIZES:
        target = ROOT / "icons" / f"icon-{s}.png"
        data = render(s)
        if args.check:
            ok = target.is_file() and Image.open(target).convert("RGBA").tobytes() == Image.open(io.BytesIO(data)).convert("RGBA").tobytes()
            print(("ok     " if ok else "STALE  ") + str(target.relative_to(ROOT)))
            bad += not ok
        else:
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(data)
            print(f"wrote {target.relative_to(ROOT)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
