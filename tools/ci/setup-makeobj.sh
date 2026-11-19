#!/usr/bin/env bash
# makeobj を用意する（CI の Linux と、手元の Windows の Git Bash）。
#   bash tools/ci/setup-makeobj.sh <指定> <置き場所>
# 指定:
#   upstream:<tag>  本家（simutrans/simutrans）のリリース <tag> の配布物を取る（Linux は makeobj_linux-x64*.zip、Windows は makeobj-win*.zip）
#   otrp:<ref>      OTRP の fork（128na/simutrans）を <ref> で取り出し、makeobj だけをビルドする（Linux だけ）。
#                   キャッシュのキーに指定をそのまま使うので、<ref> はブランチではなくタグかコミットにする
# <置き場所>/makeobj（Windows は makeobj.exe）があれば何もしない（キャッシュから戻したとき）。
# upstream は gh を使う。CI では GH_TOKEN が要る。
set -euo pipefail

spec="${1:?指定（upstream:<tag> か otrp:<ref>）が要る}"
dest="${2:?置き場所が要る}"
kind="${spec%%:*}"
ref="${spec#*:}"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) win=1; exe=makeobj.exe; asset="makeobj-win*.zip" ;;
  *) win=0; exe=makeobj; asset="makeobj_linux-x64*.zip" ;;
esac

if [ -x "$dest/$exe" ]; then
  echo "[setup-makeobj] $spec: 用意済みのものを使う（$dest/$exe）"
  exit 0
fi
mkdir -p "$dest"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

case "$kind" in
  upstream)
    gh release download "$ref" -R simutrans/simutrans -p "$asset" -D "$work"
    unzip -q "$work"/$asset -d "$work/unzip"
    bin="$(find "$work/unzip" -type f -name "$exe" | head -1)"
    [ -n "$bin" ] || { echo "[setup-makeobj] zip に $exe が無い" >&2; exit 1; }
    install -m 755 "$bin" "$dest/$exe"
    ;;
  otrp)
    if [ "$win" = 1 ]; then
      echo "[setup-makeobj] otrp: は Linux だけ（Windows では本体のビルドの手順で作った makeobj を PATH に置く）" >&2
      exit 2
    fi
    git init -q "$work/src"
    git -C "$work/src" fetch -q --depth 1 https://github.com/128na/simutrans "$ref"
    git -C "$work/src" checkout -q FETCH_HEAD
    # makeobj は libpng・zlib・bzip2 を使う。無ければ入れる（CI の runner は sudo が使える）
    if ! pkg-config --exists libpng 2> /dev/null; then
      sudo apt-get install -y -q libpng-dev zlib1g-dev libbz2-dev > /dev/null
    fi
    # 本体の Makefile は config.default を前提にする（取り出したソースの中にだけ作る）
    printf 'OSTYPE = linux\nOPTIMISE = 1\n' > "$work/src/config.default"
    make -C "$work/src/makeobj" -j"$(nproc)"
    install -m 755 "$work/src/build/default/makeobj/makeobj" "$dest/$exe"
    ;;
  *)
    echo "[setup-makeobj] 知らない指定: $spec（upstream:<tag> か otrp:<ref>）" >&2
    exit 2
    ;;
esac
echo "[setup-makeobj] $spec: $dest/$exe"
