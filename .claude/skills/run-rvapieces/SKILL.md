---
name: run-rvapieces
description: Build, run, and drive the RVA Pieces Django website locally. Use when asked to start or run the site, run the dev server, run its tests, take a screenshot of a page, log into the admin, create/publish an event, or check that a change works in the real app.
---

The RVA Pieces club site (Django, SQLite). An agent runs an **isolated** copy with
`.claude/skills/run-rvapieces/server.sh` (own port, own scratch DB, no page cache) and drives it
with the headless-browser driver `.claude/skills/run-rvapieces/driver.py` (Playwright via `uv`).

All paths are relative to the repo root. Verified on Windows 11 in Git Bash; the scripts also
handle Linux/macOS (`pkill` instead of PowerShell), but that path wasn't run.

## Prerequisites

`uv`, Node/npm and `curl` on PATH. Python 3.13 and the project's deps come from `uv` (`.venv`).
Once per machine, download the browser the driver uses (about 20s):

```bash
uv run --no-project --with playwright playwright install chromium
```

## Run (agent path)

```bash
.claude/skills/run-rvapieces/server.sh start      # migrate, superuser, scss, js, runserver; waits until it serves
uv run --no-project --with playwright python .claude/skills/run-rvapieces/driver.py demo
.claude/skills/run-rvapieces/server.sh stop
```

`start` serves on **http://127.0.0.1:8765** (`RVA_PORT` to change) and creates the superuser
**agent / agent-pass-123**. `demo` logs into the admin, creates an event, publishes it with the
admin action, then screenshots the public event page and the schedule. Expected output ends with
`200 http://127.0.0.1:8765/events/schedule/`.

Driver commands (`driver.py <command>`):

| command | what it does |
|---|---|
| `shot <path> [name]` | open a page, print HTTP status, title and console errors, save a full-page screenshot |
| `login` | log into `/admin`; the session is saved and reused by later commands |
| `logout` | forget the session, so pages render as an anonymous visitor would see them |
| `add-event <name>` | create a draft event in the admin, publish it, print its public URL |
| `demo` | `login` → `add-event "Driver Smoke Event <time>"` → screenshot it and the schedule |

```bash
uv run --no-project --with playwright python .claude/skills/run-rvapieces/driver.py shot events/schedule/ schedule
uv run --no-project --with playwright python .claude/skills/run-rvapieces/driver.py logout
```

Screenshots → `<system temp>/rvapieces-run/shots/*.png` (Windows: `%LOCALAPPDATA%\Temp\rvapieces-run\shots`).
The scratch DB, server log (`server.log`) and saved session live in the same `rvapieces-run`
folder. `server.sh status` checks the server; `server.sh reset` stops it and deletes that folder
for a clean slate.

To poke Django code directly (models, helpers) without a browser, use the same settings:

```bash
PYTHONPATH=.claude/skills/run-rvapieces DJANGO_SETTINGS_MODULE=agent_settings DJANGO_SECRET_KEY=local-dev-only \
  uv run python -c "import django; django.setup(); from events.models import Event; print(Event.objects.count())"
```

## What the isolated run changes (agent_settings.py, agent_stubs.py)

- **Database:** a scratch SQLite file in `rvapieces-run/`, never the developer's `db.sqlite3`.
  It starts empty: no events until you add some.
- **Page cache:** off. The real settings cache whole pages for 24h, so edits wouldn't show up.
- **Outside services:** `EXTERNAL_WRITES_ENABLED=False`, so nothing is ever posted to Lichess or Discord.
- **Lichess/Chessnut lookups:** without `LICHESS_API_TOKEN` / `CHESSNUT_API_KEY` in the
  environment, they return empty lists (the startup log says so). Export a real token before
  `server.sh start` to read the live data instead.

## Run (human path)

Set `DJANGO_SECRET_KEY` (and `DEBUG=1`), then `uv run python manage.py runserver`. That uses
`db.sqlite3` in the repo and the 24h page cache. It's what the developer runs from IntelliJ on port 8000.

## Test

```bash
DJANGO_SECRET_KEY=local-dev-only uv run python manage.py test
```

Expected: `Ran 29 tests`, **4 errors** (`EventAdminTests` ×3, `EventTests.test_public_events_resolve`):
`ValueError: LICHESS_API_TOKEN environment variable not set`. They pass only with a real token.
Don't run the tests with `agent_settings`: its Chessnut replacements make 9 `MagicChessnutHandlerTests` fail.

## Gotchas

- **Port 8000 is probably taken by the developer's own server, and Windows won't tell you.**
  A second `runserver` on 127.0.0.1:8000 starts without error, but requests keep going to the
  first one, so you'd be looking at the developer's real database. That's why `server.sh` uses
  8765 and refuses to start if anything already answers there.
- **Git Bash rewrites leading-slash arguments.** `driver.py shot /` arrives as
  `C:/Program Files/Git/`. Pass paths without the leading slash (`events/schedule/`, `""` for
  home); the driver catches the rewritten form and says so.
- **The event detail page needs Lichess.** Each render lists the club's studies through the Lichess
  API. With no token it fails with `ValueError: LICHESS_API_TOKEN environment variable not set`,
  and a fake token gets `HTTP 401: No such token`. `agent_stubs.py` is what makes it render locally.
- **`.env` isn't loaded automatically.** Nothing calls dotenv, and the repo's `.env` only has
  `DJANGO_SECRET_KEY`. The developer's IntelliJ run configuration supplies the rest.
- **Images on the home page and events are broken locally.** Media lives in the
  `rva-pieces-website_media` bucket, not on disk. `READ_FROM_CLOUD=True` makes local media requests fall back to the bucket.
- **The app logs console errors you can ignore when checking a change.** On event pages,
  `bootstrap is not defined` (`templates/events/event-details.html` uses `bootstrap.Tooltip` before
  `template.html` loads Bootstrap's JS), and for anonymous visitors
  `Cannot read properties of null (reading 'addEventListener')`. Both also happen on the real site.
- **Killing `uv` doesn't stop the server on Windows.** Its child `python.exe` keeps the port.
  `server.sh stop` matches processes by their `runserver 127.0.0.1:<port>` command line instead.

## Troubleshooting

- **`Something is already serving http://127.0.0.1:8765`**: a previous run is still up. Run `server.sh stop` (or `reset`).
- **`ValueError at /events/event/...` in a page title**: the server was started without
  `agent_settings`. Use `server.sh start`, not a bare `runserver`.
- **`got a Windows path 'C:/Program Files/Git/...'`**: drop the leading slash from the page path.
- **`The SECRET_KEY setting must not be empty`** when running tests: prefix the command with
  `DJANGO_SECRET_KEY=local-dev-only`.
