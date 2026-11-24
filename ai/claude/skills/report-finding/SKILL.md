---
name: report-finding
description: Writing findings and the report with pentrail - turning a confirmed lead into a finding file (pentrail finding <vector-id>), filling summary, impact, reproduction steps with command ids and remediation, rating severity, and filling or exporting the report. Use when a lead is confirmed, when the tester asks to write something up, or at the end of an engagement.
---

# Findings and the report

Creating a finding or the report is an ask step: say what you will create and why, then
run it when the tester agrees.

## A finding from a lead

```bash
pentrail vectors                         # the lead's id
pentrail finding 5 -s High               # 5-report/findings/F01-<slug>.md, prefilled
```

pentrail prefills severity, weakness, the asset, the command that found it, its output and
the evidence file. You write the parts it cannot know. `5-report/` is not protected: edit
the finding file with your file tools.

| Section | Write |
|---|---|
| Summary | two sentences: what is wrong, where |
| Impact | what an attacker gains, in the client's terms; no exaggeration |
| Steps to reproduce | numbered steps, each with the command and its id (`#16`); the tester must be able to repeat them with `pentrail runbook --ids ...` |
| Evidence | the evidence files pentrail linked; quote the lines that matter |
| Remediation | the concrete fix (version, setting, config line), and a reference |
| References | CVE, CWE, vendor advisory, OWASP |

Severity: base it on CVSS where it applies (https://www.first.org/cvss/calculator/3.1) and
say which vector string you used. When unsure, propose a rating and let the tester decide.

Only what the record shows goes in. Steps you did not run (exploitation) are written as
"the tester confirmed ..." only after the tester did and recorded it.

## The report

```bash
pentrail report            # fills 5-report/report.md (an ask step)
pentrail report --html     # also a styled report.html
pentrail report --mask     # hides credentials, for sharing
```

The tester writes the executive summary and conclusion; you can draft them from the
findings for them to edit. The appendix (hosts, commands with who ran them, evidence,
timeline) comes from the record; your commands show "pete" in the By column.

The report's figures are drawn from the record too: the attack path (per host: findings
by the phase they were found in, flags, `host own`, and `pivot <from> <to> --via "<how>"`
between hosts), a map of each web site and the findings by severity. When the path looks
incomplete, the record is: point out to the tester which flag, owned host or pivot is
missing, and let them record it. Do not draw or edit figures yourself.

## Read more

- https://owasp.org/www-community/OWASP_Risk_Rating_Methodology
- https://www.first.org/cvss/
