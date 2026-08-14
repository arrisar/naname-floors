#!/usr/bin/env python3
"""
Render the README thumbnails for every mask in Textures/NanameFloors/TerrainMasks.
Run from anywhere after adding or changing a mask:

    python3 tools/thumbnails.py

Requires Pillow.
"""

import pathlib
import sys

from PIL import Image

SIZE = 96
BASE = (74, 82, 92)
COVER = (198, 168, 116)
EDGE = (128, 134, 142)

ROOT = pathlib.Path(__file__).resolve().parent.parent
MASKS = ROOT / "Textures" / "NanameFloors" / "TerrainMasks"
OUT = ROOT / "docs" / "masks"


def main() -> int:
    sources = sorted(MASKS.glob("*.png"))
    if not sources:
        print(f"no masks found in {MASKS}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    for src in sources:
        alpha = Image.open(src).convert("RGBA").split()[3].resize((SIZE, SIZE), Image.LANCZOS)
        tile = Image.new("RGB", (SIZE, SIZE), BASE)
        tile.paste(Image.new("RGB", (SIZE, SIZE), COVER), (0, 0), alpha)

        px = tile.load()
        for i in range(SIZE):
            px[i, 0] = px[i, SIZE - 1] = px[0, i] = px[SIZE - 1, i] = EDGE

        tile.save(OUT / src.name, optimize=True)
        print(src.name)

    stale = {p.name for p in OUT.glob("*.png")} - {p.name for p in sources}
    for name in sorted(stale):
        (OUT / name).unlink()
        print(f"removed stale {name}")

    print(f"\n{len(sources)} thumbnails written to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
