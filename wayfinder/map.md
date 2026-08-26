---
labels: [wayfinder:map]
title: Local portfolio tracker for US equities
---

# Local portfolio tracker for US equities

## Destination

A complete v1 spec — settled far enough that later sessions can build the app without making design decisions of their own.

The spec must cover: the chosen price source, the data model written to disk, the rebalancing algorithm, how P/L is computed, the visual direction and screen layout, and how the app is launched.

This map is done when nothing is left to **decide** — only to build.

## Notes

**Domain.** A private portfolio tracker for one person, running entirely locally. Privacy is why the project exists: no portfolio data leaves the disk.

**Architecture settled during grilling (rounds 1–4):**

- Python + FastAPI serving on `localhost`; the front end is HTML + CSS + minimal JS, rendered with Jinja templates.
- Data stored locally on disk, managed by Python.
- v1 scope: **US equities in USD only**. One currency, one asset class.
- **Transaction-based** model: transactions (buy / sell / split) are stored; positions and average cost are derived from them.
- **No cash** as a persistent entity. Contribute mode takes an ad hoc "contribution amount" field.
- **Target weights are persistent**, set per company, all editable from one place. On startup the app shows drift from target.
- **Fractional shares** allowed, rounded to 4 decimal places.
- Rebalancing has two modes: **contribute-only** by default, **full** (with selling) opt-in. Reason: selling US equities is a taxable event.
- **Splits** are hand-entered events, present in the data model from day one.
- **P/L is split** into realised and unrealised, never summed into one number.
- **Commission** is an optional field on a transaction, defaulting to 0.
- Prices carry a **fetch timestamp** shown in the UI. No network → last known prices with their date, never an empty screen.

**Skills to invoke every session:** `grilling` and `domain-modeling`. Prototype tickets additionally use `prototype`.

**Design.** The user supplied a `frontend-design` skill (stored at `wayfinder/frontend-design.md`) — apply it, but with one constraint: **this is a tool, not a marketing page**. Spend the character budget on typography and palette; keep the data layout conventional and dense; no animation beyond feedback on an action. Inspiration galleries (Mobbin, Refero, SaaSFrame) were rejected as paywalled and visually converged.

**User preference:** the user is learning Python. Where options are otherwise equal, pick the one that puts more work in Python and less in frontend tooling.

**Repository and language.**

- The repo is **public from the first commit**: <https://github.com/itsamattbuild/INVESTMENT-PORTFOLIO>. Licensed GPL v3.
- **Portfolio data never lives inside the repo tree** — it sits outside it, under `~/Library/Application Support/`. This is a question of location, not of `.gitignore`: data outside the tree makes an accidental commit impossible rather than merely unlikely. Binding on ticket 0002.
- **Every file in the repo is written in English** — code, commits, README, docstrings, UI copy, and these planning documents alike. One language across the whole stack.
- **Every monetary value in the data model carries a currency field**, even though v1 is always `USD`. Cost: one field. Benefit: adding a second currency later is a feature rather than a data migration. This is the only concession made to extensibility — the rest (XTB, multi-currency) stays out of scope.

## Decisions so far

<!-- empty: charting resolves nothing -->

## Not yet specified

- **Portfolio value over time (equity curve).** Needs either daily snapshots — awkward when the app is opened irregularly — or fetching full price history and replaying it. Revisit once the data model is settled.
- **Dividends.** A separate event type, a separate data source, and 15% US withholding tax. Revisit after the transaction model is fixed.
- **Automatic split detection** from market data instead of hand entry. Depends on what the chosen price source can provide.
- **Treasury bonds and multi-currency.** Would pull PLN, NBP exchange rates, and accrual-based valuation into the model. Deliberately deferred, not rejected — revisit once the equity side works.
- **Backup and data format migration.** What happens when the schema changes and old files are already on disk.
- **Validation and error handling on transaction entry.** Depends on the data model.
- **Distribution.** Whether the app should be launchable without a terminal. Depends on the app lifecycle ticket.

## Out of scope

- **A local LLM managing the app.** Only makes sense once there is a stable portfolio API for it to work against. Designing it now would warp the architecture around requirements nobody can yet state. Returns as its own map.
- **Importing XTB statements.** The user deliberately defers this to a future local model rather than sending statements to a cloud model. Leaves with the LLM.
- **Anything other than US equities in USD.** The boundary of v1.

## Tickets

Open tickets live in `wayfinder/tickets/`. The frontier is every ticket that is open, unblocked, and unclaimed.

| # | Ticket | Type | Status | Blocked by |
|---|--------|------|--------|------------|
| 0001 | [Price source for US equities](tickets/0001-price-source.md) | research | open | — |
| 0002 | [Data model and on-disk format](tickets/0002-data-model.md) | grilling | open | 0001 |
| 0003 | [Rebalancing algorithm](tickets/0003-rebalancing-algorithm.md) | grilling | open | — |
| 0004 | [Visual direction and main screen layout](tickets/0004-visual-direction.md) | prototype | open | — |
| 0005 | [Application lifecycle and launching](tickets/0005-app-lifecycle.md) | grilling | open | 0001 |
