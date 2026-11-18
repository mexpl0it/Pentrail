# PeTe rules

What PeTe may run on its own in a project. `pentrail ai install` puts the block below once
under **Rules of engagement** in `0-scope/scope.md`; from then on you edit them there, per
project. `pentrail` reads them from scope.md every time (the guardrail hook before each
command PeTe runs, and `pentrail shot` for anything that runs as PeTe).

- `allow`: PeTe runs it after one "go" from you for the round.
- `ask`: Claude Code asks you every time, even inside an approved round.
- `deny`: never, whatever you say in the chat. Change the rule in scope.md if you want it.

The guardrail recognises these by the tool and its options: hydra, medusa, ncrack and nmap
`*-brute` scripts are `brute_force`; kerbrute and netexec with a user or password list are
`password_spraying`; msfconsole, sqlmap, responder, evil-winrm, impacket's exec/dump tools
and nmap `exploit` scripts are `exploitation`; nikto, nuclei, wpscan and nmap `vuln` or
`intrusive` scripts are `vuln_scripts`; credentials on a netexec, smbclient, rpcclient or
ldapsearch command line are `credentialed_enum`; `sudo` is `root_commands`.

<!-- pentrail:rules -->
### PeTe rules (AI assistant)
<!-- What an AI assistant (PeTe) may run here on its own. allow = after one "go" from
     you per round, ask = its own yes every time, deny = never. Change the word after
     the colon to change a rule. -->
- passive_recon: allow - public sources only: DNS records, certificate logs, archives
- port_scan: allow - nmap, rustscan, masscan against in-scope hosts
- max_scan_rate: 1000 - packets per second at most (nmap --max-rate, masscan --rate)
- service_enum: allow - versions, banners, safe NSE scripts, anonymous and null-session checks
- web_content_discovery: allow - ffuf, feroxbuster, gobuster, vhost fuzzing, crawling
- vuln_scripts: ask - nmap --script vuln, nikto, nuclei: probes for known flaws
- credentialed_enum: ask - enumeration with credentials you hand to PeTe
- root_commands: ask - anything that needs sudo (UDP and SYN scans)
- brute_force: deny - guessing passwords or default logins against a service
- password_spraying: deny - trying one password on many accounts
- exploitation: deny - PeTe stops at the finding; exploiting it is yours to decide
- dos: deny - anything that may slow down or crash a service
- fast_mode: off - on: a one-line plan is enough when every step is allow
<!-- pentrail:end rules -->
