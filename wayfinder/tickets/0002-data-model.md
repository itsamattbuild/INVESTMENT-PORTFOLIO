---
id: 0002
title: Data model and on-disk format
labels: [wayfinder:grilling]
parent: ../map.md
status: open
assignee: null
blocked_by: [0001]
---

# Data model and on-disk format

## Question

What exactly sits on disk, and what is the schema of each entity?

To settle:

1. **Storage format.** SQLite or JSON files? SQLite gives queries, transactionality, and resilience against an interrupted write; JSON is readable by eye, editable by hand, and diffable in git. Hard to reverse later.
2. **Transaction schema.** Fields: ticker, kind (buy / sell / split), share count, price, date, commission, note. Which are required, which optional, and which numeric types (`Decimal` or `float` — with money this is not cosmetic).
3. **Split event schema.** How to represent a 10:1 split so that recomputing the position and average cost comes out right, and so a mistaken entry can be undone.
4. **Target weight schema.** Persistent, per company. Where do they live — alongside transactions or separately? What happens to the target of a company sold down to zero?
5. **Price cache.** Its shape depends on the outcome of ticket 0001. What is stored, for how long, and whether price history is kept or only the latest value.
6. **Data file layout.** The location is already fixed (`~/Library/Application Support/`, outside the repo tree — see Context). What remains: one file or several, naming, and whether the path should be overridable by an environment variable for testing.
7. **Deriving a position from transactions.** Weighted average cost, event ordering, and how sales are handled (which cost method — average or FIFO; this affects realised P/L and tax reporting).

## Context

Settled during grilling, taken as given here:

- Transaction-based, not position-based. Transactions are facts; positions are results.
- No cash as a persistent entity.
- Fractional shares, rounded to 4 decimal places.
- P/L split into realised and unrealised.
- Splits as hand-entered events, present in the model from day one.
- Commission optional, defaulting to 0.
- **Data lives outside the repo tree** — under `~/Library/Application Support/`. The repo is public, so this is the only arrangement in which an accidental commit of transaction data is structurally impossible rather than merely unlikely. Not up for renegotiation in this ticket.
- **Every monetary value carries a currency field**, though v1 is always `USD`. Multi-currency is not being built — the point is only that adding it later should not be a data migration.
- Field names and identifiers in English.

## Deliverable

The schema of every entity, with the storage format choice justified. `CONTEXT.md` updated with any terms that sharpen along the way.
