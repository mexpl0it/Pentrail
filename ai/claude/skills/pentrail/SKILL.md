---
name: pentrail
description: Reference of the pentrail commands PeTe uses - running target commands through pentrail shot with --why, reading what ran (seen, trace, show, next --json, hosts --json), recording leads, notes and findings, and making a runbook. Use whenever you need the exact pentrail syntax or are unsure which command records or reads something.
---

# pentrail for PeTe

You run as `PENTRAIL_ACTOR=pete` with `PENTRAIL_PROJECT` set to this project, so everything
you record is marked as yours and lands here.

## Run against a target (the only way)

```bash
pentrail shot -q --by pete --why "<hypothesis>" -l <label> -- <command>
```

- `-q`: prints only "Saved:" and what was new; exits with the tool's exit code.
- Exit 3: blocked by the scope guard or the PeTe rules. Never retry another way.
- One program, no shell: no `|`, `>`, `&&`. Tools write their own files:
  `nmap ... -oA 1-enum/scans/<name>`, `ffuf ... -o 1-enum/scans/<name>.json`. pentrail reads
  `1-enum/scans/` by itself (`next`, `report`) or now with `pentrail ingest <file>`.
- Labels: short, no spaces (`nmap-full`, `smb-null`, `ferox-80`).
- Long scans: run the shot in the background and go on with short steps.

## Read before you run

| Command | Gives |
|---|---|
| `pentrail seen <host> <tool\|script\|text>` | exit 0 = ran (or running), 1 = not yet |
| `pentrail next [host] --json` | per-port playbook + coverage, done or not, with command ids |
| `pentrail trace [-H host] [-t tool] [--by pete\|you] [--json]` | what ran, when, by whom, why |
| `pentrail show <id> [-n 0]` | a command's recorded output |
| `pentrail hosts [host] --json` | hosts, ports, versions, web paths, names, leads (no secrets) |
| `pentrail names --plain` | hostnames seen in scope |
| `pentrail vectors` | leads, working first |
| `pentrail notes [host]` | notes |
| `pentrail log [n]` | the logbook |
| `pentrail scope check <host\|cmd>` | in scope? (see `scope-guard`) |
| `pentrail hostfile` | the /etc/hosts lines pentrail added |

## Record (allowed without asking)

```bash
pentrail vector add "<lead>" -t <type>    # type: web sqli lfi upload smb ldap creds misc ...
pentrail vector working|dead|done|open <id>
pentrail note -t <host> "<text>"         # #3, F01, N2 and hosts in the text become links
pentrail runbook --by pete [-H host] [--ids 3,7] [-o file]
```

## Ask first (Claude Code will prompt)

`pentrail finding <vector-id> [-s sev]`, `pentrail report`, `pentrail phase <p>`,
`pentrail target <host>`, `pentrail set <key> <value>`, `pentrail hostfile add <ip> <name>`,
`pentrail cred ...`, `pentrail up|down|restart`, anything with `sudo`.

## Never

`pentrail scope add|out|guard`, `pentrail config ...`, `pentrail capture`,
`pentrail pete install|update|remove`, `pentrail redact`, `setup`, `update`, `uninstall`,
`scope-ok`, `PENTRAIL_SCOPE_OK`. Editing `0-scope/`, `logbook.md`, `state.json`, `CLAUDE.md`
or `.claude/`. Reading `loot/` or `state.json`.
