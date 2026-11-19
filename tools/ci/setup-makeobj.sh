#!/usr/bin/env bash
# CI で makeobj を用意する（Linux）。
#   bash tools/ci/setup-makeobj.sh <指定> <置き場所>
# 指定:
#   upstream:<tag>  本家（simutrans/simutrans）のリリース <tag> の Linux 版の配布物（makeobj_linux-x64*.zip）を取る
#   otrp:<ref>      OTRP の fork（128na/simutrans）を <ref> で取り出し、makeobj だけをビルドする。
#                   キャッシュのキーに指定をそのまま使うので、<ref> はブランチではなくタグかコミットにする
# <置き場所>/makeobj があれば何もしない（キャッシュから戻したとき）。
# upstream は gh を使うので、GH_TOKEN が要る。
set -euo pipefail

spec="${1:?指定（upstream:<tag> か otrp:<ref>）が要る}"
dest="${2:?置き場所が要る}"
kind="${spec%%:*}"
ref="${spec#*:}"

if [ -x "$dest/makeobj" ]; then
  echo "[setup-makeobj] $spec: キャッシュのものを使う"
  exit 0
fi
mkdir -p "$dest"
work="$(mktemp -d)"

case "$kind" in
  upstream)
    gh release download "$ref" -R simutrans/simutrans -p "makeobj_linux-x64*.zip" -D "$work"
    unzip -q "$work"/makeobj_linux-x64*.zip -d "$work/unzip"
    install -m 755 "$work/unzip/makeobj" "$dest/makeobj"
    ;;
  otrp)
    git init -q "$work/src"
    git -C "$work/src" fetch -q --depth 1 https://github.com/128na/simutrans "$ref"
    git -C "$work/src" checkout -q FETCH_HEAD
    make -C "$work/src/makeobj" OSTYPE=linux OPTIMISE=1 -j"$(nproc)"
    install -m 755 "$work/src/build/default/makeobj/makeobj" "$dest/makeobj"
    ;;
  *)
    echo "[setup-makeobj] 知らない指定: $spec（upstream:<tag> か otrp:<ref>）" >&2
    exit 2
    ;;
esac
rm -rf "$work"
echo "[setup-makeobj] $spec: $dest/makeobj"
