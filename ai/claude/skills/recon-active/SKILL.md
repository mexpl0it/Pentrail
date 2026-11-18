---
name: recon-active
description: The first active scans of an in-scope host or range through pentrail shot - host discovery, a fast top-ports scan, the full TCP scan, versions and default scripts on what is open, and UDP top ports - at a polite rate, with output pentrail reads. Use when a target has no open ports recorded yet, for the coverage checks (full-tcp, versions, udp), or when the tester asks to scan.
---

# Active recon: ports and versions

Rules: `port_scan` (allow), `max_scan_rate` (packets per second), `root_commands` (ask:
SYN and UDP scans need sudo). Check first: `pentrail seen <host> -p-`,
`pentrail seen <host> full-tcp`, `pentrail next <host> --json` (coverage block).

## The usual order

```bash
# 1. quick look: top 1000 TCP, versions, default scripts
pentrail shot -q --by pete --why "first look: top ports, versions" -l nmap-init -- \
  nmap -sC -sV --max-rate 1000 -oA 1-enum/scans/nmap-init 10.10.10.5

# 2. every TCP port (background; connect scan, no sudo)
pentrail shot -q --by pete --why "coverage: ports outside the top 1000" -l nmap-full -- \
  nmap -p- -sT --min-rate 500 --max-rate 1000 -oA 1-enum/scans/nmap-full 10.10.10.5

# 3. versions and scripts on the ports the full scan found that step 1 did not
pentrail shot -q --by pete --why "versions on new ports from #<id>" -l nmap-new -- \
  nmap -sC -sV -p <ports> -oA 1-enum/scans/nmap-new 10.10.10.5

# 4. UDP top ports (sudo: an ask step)
pentrail shot -q --by pete --why "SNMP, TFTP, IKE are easy to miss" -l nmap-udp -- \
  sudo nmap -sU --top-ports 100 --max-rate 1000 -oA 1-enum/scans/nmap-udp 10.10.10.5
```

- `--max-rate` at or under the rule's `max_scan_rate`. For a range, also scan politely:
  `-T3`, and `--exclude` anything out of scope (the guard checks ranges too).
- `-oA 1-enum/scans/<name>`: pentrail reads the `.nmap`/`.xml` files and credits ports to
  the command. `-sC` runs only the `default` NSE category: safe.
- Hosts that do not answer ping: add `-Pn` and say why in `--why`.

## What to look for

Unusual high ports (dev web servers, admin panels), versions with known issues (a lead for
`vuln-triage`, not an exploit), hostnames in `ssl-cert`, `http-title` redirects and
`rdp-ntlm-info` (the domain: suggest `pentrail set domain <name>` to the tester), SMB
signing, anonymous FTP.

## Read more

- https://nmap.org/book/man-performance.html (rates and timing)
- https://nmap.org/nsedoc/categories/default.html
