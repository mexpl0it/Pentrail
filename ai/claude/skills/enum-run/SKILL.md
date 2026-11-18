---
name: enum-run
description: PeTe's enumeration harness - read what pentrail already recorded (captures, shots, scans), build a de-duplicated plan of missing steps per host and port from pentrail next --json, classify each step by the PeTe rules, get one approval per round, run the steps through pentrail shot with a --why, record the round and its results, then re-plan until enumeration is complete. Use when the tester asks PeTe to enumerate a target, continue enumeration, or "do the enum".
---

# Enumeration in rounds

```
read the record -> plan only what is missing -> classify by the PeTe rules -> record the plan
   -> one "go" -> run via pentrail shot --why -> record results -> summarise -> re-plan
```

## 0. Preconditions

- Scope set and the target in it: `pentrail scope check <host>` exits 0.
- Nobody runs the same thing now: the brief's "Running now", or `pentrail trace -H <host>`.
- The tester said PeTe drives (see CLAUDE.md, Who drives).

## 1. Read the record

```bash
pentrail next <host> --json     # steps: source (playbook|coverage), done, ids of the commands that did it
pentrail trace -H <host>        # everything that ran, by whom, with why
pentrail vectors                # open leads
```

The tester's capture commands count as done. Read their output (`pentrail show <id>`)
rather than repeating them. No hosts or ports yet: round 1 is `recon-active`.

## 2. Build the round

Take the `todo` steps from `next --json`, plus follow-ups from earlier output (a vhost in a
certificate, a share name, a CMS version). For each step:

1. **Dedupe**: `pentrail seen <host> <tool|script|text>`. Exit 0 = skip it, unless you can
   say what a rerun adds; that goes in `--why`.
2. **Classify** by the PeTe rules (your brief has them):

   | The step | Rule |
   |---|---|
   | nmap `-sV`/`-sC`, safe NSE (`*-info`, `*-enum-*`, `ssl-cert`, `ldap-rootdse`), whatweb, curl, smbclient `-L -N`, enum4linux-ng, snmpwalk public, showmount, `dig axfr` | service_enum / port_scan |
   | ffuf, feroxbuster, gobuster, dirsearch, vhost fuzzing | web_content_discovery |
   | `--script vuln`, `smb-vuln-*`, `unsafe=1`, nikto, nuclei, wpscan | vuln_scripts |
   | hydra, medusa, `*-brute` scripts, guessed logins (`mysql -u root`), spraying | brute_force / password_spraying |
   | full TCP, UDP, rustscan, masscan; anything with sudo | port_scan (+ max_scan_rate), root_commands |

   The playbook in `next --json` is the tester's too (`next --steps`), so it holds steps that are
   `ask` or `deny` for you (`smb-vuln-*`, `pgsql-brute`, `mysql -u root`). Classify them;
   never run a `deny` step.
3. **Adapt**: the literal target, output to `1-enum/scans/<name>`, the tester's wordlist
   (the dirbuster step in `next --json` is built from their config; otherwise SecLists
   `Discovery/Web-Content/raft-medium-directories.txt`), `--max-rate` at or under
   `max_scan_rate`.
4. **Order**: cheap and high-signal first (versions, null sessions, web fingerprint); slow
   ones (full TCP, UDP, big wordlists) in the background.

## 3. Show it, get one "go", record it

```
Round 3 - 10.10.10.5 (5 steps, 2 skipped: done before)
| # | Step | Why | Rule |
| 1 | enum4linux-ng -A 10.10.10.5 | users and shares via a null session | allow |
| 2 | feroxbuster -u http://10.10.10.5 -w <raft-medium> -o 1-enum/scans/ferox_80.txt | hidden content | allow |
| 3 | nmap -sU --top-ports 100 --max-rate 1000 -oA 1-enum/scans/udp 10.10.10.5 (sudo) | SNMP, TFTP | ask |
| 4 | nmap -p445 --script smb-vuln-* 10.10.10.5 | known SMB flaws | ask |
| - | hydra on ssh | | deny: not allowed by the PeTe rules |
Skipped: whatweb (#9, your capture 10:14), nmap -sV (#2)
```

- `allow` steps run after one "go". `ask` steps need their own yes (Claude Code prompts).
  `deny` steps are listed and never run. With `fast_mode: on` and only `allow` steps, one
  line is enough.
- After the go, record the plan before running anything:
  `pentrail note -t <host> "PeTe round 3: enum4linux-ng, feroxbuster 80, UDP top 100. Approved."`

## 4. Run

```bash
pentrail shot -q --by pete --why "users and shares via a null session" -l smb-null -- enum4linux-ng -A 10.10.10.5
```

- Exit 3: blocked. Stop that step, report it, go on with the rest.
- Never more than the round that was approved. A new idea mid-round goes in the next one.

## 5. Record the results

After each step: 2-4 lines for the tester (what, what it means, what it opens up), and in
the record:
- a lead: `pentrail vector add "<lead> (#<id>)" -t <type>`
- a dead end: `pentrail note -t <host> "<step>: nothing, <evidence> (#<id>)"`
- a lead settled: `pentrail vector dead|done <id>`

## 6. Summarise, re-plan, stop

Close the round with the summary from CLAUDE.md, including
`Again: pentrail runbook --by pete --ids <the ids of this round>`. Then `pentrail next <host> --json`
again. Stop and hand over when every playbook and coverage step is done (or skipped with a
note), `vuln-triage` has enough confirmed candidates, or the next useful step is `ask`,
`deny` or exploitation. Give the open leads, the gaps, and your proposed next move.
