#!/usr/bin/env bash
# Regenerate docs/images/*.svg from the Mermaid sources in this folder.
#
# Requires Node. Uses @mermaid-js/mermaid-cli (fetched via npx). If you already
# have a Chromium/Chrome, point PUPPETEER_EXECUTABLE_PATH at it to skip the
# download, e.g.:
#   PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium ./docs/diagrams/render.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$HERE/../images"
mkdir -p "$OUT"

PPTR_CFG="$(mktemp)"
if [ -n "${PUPPETEER_EXECUTABLE_PATH:-}" ]; then
  printf '{ "executablePath": "%s", "args": ["--no-sandbox"] }\n' "$PUPPETEER_EXECUTABLE_PATH" > "$PPTR_CFG"
else
  printf '{ "args": ["--no-sandbox"] }\n' > "$PPTR_CFG"
fi

for f in "$HERE"/*.mmd; do
  name="$(basename "$f" .mmd)"
  echo "==> $name.svg"
  npx -y @mermaid-js/mermaid-cli -i "$f" -o "$OUT/$name.svg" -p "$PPTR_CFG" -b white -t default
done

rm -f "$PPTR_CFG"
echo "Done -> $OUT"
