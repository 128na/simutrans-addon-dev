#!/bin/bash
# AMI の見本を敷く準備: 検証用のフォルダの写し（work/sample_game/<PORT>/）に pak を入れ、OTRP を MCP つきで起動して ingame/sample.nut を流す。
# 敷いた後はゲームを開いたままにする（見て回るのは手で。閉じるのは STOP=1 か手で）。GAME_DIR には書き込まない（#243。以前は GAME_DIR で直接起動して、使用状況を送っていた）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47300 bash ingame/sample_check.sh
#   PORT=47300 STOP=1 bash ingame/sample_check.sh        … 閉じて写しを消す
# 地図は GAME_DIR/save/ の flat_512_left_v64.sve（SAVE で替えられる）。保存はユーザーが行う（開くたびに空なので、見本は毎回流す）
PORT=${PORT:?PORT に MCP のポートを指定する}
WORK="work/sample_game/$PORT"
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
GAME_TAG=sample
if [ "$STOP" = 1 ]; then game_stop; echo "[sample] stopped"; exit 0; fi
# PAK で入れる pak を替えられる（レイアウト検証用モードは PAK=work/layout/dist/ami.pak）
PAK=${PAK:-dist/ami.pak}

game_start "$PAK=ami.pak" || exit 1
# 見本はコマンドラインの引数で渡すので、Windows のコマンドラインの長さの上限（32,767 文字）に収まるよう、行頭のコメント・字下げ・空行を除いて渡す。
# 行頭の空白と // で始まる行を消すので、sample.nut に複数行の文字列を足すと中身が変わる（1 行の文字列にする）
# NUT で流すスクリプトを替えられる（例: 橋とトンネルの区画だけ敷く写し）
NUT=${NUT:-ingame/sample.nut}
# TRACK で敷く軌道を替えられる（例: TRACK=ami_rail_slab。sample.nut の先頭の TRACK を置き換えて流す）
TRACK_SED=${TRACK:+s/^local TRACK = .*/local TRACK = \"$TRACK\";/}
echo "[sample] $($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' -e "${TRACK_SED:-b}" "$NUT")" --timeout 300)"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(24, 24, 0)); return 1;" > /dev/null
