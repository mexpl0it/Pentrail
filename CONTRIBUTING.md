# Contributing

pentrail is one Python file (`pentrail.py`, standard library only, Python 3.8+) plus PeTe,
the AI layer, in `ai/`.

## Branches

- **`main` always works**: `pentrail update` pulls it for everyone. Changes reach it only
  through a pull request with green tests.
- **One topic branch per change**, from an up-to-date `main`, deleted after the merge:

  | Prefix | For |
  |---|---|
  | `feat/` | a new command, option or behaviour |
  | `fix/` | a bug fix |
  | `pete/` | the AI layer (`ai/`) |
  | `docs/`, `test/` | docs or tests only |
  | `chore/` | CI, tooling, a release (`chore/release-1.11.0`) |

- **No branches named after versions.** Versions are tags (`v1.10.0`) on `main`.
- **Squash and merge**: one commit per PR, titled in the imperative ("Add pentrail runbook").
- From a fork: sync its `main` with `mexpl0it/Pentrail` first, open the PR against
  `mexpl0it/Pentrail:main`.

## Versions

[Semantic Versioning](https://semver.org) since 1.10.0:

| Bump | When |
|---|---|
| MAJOR | something people or scripts rely on breaks: a command or option removed, an exit code changed, `state.json` without a migration |
| MINOR | something new: a command, an option, a parser, a PeTe skill |
| PATCH | fixes and wording |

- `VERSION` in `pentrail.py` is the release.
- `ai/VERSION` is the release that last changed `ai/`: change `ai/`, set it to the coming
  release; otherwise leave it. `pentrail pete update --all` brings projects up to it.
- `SCHEMA` in `pentrail.py` changes only together with a step in `_migrate()`.

Every PR that changes behaviour adds lines under `## Unreleased` at the top of
`CHANGELOG.md` (Fixed / Added / Changed), written for users. A release renames that
heading to the version.

## Checks

```bash
python3 -m py_compile pentrail.py
python3 -m unittest discover -s tests -v      # throwaway $HOME, stand-in tools, no network, no sudo
```

A new command needs its `cmd_*` function, a subparser in `build_parser()`, a
`HELP_SECTIONS` row, a `DETAILS` entry, the README, the CHANGELOG and a test. Never test
against hosts you may not touch.

## Pushing and releasing

`scripts/submit.sh` does both; it shows what it will do, asks before every step that leaves
your machine and never pushes to `main`.

```bash
scripts/submit.sh -b fix/capture-zsh -m "Fix capture reading commands only at exit"
#   branch (if needed) -> checks -> commit everything -> push -> pull request to main
scripts/submit.sh -F message.txt          # title, blank line, description: for the commit and the PR

scripts/submit.sh --release
#   on main after the PR is merged: checks -> tag vVERSION -> push tag -> GitHub release
```

Without `-m` or `-F` it uses `.git/SUBMIT_MSG` when that exists (a message prepared for you,
for example by Claude Code; removed after the commit), else it asks for a title.

A release: on `chore/release-X.Y.Z`, set `VERSION` (and `ai/VERSION` if `ai/` changed since
the last release) and rename `## Unreleased` to `## X.Y.Z`. Submit it with `scripts/submit.sh`,
merge the PR, then `git switch main && scripts/submit.sh --release`. CI fails a tag that is
not `VERSION`.
