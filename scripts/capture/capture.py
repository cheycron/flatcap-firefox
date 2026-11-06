"""Render the Flatcap Firefox theme in a real Firefox on Xvfb and save screenshots (runs inside the container).

    docker run --rm --shm-size=2g -v "$PWD/dist:/addon:ro" -v "$OUT:/out" flatcap-ff-capture \
        --addon /addon/flatcap-firefox-2.0.0.zip --out /out [--baseline] [--live]

Per mode the script opens five local pages, a new tab, focuses the URL bar, types a query and saves
the whole X screen. The system color scheme is set with the Firefox pref `ui.systemUsesDarkTheme`
(Linux), so the single add-on has to pick `theme` or `dark_theme` by itself. Computed chrome values
are written next to the images as JSON.
"""
import argparse
import functools
import http.server
import json
import os
import subprocess
import threading
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

DISPLAY = ":99"
os.environ["DISPLAY"] = DISPLAY
os.environ["MOZ_REMOTE_ALLOW_SYSTEM_ACCESS"] = "1"
PORT = 8765
PAGES = ["index", "dashboard", "docs", "reports", "inbox"]
W, H = 1440, 900


def sh(*cmd, check=True, **kw):
    return subprocess.run(cmd, check=check, env={**os.environ, "DISPLAY": DISPLAY}, **kw)


def start_xvfb():
    subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", f"{W}x{H}x24", "-nolisten", "tcp"])
    time.sleep(1.5)


def start_site():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory="/site")
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()


def options(dark: bool) -> Options:
    o = Options()
    o.binary_location = "/opt/firefox/firefox"
    prefs = {
        "ui.systemUsesDarkTheme": 1 if dark else 0,
        "browser.shell.checkDefaultBrowser": False,
        "browser.startup.homepage": "about:blank",
        "browser.aboutwelcome.enabled": False,
        "browser.tabs.warnOnClose": False,
        "browser.search.suggest.enabled": False,
        "browser.urlbar.suggest.searches": False,
        "browser.urlbar.quicksuggest.enabled": False,
        "browser.urlbar.suggest.quicksuggest.sponsored": False,
        "browser.urlbar.suggest.quicksuggest.nonsponsored": False,
        "browser.urlbar.suggest.trending": False,
        "browser.urlbar.suggest.engines": False,
        "datareporting.policy.dataSubmissionEnabled": False,
        "toolkit.telemetry.reportingpolicy.firstRun": False,
        "app.update.enabled": False,
        "network.captive-portal-service.enabled": False,
        "browser.region.update.enabled": False,
        "extensions.getAddons.cache.enabled": False,
        "browser.download.autohideButton": True,
        "remote.prefs.recommended": False,  # do not let automation switch the new tab page and other UI off
        "browser.newtabpage.enabled": True,
        "browser.newtabpage.activity-stream.showWeather": False,
        "browser.newtabpage.activity-stream.system.showWeather": False,
        "browser.newtabpage.activity-stream.feeds.weatherfeed": False,
        "browser.toolbars.bookmarks.visibility": "always",
    }
    for k, v in prefs.items():
        o.set_preference(k, v)
    return o


COMPUTED_JS = """
const cs = getComputedStyle(document.documentElement);
const names = ['--lwt-accent-color','--lwt-text-color','--toolbar-bgcolor','--toolbar-color',
  '--toolbar-field-background-color','--toolbar-field-color','--toolbar-field-focus-background-color',
  '--toolbar-field-focus-border-color','--arrowpanel-background','--arrowpanel-color',
  '--arrowpanel-border-color','--sidebar-background-color','--sidebar-text-color',
  '--tab-selected-bgcolor','--tab-selected-textcolor','--tabs-border-color'];
const out = {};
for (const n of names) out[n] = cs.getPropertyValue(n).trim();
out.lwtheme = document.documentElement.hasAttribute('lwtheme');
out.lwthemetextcolor = document.documentElement.getAttribute('lwthemetextcolor');
out.systemDark = matchMedia('(prefers-color-scheme: dark)').matches;
out.title = document.title;
return out;
"""


def shot(path: Path):
    sh("import", "-window", "root", str(path))
    print("saved", path)


def computed(driver):
    driver.set_context("chrome")
    try:
        return driver.execute_script(COMPUTED_JS)
    finally:
        driver.set_context("content")


def hide_automation(driver):
    """Marionette stripes the URL bar and marks tabs while it is attached; that is not part of the theme."""
    driver.set_context("chrome")
    try:
        return driver.execute_script("""
          const names = [...document.documentElement.getAttributeNames()];
          for (const n of ['remotecontrol', 'remote-control']) document.documentElement.removeAttribute(n);
          for (const el of document.querySelectorAll('[remotecontrol],[remote-control]')) {
            el.removeAttribute('remotecontrol'); el.removeAttribute('remote-control'); }
          return names;""")
    finally:
        driver.set_context("content")


BOOKMARKS = [("Docs", "docs"), ("Dashboard", "dashboard"), ("Reports", "reports"), ("Inbox", "inbox")]


def add_bookmarks(driver):
    """A few bookmarks, so the bookmarks bar shows toolbar_text instead of the import prompt."""
    driver.set_context("chrome")
    try:
        driver.set_script_timeout(20)
        driver.execute_async_script("""
          const done = arguments[arguments.length - 1];
          const [items, port] = [arguments[0], arguments[1]];
          (async () => {
            for (const [title, page] of items)
              await PlacesUtils.bookmarks.insert({parentGuid: PlacesUtils.bookmarks.toolbarGuid,
                                                  url: `http://127.0.0.1:${port}/${page}.html`, title});
            done(true);
          })().catch(e => done(String(e)));""", BOOKMARKS, PORT)
    finally:
        driver.set_context("content")


def prepare(driver):
    driver.set_window_rect(0, 0, W, H)
    sh("xdotool", "mousemove", str(W - 5), str(H - 5))  # keep the pointer off the page: no hover states
    add_bookmarks(driver)
    base = f"http://127.0.0.1:{PORT}/"
    driver.get(base + PAGES[0] + ".html")
    for p in PAGES[1:]:
        driver.switch_to.new_window("tab")
        driver.get(base + p + ".html")
    driver.set_context("chrome")
    try:
        driver.execute_script("gBrowser.selectedTab = gBrowser.addTrustedTab('about:newtab')")
    finally:
        driver.set_context("content")
    time.sleep(4)
    print("root attributes:", hide_automation(driver))


def focus_urlbar_and_type(text: str):
    sh("xdotool", "key", "--clearmodifiers", "ctrl+l")
    time.sleep(0.6)
    sh("xdotool", "type", "--delay", "120", text)
    time.sleep(2.5)


def run_mode(args, mode: str, out: Path, tag: str):
    dark = mode == "slate"
    svc = Service(log_output=str(out / f"geckodriver-{tag}.log"))
    driver = webdriver.Firefox(options=options(dark), service=svc)
    try:
        if not args.baseline:
            driver.install_addon(args.addon, temporary=True)
            time.sleep(2)
        prepare(driver)
        info = computed(driver)
        (out / f"computed-{tag}.json").write_text(json.dumps(info, indent=2, sort_keys=True))
        shot(out / f"{tag}-ntp.png")
        focus_urlbar_and_type(args.query)
        shot(out / f"{tag}-urlbar.png")
        sh("xdotool", "key", "Escape")
        time.sleep(0.5)
        # hamburger / app menu panel
        driver.set_context("chrome")
        try:
            driver.execute_script("document.getElementById('PanelUI-menu-button').click()")
        finally:
            driver.set_context("content")
        time.sleep(1.5)
        shot(out / f"{tag}-appmenu.png")
        sh("xdotool", "key", "Escape")
        time.sleep(0.5)
        # bookmarks sidebar
        driver.set_context("chrome")
        try:
            driver.execute_script("SidebarController.show('viewBookmarksSidebar')")
        finally:
            driver.set_context("content")
        time.sleep(2)
        shot(out / f"{tag}-sidebar.png")
        if args.live:
            # one session, system scheme flips while the add-on stays installed
            for flip, name in ((not dark, "flipped"), (dark, "back")):
                driver.set_context("chrome")
                try:
                    driver.execute_script("Services.prefs.setIntPref('ui.systemUsesDarkTheme', arguments[0])", 1 if flip else 0)
                finally:
                    driver.set_context("content")
                time.sleep(3)
                (out / f"computed-{tag}-{name}.json").write_text(json.dumps(computed(driver), indent=2, sort_keys=True))
                shot(out / f"{tag}-live-{name}.png")
    finally:
        driver.quit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addon", help="path to the zip to install as a temporary add-on")
    ap.add_argument("--out", default="/out")
    ap.add_argument("--query", default="flat")
    ap.add_argument("--baseline", action="store_true", help="no add-on: Firefox's own default theme")
    ap.add_argument("--live", action="store_true", help="also flip the system scheme inside the session")
    ap.add_argument("--modes", default="slate,daylight")
    ap.add_argument("--prefix", default="")
    args = ap.parse_args()
    if not args.baseline and not args.addon:
        ap.error("--addon is required unless --baseline")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    start_xvfb()
    start_site()
    for mode in args.modes.split(","):
        run_mode(args, mode, out, f"{args.prefix}{mode}")


if __name__ == "__main__":
    main()
