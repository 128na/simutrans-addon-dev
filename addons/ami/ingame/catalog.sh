#!/bin/bash
# AMI のカタログ（見て回るための保存データ。#203）を敷いて保存するスクリプト。
# v64 の設定（settings.xml.v64）と土台（flat_1024_left.sve）で、work/catalog_game/<PORT>/ の写しを起動し、ingame/catalog.py で棚を敷く。
# 検証用のフォルダ GAME_DIR には書き込まない。addons/pak128 には AMI の pak だけを入れる（他のアドオンが入ると、カタログが読めなくなる）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47500 bash ingame/catalog.sh           … 起動して catalog.nut を流す
#   python -X utf8 ingame/catalog.py --port 47500 [--only 帯の名前] [--side temperate|snow]                       … 動いているゲームに敷く（--coverage は src/ の名前が棚に有るかの確認で、--port もゲームも要らない）
#   GAME_DIR=<検証用のフォルダ> PORT=47500 bash ingame/catalog.sh ALL                                                                       … 起動して catalog.py で全部敷き、保存する（SAVE_AS の既定は ami_catalog）
#   GAME_DIR=<検証用のフォルダ> PORT=47500 SAVE_AS=ami_catalog bash ingame/catalog.sh                                                        … 保存して GAME_DIR/save/ に置く（既にあれば止まる）
#   PORT=47500 STOP=1 bash ingame/catalog.sh                                                                     … このスクリプトが起動したゲームだけ閉じて写しを消す
PORT=${PORT:?PORT を指定する}
INGAME=$(cd "$(dirname "$0")" && pwd)
cd "$INGAME/.." || exit 1
WORK="work/catalog_game/$PORT"
source "$INGAME/game_lib.sh"  # 起動・停止・MCP のコマンド M（#243）
GAME_TAG=catalog
SAVE=${BASE:-flat_1024_left}  # 土台の保存データ（GAME_DIR/save/）
COPY_DIRS="${COPY_DIRS:-config font themes text script music pak128}"  # addons/pak128 には AMI の pak だけを入れる

script_of() { sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$1"; }

if [ "$STOP" = 1 ]; then game_stop; echo "[catalog] stopped"; exit 0; fi
game_defaults  # GAME_DIR は STOP 以外で必要（SAVE_AS の保存先と起動）
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
GAME_WAIT=${GAME_WAIT:-90}
game_start "$PAK=ami.pak" ${EXTRA_PAKS:-dist/ami_rail_old.pak} || exit 1
echo "[catalog] 起動した"
if [ "$1" = ALL ]; then
  python -X utf8 ingame/catalog.py --port "$PORT" || { echo "[catalog] 敷けなかった所がある。保存しない"; exit 1; }
  PORT=$PORT GAME_DIR=$GAME_DIR SAVE_AS=${SAVE_AS:-ami_catalog} bash "$0"
  exit $?
fi
[ -n "$NUT" ] && echo "$($M --run-squirrel "$(script_of "$NUT")" --timeout 600)"
exit 0
