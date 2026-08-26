"""Phase 1c: FIFO versus weighted average cost on one realistic history."""

from decimal import Decimal as D

BUYS = [(D("10"), D("100.00"), "2024-03-04"),
        (D("20"), D("150.00"), "2024-06-10"),
        (D("30"), D("200.00"), "2024-09-16")]
SELL_Q, SELL_P = D("25"), D("220.00")

total_sh = sum(q for q, _, _ in BUYS)
total_cost = sum(q * p for q, p, _ in BUYS)

print(f"History: buys 10@100, 20@150, 30@200; then sell {SELL_Q} @{SELL_P}")
print(f"Total held before sale: {total_sh} sh, total cost ${total_cost}")
print()

# ---- weighted average
avg = total_cost / total_sh
w_cost = SELL_Q * avg
w_realised = SELL_Q * SELL_P - w_cost
print(f"WEIGHTED AVERAGE")
print(f"  average cost        : ${avg:.4f}")
print(f"  cost of sold lots   : {SELL_Q} x ${avg:.4f} = ${w_cost:.2f}")
print(f"  realised profit     : ${SELL_Q * SELL_P} - ${w_cost:.2f} = ${w_realised:.2f}")
print(f"  remaining basis     : ${total_cost - w_cost:.2f} over {total_sh - SELL_Q} sh")
print()

# ---- FIFO
left = SELL_Q
fifo_cost = D(0)
for q, p, _ in BUYS:
    take = min(left, q)
    fifo_cost += take * p
    left -= take
    if left == 0:
        break
f_realised = SELL_Q * SELL_P - fifo_cost
print(f"FIFO")
print(f"  lots consumed       : 10 @ $100 then 15 @ $150")
print(f"  cost of sold lots   : ${fifo_cost:.2f}")
print(f"  realised profit     : ${SELL_Q * SELL_P} - ${fifo_cost:.2f} = ${f_realised:.2f}")
print(f"  remaining basis     : ${total_cost - fifo_cost:.2f} over {total_sh - SELL_Q} sh")
print()
print(f"DIVERGENCE: FIFO realises ${f_realised - w_realised:.2f} more "
      f"({(f_realised / w_realised - 1) * 100:.1f}% higher) on the identical trade history")
print(f"At the Polish rate of 19%: tax due differs by ${(f_realised - w_realised) * D('0.19'):.2f}")
