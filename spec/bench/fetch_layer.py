"""Fetch layer for lifecycle tests -- copied from research/price-source.md on
main (verified by issue #1), trimmed to what the lifecycle measurements need.

Environment-dependent paths, stated plainly: with live=False the dead-network
legs probe an unroutable address. Where that address truly blackholes, the legs
end in real timeouts; behind a transparent TCP proxy (as in both sandboxes used
so far) the probe is answered instantly -- HTTP 403 in ~10 ms -- and the leg
times reported are those of the proxy refusal, not of a timeout. The script
says which case fired rather than pretending either way.
"""

from __future__ import annotations

import datetime as dt

from curl_cffi import requests as curl_requests

TIMEOUT_SECONDS = 5  # not the 30s curl_cffi default


class PriceUnavailable(Exception):
    pass


class SourceUnreachable(Exception):
    pass


def fetch_from_yahoo(ticker: str, session) -> dict:
    """Live path -- blocked in tonight's sandbox; kept for completeness."""
    try:
        response = session.get(
            f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}",
            params={"range": "1d", "interval": "1d"},
            timeout=TIMEOUT_SECONDS,
        )
    except curl_requests.exceptions.RequestException as error:
        raise SourceUnreachable(f"Yahoo unreachable: {error}") from error
    if response.status_code == 403:
        raise SourceUnreachable(f"Yahoo returned HTTP {response.status_code}")
    if response.status_code == 404:
        raise PriceUnavailable(f"{ticker}: unknown or delisted")
    meta = response.json()["chart"]["result"][0]["meta"]
    return {"ticker": ticker, "price": meta["regularMarketPrice"],
            "quoted_at": meta["regularMarketTime"], "source": "yahoo"}


def fetch_all_from_cnbc(tickers) -> dict:
    try:
        import requests
        response = requests.get(
            "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol",
            params={"symbols": "|".join(t.replace("-", ".") for t in tickers),
                    "requestMethod": "itv", "output": "json"},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception as error:
        raise SourceUnreachable(f"CNBC unreachable: {error}") from error
    return {}


def fetch_prices(tickers, live=False):
    """The full chain with #1's structure. Returns (snapshots, failures).

    With live=False, sources are simulated so the *chain timing* is measured,
    not the network. The fallback discards Yahoo snapshots exactly like #1's
    example code -- that behaviour is under test here.
    """
    snapshots: dict = {}
    failures: dict = {}
    if not live:
        # simulate both sources unreachable over a real unroutable network:
        for ticker in tickers:
            snapshots[ticker] = None  # placeholder replaced below
        return _dead_network_chain(tickers)
    with curl_requests.Session(impersonate="chrome") as session:
        for ticker in tickers:
            try:
                snapshots[ticker] = fetch_from_yahoo(ticker, session)
            except PriceUnavailable as error:
                failures[ticker] = str(error)
            except SourceUnreachable:
                failures.clear()
                break
        else:
            return snapshots, failures
    try:
        snapshots = fetch_all_from_cnbc(tickers)
    except SourceUnreachable as error:
        return {}, {t: f"all sources unreachable: {error}" for t in tickers}
    return snapshots, failures


def _dead_network_chain(tickers):
    """Probe an unroutable address in #1's chain shape.

    Reports per-leg elapsed time and how the leg actually ended: a real
    timeout, an early answer (transparent proxy), or another immediate error.
    Returns (snapshots, failures, t_yahoo, t_cnbc, outcomes) where outcomes
    names the yahoo and cnbc leg endings.
    """
    import time

    def probe(request_call):
        t0 = time.perf_counter()
        try:
            request_call()
            return time.perf_counter() - t0, "answered-early"
        except Exception as error:
            kind = type(error).__name__
            slow = time.perf_counter() - t0 >= TIMEOUT_SECONDS * 0.9
            return time.perf_counter() - t0, f"timeout ({kind})" if slow else f"error: {kind}"

    def yahoo_leg():
        curl_requests.get("https://10.255.255.1/", timeout=TIMEOUT_SECONDS)

    t_yahoo, y_end = probe(yahoo_leg)
    t_cnbc, c_end = probe(
        lambda: _plain_requests("https://10.255.255.1/", timeout=TIMEOUT_SECONDS))
    outcomes = {"yahoo": y_end, "cnbc": c_end}
    return ({}, {t: "all sources unreachable" for t in tickers},
            t_yahoo, t_cnbc, outcomes)


def _plain_requests(*args, **kwargs):
    import requests
    return requests.get(*args, **kwargs)


if __name__ == "__main__":
    snaps, fails, ty, tc, legs = fetch_prices(["AAPL", "MSFT"])
    print(f"yahoo leg: {ty:.2f}s ({legs['yahoo']}), "
          f"cnbc leg: {tc:.2f}s ({legs['cnbc']}), total {ty+tc:.2f}s")
