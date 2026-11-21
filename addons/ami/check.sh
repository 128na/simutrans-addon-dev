#!/usr/bin/env bash
# AMI の検査を全部回す。CI（.github/workflows/addon-ami.yml）はこれを呼ぶだけなので、手元で回しても同じ検査になる。
#   bash addons/ami/check.sh           # リポジトリのどこからでもよい（Windows は Git Bash）
#   SKIP_BUILD=1 bash addons/ami/check.sh   # pak のビルドを飛ばす
#   MAKEOBJ_FROM_PATH=1 bash addons/ami/check.sh   # ci.env の makeobj でなく、PATH の makeobj を使う
# 道具の版は ci.env。makeobj と dat_linter は TOOLS_DIR（既定は ~/.cache/simutrans-addon-dev/ci-tools）に取ってくる。
# 要るもの: Python、gh（道具を取るとき。サインイン済み）、uvx か pipx（ruff）。
# シートの描画（Blender）はしない（#50）。
set -euo pipefail

AMI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$AMI/../.." && pwd)"
set -a; . <(grep -E '^[A-Z_]+=' "$AMI/ci.env" | tr -d '\r'); set +a

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) PY="${PYTHON:-python}" ;;
  *) PY="${PYTHON:-python3}" ;;
esac
TOOLS_DIR="${TOOLS_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/simutrans-addon-dev/ci-tools}"

step() {
  [ -n "${GITHUB_ACTIONS:-}" ] && echo "::endgroup::"
  echo "${GITHUB_ACTIONS:+::group::}== $1"
}

step "ruff $RUFF"
if command -v uvx > /dev/null; then
  ruff=(uvx "ruff@$RUFF")
else
  ruff=(pipx run "ruff==$RUFF")
fi
(cd "$ROOT" && "${ruff[@]}" check addons/ami tools)

step "dat の書き忘れ（blender/ami_dat.py の出力と src/ の dat を比べる）"
snap="$(mktemp -d)"
cp "$AMI"/src/*.dat "$snap/"
rm -f "$AMI"/src/*.dat
"$PY" -X utf8 "$AMI/blender/ami_dat.py" > /dev/null
report="$snap/report.txt"
: > "$report"
for n in $( (cd "$snap" && ls *.dat; cd "$AMI/src" && ls *.dat) | sort -u ); do
  if [ ! -f "$snap/$n" ]; then echo "生成されたが src/ に無い: $n" >> "$report"
  elif [ ! -f "$AMI/src/$n" ]; then echo "src/ にあるが生成されない: $n" >> "$report"
  elif ! diff -q --strip-trailing-cr "$snap/$n" "$AMI/src/$n" > /dev/null; then
    echo "中身が違う: $n" >> "$report"
    diff --strip-trailing-cr "$snap/$n" "$AMI/src/$n" | head -20 >> "$report" || true
  fi
done
# 作業ツリーは元に戻す（この検査で dat を書き換えたままにしない）
rm -f "$AMI"/src/*.dat
cp "$snap"/*.dat "$AMI/src/"
if [ -s "$report" ]; then
  cat "$report"
  rm -rf "$snap"
  echo "${GITHUB_ACTIONS:+::error::}blender/ami_dat.py の出力と src/ の dat が違う。ami_dat.py を実行し、出た dat をコミットする"
  exit 1
fi
rm -rf "$snap"

step "アイコン・カーソルの参照先（セルの重なり・絵の有無・背景色・別のシートの絵。check_icons.py）"
"$PY" -X utf8 "$AMI/check_icons.py"

step "踏切のシートが今の道路のシートから描かれているか（check_crossing.py）"
"$PY" -X utf8 "$AMI/check_crossing.py"

step "車庫の絵の大きさ（箱積み駅舎の箱 1 段に収まるか。check_depot.py）"
"$PY" -X utf8 "$AMI/check_depot.py"

step "道具を用意する（makeobj: $MAKEOBJ、dat_linter: $DAT_LINTER）"
bash "$ROOT/tools/ci/setup-dat-linter.sh" "$DAT_LINTER" "$TOOLS_DIR/dat_linter"
export PATH="$TOOLS_DIR/dat_linter:$PATH"
if [ -z "${MAKEOBJ_FROM_PATH:-}" ] && [ -z "${SKIP_BUILD:-}" ]; then
  spec_dir="$TOOLS_DIR/makeobj/${MAKEOBJ//[:\/]/_}"
  bash "$ROOT/tools/ci/setup-makeobj.sh" "$MAKEOBJ" "$spec_dir"
  export PATH="$spec_dir:$PATH"
fi

step "dat_linter"
(cd "$AMI/src" && dat_linter lint --tile-size 256 .)

if [ -n "${SKIP_BUILD:-}" ]; then
  step "pak のビルドは飛ばした（SKIP_BUILD）"
else
  step "pak を作る"
  { makeobj || true; } | head -1
  (cd "$AMI" && "$PY" -X utf8 build.py)
fi

[ -n "${GITHUB_ACTIONS:-}" ] && echo "::endgroup::"
echo "== AMI の検査はすべて通った"
