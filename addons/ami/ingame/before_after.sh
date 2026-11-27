#!/bin/bash
# 前後を撮る共通のスクリプト（#197）: カタログの保存データ（ami_catalog.sve）を、指定した pak の組で起動し、決まった座標を等倍（拡大率 3）で撮る。
# 前の pak と後の pak を別の PAKDIR で 2 回流せば、同じ位置・同じ拡大率の前後の画像になる。
# 使い方（アドオンのディレクトリで。pak は dist/ から別の場所に写しておく。後の分を撮る前に build.py が dist/ を上書きするため）:
#   mkdir -p work/ba/before && cp dist/ami.pak dist/ami_rail_old.pak work/ba/before/            # 前（直す前にビルドした pak）
#   PAKDIR=work/ba/before OUT=work/ba/before_shots PORT=47200 bash ingame/before_after.sh        # 既定の座標（下の SPOTS）を撮る
#   PAKDIR=work/ba/after OUT=work/ba/after_shots PORT=47200 SPOTS_FILE=my_spots.txt bash ingame/before_after.sh
#   PAKDIR=… OUT=… CANAL=1 bash ingame/before_after.sh                                          # 運河の見本（温暖・降雪）を空き地に敷いて撮る
#   前後を一度に撮る（#227）: PAKDIR の代わりに PAKDIR_BEFORE と PAKDIR_AFTER を渡す。OUT/before・OUT/after に撮り（同じ PORT で順に 2 回起動する）、
#     OUT/pairs/<名前>.png に前後を横に並べる（ingame/ba_pairs.py）。
#   PAKDIR_BEFORE=work/ba/before PAKDIR_AFTER=work/ba/after OUT=work/ba/shots PORT=47200 LAYOUTS_FILE=layouts.txt SPOTS_FILE=spots.txt bash ingame/before_after.sh
#   LAYOUTS_FILE（敷き方。1 行 1 つ。# で始まる行は飛ばす）: 「NUT の相対パス  OX  OY  SNOW  [名前=値 …]」。NUT の行頭の
#     「local OX = …;」「local OY = …;」「local SNOW = …;」を置き換えて、ゲームに流す（SNOW は 0 で降雪に塗る、9 で塗らない。canal.nut と同じ決まりの NUT）。
#     「名前=値」は、NUT の行頭の「local 名前 = …;」の右辺を値に置き換える（値に空白・/・& を入れない。sed の置き換えに使うため。例: W=way_desc_x("ami_canal_scenic")）。
#     NUT に該当する「local 名前 = …;」の行が無いと警告する（置き換わらないので）。
#     例: ingame/canal.nut 30 620 9 / ingame/canal.nut 542 620 0 W=way_desc_x("ami_canal_scenic")
#   SPOTS_FILE（撮る場所。1 行 1 か所）: 「名前 x y [cx0 cy0 cx1 cy1]」。後ろの 4 つは、並べる画像で切り抜く範囲（撮った画面の画素の座標。
#     左上が原点、画面は 704×560）。切り抜きは差分から自動で探さず、座標で決める。切り抜きは最近傍で CROP_SCALE（既定 6）倍にする。
#     座標は ami_catalog.sve（1024 四方）のもの。game.sh の既定の地図（512 四方）の座標とは違うので流用しない（README の「カタログ」）。
# 環境変数: PAKDIR（必須。ami.pak と ami_rail_old.pak がある場所。PAKS で名前を替える）、OUT（必須）、PORT（既定 47200）、GAME_DIR（既定
#   検証用のフォルダ。必須）、EXE（既定 sim-WinGDI64-OTRPv64.exe）、SAVE（既定 ami_catalog）、ZOOM（既定 3）、SPOTS_FILE（1 行 1 か所:
#   名前 x y。# で始まる行は飛ばす）、CANAL=1（運河・景観の運河を (30,620) 以降に敷いて撮る）。
# ゲームは work/ba_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定 settings.xml.v64 と pak128 などに、PAKDIR の pak だけを足す）で起動し、
# 撮り終えたら閉じて写しを消す（このスクリプトが起動したゲームだけ）。GAME_DIR には書き込まない。
# 降雪側は温暖側の x に 512 を足した所（カタログの決まり）。画面の撮影（--capture）は 704×560 で、上の道具の帯が写る
[ "$STOP" = 1 ] && [ -z "$PORT" ] && { echo "[ba] STOP=1 には、起動したときの PORT を渡す（既定の 47200 で閉じに行かない。#326）" >&2; exit 1; }
OUT=${OUT:?OUT を指定する}; PORT=${PORT:-47200}
if [ -n "$PAKDIR_BEFORE$PAKDIR_AFTER" ]; then  # 前後を一度に撮る（#227）。自分を 2 回呼び、撮り終えたら並べる
  [ -n "$PAKDIR_BEFORE" ] && [ -n "$PAKDIR_AFTER" ] || { echo "[ba] PAKDIR_BEFORE と PAKDIR_AFTER を両方渡す"; exit 1; }
  me=$(cd "$(dirname "$0")" && pwd)
  rm -rf "$OUT/pairs"
  for side in before after; do
    eval "pd=\$PAKDIR_$(echo $side | tr a-z A-Z)"
    PAKDIR_BEFORE= PAKDIR_AFTER= PAKDIR="$pd" OUT="$OUT/$side" bash "$me/before_after.sh" || exit 1
  done
  python -X utf8 "$me/ba_pairs.py" "$OUT" ${SPOTS_FILE:+--spots "$SPOTS_FILE"} --scale "${CROP_SCALE:-6}"
  exit $?
fi
PAKDIR=${PAKDIR:?PAKDIR を指定する}
mkdir -p "$OUT" && rm -f "$OUT"/*.png  # 前の実行の画像が残って、撮れなかった物が撮れたように見えないようにする
SAVE=${SAVE:-ami_catalog}; ZOOM=${ZOOM:-3}  # カタログの保存データ（GAME_DIR/save/ami_catalog.sve。作り方は README の「カタログ」）
PAKS=${PAKS:-"ami.pak ami_rail_old.pak"}
W="work/ba_game/$PORT"; WORK=$W
source "$(dirname "$0")/game_lib.sh"  # 起動・停止・MCP のコマンド M（#243）
GAME_TAG=ba

# 既定の座標（温暖 / 降雪。カタログの README の表と catalog.py --list の位置。高速道路の分岐など、ほかの所は SPOTS_FILE で渡す）
SPOTS_DEFAULT="t_x4 118 309
s_x4 630 309
t_m6 17 309
s_m6 529 309
t_cwalk 421 211
s_cwalk 933 211"

if [ "$STOP" = 1 ]; then game_stop; echo "[ba] stopped"; exit 0; fi

mkdir -p "$OUT"
GAME_WAIT=${GAME_WAIT:-60}
COPY_DIRS="${COPY_DIRS:-config font themes text script music ${PAKSET:-pak128}}"  # addons/<PAKSET> には前後の pak だけを入れる（256 は PAKSET・PAKSET_SRC）
PAKLIST=""; for p in $PAKS; do PAKLIST="$PAKLIST $PAKDIR/$p"; done
game_start $PAKLIST || exit 1

shot() { # 名前 x y
  timeout 60 $M --run-squirrel "gui.close_all_windows(); gui.set_zoom($ZOOM); gui.jump(coord3d($2,$3,0)); return 1;" > /dev/null 2>&1; sleep 1
  timeout 60 $M --capture "$OUT/$1.png" > /dev/null 2>&1 && echo "[ba] $OUT/$1.png"
}

if [ "$CANAL" = 1 ]; then
  # 運河の見本を空き地（y=620・680）に敷く。温暖は x=30、降雪は x=542（SNOW を 0 にして、敷いた後に降雪に塗る）
  for ox in 30 542; do
    for spec in "ami_canal 620" "ami_canal_scenic 680"; do
      read -r way oy <<< "$spec"
      sv=9; [ $ox = 542 ] && sv=0
      sed -e "s/^local SNOW = 9;/local SNOW = $sv;/" -e "s/^local OX = 20;/local OX = $ox;/" -e "s/^local OY = 20;/local OY = $oy;/" \
          -e "s/^local W = way_desc_x(\"ami_canal\");/local W = way_desc_x(\"$way\");/" ingame/canal.nut \
        | sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' > "$W/run.nut"
      timeout 300 $M --run-squirrel "$(cat "$W/run.nut")" --timeout 280 | cut -c1-100
    done
  done
  for side in t s; do
    dx=0; [ $side = s ] && dx=512
    shot ${side}_canal $((37 + dx)) 625
    shot ${side}_canal_diag $((50 + dx)) 625
    shot ${side}_scenic $((37 + dx)) 685
    shot ${side}_scenic_diag $((50 + dx)) 685
  done
fi

if [ -n "$LAYOUTS_FILE" ]; then
  # 敷き方（#227）: NUT の OX・OY・SNOW と、名前=値で渡した行頭の local を置き換えて流す
  grep -v '^#' "$LAYOUTS_FILE" | while read -r nut ox oy snow extra; do
    [ -n "$nut" ] || continue
    for k in SNOW OX OY; do grep -q "^local $k = " "$nut" || echo "[ba] 警告: $nut に local $k の行が無い（置き換わらない）"; done
    seds=(-e "s/^local SNOW = .*;/local SNOW = $snow;/" -e "s/^local OX = .*;/local OX = $ox;/" -e "s/^local OY = .*;/local OY = $oy;/")
    for kv in $extra; do grep -q "^local ${kv%%=*} = " "$nut" || echo "[ba] 警告: $nut に local ${kv%%=*} の行が無い（置き換わらない）"; seds+=(-e "s/^local ${kv%%=*} = .*;/local ${kv%%=*} = ${kv#*=};/"); done
    sed -e 's/\r$//' "$nut" | sed "${seds[@]}" | sed -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' > "$W/run.nut"
    echo "[ba] layout $nut ($ox,$oy)"
    timeout 300 $M --run-squirrel "$(cat "$W/run.nut")" --timeout 280 < /dev/null | cut -c1-100
  done
fi

if [ -n "$SPOTS_FILE" ]; then SPOTS=$(grep -v '^#' "$SPOTS_FILE"); elif [ "$CANAL" = 1 ] || [ -n "$LAYOUTS_FILE" ]; then SPOTS=""; else SPOTS="$SPOTS_DEFAULT"; fi
echo "$SPOTS" | while read -r name x y _; do [ -n "$name" ] && shot "$name" "$x" "$y"; done
game_stop
echo "[ba] done"
