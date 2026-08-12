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

## Directory Structure

```text
pfp/
├── source/          # Source files (committed to version control)
│   ├── quant-final.svg      # Animated SVG source
│   ├── build_pfp.py         # Build script
│   ├── requirements.txt     # Python dependencies
│   └── README.md            # This file
├── outputs/         # Final build artifacts (committed)
│   └── discord-perfect-500kb.png  # Discord-optimized APNG (<500KB)
└── archive/         # Intermediate/legacy files (not committed)
    ├── discord-perfect.png
    ├── discord-perfect-optimized.png
    ├── quant-pfp.png
    ├── pfp.gif
    ├── pfp_upscaled.gif
    └── SankofaForge_logo.png
```

## Outputs

- **Primary**: `outputs/discord-perfect-500kb.png` — final APNG output, optimized for Discord's 500KB avatar limit
- **Archive**: Intermediate builds, alternate formats, and unrelated files preserved but not version-controlled
