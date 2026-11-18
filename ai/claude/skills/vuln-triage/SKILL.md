---
name: vuln-triage
description: Turning enumeration output into ranked vulnerability candidates without exploiting anything - matching versions and configurations to known issues, gathering the evidence pentrail recorded, rating confidence and impact, and recording each candidate as a lead for the tester to decide on. Use when enumeration is (mostly) done, when the tester asks "what is vulnerable" or "what should I look at", or before writing findings.
---

# Triage

Goal: a short, ranked list of candidates, each backed by recorded evidence, so the tester
knows where to spend time. You do not exploit or "confirm by exploiting". Probing with
vulnerability scripts (nikto, nuclei, `--script vuln`) is `vuln_scripts`: ask.

## 1. Collect the evidence

```bash
pentrail hosts <host> --json     # ports, versions, web paths, names, leads (each with the command id)
pentrail vectors                 # leads so far
pentrail show <id>               # the output behind a version or a lead
```

## 2. Match, carefully

For each service with a version, and each odd configuration:

- Known issues for that exact version: NVD (https://nvd.nist.gov), the vendor advisory,
  Exploit-DB (https://www.exploit-db.com) to see whether public exploits exist. Read about
  them; do not download or run them.
- Check the version really is that version: banners lie and backports exist (Debian and
  Ubuntu patch without changing the upstream version). Say so when it applies.
- Misconfigurations often matter more than CVEs: anonymous access, default pages, exposed
  `.git`, directory listing, SMB signing off, verbose errors.

## 3. Rank

| Field | Values |
|---|---|
| Confidence | confirmed (the output shows it), likely (version matches, conditions unknown), possible |
| Impact | what an attacker would get: read, write, code execution, credentials, denial of service |
| Effort | default creds and public PoC < needs auth < needs chaining |
| Evidence | command ids |

## 4. Record and hand over

```bash
pentrail vector add "Apache 2.4.49 path traversal (CVE-2021-41773), version from #4, not tested" -t lfi
pentrail note -t 10.10.10.5 "triage: 3 candidates (#6 #7 #8); vsftpd 3.0.3 has no known issue (#2)"
```

Then give the tester the list, top first, with for each: why it is a candidate, what would
confirm it, and the rule it falls under (`vuln_scripts` ask, exploitation deny). The
decision to test further is theirs.

## Read more

- https://www.first.org/cvss/ (severity), https://cwe.mitre.org (weakness types)
