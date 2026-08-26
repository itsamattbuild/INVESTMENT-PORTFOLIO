# Lifecycle decision pack

Prepared for [issue #5](https://github.com/itsamattbuild/INVESTMENT-PORTFOLIO/issues/5).
The ticket stays open. Measurements first, recommendations attached — with one
environment caveat stated up front.

**Environment caveat, stated plainly.** Tonight's sandbox blocks all outbound
connections to the quote endpoints at its network layer (`query2.finance.yahoo.com`
and the CNBC endpoint both answer a proxy-generated HTTP 403 before any TLS
handshake), so **live cold-start fetches could not be re-measured tonight**.
Issue #1's numbers are used where they are the only source. What *was* measured
for real: interpreter/import/server boot costs, connection-setup costs against
a reachable host, page-latency behaviour of both startup designs against real
local servers under both network conditions, port-binding collisions, and
concurrent data-file writes. The dead-network fetch legs use `sleep(TIMEOUT)`
with #1's measured constants inside #1's chain structure — what that changes
for the user's screen is then measured end-to-end, not simulated.

## 1. Cold start, decomposed

| Component | Measured tonight | Notes |
|---|---|---|
| Python interpreter boot | 5 ms | negligible |
| import `curl_cffi.requests` | 51 ms | the mandatory compiled dep; fine |
| import `fastapi` | 107 ms | largest import cost |
| import `uvicorn` | 52 ms | |
| uvicorn process start → serving requests | **129 ms** | measured on loopback |
| TLS session, first request (real host) | **611 ms** first call, then 236–304 ms steady | stand-in host; #1 measured **1–4 s** for Yahoo's first call (cookie/session setup) and ~30 ms/ticker steady state |

Reading: everything except the first fetch call together costs roughly a third
of a second. **Startup latency is dominated by the first Yahoo round-trip**
(#1: 1–4 s of session/cookie setup, then ~350 ms for twelve sequential
tickers). Design implication confirmed: optimising ticker concurrency buys
~150 ms and isn't worth complexity (#1 already concluded this); hiding the
first-call cost behind a rendered page is worth seconds (next section).

## 2. Blocking vs non-blocking startup — measured end to end

Two minimal FastAPI apps built (`bench/app_variants.py`): identical data,
identical chain shape (Yahoo leg → CNBC leg, `TIMEOUT_SECONDS=5`, per #1).
Page served by a real HTTP client against real servers:

| Startup design | Healthy fetch (~0.35 s) | Dead network (both sources time out) |
|---|---|---|
| Blocking (page waits for fetch) | **0.35 s** to page | **10.00 s** of blank screen (two 5 s timeouts compound — exactly #1's measurement) |
| Non-blocking (render last-known immediately, background refresh) | **0.003 s** | **0.004 s** |

The settled no-network policy ("last known prices, never an empty screen") is
only literally true under non-blocking startup. A blocking design shows an
empty browser tab for ten seconds on a train — worse than any stale-price UX.

**Recommendation:** render immediately from the price cache; refresh in a
background thread; surface freshness via the two timestamps (#1). This also
removes any need for a progress indicator or ticker-concurrency machinery.
Cost: one background thread — acceptable in plain Python.

## 3. Launching twice

Measured with two real instances:

- Second instance fails fast and loudly: `[Errno 98] address already in use`
  while binding `127.0.0.1:<port>`; exit code non-zero. First instance keeps
  serving (HTTP 200 throughout).
- So the *port* collision is safe by default. The dangerous half is the second
  instance's *startup work* (fetching prices, writing cache) happening before
  the bind failure — ordering matters: bind first, do work after.

### Two processes writing the same data file — tested, not reasoned

| Store | Result |
|---|---|
| JSON, interleaved read-modify-write | **Silent data loss**: A wrote 20 log entries, B wrote 20; final file held 37 — 3 entries erased by last-writer-wins, no error anywhere |
| SQLite WAL, row-at-a-time writes, `busy_timeout=3000` | **Zero loss**, zero errors, `integrity_check=ok`; writers serialise cleanly |
| SQLite, second writer while a write transaction is held | Fails honestly after its timeout: `sqlite3.OperationalError: database is locked` |

**Recommendation:** whatever storage #2 picks, add a single-instance guard to
the launcher (pidfile or pre-bind check) — cheap insurance. If #2 chooses
SQLite, enable WAL + `busy_timeout` from day one; if JSON, atomic temp-file
renames (see the data-model pack) prevent torn files but *not* lost updates,
which makes the single-instance guard mandatory rather than advisory.

## 4. The `.command` double-clickable launcher

Written and exercised (`bench/launcher.command`). Verified here: env creation
on first run, dependency install hook, server start + readiness wait, browser
open, **already-running detection** (second launch prints "Server already
running", skips start, exits 0), and the failure path (no venv support → clear
actionable message, exit 1, no half-state left behind).

macOS-specific behaviours marked `[macOS]` in the script were reasoned, not
executed (this sandbox is Linux): Terminal.app runs the script on double-click;
`open "$APP_URL"` launches the default browser; the stop instruction uses
`lsof -ti :PORT`. One genuine macOS risk to verify on hardware: **Gatekeeper
quarantine** — a `.command` downloaded or created by another tool may be
blocked on first open ("cannot be opened because it is from an unidentified
developer"); right-click → Open clears it once. Not verifiable tonight.

Failure modes covered by the script as written: missing python3 (message),
failed venv creation (message + exit), failed pip install (message + exit),
server not becoming ready within 10 s (points at `server.log`), port busy
(detected → treated as already-running, which is correct because the app is
the only thing that binds that port).

## 5. The fallback discarding good Yahoo snapshots (#5's comment)

Reproduced concretely: Yahoo dies on ticker 10 of 12 after nine good
snapshots; CNBC batch-knows only three of the tickers.

| Strategy | Prices shown | Positions flagged |
|---|---|---|
| Replace (current example-code shape) | 3 | 9 flagged "no usable price" |
| Merge (keep Yahoo's nine, let CNBC fill gaps) | **10** | 2 |

Merge is a two-line change (`snapshots.update()` instead of assignment plus
keeping per-ticker failures), introduces no new state beyond what exists, and
never makes the result *worse*: worst case CNBC returns nothing extra and the
outcome equals today's. It also composes with #1's staleness guard unchanged —
each snapshot keeps its own timestamps and source tag.

**Recommendation:** adopt merge. The comment's instinct is right, and the demo
shows the failure mode is not hypothetical: it fires whenever CNBC lacks a
ticker (e.g. its `BRK.B` mapping gaps) precisely when Yahoo degraded mid-loop.

## Remaining questions, numbered — each with a recommendation

**Q1. Start-on-demand vs resident daemon.** Recommend on-demand via the
`.command` launcher; a resident daemon needs auto-start plumbing (launchd)
that outscopes v1. The launcher already makes re-launching idempotent.

**Q2. Blocking vs non-blocking startup.** Non-blocking, per §2. The page
renders from cache in ~4 ms regardless of network; refresh lands in the
background.

**Q3. Refresh mid-session.** Add a manual "fetch prices now" button hitting
the same background-refresh path as startup — no extra machinery once §2 is
adopted. Automatic polling is unnecessary for a once-a-day app.

**Q4. Shutdown.** Server dies with the terminal window (foreground run) or via
the printed `kill $(lsof -ti :PORT)` line (background run); every write is
atomic per the data-model pack, so there is no unsaved-data exposure. Show
"last fetched" timestamp in the footer so shutdown state is always visible.

**Q5. Single instance.** Pre-bind guard in the launcher + bind-first ordering
in the app (§3); mandatory if storage is JSON, belt-and-braces if SQLite.

**Q6. Logs and errors.** One `server.log` next to the app, written by uvicorn
plus the fetch layer's per-ticker outcomes; the launcher's error paths point
at it. No syslog/journald involvement.

*Scripts: `bench/app_variants.py` (blocking/non-blocking servers),
`bench/concurrent_writes.py`, `bench/launcher.command`. Live-quote re-measure
during a trading session remains ticket #8's job.*
