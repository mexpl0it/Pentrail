# Threat model

What can go wrong when you use pentrail (and PeTe), what pentrail does about it, and what
is left to you. Updated for 1.10.0.

## What pentrail is trusted with

| Asset | Where |
|---|---|
| Staying inside the scope (legal and contractual) | every command run in a capture or through `shot` |
| Client data: findings, evidence, tool output | the project folder (`~/pentests/<name>`, mode 700) |
| Credentials found or handed over | `state.json`, `loot/` (plain text in that folder) |
| The integrity of the record: what ran, by whom, why | `state.json`, `logbook.md`, evidence files |
| Your machine | sudo for openvpn and `/etc/hosts`; the launcher in `/usr/local/bin` |

## Trust boundaries

```
 target / third parties ──output──▶ your terminal ──▶ pentrail ──▶ project record ──▶ PeTe (Claude Code)
   untrusted text                  (capture, shot)    (parser)                          ──▶ model provider
                                                          ▲                                    │
                                                          └──────── commands via shot ─────────┘
```

Everything a target sends back (banners, pages, files, DNS answers) is untrusted. So is
anything an AI assistant decides after reading it.

## Threats and mitigations

### T1. Traffic outside the scope

*How:* a typo, a stale `/etc/hosts` line, a name that resolves somewhere else, an assistant
that follows a link.
*Mitigation:* the scope guard checks every host on a command line (`$VARS` expanded, URLs,
`user@host`, ranges with `--exclude`) before it runs, in a capture and in `shot`; exit 3
and a logbook line when it stops one. Out of scope wins over in scope, and contradictions
are conflicts. An actor (PeTe, a script) can never override it.
*Left to you:* hosts the guard cannot see on the command line: target lists in files
(`-iL`), tool configs, scripts, crawlers and dirbusters that follow redirects. Modes `warn`
and `off` check less. pentrail's own DNS lookups go to your resolver.

### T2. A target forging the record

*How:* output a target controls contains pentrail's invisible command markers or its
output brackets, a fake `# Nmap ... as: <command>` header, or a line that looks like a
shell prompt. The parser would record a command that never ran, or hide one that did. A
`runbook` would then turn the fake command into a step.
*Mitigation (1.10.0):* every capture has a random key. The shell hook signs its markers
with it and pentrail signs the brackets around its own output; anything unsigned is plain
text (`trusted_markers`, `cap_begin`). Markers in saved files are never trusted. A scan
file's command line is read only from nmap's own first line, and only if it runs nmap.
Commands guessed from prompt lines (a recording without markers) are marked unverified.
`runbook` comments out every step whose command line came from a file or was guessed.
The report's HTML and figures escape every text they show, so a path or title a target
chose cannot add markup or script to the report.
Tests: `TestCapture` (a stand-in tool forges markers), `test_a_scan_file_cannot_name_its_own_command`.
*Left to you:* what a tool reports (ports, versions, paths) is the target's to lie about.
Read a raw recording with `pentrail show` or `less`, not `cat`: escape sequences in it can
redraw your terminal.

### T3. Prompt injection into PeTe

*How:* target text (a page, a banner, a file, a lead's description) tells the assistant to
do something else: scan another host, run a denied tool, change its own rules, or send
data somewhere.
*Mitigation:* the limits are enforced in code, not in the prompt. The guardrail hook checks
every Bash command and web fetch (scope, PeTe rules, protected files, the commands that
change PeTe's guardrails) and fails closed. `shot` refuses denied tools for any actor,
including inside a script. Claude Code asks you before findings, credentials, sudo,
`/etc/hosts` and anything not allowed. Everything PeTe runs is recorded as PeTe's with
its reason (`pentrail trace --by pete`).
*Left to you:* inside what the rules allow, a manipulated PeTe can still run allowed scans
on in-scope hosts or write misleading notes and leads; check its claims against the ids it
cites. A web fetch to a third-party host is not decided by the hook (Claude Code asks): do
not approve a fetch whose URL you do not understand, since a URL can carry data out. Read a
script before you let PeTe run it.

### T4. Credentials and client data leaking

*How:* secrets in command lines, JSON, the session brief or a report; client data in what
PeTe reads; a shared project folder.
*Mitigation:* the project folder is mode 700. Your own secrets (`pentrail redact add`) are
stored as hashes and scrubbed before anything is saved or parsed. `mask_secrets` replaces
stored credentials and password arguments with `[secret]` in every JSON output, the brief,
`trace` and `runbook`. PeTe's settings deny reading `state.json` and `loot/`.
`report --mask` hides secrets for sharing, in the figures too; a flag's value is never
drawn.
*Left to you:* credentials sit in plain text in `state.json` and `loot/`: use disk
encryption. What PeTe reads (command output) goes to the model provider; keep data your
contract forbids sharing away from it ([ai/TERMS.md](ai/TERMS.md)).

### T5. PeTe getting around its guardrails

*How:* editing its settings, the scope or the logbook; installing or removing itself;
`scope-ok`; running raw commands from a script.
*Mitigation:* those pentrail commands are denied in the permissions and again in the hook,
protected paths cannot be edited, overrides are refused for actors, and `shot` enforces
the deny list. `sh`/`bash` scripts are not allowed without your yes.
*Left to you:* the hook sees `sh script.sh`, not what is inside it. Read a script before
you approve it.

### T6. Your machine

*How:* sudo misuse, a poisoned compile cache, a malicious file in a project folder, a
hostile `.ovpn`.
*Mitigation:* sudo only for openvpn, `/etc/hosts` and installing the launcher. `hostfile`
validates IPs and names (no line injection), removes only lines it tagged, and changes a
line of yours only after you say yes. The compiled cache lives in a 700 folder and is
ignored when someone else could write it. The launcher runs Python isolated (`-I -S`), so a
`json.py` in a project folder is never imported. openvpn's log is created as you.
*Left to you:* an `.ovpn` can run scripts as root (`up`, `down`): use only configs from your
lab provider or client.

### T7. The code you run

*How:* `pentrail update` pulls `main` and reinstalls the launcher with sudo; whoever can
push to `main` changes what you run.
*Mitigation:* `--ff-only` pulls of the branch you chose; signed commits.
*Left to you:* two-factor authentication on every account that can push, and a look at
`git log` before `pentrail update`.

## Out of scope

A compromised local account or machine, Claude Code itself, and the security of the tools
pentrail runs (nmap, ffuf, ...).

## Reporting

Found a way around one of these? Open a private security advisory on the GitHub
repository rather than a public issue.
