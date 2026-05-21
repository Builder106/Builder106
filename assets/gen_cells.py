#!/usr/bin/env python3
"""Generate per-cell SVGs for the periodic table.

Each cell is a self-contained 130x130 SVG with a transparent background,
so they tile into a continuous-looking grid when laid out in an HTML
<table>. Each cell is wrapped in <a> in the README for click-through.

Usage:
    python3 gen_cells.py svgs            # writes cells/*.svg
    python3 gen_cells.py table > /tmp/t  # prints HTML <table> markup
"""
import os
import sys

# (period, slot, num, symbol, lang, project_id, discipline_code)
CELLS = [
    (0, 0,  1, "Oc", "OCaml",      "ocaml_limit",    "Q"),
    (0, 7,  2, "C",  "C99",        "qforge",         "Q"),
    (1, 0,  3, "Rs", "Rust",       "ClearHash",      "Y"),
    (1, 1,  4, "Py", "Python",     "CapitolAlpha",   "Q"),
    (1, 6,  5, "R",  "R",          "datafest-2026",  "A"),
    (1, 7,  6, "Js", "JavaScript", "EconOS",         "Q"),
    (2, 0,  7, "Rb", "Ruby",       "LinuxBenchHub",  "W"),
    (2, 1,  8, "Ts", "TypeScript", "STAIJA",         "W"),
    (2, 2,  9, "Ts", "TypeScript", "StudySprint",    "W"),
    (2, 3, 10, "Sv", "Svelte",     "MicroMatch",     "W"),
    (2, 4, 11, "Ts", "TypeScript", "MedCore",        "A"),
    (2, 5, 12, "Ts", "TypeScript", "portfolio",      "W"),
    (2, 6, 13, "Py", "Python",     "IMC_Prosperity", "Q"),
    (2, 7, 14, "Py", "Python",     "HackHelper",     "Y"),
    (3, 0, 15, "Sw", "Swift",      "donut",          "M"),
    (3, 1, 16, "Sw", "Swift",      "DOOM",           "M"),
    (3, 2, 17, "Kt", "Kotlin",     "MetaHelper",     "M"),
    (3, 3, 18, "Sh", "Shell",      "PocketStyle",    "T"),
    (3, 4, 19, "Py", "Python",     "terminal",       "T"),
]

REPO_NAME = {  # project_id -> actual repo name (slug)
    "portfolio": "builder106.github.io",
}

# Currently-active project: gets a "NOW" indicator
NOW_PROJECT = "LinuxBenchHub"

# (label, dark_hex, light_hex)
DISC = {
    "Q": ("Quant",    "#3fb950", "#1a7f37"),
    "Y": ("Cybersec", "#f85149", "#cf222e"),
    "A": ("Analyst",  "#d29922", "#9a6700"),
    "W": ("SWE",      "#a78bfa", "#6b46c1"),
    "M": ("Mobile",   "#58a6ff", "#0969da"),
    "T": ("Tooling",  "#8b949e", "#656d76"),
}


def cell_svg(theme, num, symbol, lang, project, disc):
    is_dark = theme == "dark"
    fg     = "#e6edf3" if is_dark else "#1f2328"
    muted  = "#8b949e" if is_dark else "#656d76"
    faded  = "#6e7681" if is_dark else "#8c959f"
    border = "#30363d" if is_dark else "#d0d7de"
    cardbg = "#0d1117" if is_dark else "#ffffff"
    accent = DISC[disc][1 if is_dark else 2]

    reveal_delay = (num - 1) * 0.08
    pulse_offset = -((num * 0.21) % 4)
    is_now = project == NOW_PROJECT

    now_marker = ""
    if is_now:
        now_marker = f'''
    <g transform="translate(118, 14)">
      <circle r="4" fill="{accent}">
        <animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite"/>
      </circle>
      <circle r="4" fill="{accent}" opacity="0.4">
        <animate attributeName="r" values="4;9;4" dur="1.6s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.5;0;0.5" dur="1.6s" repeatCount="indefinite"/>
      </circle>
    </g>'''

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="130" height="130" viewBox="0 0 130 130" role="img" aria-label="{num:02d} {symbol} {lang} {project}">
  <g opacity="1">
    <set attributeName="opacity" to="0" begin="0s"/>
    <animate attributeName="opacity" from="0" to="1" begin="{reveal_delay:.2f}s" dur="0.55s" fill="freeze"/>
    <rect x="0.5" y="0.5" width="129" height="129" rx="4" fill="{cardbg}" stroke="{border}" stroke-width="1"/>
    <rect x="0.5" y="0.5" width="129" height="3" rx="1.5" fill="{accent}">
      <animate attributeName="opacity" values="1;0.45;1" dur="4s" begin="{pulse_offset:.2f}s" repeatCount="indefinite"/>
    </rect>
    <text x="10" y="20" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" font-weight="500" fill="{accent}">{num:02d}</text>{now_marker}
    <text x="65" y="74" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="50" font-weight="700" fill="{fg}" text-anchor="middle" letter-spacing="-1">{symbol}</text>
    <text x="65" y="98" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="11" font-weight="600" fill="{muted}" text-anchor="middle">{lang}</text>
    <text x="65" y="116" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" fill="{faded}" text-anchor="middle">{project}</text>
  </g>
</svg>
'''


def write_svgs(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for _, _, num, symbol, lang, project, disc in CELLS:
        for theme in ("dark", "light"):
            path = os.path.join(out_dir, f"{num:02d}-{symbol.lower()}-{theme}.svg")
            with open(path, "w") as f:
                f.write(cell_svg(theme, num, symbol, lang, project, disc))


def print_table():
    by_pos = {(p, s): (num, symbol, project) for p, s, num, symbol, _, project, _ in CELLS}
    print('<table cellspacing="2" cellpadding="0" border="0">')
    # Column header: group numbers
    print('  <tr>')
    print('    <td width="28"></td>')
    for g in range(1, 9):
        print(f'    <td width="132" align="center"><sub><code>{g}</code></sub></td>')
    print('  </tr>')
    for period in range(4):
        print('  <tr>')
        # Row header: period number
        print(f'    <td width="28" align="right" valign="middle"><sub><code>{period + 1}</code></sub></td>')
        for slot in range(8):
            if (period, slot) in by_pos:
                num, symbol, project = by_pos[(period, slot)]
                repo = REPO_NAME.get(project, project)
                stem = f"{num:02d}-{symbol.lower()}"
                url = f"https://github.com/Builder106/{repo}"
                print(f'    <td width="132" align="center"><a href="{url}" title="{project}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/cells/{stem}-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/cells/{stem}-light.svg"><img alt="{num:02d} {symbol} {project}" src="assets/cells/{stem}-dark.svg" width="130" height="130"></picture></a></td>')
            else:
                print(f'    <td width="132"></td>')
        print('  </tr>')
    print('</table>')


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "svgs"
    if mode == "svgs":
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cells")
        write_svgs(out)
        print(f"wrote {len(CELLS) * 2} svgs to {out}/", file=sys.stderr)
    elif mode == "table":
        print_table()
    else:
        print(f"unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)
