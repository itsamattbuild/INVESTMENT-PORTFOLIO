"""Phase 1b: float versus Decimal on one realistic position history.

Sequence: two fractional buys, a 3:2 split, another buy, a partial sale --
then 250 further round-trip trades to see whether error accumulates.
Every step is quantised to 4 decimal places (the app's settled rule) under
both arithmetics, so the comparison isolates the *arithmetic*, not formatting.
"""

from decimal import Decimal, ROUND_HALF_UP

Q4 = Decimal("0.0001")
Q2 = Decimal("0.01")


def q4(x: Decimal) -> Decimal:
    return x.quantize(Q4, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------- scenario
STEPS = [
    ("buy",  "AAPL", "500.00", "309.90", None),        # $500 buys 1.6134 sh
    ("buy",  "AAPL", "750.00", "287.05", None),        # $750 buys 2.6128 sh
    ("split","AAPL", None,       None,     (3, 2)),    # 3:2 split
    ("buy",  "AAPL", "300.00", "322.40", None),        # top-up
    ("sell", "AAPL", "HALF",   "341.10", None),        # partial sale
]

FAST_INFO_PRICE = 309.8999938964844   # what yfinance fast_info reports for 309.9


def run_float(prices_source: str = "raw"):
    shares = 0.0
    cost = 0.0
    realised = 0.0
    log = []

    def px(p):
        # 'fast_info' models ingesting the float32 artefact unchanged
        return FAST_INFO_PRICE if prices_source == "fast_info" else p

    for kind, t, amt, price, ratio in STEPS:
        if kind == "buy":
            cash = float(amt)
            p = px(float(price))
            n_shares = q4f(cash / p)
            shares += n_shares
            cost += n_shares * p + 1.00          # $1 commission
        elif kind == "split":
            shares = q4f(shares * ratio[0] / ratio[1])
        elif kind == "sell":
            n_sell = q4f(shares / 2)
            avg = cost / shares
            proceeds = n_sell * px(float(price)) - 1.00
            realised += proceeds - n_sell * avg
            shares -= n_sell
            cost -= n_sell * avg
        log.append((kind, shares, cost))
    return shares, cost, realised, log


def q4f(x: float) -> float:
    return float(q4(Decimal(repr(x))))


def run_decimal():
    shares = Decimal(0)
    cost = Decimal(0)
    realised = Decimal(0)
    for kind, t, amt, price, ratio in STEPS:
        if kind == "buy":
            cash = Decimal(amt)
            p = Decimal(price)
            n_shares = q4(cash / p)
            shares += n_shares
            cost += n_shares * p + Decimal("1.00")
        elif kind == "split":
            shares = q4(shares * ratio[0] / ratio[1])
        elif kind == "sell":
            n_sell = q4(shares / 2)
            avg = q4(cost / shares)
            proceeds = n_sell * Decimal(price) - Decimal("1.00")
            realised += proceeds - n_sell * avg
            shares -= n_sell
            cost -= n_sell * avg
    return shares, cost, realised


print("== step-by-step: share count and cost basis, float vs Decimal ==")
fs, fc, fr, flog = run_float()
ds, dc, dr = run_decimal()
kinds = [s[0] for s in STEPS]
print(f"{'after':>8} {'shares(float)':>16} {'shares(Dec)':>14} "
      f"{'cost(float)':>14} {'cost(Dec)':>12}")
sh_d2, co_d2 = Decimal(0), Decimal(0)
dec_rows = []
for kind, t, amt, price, ratio in STEPS:
    if kind == "buy":
        nd = q4(Decimal(amt) / Decimal(price))
        sh_d2 += nd
        co_d2 += nd * Decimal(price) + Decimal("1.00")
    elif kind == "split":
        sh_d2 = q4(sh_d2 * ratio[0] / ratio[1])
    else:
        sd = q4(sh_d2 / 2)
        ad = q4(co_d2 / sh_d2)
        sh_d2 -= sd
        co_d2 -= sd * ad
    dec_rows.append((kind, sh_d2, co_d2))
for (kind, f_shares, f_cost), (d_kind, d_shares, d_cost) in zip(flog, dec_rows):
    print(f"{kind:>8} {f_shares:>16.6f} {str(d_shares)[:14]:>14} "
          f"{f_cost:>14.6f} {str(d_cost.quantize(Q2))[:12]:>12}")
ds_last, dc_last, _dr = run_decimal()

print()
print("== end state after the five steps ==")
print(f"share count : float {fs!r:<22} Decimal {ds_last}")
print(f"cost basis  : float ${fc:.6f}      Decimal ${dc_last}")
print(f"realised P/L: float ${fr:.6f}      Decimal ${dr}")

# valuation divergence from the fast_info artefact alone
import struct as _struct
n = fs
price_raw = 341.10
struct_fi = _struct.unpack('f', _struct.pack('f', 341.10))[0]
val_raw, val_fi = n * price_raw, n * struct_fi
print()
print("== the #1 data point, propagated ==")
print(f"yfinance fast_info turns 309.9 into {FAST_INFO_PRICE!r} (a float32 artefact)")
print(f"same artefact applied to a sale price of 341.10 -> {struct_fi!r}")
print(f"valuation of {n:.4f} sh at 341.10 exact : ${val_raw:,.4f}")
print(f"valuation at the artefact             : ${val_fi:,.4f}")
print(f"difference on ONE position            : ${abs(val_raw-val_fi):,.4f}")

# accumulation over many trades
print()
print("== accumulation: 250 further buy/sell round trips ==")
import random
rng = random.Random(7)
sh_f, cost_f, real_f = fs, fc, fr
sh_d, cost_d, real_d = ds_last, dc_last, dr
for i in range(250):
    p = 300 + rng.uniform(-20, 20)
    if i % 2 == 0:                                   # buy $200 worth
        nf = float(q4(Decimal(repr(200.0 / p))))
        nd = q4(Decimal("200.00") / Decimal(repr(p)))
        sh_f += nf; cost_f += nf * p + 1.0
        sh_d += nd; cost_d += nd * Decimal(repr(p)) + Decimal("1.00")
    else:                                            # sell a tenth
        sf = float(q4(Decimal(repr(sh_f / 10))))
        sd = q4(sh_d / 10)
        af = cost_f / sh_f
        ad = q4(cost_d / sh_d)
        real_f += sf * p - sf * af - 1.0
        real_d += sd * Decimal(repr(p)) - sd * ad - Decimal("1.00")
        sh_f -= sf; cost_f -= sf * af
        sh_d -= sd; cost_d -= sd * ad
print(f"share count : float {sh_f!r:<22} Decimal {q4(sh_d)}")
print(f"realised P/L: float ${real_f:,.6f}   Decimal ${real_d:,.6f}")
print(f"divergence in realised P/L after ~505 transactions: "
      f"${abs(real_f - float(real_d)):,.6f}")
