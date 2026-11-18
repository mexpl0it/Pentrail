---
name: add-command
description: Checklist for adding or changing a pentrail CLI command or option end to end - the cmd_* function, its subparser, HELP_SECTIONS, DETAILS, the README command reference, the CHANGELOG, the PeTe permissions and guardrail when PeTe may (not) run it, and a test. Use whenever a task adds, renames or changes a pentrail command, subcommand, flag or alias.
---

# Adding or changing a command

pentrail is one file; a command touches several places in it. Work through all of them.

## 1. The function

```python
def cmd_example(args):
    """One line: what it does. More lines: what it decides and why."""
    d = require_engagement()                 # the active project (or die with a hint)
    with locked(d):                          # only when it changes state.json
        st = load_state(d)
        ...
        save_state(d, st)                    # also refreshes the docs
    log_event("example", "what happened", d) # when something happened worth a logbook line
    ok("Done: ...")
```

- Put it next to the commands it belongs with: pentrail.py runs from helpers and state, through
  VPN, scope, parsing, capture, shot, docs, findings, planning/trace, the AI layer and setup, to
  help texts, `build_parser()` and `main()` at the bottom.
- Output: `info ok warn err die`, symbols from `SYM`, colours `B G Y R C M DIM N`. A `--json`
  output goes through `mask_secrets` and holds no credential.
- Exit codes are API: 0 ok, 1 error / not found, 3 blocked by scope or PeTe rules. Never
  reuse 3 for anything else.
- Standard library only, Python 3.8 syntax.

## 2. The parser (`build_parser()`)

```python
s = sub.add_parser("example", aliases=["ex"], help="one line for 'pentrail -h'")
s.add_argument(...); s.set_defaults(func=cmd_example)
```

An alias also goes into `HELP_ALIASES` so `pentrail help ex` finds the details. Commands that
take free text after them use `nargs=argparse.REMAINDER`.

## 3. Help

- `HELP_SECTIONS`: a row in the section it belongs to (`(usage, line1, line2)`, ~60 chars a line).
- `DETAILS["example"] = (what, usage, [body lines], example)`: the long `pentrail help example`.
- Check: `NO_COLOR=1 python3 pentrail.py help example` and `python3 pentrail.py help`.

## 4. PeTe, if the command matters to it

Decide: may PeTe run it on its own (read-only, recording), only after a yes (changes
facts, sudo, findings), or never (changes the scope, the guard, the PeTe rules, PeTe
itself, or hands it a shell)?

- `ai/claude/settings.json`: add `Bash(pentrail example *)` to `allow`, `ask` or `deny`.
- Never: also add it to `_GUARD_CMDS` in pentrail.py (the hook denies it whatever the
  settings say). The tests check every `Bash(pentrail X ...)` rule names a real command.
- A new `shot` option that takes a value: add it to `_shot_inner`, or the guardrail misreads
  the command line.
- Tell PeTe: the `pentrail` skill (`ai/claude/skills/pentrail/SKILL.md`) and, if it changes
  how PeTe works, `ai/claude/CLAUDE.md`. Then follow the `pete-layer` skill (ai/VERSION).

## 5. Docs and tests

- README: the section that explains it, and the Command reference table.
- CHANGELOG: lines under `## Unreleased` (Added / Changed / Fixed), in the user's words.
- A test in `tests/test_pentrail.py` using `Sandbox` (`sb.run(...)`, `sb.state()`).
- `python3 -m unittest discover -s tests -v`.
- Does it read output a target controls, or turn recorded text into something that runs?
  Check it against THREAT-MODEL.md (T2, T3) and update that file when the answer changes.
