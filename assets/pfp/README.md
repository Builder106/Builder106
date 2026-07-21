# SVG — animated profile picture

Renders an animated SVG (`quant-final.svg`) into a Discord-compatible animated PNG by frame-grabbing it through a headless browser.

## Pipeline

`build_pfp.py`:
1. Launches headless Chromium via Playwright at 256×256.
2. Loads `quant-final.svg` inside an HTML wrapper with the dark background pinned (`#0D1117`).
3. Captures frames across the SVG's animation loop.
4. Composites each frame onto an opaque RGB canvas (Discord's APNG decoder clips transparency badly otherwise) and offsets the frame order so the static fallback is the "good" frame.
5. Writes `discord-perfect.png` (animated PNG).

## Run

```bash
pip install playwright pillow
playwright install chromium
python build_pfp.py
```

## Outputs in this folder

- `quant-pfp.svg`, `quant-final.svg` — source SVGs (the `quant-final.svg` is what the script reads).
- `quant-pfp.png` — static raster of the SVG.
- `discord-perfect.png` — final APNG output, suitable for Discord avatar upload.
- `pfp.gif`, `pfp_upscaled.gif` — alternate GIF exports.
- `extension_test_screenshot.png` — unrelated, leftover from another project.
