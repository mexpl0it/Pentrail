---
name: retest
description: Running recorded work again with pentrail runbook - a whole host, one actor's commands, one round by command ids, or one phase - for a retest after a fix, a box reset, a second opinion or to show exactly what PeTe did, and comparing the new results with the old ones. Use when the tester asks to repeat, replay, rerun or retest something, or asks how to reproduce PeTe's work.
---

# Running it again

`pentrail runbook` turns recorded commands into a script. Each step runs again through
`pentrail shot`, so the scope guard (and, for you, the PeTe rules) checks it again and the
rerun gets its own id and evidence: the old and the new results sit side by side.

## Make the runbook

```bash
pentrail runbook --by pete --ids 14,15,16       # one round (ids from its summary)
pentrail runbook -H 10.10.10.5                  # everything that ran against a host, by anyone
pentrail runbook --by pete --phase enum         # everything PeTe ran in enum
pentrail runbook -t nmap -H 10.10.10.5          # only the nmap runs
pentrail runbook --by pete -o 1-enum/rerun.sh   # to a file (mode 700) instead of the screen
```

Each step shows the original id, time, phase, who, source, exit code, PeTe rule and why.
Credentials stay masked: such steps are commented out, and so are interactive sessions
(ssh, evil-winrm, nc, ...). Steps with pipes or redirects run under `sh -c`.

## Who runs it

- **The tester** runs the script (`sh rerun.sh`) after reading it. That is the usual way,
  and the right one for a retest the client will see.
- **You** do not run the script as a whole. To redo a round yourself, show the runbook, get
  the "go" as for any round (`enum-run`), and run its steps one by one as your own shots
  with `--why "rerun of #<id>: <reason>"`. The guardrail then checks every step.

## Compare

After a rerun, put old and new next to each other:

```bash
pentrail trace -H <host> -t <tool>      # the old id and the new one
pentrail show <old-id> -n 0 > /tmp/old.txt; pentrail show <new-id> -n 0 > /tmp/new.txt; diff /tmp/old.txt /tmp/new.txt
```

Report per finding: still there (with the new id), fixed (what changed in the output), or
inconclusive (and why). Update the lead: `pentrail vector done <id>` when the fix holds.
Record the retest: `pentrail note -t <host> "retest of F01: fixed, #31 shows ... (was #15)"`.
