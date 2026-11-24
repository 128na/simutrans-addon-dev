#!/bin/bash
# 複線の直角のカーブで、角のタイルの版の敷き方を比べる検討用の見本（#94）。ingame/curve_base_study.nut を流す。
# 起動・終了は ingame/curve_switch_study.sh（work/study_game/<PORT>/ の写しに AMI と iss の線路の pak を足して起動する）に任せる。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47200 bash ingame/curve_base_study.sh > work/curve94/launch.log
#                                                       … 起動して敷き、[check] の行を出す（出力は管に通さずファイルへ。
#                                                         ゲームを起動した子のシェルが管を持ったままになり、ゲームを閉じるまで終わらない）
#   PORT=47200 CAPTURE=1 OUT=work/curve94/shots bash ingame/curve_base_study.sh  … 輪の角ごとに撮る（<組>_<敷き方>_<角>.png）
#   COMPOSE=1 OUT=work/curve94/shots bash ingame/curve_base_study.sh             … 撮った画面を角ごとの格子（<OUT>/../grid_<角>.png）に並べる
#   PORT=47200 STOP=1 bash ingame/curve_base_study.sh                           … 閉じて写しを消す
# SETS・LAYOUTS の名前と順は curve_base_study.nut の SETS・LAYOUTS と合わせる
SETS="iss ami ami+wall ami+cat"
LAYOUTS="N R X"
CORNERS="top:0:0 right:6:0 bottom:6:6 left:0:6"
OX=150; OY=20; LDX=12; SDY=12

if [ "$COMPOSE" = 1 ]; then
  # 格子は行が SETS の順、列が LAYOUTS の順。画面（704x536）の上のツールバーと下の状態行を切る
  OUT=${OUT:-work/curve94/shots}
  BLENDER=${BLENDER:-blender}
  for spot in $CORNERS; do
    name=${spot%%:*}
    files=()
    for s in $SETS; do for l in $LAYOUTS; do files+=("$OUT/${s/+/_}_${l}_${name}.png"); done; done
    "$BLENDER" -b --factory-startup --python ../../tools/blender/grid.py -- "$OUT/../grid_$name.png" 0,40,704,536 3 "${files[@]}" > /dev/null 2>&1 \
      && echo "[compose] $OUT/../grid_$name.png"
  done
  # R の壁の角を 4 倍に。左から 右の角の外・内、左の角の外・内（点は CAPTURE の画面での角のタイルの位置。紫の点が中心）
  "$BLENDER" -b --factory-startup --python ../../tools/blender/zoom.py -- "$OUT/ami_wall_R_right.png" "$OUT/../zoom_right.png" 60 4 281,352 156,342 > /dev/null 2>&1
  "$BLENDER" -b --factory-startup --python ../../tools/blender/zoom.py -- "$OUT/ami_wall_R_left.png" "$OUT/../zoom_left.png" 60 4 326,360 456,360 > /dev/null 2>&1
  "$BLENDER" -b --factory-startup --python ../../tools/blender/hcat.py -- "$OUT/../wall_zoom.png" "$OUT/../zoom_right.png" "$OUT/../zoom_left.png" > /dev/null 2>&1 \
    && echo "[compose] $OUT/../wall_zoom.png"
  exit 0
fi

PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port $PORT"

if [ "$STOP" = 1 ]; then PORT=$PORT STOP=1 bash "$(dirname "$0")/curve_switch_study.sh"; exit $?; fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/curve94/shots}
  ZOOM=${ZOOM:-3}
  mkdir -p "$OUT"
  si=0
  for s in $SETS; do
    li=0
    for l in $LAYOUTS; do
      # 輪の 4 つの角（画面で上・右・下・左）の外の角のタイルへ飛んで撮る。飛んだ先は画面の中心に来ず、角によって位置が違う
      # （下の角へ飛んだ画面には輪のほぼ全体が入る）。マウスの下のタイルの強調も写る
      for spot in $CORNERS; do
        IFS=: read -r name dx dy <<< "$spot"
        x=$((OX + li * LDX + dx)); y=$((OY + si * SDY + dy))
        $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($x,$y,0)); return 1;" > /dev/null 2>&1
        sleep 1
        f="$OUT/${s/+/_}_${l}_${name}.png"
        $M --capture "$f" > /dev/null 2>&1 && echo "[capture] $f ($x,$y)"
      done
      li=$((li + 1))
    done
    si=$((si + 1))
  done
  exit 0
fi

GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する} \
  PORT=$PORT NUT=ingame/curve_base_study.nut bash "$(dirname "$0")/curve_switch_study.sh"
