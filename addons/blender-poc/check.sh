#!/usr/bin/env bash
# blender-poc の検査。CI（.github/workflows/addon-blender-poc.yml）はこれを呼ぶだけ。手元でも同じものを回せる（Windows は Git Bash）。
#   bash addons/blender-poc/check.sh
# POC なので Python の検査だけ（pak は作らない。#50）。道具の版は ci.env。要るもの: uvx か pipx（ruff）。
set -euo pipefail

POC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$POC/../.." && pwd)"
set -a; . <(grep -E '^[A-Z_]+=' "$POC/ci.env" | tr -d '\r'); set +a

echo "== ruff $RUFF"
if command -v uvx > /dev/null; then
  ruff=(uvx "ruff@$RUFF")
else
  ruff=(pipx run "ruff==$RUFF")
fi
(cd "$ROOT" && "${ruff[@]}" check addons/blender-poc)
echo "== blender-poc の検査はすべて通った"
