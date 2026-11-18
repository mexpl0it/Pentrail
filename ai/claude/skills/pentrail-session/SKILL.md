---
name: pentrail-session
description: Start of a PeTe session in a pentrail project - read the session brief, check what changed since last time and what is running, agree who drives, and propose the next move. Use at the start of every session, after a /clear or compaction, or when the tester asks "where are we", "what's next" or "pick up where we left off".
---

# Starting a session

The SessionStart hook put the brief in your context. Build on it; do not ask the tester
for what the record already says.

## 1. Orient (read only, no target traffic)

```bash
pentrail pete brief             # the brief again, if it is not in your context
pentrail status                 # VPN, project, active box
pentrail log 20                 # what happened last, by whom
pentrail trace --by pete        # what you ran in earlier sessions, each with its why
pentrail vectors                # open leads, working first
pentrail next --json            # the plan for the active box: what is done, what is not
```

Running now (the brief's "Running now", or `pentrail trace`): a scan in flight, or the
command in the tester's capture. Never start the same thing again.

## 2. Check the ground rules

- Scope set? The brief says so. No scope: nothing is checked, so do nothing against
  targets. Ask the tester to set it (`pentrail scope add <host>`); you never do that.
- PeTe rules in `0-scope/scope.md`? If they are missing the defaults apply (brute force,
  spraying, exploitation and DoS deny; vuln scripts, credentials and sudo ask).
- VPN needed and down? Tell the tester (`pentrail up`, or `pentrail check` to diagnose).

## 3. Agree who drives

Ask in one line, unless the tester already said: "Shall I run the next round (you approve
it first), or do you drive and I advise?" See CLAUDE.md, Who drives.

## 4. Propose the next move

Three lines at most:

```
Where we are: 10.10.10.5, enum. 22, 80, 445 open; 2 open leads (#3 web login, #5 smb guest).
Not done yet: full TCP scan, UDP top ports, vhost fuzzing on 80.
Proposal: round 3 = those three (all allow). Go?
```

Then continue with `enum-run` for a round, or with the skill that fits the request.
