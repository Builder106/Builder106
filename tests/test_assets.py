import importlib.util
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


ASSETS = Path(__file__).parents[1] / "assets"
sys.path.insert(0, str(ASSETS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, ASSETS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def a11y():
    return load("a11y")


@pytest.fixture(scope="module")
def cells():
    return load("gen_cells")


@pytest.fixture(scope="module")
def palette():
    return load("make_palette")


@pytest.fixture(scope="module")
def audit():
    return load("audit")


def test_a11y_helpers_cover_colour_math(a11y):
    assert a11y.channels("#123456") == pytest.approx((18 / 255, 52 / 255, 86 / 255))
    assert a11y.to_hex((0.0, 0.5, 1.0)) == "#0080ff"
    assert a11y.luminance("#ffffff") == pytest.approx(1.0)
    assert a11y.contrast("#000000", "#ffffff") == pytest.approx(21.0)
    assert a11y.mix("#000000", "#ffffff", 0.25) == "#bfbfbf"
    assert a11y.solve("#808080", ["#ffffff"], 7, "darken") != "#808080"
    assert a11y.solve("#808080", ["#000000"], 7, "lighten") != "#808080"
    assert a11y.solve("#808080", ["#ffffff"], 100, "darken") != "#808080"


def test_cell_helpers_and_svg_variants(cells):
    assert cells.disc_label("A") == "Analyst"
    assert cells.disc_accent("A", "dark").startswith("#")
    assert cells.disc_tint("A", "light").startswith("#")
    assert cells.disc_text("A", "dark").startswith("#")
    for theme in ("dark", "light"):
        svg = cells.cell_svg(theme, 10, "Ts", "TypeScript", "Demo", "W")
        assert 'role="img"' in svg
        assert "Demo" in svg
    assert "NOW" not in cells.cell_svg("dark", 10, "Ts", "TypeScript", "Demo", "W")


def test_cell_generation_and_tables(cells, tmp_path, capsys):
    cells.write_svgs(tmp_path)
    assert len(list(tmp_path.glob("*.svg"))) == len(cells.CELLS) * 2
    cells.print_table()
    table = capsys.readouterr().out
    assert table.startswith("<table")
    assert "github.com/Builder106" in table


def test_palette_build_and_report(palette, capsys):
    assert palette.seed(120, "light").startswith("#")
    result = palette.build()
    assert set(result["neutral"]) == {"light", "dark"}
    assert set(result["tracks"]) == set(palette.ORDER)
    palette.report(result)
    assert "light:" in capsys.readouterr().out


def test_audit_helpers_and_svg_paths(audit, tmp_path):
    assert audit.is_large(24, "400")
    assert audit.is_large(18.66, "bold")
    assert not audit.is_large(18.65, "bold")
    assert not audit.is_large(20, "400")

    svg = tmp_path / "sample-light.svg"
    svg.write_text(
        '''<svg xmlns="http://www.w3.org/2000/svg">
          <style>.x { fill: #000000; fill: #ffffff; }</style>
          <g font-size="24" font-weight="700">
            <rect width="129" height="129" fill="#ffffff"/>
          <text fill="#ffffff">large</text>
          </g>
          <rect fill="#fefefe"/>
          <linearGradient><stop stop-color="#ffffff" stop-opacity="1"/><stop stop-color="#000000" stop-opacity="0"/></linearGradient>
          <path stroke="#eeeeee"/>
          <path stroke="#d0d7de"/>
          <g><text fill="url(#animated)">animated</text></g>
          <animate attributeName="x" repeatCount="indefinite"/>
        </svg>''',
        encoding="utf-8",
    )
    fills = audit.backgrounds(svg, "light")
    assert "#ffffff" in fills
    assert "#fefefe" in fills
    assert audit.nearest_background(ET.Element("text"), svg, "dark") == "#0d1117"
    assert audit.nearest_background(ET.Element("text", {"data-bg": "#123456"}), svg, "dark") == "#123456"

    problems = audit.audit_svg(svg)
    assert any("animated fill" in problem for problem in problems)
    assert any("stroke" in problem for problem in problems)
    assert any("SMIL" in problem for problem in problems)


def test_audit_readme_and_main(audit, tmp_path, monkeypatch, capsys):
    readme = tmp_path / "README.md"
    readme.write_text(
        '<img src="x"> ![badge](https://img.shields.io/badge/test-777777)',
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "README", readme)
    problems = audit.audit_readme()
    assert any("no alt" in problem for problem in problems)
    assert any("badge" in problem for problem in problems)

    monkeypatch.setattr(audit, "audit_svg", lambda path: [])
    monkeypatch.setattr(audit, "audit_readme", lambda: [])
    assert audit.main() == 0
    assert "PASS" in capsys.readouterr().out

    monkeypatch.setattr(audit, "audit_svg", lambda path: ["issue"])
    monkeypatch.setattr(audit, "audit_readme", lambda: ["readme issue"])
    assert audit.main() == 1
    assert "issue(s)" in capsys.readouterr().out


def test_build_main_success_and_failure(monkeypatch, tmp_path, capsys):
    build = load("build")
    monkeypatch.setattr(build, "__file__", str(tmp_path / "build.py"))
    calls = []

    monkeypatch.setattr(build, "run", lambda command, cwd=None: calls.append((command, cwd)) or True)
    build.main()
    assert len(calls) == 2
    assert "Build complete" in capsys.readouterr().out

    monkeypatch.setattr(build, "run", lambda command, cwd=None: False)
    with pytest.raises(SystemExit, match="1"):
        build.main()
    assert "Build failed" in capsys.readouterr().err


def test_unified_generation_and_write_unified(cells, tmp_path, monkeypatch):
    for theme in ("dark", "light"):
        svg = cells.unified_svg(theme)
        assert svg.startswith("<svg")
        assert "BUILDER106" in svg
        assert "SYMBOLS" in svg
        assert "class=\"now\"" in svg

    cells.write_unified()


def test_build_run_reports_success_and_failure(monkeypatch):
    build = load("build")
    calls = []

    class Result:
        stdout = "out"
        stderr = "err"
        returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (calls.append(args) or Result()))
    assert build.run(["echo", "ok"])
    Result.returncode = 1
    assert not build.run(["false"])
    assert len(calls) == 2
