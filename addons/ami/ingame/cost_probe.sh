#!/bin/bash
# 駅・車庫の建設費の測定（#160）。ゲームを検証用フォルダの写し（work/cost/<PORT>/）で起動し、ingame/cost_probe.nut を流して閉じる。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47300 bash ingame/cost_probe.sh
# 建てる前後の所持金（float）の差と、純資産（整数）の差を並べて出す。
PORT=${PORT:?PORT に MCP のポートを指定する}
WORK="work/cost/$PORT"
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
GAME_TAG=cost
trap game_cleanup EXIT
trap 'exit 130' INT TERM
game_start "${PAK:-dist/ami.pak}=ami.pak" || exit 1
S=$(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ${NUT:-ingame/cost_probe.nut})
$M --run-squirrel "$S" --timeout 120
