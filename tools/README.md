# tools

Maintainer tools. They are not part of the package: `pip install` leaves them out.

## README images

`docs_images.py` builds the demo and rewrites the four images the README shows:

- `docs/card.png`: Tobi's card.png.
- `docs/idle.gif`: Wren's room idling, at 2x.
- `docs/tobi.png` and `docs/wren.png`: the two sheets at 1046 px, light and dark, with reduced motion so they show the still frame.

The screenshots need Node and `playwright-core` with a Chromium it can launch. Run from the repo root:

```sh
PYTHONPATH=src python3 tools/docs_images.py
```

If `require('playwright-core')` can't find it, point `PLAYWRIGHT_CORE` at its folder. `--no-shots` writes only card.png and idle.gif. `--keep DIR` keeps the demo it built.

The card names the month it was built, so card.png changes from month to month. Retake the images when the sheet or the card changes, and check that the alt text in the README still describes them.
