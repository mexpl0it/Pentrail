---
name: pete-layer
description: Changing PeTe, pentrail's AI layer in ai/ - its prompt (ai/claude/CLAUDE.md), skills, PeTe rules and Claude Code settings - together with the guardrail code in pentrail.py that enforces them, the ai/VERSION bump, and checking the result by installing it into a sandbox project. Use for any change under ai/, to the guardrail hook, the session brief, the status line, or to what PeTe may run.
---

# Changing PeTe

PeTe is data (`ai/`) plus enforcement (pentrail.py). A change to one usually needs the
other. The point of PeTe: it is transparent (every target command through
`pentrail shot -q --by pete --why ...`, plans and results in the record, claims cite ids)
and repeatable (`pentrail runbook`). Keep every change in that spirit.

## Where things live

| Want to change | Data (ai/) | Enforcement (pentrail.py) |
|---|---|---|
| what PeTe knows or how it works | `claude/CLAUDE.md`, `claude/skills/<name>/SKILL.md` | |
| allow / ask / deny per activity | `claude/rules.md` | `RULES_BLOCK` (same text), `RULE_TOOLS`, `rule_of()` |
| which pentrail commands it may run | `claude/settings.json` permissions | `_GUARD_CMDS` (always denied) |
| what is checked before each command | `claude/settings.json` hooks | `ai_pretooluse()`, `_shot_inner()`, `split_cmdline()` |
| what it reads at the start | | `ai_brief()`, `ai_sessionstart()` |
| install / update / remove | | `ai_install()`, `ai_remove()`, `_settings_sync()` |

## Rules

- **rules.md and RULES_BLOCK hold the same block.** Change both (or regenerate rules.md's
  block from RULES_BLOCK). A new rule also needs `RULE_TOOLS`/`rule_of()` to recognise it.
- **Never weaken a guard** to make a skill work. If a skill needs something the guardrail
  stops, the skill is wrong or the tester must do that step. Limits belong in code (the hook,
  `shot`), not only in the prompt: target text can talk PeTe into anything the code allows
  (THREAT-MODEL.md, T3 and T5).
- **Skills**: frontmatter `name` = folder name and a `description` that says what it does
  and when to use it (under 1024 chars). Every pentrail command in a code span must exist
  (`pentrail <cmd>`; there is no `pete` program). New skill: list it in `ai/claude/CLAUDE.md`
  under Skills and in `ai/README.md`. No exploitation, brute force or spraying instructions.
- **Personal skills beat project skills** in Claude Code: a skill with the same name in
  `~/.claude/skills/` shadows the one PeTe installs. Avoid generic names.
- **settings.json** uses `Bash(cmd *)` rules, `/path` for paths anchored at the project, and
  the PreToolUse hook keeps `"onFailure": "block"`.

## Version

Any change under `ai/` sets `ai/VERSION` to the release it ships in (the CHANGELOG's next
version). `pentrail pete status` then shows projects an update, and
`pentrail pete update --all` installs it (files the tester changed are kept as `.bak`).

## Check

```bash
python3 -m unittest discover -s tests -v       # shape of ai/, install/remove, the hook
```

Then in a sandbox (`sandbox-test` skill): `pentrail pete install`, `pentrail pete status`,
feed the hook the commands your change is about, `pentrail pete brief`. If you can, start
`claude` in the sandbox project and watch one round of `enum-run` against stand-in tools.
