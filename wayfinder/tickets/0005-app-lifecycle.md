---
id: 0005
title: Application lifecycle and launching
labels: [wayfinder:grilling]
parent: ../map.md
status: open
assignee: null
blocked_by: [0001]
---

# Application lifecycle and launching

## Question

What happens between wanting to open the app and looking at current data?

To settle:

1. **How it starts.** A terminal command? A double-clickable `.command` script? Should the server run continuously in the background, or start on demand?
2. **What startup does.** The order: load data → fetch prices → recompute → render. Does the price fetch block the page, or does the page render immediately with stale prices and refresh once the fetch lands?
3. **How long the fetch takes.** With a dozen or so tickers — sequential or concurrent? Is a progress indicator needed?
4. **Refreshing mid-session.** Is there a "fetch prices now" button, or only the startup fetch?
5. **Shutdown.** What stops the server, and what happens to unsaved data.
6. **One user, one instance.** What happens when the app is launched twice — port already bound, two processes writing the same file.
7. **Where logs and errors go.** When a price fetch fails, there has to be somewhere to look.

## Context

Settled during grilling, taken as given here:

- FastAPI serving on `localhost`.
- Prices fetched at application startup.
- No network → last known prices with their timestamp, never an empty screen.
- The user is learning Python — prefer solutions that read clearly in Python over clever ones.

## Deliverable

The application lifecycle described from launch to shutdown, with explicit behaviour for every failure mode.
