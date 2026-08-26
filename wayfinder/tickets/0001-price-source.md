---
id: 0001
title: Price source for US equities
labels: [wayfinder:research]
parent: ../map.md
status: open
assignee: null
blocked_by: []
---

# Price source for US equities

## Question

Where does the app get current US equity prices, and how does it behave when that source fails?

To settle:

1. **Which source.** Candidates: `yfinance` (free, unofficial, historically breaks when Yahoo changes something), Stooq (CSV, stable, US data quality unverified), Alpha Vantage / Finnhub (official APIs, free tier with limits — find out which), Tiingo. Investigate: is the library maintained, how often does it break, what are the request limits, does it need an API key.
2. **Fallback.** Whether a second source is worth having, and what switching over looks like.
3. **Response shape.** What exactly a source returns for one ticker: last price, closing price, timestamp, currency. This determines the shape of the price cache in the data model (ticket 0002).
4. **Ticker validation.** How the app confirms a typed ticker exists before the user saves a transaction against it.
5. **Splits and adjustments.** Whether the source exposes split information — this decides whether `automatic split detection` can ever come out of the fog.
6. **Failure behaviour.** Already settled: show last known prices with their timestamp. This ticket determines which failures actually occur (rate limit, no network, ticker delisted, source returns garbage) and how to tell them apart.

## Context

Settled during grilling, taken as given here:

- US equities only, USD only. No Warsaw exchange, no foreign ETFs, no FX.
- Prices are fetched at application startup.
- Every price must carry its fetch time.
- Preference: a pure-Python solution with no paid third-party service.

## Deliverable

A markdown file in the repo comparing the sources, with a recommendation and working example code that fetches prices for several tickers. The recommendation must be justified by failure risk, not by how pleasant the API is.
