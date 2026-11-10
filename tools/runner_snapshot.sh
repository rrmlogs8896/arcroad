#!/bin/bash
# Bake the code the research runner's jobs need into its image, so no job depends on GitHub.
# Run from the repo root on the iMac just before deploying the runner: bash tools/runner_snapshot.sh
set -euo pipefail
dest=research/runner/app/repo
mkdir -p "$dest"
git archive HEAD tools pipeline data | tar -x -C "$dest"
git rev-parse HEAD > "$dest/COMMIT"
echo "snapshot $(cat "$dest/COMMIT" | cut -c1-7) in $dest ($(du -sh "$dest" | cut -f1))"
