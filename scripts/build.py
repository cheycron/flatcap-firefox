#!/usr/bin/env python3
"""Generate the Flatcap 2.0 theme for Firefox (one add-on: Daylight and Slate).

    python3 scripts/build.py              # write manifest.json and the README blocks
    python3 scripts/build.py --check      # fail if generated output is stale, an icon is wrong, or contrast misses a target
    python3 scripts/build.py --sync       # refresh src/ and images/logo.png from ../00-Flatcap, then rebuild
    python3 scripts/build.py --contrast   # print the full contrast report
    python3 scripts/build.py --package    # build, then write the reproducible AMO zip to dist/

Input  : src/theme.json, a versioned copy of the Flatcap 2.0 core (the only source of values).
         scripts/mapping.py, the role mapping (roles only, no hex).
Outputs: manifest.json   "theme" = Daylight (Firefox in the light scheme), "dark_theme" = Slate (dark scheme)
         README.md       only the blocks between <!-- build:NAME --> markers
         dist/flatcap-firefox-<version>.zip   (--package; ignored by git)

No hex value is written by hand. Python 3.10+, standard library only. Output is deterministic.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mapping as M  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "src" / "theme.json"
README = ROOT / "README.md"
MANIFEST = ROOT / "manifest.json"
DIST = ROOT / "dist"
CORE = (ROOT / ".." / "00-Flatcap").resolve()
SYNCED = [("src/theme.json", "src/theme.json"), ("src/logo.svg", "src/logo.svg"), ("images/logo.png", "images/logo.png")]

MODES = ("slate", "daylight")
NAME = {"slate": "Flatcap Slate", "daylight": "Flatcap Daylight"}
ICON_SIZES = (48, 96, 128)
STRICT_MIN_VERSION = "109.0"   # Manifest V3 in Firefox starts at 109; dark_theme (68) and color_scheme (100) are older
DESCRIPTION = ("Quiet precision for Firefox. Flatcap Slate in dark mode and Flatcap Daylight in light mode, "
               "following your system.")
AUTHOR = "Leonardo Anibal Chocron"
HOMEPAGE = "https://github.com/cheycron/flatcap-firefox"
GECKO_ID = "flatcap-theme@cheycron.com"
HEX6 = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------
def load() -> dict:
    return json.loads(THEME.read_text(encoding="utf-8"))


def role(theme: dict, mode: str, name: str) -> str:
    value = theme["themes"][mode].get(name)
    if value is None:
        raise SystemExit(f"error: unknown Flatcap role {name!r}")
    return value


def colors(theme: dict, mode: str) -> dict[str, str]:
    out: dict[str, str] = {}
    owner: dict[str, str] = {}
    for area, entries in M.COLORS:
        for key, name, _note in entries:
            if key in out:
                raise SystemExit(f"error: Firefox key {key!r} assigned twice ({owner[key]} and {area})")
            out[key] = role(theme, mode, name)
            owner[key] = area
    return out


def theme_object(theme: dict, mode: str) -> dict:
    return {"colors": colors(theme, mode), "properties": {"color_scheme": M.COLOR_SCHEME[mode]}}


def dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def manifest(theme: dict) -> dict:
    if len(DESCRIPTION) > 132:
        raise SystemExit("error: description is longer than the 132 characters AMO shows")
    out = {
        "manifest_version": 3,
        "version": theme["version"],
        "name": "Flatcap",
        "description": DESCRIPTION,
        "author": AUTHOR,
        "homepage_url": HOMEPAGE,
        "icons": {str(s): f"icons/icon-{s}.png" for s in ICON_SIZES},
        "browser_specific_settings": {"gecko": {"id": GECKO_ID, "strict_min_version": STRICT_MIN_VERSION}},
    }
    for mode in ("daylight", "slate"):
        out[M.MANIFEST_KEY[mode]] = theme_object(theme, mode)
    return out


# ---------------------------------------------------------------------------
# Contrast (WCAG 2.x relative luminance, no rounding before comparing)
# ---------------------------------------------------------------------------
def lum(h: str) -> float:
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a: str, b: str) -> float:
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


# (group, label, foreground key, background key, target). Keys are Firefox keys of the manifest.
# Targets follow docs/accessibility.md: 7 primary text, 5 informative text and icons, 4.5 selection
# label, 3 functional boundaries, 1 = informational only (fill against fill, no requirement).
CHECKS = [
    ("Tabs", "inactive tab text on the tab strip", "tab_background_text", "frame", 5),
    ("Tabs", "inactive tab text, window not focused", "tab_background_text", "frame_inactive", 5),
    ("Tabs", "selected tab text", "tab_text", "tab_selected", 7),
    ("Tabs", "selected tab indicator vs tab strip", "tab_line", "frame", 3),
    ("Tabs", "selected tab indicator vs selected tab", "tab_line", "tab_selected", 3),
    ("Tabs", "loading indicator vs tab strip", "tab_loading", "frame", 3),
    ("Tabs", "loading indicator vs selected tab", "tab_loading", "tab_selected", 3),
    ("Tabs", "selected tab fill vs tab strip (informational: the indicator carries it)", "tab_selected", "frame", 1),
    ("Toolbar text and icons", "bookmarks text on toolbar", "toolbar_text", "toolbar", 7),
    ("Toolbar text and icons", "bookmarks text on hovered button", "toolbar_text", "button_background_hover", 7),
    ("Toolbar text and icons", "bookmarks text on pressed button", "toolbar_text", "button_background_active", 7),
    ("Toolbar text and icons", "icons on toolbar", "icons", "toolbar", 5),
    ("Toolbar text and icons", "icons on tab strip", "icons", "frame", 5),
    ("Toolbar text and icons", "icons on hovered button", "icons", "button_background_hover", 5),
    ("Toolbar text and icons", "icons on pressed button", "icons", "button_background_active", 5),
    ("Toolbar text and icons", "attention icons on toolbar", "icons_attention", "toolbar", 5),
    ("Toolbar text and icons", "attention icons on hovered button", "icons_attention", "button_background_hover", 5),
    ("Toolbar text and icons", "attention icons on pressed button", "icons_attention", "button_background_active", 5),
    ("URL bar", "field text", "toolbar_field_text", "toolbar_field", 7),
    ("URL bar", "focused field text", "toolbar_field_text_focus", "toolbar_field_focus", 7),
    ("URL bar", "selected text in the field", "toolbar_field_highlight_text", "toolbar_field_highlight", 4.5),
    ("URL bar", "field outline vs toolbar", "toolbar_field_border", "toolbar", 3),
    ("URL bar", "field outline vs field", "toolbar_field_border", "toolbar_field", 3),
    ("URL bar", "focus indicator vs toolbar", "toolbar_field_border_focus", "toolbar", 3),
    ("URL bar", "focus indicator vs focused field", "toolbar_field_border_focus", "toolbar_field_focus", 3),
    ("Popups", "popup text", "popup_text", "popup", 7),
    ("Popups", "highlighted item text", "popup_highlight_text", "popup_highlight", 7),
    ("Popups", "popup edge (decorative, informational)", "popup_border", "popup", 1),
    ("Sidebar", "sidebar text", "sidebar_text", "sidebar", 7),
    ("Sidebar", "highlighted row text", "sidebar_highlight_text", "sidebar_highlight", 7),
    ("New tab page", "page text", "ntp_text", "ntp_background", 7),
    ("New tab page", "card text", "ntp_text", "ntp_card_background", 7),
]


def checks(theme: dict, mode: str) -> list[dict]:
    c = colors(theme, mode)
    rows = []
    for group, label, fg, bg, target in CHECKS:
        for k in (fg, bg):
            if k not in c:
                raise SystemExit(f"error: contrast check references unknown key {k!r}")
        rows.append({"group": group, "label": label, "fg": c[fg], "bg": c[bg], "target": target,
                     "ratio": ratio(c[fg], c[bg])})
    return rows


def failures(theme: dict) -> list[str]:
    return [f"{NAME[m]}: {r['group']}: {r['label']} {r['ratio']:.2f}:1 < {r['target']:g}:1"
            for m in MODES for r in checks(theme, m) if r["ratio"] + 1e-9 < r["target"]]


def contrast_report(theme: dict) -> str:
    lines = []
    for mode in MODES:
        lines.append(f"[{NAME[mode]}]")
        group = None
        for r in checks(theme, mode):
            if r["group"] != group:
                group = r["group"]
                lines.append(f"  {group}")
            flag = "" if r["ratio"] + 1e-9 >= r["target"] else "  <-- below target"
            lines.append(f"    {r['label']:<72}{r['ratio']:6.2f}:1  (target {r['target']:g}){flag}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# README blocks
# ---------------------------------------------------------------------------
def md_mapping(theme: dict) -> str:
    rows = ["| Area | Firefox key | Flatcap role | Slate | Daylight | Paints |", "| :--- | :--- | :--- | :--- | :--- | :--- |"]
    total = 0
    for area, entries in M.COLORS:
        for i, (key, name, note) in enumerate(entries):
            rows.append(f"| {area if i == 0 else ''} | `{key}` | `{name}` | `{role(theme, 'slate', name)}` | "
                        f"`{role(theme, 'daylight', name)}` | {note} |")
            total += 1
    rows += ["", f"{total} `theme.colors` keys per mode, plus `properties.color_scheme` (`dark` in Slate, `light` in Daylight)."]
    return "\n".join(rows)


def md_contrast(theme: dict) -> str:
    S, D = checks(theme, "slate"), checks(theme, "daylight")
    groups: dict[str, list[tuple[dict, dict]]] = {}
    for a, b in zip(S, D):
        groups.setdefault(a["group"], []).append((a, b))
    rows = ["| Check | Pairs | Lowest Slate | Lowest Daylight | Target | Result |",
            "| :--- | ---: | ---: | ---: | ---: | :--- |"]
    for g, pairs in groups.items():
        real = [(a, b) for a, b in pairs if a["target"] > 1]
        if not real:
            continue
        targets = sorted({a["target"] for a, _ in real})
        s, d = min(a["ratio"] for a, _ in real), min(b["ratio"] for _, b in real)
        ok = all(a["ratio"] + 1e-9 >= a["target"] and b["ratio"] + 1e-9 >= b["target"] for a, b in real)
        rows.append(f"| {g} | {len(real)} | {s:.2f}:1 | {d:.2f}:1 | " + "/".join(f"{t:g}" for t in targets)
                    + f":1 | {'met' if ok else 'not met'} |")
    info = [(a, b) for a, b in zip(S, D) if a["target"] <= 1]
    rows += ["", "Informational pairs (decorative fills and edges, no target):", "",
             "| Pair | Slate | Daylight |", "| :--- | ---: | ---: |"]
    rows += [f"| {a['label']} | {a['ratio']:.2f}:1 | {b['ratio']:.2f}:1 |" for a, b in info]
    return "\n".join(rows)


README_BLOCKS = {"mapping": md_mapping, "contrast": md_contrast}


def render_readme(theme: dict) -> str:
    text = README.read_text(encoding="utf-8")
    for name, fn in README_BLOCKS.items():
        pat = re.compile(rf"(<!-- build:{name} -->)\n.*?(<!-- /build:{name} -->)", re.S)
        if not pat.search(text):
            raise SystemExit(f"error: README.md is missing the build:{name} markers")
        text = pat.sub(lambda m: m.group(1) + "\n" + fn(theme) + "\n" + m.group(2), text)
    return text


# ---------------------------------------------------------------------------
# Validation and packaging
# ---------------------------------------------------------------------------
def png_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def validate(theme: dict) -> list[str]:
    errs = []
    for mode in MODES:
        for key, value in colors(theme, mode).items():
            if not HEX6.match(value):
                errs.append(f"{NAME[mode]}: {key} is not a #RRGGBB color ({value!r})")
    for s in ICON_SIZES:
        p = ROOT / "icons" / f"icon-{s}.png"
        size = png_size(p) if p.is_file() else None
        if size != (s, s):
            errs.append(f"{p.relative_to(ROOT)} must be a {s}x{s} PNG (run python3 scripts/render_icons.py)")
    return errs


def package_files() -> list[str]:
    files = ["manifest.json", "LICENSE"] + [f"icons/icon-{s}.png" for s in ICON_SIZES]
    return sorted(files)


def package(version: str) -> Path:
    DIST.mkdir(exist_ok=True)
    target = DIST / f"flatcap-firefox-{version}.zip"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in package_files():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))  # fixed: same bytes on every run
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            z.writestr(info, (ROOT / name).read_bytes(), compresslevel=9)
    return target


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if generated outputs are stale")
    ap.add_argument("--contrast", action="store_true", help="print the contrast report and exit")
    ap.add_argument("--package", action="store_true", help="build, then write the AMO zip to dist/")
    ap.add_argument("--sync", nargs="?", const=str(CORE), metavar="PATH",
                    help="copy theme.json, logo.svg and logo.png from the core checkout (default ../00-Flatcap)")
    args = ap.parse_args()

    if args.sync:
        core = Path(args.sync)
        for src, dst in SYNCED:
            if not (core / src).is_file():
                print(f"error: {core / src} not found", file=sys.stderr)
                return 2
            shutil.copyfile(core / src, ROOT / dst)
            print(f"synced {src}")
        print("note: run python3 scripts/render_icons.py if the logo changed")

    theme = load()
    if not str(theme.get("version", "")).startswith("2."):
        print(f"error: expected Flatcap 2.x theme.json, got {theme.get('version')}", file=sys.stderr)
        return 2
    errs = validate(theme)
    if errs:
        print("\n".join("error: " + e for e in errs), file=sys.stderr)
        return 2
    if args.contrast:
        print(contrast_report(theme))
        return 0
    upstream = CORE / "src" / "theme.json"
    if upstream.is_file() and upstream.read_bytes() != THEME.read_bytes():
        print("note: src/theme.json differs from ../00-Flatcap (run --sync to refresh)", file=sys.stderr)

    outs = {MANIFEST: dumps(manifest(theme)), README: render_readme(theme)}
    stale = []
    for path, text in outs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(path.name)
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
    fails = failures(theme)
    if args.check:
        if stale:
            print("stale: " + ", ".join(stale) + " (run python3 scripts/build.py)", file=sys.stderr)
        if fails:
            print("contrast below target:\n  " + "\n  ".join(fails), file=sys.stderr)
        if stale or fails:
            return 1
        print("ok: generated files are up to date and every contrast check meets its target")
    elif fails:
        print("warning: contrast below target (see --contrast):\n  " + "\n  ".join(fails), file=sys.stderr)
        if args.package:
            return 1
    if args.package:
        target = package(theme["version"])
        print(f"packaged {target.relative_to(ROOT)} ({target.stat().st_size} bytes): " + ", ".join(package_files()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
