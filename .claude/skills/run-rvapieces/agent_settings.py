"""Settings for running the site locally from an agent/driver.

Same as RvaPiecesWebsite.settings, but:
- its own SQLite file and no page cache, so a driver run never touches the developer's
  db.sqlite3 or serves stale cached pages
- outside-service writes (Lichess chapters/studies, Discord posts) are always off
- Lichess/Chessnut reads return nothing when their tokens aren't set (agent_stubs.py)
Selected with DJANGO_SETTINGS_MODULE=agent_settings and this directory on PYTHONPATH.
"""

import os
import tempfile
from pathlib import Path

from RvaPiecesWebsite.settings import *  # noqa: F401,F403

_run_dir = Path(
    os.environ.get("RVA_RUN_DIR", Path(tempfile.gettempdir()) / "rvapieces-run")
)
_run_dir.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": _run_dir / "db.sqlite3"}
}
CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
EXTERNAL_WRITES_ENABLED = False
INSTALLED_APPS = [*INSTALLED_APPS, "agent_stubs.AgentStubsConfig"]  # noqa: F405
