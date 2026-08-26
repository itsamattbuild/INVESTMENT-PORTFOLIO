"""Benchmark 3: what an interrupted write leaves behind -- SIGKILL mid-write.

Parent spawns a writer child, lets it get partway through (tracked via progress
lines on stdout), then sends SIGKILL. The parent then inspects what is on disk
and whether it is recoverable. This is run several times per configuration.
"""

import json
import os
import signal
import sqlite3
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from common import make_transactions

TXNS = make_transactions(500)
CHILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interrupt_child.py")

CHILD_CODE = r'''
import json, os, sqlite3, sys, time
mode, path, txns_path = sys.argv[1], sys.argv[2], sys.argv[3]
txns = json.load(open(txns_path))

if mode == "json_naive":
    # The obvious implementation: rewrite the whole file in place.
    docs = list(txns)
    docs.append({"id": 501, "ticker": "AAPL", "kind": "buy", "shares": 1.0,
                 "price": 309.9, "split_from": None, "split_to": None,
                 "date": "2026-08-26", "currency": "USD", "commission": 0.0,
                 "note": ""})
    payload = json.dumps({"version": 1, "transactions": docs}, indent=2)
    with open(path, "w") as f:
        step = max(1, len(payload) // 200)
        for i in range(0, len(payload), step):
            f.write(payload[i:i+step])
            f.flush()
            os.fsync(f.fileno())          # force bytes to disk: no cheating
            print("chunk", flush=True)
            time.sleep(0.004)

elif mode == "json_atomic":
    # The safe implementation: temp file, fsync, atomic rename.
    docs = list(txns) + [{"id": 501, "ticker": "AAPL", "kind": "buy",
                          "shares": 1.0, "price": 309.9, "split_from": None,
                          "split_to": None, "date": "2026-08-26",
                          "currency": "USD", "commission": 0.0, "note": ""}]
    tmp = path + ".tmp"
    payload = json.dumps({"version": 1, "transactions": docs}, indent=2)
    with open(tmp, "w") as f:
        step = max(1, len(payload) // 200)
        for i in range(0, len(payload), step):
            f.write(payload[i:i+step])
            f.flush()
            os.fsync(f.fileno())
            print("chunk", flush=True)
            time.sleep(0.004)
    os.replace(tmp, path)
    print("done", flush=True)

elif mode == "sqlite_rows":
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY, ticker TEXT NOT NULL, kind TEXT NOT NULL,
        shares REAL, price REAL, split_from INTEGER, split_to INTEGER,
        date TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'USD',
        commission REAL NOT NULL DEFAULT 0, note TEXT)""")
    if not con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]:
        con.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        [tuple(t[k] for k in ("id","ticker","kind","shares","price",
                                              "split_from","split_to","date",
                                              "currency","commission","note"))
                         for t in txns])
        con.commit()
        print("seeded", flush=True)
    # append one new row, committed on its own -- the normal usage pattern
    time.sleep(0.05)
    con.execute("INSERT INTO transactions VALUES (501,'AAPL','buy',1.0,309.9,"
                "NULL,NULL,'2026-08-26','USD',0.0,'')")
    con.commit()
    print("row", flush=True)

elif mode == "sqlite_bigtxn":
    # worst case for SQLite: everything in ONE transaction, killed halfway
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS transactions ("
                "id INTEGER PRIMARY KEY, ticker TEXT NOT NULL, kind TEXT NOT NULL,"
                "shares REAL, price REAL, split_from INTEGER, split_to INTEGER,"
                "date TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'USD',"
                "commission REAL NOT NULL DEFAULT 0, note TEXT)")
    con.execute("BEGIN")
    for i, t in enumerate(txns):
        con.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    tuple(t[k] for k in ("id","ticker","kind","shares","price",
                                         "split_from","split_to","date","currency",
                                         "commission","note")))
        if i % 25 == 0:
            print("row", flush=True)
            time.sleep(0.004)
    con.commit()
    print("committed-all", flush=True)
'''

with open(CHILD, "w") as f:
    f.write(CHILD_CODE)

# Some sandboxed environments deny repeated SQLite writes inside a repo
# tree; set BENCH_OUT to redirect outputs elsewhere if needed.
OUT = os.environ.get("BENCH_OUT") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
json.dump([t.__dict__ for t in TXNS], open(os.path.join(OUT, "txns.json"), "w"))


def seed_json(path):
    with open(path, "w") as f:
        json.dump({"version": 1, "transactions": []}, f)


def run_and_kill(mode, path, kill_after_n_progress):
    env = dict(os.environ)
    p = subprocess.Popen([sys.executable, CHILD, mode, path,
                          os.path.join(OUT, "txns.json")],
                         stdout=subprocess.PIPE, text=True, env=env)
    seen = 0
    deadline = time.time() + 60
    while seen < kill_after_n_progress and time.time() < deadline:
        line = p.stdout.readline()
        if not line:
            break
        if line.startswith(("chunk", "row")):
            seen += 1
    p.send_signal(signal.SIGKILL)
    p.wait()


def check_sqlite(path):
    con = sqlite3.connect(path)
    n = con.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    ic = con.execute("PRAGMA integrity_check").fetchone()[0]
    con.close()
    return n, ic


print("=" * 72)
print("TEST A -- JSON rewritten in place (500 txns + 1), killed mid-write (5 runs)")
for i in range(5):
    path = os.path.join(OUT, "kill_a_{i}.json")
    seed_json(path)
    run_and_kill("json_naive", path, kill_after_n_progress=90)
    raw = open(path, "rb").read().decode("utf-8", errors="replace")
    try:
        json.loads(raw)
        verdict = "parses OK (unexpected)"
    except json.JSONDecodeError as e:
        verdict = f"UNPARSEABLE: {e.msg} at char {e.pos} ({e.pos * 100 // len(raw)}% in)"
    # the key question: is ANY of the ledger recoverable from this file?
    print(f"  run {i+1}: {os.path.getsize(path):>7,} B of ~134 kB on disk -> {verdict}")

print()
print("TEST B -- JSON via temp-file + atomic rename, killed mid-write (5 runs)")
for i in range(5):
    path = os.path.join(OUT, "kill_b_{i}.json")
    seed_json(path)
    run_and_kill("json_atomic", path, kill_after_n_progress=90)
    leftover_tmp = os.path.exists(path + ".tmp")
    data = json.load(open(path))
    ok = isinstance(data, dict) and data.get("transactions") == []
    tmp_valid = False
    if leftover_tmp:
        try:
            json.load(open(path + ".tmp"))
            tmp_valid = True
        except Exception:
            pass
    print(f"  run {i+1}: main file valid with old content intact: {ok}; "
          f"stray .tmp present: {leftover_tmp}"
          + (f" (itself {'valid' if tmp_valid else 'TRUNCATED'} JSON)" if leftover_tmp else ""))

print()
print("TEST C -- SQLite, row-at-a-time appends, killed right after a commit")
for i in range(3):
    path = os.path.join(OUT, f"kill_c_{i}.db")
    if os.path.exists(path):
        os.remove(path)
    run_and_kill("sqlite_rows", path, kill_after_n_progress=2)
    n, ic = check_sqlite(path)
    files = sorted(f for f in os.listdir(OUT)
                   if os.path.basename(path) in f)
    print(f"  run {i+1}: {n} rows visible, integrity_check={ic}, files={files}")

print()
print("TEST D -- SQLite, ALL 500 rows in one transaction, killed halfway")
for i in range(3):
    path = os.path.join(OUT, f"kill_d_{i}.db")
    if os.path.exists(path):
        os.remove(path)
    run_and_kill("sqlite_bigtxn", path, kill_after_n_progress=6)
    n, ic = check_sqlite(path)
    print(f"  run {i+1}: {n} rows visible (all-or-nothing), integrity_check={ic}")
