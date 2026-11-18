# pentrail

The pentest logbook. One command sets up a project; after that pentrail guards your scope,
records every command with its output, reads what your tools find into Markdown docs, and
builds the report from it.

For labs, engagements and bug bounty programs you are **authorized** to test. One Python
file (3.8+), standard library only, built for Kali/Linux.

```bash
python3 pentrail.py setup               # launcher on PATH, missing tools, config
pentrail new box1 10.10.10.5            # project + scope; an IP asks about the VPN and /etc/hosts
cd "$(pentrail dir)"
pentrail capture recon                  # work as usual: scope-checked, recorded, read into the docs
pentrail next                           # per port: what you ran, what is untouched
pentrail finding 3                      # lead #3 is real: write it up
pentrail report --html                  # 5-report/report.md + report.html
```

Bug bounty: `pentrail new acme '*.acme.com' api.acme.io` (domains only: no VPN, no
questions). `pentrail` alone shows the home screen, `pentrail help <command>` the details.

## A project

```
~/pentests/box1/                mode 700
├── 0-scope/scope.md            in / out of scope, rules of engagement
├── 1-enum/enum.md              per host: ports, web paths, names, leads, notes
│   ├── scans/                  tool output files, read automatically
│   └── evidence/               recordings and screenshots of this phase
├── 2-foothold/ 3-privesc/ 4-lateral/   a doc + evidence/ per phase
├── 5-report/findings/F01-*.md  one file per finding; report.md
├── notes.md  logbook.md        your notes (linked to hosts, leads, findings); the timeline
└── state.json  loot/  .env     what pentrail knows; exported credentials; $TARGET, $VPN_IP
```

Docs are plain Markdown. pentrail writes only between its `<!-- pentrail:auto ... -->`
markers and keeps everything else you write. `pentrail phase <name>` (or
`capture <phase>`) decides where evidence goes.

## Scope

```bash
pentrail scope add 10.10.10.0/24        # or: an IP, 10.10.10.1-50, a domain, *.domain, a URL
pentrail scope out blog.acme.com        # out of scope always wins
pentrail scope check nmap -sV 10.10.10.5   # exit 0 in, 3 out / not listed / conflict, 2 no host, 4 no scope
pentrail scope resolve                  # names that point into your ranges join the scope; conflicts listed
pentrail scope guard strict|warn|off    # stop, only report, or don't check
```

Before a command runs in a capture or through `shot`, pentrail finds every host in it
(variables expanded, URLs, `user@host`, ranges with `--exclude`) and stops it when one is
outside the scope; the stop goes into the logbook. Results about out-of-scope hosts are
never recorded. `scope-ok <command>` runs one anyway, logged. Contradictions (an
out-of-scope name inside an in-scope range) are conflicts until you settle them.

## Recording your work

```bash
pentrail capture recon                  # a recording shell (zsh or bash); exit to stop
pentrail shot -l smb -- enum4linux-ng -A 10.10.10.5   # run one command, keep it as evidence
pentrail shot --last                    # in a capture: keep what you just ran
pentrail ingest scan.xml                # read a saved tool file
```

Every finished command is read within seconds: ports and versions, web paths, hostnames,
leads and credentials land in the docs with the command that found them. pentrail reads
nmap (normal, greppable, XML), rustscan, masscan, the common dirbusters, vhost and
subdomain tools, httpx, whatweb, nuclei, nikto, curl and wget. Output a target controls
cannot add or hide commands in the record (see [THREAT-MODEL.md](THREAT-MODEL.md)).
`pentrail config auto_shot on` keeps every command that found something as a screenshot.
`pentrail redact add <value>` keeps your own secrets out of every recording.

## Looking it up instead of running it again

```bash
pentrail hosts [host] [--json]          # hosts, ports, versions, who found them
pentrail seen 10.10.10.5 gobuster       # ran (or running) against that host? exit 0, else 1
pentrail trace -H 10.10.10.5 [--by pete]   # what ran: when, phase, who, why, output file
pentrail show 12                        # the output of command #12
pentrail runbook -H 10.10.10.5 -o rerun.sh   # all of it as a script that runs each step again
pentrail next [host] [--steps]          # per port what ran against it; --steps: the standard steps
pentrail vectors   pentrail notes   pentrail log
```

`seen` counts the dirbusters as one tool and matches nmap scripts (`-sC` is `default`). A
runbook reruns every step through `shot`, so the scope is checked again and the rerun is
recorded next to the original; steps that need a credential, interactive sessions and
command lines read from files stay commented out for you to check.

## Findings and the report

```bash
pentrail finding 3                      # 5-report/findings/F01-....md from lead #3, prefilled
pentrail finding F01                    # print it clean, ready for a bug bounty platform
pentrail report [--mask] [--html] [--pdf]
```

A finding gets the asset, a starting severity and CWE, the command that found it, its
output and the evidence file; you write the summary, impact and fix. The report collects
the scope, findings by severity, your phase docs and an appendix (hosts, credentials,
commands with who ran them, evidence, timeline). `--mask` hides secrets.

## PeTe, the AI layer (optional)

PeTe is an assistant for [Claude Code](https://code.claude.com) that does scoping, recon,
enumeration, triage and reporting the pentrail way. It does not exploit anything.

```bash
pentrail pete install [project]         # CLAUDE.md, 14 skills, settings and hooks into the project
cd ~/pentests/box1 && claude            # trust the folder
pentrail pete                           # status, and what to do next
```

- Every target command it runs goes through `pentrail shot --by pete --why "<reason>"`.
- A guardrail hook checks each command and fetch before it runs (scope, the PeTe rules in
  `scope.md`, protected files); `shot` enforces the rules too. Brute force, spraying,
  exploitation and DoS are `deny`; vuln scripts, credentials and sudo `ask`.
- `pentrail trace --by pete` shows what it did and why; `pentrail runbook --by pete` repeats it.

Details: [ai/README.md](ai/README.md). Terms: [ai/TERMS.md](ai/TERMS.md).

## Hosts, VPN and /etc/hosts

```bash
pentrail hostfile add 10.10.10.5 dc01.box.htb box.htb   # one tagged line per name; says if it is in scope
pentrail hostfile [rm <name|ip> | clean [--all]]        # list or remove pentrail's lines, never yours
pentrail up | down | restart | status | check [ip] | watch
pentrail target dc01   pentrail host own 10.10.10.7   pentrail pivot 10.10.10.5 10.10.10.7
pentrail creds [users|hashes|export]   pentrail flag user <value>
```

openvpn runs as a root daemon that survives the terminal. `up` counts the tunnel as up when
openvpn reports it or a new tun device gets an address. `new` asks about the VPN only when a
target is an IP or range (`--vpn`: without asking, `--no-vpn`: never).

## Install, update, remove

```bash
python3 pentrail.py setup [--dry-run]   # asks before each change; sudo only to install and apt
pentrail update                         # git pull the checkout, reinstall the launcher, refresh PeTe's copy
pentrail uninstall [--config]           # launcher, cache, shell helper; projects are never deleted
pentrail doctor                         # tools, config, launcher version
```

Run pentrail as your normal user; it uses sudo only for openvpn, `/etc/hosts` and the
launcher. Config: `~/.config/pentrail/config.json`. Colours follow `NO_COLOR`; without a
UTF-8 terminal the symbols fall back to `[+] [*] [!]`.

## More

- `pentrail help` for every command, `pentrail help <command>` for one.
- [THREAT-MODEL.md](THREAT-MODEL.md): what can go wrong and what pentrail does about it.
- [CHANGELOG.md](CHANGELOG.md): what changed per release.
- [CONTRIBUTING.md](CONTRIBUTING.md): branches, versions, releases, tests
  (`python3 -m unittest discover -s tests -v`).
