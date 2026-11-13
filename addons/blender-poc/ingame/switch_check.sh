#!/bin/bash
# 分岐の絵（OTRP の switch 画像）を手で確かめる準備: pak を入れ、固定の道具がある OTRP のビルドを MCP つきで起動し、見本を敷く。
# 敷いた後はゲームを開いたままにする（タイルの詳細で選択肢を選んで見る）。閉じるのは手で。
# 使い方（アドオンのディレクトリで。makeobj で dist/bpoc.pak を作っておく）:
#   GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe bash ingame/switch_check.sh
# SAVE は空の平らなマップ（既定 flat2）。見本は ingame/switch_all.nut（線路の 11 アドオンを 1 行ずつ。名札つき）
GAME_DIR=${GAME_DIR:?GAME_DIR を指定する（例: F:/Simutrans/addon_check）}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat2}
PORT=${PORT:-47123}
M="python ${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py} --port $PORT"

cp dist/bpoc.pak "$GAME_DIR/addons/pak128/bpoc.pak" || exit 1
(cd "$GAME_DIR" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
echo "[switch] $($M --run-squirrel "$(cat ingame/switch_all.nut)" --timeout 300)"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(16, 8, 0)); return 1;" > /dev/null
