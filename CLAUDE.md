# CLAUDE.md

A local-first portfolio tracker for US equities. **Planning stage: there is no
application code yet, and that is deliberate.** Decisions are being settled one
at a time before anything is built.

## Read the map first

The project is planned with the **wayfinder** method. The map is
[issue #6](https://github.com/itsamattbuild/INVESTMENT-PORTFOLIO/issues/6),
labelled `wayfinder:map`. It holds the destination, the binding constraints, the
decisions already made, and the fog not yet sharp enough to ticket.

```bash
gh issue view 6 -R itsamattbuild/INVESTMENT-PORTFOLIO
```

Read the map before touching anything. Read individual tickets on demand — the
map is the low-resolution view, and reading every ticket defeats it.

Tickets are the map's child issues, labelled by type: `wayfinder:research`,
`wayfinder:prototype`, `wayfinder:grilling`, `wayfinder:task`. Blocking uses
GitHub's native issue dependencies, so the **frontier** — open, unblocked,
unclaimed — is visible in the issue list.

## Working a ticket

1. **Claim it first**, before any work, by adding an `agent:*` label. An
   unclaimed ticket is one another agent may take at the same moment.
2. Invoke the skills the map's Notes name for that ticket type.
3. Post the answer as a comment on the ticket, close it, and add one line to
   `Decisions so far` on the map linking back.
4. Add any newly-sharp questions as new child tickets. Graduate fog out of
   `Not yet specified` as it becomes specifiable.

**One session, one ticket.** Research tickets are the exception and may run in
parallel.

## Parallel agents

More than one agent works this repo. Each works on its own branch, and **only
Claude edits the map**. Before starting, check which tickets carry an `agent:*`
label and stay out of them.

## Binding constraints

These hold across every ticket. The map carries the full set and the reasoning;
these three are the ones that cause damage when broken silently.

- **Portfolio data never enters the repo tree.** It lives under
  `~/Library/Application Support/`. The repo is public. Keeping data outside the
  tree is what makes an accidental commit impossible rather than unlikely, so
  treat the location as fixed, not as a preference.
- **Every file in this repo is written in English** — code, commits, docs, and
  interface copy alike.
- **Use the vocabulary in [CONTEXT.md](CONTEXT.md) exactly**: `drift`,
  `target weight`, `contribution amount`, `realised` / `unrealised profit`,
  `price snapshot`. It is a glossary of domain terms and nothing else — keep
  implementation decisions in tickets, where they can be argued with.

## The repository owner

Learning Python. Where two options are otherwise equal, pick the one that puts
more work in Python and less in frontend tooling, and say why in a sentence.
