"""Rebalancing definitions A and B on one fixed portfolio -- corrected.

A. minimise the SUM of absolute drifts          (L1)
B. minimise the LARGEST absolute drift          (L-inf)

Contribute-only (x >= 0), weights vs positions only, fractional shares
to 4 dp. Definition B implemented properly:
  - when C cannot fill all underweights: lift the DEEPEST underweights to a
    common shortfall level L (water-filling from below), L found by bisection;
  - when C overfills: fill every gap, then spread the surplus equally among
    the filled positions (that keeps the maximum overshoot smallest).
"""

PORTFOLIO = [
    ("AAPL",  309.90,  50.0, 12.0),
    ("MSFT",  430.00,  20.0, 12.0),
    ("NVDA",  175.00, 100.0,  8.0),
    ("GOOGL", 200.00,  30.0, 10.0),
    ("AMZN",  230.00,  25.0, 10.0),
    ("META",  740.00,  10.0,  8.0),
    ("TSLA",  350.00,  15.0,  5.0),
    ("BRK-B", 505.00,  20.0, 15.0),
    ("JPM",   300.00,  25.0, 10.0),
    ("WMT",   100.00, 110.0, 10.0),
]


def rows_of(portfolio=None):
    return [(t, p, s, tw / 100.0, p * s)
            for t, p, s, tw in (portfolio or PORTFOLIO)]


def gaps_for(rows, C):
    Vc = sum(r[4] for r in rows) + C
    return {r[0]: r[3] * Vc - r[4] for r in rows}, Vc


def plan_greedy(rows, C, gaps):
    """Definition A needs a tie-break; 'biggest gap first' is the usual one."""
    alloc = {r[0]: 0.0 for r in rows}
    left = C
    for t in sorted(gaps, key=lambda t: -gaps[t]):
        take = min(max(0.0, gaps[t]), left)
        alloc[t] += take
        left -= take
        if left <= 1e-9:
            break
    if left > 1e-6:
        alloc[sorted(gaps, key=lambda t: -gaps[t])[0]] += left   # surplus dumped
    return alloc


def plan_minmax(rows, C, gaps):
    """Definition B, canonical."""
    pos = {t: g for t, g in gaps.items() if g > 0}
    total_pos = sum(pos.values())
    alloc = {r[0]: 0.0 for r in rows}
    if not pos:
        # every position is at/over target and selling is off:
        # there is nowhere sensible to put the contribution.
        return alloc
    if C <= total_pos:
        # water-filling: lift deepest gaps to a common shortfall L
        def spend(L):
            return sum(max(0.0, g - L) for g in pos.values())
        lo, hi = 0.0, max(pos.values())
        for _ in range(200):
            mid = (lo + hi) / 2
            if spend(mid) > C:
                lo = mid
            else:
                hi = mid
        L = hi
        for t, g in pos.items():
            alloc[t] = max(0.0, g - L)
    else:
        # fill everything, spread surplus equally among the filled names
        for t, g in pos.items():
            alloc[t] = g
        surplus = (C - total_pos) / len(pos)
        for t in pos:
            alloc[t] += surplus
    return alloc


def score(rows, alloc, Vc):
    # returns (sum|drift|, max|drift|)
    tot = mx = 0.0
    for t, p, sh, tw, v in rows:
        d = (v + alloc.get(t, 0.0)) / Vc - tw
        tot += abs(d)
        mx = max(mx, abs(d))
    return tot, mx


def show(title, rows, alloc, Vc, threshold=0.0):
    print(f"\n{title}")
    print(f"{'ticker':>7} {'now':>7} {'target':>7} {'buy$':>9} {'shares':>9} {'after':>7} {'drift':>8}")
    tot = mx = 0.0
    trades = 0
    for t, p, sh, tw, v in rows:
        x = alloc.get(t, 0.0)
        shares = round(x / p, 4)
        spent = round(shares * p, 2)
        if shares > 0:
            trades += 1
        d = (v + spent) / Vc - tw
        tot += abs(d)
        mx = max(mx, abs(d))
        mark = "" if shares == 0 or spent >= threshold else f"   <- below ${threshold:.0f} threshold"
        print(f"{t:>7} {v/Vc*100:>6.2f}% {tw*100:>6.1f}% {spent:>9.2f} {shares:>9.4f} "
              f"{(v+spent)/Vc*100:>6.2f}% {d*100:>+7.2f}%{mark}")
    print(f"  trades: {trades}, sum|drift|={tot*100:.2f} pp, max|drift|={mx*100:.2f} pp")
    return tot, mx, trades


def compare(C, rows=None):
    rows = rows or rows_of()
    V = sum(r[4] for r in rows)
    Vc = V + C
    gaps, _ = gaps_for(rows, C)
    a = plan_greedy(rows, C, gaps)
    b = plan_minmax(rows, C, gaps)
    ta, ma = score(rows, a, Vc)
    tb, mb = score(rows, b, Vc)
    print("=" * 76)
    print(f"CONTRIBUTION ${C:,.0f}   (portfolio ${V:,.0f})")
    show(f"A  biggest-gap-first:", rows, a, Vc)
    show(f"B  water-filling (equalise shortfalls):", rows, b, Vc)
    print(f"\n  scores:  A sum|drift|={ta*100:6.2f} pp max={ma*100:5.2f} pp"
          f"   |  B sum|drift|={tb*100:6.2f} pp max={mb*100:5.2f} pp")
    diff = {r[0] for r in rows if abs(a.get(r[0], 0) - b.get(r[0], 0)) > 0.01}
    print(f"  allocations differ for: {', '.join(sorted(diff)) or '(identical)'}")
    return rows, a, b


if __name__ == "__main__":
    for C in (1000.0, 10000.0, 60000.0):
        compare(C)
