#!/usr/bin/env bash
# 画面を出さない OTRP 本体（Makefile の BACKEND=posix）をビルドする（CI の Linux 用。#236）。
#   bash tools/ci/setup-headless-sim.sh otrp:<ref> <置き場所>
# <置き場所>/sim と <置き場所>/simutrans-test-base.zip（本体の tests/ にある pakset）ができる。あれば何もしない（キャッシュから戻したとき）。
# <ref> はタグかコミット（キャッシュのキーに指定をそのまま使う）。
# Windows の手元では使わない（MinGW で作った sim を HEADLESS_SIM_BIN に渡す。addons/ami/README.md の「画面を出さない本体での読み込みの検査」）。
set -euo pipefail

spec="${1:?指定（otrp:<ref>）が要る}"
dest="${2:?置き場所が要る}"
[ "${spec%%:*}" = otrp ] || { echo "[setup-headless-sim] 知らない指定: $spec（otrp:<ref>）" >&2; exit 2; }
ref="${spec#*:}"

if [ -x "$dest/sim" ] && [ -f "$dest/simutrans-test-base.zip" ]; then
  echo "[setup-headless-sim] $spec: 用意済みのものを使う（$dest/sim）"
  exit 0
fi
mkdir -p "$dest"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

git init -q "$work/src"
git -C "$work/src" fetch -q --depth 1 https://github.com/128na/simutrans "$ref"
git -C "$work/src" checkout -q FETCH_HEAD
# 本体は libpng・zlib・bzip2・zstd を使う（SDL・FreeType は要らない）
if ! pkg-config --exists libpng libzstd 2> /dev/null; then
  sudo apt-get install -y -q build-essential pkg-config libbz2-dev libpng-dev zlib1g-dev libzstd-dev > /dev/null
fi
printf 'BACKEND = posix\nOSTYPE = linux\nCOLOUR_DEPTH = 16\nDEBUG = 0\nMSG_LEVEL = 3\nOPTIMISE = 1\nMULTI_THREAD = 1\nUSE_ZSTD = 1\nUSE_FREETYPE = 0\n' > "$work/src/config.default"
make -C "$work/src" -j"$(nproc)"
install -m 755 "$work/src/build/default/sim" "$dest/sim"
cp "$work/src/tests/simutrans-test-base.zip" "$dest/simutrans-test-base.zip"
echo "[setup-headless-sim] $spec: $dest/sim"
