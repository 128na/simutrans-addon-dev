#!/bin/bash
# 配る pak の読み込みの確認（#91）: 配る zip と同じ種類別の pak だけを入れたゲームを起動し、ingame/beta_check.nut で全部の物を 1 つずつ道具で敷く。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47400 bash ingame/beta_check.sh
# ゲームは work/beta_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）で起動し、GAME_DIR には書き込まない。
# 写しからは AMI の古い pak（addons/pak128/ami*.pak）を外し、PAKS（既定は build.py の KINDS の種類別の pak 全部から旧描画位置の 1 本を除いたもの）を入れる。
# 敷く物は src/*.dat のうち PAKS に入る物（build.py の belongs）の obj・name・waytype・system_type から作る（提供用の ex_donors.dat は除く）。
# 旧描画位置の物（#26）は新と同じ橋・高架に載る way が混ざる（ADR 0011）ので、既定には入れず PAKS=dist/ami_rail_old.pak で別に確かめる。終わったらゲームを閉じて写しを消す。
# 出力: 敷いた結果（先頭が ok なら全部敷けた）と、ゲームのログ（-log 1 -debug 3 の simu.log。work/beta_game/simu_<PORT>.log に残す）のうち、
# 読んだ AMI の pak と、AMI の物の名前を含む警告・エラーの行（同じ物を二重に読むと「object way::<名前> is overlaid!」が出る）。
# 全部敷けて警告が無ければ 0、どちらかが外れたら 1 で終わる
PORT=${PORT:?PORT に MCP のポートを指定する}
# 既定の PAKS は build.py の KINDS の全部（旧描画位置の ami_rail_old.pak を除く）。ラインナップが増えても build.py に追従する（#177）
PAKS=${PAKS:-$(python -X utf8 -c "
import sys
sys.path.insert(0, '.')
import build
print(' '.join('dist/' + k for k in build.KINDS if k != build.OLD_PAK))
")}
NUT=ingame/beta_check.nut
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/beta_game/$PORT"
[ -n "$PAKS" ] || { echo "[beta] PAKS が空（既定の組み立てに失敗した）"; exit 1; }
for p in $PAKS; do [ -f "$p" ] || { echo "[beta] $p が無い"; exit 1; }; done
trap game_cleanup EXIT
trap 'exit 130' INT TERM
GAME_TAG=beta
GAME_ARGS="${GAME_ARGS:-} -log 1 -debug 3"  # 警告と読み込みの行まで simu.log に出す
game_start $PAKS || exit 1
sleep 3

# 敷く物の一覧: [名前, obj, waytype, system_type, type, own_waytype]。PAKS の pak に入る物だけ（build.py の belongs。旧描画位置の物は ami_rail_old.pak だけに入る。#26）
KEEP=" $(python -X utf8 -c "
import os, sys
sys.path.insert(0, '.')
import build
paks = [os.path.basename(p) for p in sys.argv[1:]]
for f in sorted(os.listdir('src')):
    if f.endswith('.dat') and f != 'ex_donors.dat' and any(build.belongs(p, f[:-4]) for p in paks):
        print(f[:-4], end=' ')
" $PAKS)"
ITEMS=$(for f in src/*.dat; do
  case $f in *ex_donors.dat) continue ;; esac
  case $KEEP in *" $(basename "$f" .dat) "*) ;; *) continue ;; esac
  awk -F= 'tolower($1)=="obj"{o=$2} tolower($1)=="name"{n=$2} tolower($1)=="waytype"{w=$2} tolower($1)=="system_type"{s=$2} tolower($1)=="type"{t=$2} tolower($1)=="own_waytype"{ow=$2}
    END{gsub(/\r/,"",o); gsub(/\r/,"",n); gsub(/\r/,"",w); gsub(/\r/,"",s); gsub(/\r/,"",t); gsub(/\r/,"",ow); if (s=="") s=0; printf "[\"%s\",\"%s\",\"%s\",%s,\"%s\",\"%s\"],", n, o, w, s, t, ow}' "$f"
done | sed 's/,$//')
SQ=$(sed -e '/^[[:space:]]*\/\//d' -e '/^[[:space:]]*$/d' -e "s/^local ITEMS = .*/local ITEMS = [$ITEMS];/" "$NUT")
RESULT=$(python -X utf8 -c "import json,sys; print(json.load(sys.stdin).get('result'))" <<< "$($M --timeout 300 --run-squirrel "$SQ")")
echo "$RESULT"
fail=0
[ "${RESULT#ok }" != "$RESULT" ] || fail=1
# ログ（-debug 3 で警告と読み込みの行まで出す。段を下げると 1 行しか出ず、二重に読んだ物の overlaid の警告も出ない）
LOG="work/beta_game/simu_$PORT.log"
[ -f "$WORK/simu.log" ] && cp "$WORK/simu.log" "$LOG"  # 写しを消した後も読めるように
# 踏切は名前が script から読めず、pak128 の踏切でも通るので、ログの登録の行（crossing_logic_t::register_desc）で AMI の踏切が全部読まれたかを見る（#177）
if [ -f "$LOG" ]; then
  for n in $(grep -o '"ami_crossing_[a-z_]*"' <<< "$ITEMS" | tr -d '"'); do
    grep -aq "register_desc():.$n\$" "$LOG" || { echo "[beta] 踏切 $n がログに登録されていない"; fail=1; }
  done
fi
if [ -f "$LOG" ] && grep -aq "obj_reader_t::read_file" "$LOG"; then
  echo "[beta] 読んだ AMI の pak: $(grep -aoE "addons/pak128/ami[a-z_]*\.pak" "$LOG" | sort -u | tr '\n' ' ')"
  echo "[beta] ログの警告・エラー（AMI の物の名前 ami_ を含む行。全体は $LOG）:"
  if grep -aiE "warning|error" "$LOG" | grep -aE "ami_"; then fail=1; else echo "  なし"; fi
else
  echo "[beta] ログに pak の読み込みの行が無い（ログを読めなかった。$LOG）"
  fail=1
fi
exit $fail  # 敷けない物か、AMI の物の警告があれば 1（trap でゲームを閉じる）
