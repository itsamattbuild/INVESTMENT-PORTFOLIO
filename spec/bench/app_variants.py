"""Blocking vs non-blocking startup -- two minimal FastAPI apps, measured.

The fetch chain mirrors #1's shape: Yahoo leg then CNBC leg, TIMEOUT_SECONDS=5
each. Tonight's sandbox cannot produce real network timeouts (transparent
proxy accepts all TCP), so the dead-network case sleeps for the timeout
duration instead -- the arithmetic (5s + 5s) is #1's measurement; what is
measured for real here is what each design does to the user's screen.
"""

import json
import threading
import time

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

TIMEOUT = 5.0
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
           "META", "TSLA", "BRK-B", "JPM", "V", "JNJ", "WMT"]
CACHE = "/tmp/opencode/life/price_cache.json"

# last known prices, as the no-network policy requires them on disk
json.dump({t: {"price": 100.0 + i, "quoted_at": "2026-08-25T20:00:01Z"}
           for i, t in enumerate(TICKERS)}, open(CACHE, "w"))


def fetch_chain(network: str):
    """#1's chain. network='dead' -> both sources time out; 'healthy' -> ~0.35s."""
    if network == "dead":
        time.sleep(TIMEOUT)          # yahoo leg
        time.sleep(TIMEOUT)          # cnbc leg
        return None
    time.sleep(0.35)                 # measured sequential 12-ticker fetch (#1)
    return {t: {"price": 200.0, "quoted_at": "now"} for t in TICKERS}


def make_app(kind: str, network: str) -> FastAPI:
    app = FastAPI()
    state = {"fresh": False}

    def do_fetch():
        result = fetch_chain(network)
        if result:
            json.dump(result, open(CACHE, "w"))
        state["fresh"] = True

    if kind == "nonblocking":
        @app.on_event("startup")
        def _start():
            threading.Thread(target=do_fetch, daemon=True).start()

    @app.get("/api/prices")
    def prices():
        return {"prices": json.load(open(CACHE)), "fresh": state["fresh"]}

    @app.get("/", response_class=HTMLResponse)
    def index():
        t0 = time.perf_counter()
        if kind == "blocking":
            do_fetch()               # page waits for the whole chain
            body = "<h1>portfolio</h1>"
        else:
            body = ("<h1>portfolio</h1>"
                    f"<p>showing last known prices (fetched "
                    f"{json.load(open(CACHE))['AAPL']['quoted_at']})</p>"
                    "<script>setTimeout(()=>fetch('/api/prices'),500)</script>")
        print(f"[{kind}] / rendered in {time.perf_counter()-t0:.3f}s "
              f"(server-side)", flush=True)
        return body
    return app


if __name__ == "__main__":
    import sys
    kind, network, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
    uvicorn.run(make_app(kind, network), host="127.0.0.1", port=port,
                log_level="warning")
