#!/bin/bash
# 基盤・高架の面の描き込みの段（#78。blender/surface_calib.py）の見本（ingame/surface_sample.nut）を敷いて撮る。
# 使い方（アドオンのディレクトリで。先に python -X utf8 build.py で dist/ami.pak、python -X utf8 blender/surface_calib.py で
# rounds/ami_surface_calib.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=47400 bash ingame/surface_capture.sh
# ゲームは work/calib_game/<PORT>/ の写し（calib_capture.sh と同じ作り）で起動し、撮り終えたら閉じて写しも消す。GAME_DIR には書き込まない。
# 画像は OUT（既定 work/surface/shots）に <気候>_<区画>_surf<段>.png。区画は G（地上の基盤の版。3 線と 1 本）・V（高架の版）、
# GD・VD は同じ区画の斜めの 1 本の辺り。拡大率は ZOOM（既定 3 = 等倍）
GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PORT=${PORT:?PORT を指定する}
OUT=${OUT:-work/surface/shots}
ZOOM=${ZOOM:-3}
STEPS=${STEPS:-"0 1 2 3 j"}   # surface_sample.nut の STEPS と同じ並び
DX=26
VY=14
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port $PORT"
PAKS=${PAKS:-"dist/ami.pak rounds/ami_surface_calib.pak"}
NUT=ingame/surface_sample.nut
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
