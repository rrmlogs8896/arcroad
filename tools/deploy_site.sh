#!/bin/bash
# The only way arcroad.org ships: lint and every test first, then one wrangler deploy of web/.
# A failing check stops the deploy. Run from the repo root: bash tools/deploy_site.sh
set -euo pipefail
python3 -m ruff --version >/dev/null 2>&1 && python3 -m pytest --version >/dev/null 2>&1 || {
  echo "Needs ruff and pytest once: python3 -m pip install --user ruff pytest"; exit 1; }
python3 -m ruff check pipeline tests
python3 -m pytest -q
npx wrangler pages deploy web --project-name=arcroad-org
