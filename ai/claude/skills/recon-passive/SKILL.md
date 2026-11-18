---
name: recon-passive
description: Passive reconnaissance for an in-scope domain - DNS records, certificate transparency, archived URLs and public code - without sending traffic to the target, and how to feed what it finds back into pentrail. Use at the start of a domain or bug bounty engagement, or when the tester asks for subdomains, OSINT or "what is out there" before scanning.
---

# Passive recon

Rule: `passive_recon` (allow by default). Passive means the target never sees you: you ask
third parties (certificate logs, archives, public DNS) about it.

## What and how

| Question | Source | How PeTe gets it |
|---|---|---|
| subdomains with certificates | crt.sh | WebFetch `https://crt.sh/?q=%25.<domain>&output=json` |
| historic URLs, old endpoints | Wayback Machine CDX | WebFetch `https://web.archive.org/cdx/search/cdx?url=*.<domain>/*&output=json&fl=original&collapse=urlkey&limit=500` |
| DNS records | public resolvers | `pentrail shot -q --by pete --why "..." -l dns -- dig +noall +answer <domain> ANY` (the domain is a target, so through shot) |
| mail and SPF/DMARC | DNS TXT | `dig +short TXT <domain>`, `dig +short TXT _dmarc.<domain>` through shot |
| leaked code, configs | GitHub | WebFetch on github.com search pages (github.com is always allowed) |

Third-party sites are not in the scope, so a Bash `curl crt.sh` is stopped by the
guardrail; WebFetch to them is fine. Never fetch the target itself with WebFetch: the
guardrail sends you to `pentrail shot ... curl` for that.

## Feed it back

- Save what you collected for the record: write the list to `1-enum/scans/subdomains-crtsh.txt`
  (one name per line), then `pentrail ingest 1-enum/scans/subdomains-crtsh.txt`. Names in scope
  show up in `pentrail names`; names outside it are dropped.
- New names are **unknown** to the scope until they resolve into it. List them for the
  tester, grouped: resolves into the scope / resolves elsewhere / does not resolve. Never
  touch an unknown name. The tester adds names (`pentrail scope add`) or maps them
  (`pentrail hostfile add <ip> <name>`).
- Note the sources you used: `pentrail note -t none "passive recon: crt.sh, wayback (n names, m in scope)"`.

## What to look for

Dev, staging, vpn, sso, admin and api names; wildcard certificates; old endpoints in the
archive (`.bak`, `/api/v1`, upload forms); internal hostnames in public records.

## Read more

- https://book.hacktricks.wiki/en/generic-methodologies-and-resources/external-recon-methodology/index.html
- https://crt.sh and https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server
