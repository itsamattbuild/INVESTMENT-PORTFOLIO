# Wayfinder — local tracker convention

No issue tracker is configured, so the map and its tickets live as markdown files in this directory.

## Layout

```
wayfinder/
├── map.md              ← the map (labels: wayfinder:map). The single canonical artifact.
├── frontend-design.md  ← user-supplied skill, used by ticket 0004
└── tickets/
    └── NNNN-slug.md    ← tickets, children of the map
```

## Ticket frontmatter

```yaml
id: 0003
title: ...
labels: [wayfinder:research | wayfinder:prototype | wayfinder:grilling | wayfinder:task]
parent: ../map.md
status: open | closed
assignee: null | <who is working on it>
blocked_by: [0001, 0002]
```

## Operations

- **Frontier** — tickets with `status: open`, an empty `assignee`, and every `blocked_by` closed.
- **Claim** — write yourself into `assignee` **before** starting work. That is what separates a taken ticket from a free one.
- **Resolve** — append a `## Resolution` section to the ticket, set `status: closed`, and add a line to `## Decisions so far` in `map.md` linking back to the ticket.
- **Rule out of scope** — close the ticket and add a line to `## Out of scope` in the map. It does not go in `Decisions so far`: that section records the route actually walked, and a scope boundary is not a step along it.

## Rule

One session, one ticket. Exception: research tickets (`wayfinder:research`) may run in parallel.
