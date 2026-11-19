#!/bin/bash
# くどさの物差しを合わせる見本（ingame/calib.nut）を撮る（#56 の C）。
# 敷く前の地面と敷いた後を、同じ場所・同じ拡大率で撮る（差から way の画素だけを選ぶため。tools/blender/busy_measure.py）。
# 使い方（アドオンのディレクトリで。python -X utf8 blender/calib.py で work/calib/ami_calib.pak を作っておく）:
#   GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe PORT=47125 bash ingame/calib_capture.sh
# ami_calib.pak を GAME_DIR/addons/pak128/ に入れて起動し、撮った後にゲームを閉じて ami_calib.pak を消す。
# 画像は OUT（既定 work/calib/shots）に <気候>_<段の名前>_z<拡大率>_<bare|way>.png で置く
GAME_DIR=${GAME_DIR:?GAME_DIR を指定する（例: F:/Simutrans/addon_check）}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PORT=${PORT:-47125}
OUT=${OUT:-work/calib/shots}
ZOOMS=${ZOOMS:-"3 4 6"}   # 3 が等倍、4 が 3/4、6 が 1/2（本体 display/simgraph16.cc の zoom_num・zoom_den）
M="python ${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py} --port $PORT"
WAYS="calib0 calib1 calib2 calib3 calib4 pak128 iss"   # calib.nut の WAYS と同じ順
DX=16

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[calib] ポート $PORT で既にゲームが動いている"; exit 1; }
cp work/calib/ami_calib.pak "$GAME_DIR/addons/pak128/ami_calib.pak" || exit 1
(cd "$GAME_DIR" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
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
echo "[calib] $($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ingame/calib.nut)" --timeout 300)"
shoot way
echo "[calib] $OUT に撮った。ゲームを閉じてから GAME_DIR/addons/pak128/ami_calib.pak を消す"
