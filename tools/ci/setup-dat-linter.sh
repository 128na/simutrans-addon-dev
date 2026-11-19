#!/usr/bin/env bash
# CI で dat_linter（128na/simutrans-dat-linter）の Linux 版を用意する。
#   bash tools/ci/setup-dat-linter.sh <版> <置き場所>
# <置き場所>/dat_linter があれば何もしない。gh を使うので、GH_TOKEN が要る。
set -euo pipefail

version="${1:?版（例: v0.3.1）が要る}"
dest="${2:?置き場所が要る}"

if [ -x "$dest/dat_linter" ]; then
  echo "[setup-dat-linter] $version: キャッシュのものを使う"
  exit 0
fi
mkdir -p "$dest"
gh release download "$version" -R 128na/simutrans-dat-linter -p "dat_linter-x86_64-unknown-linux-gnu" -O "$dest/dat_linter" --clobber
chmod 755 "$dest/dat_linter"
echo "[setup-dat-linter] $version: $dest/dat_linter"
