---
name: audit-trail
description: Keeping PeTe's work transparent and auditable in pentrail - every target command with --by pete and a --why, the round plan and approvals as notes, leads and dead ends recorded with command ids, and how the tester reviews it all (trace --by pete, show, log, runbook). Use when the tester asks what PeTe did or why, before ending a session, when handing over, and whenever a result or decision needs to be on record.
---

# Keeping the record

The tester (and whoever reads the report) must be able to answer from the record alone:
what did PeTe run, why, what came of it, and who approved it. Your chat disappears; the
record stays in the project.

## What goes where

| What | How | Where it ends up |
|---|---|---|
| a command against a target | `pentrail shot -q --by pete --why "..." -l <label> -- <cmd>` | evidence file, `trace`, logbook (`(by pete)`, `why:`), phase doc |
| the plan of a round, the approval | `pentrail note -t <host> "PeTe round n: ... Approved."` | notes.md, enum.md, logbook |
| a lead | `pentrail vector add "<lead> (#id)" -t <type>` | leads, enum.md |
| a dead end | `pentrail note -t <host> "<step>: nothing, <why> (#id)"` | notes.md |
| a decision not to run something | `pentrail note -t <host> "skipped <step>: <rule or reason>"` | notes.md |
| a blocked command | logged by the guardrail itself (`hook blocked ... (by pete)`) | logbook |

A good `--why` is a hypothesis you can check against the output:

- `--why "SMB null session: list users and shares"` (not `--why "enum4linux"`)
- `--why "vhost from the TLS cert (#7): does it serve another site?"`
- `--why "rerun of #12 with raft-large: #12 used a small list"`

## Claims cite ids

Write "SMB signing is off (#15)", not "SMB signing is off". If you did not check
something, say so. If an output was ambiguous, quote the two lines that matter and give
the id.

## How the tester audits you

```bash
pentrail trace --by pete            # everything you ran, with why, exit code, output file
pentrail trace --by pete --json     # the same for a script (credentials masked)
pentrail show <id>                  # the output of one command
pentrail log 50                     # the logbook: shots, notes, leads, blocks, by whom
pentrail notes <host>               # your round plans and dead ends next to theirs
pentrail runbook --by pete          # all of it as a script that runs it again
```

## Before the session ends

1. Every lead you found is a vector; every dead end is a note.
2. The last round has its summary with the `Again: pentrail runbook ... --ids ...` line.
3. Tell the tester what is still open and what you would do next, in three lines.
