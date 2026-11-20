#!/bin/bash
# 分岐の追加画像の見本（ingame/ex_sample.nut を ingame/ex_check.sh で敷いたゲーム）を撮る。区画ごとに Y字分岐・三方分岐の 8 か所へ移って撮り、OUT に置く。
# 使い方（アドオンのディレクトリで、ゲームを開いたまま）: PORT=47300 OUT=work/ex/after bash ingame/ex_capture.sh
#   BLOCKS で撮る区画の番号（ex_sample.nut の WAYS の順、0 から）を絞れる（例: BLOCKS="0 4"）。既定は 0〜7
# 画像の名前: <気候>_<区画の番号>_<Y か 3W><根元の向き>.png。場所は ex_sample.nut の冒頭の表（区画の原点は (OX, OY + 番号 * SPACING)、降雪は x + 256）
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port ${PORT:?PORT を指定する}"
OUT=${OUT:-work/ex/capture}
ZOOM=${ZOOM:-3}
OX=150; OY=20; SPACING=40
BLOCKS=${BLOCKS:-0 1 2 3 4 5 6 7}
mkdir -p "$OUT"
for season in temperate:0 snow:256; do
  IFS=: read s dx <<< "$season"
  for b in $BLOCKS; do
    for k in 0 1 2 3; do
      d=$(echo E W N S | cut -d' ' -f$((k + 1)))
      for row in 0 1; do
        kind=$([ $row = 0 ] && echo Y || echo 3W)
        x=$((OX + dx + 4 + 10 * k)); y=$((OY + b * SPACING + 4 + 10 * row))
        $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($x,$y,0)); return 1;" > /dev/null 2>&1
        sleep 1
        $M --capture "$OUT/${s}_${b}_${kind}${d}.png" > /dev/null 2>&1 && echo "[capture] $OUT/${s}_${b}_${kind}${d}.png"
      done
    done
  done
done
