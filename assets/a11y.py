#!/usr/bin/env python3
"""Contrast maths shared by make_palette.py and audit.py.

Targets come from WCAG 2.2:
  1.4.6 Contrast (Enhanced), AAA — 7:1 for normal text, 4.5:1 for large text
        (large = 24px+, or 18.66px+ when bold)
  1.4.11 Non-text Contrast, AA  — 3:1 for meaningful graphics and boundaries
"""

import colorsys

AAA_TEXT = 7.0
AAA_LARGE_TEXT = 4.5
NON_TEXT = 3.0


def channels(hex_colour: str) -> tuple[float, float, float]:
    h = hex_colour.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))


def to_hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c * 255))) for c in rgb))


def luminance(hex_colour: str) -> float:
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in channels(hex_colour)]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def mix(fg: str, bg: str, ratio: float) -> str:
    return to_hex(tuple(f * ratio + b * (1 - ratio) for f, b in zip(channels(fg), channels(bg), strict=True)))


def solve(seed: str, backgrounds: list[str], target: float, direction: str) -> str:
    """Shift `seed` lighter or darker, holding its hue and saturation, until it
    clears `target` against every background. Returns the closest colour to the
    seed that qualifies, or the endpoint of the ramp if none does."""
    h, light, s = colorsys.rgb_to_hls(*channels(seed))
    step = -0.005 if direction == "darken" else 0.005
    best = seed
    for i in range(0, 201):
        candidate = to_hex(colorsys.hls_to_rgb(h, min(1.0, max(0.0, light + step * i)), s))
        best = candidate
        if all(contrast(candidate, bg) >= target for bg in backgrounds):
            return candidate
    return best
