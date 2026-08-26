"""Shared synthetic dataset and store implementations for the #2 storage benchmark.

500 synthetic transactions across 12 tickers, deterministic seed.
Both stores hold the identical logical data; only the encoding differs.
"""

from __future__ import annotations

import json
import random
import sqlite3
from dataclasses import dataclass
from decimal import Decimal

TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META",
           "TSLA", "BRK-B", "JPM", "V", "JNJ", "WMT"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id         INTEGER PRIMARY KEY,
    ticker     TEXT NOT NULL,
    kind       TEXT NOT NULL CHECK (kind IN ('buy','sell','split')),
    shares     REAL,
    price      REAL,
    split_from INTEGER,
    split_to   INTEGER,
    date       TEXT NOT NULL,
    currency   TEXT NOT NULL DEFAULT 'USD',
    commission REAL NOT NULL DEFAULT 0,
    note       TEXT
);
CREATE INDEX IF NOT EXISTS idx_tx_ticker ON transactions(ticker);
"""


@dataclass(frozen=True)
class Txn:
    id: int
    ticker: str
    kind: str          # buy | sell | split
    shares: float      # None for split
    price: float       # None for split
    split_from: int    # None except split
    split_to: int      # None except split
    date: str          # ISO-8601
    currency: str
    commission: float
    note: str


def make_transactions(n: int = 500, seed: int = 42) -> list[Txn]:
    import datetime as dt

    rng = random.Random(seed)
    txns: list[Txn] = []
    today = dt.date(2020, 1, 2)
    prices = {t: round(rng.uniform(40, 450), 2) for t in TICKERS}
    holdings = {t: 0.0 for t in TICKERS}
    while len(txns) < n:
        today += dt.timedelta(days=rng.randint(0, 3))
        d = today.isoformat()
        t = rng.choice(TICKERS)
        prices[t] = round(prices[t] * rng.uniform(0.97, 1.03), 2)
        r = rng.random()
        if r < 0.04 and len(txns) > 20:                     # split
            num, den = rng.choice([(2, 1), (3, 1), (3, 2), (10, 1)])
            txns.append(Txn(len(txns) + 1, t, "split", None, None, den, num,
                            d, "USD", 0.0, ""))
            holdings[t] *= num / den
        elif r < 0.25 and holdings[t] > 1.0:                # sell part
            q = round(holdings[t] * rng.uniform(0.05, 0.3), 4)
            txns.append(Txn(len(txns) + 1, t, "sell", q, prices[t], None, None,
                            d, "USD", round(rng.uniform(0, 2), 2), ""))
            holdings[t] -= q
        else:                                               # buy
            q = round(rng.uniform(0.5, 30), 4)
            txns.append(Txn(len(txns) + 1, t, "buy", q, prices[t], None, None,
                            d, "USD", round(rng.uniform(0, 2), 2), ""))
            holdings[t] += q
    return txns


def derive_positions_float(rows: list[dict]) -> dict[str, dict]:
    """Fold transactions into positions using float arithmetic."""
    pos: dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: (r["date"], r["id"])):
        p = pos.setdefault(r["ticker"], {"shares": 0.0, "cost": 0.0, "realised": 0.0})
        if r["kind"] == "buy":
            p["shares"] += r["shares"]
            p["cost"] += r["shares"] * r["price"] + r["commission"]
        elif r["kind"] == "sell":
            avg = p["cost"] / p["shares"]
            q = min(r["shares"], p["shares"])
            p["realised"] += q * r["price"] - q * avg - r["commission"]
            p["shares"] -= q
            p["cost"] -= q * avg
        else:  # split
            p["shares"] *= r["split_to"] / r["split_from"]
    return pos


def derive_positions_decimal(rows: list[dict]) -> dict[str, dict]:
    """Same fold under Decimal, quantised where the app would quantise (4 dp)."""
    q4 = Decimal("0.0001")
    pos: dict[str, dict] = {}
    for r in sorted(rows, key=lambda r: (r["date"], r["id"])):
        p = pos.setdefault(r["ticker"], {"shares": Decimal(0), "cost": Decimal(0),
                                         "realised": Decimal(0)})
        if r["kind"] == "buy":
            sh = Decimal(str(r["shares"]))
            pr = Decimal(str(r["price"])) if not isinstance(r["price"], Decimal) else r["price"]
            com = Decimal(str(r["commission"]))
            p["shares"] += sh
            p["cost"] += sh * pr + com
        elif r["kind"] == "sell":
            sh = Decimal(str(r["shares"]))
            pr = Decimal(str(r["price"])) if not isinstance(r["price"], Decimal) else r["price"]
            com = Decimal(str(r["commission"]))
            avg = (p["cost"] / p["shares"]).quantize(q4)
            q = min(sh, p["shares"])
            p["realised"] += q * pr - q * avg - com
            p["shares"] -= q
            p["cost"] -= q * avg
        else:
            p["shares"] = (p["shares"] * Decimal(r["split_to"])
                           / Decimal(r["split_from"])).quantize(q4)
    return pos


# ---------------------------------------------------------------- JSON store

class JsonStore:
    """One pretty-printed file holding every transaction."""

    def __init__(self, path):
        self.path = str(path)

    def write_all(self, txns: list[Txn]) -> None:
        docs = [{
            "id": t.id, "ticker": t.ticker, "kind": t.kind,
            "shares": t.shares, "price": t.price,
            "split_from": t.split_from, "split_to": t.split_to,
            "date": t.date, "currency": t.currency,
            "commission": t.commission, "note": t.note,
        } for t in txns]
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "transactions": docs}, f, indent=2)

    def read_all(self) -> list[dict]:
        with open(self.path, encoding="utf-8") as f:
            return json.load(f)["transactions"]

    def append(self, txn: Txn) -> None:
        docs = self.read_all()
        docs.append({
            "id": txn.id, "ticker": txn.ticker, "kind": txn.kind,
            "shares": txn.shares, "price": txn.price,
            "split_from": txn.split_from, "split_to": txn.split_to,
            "date": txn.date, "currency": txn.currency,
            "commission": txn.commission, "note": txn.note,
        })
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "transactions": docs}, f, indent=2)


# ------------------------------------------------------------- SQLite store

class SqliteStore:
    def __init__(self, path):
        self.path = str(path)

    def write_all(self, txns: list[Txn]) -> None:
        con = sqlite3.connect(self.path)
        con.executescript(SCHEMA)
        con.executemany(
            "INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [(t.id, t.ticker, t.kind, t.shares, t.price, t.split_from,
              t.split_to, t.date, t.currency, t.commission, t.note) for t in txns])
        con.commit()
        con.close()

    def read_all(self) -> list[dict]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute("SELECT * FROM transactions ORDER BY id")]
        con.close()
        return rows

    def append(self, txn: Txn) -> None:
        con = sqlite3.connect(self.path)
        con.execute(
            "INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (txn.id, txn.ticker, txn.kind, txn.shares, txn.price, txn.split_from,
             txn.split_to, txn.date, txn.currency, txn.commission, txn.note))
        con.commit()
        con.close()
