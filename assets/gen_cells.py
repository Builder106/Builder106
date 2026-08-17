#!/usr/bin/env python3
"""Generate per-cell SVGs for the periodic table.

Each cell is a self-contained 130x130 SVG with a transparent background,
so they tile into a continuous-looking grid when laid out in an HTML
<table>. Each cell is wrapped in <a> in the README for click-through.

Usage:
    python3 gen_cells.py svgs            # writes cells/*.svg
    python3 gen_cells.py table > /tmp/t  # prints HTML <table> markup
"""

import json
import os
import sys
from pathlib import Path

# Every colour comes from palette.json, which mirrors the hero SVGs.
# Regenerate it with make_palette.py; never hard-code a hex in here.
PALETTE = json.loads((Path(__file__).parent / "palette.json").read_text())
NEUTRAL = PALETTE["neutral"]
TRACK = PALETTE["tracks"]

# (period, slot, num, symbol, lang, project_id, discipline_code)
CELLS = [
    (0, 0, 1, "Oc", "OCaml", "ocaml_limit", "Q"),
    (0, 7, 2, "C", "C99", "qforge", "Q"),
    (1, 0, 3, "Rs", "Rust", "ClearHash", "Y"),
    (1, 1, 4, "Py", "Python", "CapitolAlpha", "A"),
    (1, 6, 5, "R", "R", "datafest-2026", "A"),
    (1, 7, 6, "Py", "Python", "EconOS", "Q"),
    (2, 0, 7, "Rb", "Ruby", "LinuxBenchHub", "A"),
    (2, 1, 8, "Ts", "TypeScript", "STAIJA", "W"),
    (2, 2, 9, "Ts", "TypeScript", "StudySprint", "W"),
    (2, 3, 10, "Sv", "Svelte", "MicroMatch", "W"),
    (2, 4, 11, "Ts", "TypeScript", "MedCore", "H"),
    (2, 5, 12, "Ts", "TypeScript", "portfolio", "W"),
    (2, 6, 13, "Py", "Python", "IMC_Prosperity", "L"),
    (2, 7, 14, "Sw", "Swift", "celestial_sanctum", "M"),
    (3, 0, 15, "Go", "Go", "halberd", "Y"),
    (3, 1, 16, "Ts", "TypeScript", "quarry", "Y"),
    (3, 2, 17, "Ts", "TypeScript", "enclave", "L"),
    (3, 3, 18, "Ts", "TypeScript", "helm", "L"),
    (3, 4, 19, "Kt", "Kotlin", "MetaHelper", "M"),
    (3, 5, 20, "Rs", "Rust", "ascii_arcade", "T"),
]

REPO_NAME = {  # project_id -> actual repo name (slug)
    "ocaml_limit": "ocaml-limit",
    "ClearHash": "clear-hash",
    "CapitolAlpha": "capitol-alpha",
    "EconOS": "econ-os",
    "LinuxBenchHub": "linux-bench-hub",
    "STAIJA": "staija",
    "StudySprint": "study-sprint",
    "MicroMatch": "micro-match",
    "MedCore": "med-core",
    "portfolio": "builder106.github.io",
    "IMC_Prosperity": "imc-prosperity",
    "celestial_sanctum": "celestial-sanctum",
    "halberd": "halberd",
    "quarry": "quarry",
    "enclave": "enclave",
    "helm": "helm",
    "MetaHelper": "meta-helper",
    "ascii_arcade": "ascii-arcade",
}

# Currently-active project: gets a "NOW" indicator
NOW_PROJECT = "MicroMatch"


def disc_label(code):
    return TRACK[code]["label"]


def disc_accent(code, theme):
    return TRACK[code][theme]["accent"]


def disc_tint(code, theme):
    return TRACK[code][theme]["tint"]


def disc_text(code, theme):
    """Label colour for text set on a discipline's card. Darker/lighter than the
    accent so it clears WCAG 2.2 AAA (7:1) against the tint."""
    return TRACK[code][theme]["text"]


# Animation, declared in CSS rather than SMIL so that a reader who has asked
# their OS for reduced motion actually gets a still image (WCAG 2.2.2).
MOTION_CSS = """  <style>
    .cell   { animation: reveal 0.55s both; }
    .halo   { opacity: 0; animation: spotlight 16s linear infinite; }
    .wave   { animation: wave 5s linear infinite; }
    .pulse  { animation: pulse 4s ease-in-out infinite; }
    .now    { animation: pulse 1.6s ease-in-out infinite; }
    .ripple { transform-origin: center; animation: ripple 1.6s linear infinite; }
    @keyframes reveal    { from { opacity: 0; } to { opacity: 1; } }
    @keyframes spotlight { 0% { opacity: 0; } 4%, 10% { opacity: 0.55; } 14%, 100% { opacity: 0; } }
    @keyframes wave      { 0% { opacity: 0.4; } 10%, 20% { opacity: 1; } 30%, 100% { opacity: 0.4; } }
    @keyframes pulse     { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    @keyframes ripple    { from { transform: scale(1); opacity: 0.5; } to { transform: scale(2.25); opacity: 0; } }
    @media (prefers-reduced-motion: reduce) {
      .cell, .halo, .wave, .pulse, .now, .ripple { animation: none; }
      .cell, .wave, .pulse, .now { opacity: 1; }
      .halo, .ripple { opacity: 0; }
    }
  </style>"""


def cell_svg(theme, num, symbol, lang, project, disc):
    is_dark = theme == "dark"
    n = NEUTRAL[theme]
    fg = n["fg"]
    muted = n["muted"]
    faded = n["faded"]
    border = n["border"]
    accent = disc_accent(disc, theme)
    label_ink = disc_text(disc, theme)
    cardbg = disc_tint(disc, theme)  # per-discipline tinted bg
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
      <circle class="now" r="4" fill="{accent}"/>
      <circle class="ripple" r="4" fill="{accent}" opacity="0.5"/>
    </g>'''

    label = disc_label(disc)
    disc_x = 106 if is_now else 120
    disc_tag = f'<text x="{disc_x}" y="22" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" font-weight="600" fill="{label_ink}" text-anchor="end">{label}</text>'

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="130" height="130" viewBox="0 0 130 130" role="img" aria-label="{num:02d} {symbol} {lang} {project} {label}">
  <defs>
{MOTION_CSS}
    <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"  stop-color="{accent}" stop-opacity="{tint_opacity_top}"/>
      <stop offset="60%" stop-color="{accent}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <g class="cell" style="animation-delay: {reveal_delay:.2f}s">
    <rect x="0.5" y="0.5" width="129" height="129" rx="4" fill="{cardbg}" stroke="{border}" stroke-width="1"/>
    <rect x="0.5" y="0.5" width="129" height="129" rx="4" fill="url(#{grad_id})"/>
    <rect class="pulse" style="animation-delay: {pulse_offset:.2f}s" x="0.5" y="0.5" width="129" height="3" rx="1.5" fill="{accent}"/>
    <text x="10" y="22" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="500" fill="{label_ink}">{num:02d}</text>{disc_tag}{now_marker}
    <text x="65" y="76" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="50" font-weight="700" fill="{fg}" text-anchor="middle" letter-spacing="-1">{symbol}</text>
    <text x="65" y="101" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="13" font-weight="600" fill="{muted}" text-anchor="middle">{lang}</text>
    <text x="65" y="120" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{faded}" text-anchor="middle">{project}</text>
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
    print("  <tr>")
    print('    <td width="28"></td>')
    for g in range(1, 9):
        print(f'    <td width="132" align="center"><sub><code>{g}</code></sub></td>')
    print("  </tr>")
    for period in range(4):
        print("  <tr>")
        # Row header: period number
        print(f'    <td width="28" align="right" valign="middle"><sub><code>{period + 1}</code></sub></td>')
        for slot in range(8):
            if (period, slot) in by_pos:
                num, symbol, project = by_pos[(period, slot)]
                repo = REPO_NAME.get(project, project)
                stem = f"{num:02d}-{symbol.lower()}"
                url = f"https://github.com/Builder106/{repo}"
                print(
                    f'    <td width="132" align="center"><a href="{url}" title="{project}"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/cells/{stem}-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/cells/{stem}-light.svg"><img alt="{num:02d} {symbol} {project}" src="assets/cells/{stem}-dark.svg" width="130" height="130"></picture></a></td>'
                )
            else:
                print('    <td width="132"></td>')
        print("  </tr>")
    print("</table>")


def unified_svg(theme):
    """Single SVG containing the whole periodic table — visual centerpiece.
    Click-through per cell isn't possible when img-served; flat link list below
    the SVG in the README provides navigation."""
    is_dark = theme == "dark"
    n = NEUTRAL[theme]
    fg = n["fg"]
    muted = n["muted"]
    faded = n["faded"]
    border = n["border"]
    cell_text_muted = n["muted"]
    cell_text_faded = n["faded"]
    chrome_rule = n["rule"]

    W, H = 1200, 885
    MARGIN_L, MARGIN_TOP = 52, 130
    CELL_W, CELL_H = 130, 130
    COL_STRIDE, ROW_STRIDE = 139, 145

    by_pos = {(p, s): (num, symbol, lang, project, disc) for p, s, num, symbol, lang, project, disc in CELLS}

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Periodic table of self — 20 projects, 10 languages, 8 disciplines">'
    ]

    # Defs: per-discipline cell gradients only (no canvas bg — blends into page)
    out.append(MOTION_CSS)
    out.append("  <defs>")
    for code in TRACK:
        accent = disc_accent(code, theme)
        tint_opacity = 0.45 if is_dark else 0.35
        out.append(
            f'    <linearGradient id="grad-{code}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="{accent}" stop-opacity="{tint_opacity}"/><stop offset="60%" stop-color="{accent}" stop-opacity="0"/></linearGradient>'
        )
    out.append("  </defs>")

    # Header
    out.append(
        f'  <text x="52" y="52" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="15" fill="{muted}" letter-spacing="3">BUILDER106  //  THE ELEMENTS</text>'
    )
    out.append(
        f'  <text x="52" y="82" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="14" fill="{faded}">20 projects  ·  10 languages  ·  8 disciplines  ·  arranged by language &amp; track</text>'
    )
    out.append(f'  <line x1="52" y1="102" x2="{W - 47}" y2="102" stroke="{chrome_rule}" stroke-width="1"/>')

    # Group labels (1..8 across the top of cell columns)
    for g in range(8):
        cx = MARGIN_L + g * COL_STRIDE + CELL_W // 2
        out.append(
            f'    <text x="{cx}" y="122" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="500" fill="{muted}" text-anchor="middle">{g + 1}</text>'
        )

    # Period labels (1..4 down the left side)
    for p in range(4):
        cy = MARGIN_TOP + p * ROW_STRIDE + CELL_H // 2 + 5
        out.append(
            f'    <text x="36" y="{cy}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" font-weight="500" fill="{muted}" text-anchor="end">{p + 1}</text>'
        )

    # Cells
    for (p, s), (num, symbol, lang, project, disc) in sorted(by_pos.items()):
        accent = disc_accent(disc, theme)
        label_ink = disc_text(disc, theme)
        cardbg = disc_tint(disc, theme)
        x = MARGIN_L + s * COL_STRIDE
        y = MARGIN_TOP + p * ROW_STRIDE
        reveal_delay = (num - 1) * 0.25
        pulse_offset = -((num * 0.21) % 4)
        # Brightness wave: each cell phase-shifted by atomic number, 5s cycle
        wave_offset = -(((num - 1) * 0.25) % 5)
        # Discipline spotlight: 8 disciplines × 2s slot in a 16s cycle
        slot_map = {"Q": 0, "L": 1, "Y": 2, "A": 3, "W": 4, "H": 5, "M": 6, "T": 7}
        slot = slot_map[disc]
        is_now = project == NOW_PROJECT

        out.append(f'  <g class="cell" style="animation-delay: {reveal_delay:.2f}s" transform="translate({x}, {y})">')
        # Spotlight halo — sits behind the card, glows during this discipline's slot
        out.append(
            f'    <rect class="halo" style="animation-delay: {slot * 2}s" x="-4" y="-4" width="138" height="138" rx="8" fill="{accent}"/>'
        )
        # Card
        out.append(
            f'    <rect x="0.5" y="0.5" width="129" height="129" rx="4" fill="{cardbg}" stroke="{border}" stroke-width="1"/>'
        )
        # Gradient overlay with brightness wave
        out.append(
            f'    <rect class="wave" style="animation-delay: {wave_offset:.2f}s" x="0.5" y="0.5" width="129" height="129" rx="4" fill="url(#grad-{disc})"/>'
        )
        label = disc_label(disc)
        disc_x = 106 if is_now else 120
        out.append(
            f'    <rect class="pulse" style="animation-delay: {pulse_offset:.2f}s" x="0.5" y="0.5" width="129" height="3" rx="1.5" fill="{accent}"/>'
        )
        out.append(
            f'    <text x="10" y="22" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="500" fill="{label_ink}">{num:02d}</text>'
        )
        out.append(
            f'    <text x="{disc_x}" y="22" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" font-weight="600" fill="{label_ink}" text-anchor="end">{label}</text>'
        )
        if is_now:
            out.append('    <g transform="translate(118, 14)">')
            out.append(f'      <circle class="now" r="4" fill="{accent}"/>')
            out.append(f'      <circle class="ripple" r="4" fill="{accent}" opacity="0.5"/>')
            out.append("    </g>")
        out.append(
            f'    <text x="65" y="76" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="50" font-weight="700" fill="{fg}" text-anchor="middle" letter-spacing="-1">{symbol}</text>'
        )
        out.append(
            f'    <text x="65" y="101" font-family="-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif" font-size="13" font-weight="600" fill="{cell_text_muted}" text-anchor="middle">{lang}</text>'
        )
        out.append(
            f'    <text x="65" y="120" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="{cell_text_faded}" text-anchor="middle">{project}</text>'
        )
        out.append("  </g>")

    # Legend area
    legend_y = MARGIN_TOP + 4 * ROW_STRIDE + 12
    out.append(
        f'  <line x1="52" y1="{legend_y}" x2="{W - 47}" y2="{legend_y}" stroke="{chrome_rule}" stroke-width="1"/>'
    )
    out.append(
        f'  <text x="52" y="{legend_y + 30}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" fill="{muted}" letter-spacing="2">GROUPS</text>'
    )

    chip_x, chip_y = 65, legend_y + 14
    order = ["Q", "L", "Y", "A", "W", "H", "M", "T"]
    for code in order:
        name = disc_label(code)
        accent = disc_accent(code, theme)
        chip_bg = disc_tint(code, theme)
        out.append(f'  <g transform="translate({chip_x}, {chip_y})">')
        out.append(
            f'    <rect x="0" y="0" width="120" height="26" rx="3" fill="{chip_bg}" stroke="{border}" stroke-width="1"/>'
        )
        out.append(f'    <rect x="0" y="0" width="120" height="3" rx="1.5" fill="{accent}"/>')
        out.append(
            f'    <text x="60" y="17" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" fill="{muted}" text-anchor="middle">{name}</text>'
        )
        out.append("  </g>")
        chip_x += 132

    sym_y = legend_y + 80
    out.append(
        f'  <text x="52" y="{sym_y + 24}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" fill="{muted}" letter-spacing="2">SYMBOLS</text>'
    )
    syms_rows = [
        [
            ("Oc", "OCaml"),
            ("Rs", "Rust"),
            ("C", "C99"),
            ("Py", "Python"),
            ("R", "R"),
            ("Rb", "Ruby"),
        ],
        [
            ("Ts", "TypeScript"),
            ("Sv", "Svelte"),
            ("Sw", "Swift"),
            ("Go", "Go"),
            ("Kt", "Kotlin"),
        ],
    ]
    sym_chip_bg = n["surface"]
    for r_idx, row in enumerate(syms_rows):
        cx = 65 if r_idx == 0 else 150
        cy = sym_y + r_idx * 36
        for sym, name in row:
            out.append(f'  <g transform="translate({cx}, {cy})">')
            out.append(
                f'    <rect x="0" y="0" width="160" height="30" rx="4" fill="{sym_chip_bg}" stroke="{border}" stroke-width="1"/>'
            )
            out.append(
                f'    <text x="80" y="20" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" text-anchor="middle"><tspan font-weight="700" font-size="14" fill="{fg}">{sym}</tspan> &#160;<tspan fill="{muted}">{name}</tspan></text>'
            )
            out.append("  </g>")
            cx += 175

    out.append("</svg>")
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
    base = os.path.dirname(os.path.abspath(__file__))
    if mode == "svgs":
        out = os.path.join(base, "cells")
        write_svgs(out)
        print(f"wrote {len(CELLS) * 2} svgs to {out}/", file=sys.stderr)
    elif mode == "table":
        print_table()
    elif mode == "unified":
        write_unified()
    else:
        print(f"unknown mode: {mode}", file=sys.stderr)
        sys.exit(1)
