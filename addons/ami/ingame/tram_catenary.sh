#!/bin/bash
# 路面軌道の架線の見本（#376）。ingame/tram_catenary.nut を流す。
# ゲームは work/tram_cat_game/<PORT>/ の写しで起動し、GAME_DIR には書き込まない。敷いた後はゲームを開いたままにする。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47320 bash ingame/tram_catenary.sh   … 起動して敷く
#   PORT=47320 CAPTURE=1 OUT=work/tram_cat/shots bash ingame/tram_catenary.sh   … 撮る（区画ごと。電車は 1 回だけ出す）
#   PORT=47320 TOOLBAR=1 OUT=work/tram_cat/shots bash ingame/tram_catenary.sh   … 線路・路面軌道の道具の窓を撮る（架線がどこに並ぶか）
#   PORT=47320 STOP=1 bash ingame/tram_catenary.sh                              … 閉じて写しを消す
# PAK で AMI の pak を替えられる
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/tram_cat_game/$PORT"
OUT=${OUT:-work/tram_cat/shots}
if [ "$STOP" = 1 ]; then game_stop; echo "[tram_cat] stopped"; exit 0; fi

sq() { $M --run-squirrel "$1" > /dev/null 2>&1; }
shot() {  # shot <x> <y> <名前>
  sq "gui.close_all_windows(); gui.set_zoom(${ZOOM:-3}); gui.jump(coord3d($1,$2,0)); return 1;"
  sleep 1
  $M --capture "$OUT/$3.png" > /dev/null 2>&1 && echo "[capture] $OUT/$3.png"
}

if [ "$CAPTURE" = 1 ]; then
  mkdir -p "$OUT"
  # tram_catenary.nut の OX・OY・SPACING と区画の場所に合わせる
  for g in road:20 ground:46; do
    n=${g%:*}; oy=${g#*:}
    shot 23 $((oy + 2)) "${n}_a"
    shot 31 $((oy + 2)) "${n}_diag"
    shot 23 $((oy + 8)) "${n}_loop"
    shot 31 $((oy + 8)) "${n}_hill"
    shot 24 $((oy + 15)) "${n}_double"
    shot 26 $((oy + 18)) "${n}_depot"
  done
  # 電車: 車庫（西の端）から出して、続けて撮る
  sq "local d = depot_x(20, 38, 0); local l = d.get_convoy_list(); if (l.len() > 0) d.start_convoy(player_x(0), l[0]); return 1;"
  for i in $(seq 1 ${SHOTS:-6}); do
    shot 25 38 "train_$i"
    sleep 1
  done
  $M --run-squirrel "local o = \"\"; foreach (c in convoy_list_x()) o += c.get_name() + \" pos=\" + c.get_pos().tostring() + \" speed=\" + c.get_speed() + \"; \"; return o;"
  exit 0
fi

if [ "$TOOLBAR" = 1 ]; then
  mkdir -p "$OUT"
  # 上の道具の列の x は icon_capture.sh の MENUS と同じ
  for e in rail:145 tram:240; do
    sq "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(24, 24, 0)); return 1;"
    sleep 1
    sq "gui.click(${e##*:}, 15); return 1;"
    sleep 1
    $M --capture "$OUT/menu_${e%%:*}.png" > /dev/null 2>&1 && echo "[capture] $OUT/menu_${e%%:*}.png"
  done
  exit 0
fi

PAK=${PAK:-dist/ami.pak}
GAME_TAG=tram_cat
game_start "$PAK=ami.pak" || exit 1
$M --run-squirrel "$(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "${NUT:-ingame/tram_catenary.nut}")" --timeout 300
