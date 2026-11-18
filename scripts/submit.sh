#!/usr/bin/env bash
# Submit your changes to pentrail the way CONTRIBUTING.md describes, and release it. You run
# it; it shows what it will do, asks before every step that leaves your machine and never
# pushes to main.
#
#   scripts/submit.sh [-b <branch>] [-m "<title>" | -F <file>] [--no-pr] [-y] [--dry-run]
#       checks, commits everything that changed, pushes the topic branch, opens a PR to main
#   scripts/submit.sh --release [-y] [--dry-run]
#       on main, after the PR is merged: tag vVERSION, push the tag, GitHub release
#
# The message: -m gives a one-line title, -F a file (title, blank line, description). Without
# either it uses .git/SUBMIT_MSG when that exists (prepared for you, removed after the
# commit), else it asks for a title. The PR gets the same title and description.
set -euo pipefail

die() { printf 'submit: %s\n' "$*" >&2; exit 1; }
say() { printf '\033[1m==>\033[0m %s\n' "$*"; }
run() { if [ "$dry" = 1 ]; then printf '    (dry run) %s\n' "$*"; else "$@"; fi; }
ask() {
  [ "$yes" = 1 ] && return 0
  printf '%s [y/N] ' "$1"; read -r a
  case $a in y|Y|yes|j|J|ja) return 0;; *) return 1;; esac
}
checks() {
  say "checks"
  python3 -m py_compile pentrail.py
  python3 -m unittest discover -s tests -q </dev/null      # tests never read your keyboard
}

branch="" title="" msgfile="" release=0 pr=1 dry=0 yes=0
while [ $# -gt 0 ]; do
  case $1 in
    -b|--branch)  branch=${2:?-b needs a branch name}; shift 2;;
    -m|--message) title=${2:?-m needs a title}; shift 2;;
    -F|--file)    msgfile=${2:?-F needs a file}; shift 2;;
    --release)    release=1; shift;;
    --no-pr)      pr=0; shift;;
    -y|--yes)     yes=1; shift;;
    --dry-run)    dry=1; shift;;
    -h|--help)    sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *)            die "unknown option '$1' (see --help)";;
  esac
done
[ -z "$title" ] || [ -z "$msgfile" ] || die "-m or -F, not both"

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || die "not in a git checkout"
[ -f pentrail.py ] || die "not the pentrail repository"
version=$(sed -n 's/^VERSION = "\([^"]*\)".*/\1/p' pentrail.py)
cur=$(git rev-parse --abbrev-ref HEAD)
prepared=$(git rev-parse --git-path SUBMIT_MSG)

# ---------------------------------------------------------------------------- release
if [ "$release" = 1 ]; then
  [ "$cur" = main ] || die "a release is tagged on main (git switch main)"
  [ -z "$(git status --porcelain)" ] || die "main has uncommitted changes"
  run git pull --ff-only origin main
  grep -q "^## $version\( \|$\)" CHANGELOG.md || die "CHANGELOG.md has no '## $version' heading"
  ! git rev-parse -q --verify "refs/tags/v$version" >/dev/null || die "tag v$version exists already"
  checks
  notes=$(awk -v v="## $version" 'index($0, v) == 1 {f = 1; next} /^## / {if (f) exit} f' CHANGELOG.md)
  say "release v$version from $(git log -1 --format='%h %s')"
  ask "tag v$version, push the tag and publish the GitHub release?" || die "stopped; nothing tagged"
  run git tag -a "v$version" -m "pentrail $version"
  run git push origin "v$version"
  if command -v gh >/dev/null; then
    printf '%s\n' "$notes" | run gh release create "v$version" --title "pentrail $version" --notes-file -
  else
    say "no gh: make the release on GitHub from tag v$version, notes from CHANGELOG.md"
  fi
  exit 0
fi

# ---------------------------------------------------------------------------- submit
if [ -n "$branch" ] && [ "$branch" != "$cur" ]; then
  case $branch in
    feat/*|fix/*|pete/*|docs/*|test/*|chore/*) ;;
    *) die "branch names start with feat/ fix/ pete/ docs/ test/ or chore/ (CONTRIBUTING.md)";;
  esac
  run git switch -c "$branch"                  # your uncommitted changes come along
  cur=$branch
fi
[ "$cur" != main ] || die "you are on main: pass -b feat/<topic> (or fix/, pete/, docs/, ...) to use a branch"

# the message: -m, -F, the prepared .git/SUBMIT_MSG, or a title typed now
tmp=$(mktemp); trap 'rm -f "$tmp"' EXIT
used_prepared=0
if [ -n "$msgfile" ]; then
  [ -s "$msgfile" ] || die "message file '$msgfile' is empty or missing"
  cp "$msgfile" "$tmp"
elif [ -n "$title" ]; then
  printf '%s\n' "$title" > "$tmp"
elif [ -s "$prepared" ]; then
  cp "$prepared" "$tmp"; used_prepared=1
fi

if [ -n "$(git status --porcelain)" ]; then
  say "changes on $cur"
  git status --short
  checks
  if [ ! -s "$tmp" ]; then
    printf 'commit title (imperative, e.g. "Add pentrail runbook"): '; read -r title
    [ -n "$title" ] || die "no title; nothing committed"
    printf '%s\n' "$title" > "$tmp"
  fi
  say "commit message$([ "$used_prepared" = 1 ] && printf ' (from %s)' "$prepared")"
  sed 's/^/    /' "$tmp"
  ask "commit all of the above with this message?" || die "stopped; nothing committed"
  run git add -A
  run git commit -F "$tmp"
  [ "$used_prepared" = 0 ] || [ "$dry" = 1 ] || rm -f "$prepared"
else
  say "nothing new to commit on $cur"
  checks
fi

ask "push $cur to origin?" || die "stopped; committed locally, not pushed"
run git push -u origin "$cur"

[ "$pr" = 1 ] || exit 0
if ! command -v gh >/dev/null; then
  url=$(git remote get-url origin | sed -E 's#^git@github.com:#https://github.com/#; s#\.git$##')
  say "no gh: open the pull request at $url/compare/main...$cur"
elif gh pr view "$cur" >/dev/null 2>&1; then
  say "pull request: $(gh pr view "$cur" --json url -q .url)"
else
  # title and description from the message; without one, from the branch's commits
  if [ -s "$tmp" ]; then
    body=$(mktemp); trap 'rm -f "$tmp" "$body"' EXIT
    tail -n +3 "$tmp" | grep -v '^Co-Authored-By:' > "$body" || true    # trailers are for the commit
    run gh pr create --base main --head "$cur" --title "$(head -n 1 "$tmp")" --body-file "$body"
  else
    run gh pr create --base main --head "$cur" --fill
  fi
fi
