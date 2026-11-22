"""Regenerate the README images in docs/ from the demo.

    PYTHONPATH=src python3 tools/docs_images.py

docs/card.png is Tobi's card.png. docs/idle.gif is Wren's room idling at 2x.
docs/tobi.png and docs/wren.png are screenshots of the two sheets, taken by
tools/sheet_shots.cjs with Node and playwright-core (see tools/README.md).
A maintainer tool: not part of the package.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

from tinkerprint import art, look as looks
from tinkerprint.art import keepsake
from tinkerprint.art.pixels import Canvas
from tinkerprint.demo import run_demo
from tinkerprint.render_html import _worn

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(os.path.dirname(HERE), "docs")


def idle_gif(sheet: dict, scale: int = 2) -> bytes:
    """The sheet's room with the figure at its counter, as one looping GIF."""
    pack = art.default_pack()
    main, _ = art.sheet_looks(sheet)
    pcts = art.sheet_pcts(sheet)
    ranked = [(s, pcts[s]) for s in art.art_rank(pcts, sheet["profile"]["set"])]
    seed, tokens = looks.of_sheet(sheet)
    layers = keepsake.banner_layers(pack, main, ranked, [m["harness"] for m in sheet["party"]], seed,
                                    **looks.options(tokens))
    frames = []
    for room, wear in zip(layers.background.frames, _worn(layers.figure, layers.foreground, layers.figure_box)):
        c = Canvas(room.w, room.h)
        c.paste(room)
        c.paste(wear)
        frames.append(c)
    return keepsake.encode(frames, keepsake.DELAYS_MS, scale)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--docs", default=DOCS, help="where to write the images (default: the repo's docs/)")
    ap.add_argument("--keep", help="build the demo here and keep it, instead of a temporary folder")
    ap.add_argument("--no-shots", action="store_true", help="skip the sheet screenshots, which need Node")
    args = ap.parse_args()

    demo = args.keep or tempfile.mkdtemp(prefix="tinkerprint-docs-")
    try:
        run_demo(demo)
        shutil.copyfile(os.path.join(demo, "tobi", "card.png"), os.path.join(args.docs, "card.png"))
        with open(os.path.join(demo, "wren", "sheet.json"), encoding="utf-8") as f:
            gif = idle_gif(json.load(f))
        with open(os.path.join(args.docs, "idle.gif"), "wb") as f:
            f.write(gif)
        print("wrote card.png and idle.gif")
        if not args.no_shots:
            subprocess.run(["node", os.path.join(HERE, "sheet_shots.cjs"), demo, args.docs], check=True)
    finally:
        if not args.keep:
            shutil.rmtree(demo, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
