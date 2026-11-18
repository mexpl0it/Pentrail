---
name: methodology
description: The pentest phases pentrail is organised by (scope, enum, foothold, privesc, lateral, report), what belongs in each, where pentrail keeps it, and which phase PeTe may work in. Use when deciding what comes next, when the tester asks how a step fits the methodology, or before suggesting a change of phase.
---

# Methodology

pentrail lays a project out by phase. Each phase has a folder, a Markdown doc the tester
writes in (pentrail fills the blocks between `<!-- pentrail:auto ... -->` markers), and an
`evidence/` folder.

| Phase | Folder | What happens | PeTe |
|---|---|---|---|
| scope | `0-scope/` | what is in and out, rules of engagement, PeTe rules | reads only |
| enum | `1-enum/` | passive and active recon, ports, services, web, AD | plans and runs (rules allow) |
| foothold | `2-foothold/` | first access | advises; exploitation is the tester's |
| privesc | `3-privesc/` | local enumeration, escalation | advises only |
| lateral | `4-lateral/` | movement between hosts (`pentrail pivot`) | advises only |
| report | `5-report/` | findings, the report | drafts findings after a yes |

## The loop inside enum

```
passive recon -> port scan -> versions -> per-service enum -> web enum -> triage -> findings
       ^                                                              |
       +--------------- new names, hosts, ports feed back ------------+
```

- Breadth first: every open port gets its basic enumeration before anything goes deep.
- Coverage: a full TCP scan, `-sV` on every open TCP port, UDP top ports, and vhost fuzzing
  when there is a web port. `pentrail next <host> --json` tracks these.
- Each result is a lead (`pentrail vector add`), a fact (`pentrail set`, ask first) or a dead
  end (`pentrail note`). A lead that is confirmed becomes a finding (`report-finding`).

## Changing phase

Only the tester changes phase (`pentrail phase <name>`, which you may suggest; it asks for
permission). Suggest moving on when `pentrail next --json` shows the plan done and the leads
point at access rather than more enumeration. Foothold and later are the tester's work:
help them understand, never run exploits.

## Read more

- PTES technical guidelines: http://www.pentest-standard.org/index.php/PTES_Technical_Guidelines
- OWASP Web Security Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- HackTricks methodology: https://book.hacktricks.wiki/en/generic-methodologies-and-resources/pentesting-methodology.html
