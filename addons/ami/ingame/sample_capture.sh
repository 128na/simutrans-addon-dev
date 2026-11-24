#!/bin/bash
# AMI の見本（ingame/sample.nut）を撮る: 温暖側と降雪側の区画ごとに、決めた場所へ移って画面を撮り、work/sample/ に置く。
# 使い方（アドオンのディレクトリで、ingame/sample_check.sh で見本を敷いたゲームを開いたまま）:
#   bash ingame/sample_capture.sh            # OUT=work/sample。レイアウト検証用モードの pak なら OUT=work/sample_layout
# 撮るのは 1 本目の way（WAYS の先頭）の区画と、基盤の版と壁の区画（sample.nut の WALLED。SPACING = 30 ずつ南）と区画 W、
# 架線つきの壁の区画（CATENARY）と区画 WE、高架の区画（ELEVATED・WV・WVE・J）。一部だけ撮るときは SPOTS="名前:x:y ..." を渡す。
# 場所の意味は sample.nut の冒頭の表。画像は目で見る（絵の欠け・縦線・段・すき間）
source "$(dirname "$0")/mcp_client.sh"   # MCP_CLIENT の既定（リポジトリの隣の simutrans/）
M="python $MCP_CLIENT --port ${PORT:?PORT に MCP のポートを指定する}"
OUT=${OUT:-work/sample}
ZOOM=${ZOOM:-3}
source "$(dirname "$0")/sample_spots.sh"
mkdir -p "$OUT"
for season in temperate:20:20 snow:276:20; do
  IFS=: read s ox oy <<< "$season"
  for spot in $SPOTS; do
    IFS=: read k x y <<< "$spot"
    $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($((ox + x)),$((oy + y)),0)); return 1;" > /dev/null 2>&1
    sleep 1
    $M --capture "$OUT/${s}_$k.png" > /dev/null 2>&1 && echo "[capture] $OUT/${s}_$k.png"
  done
done
