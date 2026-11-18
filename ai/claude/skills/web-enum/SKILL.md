---
name: web-enum
description: Enumerating an in-scope web service through pentrail shot - fingerprinting, TLS certificate names, content discovery with one dirbuster, virtual host fuzzing, robots/sitemap and page source - with output pentrail reads and without repeating what ran. Use for a web port in pentrail next, the vhosts coverage check, or when the tester asks to look at a site.
---

# Web enumeration

Rules: `service_enum` (fingerprinting), `web_content_discovery` (dirbusting, vhost
fuzzing, crawling): allow. `vuln_scripts` (nikto, nuclei, wpscan): ask. Logging in with
guessed credentials is brute_force: deny.

pentrail counts ffuf, feroxbuster, gobuster, dirsearch, dirb and wfuzz as one tool:
`pentrail seen <host> ffuf` is true if any of them ran. Check the wordlist and port too
(`pentrail seen <host> raft-medium`).

## Steps

```bash
# fingerprint: server, framework, redirects, title
pentrail shot -q --by pete --why "what runs on 80" -l whatweb-80 -- whatweb -a 3 http://10.10.10.5
pentrail shot -q --by pete --why "headers, redirect target" -l curl-80 -- curl -skI http://10.10.10.5/

# names in the certificate (https)
pentrail shot -q --by pete --why "hostnames in the cert" -l cert-443 -- nmap -p443 --script ssl-cert 10.10.10.5

# robots.txt and sitemap
pentrail shot -q --by pete --why "paths the site hides" -l robots-80 -- curl -sk http://10.10.10.5/robots.txt

# content discovery (one tool, a fitting list, its own output file)
pentrail shot -q --by pete --why "hidden directories and files" -l ferox-80 -- \
  feroxbuster -u http://10.10.10.5 -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
  -t 20 --rate-limit 100 -x php,txt,bak -o 1-enum/scans/ferox_80.txt

# virtual hosts (needs the domain; filter the default response size)
pentrail shot -q --by pete --why "other sites behind the same IP" -l vhosts-80 -- \
  ffuf -u http://10.10.10.5 -H "Host: FUZZ.box.htb" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -fs <default size> -o 1-enum/scans/vhosts_80.json
```

- Use the wordlist the tester uses: `pentrail next <host> --json` shows the dirbuster command
  built from their config. Keep the rate polite.
- A name that only works through the Host header needs an `/etc/hosts` line before you
  can browse it: ask the tester (`pentrail hostfile add 10.10.10.5 dev.box.htb`), and check it
  is in scope first (`pentrail scope check dev.box.htb`).
- Look at the page source for comments, JS files with API routes, version strings, and
  forms (login, upload, search).

## What to look for

Admin and login panels, `.git/`, backups (`.bak`, `.old`, `~`), upload forms, API docs
(`/swagger`, `/api-docs`), default pages that give a version, debug pages, vhosts with a
different size. Each one is a lead: `pentrail vector add "<what> at <url> (#id)" -t web`.

## Read more

- https://book.hacktricks.wiki/en/network-services-pentesting/pentesting-web/index.html
- https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/
