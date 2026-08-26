"""Benchmark 1: on-disk size, and time to load + derive all positions."""

import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from common import JsonStore, SqliteStore, derive_positions_float, make_transactions

N_RUNS = 200
txns = make_transactions(500)

# Some sandboxed environments deny repeated SQLite writes inside a repo
# tree; set BENCH_OUT to redirect outputs elsewhere if needed.
OUT = os.environ.get("BENCH_OUT") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
jpath = os.path.join(OUT, "portfolio.json")
spath = os.path.join(OUT, "portfolio.db")

js = JsonStore(jpath)
ss = SqliteStore(spath)
js.write_all(txns)
if os.path.exists(spath):
    os.remove(spath)
ss.write_all(txns)

print(f"transactions: {len(txns)} across 12 tickers")
print(f"JSON   size: {os.path.getsize(jpath):>8,} bytes")
print(f"SQLite size: {os.path.getsize(spath):>8,} bytes")

# sanity: both stores derive identical positions
pj = derive_positions_float(js.read_all())
ps = derive_positions_float(ss.read_all())
assert pj.keys() == ps.keys()
for t in pj:
    assert abs(pj[t]["shares"] - ps[t]["shares"]) < 1e-9
    assert abs(pj[t]["cost"] - ps[t]["cost"]) < 1e-6
print("sanity: derived positions identical between stores: OK")

def time_json():
    t0 = time.perf_counter()
    rows = js.read_all()
    derive_positions_float(rows)
    return (time.perf_counter() - t0) * 1000

def time_sqlite():
    t0 = time.perf_counter()
    rows = ss.read_all()
    derive_positions_float(rows)
    return (time.perf_counter() - t0) * 1000

for name, fn in (("JSON", time_json), ("SQLite", time_sqlite)):
    # warm-up once (page cache), then measure
    fn()
    xs = [fn() for _ in range(N_RUNS)]
    print(f"{name:>7} load+derive: median {statistics.median(xs):6.2f} ms  "
          f"min {min(xs):6.2f} ms  p90 {sorted(xs)[int(0.9 * N_RUNS)]:6.2f} ms  "
          f"(n={N_RUNS})")

# scaling check: same at 5000 transactions
txns5k = make_transactions(5000)
j5, s5 = os.path.join(OUT, "big.json"), os.path.join(OUT, "big.db")
JsonStore(j5).write_all(txns5k)
if os.path.exists(s5):
    os.remove(s5)
SqliteStore(s5).write_all(txns5k)
print(f"\nat 5000 transactions: JSON {os.path.getsize(j5):,} B, SQLite {os.path.getsize(s5):,} B")
t0 = time.perf_counter(); rows = JsonStore(j5).read_all(); derive_positions_float(rows)
t_json = (time.perf_counter() - t0) * 1000
t0 = time.perf_counter(); rows = SqliteStore(s5).read_all(); derive_positions_float(rows)
t_sql = (time.perf_counter() - t0) * 1000
print(f"at 5000 transactions load+derive: JSON {t_json:.1f} ms, SQLite {t_sql:.1f} ms")
