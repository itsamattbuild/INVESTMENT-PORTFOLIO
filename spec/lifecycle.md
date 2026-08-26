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

**Platform of the numbers.** Every local figure in this document was
re-measured on 2026-08-26 on **Linux (aarch64 container), Python 3.14.4**,
after the bench scripts were made portable (`tempfile` instead of hardcoded
sandbox paths). No macOS hardware has run any of this yet: numbers marked
`[macOS]` remain reasoned, not executed. The dead-network probe in
`bench/fetch_layer.py` reports honestly which case fired on each leg — behind
this sandbox's transparent proxy both legs are answered early (~30 ms), so its
leg times here measure proxy refusals, not timeouts; the timeout arithmetic
lives in §2's sleep-based legs as before.

## 1. Cold start, decomposed

| Component | Measured | Notes |
|---|---|---|
| Python interpreter boot | 6.6 ms | negligible |
| import `curl_cffi.requests` | 47 ms | the mandatory compiled dep; fine |
| import `fastapi` | 96 ms | largest import cost |
| import `uvicorn` | 41 ms | |
| uvicorn process start → serving requests | **149 ms** median (147–272 over 7 runs) | measured on loopback |
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
| Non-blocking (render last-known immediately, background refresh) | **0.0004 s** | **0.0003 s** |

The settled no-network policy ("last known prices, never an empty screen") is
only literally true under non-blocking startup. A blocking design shows an
empty browser tab for ten seconds on a train — worse than any stale-price UX.

**Recommendation:** render immediately from the price cache; refresh in a
background thread; surface freshness via the two timestamps (#1). This also
removes any need for a progress indicator or ticker-concurrency machinery.
Cost: one background thread — acceptable in plain Python.

## 3. Launching twice

Measured with two real instances (reproduced by `bench/bench_port_collision.py`):

- Second instance fails fast and loudly: bind on `127.0.0.1:<port>` raises
  `OSError` **errno 98** (`EADDRINUSE`) and it exits rc=3 after ~0.15 s.
  First instance keeps serving (HTTP 200 throughout).
- The number is platform-specific — this machine (Linux) reports **98**; macOS,
  using BSD errno numbering, reports the same condition as **48**. Any code
  detecting this condition must compare against `errno.EADDRINUSE`, never
  against a numeric literal or a message substring. Whether the second
  instance's *failure mode* is also identical on macOS — where `SO_REUSEADDR`
  semantics differ from Linux — belongs on the hardware-verification list with
  the other `[macOS]` items below.
- So the *port* collision is safe by default on Linux. The dangerous half is
  the second instance's *startup work* (fetching prices, writing cache)
  happening before the bind failure — ordering matters: bind first, do work
  after.

### Two processes writing the same data file — tested, not reasoned

| Store | Result |
|---|---|
| JSON, interleaved read-modify-write | **Silent data loss, every run**: A wrote 20 log entries, B wrote 20; the surviving count moved between runs — 37 of 40 in the original overnight sandbox, 1–33 of 40 across ten re-runs on Linux, **30 of 40 on the target platform (Darwin arm64)** — 10 entries gone. No error anywhere; the exact loss is scheduler luck, which is worse than any stable number would be |
| SQLite WAL, row-at-a-time writes, `busy_timeout=3000` | **Zero loss** (reproduced exactly: 20/20 + 20/20 rows), zero errors, `integrity_check=ok`; writers serialise cleanly |
| SQLite, second writer while a write transaction is held | Fails honestly after its timeout: `sqlite3.OperationalError: database is locked`. Observed in the original runs; today's impatient-writer re-runs completed without overlapping writes, so no error fired — absence of contention, not absence of the error path |

**Recommendation:** a single-instance guard (pidfile or pre-bind check in the
launcher) is **mandatory if #2 settles on JSON**. The conclusion is unchanged,
but the overnight numbers understated it: on the platform this app ships to,
the review's re-run lost 10 of 40 recorded transactions — a quarter of the
ledger, silently — where the sandbox had shown 3. Atomic temp-file renames
(see the data-model pack) prevent torn files but *not* lost updates. If #2
chooses SQLite, enable WAL + `busy_timeout` from day one and fit the guard
anyway; belt-and-braces costs nothing next to a lost ledger.

## 4. The `.command` double-clickable launcher

Written and exercised (`bench/launcher.command`). Verified in the original
pack: env creation hook, dependency install, server start + readiness wait,
browser open, already-running detection, failure paths. Since then given its
full pass on this session's host (Linux arm64 — real hardware, not the macOS
target):

- Server start + readiness wait: uvicorn serving, launcher exits 0, page
  answers HTTP 200, `server.log` written next to the app.
- Browser-open fallback chain: no `open` on this host → the `xdg-open` branch
  ran and surfaced `http://127.0.0.1:8123` for the user's local browser. On
  macOS the first branch (`open "$APP_URL"`) takes over.
- Already-running detection: second launch prints "Server already running at …",
  starts nothing, exits 0.
- The printed stop line works verbatim: `kill $(lsof -ti :8123)` freed the port.
- Failure path, app module missing: readiness wait times out → "ERROR: server
  did not start. See server.log", exit 1.

One correction the pass forced: a *failed* venv creation (this host's python3
lacks ensurepip) prints the actionable error and exits 1 as designed, but
leaves the partial `.venv/` behind — "no half-state left behind" was too
strong. Harmless in practice (the next run recreates into it), but stated as
measured.

What the pass could not cover, stated just as plainly: **the Finder
double-click**. This session runs on a Linux host — the repo folder merely
lives on the Mac — so the Finder → Terminal.app hand-off, Gatekeeper quarantine
on first open ("cannot be opened because it is from an unidentified
developer"; right-click → Open clears it once), and `open "$APP_URL"` itself
remain unexecuted. Everything the script does *after* the double-click is now
verified; whether it works from Finder without a terminal stays open under the
map's Distribution item until someone actually double-clicks it on the Mac.

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
renders from cache in under half a millisecond regardless of network; refresh
lands in the
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
`bench/concurrent_writes.py`, `bench/fetch_layer.py`,
`bench/bench_port_collision.py`, `bench/launcher.command`. Live-quote
re-measure during a trading session remains ticket #8's job.*
