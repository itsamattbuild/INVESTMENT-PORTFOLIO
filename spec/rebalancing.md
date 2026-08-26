# Rebalancing decision pack

Prepared for [issue #3](https://github.com/itsamattbuild/INVESTMENT-PORTFOLIO/issues/3).
The ticket stays open. What follows turns "as close as possible to target"
from a slogan into concrete allocations you can eyeball, plus an edge-case
table ready to become tests. Every number is reproducible:
`spec/bench/rebalance.py` and `spec/bench/edge_cases*.py` on this branch,
no third-party packages.

Constraints held throughout (from the map): contribute-only default (`x ≥ 0`),
full mode opt-in, weights measured against positions only, fractional shares to
4 dp.

## The fixed example portfolio

10 US tickers, realistic prices, targets that do *not* match current holdings
(portfolio value **$94,595**, targets sum to exactly 100%):

| Ticker | Price | Held | Value | Weight | Target |
|---|---|---|---|---|---|
| AAPL | 309.90 | 50 | 15,495 | 16.38% | 12% |
| MSFT | 430.00 | 20 | 8,600 | 9.09% | 12% |
| NVDA | 175.00 | 100 | 17,500 | 18.50% | 8% |
| GOOGL | 200.00 | 30 | 6,000 | 6.34% | 10% |
| AMZN | 230.00 | 25 | 5,750 | 6.08% | 10% |
| META | 740.00 | 10 | 7,400 | 7.82% | 8% |
| TSLA | 350.00 | 15 | 5,250 | 5.55% | 5% |
| BRK-B | 505.00 | 20 | 10,100 | 10.68% | 15% |
| JPM | 300.00 | 25 | 7,500 | 7.93% | 10% |
| WMT | 100.00 | 110 | 11,000 | 11.63% | 10% |

NVDA sits far overweight — deliberately, because that is the realistic hard case.

## 1. The two definitions, computed

- **A — minimise the sum of absolute drifts** (L1). Implemented as its usual
  tie-break, "fill biggest gaps first"; also as smallest-first for a control.
- **B — minimise the largest single drift** (L∞). Implemented canonically as
  **water-filling**: lift the deepest underweights to a *common* shortfall level
  `L` (bisection on `Σ max(0, gᵢ − L) = C`); when the money overfills all gaps,
  spread the surplus equally among the filled names.

### Small contribution — $1,000

| | Definition A (biggest-gap) | Definition B (water-filling) |
|---|---|---|
| Trades | 1 | 3 |
| Allocation | BRK-B $1,000.00 | BRK-B $703.16, AMZN $273.42, GOOGL $23.42 |
| Resulting shortfalls | BRK-B −3.39 pp; others untouched | all three end at exactly **−3.70 pp** |

### Medium contribution — $10,000

| | A | B |
|---|---|---|
| Trades | 2 | 5 |
| Allocation | AMZN $4,410.76, BRK-B $5,589.24 (both filled to ~0 drift) | MSFT $1,617.57, GOOGL $2,125.68, AMZN $2,375.67, BRK-B $3,255.43, JPM $625.68 — **all ending at −2.23 pp** |
| Left untouched | GOOGL still −4.26 pp | nothing deeper than −2.23 pp among fundable names |

### Large contribution — $60,000

| | A | B |
|---|---|---|
| Trades | 8 | 9 |
| Shape | MSFT, GOOGL, AMZN, META, BRK-B, JPM, WMT filled to exactly 0 drift; AAPL gets $403.74, TSLA nothing | every fundable name lifted to a common −0.37 pp |
| Residual | NVDA +3.32 pp (unfixable without selling) | same NVDA +3.32 pp |

### Where they diverge, by how much

The allocations differ substantially — at $10k, five tickers differ; at $60k,
nine do. But the headline finding is stranger and more useful:

**In every scenario tested, both definitions produce identical scores —
identical sum-of-drifts AND identical max-drift.** Two independent reasons:

1. Any plan that spends only on underweights (never overshooting a target)
   reduces the sum of absolute drifts by exactly $1 per dollar spent. So *all*
   such plans tie under definition A — including wildly different ones. Verified
   directly: biggest-gap-first and smallest-gap-first produce completely
   different portfolios (e.g. at $10k, A fills AMZN+BRK-B; A′ fills
   MSFT+META+JPM) with the **same 24.16 pp total drift**. Definition A alone
   does not determine an allocation; a tie-break does all the work.
2. While one unshrinkable overweight exists (NVDA +10.31 pp at $1k, +8.73 pp at
   $10k, +3.32 pp at $60k), that position pins the max-drift. Every plan that
   keeps all other positions below it ties under definition B too.

**Consequence:** the argument between A and B dissolves. Neither metric ranks
realistic plans. What actually decides what the user sees is the *tie-break
policy*: concentrate ("fix few names fully") versus equalise ("improve all deep
names together"). Water-filling is the canonical equaliser: deterministic,
order-independent, treats equal gaps equally, degrades gracefully from $1 to
$1M, and coincides with A whenever A is uniquely determined.

**Recommendation:** adopt B-canonical (water-filling) as the algorithm and say
so in these terms — not because L∞ "beats" L1, but because it is the only
proposal on the table that yields one well-defined answer without arbitrary
ordering effects.

## 2. Targets unreachable without selling — said out loud

NVDA holds 18.50% against an 8% target. Contribute-only can only dilute it by
growing everything else. Flat prices, all contribution deployed elsewhere:

| Contribution pace | Diluted to 10% after | Diluted to 8% after |
|---|---|---|
| $5k/month | ~16.1 months | ~24.8 months |
| $10k/month | ~8.0 months | ~12.4 months |

The algorithm must return the plan **plus an explicit statement**: "NVDA cannot
reach 8% without selling; at your pace expect ~N months of dilution."
Measured worst case (single-position portfolio, target 40%, contribution $5k):
the correct output is an empty plan with that message — never a junk allocation.

Related degenerate case verified: when every position is at/over target and
selling is off, there is nowhere sensible to put the money. Options: (i) report
"contribution undeployed", or (ii) park it in the closest-to-target names
(water-filling puts it there anyway, e.g. two at-target names split $500/$500).
That choice belongs to #3 — see Q4 below.

## 3. Minimum trade threshold

Without a threshold, the $1,000 water-filling suggests **buying $23.42 of
GOOGL** (0.1171 sh). With a $50 minimum trade applied iteratively (drop
sub-threshold trades, re-water-fill the remainder):

| | Without threshold | With $50 threshold |
|---|---|---|
| GOOGL | $23.42 | dropped |
| AMZN | $273.42 | $285.13 |
| BRK-B | $703.16 | $714.88 |
| Unspent | $0.00 | ≈$0.01 |

A $3 contribution against a single $505 share is absorbable fractionally
(0.0059 sh) but is noise; below-threshold contributions should produce a
message, not trades.

## 4. Rounding to 4 decimal places

Quantising every buy to 4 dp on the $60,000 plan: wanted to deploy $60,000.00,
actually deployed **$60,000.02** (residual ±$0.02 across 9 positions).
Policy implication: compute dollar amounts, round to shares, then recompute
weights from actual spend; accept cent-level residuals; never let total spend
exceed the contribution.

## 5. Targets that do not sum to 100%

With targets totalling 90%, "silently normalise" and "take literally" give
measurably different plans (e.g. BRK-B $3,674 normalised vs $2,879 literal;
GOOGL $1,963 vs $2,272). With 110%, normalisation silently *deflates* every
target by /1.1. Either way the executed policy is not the typed policy.
Hard-validation (warn and refuse until fixed) is the cheapest honest option;
the alternative is explicit labelling of the scaled targets in the UI. Choice:
#3's (Q6 below).

## 6. Edge cases — expected behaviour, ready to become tests

Computed outputs exist for every row (see `bench/edge_cases*.py`):

| # | Case | Expected result |
|---|---|---|
| 1 | Zero contribution | Empty plan; screen shows residual drifts unchanged |
| 2a | Single position, at target (100%), $5k | Buy more of it; drift stays 0 |
| 2b | Single position, target 40%, $5k | Empty plan + "unreachable without selling"; no trades |
| 3 | Position already at target, gaps elsewhere | Receives nothing while deeper gaps exist; participates in surplus only after all gaps are filled (verified: two at-target names split the whole $1k when everything else was overweight) |
| 4 | Target of 0% | Contribute-only: never funded, weight dilutes passively (+1.73 pp shown drifting); full mode: sells entirely |
| 5 | Position with no target set | Open question (Q5): untouchable-but-flagged vs treated-as-0%. Untouchable recommended — treating as 0% implies selling a holding the user never asked to sell |
| 6 | Contribution below min trade size | Message, not trades ($3 case verified) |
| 7 | Targets sum 90% / 110% | Warn; either refuse or label scaled targets (Q6); both variants' allocations measured above |
| 8 | Sub-threshold trade produced by algorithm | Dropped and re-distributed iteratively; unspent ≈ $0.01 (verified) |
| 9 | 4-dp share rounding | Cent-level residual; total capped at contribution (verified ±$0.02 on $60k) |

## Remaining questions, numbered — each with a recommendation

**Q1. Objective/tie-break.** Adopt water-filling (B-canonical). Justification:
§1 — both metrics tie on realistic portfolios; water-filling is the unique
deterministic equalising rule and matches A wherever A is determined.

**Q2. Presenting the result.** Show per line: ticker, dollars, shares (4 dp),
weight before → after, resulting drift; plus portfolio-level "sum |drift| before
→ after" and the unreachable-targets message with months-to-dilute estimate
(§2). Cheap to compute; all inputs already exist.

**Q3. Full mode shape.** Sell to close the gap exactly (tolerance band = 0) with
the same water-filling logic run in both directions (surpluses become sells),
then apply the min-trade threshold to sells too. Tax flag: confirm-before-
execute, since selling realises gains (per map).

**Q4. Nowhere-to-put-money regime** (everything at/over target, contribute
mode): recommend reporting "contribution not deployed" rather than silently
parking it in near-target names. Honest beats clever; the water-filling variant
is implemented if preferred.

**Q5. Positions with no target.** Recommend untouchable + visible flag
("no target set"), excluded from funding but included in weights. Never infer
0%.

**Q6. Targets ≠ 100%.** Recommend hard warning with the option to proceed using
*explicitly labelled* normalised targets. Silent normalisation changes policy by
up to a full percentage point per name (§5).

**Q7. Minimum trade threshold.** Recommend $50 per trade (≈ one cheap odd-lot),
iterative removal as in §3, unspent amount reported to the cent.

*Scripts: `bench/rebalance.py` (main comparison), `bench/edge_cases.py`,
`bench/edge_cases_threshold.py`. Deterministic; no network; no dependencies.*
