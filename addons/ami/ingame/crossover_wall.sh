#!/bin/bash
# 壁つきの線路の間の渡り線（#101）の見本。ingame/crossover_wall.nut を流す。
# ゲームは work/crossover_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に、AMI の pak と iss の線路・架線の pak を
# 足して起動する。GAME_DIR には書き込まない。敷いた後はゲームを開いたままにする（撮るのは CAPTURE=1）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47400 bash ingame/crossover_wall.sh   … 起動して敷く（T字のタイルの way と壁を出す）
#   PORT=47400 CAPTURE=1 OUT=work/crossover/shots bash ingame/crossover_wall.sh              … 撮る（組・壁の敷き方・線の並びごと）
#   PORT=47400 SNOW=1 bash ingame/crossover_wall.sh                                          … 動いているゲームの降雪側（x+256）に同じ見本を敷く
#   （CAPTURE=1 に SNOW=1 を足すと降雪側を撮る。画像の名前の先頭に snow_ が付く）
#   PORT=47400 STOP=1 bash ingame/crossover_wall.sh                                          … 閉じて写しを消す
# PAK で AMI の pak を替えられる（直す前の pak と比べるとき）。ISS_PAKS で iss の pak を渡す
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/crossover_game/$PORT"
# crossover_wall.nut の OX・OY・SET_DY・MODE_DX と、組の中の線の並びの y（0・4・8・12）に合わせる
OX=20; OY=20; SET_DY=22; MODE_DX=20
[ "$SNOW" = 1 ] && OX=$((OX + 256))
NUT_SED="s/^local OX = 20;/local OX = $OX;/"
PRE=""; [ "$SNOW" = 1 ] && PRE="snow_"


if [ "$STOP" = 1 ]; then game_stop; echo "[crossover] stopped"; exit 0; fi

if [ "$SNOW" = 1 ] && [ "$CAPTURE" != 1 ]; then
  echo "$($M --run-squirrel "$(sed -e "$NUT_SED" -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "${NUT:-ingame/crossover_wall.nut}")" --timeout 300)"
  exit 0
fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/crossover/shots}
  ZOOM=${ZOOM:-3}
  SETS=${SETS:-"ami_wall ami_cat iss_cat"}
  MODES=${MODES:-"main all late plain relay"}
  LINES=${LINES:-"bf:0 bc:4 cf:8 bcf:12"}
  mkdir -p "$OUT"
  si=0
  for s in ami_wall ami_cat iss_cat; do
    mi=0
    for m in main all late plain relay; do
      for gspec in $LINES; do
        IFS=: read g gy <<< "$gspec"
        if [[ " $SETS " == *" $s "* && " $MODES " == *" $m "* ]]; then
          x=$((OX + mi * MODE_DX + 7)); y=$((OY + si * SET_DY + gy + 1))
          $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($x,$y,0)); return 1;" > /dev/null 2>&1
          sleep 1
          $M --capture "$OUT/${PRE}${s}_${m}_${g}.png" > /dev/null 2>&1 && echo "[capture] $OUT/${PRE}${s}_${m}_${g}.png"
        fi
      done
      mi=$((mi + 1))
    done
    si=$((si + 1))
  done
  exit 0
fi

PAK=${PAK:-dist/ami.pak}
REFS=$(cd "$(dirname "$0")" && git rev-parse --path-format=absolute --git-common-dir 2> /dev/null | xargs dirname | xargs dirname)/refs
ISS_PAKS=${ISS_PAKS:-"$REFS/iss/release/pak128/iss_rail_way.pak $REFS/iss/release/pak128/iss_rail_way-object-new_position.pak"}
NUT=${NUT:-ingame/crossover_wall.nut}

GAME_TAG=crossover
game_start "$PAK=ami.pak" $ISS_PAKS || exit 1
echo "$($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$NUT")" --timeout 300)"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 7)), $((OY + 1)), 0)); return 1;" > /dev/null
