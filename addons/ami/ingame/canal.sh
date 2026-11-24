#!/bin/bash
# 運河と船の車庫の見本（#114）。NUT（既定は ingame/canal.nut）を流す。
#   ingame/canal_link.nut … 運河と歩道（どちらも waytype が water）を並べたり突き当てたりして、つながるか・船が歩道に入るかを見る
#   ingame/canal.nut      … AMI の運河と船の車庫を敷いて、船を走らせる
# ゲームは work/canal_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に AMI の pak を足して起動する。
# GAME_DIR には書き込まない。敷いた後はゲームを開いたままにする（撮るのは CAPTURE=1）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47401 bash ingame/canal.sh   … 起動して NUT を流す
#   PORT=47401 NUT=ingame/canal_link.nut RUN=1 bash ingame/canal.sh                 … 動いているゲームに NUT を流す
#   PORT=47401 SNOW=1 bash ingame/canal.sh                                           … 動いているゲームの降雪側（x+256）に同じ見本を敷く
#   PORT=47401 CAPTURE=1 OUT=work/canal/shots bash ingame/canal.sh                   … 区画ごとに撮る（SNOW=1 を足すと降雪側。名前の先頭に snow_）
#   WAY=ami_canal_scenic …                                                           … 景観の運河（#161）を敷く（canal.nut の W を替える）
#   PORT=47401 STOP=1 bash ingame/canal.sh                                           … 閉じて写しを消す
# ZOOM は gui.set_zoom の値（3 が等倍）
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/canal_game/$PORT"
NUT=${NUT:-ingame/canal.nut}
OX=20; OY=20
[ "$SNOW" = 1 ] && OX=$((OX + 256))
WAY=${WAY:-ami_canal}   # 敷く way（景観の運河なら WAY=ami_canal_scenic。#161）
SNOWV=9; [ "$SNOW" = 1 ] && SNOWV=0
NUT_SED="s/^local SNOW = 9;/local SNOW = $SNOWV;/; s/^local OX = 20;/local OX = $OX;/; s/^local W = way_desc_x(\"ami_canal\");/local W = way_desc_x(\"$WAY\");/"
PRE=""; [ "$SNOW" = 1 ] && PRE="snow_"
# 撮る所: 名前 x y（canal.nut の区画の原点からのずれ）
SPOTS=${SPOTS:-"ground 7 5
diag 20 5
slope 6 15
close 21 16
depot 2 3"}


if [ "$STOP" = 1 ]; then game_stop; echo "[canal] stopped"; exit 0; fi

run_nut() { $M --run-squirrel "$(sed -e "$NUT_SED" -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$NUT")" --timeout 300; }

if [ "$RUN" = 1 ] || { [ "$SNOW" = 1 ] && [ "$CAPTURE" != 1 ]; }; then run_nut; exit 0; fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/canal/shots}
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

GAME_TAG=canal
game_start "$PAK=ami.pak" || exit 1
run_nut
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 8)), $((OY + 5)), 0)); return 1;" > /dev/null
