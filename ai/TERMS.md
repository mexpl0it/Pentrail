# Terms of use for PeTe

PeTe is for **authorized** security testing only: lab platforms (Hack The Box, TryHackMe,
OffSec), engagements with a written scope and permission, and bug bounty programs within
their published rules.

- **You are responsible for every command PeTe runs.** It runs on your machine, from your
  network, under your name. The scope guard, the PeTe rules and the permission prompts
  reduce mistakes; they do not move the responsibility.
- **Set the scope before PeTe works.** With no scope, pentrail checks nothing.
- **Read before you approve.** One "go" approves a whole round of `allow` steps. Read the
  round. `ask` steps get their own prompt; read those too.
- **PeTe does not exploit.** It stops at the finding. Exploitation, credential attacks and
  anything that may disrupt a service are yours to decide, under your rules of
  engagement.
- **Credentials and client data** stay in the project folder (mode 700). PeTe's brief and
  JSON outputs mask credentials. Claude Code sends what PeTe reads to the model provider:
  do not let it read data your engagement forbids sharing, and check your contract.
- **Review the record.** `pentrail trace --by pete` and the logbook show what PeTe did.
  Keep them with the engagement's evidence.

No warranty. Use at your own risk, within the law and your agreements.
