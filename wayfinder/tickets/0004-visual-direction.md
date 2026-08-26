---
id: 0004
title: Visual direction and main screen layout
labels: [wayfinder:prototype]
parent: ../map.md
status: open
assignee: 0x-alpha
blocked_by: []
---

# Visual direction and main screen layout

## Question

What does this app look like, and which screens does it consist of?

To settle:

1. **Which screens exist at all.** Candidates: portfolio overview, transaction entry, target weight editing, rebalance results, transaction history. Separate pages, or one dense page with sections?
2. **What is on the main screen, and in what order.** This is the screen looked at every day — within a second it has to answer the question you opened it for. Establish what that question is.
3. **Visual direction.** Palette, typography, density. Apply the `frontend-design` skill, but under the constraint from the map's Notes: this is a tool, not a marketing page.
4. **How drift from target is displayed.** A number, a bar, colour? This is the central element of the whole app.
5. **How stale prices are displayed.** The timestamp has to be visible without dominating. Design the "data from 3 days ago, no network" state.
6. **Colour for gains and losses.** Green/red is the convention, but it fails for colour-blind readers and gets muddy at high data density. Settle this deliberately.

## Context

Settled during grilling, taken as given here:

- HTML + CSS + minimal JS, Jinja templates served by FastAPI. No frontend build step.
- The user-supplied `frontend-design` skill is at `wayfinder/frontend-design.md`.
- Inspiration galleries rejected: paywalled and converged on a single look. The direction is to be worked out, not copied.
- Free references if needed: the marketing pages of Snowball Analytics, Getquin, Sharesight, Kubera, Portseido.
- **All interface copy in English.** One language across the stack — a label on screen should be named the same as the field in code.

## Deliverable

A static HTML prototype with dummy data, linked from this ticket. The prototype is disposable: it exists so the user can look at it and react, not so it can become production code.
