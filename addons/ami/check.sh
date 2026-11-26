#!/usr/bin/env bash
# AMI の検査を全部回す。CI（.github/workflows/addon-ami.yml）はこれを呼ぶだけなので、手元で回しても同じ検査になる。
#   bash addons/ami/check.sh           # リポジトリのどこからでもよい（Windows は Git Bash）
#   SKIP_BUILD=1 bash addons/ami/check.sh   # pak のビルドを飛ばす
#   CHECK_256_FULL=1 bash addons/ami/check.sh   # 256 のシート（src256/）を全部そろえた手元で、256 の検査を全部の物に厳しく流す（#261）
#   MAKEOBJ_FROM_PATH=1 bash addons/ami/check.sh   # ci.env の makeobj でなく、PATH の makeobj を使う
#   HEADLESS_SIM_BIN=<sim> HEADLESS_PAKSET=<simutrans-test-base.zip> bash addons/ami/check.sh   # 画面を出さない本体で pak を読む検査（下記）。Windows の手元はこれを渡す。渡さないと飛ばす
# 道具の版は ci.env。makeobj と dat_linter は TOOLS_DIR（既定は ~/.cache/simutrans-addon-dev/ci-tools）に取ってくる。
# 要るもの: Python（と Pillow・numpy。Pillow は check_cells.py が PNG を速く読む（無くても通るが数分かかる）のと、check_snow_edge.py が要る。numpy は check_ground_mask.py・check_snow_edge.py が要る。版は ci.env）、gh（道具を取るとき。サインイン済み）、uvx か pipx（ruff）。
# シートの描画（Blender）はしない（#50）。
set -euo pipefail
unset CHECK_SKIP_MISSING  # 環境に残っていると、128 の検査もシートの無い物を黙って飛ばす。256 の検査の行だけで付ける

AMI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$AMI/../.." && pwd)"
set -a; . <(grep -E '^[A-Z_]+=' "$AMI/ci.env" | tr -d '\r'); set +a

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) PY="${PYTHON:-python}" ;;
  *) PY="${PYTHON:-python3}" ;;
esac
TOOLS_DIR="${TOOLS_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/simutrans-addon-dev/ci-tools}"

# ほかの ami_dat.py・build.py・check.sh と同時に走らない（#326。重なって src/*.dat が消え、壊れた pak ができた: #197）。
# 自分をロックの下で走らせ直す。先に取った物があれば待つ。中で呼ぶ ami_dat.py・build.py は取り直さない（blender/src_lock.py）
lock="$("$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); import src_lock; print(src_lock.LOCK)' "$AMI/blender")"
[ -n "$lock" ] || { echo "blender/src_lock.py のロックの場所が分からない" >&2; exit 1; }
if [ "${AMI_SRC_LOCK:-}" != "$lock" ]; then
  exec "$PY" -X utf8 "$AMI/blender/src_lock.py" run check.sh -- "$BASH" "${BASH_SOURCE[0]}" "$@"  # bash の名前で呼ぶと、Windows では PATH の WSL の bash を拾う
fi

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

# dat の書き忘れ: ami_dat.py に一時のフォルダへ書かせて、src/（src256/）の dat と比べる。src/ の dat は消さない
# （以前は消して書き直してから戻していたので、ほかの ami_dat.py・build.py と重なったり途中で止めたりすると dat が消えた。#326）
dat_compare() {  # <src のフォルダ名> <SHEET_PAK_SIZE>
  local src="$AMI/$1" gen report n
  # if の条件の中で呼ぶので set -e が効かない。失敗は 2 で返す（1 は差分あり）
  gen="$(mktemp -d)" || return 2
  SHEET_PAK_SIZE="$2" "$PY" -X utf8 "$AMI/blender/ami_dat.py" --out "$gen" > /dev/null || { echo "blender/ami_dat.py が落ちた（SHEET_PAK_SIZE=$2）"; rm -rf "$gen"; return 2; }
  report="$gen.report.txt"
  : > "$report"
  for n in $( (cd "$gen" && ls *.dat; cd "$src" && ls *.dat) | sort -u ); do
    if [ ! -f "$src/$n" ]; then echo "生成されたが $1/ に無い: $n" >> "$report"
    elif [ ! -f "$gen/$n" ]; then echo "$1/ にあるが生成されない: $n" >> "$report"
    elif ! diff -q --strip-trailing-cr "$src/$n" "$gen/$n" > /dev/null; then
      echo "中身が違う: $n" >> "$report"
      diff --strip-trailing-cr "$src/$n" "$gen/$n" | head -20 >> "$report" || true
    fi
  done
  rm -rf "$gen"
  if [ -s "$report" ]; then cat "$report"; rm -f "$report"; return 1; fi
  rm -f "$report"
}

step "dat の書き忘れ（blender/ami_dat.py の出力と src/ の dat を比べる）"
rc=0; dat_compare src 128 || rc=$?
if [ "$rc" = 1 ]; then
  echo "${GITHUB_ACTIONS:+::error::}blender/ami_dat.py の出力と src/ の dat が違う。ami_dat.py を実行し、出た dat をコミットする"
  exit 1
elif [ "$rc" != 0 ]; then
  echo "${GITHUB_ACTIONS:+::error::}src/ の dat の書き忘れを確かめられなかった（ami_dat.py が落ちた）"
  exit 1
fi

step "256 の dat の書き忘れ（SHEET_PAK_SIZE=256 の blender/ami_dat.py の出力と src256/ の dat を比べる。#266）"
rc=0; dat_compare src256 256 || rc=$?
if [ "$rc" = 1 ]; then
  echo "${GITHUB_ACTIONS:+::error::}SHEET_PAK_SIZE=256 の blender/ami_dat.py の出力と src256/ の dat が違う。ami_dat.py を実行し、出た dat をコミットする"
  exit 1
elif [ "$rc" != 0 ]; then
  echo "${GITHUB_ACTIONS:+::error::}src256/ の dat の書き忘れを確かめられなかった（ami_dat.py が落ちた）"
  exit 1
fi

step "256 の dat の名前が pak128 と同じか、組まない物の表が実在するか（check_scaled.py。256 の PNG が無い CI でも見る。#261・#301）"
"$PY" -X utf8 "$AMI/check_scaled.py"

step "256 の持ち分マスクが pak256 の地面の形と画素で一致するか（tools/blender/check_ground_mask.py。Blender なし。#321）"
"$PY" -X utf8 "$ROOT/tools/blender/check_ground_mask.py"

step "アイコン・カーソルの参照先（セルの重なり・絵の有無・背景色・別のシートの絵・カーソルの offset・icons.py が書いた物か（*.icon_cells.txt と比べる。#330）。check_icons.py）"
"$PY" -X utf8 "$AMI/check_icons.py"

step "dat が指すセルが空（全部透明）でないか（check_cells.py。意図して空のものは check_cells.allow.txt。#241）"
"$PY" -X utf8 "$AMI/check_cells.py" --self-test
"$PY" -X utf8 "$AMI/check_cells.py"

step "踏切のシートが今の道路のシートから描かれているか（check_crossing.py）"
"$PY" -X utf8 "$AMI/check_crossing.py"

step "車庫・操車場の絵の大きさ（箱積み駅舎の箱 1 段に収まるか。check_depot.py）"
"$PY" -X utf8 "$AMI/check_depot.py"

step "物の一覧が全部の dat から作れるか、種類別の pak で全部を覆うか（lineup.py --check）"
"$PY" -X utf8 "$AMI/lineup.py" --check

step "配る readme の元に固定の版名が無いか（release.py --check。#345）"
"$PY" -X utf8 "$AMI/release.py" --self-test
"$PY" -X utf8 "$AMI/release.py" --check

step "盛土の絵の形と割り当て（向き・角・T字・十字・1 タイル・坂が期待のセルと形か。check_embankment.py）"
"$PY" -X utf8 "$AMI/check_embankment.py"

step "雪の基盤の版の下の端に路面の板の切り口が出ていないか（暗い列が通常の版より多くないか。check_snow_edge.py。#360・#366）"
"$PY" -X utf8 "$AMI/check_snow_edge.py" --self-test
"$PY" -X utf8 "$AMI/check_snow_edge.py"

# 256 のシート（src256/。SHEET_PAK_SIZE=256。#261）。256 の PNG は dat と生活道路だけをコミットする（全部は大きすぎる）ので、CI は絵のある物だけを見る
# （CHECK_SKIP_MISSING=1: シートの無い物は飛ばす）。全部のシートを描いた手元では CHECK_256_FULL=1 を付けて、全部を厳しく見る
# （絵の無い物があると落ちる。踏切・車庫・盛土のシートの検査も含む）
export SHEET_PAK_SIZE=256
if [ "${CHECK_256_FULL:-}" = "1" ]; then
  step "256 のシートの検査（全部。アイコン・カーソル・空のセル・踏切・車庫・盛土・雪の基盤の版の下の端。SHEET_PAK_SIZE=256。#261）"
  "$PY" -X utf8 "$AMI/check_icons.py"
  "$PY" -X utf8 "$AMI/check_cells.py"
  "$PY" -X utf8 "$AMI/check_crossing.py"
  "$PY" -X utf8 "$AMI/check_depot.py"
  "$PY" -X utf8 "$AMI/check_embankment.py"
  "$PY" -X utf8 "$AMI/check_snow_edge.py"
else
  step "256 のシートの検査（絵のある物だけ。アイコン・カーソル・空のセル・雪の基盤の版の下の端。SHEET_PAK_SIZE=256。#261）"
  CHECK_SKIP_MISSING=1 "$PY" -X utf8 "$AMI/check_icons.py"
  CHECK_SKIP_MISSING=1 "$PY" -X utf8 "$AMI/check_cells.py"
  CHECK_SKIP_MISSING=1 "$PY" -X utf8 "$AMI/check_snow_edge.py"
fi
unset SHEET_PAK_SIZE

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
if [ "${CHECK_256_FULL:-}" = "1" ]; then
  (cd "$AMI/src256" && dat_linter lint --tile-size 512 .)  # 256 の pak（#266）
else
  # 256 の PNG は生活道路だけをコミットする（#261）ので、絵のある dat だけを lint する（絵の無い dat は missing-image-file で落ちる）
  rm -rf "$AMI/work256/lint"
  (cd "$AMI" && SHEET_PAK_SIZE=256 "$PY" -X utf8 build.py --stage-sheeted work256/lint)
  (cd "$AMI/work256/lint" && dat_linter lint --tile-size 512 .)
fi

step "dat の静かな誤り（行末の # 注記・数値でない値・行頭の空白・知らない obj・way の絵の綴りと坂。dat_lint_extra.py）"
"$PY" -X utf8 "$ROOT/tools/dat_lint_extra/dat_lint_extra.py" --self-test
"$PY" -X utf8 "$ROOT/tools/dat_lint_extra/dat_lint_extra.py" "$AMI/src"
"$PY" -X utf8 "$ROOT/tools/dat_lint_extra/dat_lint_extra.py" "$AMI/src256"  # 256 の dat（#266）

if [ -n "${SKIP_BUILD:-}" ]; then
  step "pak のビルドは飛ばした（SKIP_BUILD）"
else
  step "pak を作る"
  { makeobj || true; } | head -1
  (cd "$AMI" && "$PY" -X utf8 build.py)
  step "256 の pak を作る（SHEET_PAK_SIZE=256。makeobj pak512。警告があれば止まる。#266。256 の PNG は dat と生活道路だけなので、CHECK_256_FULL=1 が無いときは BUILD_SKIP_MISSING=1 で絵のある物だけを組む。#261）"
  if [ "${CHECK_256_FULL:-}" = "1" ]; then
    (cd "$AMI" && SHEET_PAK_SIZE=256 "$PY" -X utf8 build.py)
  else
    (cd "$AMI" && SHEET_PAK_SIZE=256 BUILD_SKIP_MISSING=1 "$PY" -X utf8 build.py)
  fi
fi

if [ -n "${SKIP_BUILD:-}" ]; then
  :
else
  step "画面を出さない本体で配る pak を読む（tools/ci/check_pak_load.py。#236）"
  sim="${HEADLESS_SIM_BIN:-}"; pakset="${HEADLESS_PAKSET:-}"
  if [ -n "$sim" ] && [ -z "$pakset" ]; then
    echo "HEADLESS_SIM_BIN だけで HEADLESS_PAKSET が無い（本体の tests/simutrans-test-base.zip を渡す）" >&2
    exit 1
  fi
  if [ -z "$sim" ]; then
    case "$(uname -s)" in
      MINGW*|MSYS*|CYGWIN*) ;;
      *)
        hdir="$TOOLS_DIR/headless-sim/${HEADLESS_SIM//[:\/]/_}"
        bash "$ROOT/tools/ci/setup-headless-sim.sh" "$HEADLESS_SIM" "$hdir"
        sim="$hdir/sim"; pakset="$hdir/simutrans-test-base.zip" ;;
    esac
  fi
  if [ -z "$sim" ]; then
    SKIPPED_HEADLESS=1
    echo "飛ばした（Windows の手元で HEADLESS_SIM_BIN・HEADLESS_PAKSET が無い。addons/ami/README.md の「画面を出さない本体での読み込みの検査」）"
  else
    # 種類別の pak は全部一緒に、全部入りの ami.pak は単独で読む（一緒に置くと名前が重複する）
    kinds=(); for f in "$AMI"/dist/ami_*.pak; do kinds+=("$f"); done
    # --makeobj: 本体に登録された名前（way・橋・トンネル・架線・標識・建物）を makeobj list の名前と比べる（#245）
    pl=("$PY" -X utf8 "$ROOT/tools/ci/check_pak_load.py" --sim "$sim" --pakset "$pakset" --makeobj makeobj)
    "${pl[@]}" "${kinds[@]}"
    "${pl[@]}" "$AMI/dist/ami.pak"
    # 壊した pak（空・ROOT の大きさ・参照切れ・名前の重複・登録されない物・半分で切れた pak・余る物）で失敗することの確かめ（XREF を持つ種類別の pak から作る）
    "${pl[@]}" --self-test "$AMI/dist/ami_monorail.pak"
  fi
fi

[ -n "${GITHUB_ACTIONS:-}" ] && echo "::endgroup::"
echo "== AMI の検査はすべて通った${SKIPPED_HEADLESS:+（画面を出さない本体での pak の読み込みは飛ばした）}"
