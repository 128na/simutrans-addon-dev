#!/bin/bash
# 分岐の絵（OTRP の switch 画像）を確かめる準備: pak を入れ、固定の道具がある OTRP のビルドを MCP つきで起動し、見本を敷く。
# 敷いた後はゲームを開いたままにする（タイルの詳細で選択肢を選んで見る）。閉じるのは手で。
# 使い方（アドオンのディレクトリで。makeobj で dist/bpoc.pak を作っておく）:
#   GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe bash ingame/switch_check.sh
# 見本の場所:
#   ingame/switch.nut      固定: x=125〜140, y=100〜115（T字 4 つと十字。左が選択 1、右が選択 2。上が bpoc_track、下が側壁 single）
#   ingame/switch_auto.nut 自動選択: y=120 の行、x=150 から 8 ずつ 8 通り
GAME_DIR=${GAME_DIR:?GAME_DIR を指定する（例: F:/Simutrans/addon_check）}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat}
PORT=${PORT:-47123}
M="python ${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py} --port $PORT"

cp dist/bpoc.pak "$GAME_DIR/addons/pak128/bpoc.pak" || exit 1
(cd "$GAME_DIR" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
echo "[switch] 固定:   $($M --run-squirrel "$(cat ingame/switch.nut)")"
echo "[switch] 自動選択: $($M --run-squirrel "$(cat ingame/switch_auto.nut)")"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(2); gui.jump(coord3d(128, 103, 0)); return 1;" > /dev/null
