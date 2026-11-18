---
name: release
description: Making a pentrail release with the repository's branch and SemVer strategy - choosing the bump from the CHANGELOG's Unreleased lines, setting VERSION and ai/VERSION, renaming the CHANGELOG heading, and handing the push, tag and GitHub release to scripts/submit.sh, which the user runs. Use when the user asks to release, bump the version or tag, or when deciding which branch or version a change belongs to.
---

# Releasing pentrail

The user pushes, tags and releases **themselves** with `scripts/submit.sh`. Prepare the
change, run the checks, then give them the exact command. Do not commit, push or tag.

## Which branch

A topic branch from an up-to-date `main`: `feat/`, `fix/`, `pete/`, `docs/`, `test/` or
`chore/` plus a short topic. Never work on `main`; never name a branch after a version.

## Which version

From the lines under `## Unreleased` in CHANGELOG.md (`git log v<last>..HEAD` to double-check):

- a command, option, exit code or state.json layout people rely on breaks: MAJOR
- anything Added (command, option, parser, PeTe skill): MINOR, PATCH to 0
- only Fixed or wording: PATCH

`ai/VERSION` becomes the new version only when `ai/` changed since the last release
(`git diff --stat v<last>..HEAD -- ai/`). `SCHEMA` changes only with a `_migrate()` step.

## Prepare the release

1. Branch `chore/release-X.Y.Z` (or the PR itself, when it is the only change in the release).
2. `VERSION = "X.Y.Z"` in pentrail.py, and `ai/VERSION` if needed.
3. CHANGELOG: `## Unreleased` becomes `## X.Y.Z`, with a one-paragraph summary under it.
4. `python3 -m unittest discover -s tests -v`: it checks VERSION, the CHANGELOG and ai/VERSION agree.

## Hand over

Write the commit message to `.git/SUBMIT_MSG`: an imperative title, a blank line, then
what changed and why for a reviewer. `scripts/submit.sh` uses it for the commit and the pull
request and removes it after the commit.

```bash
scripts/submit.sh -b chore/release-X.Y.Z -m "Release X.Y.Z"  # checks, commit, push, PR
# after the PR is merged:
git switch main && scripts/submit.sh --release                 # tag vX.Y.Z, push it, GitHub release
```

Users then get it with `pentrail update`, and projects with PeTe with
`pentrail pete update --all` when `ai/VERSION` moved.
