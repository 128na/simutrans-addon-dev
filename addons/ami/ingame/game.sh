#!/bin/bash
# 検証用のフォルダの写しでゲームを 1 台起動し、見本を流して開いたままにする。撮る・閉じるも同じスクリプトで行う（#119）。
# ゲームは work/game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に、AMI の pak（PAK）と EXTRA_PAKS を足して起動する。
# GAME_DIR には書き込まない。EXTRA_TEXTS に訳のファイル（*.tab）を渡すと、写しの addons/pak128/text/ に入れる。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=47300 NUT=ingame/sidewalk_struct.nut bash ingame/game.sh   … 起動して NUT を流す
#   PORT=47300 NUT=<見本> bash ingame/game.sh RUN                                         … 動いているゲームに NUT を流す
#   PORT=47300 OUT=work/x SPOTS="名前:x:y 名前:x:y" bash ingame/game.sh CAPTURE             … 等倍（ZOOM）で場所ごとに撮る
#   PORT=47300 bash ingame/game.sh STOP                                                    … 閉じて写しを消す
# 道路の見本（road_sample.nut）は ROAD_NAMES="ami_road_expressway"・CLIMATES="snow" で種類・気候を絞れる（空白区切り。既定は全部）
# NUT の中の行頭の「local OX = <数>;」は、OX を渡すとその値に置き換える（降雪側に同じ見本を敷くとき）
PORT=${PORT:?PORT を指定する}
INGAME=$(cd "$(dirname "$0")" && pwd)
cd "$INGAME/.." || exit 1  # アドオンのディレクトリ（work/ と相対のパスはここから）
source "$INGAME/mcp_client.sh"
M="python -X utf8 $MCP_CLIENT --port $PORT"
WORK="work/game/$PORT"

script_of() {
  local sed_ox=()
  [ -n "$OX" ] && sed_ox=(-e "s/^local OX = [0-9]*;/local OX = $OX;/")
  # 道路の見本の絞り込み（#208）: ROAD_NAMES="ami_road_general ..."・CLIMATES="temperate snow"
  if [ -n "$ROAD_NAMES" ]; then
    local rl; rl=$(printf '"%s", ' $ROAD_NAMES); sed_ox+=(-e "s/^local ROADS = .*/local ROADS = [${rl%, }];/")
  fi
  if [ -n "$CLIMATES" ]; then
    local ol="" c; for c in $CLIMATES; do
      case "$c" in temperate) ol+="[20, 20, 0], " ;; snow) ol+="[276, 20, 1], " ;; *) echo "CLIMATES は temperate・snow: $c" >&2 ;; esac
    done
    sed_ox+=(-e "s/^local ORIGINS = .*/local ORIGINS = [${ol%, }];/")
  fi
  sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "${sed_ox[@]}" "$1"
}

stop_game() {
  local win; win=$(cd "$WORK" 2> /dev/null && pwd -W) || return 0
  powershell.exe -NoProfile -Command "\$d = '$win'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}

case "$1" in
  STOP) stop_game; echo "[game] stopped"; exit 0 ;;
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

GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PAK=${PAK:-dist/ami.pak}
$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[game] ポート $PORT で既にゲームが動いている"; exit 1; }
rm -rf "$WORK"
mkdir -p "$WORK/save"
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$WORK/" || exit 1
for d in config font themes text script music pak128 addons; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$WORK/" || exit 1; }
done
printf '\nday_night_shift = 0\n' >> "$WORK/config/simuconf.tab"
cp "$GAME_DIR/save/$SAVE.sve" "$WORK/save/" || exit 1
SETTINGS=${SETTINGS:-settings.xml}  # 写しに入れる設定（GAME_DIR の中のファイル名。v64 は settings.xml.v64）
[ -f "$GAME_DIR/$SETTINGS" ] && { cp "$GAME_DIR/$SETTINGS" "$WORK/settings.xml"; chmod u+w "$WORK/settings.xml"; }
cp "$PAK" "$WORK/addons/pak128/ami.pak" || exit 1
for p in ${EXTRA_PAKS:-}; do cp "$p" "$WORK/addons/pak128/$(basename "$p")" || exit 1; done
# 訳のファイル（addons/pak128/text/<言語>_<名前>.tab。本体は名前の先頭 2 文字で言語を決める: dataobj/translator.cc）
for t in ${EXTRA_TEXTS:-}; do mkdir -p "$WORK/addons/pak128/text" && cp "$t" "$WORK/addons/pak128/text/$(basename "$t")" || exit 1; done
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
[ -n "$NUT" ] && echo "$($M --run-squirrel "$(script_of "$NUT")" --timeout 300)"
exit 0
