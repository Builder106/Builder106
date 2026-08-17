#!/usr/bin/env python3
"""Build script for Builder106 assets.

Generates all derived assets from source files.
Run from the assets/ directory:
    python3 build.py
"""

import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None):
    """Run a command and return success."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode == 0


def main():
    assets_dir = Path(__file__).parent
    cells_dir = assets_dir / "cells"

    # Ensure output directories exist
    cells_dir.mkdir(parents=True, exist_ok=True)

    print("Building assets...")
    ok = True

    # 1. Generate per-cell SVGs
    print("\n1. Generating cell SVGs...")
    ok &= run([sys.executable, "gen_cells.py", "svgs"], cwd=assets_dir)

    # 2. Generate unified table SVGs
    print("\n2. Generating unified table SVGs...")
    ok &= run([sys.executable, "gen_cells.py", "unified"], cwd=assets_dir)

    # 3. Rasterize SVGs to PNGs (optional, requires cairosvg or similar)
    # For now, skip - PNGs can be generated separately if needed
    # print("\n3. Rasterizing SVGs to PNGs...")
    # ok &= run([...])

    if ok:
        print("\n✓ Build complete!")
        print(f"  Generated in {assets_dir}:")
        print("    table-dark.svg, table-light.svg")
        print(f"    cells/: {len(list(cells_dir.glob('*.svg')))} SVGs")
    else:
        print("\n✗ Build failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
