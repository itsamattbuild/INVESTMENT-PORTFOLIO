# Wayfinder

This project is planned with the wayfinder method: a **map** that indexes what
still needs deciding, and one **ticket** per open question, worked one at a time
until the way to the destination is clear.

The tracker is this repository's GitHub issues.

- **The map** — [Map: local portfolio tracker for US equities](https://github.com/itsamattbuild/INVESTMENT-PORTFOLIO/issues/6),
  labelled `wayfinder:map`. Read it first. It carries the destination, the
  binding constraints, the decisions made so far, and the fog that is not yet
  sharp enough to ticket.
- **Tickets** — child issues of the map, labelled by type: `wayfinder:research`,
  `wayfinder:prototype`, `wayfinder:grilling`, `wayfinder:task`.
- **The frontier** — open child issues that are unblocked and unclaimed. Blocking
  uses GitHub's native issue dependencies, so the frontier is visible in the
  issue list without opening anything.

Tickets briefly lived as markdown files in this directory. They were moved to
issues once a second agent joined the work; the issues are now the only
canonical copy.

## Working a ticket

1. Read the map. Do not read every ticket — the map is the low-resolution view.
2. Take a frontier ticket and **claim it before doing any work** by adding an
   `agent:*` label.
3. Resolve it, invoking the skills named in the map's Notes.
4. Post the answer as a comment, close the issue, and add a line to
   `Decisions so far` on the map.

One session, one ticket. Research tickets may run in parallel.

## What stays here

- `frontend-design.md` — a design skill supplied by the repository owner,
  referenced by the visual direction ticket.
