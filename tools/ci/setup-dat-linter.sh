#!/usr/bin/env bash
# dat_linter（128na/simutrans-dat-linter）を用意する（CI の Linux と、手元の Windows の Git Bash）。
#   bash tools/ci/setup-dat-linter.sh <版> <置き場所>
# <置き場所>/dat_linter（Windows は dat_linter.exe）があれば何もしない。gh を使う。CI では GH_TOKEN が要る。
set -euo pipefail

version="${1:?版（例: v0.3.1）が要る}"
dest="${2:?置き場所が要る}"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) exe=dat_linter.exe; asset=dat_linter-x86_64-pc-windows-msvc.exe ;;
  *) exe=dat_linter; asset=dat_linter-x86_64-unknown-linux-gnu ;;
esac

if [ -x "$dest/$exe" ]; then
  echo "[setup-dat-linter] $version: 用意済みのものを使う（$dest/$exe）"
  exit 0
fi
mkdir -p "$dest"
gh release download "$version" -R 128na/simutrans-dat-linter -p "$asset" -O "$dest/$exe" --clobber
chmod 755 "$dest/$exe"
echo "[setup-dat-linter] $version: $dest/$exe"
