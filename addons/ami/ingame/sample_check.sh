#!/bin/bash
# AMI の見本を敷く準備: pak を入れ、OTRP を MCP つきで flat_512 で起動して ingame/sample.nut を流す。
# 敷いた後はゲームを開いたままにする（見て回るのは手で。閉じるのも手で）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe bash ingame/sample_check.sh
# flat_512.sve は読み取り専用で、保存はユーザーが行う（開くたびに空なので、見本は毎回流す）
GAME_DIR=${GAME_DIR:?GAME_DIR を指定する（例: F:/Simutrans/addon_check）}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PORT=${PORT:-47123}
M="python ${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py} --port $PORT"

cp dist/ami.pak "$GAME_DIR/addons/pak128/ami.pak" || exit 1
(cd "$GAME_DIR" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
echo "[sample] $($M --run-squirrel "$(cat ingame/sample.nut)" --timeout 300)"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(24, 24, 0)); return 1;" > /dev/null
