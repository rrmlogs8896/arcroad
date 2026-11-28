#!/bin/bash
# Public copy (28 Nov 2026): after a live deploy, bring the public arcroad-open repo up to date as one
# new commit, so its history grows release by release. Only files the public repo already holds are
# updated. New files are listed for review and never added here. A privacy screen and the public
# repo's own tests run first; any hit or failure stops before anything is pushed.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DST="${ARCROAD_OPEN:-}"
if [ -z "$DST" ]; then
  for d in "$HOME/Sites/arcroad-open" "$HOME/arcroad-open" "$HOME/Documents/arcroad-open"; do
    if [ -d "$d/.git" ]; then DST="$d"; break; fi
  done
fi
if [ -z "$DST" ] || [ ! -d "$DST/.git" ]; then
  echo "open-sync: public copy not found (set ARCROAD_OPEN to its folder). Skipped."; exit 0
fi
PY="${PY:-python3}"
cd "$DST"
git pull --ff-only -q
# The public copy keeps its own versions of these (public README and notices, its own CI and deploy).
KEEP='^(README\.md|\.gitignore|DISCLAIMER\.md|DATA-LICENSE\.md|LICENSE|SECURITY\.md|\.github/.*|\.devcontainer/.*|tools/deploy_site\.sh|tests/test_deploy_site_venv\.py)$'
git ls-files -z | while IFS= read -r -d '' f; do
  if [[ "$f" =~ $KEEP ]]; then continue; fi
  if [ -f "$SRC/$f" ] && ! cmp -s "$SRC/$f" "$f"; then cp "$SRC/$f" "$f"; fi
done
NEW=$(cd "$SRC" && git ls-files web functions pipeline tools tests docs data | while read -r f; do
  [ -e "$DST/$f" ] || echo "$f"; done | grep -v -E '^(web/(jury|admin)/|tools/open_sync\.sh$)' || true)
if git diff --quiet; then
  echo "open-sync: public copy already matches. Nothing to push."
else
  HITS=$(git diff -U0 | grep '^+' | grep -v '^+++' | grep -n -i -E 'genpact|mythri|janapriya|miwa|passcode|location\.csv|\.gpx\b|gcp-project|BEGIN [A-Z ]*PRIVATE KEY|api[_-]?key *[:=]' || true)
  if [ -n "$HITS" ]; then
    echo "open-sync: STOPPED. Privacy screen matched these added lines:"; echo "$HITS" | cut -c1-160
    git stash -q; echo "open-sync: changes set aside (git stash) in the public copy; nothing pushed."; exit 1
  fi
  if [ -d tests ]; then
    "$PY" -m pytest -q -x >/tmp/open-sync-tests.log 2>&1 || { echo "open-sync: STOPPED. Public copy tests failed, see /tmp/open-sync-tests.log. Nothing pushed."; git stash -q; exit 1; }
  fi
  MSG=$(cd "$SRC" && git log -1 --pretty=%s)
  git add -u
  git commit -q -m "Release $(date +%Y-%m-%d): $MSG"
  git push -q
  echo "open-sync: pushed $(git rev-parse --short HEAD) to the public copy ($(git diff --stat HEAD~1 | tail -1))"
fi
if [ -n "$NEW" ]; then
  echo "open-sync: new files not yet in the public copy (review before adding):"; echo "$NEW" | sed 's/^/  /' | head -40
fi
