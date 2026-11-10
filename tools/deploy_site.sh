#!/bin/bash
# The only way arcroad.org ships: lint and every test first, then one wrangler deploy of web/.
# A failing check stops the deploy. Run from the repo root: bash tools/deploy_site.sh
# If the Python environment at ~/.venvs/arcroad exists it is used automatically, so no
# "source" step is needed. ARCROAD_VENV overrides that location (the tests use it).
set -euo pipefail
VENV="${ARCROAD_VENV:-$HOME/.venvs/arcroad}"
if [ -x "$VENV/bin/python3" ]; then
  PY="$VENV/bin/python3"
elif [ -x "$VENV/bin/python" ]; then
  PY="$VENV/bin/python"
else
  PY=python3
fi
"$PY" -m ruff --version >/dev/null 2>&1 && "$PY" -m pytest --version >/dev/null 2>&1 || {
  echo "Needs ruff and pytest once: python3 -m pip install --user ruff pytest"; exit 1; }
"$PY" -m ruff check pipeline tests
"$PY" -m pytest -q
npx wrangler pages deploy web --project-name=arcroad-org
