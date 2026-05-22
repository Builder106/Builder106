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

# (label, dark_accent, light_accent, dark_cellbg, light_cellbg)
DISC = {
    "Q": ("Quant",    "#3fb950", "#1a7f37", "#0d2a17", "#e6f5ea"),
    "Y": ("Cybersec", "#f85149", "#cf222e", "#2e1416", "#fbe7e9"),
    "A": ("Analyst",  "#d29922", "#9a6700", "#2e2208", "#f8edd2"),
    "W": ("SWE",      "#a78bfa", "#6b46c1", "#1c1340", "#ebe4f7"),
    "M": ("Mobile",   "#58a6ff", "#0969da", "#0f1f3a", "#dfecfb"),
    "T": ("Tooling",  "#8b949e", "#656d76", "#1a1e23", "#eaecef"),
}


def cell_svg(theme, num, symbol, lang, project, disc):
    is_dark = theme == "dark"
    fg     = "#e6edf3" if is_dark else "#1f2328"
    muted  = "#8b949e" if is_dark else "#656d76"
    faded  = "#6e7681" if is_dark else "#8c959f"
    border = "#30363d" if is_dark else "#d0d7de"
    accent = DISC[disc][1 if is_dark else 2]
    cardbg = DISC[disc][3 if is_dark else 4]  # per-discipline tinted bg
    # Gradient overlay on top of the tinted bg, for extra depth at the top edge
    tint_opacity_top = 0.45 if is_dark else 0.35
    grad_id = f"g{num}"

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
  <defs>
    <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="{accent}" stop-opacity="{tint_opacity_top}"/>
      <stop offset="60%" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <g opacity="1">
    <set attributeName="opacity" to="0" begin="0s"/>
    <animate attributeName="opacity" from="0" to="1" begin="{reveal_delay:.2f}s" dur="0.55s" fill="freeze"/>
    <rect x="0.5" y="0.5" width="129" height="129" rx="4" fill="{cardbg}" stroke="{border}" stroke-width="1"/>
    <rect x="0.5" y="0.5" width="129" height="129" rx="4" fill="url(#{grad_id})"/>
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


def unified_svg(theme):
    """Single SVG containing the whole periodic table — visual centerpiece.
    Click-through per cell isn't possible when img-served; flat link list below
    the SVG in the README provides navigation."""
    is_dark = theme == "dark"
    bg_start  = "#0b0f15" if is_dark else "#ffffff"
    bg_end    = "#161b22" if is_dark else "#f0f3f6"
    dots_fill = "#1f2630" if is_dark else "#e6eaef"
    fg        = "#e6edf3" if is_dark else "#1f2328"
    muted     = "#7d8590" if is_dark else "#656d76"
    faded     = "#6e7681" if is_dark else "#8c959f"
    border    = "#30363d" if is_dark else "#d0d7de"
    cell_text_muted = "#8b949e" if is_dark else "#656d76"
    cell_text_faded = "#6e7681" if is_dark else "#8c959f"
    chrome_rule = "#262d36" if is_dark else "#e6eaef"

    W, H = 1200, 880
    MARGIN_L, MARGIN_TOP = 52, 130
    CELL_W, CELL_H = 130, 130
    COL_STRIDE, ROW_STRIDE = 139, 145

    by_pos = {(p, s): (num, symbol, lang, project, disc)
              for p, s, num, symbol, lang, project, disc in CELLS}

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Periodic table of self — 19 projects across 12 languages and 6 disciplines">']

    # Defs: bg gradient, dots, per-discipline cell gradients
    out.append('  <defs>')
    out.append(f'    <linearGradient id="canvasBg" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="{bg_start}"/><stop offset="100%" stop-color="{bg_end}"/></linearGradient>')
    out.append(f'    <pattern id="dots" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="1.4" cy="1.4" r="1.4" fill="{dots_fill}"/></pattern>')
    for code, (_, da, la, _, _) in DISC.items():
        accent = da if is_dark else la
        tint_opacity = 0.45 if is_dark else 0.35
        out.append(f'    <linearGradient id="grad-{code}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{accent}" stop-opacity="{tint_opacity}"/><stop offset="60%" stop-color="{accent}" stop-opacity="0"/></linearGradient>')
    out.append('  </defs>')

    # Canvas
    out.append(f'  <rect width="{W}" height="{H}" fill="url(#canvasBg)"/>')
    out.append(f'  <rect width="{W}" height="{H}" fill="url(#dots)"/>')

    # Header
    out.append(f'  <text x="52" y="50" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="14" fill="{muted}" letter-spacing="3">BUILDER106  //  THE ELEMENTS</text>')
    out.append(f'  <text x="52" y="80" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="13" fill="{faded}">19 projects  ·  12 languages  ·  6 disciplines  ·  arranged by language &amp; track</text>')
    out.append(f'  <line x1="52" y1="100" x2="{W - 47}" y2="100" stroke="{chrome_rule}" stroke-width="1"/>')

    # Group labels (1..8 across the top of cell columns)
    for g in range(8):
        cx = MARGIN_L + g * COL_STRIDE + CELL_W // 2
        out.append(f'    <text x="{cx}" y="120" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{muted}" text-anchor="middle">{g + 1}</text>')

    # Period labels (1..4 down the left side)
    for p in range(4):
        cy = MARGIN_TOP + p * ROW_STRIDE + CELL_H // 2 + 4
        out.append(f'    <text x="36" y="{cy}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{muted}" text-anchor="end">{p + 1}</text>')

    # Cells
    for (p, s), (num, symbol, lang, project, disc) in sorted(by_pos.items()):
        accent = DISC[disc][1 if is_dark else 2]
        cardbg = DISC[disc][3 if is_dark else 4]
        x = MARGIN_L + s * COL_STRIDE
        y = MARGIN_TOP + p * ROW_STRIDE
        reveal_delay = (num - 1) * 0.06
        pulse_offset = -((num * 0.21) % 4)
        is_now = project == NOW_PROJECT

        out.append(f'  <g opacity="1" transform="translate({x}, {y})">')
        out.append(f'    <set attributeName="opacity" to="0" begin="0s"/>')
        out.append(f'    <animate attributeName="opacity" from="0" to="1" begin="{reveal_delay:.2f}s" dur="0.55s" fill="freeze"/>')
        out.append(f'    <rect x="0.5" y="0.5" width="129" height="129" rx="4" fill="{cardbg}" stroke="{border}" stroke-width="1"/>')
        out.append(f'    <rect x="0.5" y="0.5" width="129" height="129" rx="4" fill="url(#grad-{disc})"/>')
        out.append(f'    <rect x="0.5" y="0.5" width="129" height="3" rx="1.5" fill="{accent}"><animate attributeName="opacity" values="1;0.45;1" dur="4s" begin="{pulse_offset:.2f}s" repeatCount="indefinite"/></rect>')
        out.append(f'    <text x="10" y="20" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" font-weight="500" fill="{accent}">{num:02d}</text>')
        if is_now:
            out.append(f'    <g transform="translate(118, 14)">')
            out.append(f'      <circle r="4" fill="{accent}"><animate attributeName="opacity" values="1;0.3;1" dur="1.6s" repeatCount="indefinite"/></circle>')
            out.append(f'      <circle r="4" fill="{accent}" opacity="0.4"><animate attributeName="r" values="4;9;4" dur="1.6s" repeatCount="indefinite"/><animate attributeName="opacity" values="0.5;0;0.5" dur="1.6s" repeatCount="indefinite"/></circle>')
            out.append(f'    </g>')
        out.append(f'    <text x="65" y="74" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="50" font-weight="700" fill="{fg}" text-anchor="middle" letter-spacing="-1">{symbol}</text>')
        out.append(f'    <text x="65" y="98" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="11" font-weight="600" fill="{cell_text_muted}" text-anchor="middle">{lang}</text>')
        out.append(f'    <text x="65" y="116" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" fill="{cell_text_faded}" text-anchor="middle">{project}</text>')
        out.append(f'  </g>')

    # Legend area
    legend_y = MARGIN_TOP + 4 * ROW_STRIDE + 8
    out.append(f'  <line x1="52" y1="{legend_y}" x2="{W - 47}" y2="{legend_y}" stroke="{chrome_rule}" stroke-width="1"/>')
    out.append(f'  <text x="52" y="{legend_y + 26}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{muted}" letter-spacing="2">GROUPS</text>')

    chip_x, chip_y = 140, legend_y + 12
    order = ["Q", "W", "Y", "A", "M", "T"]
    for code in order:
        name, da, la, dbg, lbg = DISC[code]
        accent = da if is_dark else la
        chip_bg = dbg if is_dark else lbg
        out.append(f'  <g transform="translate({chip_x}, {chip_y})">')
        out.append(f'    <rect x="0" y="0" width="118" height="22" rx="3" fill="{chip_bg}" stroke="{border}" stroke-width="1"/>')
        out.append(f'    <rect x="0" y="0" width="4" height="22" rx="2" fill="{accent}"/>')
        out.append(f'    <text x="14" y="15" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{muted}">{name}</text>')
        out.append(f'  </g>')
        chip_x += 130

    sym_y = legend_y + 64
    out.append(f'  <text x="52" y="{sym_y}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{muted}" letter-spacing="2">SYMBOLS</text>')
    syms = [("Oc","OCaml"),("Rs","Rust"),("C","C99"),("Py","Python"),("R","R"),("Rb","Ruby"),("Ts","TypeScript"),("Js","JavaScript"),("Sv","Svelte"),("Sw","Swift"),("Kt","Kotlin"),("Sh","Shell")]
    sx = 140
    for sym, name in syms:
        out.append(f'  <text x="{sx}" y="{sym_y}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{faded}"><tspan font-weight="700" fill="{fg}">{sym}</tspan> {name}</text>')
        sx += 86

    out.append('</svg>')
    return "\n".join(out)


def write_unified():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    for theme in ("dark", "light"):
        path = os.path.join(out_dir, f"table-{theme}.svg")
        with open(path, "w") as f:
            f.write(unified_svg(theme))
    print(f"wrote 2 unified table svgs to {out_dir}/", file=sys.stderr)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "svgs"
    if mode == "svgs":
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cells")
        write_svgs(out)
        print(f"wrote {len(CELLS) * 2} svgs to {out}/", file=sys.stderr)
    elif mode == "table":
        print_table()
    elif mode == "unified":
        write_unified()
    else:
        print(f"unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)
