#!/bin/bash
# 駅・車庫の建設費の測定（#160）。ゲームを検証用フォルダの写し（work/cost/<PORT>/）で起動し、ingame/cost_probe.nut を流して閉じる。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   PORT=47300 bash ingame/cost_probe.sh   （GAME_DIR の既定は F:/Simutrans/addon_check、EXE の既定は OTRPv64_3.exe）
# 建てる前後の所持金（float）の差と、純資産（整数）の差を並べて出す。
GAME_DIR=${GAME_DIR:-F:/Simutrans/addon_check}; EXE=${EXE:-OTRPv64_3.exe}; PORT=${PORT:-47300}; SAVE=${SAVE:-flat_512}
source ingame/mcp_client.sh
W=work/cost/$PORT; rm -rf $W; mkdir -p $W/save
cp $GAME_DIR/$EXE $GAME_DIR/*.dll $W/
for d in config font themes text script music pak128 addons; do [ -d $GAME_DIR/$d ] && cp -r $GAME_DIR/$d $W/; done
cp $GAME_DIR/save/$SAVE.sve $W/save/; cp dist/ami.pak $W/addons/pak128/ami.pak
[ -f $GAME_DIR/settings.xml ] && cp $GAME_DIR/settings.xml $W/
bash "$(dirname "${BASH_SOURCE[0]:-$0}")/strip_usage_log.sh" "$W/settings.xml" || exit 1  # 送信用の記録を外す（#235）
WIN=$(cd $W && pwd -W)
(cd $W && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port $PORT > /dev/null 2>&1 &)
for r in $(seq 1 120); do timeout 10 python -X utf8 $MCP_CLIENT --port $PORT --timeout 5 --run-squirrel "return 1;" >/dev/null 2>&1 && break; sleep 1; done
S=$(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' ${NUT:-ingame/cost_probe.nut})
python -X utf8 $MCP_CLIENT --port $PORT --run-squirrel "$S" --timeout 120
powershell.exe -NoProfile -Command "\$d = '$WIN'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" >/dev/null 2>&1
sleep 1; rm -rf $W
