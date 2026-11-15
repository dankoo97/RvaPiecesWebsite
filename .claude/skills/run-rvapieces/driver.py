"""Headless-browser driver for the locally running RVA Pieces site.

Run with (from the repo root, dev server already up on :8000):
    uv run --no-project --with playwright python .claude/skills/run-rvapieces/driver.py <command> ...

Commands
    shot <path> [name]     open a page, print status/title/console errors, save a screenshot
    login                  log into /admin as the agent superuser; later commands reuse the session
    logout                 forget the saved session (next commands browse as an anonymous visitor)
    add-event <name>       create a draft Event in the admin, publish it, print its public URL
    demo                   login -> add-event "Driver Smoke Event <time>" -> screenshot it + the schedule

Screenshots and the saved login session go to $RVA_RUN_DIR (default: <system temp>/rvapieces-run).
"""

import os
import re
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get(
    "RVA_BASE_URL", f"http://127.0.0.1:{os.environ.get('RVA_PORT', '8765')}"
)
RUN_DIR = Path(
    os.environ.get("RVA_RUN_DIR", Path(tempfile.gettempdir()) / "rvapieces-run")
)
SHOTS = RUN_DIR / "shots"
STATE = RUN_DIR / "browser-state.json"
USER = os.environ.get("RVA_ADMIN_USER", "agent")
PASSWORD = os.environ.get("RVA_ADMIN_PASSWORD", "agent-pass-123")


def open_page(p):
    browser = p.chromium.launch()
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        storage_state=str(STATE) if STATE.exists() else None,
    )
    page = context.new_page()
    errors = []
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.on("pageerror", lambda e: errors.append(str(e)))
    return browser, context, page, errors


def save_shot(page, name):
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"screenshot: {path}")
    return path


def report(page, response, errors):
    status = response.status if response else "?"
    print(f"{status} {page.url}  title={page.title()!r}")
    for e in errors:
        print(f"  console error: {e}")


def site_path(arg):
    """Accept 'events/schedule/' or '/events/schedule/'. Git Bash rewrites a leading-slash
    argument into a Windows path (e.g. '/' -> 'C:/Program Files/Git/'), so catch that."""
    if re.match(r"^[A-Za-z]:[/\\]", arg):
        sys.exit(
            f"got a Windows path {arg!r}: Git Bash converted a leading-slash argument. "
            "Drop the leading slash (e.g. 'events/schedule/') or set MSYS_NO_PATHCONV=1."
        )
    return "/" + arg.lstrip("/")


def cmd_shot(p, path="", name=None):
    path = site_path(path)
    browser, _, page, errors = open_page(p)
    response = page.goto(BASE + path, wait_until="load")
    report(page, response, errors)
    save_shot(
        page, name or (re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-") or "home")
    )
    browser.close()


def do_login(page, context):
    page.goto(f"{BASE}/admin/login/?next=/admin/")
    page.fill("#id_username", USER)
    page.fill("#id_password", PASSWORD)
    page.click("input[type=submit]")
    page.wait_for_url(f"{BASE}/admin/")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(STATE))
    print(f"logged in as {USER}; session saved to {STATE}")


def cmd_login(p):
    browser, context, page, _ = open_page(p)
    do_login(page, context)
    save_shot(page, "admin-home")
    browser.close()


def cmd_add_event(p, name):
    browser, context, page, errors = open_page(p)
    page.goto(f"{BASE}/admin/events/event/add/")
    if "/admin/login/" in page.url:
        do_login(page, context)
        page.goto(f"{BASE}/admin/events/event/add/")

    page.fill("#id_name", name)
    page.fill("#id_short_description", f"{name}: created by the run-rvapieces driver.")
    page.fill("#id_location", "Richmond, VA")
    page.click("input[name=_save]")
    page.wait_for_url(re.compile(r".*/admin/events/event/$"))

    # Publish the draft with the "publish_draft" admin action (publishing makes a public copy).
    page.locator("tr", has_text=name).locator("input.action-select").first.check()
    page.select_option("select[name=action]", "publish_draft")
    page.click("button[name=index]")
    page.wait_for_load_state("load")
    for msg in page.locator("ul.messagelist li").all_inner_texts():
        print(f"admin message: {msg}")
    save_shot(page, "admin-after-publish")

    # Find the published (non-draft) copy's public URL from the event's change page.
    page.goto(f"{BASE}/admin/events/event/?is_published__exact=1&q={name}")
    page.locator("#result_list a", has_text=name).first.click()
    slug = page.input_value("#id_slug") if page.locator("#id_slug").count() else None
    if not slug:  # slug is read-only on the change page in some states
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    url = f"/events/event/{slug}/"
    print(f"public url: {BASE}{url}")
    for e in errors:
        print(f"  console error: {e}")
    browser.close()
    return url


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    command, args = argv[0], argv[1:]
    with sync_playwright() as p:
        if command == "shot":
            cmd_shot(p, *args)
        elif command == "logout":
            STATE.unlink(missing_ok=True)
            print("logged out (session file removed)")
        elif command == "login":
            cmd_login(p)
        elif command == "add-event":
            cmd_add_event(p, " ".join(args))
        elif command == "demo":
            cmd_login(p)
            url = cmd_add_event(p, f"Driver Smoke Event {time.strftime('%H%M%S')}")
            cmd_shot(p, url, "public-event")
            cmd_shot(p, "/events/schedule/", "schedule")
        else:
            print(f"unknown command: {command}\n{__doc__}")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
