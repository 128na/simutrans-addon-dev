#!/bin/bash
# AMI のカタログ（見て回るための保存データ。#203）を敷いて保存するスクリプト。
# v64 の設定（settings.xml.v64）と土台（flat_1024_left.sve）で、work/catalog_game/<PORT>/ の写しを起動し、ingame/catalog.py で棚を敷く。
# 検証用のフォルダ GAME_DIR には書き込まない。addons/pak128 には AMI の pak だけを入れる（他のアドオンが入ると、カタログが読めなくなる）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=F:/Simutrans/addon_check EXE=sim-WinGDI64-OTRPv64.exe PORT=47500 bash ingame/catalog.sh           … 起動して catalog.nut を流す
#   python -X utf8 ingame/catalog.py --port 47500 [--only 帯の名前] [--side temperate|snow]                       … 動いているゲームに敷く（--coverage は src/ の名前が棚に有るかの確認）
#   PORT=47500 bash ingame/catalog.sh ALL                                                                       … 起動して catalog.py で全部敷き、保存する（SAVE_AS の既定は ami_catalog）
#   PORT=47500 SAVE_AS=ami_catalog bash ingame/catalog.sh                                                        … 保存して GAME_DIR/save/ に置く（既にあれば止まる）
#   PORT=47500 STOP=1 bash ingame/catalog.sh                                                                     … このスクリプトが起動したゲームだけ閉じて写しを消す
PORT=${PORT:?PORT を指定する}
INGAME=$(cd "$(dirname "$0")" && pwd)
cd "$INGAME/.." || exit 1
source "$INGAME/mcp_client.sh"
M="python -X utf8 $MCP_CLIENT --port $PORT"
WORK="work/catalog_game/$PORT"
GAME_DIR=${GAME_DIR:-F:/Simutrans/addon_check}
EXE=${EXE:-sim-WinGDI64-OTRPv64.exe}
BASE=${BASE:-flat_1024_left}

script_of() { sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$1"; }

stop_game() {
  local win; win=$(cd "$WORK" 2> /dev/null && pwd -W) || return 0
  powershell.exe -NoProfile -Command "\$d = '$win'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}

if [ "$STOP" = 1 ]; then stop_game; echo "[catalog] stopped"; exit 0; fi
if [ -n "$SAVE_AS" ]; then
  # world.save_game は写し（$WORK/save/）に書く。検証用のフォルダの save/ へは、既にあれば止まり、無ければ写して読み取り専用にする
  dest="$GAME_DIR/save/$SAVE_AS.sve"
  [ -e "$dest" ] && { echo "[catalog] $dest が既にある（上書きしない）"; exit 1; }
  out=$($M --run-squirrel "return world.save_game(\"$SAVE_AS\");" --timeout 600); echo "[catalog] save_game: $out"
  [ "$out" = '{"result":null}' ] || exit 1
  cp "$WORK/save/$SAVE_AS.sve" "$dest" || exit 1
  chmod a-w "$dest"; ls -l "$dest"; exit 0
fi

PAK=${PAK:-dist/ami.pak}
$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[catalog] ポート $PORT で既にゲームが動いている"; exit 1; }
rm -rf "$WORK"
mkdir -p "$WORK/save" "$WORK/addons/pak128"
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$WORK/" || exit 1
for d in config font themes text script music pak128; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$WORK/" || exit 1; }
done
printf '\nday_night_shift = 0\n' >> "$WORK/config/simuconf.tab"
cp "$GAME_DIR/save/$BASE.sve" "$WORK/save/" || exit 1
cp "$GAME_DIR/settings.xml.v64" "$WORK/settings.xml" || exit 1; chmod u+w "$WORK/settings.xml"
bash "$INGAME/strip_usage_log.sh" "$WORK/settings.xml" || exit 1  # 送信用の記録を外す（#235）
cp "$PAK" "$WORK/addons/pak128/ami.pak" || exit 1
for p in ${EXTRA_PAKS:-dist/ami_rail_old.pak}; do cp "$p" "$WORK/addons/pak128/$(basename "$p")" || exit 1; done
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$BASE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 90); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
echo "[catalog] 起動した"
if [ "$1" = ALL ]; then
  python -X utf8 ingame/catalog.py --port "$PORT" || { echo "[catalog] 敷けなかった所がある。保存しない"; exit 1; }
  PORT=$PORT GAME_DIR=$GAME_DIR SAVE_AS=${SAVE_AS:-ami_catalog} bash "$0"
  exit $?
fi
[ -n "$NUT" ] && echo "$($M --run-squirrel "$(script_of "$NUT")" --timeout 600)"
exit 0
