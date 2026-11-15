#!/usr/bin/env bash
# Start/stop an isolated local copy of the site for agents and drivers.
#
#   .claude/skills/run-rvapieces/server.sh start    # prepare + run in background, wait until it serves
#   .claude/skills/run-rvapieces/server.sh status
#   .claude/skills/run-rvapieces/server.sh stop
#   .claude/skills/run-rvapieces/server.sh reset    # stop and delete the scratch DB/screenshots
#
# Isolation: its own port (RVA_PORT, default 8765), its own SQLite file and no page cache
# (agent_settings.py), so it never touches the developer's db.sqlite3 or their own server on 8000.
# Run from the repo root (Git Bash on Windows, or bash on Linux/macOS).
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SKILL_DIR/../../.." && pwd)"
PORT="${RVA_PORT:-8765}"
URL="http://127.0.0.1:$PORT"
RUN_DIR="${RVA_RUN_DIR:-$(python3 -c 'import tempfile; print(tempfile.gettempdir())' 2>/dev/null || echo "${TMPDIR:-/tmp}")/rvapieces-run}"
LOG="$RUN_DIR/server.log"

export PYTHONPATH="$SKILL_DIR" DJANGO_SETTINGS_MODULE=agent_settings RVA_RUN_DIR="$RUN_DIR"
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-local-dev-only}" DEBUG="${DEBUG:-1}" PYTHONUNBUFFERED=1
# Allow the browser driver's origin for CSRF (admin logins/forms POST from it).
export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-$URL}" DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-127.0.0.1,localhost}"

serving() { curl -s -o /dev/null --max-time 2 "$URL/"; }

stop_server() {
  if command -v powershell.exe >/dev/null 2>&1; then
    # uv's child python.exe survives killing uv itself on Windows; match the command line instead.
    powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='python.exe' or Name='uv.exe'\" | Where-Object { \$_.CommandLine -like '*runserver 127.0.0.1:$PORT*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }" || true
  else
    pkill -f "runserver 127.0.0.1:$PORT" || true
  fi
}

case "${1:-}" in
  start)
    if serving; then
      echo "Something is already serving $URL. Use '$0 stop', or pick another port with RVA_PORT=..." >&2
      exit 1
    fi
    mkdir -p "$RUN_DIR"
    cd "$REPO"
    echo "== migrate ($RUN_DIR/db.sqlite3)"
    uv run python manage.py migrate --noinput 2>&1 | grep -v -E 'requires-python|^  Apply' || true
    echo "== superuser agent / agent-pass-123"
    DJANGO_SUPERUSER_USERNAME=agent DJANGO_SUPERUSER_EMAIL=agent@example.com \
      DJANGO_SUPERUSER_PASSWORD=agent-pass-123 \
      uv run python manage.py createsuperuser --noinput 2>&1 | grep -v requires-python || true
    echo "== scss + js"
    uv run python manage.py sass static/scss static/styles 2>&1 | grep -v requires-python | tail -1
    [ -d node_modules ] || npm ci --silent
    npm run --silent build:js
    echo "== runserver $URL (log: $LOG)"
    nohup uv run python manage.py runserver "127.0.0.1:$PORT" --noreload >"$LOG" 2>&1 &
    for _ in $(seq 60); do serving && break; sleep 1; done
    if serving; then echo "ready: $URL"; else echo "server didn't come up; see $LOG" >&2; tail -20 "$LOG" >&2; exit 1; fi
    ;;
  status)
    if serving; then echo "up: $URL"; else echo "down: $URL"; exit 1; fi
    ;;
  stop)
    stop_server
    for _ in $(seq 10); do serving || break; sleep 0.5; done
    if serving; then echo "still serving $URL" >&2; exit 1; else echo "stopped"; fi
    ;;
  reset)
    stop_server
    rm -rf "$RUN_DIR"
    echo "removed $RUN_DIR"
    ;;
  *)
    sed -n 2,11p "$0"
    exit 2
    ;;
esac
