"""Edge cases v2 -- corrected fixtures, real threshold pass."""

from rebalance import PORTFOLIO, rows_of, gaps_for, plan_minmax, score

MIN_TRADE = 50.0   # candidate minimum-trade threshold


def apply_threshold(rows, C, gaps, min_trade):
    """Drop sub-threshold trades, re-water-fill the rest, repeat until stable.
    Returns (alloc, unspent_dollars)."""
    alive = {t for t, g in gaps.items() if g > 0}
    while True:
        sub = [(r[0], r[1], r[2], r[3], r[4]) for r in rows if r[0] in alive]
        alloc = plan_minmax(sub, C, {t: gaps[t] for t in alive})
        small = {t for t in alive
                 if 0 < round(alloc.get(t, 0) / next(r[1] for r in rows if r[0] == t), 4)
                 * next(r[1] for r in rows if r[0] == t) < min_trade}
        if not small:
            spent = sum(round(round(v / next(p for tt, p, *_ in rows if tt == t), 4)
                              * next(p for tt, p, *_ in rows if tt == t), 2)
                        for t, v in alloc.items())
            return alloc, C - spent
        alive -= small
        if not alive:
            return {}, C


print("=== minimum-trade threshold on the SMALL contribution ($1,000) ===")
rows = rows_of()
C = 1000.0
gaps, _ = gaps_for(rows, C)
raw = plan_minmax(rows, C, gaps)
print("without threshold:")
for t, p, sh, tw, v in rows:
    if raw.get(t, 0) > 0:
        n_sh = round(raw[t] / p, 4)
        print(f"  {t:>7}: buy ${round(n_sh*p,2):>8.2f} ({n_sh:.4f} sh)")
alloc, unspent = apply_threshold(rows, C, gaps, MIN_TRADE)
print(f"with ${MIN_TRADE:.0f} minimum trade:")
for t, p, sh, tw, v in rows:
    if alloc.get(t, 0) > 0:
        n_sh = round(alloc[t] / p, 4)
        print(f"  {t:>7}: buy ${round(n_sh*p,2):>8.2f} ({n_sh:.4f} sh)")
print(f"  unspent: ${unspent:.2f}")

print("\n=== rounding residuals: every buy quantised to 4 dp ===")
C = 60000.0
gaps, _ = gaps_for(rows, C)
big = plan_minmax(rows, C, gaps)
want = total_got = 0.0
for t, p, sh, tw, v in rows:
    x = big.get(t, 0)
    if x > 0:
        n_sh = round(x / p, 4)
        want += x
        total_got += round(n_sh * p, 2)
print(f"wanted to deploy ${want:.2f}, actually deployed ${total_got:.2f}, "
      f"residual ${want-total_got:.2f} across 9 positions")

print("\n=== case 3 fixed: one position EXACTLY at target, small contribution ===")
# AAPL exactly at 12%, MSFT exactly at 12%; others deliberately off
# values chosen so AAPL and MSFT sit EXACTLY at their targets
at_t = [("AAPL", 309.9, 12000/309.9, 12.0),
        ("MSFT", 430.0, 12000/430.0, 12.0),
        ("NVDA", 175.0, 36000/175.0, 8.0),      # overweight: 36% vs 8%
        ("BRK-B", 505.0, 40000/505.0, 25.0)]    # overweight: 40% vs 25%
rows3 = rows_of(at_t)
V3 = sum(r[4] for r in rows3)
print(f"initial weights: " + ", ".join(f"{t} {v/V3*100:.2f}%/{tw*100:.0f}%" for t,p,s,tw,v in rows3))
gaps3, _ = gaps_for(rows3, 1000.0)
b3 = plan_minmax(rows3, 1000.0, gaps3)
for t, p, sh, tw, v in rows3:
    n_sh = round(b3.get(t, 0)/p, 4)
    print(f"  {t:>7}: buy ${round(n_sh*p,2):>8.2f}  (drift was {gaps3[t]/(V3+1000)*100:+.2f} pp)")

print("\n=== case 7a fixed: targets summing to 90% ===")
p90 = [(t, p, s, tw * 0.9) for t, p, s, tw in PORTFOLIO]
rows90 = rows_of(p90)
C = 10000.0
rows_norm = rows_of([(t, p, s, tw / 0.9) for t, p, s, tw in PORTFOLIO])
gaps_norm, _ = gaps_for(rows_norm, C)
gaps_raw = {r[0]: r[3] * (sum(r[4] for r in rows90) + C) - r[4] for r in rows90}
bn = plan_minmax(rows90, C, gaps_norm)
br = plan_minmax(rows90, C, gaps_raw)
diffs = []
for t, p, sh, tw, v in rows90:
    a_n, a_r = bn.get(t, 0), br.get(t, 0)
    if abs(a_n - a_r) > 0.5:
        diffs.append(f"{t}: normalised ${a_n:.0f} vs raw ${a_r:.0f}")
tn, mn = score(rows90, bn, sum(r[4] for r in rows90) + C)
tr, mr = score(rows90, br, sum(r[4] for r in rows90) + C)
print("allocations that differ between 'silently normalise' and 'take literally':")
for d in diffs[:6]:
    print("  " + d)
print(f"scores: normalised sum|drift|={tn*100:.1f}pp max={mn*100:.1f}pp | "
      f"raw sum|drift|={tr*100:.1f}pp max={mr*100:.1f}pp")
