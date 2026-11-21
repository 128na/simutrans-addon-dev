#!/bin/bash
# 複線の直角のカーブで、角のタイルの版の敷き方を比べる検討用の見本（#94）。ingame/curve_base_study.nut を流す。
# 起動・終了は ingame/curve_switch_study.sh（work/study_game/<PORT>/ の写しに AMI と iss の線路の pak を足して起動する）に任せる。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=47200 bash ingame/curve_base_study.sh   … 起動して敷き、[check] の行を出す
#   PORT=47200 CAPTURE=1 OUT=work/curve94/shots bash ingame/curve_base_study.sh                 … 輪の角ごとに撮る（<組>_<敷き方>_<角>.png）
#   PORT=47200 STOP=1 bash ingame/curve_base_study.sh                                          … 閉じて写しを消す
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port $PORT"
OX=150; OY=20; LDX=12; SDY=12
SETS="iss ami ami+wall ami+cat"
LAYOUTS="N R X"

if [ "$STOP" = 1 ]; then PORT=$PORT STOP=1 bash "$(dirname "$0")/curve_switch_study.sh"; exit $?; fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/curve94/shots}
  ZOOM=${ZOOM:-3}
  mkdir -p "$OUT"
  si=0
  for s in $SETS; do
    li=0
    for l in $LAYOUTS; do
      # 輪の 4 つの角（画面で上・右・下・左）を、外の角のタイルへ飛んで撮る（等倍では輪の全体が画面に入らない）
      for spot in top:0:0 right:6:0 bottom:6:6 left:0:6; do
        IFS=: read name dx dy <<< "$spot"
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

GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する} EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）} \
  PORT=$PORT NUT=ingame/curve_base_study.nut bash "$(dirname "$0")/curve_switch_study.sh"
