#!/bin/bash
# Rebuild the functions bundle for the Workers-hosted site. Run from the repo root: bash site/build.sh
set -euo pipefail
npx wrangler@4.156.2 pages functions build functions --outdir site/dist --output-routes-path /tmp/arcroad_routes.json
echo "functions bundle ready in site/dist"
