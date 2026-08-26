#!/bin/bash
# Investment Portfolio -- double-clickable launcher for macOS.
# Place in the project folder (or anywhere); double-clicking runs this script
# in Terminal.app. Tested for logic on Linux bash; macOS-specific steps are
# marked [macOS] and were reasoned from documentation, not executed.

set -u
APP_PORT=8123
APP_URL="http://127.0.0.1:${APP_PORT}"
DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DIR/.venv"

echo "== Investment Portfolio launcher =="

# 1. Python must exist
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found. Install Python 3.11+ from python.org"
    echo "or run 'xcode-select --install'."   # [macOS]
    exit 1
fi

# 2. venv with the dependencies; created on first run only
if [ ! -x "$VENV/bin/python" ]; then
    echo "First run: creating a private Python environment..."
    if ! python3 -m venv "$VENV" 2>/dev/null; then
        echo "ERROR: could not create the environment."
        echo "On macOS run:  xcode-select --install"
        exit 1
    fi
    "$VENV/bin/pip" --quiet install curl_cffi requests fastapi "uvicorn[standard]" \
        || { echo "ERROR: dependency install failed (no internet?)"; exit 1; }
fi

# 3. start the server unless one is already listening
if curl -s -o /dev/null --max-time 1 "$APP_URL"; then
    echo "Server already running at $APP_URL"
else
    echo "Starting server at $APP_URL ..."
    (cd "$DIR" && nohup "$VENV/bin/python" -m uvicorn app:app \
        --host 127.0.0.1 --port "$APP_PORT" >> "$DIR/server.log" 2>&1 &)
    # wait until it answers (max ~10 s)
    for _ in $(seq 1 50); do
        if curl -s -o /dev/null --max-time 1 "$APP_URL"; then break; fi
        sleep 0.2
    done
    if ! curl -s -o /dev/null --max-time 1 "$APP_URL"; then
        echo "ERROR: server did not start. See server.log"
        exit 1
    fi
fi

# 4. show the page [macOS: 'open' launches the default browser;
#    on other platforms fall back to xdg-open or print the URL]
if command -v open >/dev/null 2>&1; then
    open "$APP_URL"                       # [macOS]
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$APP_URL"
else
    echo "Open $APP_URL in your browser."
fi

echo "Ready. The server keeps running in the background;"
echo "to stop it:  kill \$(lsof -ti :$APP_PORT)"
