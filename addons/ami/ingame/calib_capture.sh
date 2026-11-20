#!/bin/bash
# くどさの物差しを合わせる見本（ingame/calib.nut）を撮る（#56 の C）。
# 敷く前の地面と敷いた後を、同じ場所・同じ拡大率で撮る（差から way の画素だけを選ぶため。tools/blender/busy_measure.py）。
# 使い方（アドオンのディレクトリで。python -X utf8 blender/calib.py で work/calib/ami_calib.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=47125 bash ingame/calib_capture.sh
# ゲームは work/calib_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に PAKS を足して起動し、
# 撮り終えたら閉じて写しも消す。GAME_DIR には書き込まない（同時に別のセッションが撮っても取り合わない。ポートは PORT で分ける）。
# NUT（既定 ingame/calib.nut）で敷く見本を替えられる（WAYS の行を WAYS_NUT で置き換える）。
# 画像は OUT（既定 work/calib/shots）に <気候>_<段の名前>_z<拡大率>_<bare|way>.png で置く
GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PORT=${PORT:-47125}
OUT=${OUT:-work/calib/shots}
ZOOMS=${ZOOMS:-"3 4 6"}   # 3 が等倍、4 が 3/4、6 が 1/2（本体 display/simgraph16.cc の zoom_num・zoom_den）
source "$(dirname "$0")/mcp_client.sh"   # MCP_CLIENT の既定（リポジトリの隣の simutrans/）
M="python $MCP_CLIENT --port $PORT"
# 並べる way（calib.nut の WAYS）と、画像の名前に使う短い名前。手本の way は GAME_DIR に入っているもの（既定は pak128 本体の在来線と SIS の新幹線の線路）。WAYS_NUT を渡すと、その way を並べる（ラウンドの比べ: #56）
WAYS_NUT=${WAYS_NUT:-"ami_rail_ballast_calib0 ami_rail_ballast_calib1 ami_rail_ballast_calib2 ami_rail_ballast_calib3 ami_rail_ballast_calib4 Rail_160_Tracks SIS_ST_TGbl_E01-999S"}
WAYS=""
for w in $WAYS_NUT; do
  case $w in
    Rail_160_Tracks) WAYS="$WAYS pak128" ;; iss_wtg_0240_single) WAYS="$WAYS iss" ;; SIS_ST_TGbl_E01-999S) WAYS="$WAYS sis" ;;
    ami_rail_ballast_*) WAYS="$WAYS ${w#ami_rail_ballast_}" ;; *) WAYS="$WAYS ${w#ami_}" ;;
  esac
done
PAKS=${PAKS:-work/calib/ami_calib.pak}   # GAME_DIR/addons/pak128/ に入れる pak（空白区切り）
DX=16

NUT=${NUT:-ingame/calib.nut}
WORK="work/calib_game/$PORT"

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[calib] ポート $PORT で既にゲームが動いている"; exit 1; }
# 写しの中の exe で動いているものだけを止める
stop_game() {
  powershell.exe -NoProfile -Command "\$d = '$WORK_WIN'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}
rm -rf "$WORK"
mkdir -p "$WORK/save"
WORK_WIN=$(cd "$WORK" && pwd -W)
trap stop_game EXIT
trap 'exit 130' INT TERM
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$WORK/" || exit 1
for d in config font themes text script music pak128 addons; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$WORK/" || exit 1; }
done
cp "$GAME_DIR/save/$SAVE.sve" "$WORK/save/" || exit 1
[ -f "$GAME_DIR/settings.xml" ] && { cp "$GAME_DIR/settings.xml" "$WORK/settings.xml"; chmod u+w "$WORK/settings.xml"; }
for p in $PAKS; do cp "$p" "$WORK/addons/pak128/$(basename "$p")" || exit 1; done
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
mkdir -p "$OUT"

shoot() {  # $1 = bare|way
  for season in temperate:20:20 snow:276:20; do
    IFS=: read s ox oy <<< "$season"
    i=0
    for w in $WAYS; do
      for z in $ZOOMS; do
        $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($z); gui.jump(coord3d($((ox + i * DX + 5)),$((oy + 5)),0)); return 1;" > /dev/null 2>&1
        sleep 1
        $M --capture "$OUT/${s}_${w}_z${z}_$1.png" > /dev/null 2>&1 || echo "[calib] 撮れなかった: ${s}_${w}_z${z}_$1"
      done
      i=$((i + 1))
    done
  done
}

shoot bare
WAYS_SQ="[$(printf '"%s",' $WAYS_NUT | sed 's/,$//')]"
echo "[calib] $($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' -e "s/^local WAYS = .*/local WAYS = $WAYS_SQ;/" "$NUT")" --timeout 300)"
shoot way
echo "[calib] $OUT に撮った（ゲームは閉じ、写しは消す）"
