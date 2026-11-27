#!/bin/bash
# 跨座式モノレールの見本（#113）。ingame/monorail.nut を流す。
# ゲームは work/monorail_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に AMI の pak を足して起動する。
# GAME_DIR には書き込まない。EXTRA_PAKS（空白区切り）の pak は写しの addons/pak128/ にだけ入れる（動作の確かめに借りた車両など。
# リポジトリにも GAME_DIR にも置かない）。敷いた後はゲームを開いたままにする（撮るのは CAPTURE=1）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47400 EXTRA_PAKS="a.pak b.pak" bash ingame/monorail.sh  … 起動して敷く
#   PORT=47400 SNOW=1 bash ingame/monorail.sh                         … 動いているゲームの降雪側（x+256）に同じ見本を敷く
#   PORT=47400 CAPTURE=1 OUT=work/monorail/shots bash ingame/monorail.sh  … 区画ごとに撮る（SNOW=1 を足すと降雪側。名前の先頭に snow_）
#   PORT=47400 STOP=1 bash ingame/monorail.sh                         … 閉じて写しを消す
# ZOOM は gui.set_zoom の値（3 が等倍）
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/monorail_game/$PORT"
OX=20; OY=20
[ "$SNOW" = 1 ] && OX=$((OX + 256))
NUT_SED="s/^local OX = 20;/local OX = $OX;/"
PRE=""; [ "$SNOW" = 1 ] && PRE="snow_"
# 撮る所（monorail.nut の区画の原点からのずれ）は sample_spots.sh の MONORAIL_SPOTS（sample_parallel.sh と共通）
source "$(dirname "$0")/sample_spots.sh"

if [ "$STOP" = 1 ]; then game_stop; echo "[monorail] stopped"; exit 0; fi

run_nut() { $M --run-squirrel "$(sed -e "$NUT_SED" -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ingame/monorail.nut)" --timeout 300; }

if [ "$SNOW" = 1 ] && [ "$CAPTURE" != 1 ]; then run_nut; exit 0; fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/monorail/shots}
  mkdir -p "$OUT"
  for spot in $MONORAIL_SPOTS; do
    IFS=: read -r name dx dy <<< "$spot"
    if [ -z "$ONLY" ] || [[ " $ONLY " == *" $name "* ]]; then
      $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(${ZOOM:-3}); gui.jump(coord3d($((OX + dx)),$((OY + dy)),0)); return 1;" > /dev/null 2>&1
      sleep 1
      $M --capture "$OUT/${PRE}$name.png" > /dev/null 2>&1 && echo "[capture] $OUT/${PRE}$name.png"
    fi
  done
  exit 0
fi

PAK=${PAK:-dist/ami.pak}

GAME_TAG=monorail
game_start "$PAK=ami.pak" $EXTRA_PAKS || exit 1
run_nut
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 8)), $((OY + 5)), 0)); return 1;" > /dev/null
