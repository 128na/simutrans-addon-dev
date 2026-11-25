#!/bin/bash
# 分岐の追加画像（ex 画像）の見本（ingame/ex_sample.nut）を敷く: 検証用のフォルダの写し（work/ex_game/<PORT>/）に pak を入れ、OTRP を MCP つきで起動して見本を流す。
# 敷いた後はゲームを開いたままにする（撮るのは ingame/ex_capture.sh。閉じるのは STOP=1 か手で）。GAME_DIR には書き込まない（#243。以前は GAME_DIR で直接起動して、使用状況を送っていた）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47300 bash ingame/ex_check.sh
#   PORT=47300 STOP=1 bash ingame/ex_check.sh        … 閉じて写しを消す
# PORT は必ず渡す（ほかの作業とポートを分けるため）。WAYS で敷く組を替えられる（ex_sample.nut の WAYS の行を置き換える。Squirrel の配列の式）
#   道路の例（#210）: WAYS='[["ami_road_trunk", null], ["ami_road_trunk_base_single", "ami_wall_road_single"]]'（道路は ex_sample.nut が wt_road で読む。
#     壁は版ごとの way-object: 生活道路の基盤・高架は ami_wall_road_single_ell、一般道路は _arc、幹線・高速は ami_wall_road_<single|back|center|front>）
#   高架の版の例（#82）: WAYS='[["ami_rail_ballast_elev_single", null], ["ami_rail_ladder_elev_single", null]]'
#   高架に架線つきの壁を重ねる例（#85）: WAYS='[["ami_rail_ballast_elev_single", "ami_wall_rail_single_catenary"]]'
PORT=${PORT:?PORT を指定する}
WORK="work/ex_game/$PORT"
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
GAME_TAG=ex
if [ "$STOP" = 1 ]; then game_stop; echo "[ex] stopped"; exit 0; fi
PAK=${PAK:-dist/ami.pak}
NUT=${NUT:-ingame/ex_sample.nut}

game_start "$PAK=ami.pak" || exit 1
WAYS_SED=${WAYS:+s/^local WAYS = .*/local WAYS = $WAYS;/}
echo "$($M --run-squirrel "$(sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' -e "${WAYS_SED:-b}" "$NUT")" --timeout 300)"
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(154, 24, 0)); return 1;" > /dev/null
