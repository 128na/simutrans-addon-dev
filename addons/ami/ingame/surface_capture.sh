#!/bin/bash
# 基盤・高架の面の描き込みの段（#78。blender/surface_calib.py）の見本（ingame/surface_sample.nut）を敷いて撮る。
# 使い方（アドオンのディレクトリで。先に python -X utf8 build.py で dist/ami.pak、python -X utf8 blender/surface_calib.py で
# rounds/ami_surface_calib.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47400 bash ingame/surface_capture.sh
# ゲームは work/calib_game/<PORT>/ の写し（calib_capture.sh と同じ作り）で起動し、撮り終えたら閉じて写しも消す。GAME_DIR には書き込まない。
# 画像は OUT（既定 work/surface/shots）に <気候>_<区画>_surf<段>.png。区画は G（地上の基盤の版。3 線と 1 本）・V（高架の版）、
# GD・VD は同じ区画の斜めの 1 本の辺り。拡大率は ZOOM（既定 3 = 等倍）
PORT=${PORT:?PORT を指定する}
OUT=${OUT:-work/surface/shots}
ZOOM=${ZOOM:-3}
STEPS=${STEPS:-"0 1 2 3 j"}   # surface_sample.nut の STEPS と同じ並び
DX=26
VY=14
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
PAKS=${PAKS:-"dist/ami.pak rounds/ami_surface_calib.pak"}
NUT=ingame/surface_sample.nut
WORK="work/calib_game/$PORT"

trap game_cleanup EXIT
trap 'exit 130' INT TERM
GAME_TAG=calib
game_start $PAKS || exit 1
mkdir -p "$OUT"
echo "[surface] $($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$NUT")" --timeout 300)"
for season in temperate:20:20 snow:276:20; do
  IFS=: read s ox oy <<< "$season"
  i=0
  for st in $STEPS; do
    for spot in G:10:4 V:10:$((VY + 4)) GD:19:2 VD:19:$((VY + 2)); do
      IFS=: read k dx dy <<< "$spot"
      $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($((ox + i * DX + dx)),$((oy + dy)),0)); return 1;" > /dev/null 2>&1
      sleep 1
      $M --capture "$OUT/${s}_${k}_surf${st}.png" > /dev/null 2>&1 || echo "[surface] 撮れなかった: ${s}_${k}_surf${st}"
    done
    i=$((i + 1))
  done
done
echo "[surface] $OUT に撮った（ゲームは閉じ、写しは消す）"
