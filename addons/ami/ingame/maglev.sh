#!/bin/bash
# リニアの見本（#371）。ingame/maglev.nut を流す。
# ゲームは work/maglev_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に AMI の pak を足して起動する。
# GAME_DIR には書き込まない。EXTRA_PAKS（空白区切り）の pak は写しの addons/pak128/ にだけ入れる（試しの車両など。
# リポジトリにも GAME_DIR にも置かない）。敷いた後はゲームを開いたままにする（撮るのは CAPTURE=1）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47500 EXTRA_PAKS="test.pak" bash ingame/maglev.sh  … 起動して敷く
#   PORT=47500 SNOW=1 bash ingame/maglev.sh                         … 動いているゲームの降雪側（x+256）に同じ見本を敷く
#   PORT=47500 CAPTURE=1 OUT=work/maglev/shots bash ingame/maglev.sh  … 区画ごとに撮る（SNOW=1 を足すと降雪側。名前の先頭に snow_）
#   PORT=47500 STOP=1 bash ingame/maglev.sh                         … 閉じて写しを消す
# ZOOM は gui.set_zoom の値（3 が等倍）。ONLY に撮る所の名前（空白区切り）を渡すと、それだけ撮る
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/maglev_game/$PORT"
OX=20; OY=20
[ "$SNOW" = 1 ] && OX=$((OX + 256))
NUT_SED="s/^local OX = 20;/local OX = $OX;/"
[ "$SNOW" = 1 ] && NUT_SED="$NUT_SED;s/^local SNOW = 9;/local SNOW = 0;/"
PRE=""; [ "$SNOW" = 1 ] && PRE="snow_"
# 撮る所: 名前 x y（maglev.nut の区画の原点からのずれ）
SPOTS="guideway 8 5
guideway_diag 21 5
beam 8 17
beam_diag 21 17
tube 8 29
tube_diag 21 29
pair 9 40
pair_elev 27 40
tube_pair 45 40
center 9 46
tunnel 4 51
elev_single 49 3
elev_single_r 63 3
elev_back 49 13
elev_center 49 23
elev_front 49 33
elev_front_r 63 33
beam_elev_front 89 3
beam_elev_center 89 13
beam_elev_back 89 23
beam_elev_r 103 3
tube_elev_single 129 3
tube_elev_back 129 13
tube_elev_center 129 23
tube_elev_front 129 33
tube_elev_r 143 3"

if [ "$STOP" = 1 ]; then game_stop; echo "[maglev] stopped"; exit 0; fi

run_nut() { $M --run-squirrel "$(sed -e "$NUT_SED" -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ingame/maglev.nut)" --timeout 300; }

if [ "$SNOW" = 1 ] && [ "$CAPTURE" != 1 ]; then run_nut; exit 0; fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/maglev/shots}
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

GAME_TAG=maglev
game_start "$PAK=ami.pak" $EXTRA_PAKS || exit 1
run_nut
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 8)), $((OY + 5)), 0)); return 1;" > /dev/null
