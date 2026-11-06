# Flatcap for Firefox

![Version](https://img.shields.io/badge/version-2.0.0-blueviolet) ![Firefox](https://img.shields.io/badge/Firefox-%E2%89%A5109-orange) ![License](https://img.shields.io/badge/license-MIT-blue) [![AMO](https://img.shields.io/badge/Firefox%20Add--ons-Flatcap-ff7139)](https://addons.mozilla.org/en-US/firefox/addon/flatcap/)

<p align="center">
  <img src="https://raw.githubusercontent.com/cheycron/flatcap-firefox/main/images/screenshot-slate.png" alt="Flatcap Slate in Firefox: tabs, toolbar, focused URL bar with suggestions and the new tab page" width="100%">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/cheycron/flatcap-firefox/main/images/screenshot-daylight.png" alt="Flatcap Daylight in Firefox: the same window in the light theme" width="100%">
</p>

<p align="center"><sub>Flatcap Slate (dark) above, Flatcap Daylight (light) below.</sub></p>

**Flatcap for Firefox** brings the Flatcap visual system to the browser frame: matte graphite surfaces, one mineral-blue accent, and an interface that stays in the background.

> The interface organizes. Content takes the foreground. Color informs.

## Quiet precision

[Flatcap](https://github.com/cheycron/flatcap-theme) is a semantic visual system. Colors are named for **what they do**, and the two modes share roles rather than values: Daylight is not an inverted Slate. The tab strip is the canvas, the selected tab continues the toolbar, the URL bar is recessed and the suggestions panel is the only floating layer.

## Install

Install **Flatcap** from [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/flatcap/), or temporarily from this repo: `python3 scripts/build.py --package`, then `about:debugging` > This Firefox > Load Temporary Add-on and pick `manifest.json`.

## Slate and Daylight in one add-on

The add-on is a single static theme. `theme` holds **Daylight** and `dark_theme` holds **Slate**; Firefox uses `dark_theme` when its color scheme is dark. Each mode also sets `properties.color_scheme` explicitly, so the page `prefers-color-scheme` follows the theme rather than the OS.

By default the mode follows your operating system's light or dark setting, and it switches live when that setting changes. Keep Flatcap enabled as the theme in **Add-ons and themes > Themes**.

Sources: [MDN `dark_theme`](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/dark_theme), [MDN `theme`](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/manifest.json/theme), [Browser Compat Data](https://github.com/mdn/browser-compat-data/blob/main/webextensions/manifest/dark_theme.json).

## How colors are chosen

Every value comes from the Flatcap 2.0 core (`src/theme.json`) and is assigned by role in `scripts/mapping.py`, never by palette position. Each key per mode:

<!-- build:mapping -->
| Area | Firefox key | Flatcap role | Slate | Daylight | Paints |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Window and tabs | `frame` | `bg.canvas` | `#191D22` | `#F3F5F7` | Window frame and tab strip backdrop |
|  | `frame_inactive` | `bg.canvas` | `#191D22` | `#F3F5F7` | Same backdrop when the window is not focused |
|  | `tab_background_text` | `text.secondary` | `#AEB8C4` | `#465463` | Text of the tabs that are not selected |
|  | `tab_text` | `text.primary` | `#D5DBE3` | `#28313B` | Text of the selected tab |
|  | `tab_selected` | `bg.surface` | `#20252B` | `#FAFBFC` | Selected tab; continues the toolbar below it |
|  | `tab_line` | `accent.fg` | `#9BBFDF` | `#285D85` | Persistent indicator on the selected tab |
|  | `tab_loading` | `accent.fg` | `#9BBFDF` | `#285D85` | Tab loading indicator |
| Toolbar | `toolbar` | `bg.surface` | `#20252B` | `#FAFBFC` | Navigation bar, bookmarks bar and find bar |
|  | `toolbar_text` | `text.primary` | `#D5DBE3` | `#28313B` | Bookmarks and find bar text |
|  | `icons` | `text.secondary` | `#AEB8C4` | `#465463` | Toolbar icons |
|  | `icons_attention` | `accent.fg` | `#9BBFDF` | `#285D85` | Starred bookmark, finished download |
|  | `button_background_hover` | `bg.hover` | `#323A43` | `#E6EBF0` | Toolbar button on hover |
|  | `button_background_active` | `bg.selected` | `#263E53` | `#DCE9F4` | Toolbar button pressed or open |
|  | `toolbar_top_separator` | `border.subtle` | `#3D4652` | `#D2D9E0` | Line above the toolbar |
|  | `toolbar_bottom_separator` | `border.subtle` | `#3D4652` | `#D2D9E0` | Line between the toolbar and the page |
|  | `toolbar_vertical_separator` | `border.subtle` | `#3D4652` | `#D2D9E0` | Separators in the bookmarks bar |
| URL bar and find field | `toolbar_field` | `bg.canvas` | `#191D22` | `#F3F5F7` | Field background, recessed into the toolbar |
|  | `toolbar_field_text` | `text.primary` | `#D5DBE3` | `#28313B` | Field text |
|  | `toolbar_field_border` | `border.control` | `#8593A5` | `#6C7A89` | Functional outline that identifies the field |
|  | `toolbar_field_focus` | `bg.raised` | `#292F36` | `#FFFFFF` | Focused field; joins the floating suggestions panel |
|  | `toolbar_field_text_focus` | `text.primary` | `#D5DBE3` | `#28313B` | Focused field text |
|  | `toolbar_field_border_focus` | `focus.ring` | `#B0D2F0` | `#285D85` | Focus indicator of the field |
|  | `toolbar_field_highlight` | `selection.bg` | `#3C546B` | `#C8DDF0` | Selected text in the field (text selection) |
|  | `toolbar_field_highlight_text` | `selection.fg` | `#D5DBE3` | `#28313B` | Selected text ink in the field |
| Popups and panels | `popup` | `bg.raised` | `#292F36` | `#FFFFFF` | Menus, panels and the URL suggestions (Firefox 156 and earlier) |
|  | `popup_text` | `text.primary` | `#D5DBE3` | `#28313B` | Popup text |
|  | `popup_border` | `border.subtle` | `#3D4652` | `#D2D9E0` | Popup edge |
|  | `popup_highlight` | `bg.selected` | `#263E53` | `#DCE9F4` | Keyboard-highlighted popup item |
|  | `popup_highlight_text` | `text.primary` | `#D5DBE3` | `#28313B` | Text of the highlighted popup item |
| Sidebar | `sidebar` | `bg.surface` | `#20252B` | `#FAFBFC` | Sidebar background |
|  | `sidebar_text` | `text.primary` | `#D5DBE3` | `#28313B` | Sidebar text |
|  | `sidebar_border` | `border.subtle` | `#3D4652` | `#D2D9E0` | Sidebar edge and splitter |
|  | `sidebar_highlight` | `bg.selected` | `#263E53` | `#DCE9F4` | Highlighted row in the built-in sidebars |
|  | `sidebar_highlight_text` | `text.primary` | `#D5DBE3` | `#28313B` | Text of the highlighted row |
| New tab page | `ntp_background` | `bg.canvas` | `#191D22` | `#F3F5F7` | Page background |
|  | `ntp_text` | `text.primary` | `#D5DBE3` | `#28313B` | Page text |
|  | `ntp_card_background` | `bg.surface` | `#20252B` | `#FAFBFC` | Cards and shortcut tiles (Firefox 157 and later) |

37 `theme.colors` keys per mode, plus `properties.color_scheme` (`dark` in Slate, `light` in Daylight).
<!-- /build:mapping -->

## Accessibility

`scripts/build.py` computes WCAG 2.x contrast from the theme values and fails if a pair misses its target.

<!-- build:contrast -->
| Check | Pairs | Lowest Slate | Lowest Daylight | Target | Result |
| :--- | ---: | ---: | ---: | ---: | :--- |
| Tabs | 7 | 8.02:1 | 6.42:1 | 3/5/7:1 | met |
| Toolbar text and icons | 10 | 5.51:1 | 5.68:1 | 5/7:1 | met |
| URL bar | 7 | 4.93:1 | 4.02:1 | 3/4.5/7:1 | met |
| Popups | 2 | 7.95:1 | 10.68:1 | 7:1 | met |
| Sidebar | 2 | 7.95:1 | 10.68:1 | 7:1 | met |
| New tab page | 2 | 11.07:1 | 12.06:1 | 7:1 | met |

Informational pairs (decorative fills and edges, no target):

| Pair | Slate | Daylight |
| :--- | ---: | ---: |
| selected tab fill vs tab strip (informational: the indicator carries it) | 1.10:1 | 1.05:1 |
| popup edge (decorative, informational) | 1.41:1 | 1.42:1 |
<!-- /build:contrast -->

Known limits:

- **Computed, not sampled.** Ratios come from the values, not from every rendered widget. Firefox derives some states (hover overlays, disabled items, inactive windows) itself, and web content is outside the theme.
- **Transparency and overlays** that Firefox draws over theme colors are not modelled.
- **Decorative edges** (popup border, selected tab against the strip) are informational; the tab line carries the selected state.
- **Version differences.** `ntp_card_background` applies from Firefox 157 and later; on 156 and earlier the URL suggestions use `popup`. Other keys may be ignored on older versions; the theme degrades to Firefox defaults for them.

## Compatibility

- `strict_min_version` is **109.0** (Manifest V3 in Firefox). This release was checked on Firefox **159** (Linux), in both modes and with a live mode change, and on the author's desktop Firefox. Older versions were not tested.
- Firefox for Android was not tested.

## How it is built

`manifest.json` and the generated README blocks come from a script; do not edit them by hand.

```sh
python3 scripts/build.py            # regenerate manifest.json and README blocks
python3 scripts/build.py --check    # fail if generated files are stale or contrast misses a target
python3 scripts/build.py --sync     # copy theme.json from ../00-Flatcap, then rebuild
python3 scripts/build.py --contrast # print the full contrast report
python3 scripts/build.py --package  # write dist/flatcap-firefox-2.0.0.zip (fixed order, dates and modes)
python3 scripts/render_icons.py     # derive icons/ from src/logo.svg (--check to verify)
```

Needs Python 3.10+. Icons use the Flatcap Mineral mark.

## Upgrading from v1

The add-on ID (`flatcap-theme@cheycron.com`) is unchanged, so installed copies update in place. v1 was a single dark Nord-like palette; it is now Slate, and a Daylight mode appears when Firefox is in light mode.

## License

MIT. The cap drawing in the icon derives from third-party artwork (Vexels, [terms](https://vexels.com/terms-and-conditions/)) and is not relicensed by MIT.

## Support

If Flatcap makes your workspace calmer, you can support its development.

<p align="center">
  <a href="https://www.buymeacoffee.com/cheycron">
    <img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me a Coffee">
  </a>
</p>
