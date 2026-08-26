"""Benchmark 2: what 'git diff' looks like after appending one transaction."""

import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import JsonStore, SqliteStore, Txn, make_transactions

# Some sandboxed environments deny repeated SQLite writes inside a repo
# tree; set BENCH_OUT to redirect outputs elsewhere if needed.
OUT = os.environ.get("BENCH_OUT") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
ROOT = os.path.join(OUT, "gitrepo")
NEW = Txn(501, "AAPL", "buy", 3.1234, 309.90, None, None,
          "2026-08-26", "USD", 1.00, "added while benchmarking")


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True, cwd=ROOT)


def prepare():
    shutil.rmtree(ROOT, ignore_errors=True)
    os.makedirs(ROOT)
    sh("git", "init", "-q")
    txns = make_transactions(500)
    JsonStore(os.path.join(ROOT, "portfolio.json")).write_all(txns)
    SqliteStore(os.path.join(ROOT, "portfolio.db")).write_all(txns)
    # a second JSON in append-friendly format: one object per line, comma-leading
    docs = []
    import json
    for t in txns:
        docs.append(json.dumps({
            "id": t.id, "ticker": t.ticker, "kind": t.kind,
            "shares": t.shares, "price": t.price, "split_from": t.split_from,
            "split_to": t.split_to, "date": t.date, "currency": t.currency,
            "commission": t.commission, "note": t.note}, separators=(", ", ": ")))
    with open(os.path.join(ROOT, "portfolio-line.json"), "w") as f:
        f.write("[\n" + "\n".join(docs) + "\n]\n")
    sh("git", "add", ".")
    sh("git", "-c", "user.email=b@b", "-c", "user.name=b", "commit", "-qm", "baseline")


def report(name, path):
    st = sh("git", "diff", "--numstat", "--", path).stdout.strip()
    stat = sh("git", "diff", "--stat", "--", path).stdout.strip().splitlines()[-1]
    binary = sh("git", "diff", "--", path).stdout.startswith("Binary")
    size_delta = None
    print(f"\n{name}")
    print(f"  numstat: {st if not binary else '(binary)'}")
    print(f"  {stat}" + ("  [diff is BINARY - unreviewable line by line]" if binary else ""))
    return binary


prepare()
# JSON: standard indent=2 rewrite (what json.dump produces on append)
JsonStore(os.path.join(ROOT, "portfolio.json")).append(NEW)
report("JSON, pretty-printed, rewritten wholesale on append:", "portfolio.json")

# SQLite: one INSERT committed
SqliteStore(os.path.join(ROOT, "portfolio.db")).append(NEW)
report("SQLite, one row INSERTed:", "portfolio.db")

# line-oriented JSON: appending = one new line before the closing bracket
with open(os.path.join(ROOT, "portfolio-line.json")) as f:
    body = f.read()
one = (' {"id": 501, "ticker": "AAPL", "kind": "buy", "shares": 3.1234, '
       '"price": 309.9, "split_from": null, "split_to": null, "date": "2026-08-26", '
       '"currency": "USD", "commission": 1.0, "note": "added while benchmarking"}')
with open(os.path.join(ROOT, "portfolio-line.json"), "w") as f:
    f.write(body.rstrip()[:-2] + ",\n" + one + "\n]\n")
report("JSON, one-object-per-line, appended:", "portfolio-line.json")

print("\n--- actual diff text for the line-format JSON ---")
print(sh("git", "diff", "--unified=1", "--", "portfolio-line.json").stdout)
