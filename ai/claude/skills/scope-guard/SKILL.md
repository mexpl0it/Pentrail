---
name: scope-guard
description: How pentrail's scope guard and PeTe's guardrail decide what may be touched - scope check exit codes, verdicts (in, out, unknown, conflict), names that resolve into the scope, and what to do when a command is blocked. Use before touching a new host, name or URL, when a command was blocked, or when the tester asks whether something is in scope.
---

# The scope guard

pentrail reads the scope from `0-scope/scope.md` (In scope / Out of scope: IPs, ranges,
domains, `*.domain`, URLs). Out of scope always wins. You never change it.

## Check before you touch

```bash
pentrail scope                              # the scope and the guard mode
pentrail scope check 10.10.10.5             # one host
pentrail scope check nmap -sV 10.10.10.5    # a whole command line, every host in it
pentrail scope check --json <host|cmd>      # verdicts for a script
```

| Exit | Meaning | You |
|---|---|---|
| 0 | in scope | go on (through `pentrail shot`) |
| 3 | out of scope, not in scope, or a conflict | do not touch it; tell the tester |
| 2 | no host in what you checked | local work, fine |
| 4 | no scope set | do nothing against targets; ask the tester to set the scope |

## Verdicts

- **in**: listed, or a name that resolves only to in-scope addresses.
- **out**: listed under Out of scope (or resolves to an out-of-scope address).
- **unknown**: not listed. Treated as out. New names you discover (a vhost in a
  certificate, a domain in a redirect) are unknown until they resolve into the scope; ask
  the tester to add them or to map them (`pentrail hostfile add <ip> <name>`).
- **conflict**: the scope contradicts itself (an in-scope name pointing at an out-of-scope
  IP, or the other way round). Out wins until the tester settles it with the client.

## When you are blocked

The guardrail hook (before your Bash commands and web fetches) or `pentrail shot` (exit 3)
said no. Then:

1. Stop that step. Do not retry it another way: not another tool, not a script, not an IP
   instead of the name, not an encoded command. Every stop is in the logbook.
2. Tell the tester in one line: what you wanted, which host, the verdict, and why the step
   mattered. If you think the host belongs in scope, say so; the tester decides.
3. Go on with the rest of the round.

"Run it as: pentrail shot ..." from the hook means the host is in scope but you used a raw
command: run exactly that shot (with your `--why`).

## Read more

- pentrail README, Scope: names in your IP ranges, conflicts, blocking or informative.
