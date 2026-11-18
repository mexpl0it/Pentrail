# PeTe: pentrail's AI layer for Claude Code

PeTe is an assistant that works the pentrail way: it scopes, recons, enumerates, triages
and writes findings for targets you are authorized to test, and it does not exploit
anything. Everything it runs goes through pentrail's scope guard and is recorded with its
output, who ran it and **why**, so you can audit it and run it again.

pentrail works the same without this folder. Nothing here is used until you install it in
a project.

## What is in here

```
ai/
├── VERSION                 the layer's version: the release that last changed it
├── README.md               this file
├── TERMS.md                authorized testing only; you own every command PeTe runs
└── claude/
    ├── CLAUDE.md           PeTe's prompt: Rule 0, the record, who drives, the PeTe rules, teaching
    ├── rules.md            the PeTe rules block that goes into 0-scope/scope.md
    ├── settings.json       Claude Code: permissions, the two hooks, the status line, PENTRAIL_ACTOR=pete
    └── skills/             14 skills, one folder each with a SKILL.md
```

Skills: `pentrail-session`, `methodology`, `scope-guard`, `pentrail`, `enum-run`,
`recon-passive`, `recon-active`, `service-enum`, `web-enum`, `ad-enum`, `vuln-triage`,
`report-finding`, `audit-trail`, `retest`.

## Install

```bash
pentrail setup                    # once, from the checkout: copies ai/ to ~/.local/share/pentrail/ai
pentrail pete install [project]   # into a project (default: the active one); 'pentrail ai install' is the same
cd ~/pentests/box1 && claude      # trust the folder when Claude Code asks
pentrail pete                     # status, and what to do next
```

`pete install` writes `CLAUDE.md`, `.claude/skills/` and `.claude/settings.json` into the
project, puts the PeTe rules under Rules of engagement in `0-scope/scope.md`, and records
in `.claude/pentrail-ai.json` the version and a SHA-256 of every file it wrote and every
settings entry it added. That stamp is what makes the install repeatable: running it again
changes nothing, `pete update` replaces only what it installed (your edits are kept as
`.bak`), and `pete remove` takes out only what it put in.

## The guardrails, from the outside in

1. **The scope** in `0-scope/scope.md`, which only you change.
2. **Claude Code's permissions** (`settings.json`): pentrail's read commands and
   `pentrail shot -q --by pete` are allowed; findings, the report, phase and target changes,
   credentials, `/etc/hosts` and `sudo` ask; scope and config changes, `capture`, PeTe's own
   install, and edits of the scope, logbook, state and PeTe's files are denied.
3. **The guardrail hook** before every Bash command and web fetch: out-of-scope hosts,
   in-scope hosts reached outside `pentrail shot`, scope overrides, protected files and
   tools the PeTe rules deny are stopped, with the reason (and often the right command).
   A hook that fails or times out blocks the call (`onFailure: block`). Every stop is in
   the logbook.
4. **`pentrail shot` itself**: the scope check, and for anything that runs as PeTe (or any
   actor that is not you), the PeTe rules' `deny` list. That also covers a script PeTe
   might start.

## Transparent and repeatable

| You want to know | Run |
|---|---|
| what PeTe ran, and why | `pentrail trace --by pete` |
| the output of one of its commands | `pentrail show <id>` |
| its round plans, approvals, dead ends | `pentrail notes <host>`, `pentrail log` |
| everything it did, as a script to run again | `pentrail runbook --by pete [-H host] [--ids ...]` |
| what it read at the start | `pentrail pete brief` |
| which PeTe a project has, and whether it changed | `pentrail pete status` |

## Changing the layer

See `CONTRIBUTING.md` and the `pete-layer` skill in `.claude/skills/` of the repository: a
change to anything in `ai/` bumps `ai/VERSION` to the release it ships in, and the tests
check that every skill is well formed and only uses pentrail commands that exist.
