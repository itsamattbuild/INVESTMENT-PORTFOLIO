"""Edge cases and remaining worked examples for issue #3."""

from rebalance import PORTFOLIO, rows_of, gaps_for, plan_minmax, plan_greedy, score


def run_case(title, portfolio, C, note="", threshold=0.0):
    rows = rows_of(portfolio)
    V = sum(r[4] for r in rows)
    gaps, _ = gaps_for(rows, C)
    b = plan_minmax(rows, C, gaps)
    print(f"\n--- {title} ---")
    print(f"portfolio ${V:,.2f}, contribution ${C:,.2f}, targets sum "
          f"{sum(r[3] for r in rows)*100:.0f}%")
    for t, p, sh, tw, v in rows:
        x = b.get(t, 0.0)
        shares = round(x / p, 4) if p else 0.0
        spent = round(shares * p, 2)
        d = (v + spent) / (V + C) - tw if V + C else 0.0
        print(f"  {t:>7} wt {v/V*100 if V else 0:6.2f}% -> target {tw*100:5.1f}% | "
              f"buy {spent:>10.2f} ({shares:>8.4f} sh) | drift {d*100:+6.2f}%")
    if note:
        print(f"  NOTE: {note}")


# 1 -- zero contribution
run_case("1. zero contribution", PORTFOLIO, 0.0,
         "plan must be empty; app should show residual drift instead")

# 2 -- single-position portfolio
single = [("AAPL", 309.90, 100.0, 100.0)]
run_case("2a. single position AT target (100%)", single, 5000.0,
         "only sane plan: buy more AAPL; drift stays 0")
single2 = [("AAPL", 309.90, 100.0, 40.0)]
run_case("2b. single position, target 40%", single2, 5000.0,
         "contribute-only CANNOT fix this; every dollar worsens max|drift| "
         "-> must say 'unreachable without selling', not return junk")

# 3 -- position already at target
at_target = [("MSFT", 430.0, 22.093, 15.0), ("NVDA", 175.0, 57.143, 25.0),
             ("JPM", 300.0, 33.333, 60.0)]
# values: MSFT 9500 (15%), NVDA 10000 (25%), JPM 10000 (60%) of 29500... make exact:
at_target = [("MSFT", 430.0, 22500/430.0, 15.0),
             ("NVDA", 175.0, 37500/175.0, 25.0),
             ("JPM",  300.0, 60000/300.0, 60.0)]
run_case("3. one position already at target", at_target, 10000.0,
         "at-target position receives nothing while gaps exist; "
         "only when C exceeds total gaps does everyone share surplus")

# 4 -- target of 0%
with_zero = PORTFOLIO + [("TSLA-old", 350.0, 5.0, 0.0)]
run_case("4. a position with 0% target", with_zero, 5000.0,
         "contribute-only never sells it: weight can only be diluted; "
         "full mode sells it entirely")

# 5 -- position with no target set
no_target = [(t, p, s, tw) for t, p, s, tw in PORTFOLIO[:5]]
rows = rows_of(no_target)
V = sum(r[4] for r in rows)
print("\n--- 5. position with no target set ---")
print(f"option A: treat as untouchable -> excluded from funding; weights still measured against ALL positions:")
for t, p, sh, tw, v in rows:
    print(f"  {t:>7}: {'HAS TARGET' if tw else 'NO TARGET'} wt={v/V*100:.2f}%")
print(f"option B: treat as 0% target -> contribute mode would starve it forever "
      f"(and full mode would sell it immediately)")

# 6 -- contribution below any sensible trade size
tiny = [("BRK-B", 505.0, 20.0, 15.0)]
run_case("6a. $3 contribution vs $505 share", tiny, 3.0,
         "fractional shares CAN absorb it (0.0059 sh) but a $3 trade is noise; "
         "minimum-trade threshold should catch it")
run_case("6b. $3 contribution vs threshold rule (<$10)", tiny, 3.0,
         "recommended: report 'contribution below minimum trade size' instead of trading")

# 7 -- targets not summing to 100%
p90 = [(t, p, s, tw * 0.9) for t, p, s, tw in PORTFOLIO]
p110 = [(t, p, s, tw * 1.1) for t, p, s, tw in PORTFOLIO]
rows90 = rows_of(p90)
C = 10000.0
gaps90, _ = gaps_for(rows90, C)
b_norm = plan_minmax(rows90, C, gaps90)
print("\n--- 7a. targets summing to 90%, normalised implicitly ---")
print("if the app silently normalises (divides by 0.9), the EFFECTIVE target for")
print("AAPL becomes 12%/0.9 = 13.33% -- the user asked for 12%. Allocation under")
b_true = plan_minmax(rows90, C, {r[0]: r[3]*(V90 := sum(r[4] for r in rows90)+C) - r[4] for r in rows90})
tb, mb = score(rows90, b_norm, sum(r[4] for r in rows90) + C)
tt, mt = score(rows90, b_true, sum(r[4] for r in rows90) + C)
print(f"  plan vs normalised targets : sum|drift|={tb*100:.2f} pp max={mb*100:.2f} pp")
print(f"  plan vs raw (sum=90%)      : sum|drift|={tt*100:.2f} pp max={mt*100:.2f} pp")
print(f"  -> the two plans differ; user intent is ambiguous until #3 picks a policy")
run_case("7b. targets summing to 110%", p110, 10000.0,
         "normalising inflates nothing--it DEFLATES everyone by /1.1; "
         "either way the user's stated policy was not what they typed")

# dilution math: unreachable overweight, contribute-only
print("\n--- dilution: NVDA at 18.31%, target 8%, contribute-only ---")
nvda_v, V0 = 17500.0, 94595.0
for label, C_m in [("$5k/month", 5000.0), ("$10k/month", 10000.0)]:
    for goal in (0.10, 0.08):
        n = (nvda_v / goal - V0) / C_m
        print(f"  {label}: NVDA diluted to {goal*100:.0f}% after ~{max(n,0):.1f} months"
              f" (flat prices, all contributions deployed elsewhere)")
