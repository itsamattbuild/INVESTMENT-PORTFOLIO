# Price source for US equities

Research for [issue #1](https://github.com/itsamattbuild/INVESTMENT-PORTFOLIO/issues/1).

Every candidate below was installed and called with real tickers. Nothing here is
taken from a README. Where a source could not be tested, it says so and why.

**Test conditions.** 2026-08-25, 21:00–21:16 ET — a Tuesday, after the 20:00 ET
post-market close. The market was **closed** for all runs. Live-session delay
behaviour is therefore untested for every source, and weekend behaviour is
untested. This matters and is flagged again where it does.

Twelve tickers were used throughout, matching the expected portfolio size:
`AAPL MSFT NVDA GOOGL AMZN META TSLA BRK-B JPM V JNJ WMT`.

---

## Recommendation

**Primary: the Yahoo chart endpoint, called directly.**
`GET https://query2.finance.yahoo.com/v8/finance/chart/{ticker}` via `curl_cffi`.

**Fallback: the CNBC quote endpoint.**
`GET https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol` via `requests`.

**Ticker validation: the Yahoo search endpoint.**
`GET https://query2.finance.yahoo.com/v1/finance/search`.

**Not recommended: `yfinance`**, despite being the obvious choice — reasons below.
It stays useful as an early-warning tracker, not as a dependency.

### Why, by failure risk

The question is not which API is pleasant. It is: *when this breaks, will the app
know?* An app opened daily that shows a confident wrong number is worse than one
that shows an error, because nobody audits a number that looks plausible.

Ranked by the thing that actually causes damage — **silent wrongness**:

| Source | Bad ticker | Network down | Are they distinguishable? |
|---|---|---|---|
| **Yahoo raw** | HTTP 404 + structured `chart.error` | `curl_cffi` `Timeout` / `DNSError` | **Yes — two disjoint channels** |
| **CNBC** | HTTP 200, `code: 1` | `requests.ConnectionError` | **Yes — clean sentinel** |
| yfinance `.download()` | silent empty DataFrame | **silent empty DataFrame** | **No — identical** |
| yfinance `.info` | silent, `regularMarketPrice=None` | raises | partly |
| yfinance `fast_info` | `KeyError: 'currentTradingPeriod'` | raises | only by catching an internal |

`yf.download()` is yfinance's fastest path and its most dangerous: a dropped
Wi-Fi connection and a genuinely dead ticker produce **the same empty DataFrame
with the same "possibly delisted" message**. That single row is the reason
yfinance is not the recommendation.

There is a second reason. `fast_info` — the natural "just give me the price" call —
**has no timestamp field at all.** Verified: the only time-related key is
`timezone`. CONTEXT.md defines a *price snapshot* as a price together with the
time it was fetched, and states the reason plainly: without one you cannot tell a
falling portfolio from a broken fetch. `fast_info` cannot express a price
snapshot. Getting a timestamp means calling `.info` and pulling 187 keys.

The Yahoo chart endpoint, by contrast, returns the richest staleness information
of anything tested: `regularMarketTime`, `gmtoffset`, `exchangeTimezoneName`,
and `currentTradingPeriod` giving exact session boundaries. You can classify
live / closed / stale entirely from the payload.

### Which one would I bet on still working in a year?

**The Yahoo endpoint — with moderate, not high, confidence.**

The honest case against it: it is unofficial, unsanctioned, and Yahoo is actively
trying to block non-browser clients (see *The thing worth knowing* below). It can
break tomorrow.

The case for it anyway is **repair capacity, not stability**. `yfinance` has
25,074 stars, one maintainer shipping a release every ~20 days (median of the
last 20 releases), and a measured track record on acute breakages:

| Breakage | Reported | Released fix | Days |
|---|---|---|---|
| #2422 `YFRateLimitError` (141 comments) | 2025-04-30 | 0.2.58, 05-02 (partial) → 0.2.61, 05-12 (real) | **2 / 12** |
| #2284 `Edge: 429` | 2025-02-19 | 0.2.61, 2025-05-12 | **82** |
| #2125 `429 in loop` | 2024-11-14 | 0.2.54, 2025-02-18 | **96** |

Loud, total outages get fixed in days — six releases shipped in twenty days
during the April 2025 crisis. Intermittent ones sit for months.

This is the actual argument: **because we call the same upstream that yfinance
calls, its issue tracker is a free early-warning system and a free diagnosis**,
even though we do not depend on the library. When Yahoo changes something, 25,000
users find out before we do and one maintainer publishes the workaround. We copy
it into forty lines of our own Python. We get the community's repair capacity
without inheriting the library's silent failure modes.

**Bus factor is 1.** ValueRaider has 1,077 commits; the original author 380 and is
largely inactive; third place has 41. One person is the project. That is a real
risk to the early-warning system, not to the endpoint itself.

### What the fallback is when it does not work

CNBC, and it is a genuine fallback rather than a decorative one: **different
vendor, different network path, different client library, no shared dependency**.
Yahoo blocking us does not imply CNBC blocking us. It cross-validated exactly —
all 12 prices matched Yahoo to the cent (diff `0.0000`).

Its limits are known and acceptable for a fallback: no split data, and it uses
`BRK.B` where Yahoo uses `BRK-B`, so a small ticker-mapping layer is needed.

The failure hierarchy the app should implement, in order:

1. Yahoo chart endpoint.
2. On transport failure or 404-for-everything → CNBC.
3. On both failing → **last known prices with their timestamp**, which is already
   settled policy. Never an empty screen.

I would *not* invert this and make CNBC primary despite it being faster and
cleaner to parse. It is an undocumented endpoint serving CNBC's own page widgets:
no contract, no versioning, no issue tracker, no community. When it changes,
nobody announces it and nobody publishes a fix. Yahoo is the more fragile
endpoint with the vastly better repair story, and repair story wins.

---

## The thing worth knowing

**`yfinance` depends on `curl_cffi`, a TLS-fingerprint impersonation library.**

This is not an implementation detail. Testing isolated the mechanism precisely:

- plain `requests` → **HTTP 429 on the very first call**
- `curl_cffi` **without** `impersonate` → **HTTP 429**
- `curl_cffi` **with** `impersonate="chrome"` → **HTTP 200**

Identical headers in all three cases. So the 429 is **not rate limiting** — it is
Yahoo fingerprinting the TLS handshake and refusing anything that is not a
browser. The word "429" in yfinance's issue tracker has been misleading people
for years: the fix in 0.2.61 was not backoff, it was switching HTTP clients to
one that lies about being Chrome.

Two consequences:

1. **The relationship with the data source is adversarial, not merely
   unofficial.** The library is in an arms race, not a parsing exercise. That is a
   different and worse risk profile than "Yahoo might change their HTML."
2. **There is no zero-dependency Python fallback to Yahoo.** Any plan of the form
   "if yfinance breaks I'll just call the endpoint with `requests`" does not work
   and cannot be made to work. `curl_cffi` is mandatory — and it is a compiled
   dependency with open build-failure issues (#2449, #2463).

CNBC, notably, needs none of this. Plain `requests` works.

---

## Candidates

### Eliminated

**Stooq — dead for scripted access.** Independently confirmed:

- `https://stooq.com/q/l/?s=aapl.us&f=sd2t2ohlcv&h&e=csv` → **HTTP 404**
- `https://stooq.com/q/d/l/?s=aapl.us&i=d` → HTTP 200, but the body is
  `<noscript>This site requires JavaScript to verify your browser…` — a
  JavaScript proof-of-work anti-bot challenge, not CSV.

**`pandas-datareader`'s Stooq reader no longer exists.** Version 0.11.1 ships only
six macro sources; `pandas_datareader.stooq` is `ModuleNotFoundError` and
`DataReader(..., "stooq")` raises `NotImplementedError`. The candidate is dead on
both paths. This is exactly the failure mode the ticket was written to catch: a
package that looks alive on PyPI (released 2026-06-24) and returns nothing.

**Alpha Vantage — disqualified by its own documentation.** Two quotes from
<https://www.alphavantage.co/support/>:

> free stock API service covering the majority of our datasets for **25 API
> requests per day**

> Realtime and 15-minute delayed US market data is regulated by the stock
> exchanges, FINRA, and the SEC.

Twelve tickers is 12 of 25 daily calls; opening the app twice exhausts the quota.
And anything fresher than end-of-day is a paid plan. Verified with the public
`demo` key (IBM only): values are strings, keys are numbered (`"05. price"`),
there is **no currency field at all**, and the timestamp is a bare date
(`"07. latest trading day": "2026-08-25"`) — no time, no timezone, so intraday
staleness is undetectable.

**Nasdaq `api.nasdaq.com` — looks alive, is not usable.** Flagging loudly because
it returns HTTP 200 and a rich-looking JSON tree:

```json
"primaryData": {"lastSalePrice": "$309.90", "lastTradeTimestamp": "Aug 25, 2026",
                "isRealTime": false, "currency": null}
```

`currency` is literally `null`. The timestamp is a bare date. The price needs
`$`-stripping. It takes **24.6 s** for 12 sequential tickers. It fails two
explicit v1 requirements — currency field and fetch time — while appearing to work.

Also probed and rejected: Yahoo `v6/quoteSummary` (**404**, removed), Yahoo
`v7/finance/quote` (**401**, crumb-gated — so there is *no* working Yahoo batch
endpoint), Financial Modeling Prep (401), Twelve Data (401).

### Not empirically verified

Both require creating an account with an email address. I did not sign up on the
repository owner's behalf, so these are documented limits only — **not tested**.

**Finnhub.** Endpoint reachable: `GET /api/v1/quote?symbol=AAPL` without a token
→ **HTTP 401**. From <https://finnhub.io/docs/api/rate-limit>:

> If your limit is exceeded, you will receive a response with status code `429`.
> On top of all plan's limit, there is a 30 API calls/ second limit.

The free tier's per-minute figure could not be extracted — finnhub.io/pricing is
JavaScript-rendered and the number is not in the served HTML. Not quoted from
memory.

**Tiingo.** Endpoint reachable: `GET https://api.tiingo.com/iex/AAPL` without a
token → **HTTP 403 `{"detail":"Please supply a token"}`**. Free plan per
<https://www.tiingo.com/about/pricing>: 50 requests/hour, 1,000/day, 500 unique
symbols/month, 1 GB bandwidth. The 500-symbol cap is generous for 12 tickers.
Real-time is listed under the paid Power plan; the free tier is end-of-day.

Neither is dismissed on merit. If the Yahoo path collapses and CNBC with it,
Tiingo is the first place to look for a keyed replacement — its limits comfortably
fit this workload. But both require a key, and the ticket states a preference for
no third-party service.

---

## For issue #2 — the response shape

Reporting the shape only. The schema is #2's decision, not this ticket's.

### Yahoo chart endpoint — `meta` object, verbatim

```json
{"currency": "USD", "symbol": "AAPL", "exchangeName": "NMS",
 "fullExchangeName": "NasdaqGS", "instrumentType": "EQUITY",
 "firstTradeDate": 345479400, "regularMarketTime": 1787688001,
 "hasPrePostMarketData": true, "gmtoffset": -14400, "timezone": "EDT",
 "exchangeTimezoneName": "America/New_York", "regularMarketPrice": 309.9,
 "regularMarketDayHigh": 313.58, "regularMarketDayLow": 308.21,
 "regularMarketVolume": 25666176, "chartPreviousClose": 310.34, "priceHint": 2,
 "currentTradingPeriod": {"pre": {...}, "regular": {"start": 1787664600,
                          "end": 1787688000}, "post": {...}}}
```

Answering #2's four questions directly:

- **Fields and types.** `regularMarketPrice` is a **`float`**. `regularMarketTime`
  is an **`int`** (epoch seconds, UTC). `currency`, `symbol`, `instrumentType`,
  `exchangeTimezoneName` are **`str`**. `gmtoffset` is an `int` (seconds).
- **Timestamp: comes from the source.** Epoch seconds, UTC. It is the **regular
  session close** when the market is shut (decoded here as 2026-08-25 16:00:01 ET),
  and the last trade time when open. It is *not* the fetch time — those are two
  different facts and #2 should decide whether to store both. My read: store both.
  The source timestamp answers "how old is this price"; the fetch time answers
  "when did we last successfully reach the source". They diverge exactly when
  something is wrong, which is when you need them.
- **Currency: stated explicitly**, not assumed. `"currency": "USD"`.
- **`instrumentType` is worth storing.** It is what distinguishes an equity from
  an ETF, and it is what would have caught the `FB` trap described below.

Note a float precision artefact: `fast_info` reports `lastPrice` as
`309.8999938964844`. The raw endpoint reports `309.9`. Given #2 is already
weighing `Decimal` against `float` for money, this is a data point in favour of
`Decimal` — and of parsing the raw endpoint rather than the library.

### CNBC — fields, verbatim

```
symbol: 'AAPL'   code: 0 (int)   name: 'Apple Inc.'
last: '309.90'   last_time: '2026-08-25T16:00:00.000-0400'
open: '310.79'   high: '313.59'  low: '308.21'  previous_day_closing: '310.34'
currencyCode: 'USD'   timeZone: 'EDT'   curmktstatus: 'POST_MKT'
volume: '22,997,124'   type: 'STOCK'   exchange: 'NASDAQ'
```

- **Every numeric is a `str`**, including the price. `volume` contains thousands
  separators — `float('22,997,124')` throws.
- **Timestamp from source, ISO-8601 with UTC offset** — the cleanest format
  tested, no epoch conversion needed.
- **Currency explicit** (`currencyCode`).
- `code` is an `int`: `0` = found, `1` = unknown symbol.

Both sources state currency explicitly, which means the map's "every monetary
value carries a currency field" rule is satisfiable from the payload rather than
hardcoded — the currency written to disk can be the one the source reported.

### One inconsistency #2 should know about

`fast_info['previousClose']` = 310.66, but `fast_info['regularMarketPreviousClose']`
= 310.34 and `.info['previousClose']` = 310.34. **Two fields named
`previousClose` disagree within one library.** Whatever #2 stores, name the field
after the endpoint field it came from, not after what it means.

---

## For issue #5 — timing and failure distinguishability

### How long a fetch takes

Twelve tickers, three runs each, seconds:

| Method | Native batch? | min | median |
|---|---|---|---|
| **CNBC — one batch call** | **yes** | **0.053** | **0.065** |
| Yahoo raw — 12 concurrent (12 threads) | no | 0.199 | 0.228 |
| `yf.download()` | yes | 0.290 | 0.314 |
| yfinance — 12 concurrent | no | 0.332 | 0.346 |
| Yahoo raw — 12 sequential (one session) | no | 0.353 | 0.353 |
| yfinance — 12 sequential `fast_info` | no | 0.859 | 0.892 |
| Nasdaq — 12 sequential | no | 24.648 | 26.724 |

**Does concurrency help? Barely, and #5 should probably not bother.** Yahoo raw
goes from 0.353 s sequential to 0.199 s concurrent — a saving of **0.15 seconds**
on a once-per-startup operation. That does not justify a thread pool in a codebase
whose owner is learning Python. Sequential is ~350 ms, which is below the
threshold where a progress indicator earns its place.

Two caveats for #5:

- **The first call on a cold path costs 1–4 s extra** (session and cookie setup —
  visible as outliers of 4.45 s and 1.21 s in the raw runs). So startup latency is
  dominated by connection setup, not by ticker count. This is the number to design
  the startup sequence around, not the 350 ms steady state.
- These timings are from a closed market. Live-session load is untested.

**Rate limiting under concurrency: none observed today.** Yahoo raw took 120 calls
across 16 threads in 1.33 s (90 req/s) — 120× HTTP 200, zero failures. yfinance:
96 calls, zero errors. CNBC: 60 batch calls, all 200. Testing stopped there rather
than risk an IP ban. **Absence of a limit today is not proof there is no limit**,
and the issue history shows Yahoo has throttled hard in the past. For 12 tickers
once a day this is a non-issue either way.

### Which failures are distinguishable at the call site

This is the section #5 most needs. Using the recommended sources:

| Condition | Yahoo raw | CNBC |
|---|---|---|
| Unknown ticker | HTTP **404**, `chart.error.code = "Not Found"` | HTTP 200, `code: 1` |
| Delisted ticker | HTTP **404**, same body | HTTP 200, `code: 0`, **stale price returned** |
| No network | `curl_cffi.requests.exceptions.Timeout` (30 s default) | `requests.exceptions.ConnectionError` |
| DNS failure | `curl_cffi.requests.exceptions.DNSError` | `ConnectionError` ← `NameResolutionError` |
| Rate limit | HTTP 429 (not reproducible today) | not reproducible |

So there are **three distinct categories** the app can act on differently, which
is what #5 needs to write failure behaviour against:

1. **Transport failure** (exception) → the whole fetch failed → show all last
   known prices with their timestamps. This is the settled no-network policy.
2. **Per-ticker rejection** (404 / `code: 1`) → that one ticker is bad → other
   eleven prices are fine, flag only that position.
3. **Stale success** (HTTP 200, old timestamp) → the dangerous one, below.

Note that **unknown and delisted are not distinguishable on Yahoo** — both are a
404 with an identical body. For this app that is acceptable: both mean "no current
price for this ticker", and the position still exists in history either way.

**Two things #5 should know about startup latency on a dead network.**

First, do not use the 30-second default timeout. That is the `curl_cffi` default
and it means a dead network stalls startup for half a minute before falling back.
Set it explicitly — the example code uses 5 s.

Second, **the timeouts compound**. Measured with an unroutable proxy, the full
chain takes **10.0 s** before giving up: 5 s waiting for Yahoo, then 5 s waiting
for CNBC. Having a fallback doubles the worst-case stall. That is the strongest
argument for #5's "render immediately with last known prices, refresh when the
fetch lands" option over "block the page on the fetch" — on a train with no
signal, blocking means ten seconds of nothing.

---

## For the map's fog — splits

**Automatic split detection is feasible. This can come out of `Not yet specified`.**

The Yahoo chart endpoint with `&events=div|split` returns exact ratios:

```json
"1718026200": {"date": 1718026200, "numerator": 10.0, "denominator": 1.0, "splitRatio": "10:1"}
"1598880600": {"date": 1598880600, "numerator": 4.0,  "denominator": 1.0, "splitRatio": "4:1"}
"1661434200": {"date": 1661434200, "numerator": 3.0,  "denominator": 1.0, "splitRatio": "3:1"}
```

Verified against known events: NVDA 10:1 (June 2024), AAPL 4:1 (Aug 2020),
TSLA 3:1 (Aug 2022). All three correct.

Use the **raw endpoint, not `yfinance.Ticker.splits`**, for this. The library
returns a single `float64` — a 3:2 split arrives as `1.5`, losing the numerator
and denominator. The raw endpoint preserves both, which matters when recomputing a
position's share count exactly.

CNBC and Nasdaq expose no split data, so the fallback source cannot do this. That
is fine — split detection is a convenience, not a startup-critical path.

This does **not** mean splits should stop being hand-entered. The map settled that
splits are hand-entered events present in the data model from day one, and this
finding does not overturn it. What it enables is a *check*: the app can compare
detected splits against entered ones and warn about a missing entry. That is a
separate ticket, and a much smaller one than "detect splits automatically."

---

## Ticker validation

Yahoo has a real search endpoint, free and keyless:

`GET https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5&newsCount=0`

| Query | Result |
|---|---|
| `AAPL` | first = `{'symbol':'AAPL','shortname':'Apple Inc.','quoteType':'EQUITY','exchange':'NMS'}` |
| `BRK-B` | first = `{'symbol':'BRK-B','shortname':'Berkshire Hathaway Inc. New','quoteType':'EQUITY','exchange':'NYQ'}` |
| `tesla` | first = `TSLA` — name search works, not just symbols |
| `ZZZZFAKE` | **`quotes` count = 0** — clean and unambiguous |

This is the right mechanism: one cheap call, and a `0 results` signal that is
distinct from every network error. Validate-by-fetch is worse, because a fetch
failure is ambiguous between "bad ticker" and "no network".

**It must be filtered.** Search is fuzzy and international — `AAPL` also returns
`AAPL19.BK` (Thailand), `AAPLC.BA` (Buenos Aires), `AAPL.VI` (Vienna). For a
USD-only app: require `quoteType == 'EQUITY'` and a US `exchange`
(`NMS`, `NYQ`, `NGM`, `PCX`, `ASE`), and **reject `quoteType == 'ETF'`**.

That ETF rejection is not hypothetical — see below.

---

## The staleness trap

**Whatever source is chosen, the app must compare the source's timestamp against
now and refuse any price older than one trading session.** Without that check,
both of the following put a confident wrong number into the portfolio.

**`FB` returns a live price for the wrong company.** Yahoo now maps the ticker to
*ProShares S&P 500 Dynamic Daily Buffer ETF*. `fast_info` returns `45.043` with no
timestamp and no indication anything is wrong. The raw endpoint gives it away
twice — `instrumentType: 'ETF'` and a `regularMarketTime` **4.25 days old**, with
`regularMarketVolume: 45`. Nothing in either payload says "stale". Only comparing
the timestamp to the clock reveals it.

**`TWTR` on CNBC returns `code: 0` and a price from 2022.** Success code, plausible
number: `last: '53.70'`, `last_time: '2022-10-27T16:00:00.000-0500'`. A naive
`float(q['last'])` reads a four-year-old price as current. The `name` field
contains `"(delisted)"` and `last_time` gives it away — but only if you look.

This is the single most important finding for a daily-opened app, and it is why
the staleness guard belongs in the fetch layer rather than the UI: by the time a
price reaches the screen it looks like every other price.

Note that **no source returns an error when the market is closed.** All of them
return the last close and correctly label it (`marketState: 'POSTPOST'`,
`curmktstatus: 'POST_MKT'`, `regularMarketTime` = 16:00:01). Interpreting that is
the app's job. So the guard cannot be "reject anything not from today" — it has to
be session-aware, which is exactly what `currentTradingPeriod` is for.

---

## Example code

Requires `pip install curl_cffi requests`. No API key.

This was executed, not just written. It fetches all six tickers successfully;
`ZZZZFAKE` and `TWTR` raise `PriceUnavailable`, `FB` is rejected as an ETF, the
CNBC fallback returns `BRK-B` at 504.32 matching Yahoo to the cent, and a dead
network produces the failure dict rather than an exception.

```python
"""Fetch price snapshots for several US equities.

Primary source: Yahoo's chart endpoint. Fallback: CNBC's quote endpoint.
A price snapshot is a price together with the time it was fetched
(see CONTEXT.md) -- this module never returns one without the other.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import requests
from curl_cffi import requests as curl_requests

TIMEOUT_SECONDS = 5  # not the 30s curl_cffi default: a dead network must fail fast
MAX_AGE = dt.timedelta(days=4)  # tolerates a long weekend plus a public holiday

YAHOO_CHART = "https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
YAHOO_SEARCH = "https://query2.finance.yahoo.com/v1/finance/search"
CNBC_QUOTE = (
    "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
)


class PriceUnavailable(Exception):
    """No usable price for this ticker. The ticker is the problem."""


class SourceUnreachable(Exception):
    """The source could not be reached at all. The network is the problem."""


@dataclass(frozen=True)
class PriceSnapshot:
    ticker: str
    price: float
    currency: str
    quoted_at: dt.datetime  # when the source says the price is from
    fetched_at: dt.datetime  # when we successfully reached the source
    source: str

    @property
    def age(self) -> dt.timedelta:
        return self.fetched_at - self.quoted_at


def _check_freshness(snapshot: PriceSnapshot) -> PriceSnapshot:
    """Reject a plausible-looking price that is actually years old.

    Yahoo returns a live-looking quote for FB (now an unrelated ETF) and CNBC
    returns a 2022 price for TWTR with a success code. Both are caught here.
    """
    if snapshot.age > MAX_AGE:
        raise PriceUnavailable(
            f"{snapshot.ticker}: price is {snapshot.age.days} days old "
            f"(quoted {snapshot.quoted_at.isoformat()}) -- refusing it"
        )
    return snapshot


def fetch_from_yahoo(ticker: str, session) -> PriceSnapshot:
    try:
        response = session.get(
            YAHOO_CHART.format(ticker=ticker),
            params={"range": "1d", "interval": "1d"},
            timeout=TIMEOUT_SECONDS,
        )
    except curl_requests.exceptions.RequestException as error:
        # Covers Timeout and DNSError: the source, not the ticker, is at fault.
        raise SourceUnreachable(f"Yahoo unreachable: {error}") from error

    if response.status_code == 404:
        raise PriceUnavailable(f"{ticker}: unknown or delisted at Yahoo")
    if response.status_code != 200:
        raise SourceUnreachable(f"Yahoo returned HTTP {response.status_code}")

    meta = response.json()["chart"]["result"][0]["meta"]

    if meta.get("instrumentType") != "EQUITY":
        raise PriceUnavailable(
            f"{ticker}: not an equity but {meta.get('instrumentType')!r}"
        )

    return _check_freshness(
        PriceSnapshot(
            ticker=meta["symbol"],
            price=meta["regularMarketPrice"],
            currency=meta["currency"],
            quoted_at=dt.datetime.fromtimestamp(
                meta["regularMarketTime"], tz=dt.timezone.utc
            ),
            fetched_at=dt.datetime.now(dt.timezone.utc),
            source="yahoo",
        )
    )


def fetch_all_from_cnbc(tickers: list[str]) -> dict[str, PriceSnapshot]:
    """The fallback. One request for every ticker -- CNBC batches natively."""
    # CNBC writes Berkshire class B as BRK.B where Yahoo writes BRK-B.
    to_cnbc = {t: t.replace("-", ".") for t in tickers}
    from_cnbc = {v: k for k, v in to_cnbc.items()}

    try:
        response = requests.get(
            CNBC_QUOTE,
            params={
                "symbols": "|".join(to_cnbc.values()),  # pipe, not comma
                "requestMethod": "itv",
                "partnerId": "2",
                "output": "json",
                "exthrs": "1",
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise SourceUnreachable(f"CNBC unreachable: {error}") from error

    quotes = response.json()["FormattedQuoteResult"]["FormattedQuote"]
    fetched_at = dt.datetime.now(dt.timezone.utc)
    snapshots = {}

    for quote in quotes:
        if quote.get("code") != 0:  # 1 means CNBC does not know this symbol
            continue
        ticker = from_cnbc.get(quote["symbol"], quote["symbol"])
        snapshot = PriceSnapshot(
            ticker=ticker,
            price=float(quote["last"]),  # every CNBC number arrives as a string
            currency=quote["currencyCode"],
            quoted_at=dt.datetime.fromisoformat(quote["last_time"]),
            fetched_at=fetched_at,
            source="cnbc",
        )
        try:
            snapshots[ticker] = _check_freshness(snapshot)
        except PriceUnavailable:
            continue  # e.g. TWTR, which CNBC reports successfully with a 2022 price

    return snapshots


def ticker_exists(query: str) -> bool:
    """Confirm a typed ticker before saving a transaction against it."""
    US_EXCHANGES = {"NMS", "NYQ", "NGM", "PCX", "ASE"}
    with curl_requests.Session(impersonate="chrome") as session:
        response = session.get(
            YAHOO_SEARCH,
            params={"q": query, "quotesCount": 5, "newsCount": 0},
            timeout=TIMEOUT_SECONDS,
        )
    return any(
        quote.get("symbol") == query
        and quote.get("quoteType") == "EQUITY"  # rejects the FB-style ETF trap
        and quote.get("exchange") in US_EXCHANGES
        for quote in response.json().get("quotes", [])
    )


def fetch_prices(tickers: list[str]) -> tuple[dict[str, PriceSnapshot], dict[str, str]]:
    """Fetch every ticker, falling back to CNBC if Yahoo is unreachable.

    Returns the snapshots obtained and, separately, the tickers that failed with
    the reason for each. The caller shows last known prices for the failures --
    never an empty screen.
    """
    snapshots: dict[str, PriceSnapshot] = {}
    failures: dict[str, str] = {}

    # impersonate="chrome" is not optional: Yahoo answers 429 to any client whose
    # TLS fingerprint is not a browser's, regardless of headers.
    with curl_requests.Session(impersonate="chrome") as session:
        for ticker in tickers:
            try:
                snapshots[ticker] = fetch_from_yahoo(ticker, session)
            except PriceUnavailable as error:
                failures[ticker] = str(error)
            except SourceUnreachable:
                failures.clear()
                break  # Yahoo is down entirely; try the fallback for everything
        else:
            return snapshots, failures

    try:
        snapshots = fetch_all_from_cnbc(tickers)
    except SourceUnreachable as error:
        return {}, {t: f"all sources unreachable: {error}" for t in tickers}

    for ticker in tickers:
        if ticker not in snapshots:
            failures.setdefault(ticker, "no usable price from any source")
    return snapshots, failures


if __name__ == "__main__":
    portfolio = ["AAPL", "MSFT", "NVDA", "BRK-B", "JNJ", "WMT"]
    prices, problems = fetch_prices(portfolio)

    for ticker, snapshot in prices.items():
        print(
            f"{ticker:6} {snapshot.price:>10.2f} {snapshot.currency} "
            f"quoted {snapshot.quoted_at:%Y-%m-%d %H:%M} UTC "
            f"via {snapshot.source}"
        )
    for ticker, reason in problems.items():
        print(f"{ticker:6} FAILED -- {reason}")

    print(f"\nFB is an equity: {ticker_exists('FB')}")        # False -- now an ETF
    print(f"AAPL is an equity: {ticker_exists('AAPL')}")      # True
    print(f"ZZZZFAKE is an equity: {ticker_exists('ZZZZFAKE')}")  # False
```

---

## Open questions this raises

Not resolved here, and small enough to be their own tickets:

- **Live-market behaviour is untested.** Everything above was measured with the
  market closed. Yahoo equity data is exchange-delayed roughly 15 minutes during
  regular hours, but that was not verified. Worth one re-run during a session
  before the fetch layer is considered settled.
- **Splits as a cross-check** rather than automatic entry, per the section above.
- **The `MAX_AGE` constant is a guess.** Four days tolerates a long weekend plus a
  holiday, but the session-aware version using `currentTradingPeriod` is more
  correct. Whether the extra complexity is worth it is a judgement for #5.
