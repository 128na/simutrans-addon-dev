#!/bin/bash
# 検証用のフォルダの写しでゲームを 1 台起動し、見本を流して開いたままにする。撮る・閉じるも同じスクリプトで行う（#119）。
# ゲームは work/game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に、AMI の pak（PAK）と EXTRA_PAKS を足して起動する。
# GAME_DIR には書き込まない。EXTRA_TEXTS に訳のファイル（*.tab）を渡すと、写しの addons/pak128/text/ に入れる。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47300 NUT=ingame/sidewalk_struct.nut bash ingame/game.sh   … 起動して NUT を流す
#   PORT=47300 NUT=<見本> bash ingame/game.sh RUN                                         … 動いているゲームに NUT を流す
#   PORT=47300 OUT=work/x SPOTS="名前:x:y 名前:x:y" bash ingame/game.sh CAPTURE             … 等倍（ZOOM）で場所ごとに撮る
#   PORT=47300 bash ingame/game.sh STOP                                                    … 閉じて写しを消す
# 道路の見本（road_sample.nut）は ROAD_NAMES="ami_road_expressway"・CLIMATES="snow" で種類・気候を絞れる（空白区切り。既定は全部）
# NUT の中の行頭の「local OX = <数>;」は、OX を渡すとその値に置き換える（降雪側に同じ見本を敷くとき）
PORT=${PORT:?PORT を指定する}
INGAME=$(cd "$(dirname "$0")" && pwd)
cd "$INGAME/.." || exit 1  # アドオンのディレクトリ（work/ と相対のパスはここから）
WORK="work/game/$PORT"
source "$INGAME/game_lib.sh"  # 起動・停止・MCP のコマンド M（#243）
GAME_TAG=game

script_of() {
  local sed_ox=()
  [ -n "$OX" ] && sed_ox=(-e "s/^local OX = [0-9]*;/local OX = $OX;/")
  # 道路の見本の絞り込み（#208）: ROAD_NAMES="ami_road_general ..."・CLIMATES="temperate snow"
  if [ -n "$ROAD_NAMES$CLIMATES" ]; then
    case "$1" in *road_sample.nut) ;; *) echo "ROAD_NAMES・CLIMATES は road_sample.nut だけに効く: $1" >&2; exit 1 ;; esac
  fi
  if [ -n "$ROAD_NAMES" ]; then
    [[ "$ROAD_NAMES" =~ ^[A-Za-z0-9_\ ]+$ ]] || { echo "ROAD_NAMES は英数字・_・空白だけ" >&2; exit 1; }
    local rl; rl=$(printf '"%s", ' $ROAD_NAMES); sed_ox+=(-e "s/^local ROADS = .*/local ROADS = [${rl%, }];/")
  fi
  if [ -n "$CLIMATES" ]; then
    local ol="" c; for c in $CLIMATES; do
      case "$c" in temperate) ol+="[20, 20, 0], " ;; snow) ol+="[276, 20, 1], " ;; *) echo "CLIMATES は temperate・snow（空白区切り）: $c" >&2; exit 1 ;; esac
    done
    [ -n "$ol" ] || { echo "CLIMATES が空" >&2; exit 1; }
    sed_ox+=(-e "s/^local ORIGINS = .*/local ORIGINS = [${ol%, }];/")
  fi
  sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "${sed_ox[@]}" "$1"
}

# 絞り込みの値が不正なら、ゲームを起動する前に止める（script_of の中の exit は $(...) では効かない）
[ -n "$NUT" ] && { script_of "$NUT" > /dev/null || exit 1; }

case "$1" in
  STOP) game_stop; echo "[game] stopped"; exit 0 ;;
  RUN) echo "$($M --run-squirrel "$(script_of "${NUT:?NUT を指定する}")" --timeout 300)"; exit 0 ;;
  CAPTURE)
    OUT=${OUT:-work/game_shots}; ZOOM=${ZOOM:-3}; mkdir -p "$OUT"
    for spot in ${SPOTS:?SPOTS を指定する}; do
      IFS=: read n x y <<< "$spot"
      $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($x,$y,0)); return 1;" > /dev/null 2>&1
      sleep "${WAIT:-1}"
      $M --capture "$OUT/$n.png" > /dev/null 2>&1 && echo "[capture] $OUT/$n.png"
    done
    exit 0 ;;
esac

PAK=${PAK:-dist/ami.pak}
game_start "$PAK=ami.pak" ${EXTRA_PAKS:-} || exit 1
[ -n "$NUT" ] && echo "$($M --run-squirrel "$(script_of "$NUT")" --timeout 300)"
exit 0
