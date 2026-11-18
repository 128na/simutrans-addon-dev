#!/bin/bash
# AMI の見本（ingame/sample.nut）を撮る: 温暖側と降雪側の区画ごとに、決めた場所へ移って画面を撮り、work/sample/ に置く。
# 使い方（アドオンのディレクトリで、ingame/sample_check.sh で見本を敷いたゲームを開いたまま）:
#   bash ingame/sample_capture.sh            # OUT=work/sample。レイアウト検証用モードの pak なら OUT=work/sample_layout
# 撮るのは 1 本目の way（WAYS の先頭）の区画と、基盤の版と壁の区画（sample.nut の WALLED。SPACING = 30 ずつ南）と区画 W、
# 架線つきの壁の区画（CATENARY）と区画 WE。一部だけ撮るときは SPOTS="名前:x:y ..." を渡す。
# 場所の意味は sample.nut の冒頭の表。画像は目で見る（絵の欠け・縦線・段・すき間）
M="python ${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py} --port ${PORT:-47123}"
OUT=${OUT:-work/sample}
ZOOM=${ZOOM:-3}
# 名前:区画の原点からの x:y（sample.nut の区画）
#   H0〜H7 は分岐の自動選択の 8 通り（nse2・nse1・nsw2・nsw1・new2・new1・sew2・sew1 の順。sample.nut の AUTO）
#   S・B・C・F は基盤の版の single・back・center・front の区画（AFC・B・DE と、分岐 H0）。W1〜W3 は区画 W（y=150〜）
WALLED_SPOTS=""
for v in S:30 B:60 C:90 F:120; do
  IFS=: read n dy <<< "$v"
  WALLED_SPOTS="$WALLED_SPOTS ${n}_AFC:8:$((2 + dy)) ${n}_B:3:$((7 + dy)) ${n}_DE:14:$((7 + dy)) ${n}_H0:3:$((22 + dy))"
done
# 架線つきの壁（sample.nut の CATENARY）: SE・BE・CE・FE は single・back・center・front の区画（y=180〜）、WE1〜WE3 は区画 WE（y=300〜）
for v in SE:180 BE:210 CE:240 FE:270; do
  IFS=: read n dy <<< "$v"
  WALLED_SPOTS="$WALLED_SPOTS ${n}_AFC:8:$((2 + dy)) ${n}_B:3:$((7 + dy)) ${n}_DE:14:$((7 + dy)) ${n}_H0:3:$((22 + dy))"
done
SPOTS=${SPOTS:-"AFC:8:2 B:3:7 DE:14:7 G1:25:3 G2:25:15 I:5:14 H0:3:22 H1:11:22 H2:19:22 H3:27:22 H4:35:22 H5:43:22 H6:51:22 H7:59:22$WALLED_SPOTS W1:6:155 W2a:19:153 W2b:19:163 W3:2:163 WE1:6:305 WE2a:19:303 WE2b:19:313 WE3:2:313"}
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
