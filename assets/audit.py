#!/usr/bin/env python3
"""Check the profile's assets against WCAG 2.2.

Walks the shipped SVGs and the README rather than the palette, so it catches a
colour that drifted out of the lookup table as well as one that was never in it.

    python3 audit.py        # from the assets/ directory
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from a11y import AAA_LARGE_TEXT, AAA_TEXT, NON_TEXT, contrast

SVG = "{http://www.w3.org/2000/svg}"
ASSETS = Path(__file__).parent
README = ASSETS.parent / "README.md"

# Backgrounds a given file's text can sit on. The table has no canvas of its
# own — it is drawn straight onto the GitHub page — so its page colours are
# GitHub's, not ours.
PAGE = {"light": "#ffffff", "dark": "#0d1117"}

# Colours that are decoration only, and so exempt from 1.4.11.
DECORATIVE = {"#d0d7de", "#1f2630", "#1c2530"}


def is_large(size: float, weight: str) -> bool:
    return size >= 24 or (size >= 18.66 and weight in {"600", "700", "bold"})


def backgrounds(path: Path, theme: str) -> set[str]:
    """Every fill that text in this file can land on."""
    root = ET.parse(path).getroot()
    fills = {PAGE[theme]}
    for el in root.iter():
        fill = el.get("fill", "")
        if fill.startswith("#") and el.tag in (f"{SVG}rect",):
            fills.add(fill.lower())
    # gradient stops (the hero/banner canvas)
    for stop in root.iter(f"{SVG}stop"):
        colour = stop.get("stop-color", "")
        if colour.startswith("#") and stop.get("stop-opacity") != "0":
            fills.add(colour.lower())
    return fills


def nearest_background(el, path: Path, theme: str) -> str:
    """Worst-case background for an element: for cell text it is the card tint
    it sits inside, otherwise the page."""
    parent_fill = el.get("data-bg")
    return parent_fill or PAGE[theme]


def audit_svg(path: Path) -> list[str]:
    theme = "dark" if "dark" in path.name else "light"
    tree = ET.parse(path)
    root = tree.getroot()
    problems = []

    # Map each group's card fill so text inside it is checked against the card,
    # not the page.
    for group in root.iter(f"{SVG}g"):
        card = None
        for rect in group.iter(f"{SVG}rect"):
            fill = rect.get("fill", "")
            if fill.startswith("#") and rect.get("width") in {"129", "120", "160"}:
                card = fill
                break
        for text in group.iter(f"{SVG}text"):
            if card:
                text.set("data-bg", card)

    # SVG text inherits typography from its ancestors, so resolve it downward
    # before deciding whether a label counts as large text.
    inherited = {}
    for parent in root.iter():
        for child in parent:
            style = dict(inherited.get(id(parent), {}))
            for attr in ("font-size", "font-weight"):
                if parent.get(attr):
                    style[attr] = parent.get(attr)
            inherited[id(child)] = style

    for text in root.iter(f"{SVG}text"):
        fill = (text.get("fill") or "").lower()
        if not fill.startswith("#"):
            continue  # animated fills are checked via the stylesheet below
        from_parent = inherited.get(id(text), {})
        size = float(text.get("font-size") or from_parent.get("font-size", "16"))
        weight = text.get("font-weight") or from_parent.get("font-weight", "400")
        bg = nearest_background(text, path, theme)
        target = AAA_LARGE_TEXT if is_large(size, weight) else AAA_TEXT
        ratio = contrast(fill, bg)
        content = (text.text or "").strip()[:24]
        if ratio < target:
            problems.append(f"  1.4.6 text {fill} on {bg} = {ratio:.2f}:1 (need {target}) — {size:g}px {content!r}")

    # Colours declared in the stylesheet (the hero's cycling track labels).
    style = root.find(f".//{SVG}style")
    if style is not None and style.text:
        page = min(
            (c for c in backgrounds(path, theme)),
            key=lambda c: abs(contrast(c, PAGE[theme]) - 1),
        )
        for colour in sorted(set(re.findall(r"fill:\s*(#[0-9a-fA-F]{6})", style.text))):
            ratio = contrast(colour, page)
            if ratio < AAA_LARGE_TEXT:  # these labels are 32px bold
                problems.append(f"  1.4.6 animated fill {colour} on {page} = {ratio:.2f}:1 (need 4.5)")

    # Meaningful graphics: card borders, hairlines, accent bars.
    for el in root.iter():
        stroke = (el.get("stroke") or "").lower()
        if stroke.startswith("#") and stroke not in DECORATIVE:
            ratio = contrast(stroke, PAGE[theme])
            if ratio < NON_TEXT:
                problems.append(f"  1.4.11 stroke {stroke} on {PAGE[theme]} = {ratio:.2f}:1 (need 3.0)")

    # Motion: anything that loops must be stoppable.
    source = path.read_text()
    loops = 'repeatCount="indefinite"' in source or "infinite" in source
    if loops and "prefers-reduced-motion" not in source:
        problems.append("  2.2.2 loops forever with no prefers-reduced-motion fallback")
    if "<animate" in source:
        problems.append("  2.2.2 uses SMIL <animate>, which prefers-reduced-motion cannot stop")

    return problems


def audit_readme() -> list[str]:
    problems = []
    text = README.read_text()
    for colour in re.findall(r"img\.shields\.io/badge/[^)\s]*?-([0-9a-fA-F]{6})(?:\?|\))", text):
        ratio = contrast("#" + colour, "#ffffff")
        if ratio < AAA_TEXT:
            problems.append(f"  1.4.6 badge #{colour} with white text = {ratio:.2f}:1 (need 7.0)")
    for img in re.findall(r"<img\s[^>]*>", text):
        if "alt=" not in img:
            problems.append(f"  1.1.1 <img> with no alt: {img[:60]}")
    return problems


def main() -> int:
    failures = 0
    for name in (
        "hero-light.svg",
        "hero-dark.svg",
        "table-light.svg",
        "table-dark.svg",
        "banner-light.svg",
        "banner-dark.svg",
    ):
        problems = audit_svg(ASSETS / name)
        print(f"{name}: {'PASS' if not problems else str(len(problems)) + ' issue(s)'}")
        for line in problems:
            print(line)
        failures += len(problems)

    problems = audit_readme()
    print(f"README.md: {'PASS' if not problems else str(len(problems)) + ' issue(s)'}")
    for line in problems:
        print(line)
    failures += len(problems)

    print(f"\n{failures} issue(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
