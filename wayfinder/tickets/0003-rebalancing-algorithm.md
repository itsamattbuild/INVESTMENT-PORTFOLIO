---
id: 0003
title: Rebalancing algorithm
labels: [wayfinder:grilling]
parent: ../map.md
status: open
assignee: null
blocked_by: []
---

# Rebalancing algorithm

## Question

How exactly does the app compute what to sell and what to buy in order to reach the target weights?

To settle:

1. **Contribute mode.** The user supplies a contribution amount; the algorithm distributes it to get as close as possible to the target weights. The question is what "as close as possible" means — minimise the sum of drifts, or minimise the largest drift? Those two definitions give different answers.
2. **Targets unreachable without selling.** A company sits at 25% against a 15% target. In contribute-only mode there is no way to shrink it except by diluting it with everything else. What happens when the contribution is too small to fix that? The algorithm has to say so outright, not quietly return a meaningless result.
3. **Full mode.** With selling allowed. Does it aim to hit targets exactly, or leave a tolerance band?
4. **Minimum trade threshold.** Whether to suggest buying $3 of something. A cutoff is probably needed.
5. **Targets that do not sum to 100%.** What the app does when targets total 90% or 110%. Hard validation, or normalisation?
6. **Positions with no target.** A holding for which no target weight was set. Treat as a 0% target (sell it off) or as untouchable?
7. **Presenting the result.** A line reading "buy 2.3741 NVDA for $431" — do we also show the weight before and after, and the residual drift?

## Context

Settled during grilling, taken as given here:

- Target weights are persistent, set per company, all editable from one place.
- Default mode is contribute-only. Full rebalancing with selling is opt-in.
- The contribution amount is an ad hoc field, never stored.
- Fractional shares, 4 decimal places.
- Weights are measured against positions alone — no cash in the denominator.

## Deliverable

The algorithm described precisely enough to implement without further questions, plus a set of edge-case scenarios with their expected results — ready to become tests.
