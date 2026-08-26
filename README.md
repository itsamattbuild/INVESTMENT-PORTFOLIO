# Investment Portfolio

A local-first portfolio tracker for US equities. Runs entirely on your own
machine: fetches current prices on startup, computes position weights, and
tells you what to buy or sell to reach your target allocation.

Privacy is the reason this exists. Your holdings never leave your disk.

## Status

**Planning.** No application code yet.

The design is being worked out first, one decision at a time, using the
[wayfinder](wayfinder/) method: a map of what still needs deciding, plus one
ticket per open question. The map lives in
[issue #6](https://github.com/itsamattbuild/INVESTMENT-PORTFOLIO/issues/6); its
open child issues are what is left to decide. [`CONTEXT.md`](CONTEXT.md) is the
domain glossary.

## Planned scope (v1)

- US equities, USD only
- Transactions as the source of truth; positions derived from them
- Target weight per company, persisted
- Rebalancing in two modes: contribute-only (default) and full (allows selling)
- Realised and unrealised P/L, reported separately
- Prices fetched at startup, with the fetch timestamp always visible

Deliberately out of scope for now: multi-currency, broker imports, and any LLM
integration. See the map for the reasoning.

## Stack

Python + FastAPI serving HTML on localhost. No frontend build step.

## Licence

GPL v3. See [LICENSE](LICENSE).
