"""Role mapping for the Flatcap 2.0 Firefox theme.

Data only. Every color is a Flatcap role from src/theme.json (no hex here). Roles are chosen by the
function of the Firefox surface, never by the position of a color in the v1 palette:

    bg.canvas   the recessed backdrop behind the chrome and the new-tab page (the "main area")
    bg.surface  navigation chrome: toolbar, selected tab, sidebar, new-tab cards
    bg.raised   only what floats: popup panels and the expanded URL bar
    bg.hover / bg.selected   neutral hover, and persistent selection / pressed state

build.py rejects a key assigned twice and a role that is not in the core.

Firefox keys that are deliberately not used (see README, "Compatibility"):
    tab_background_separator, toolbar_field_separator   ignored since Firefox 89
    frame_incognito, frame_incognito_inactive           not supported by Firefox
    ntp_header, ntp_link                                not supported by Firefox
"""

# (area, [(firefox key, role, what it paints)])
COLORS = [
    ("Window and tabs", [
        ("frame", "bg.canvas", "Window frame and tab strip backdrop"),
        ("frame_inactive", "bg.canvas", "Same backdrop when the window is not focused"),
        ("tab_background_text", "text.secondary", "Text of the tabs that are not selected"),
        ("tab_text", "text.primary", "Text of the selected tab"),
        ("tab_selected", "bg.surface", "Selected tab; continues the toolbar below it"),
        ("tab_line", "accent.fg", "Persistent indicator on the selected tab"),
        ("tab_loading", "accent.fg", "Tab loading indicator"),
    ]),
    ("Toolbar", [
        ("toolbar", "bg.surface", "Navigation bar, bookmarks bar and find bar"),
        ("toolbar_text", "text.primary", "Bookmarks and find bar text"),
        ("icons", "text.secondary", "Toolbar icons"),
        ("icons_attention", "accent.fg", "Starred bookmark, finished download"),
        ("button_background_hover", "bg.hover", "Toolbar button on hover"),
        ("button_background_active", "bg.selected", "Toolbar button pressed or open"),
        ("toolbar_top_separator", "border.subtle", "Line above the toolbar"),
        ("toolbar_bottom_separator", "border.subtle", "Line between the toolbar and the page"),
        ("toolbar_vertical_separator", "border.subtle", "Separators in the bookmarks bar"),
    ]),
    ("URL bar and find field", [
        ("toolbar_field", "bg.canvas", "Field background, recessed into the toolbar"),
        ("toolbar_field_text", "text.primary", "Field text"),
        ("toolbar_field_border", "border.control", "Functional outline that identifies the field"),
        ("toolbar_field_focus", "bg.raised", "Focused field; joins the floating suggestions panel"),
        ("toolbar_field_text_focus", "text.primary", "Focused field text"),
        ("toolbar_field_border_focus", "focus.ring", "Focus indicator of the field"),
        ("toolbar_field_highlight", "selection.bg", "Selected text in the field (text selection)"),
        ("toolbar_field_highlight_text", "selection.fg", "Selected text ink in the field"),
    ]),
    ("Popups and panels", [
        ("popup", "bg.raised", "Menus, panels and the URL suggestions (Firefox 156 and earlier)"),
        ("popup_text", "text.primary", "Popup text"),
        ("popup_border", "border.subtle", "Popup edge"),
        ("popup_highlight", "bg.selected", "Keyboard-highlighted popup item"),
        ("popup_highlight_text", "text.primary", "Text of the highlighted popup item"),
    ]),
    ("Sidebar", [
        ("sidebar", "bg.surface", "Sidebar background"),
        ("sidebar_text", "text.primary", "Sidebar text"),
        ("sidebar_border", "border.subtle", "Sidebar edge and splitter"),
        ("sidebar_highlight", "bg.selected", "Highlighted row in the built-in sidebars"),
        ("sidebar_highlight_text", "text.primary", "Text of the highlighted row"),
    ]),
    ("New tab page", [
        ("ntp_background", "bg.canvas", "Page background"),
        ("ntp_text", "text.primary", "Page text"),
        ("ntp_card_background", "bg.surface", "Cards and shortcut tiles (Firefox 157 and later)"),
    ]),
]

# theme.properties per mode. color_scheme drives the chrome (menus, context menus) and, because
# content_color_scheme is not set, the content (about: pages, prefers-color-scheme of web pages).
# It is explicit instead of "auto" so the mode never depends on a luminance heuristic.
COLOR_SCHEME = {"slate": "dark", "daylight": "light"}

# Which manifest key carries each mode. Firefox applies "theme" when it is in the light scheme and
# "dark_theme" when it is in the dark scheme (see README, "Slate and Daylight").
MANIFEST_KEY = {"daylight": "theme", "slate": "dark_theme"}
