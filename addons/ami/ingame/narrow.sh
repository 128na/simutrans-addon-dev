#!/bin/bash
# 狭軌の見本（#370）。ingame/narrow.nut を流す。作りは monorail.sh と同じ。
# ゲームは work/narrow_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に AMI の pak を足して起動する。
# GAME_DIR には書き込まない。EXTRA_PAKS（空白区切り）の pak は写しの addons/pak128/ にだけ入れる（動作の確かめに使う狭軌の車両。
# pak128 には狭軌の車両が無い。リポジトリにも GAME_DIR にも置かない）。敷いた後はゲームを開いたままにする（撮るのは CAPTURE=1）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47320 EXTRA_PAKS="a.pak" bash ingame/narrow.sh  … 起動して敷く
#   PORT=47320 SNOW=1 bash ingame/narrow.sh                         … 動いているゲームの降雪側（x+256）に同じ見本を敷く
#   PORT=47320 CAPTURE=1 OUT=work/narrow/shots bash ingame/narrow.sh  … 区画ごとに撮る（SNOW=1 を足すと降雪側。名前の先頭に snow_）
#   PORT=47320 STOP=1 bash ingame/narrow.sh                         … 閉じて写しを消す
# ZOOM は gui.set_zoom の値（3 が等倍）
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/narrow_game/$PORT"
OX=20; OY=20
[ "$SNOW" = 1 ] && OX=$((OX + 256))
NUT_SED="s/^local OX = 20;/local OX = $OX;/"
PRE=""; [ "$SNOW" = 1 ] && PRE="snow_"
# 撮る所: 名前 x y（narrow.nut の区画の原点からのずれ）
SPOTS="wood_loop 7 5
wood_diag 20 5
wood_slope 30 4
ballast_loop 7 19
ballast_diag 20 19
ballast_slope 30 18
tunnel 42 18
compare 9 11"

if [ "$STOP" = 1 ]; then game_stop; echo "[narrow] stopped"; exit 0; fi

run_nut() { $M --run-squirrel "$(sed -e "$NUT_SED" -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ingame/narrow.nut)" --timeout 300; }

if [ "$SNOW" = 1 ] && [ "$CAPTURE" != 1 ]; then run_nut; exit 0; fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/narrow/shots}
  mkdir -p "$OUT"
  echo "$SPOTS" | while read -r name dx dy; do
    if [ -z "$ONLY" ] || [[ " $ONLY " == *" $name "* ]]; then
      $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(${ZOOM:-3}); gui.jump(coord3d($((OX + dx)),$((OY + dy)),0)); return 1;" > /dev/null 2>&1
      sleep 1
      $M --capture "$OUT/${PRE}$name.png" > /dev/null 2>&1 && echo "[capture] $OUT/${PRE}$name.png"
    fi
  done
  exit 0
fi

PAK=${PAK:-dist/ami.pak}

GAME_TAG=narrow
game_start "$PAK=ami.pak" $EXTRA_PAKS || exit 1
run_nut
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 7)), $((OY + 5)), 0)); return 1;" > /dev/null
