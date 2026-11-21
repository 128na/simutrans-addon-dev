#!/bin/bash
# 分岐の追加画像（ex 画像）の見本（ingame/ex_sample.nut）を敷く: pak を入れ、OTRP を MCP つきで flat_512 で起動して見本を流す。
# 敷いた後はゲームを開いたままにする（撮るのは ingame/ex_capture.sh。閉じるのは手で、または KILL=1 で終わりに閉じる）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe PORT=47300 bash ingame/ex_check.sh
# PORT は必ず渡す（ほかの作業とポートを分けるため）。WAYS で敷く組を替えられる（ex_sample.nut の WAYS の行を置き換える。Squirrel の配列の式）
#   高架の版の例（#82）: WAYS='[["ami_rail_ballast_elev_single", null], ["ami_rail_ladder_elev_single", null]]'
GAME_DIR=${GAME_DIR:?GAME_DIR を指定する（例: F:/Simutrans/addon_check）}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
PORT=${PORT:?PORT を指定する}
SAVE=${SAVE:-flat_512}
PAK=${PAK:-dist/ami.pak}
NUT=${NUT:-ingame/ex_sample.nut}
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port $PORT"

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[ex] ポート $PORT で既にゲームが動いている（PORT を替えるか、そのゲームを閉じる）"; exit 1; }
cp "$PAK" "$GAME_DIR/addons/pak128/ami.pak" || exit 1
(cd "$GAME_DIR" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
WAYS_SED=${WAYS:+s/^local WAYS = .*/local WAYS = $WAYS;/}
echo "$($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' -e "${WAYS_SED:-b}" "$NUT")" --timeout 300)"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(154, 24, 0)); return 1;" > /dev/null
