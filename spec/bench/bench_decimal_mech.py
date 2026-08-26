"""Where float actually bites -- three concrete mechanisms, measured."""

import json
import statistics
import sys
import time
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import derive_positions_decimal, derive_positions_float, make_transactions

Q4 = Decimal("0.0001")

print("== mechanism 1: the float32 artefact flipping the 4th decimal place ==")
FAST_INFO = 309.8999938964844
RAW = 309.9
flips = []
for cash in range(100, 3000):
    n_exact = cash / RAW
    n_art = cash / FAST_INFO
    d1 = Decimal(repr(n_exact)).quantize(Q4, rounding=ROUND_HALF_UP)
    d2 = Decimal(repr(n_art)).quantize(Q4, rounding=ROUND_HALF_UP)
    if d1 != d2:
        flips.append((cash, d1, d2))
print(f"dollar amounts where buying with price {RAW} vs {FAST_INFO} yields a "
      f"DIFFERENT 4dp share count: {len(flips)} of {len(range(100, 3000))}")
for cash, d1, d2 in flips[:5]:
    print(f"  ${cash}: exact -> {d1} sh, artefact -> {d2} sh "
          f"({float(abs(d2-d1))*RAW:.4f} USD of shares silently mis-bought)")

print()
print("== mechanism 2: Python round() is banker's rounding, brokers are half-up ==")
cases = [(0.00005,), (1.61345,), (2.00015,), (0.00015,), (3.33335,)]
for (x,) in cases:
    print(f"  value {x!r:<10}: python round(x,4) = {round(x, 4)!r:<8}"
          f"   half-up = {Decimal(repr(x)).quantize(Q4, ROUND_HALF_UP)}")

print()
print("== mechanism 3: what json.dump writes for ordinary float results ==")
examples = [("0.1 + 0.2", 0.1 + 0.2),
            ("500-txn accumulated cost basis", 1102349.7103560003),
            ("NVDA share count after the fold", 555.3283000000001)]
for label, v in examples:
    print(f"  {label:<34}: stored as {json.dumps(v)}")
print("  (harmless to recompute with, but the *permanent record* carries noise")
print("   that every human reader has to mentally round away)")

print()
print("== cost of Decimal: same 500-txn derivation, both arithmetics ==")
txns = make_transactions(500)
rows_f = [t.__dict__ | {"_": None} for t in txns]
rows_d = [{**t.__dict__, "shares": t.shares, "price": t.price,
           "commission": t.commission} for t in txns]

def bench(fn, rows, n=50):
    fn(rows)
    xs = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn(rows)
        xs.append((time.perf_counter() - t0) * 1000)
    return statistics.median(xs)

tf = bench(derive_positions_float, rows_f)
td = bench(derive_positions_decimal, rows_d)
print(f"  float  : {tf:6.2f} ms")
print(f"  Decimal: {td:6.2f} ms  ({td/tf:.1f}x slower -- still sub-100 ms)")
