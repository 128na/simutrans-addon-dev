#!/bin/bash
# 前後を撮る共通のスクリプト（#197）: カタログの保存データ（ami_catalog.sve）を、指定した pak の組で起動し、決まった座標を等倍（拡大率 3）で撮る。
# 前の pak と後の pak を別の PAKDIR で 2 回流せば、同じ位置・同じ拡大率の前後の画像になる。
# 使い方（アドオンのディレクトリで。pak は dist/ から別の場所に写しておく。後の分を撮る前に build.py が dist/ を上書きするため）:
#   mkdir -p work/ba/before && cp dist/ami.pak dist/ami_rail_old.pak work/ba/before/            # 前（直す前にビルドした pak）
#   PAKDIR=work/ba/before OUT=work/ba/before_shots PORT=47200 bash ingame/before_after.sh        # 既定の座標（下の SPOTS）を撮る
#   PAKDIR=work/ba/after OUT=work/ba/after_shots PORT=47200 SPOTS_FILE=my_spots.txt bash ingame/before_after.sh
#   PAKDIR=… OUT=… CANAL=1 bash ingame/before_after.sh                                          # 運河の見本（温暖・降雪）を空き地に敷いて撮る
# 環境変数: PAKDIR（必須。ami.pak と ami_rail_old.pak がある場所。PAKS で名前を替える）、OUT（必須）、PORT（既定 47200）、GAME_DIR（既定
#   F:/Simutrans/addon_check）、EXE（既定 sim-WinGDI64-OTRPv64.exe）、SAVE（既定 ami_catalog）、ZOOM（既定 3）、SPOTS_FILE（1 行 1 か所:
#   名前 x y。# で始まる行は飛ばす）、CANAL=1（運河・景観の運河を (30,620) 以降に敷いて撮る）。
# ゲームは work/ba_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定 settings.xml.v64 と pak128 などに、PAKDIR の pak だけを足す）で起動し、
# 撮り終えたら閉じて写しを消す（このスクリプトが起動したゲームだけ）。GAME_DIR には書き込まない。
# 降雪側は温暖側の x に 512 を足した所（カタログの決まり）。画面の撮影（--capture）は 704×560 で、上の道具の帯が写る
PAKDIR=${PAKDIR:?PAKDIR を指定する}; OUT=${OUT:?OUT を指定する}; PORT=${PORT:-47200}
GAME_DIR=${GAME_DIR:-F:/Simutrans/addon_check}; EXE=${EXE:-sim-WinGDI64-OTRPv64.exe}; SAVE=${SAVE:-ami_catalog}; ZOOM=${ZOOM:-3}
PAKS=${PAKS:-"ami.pak ami_rail_old.pak"}
source "$(dirname "$0")/mcp_client.sh"
M="python -X utf8 $MCP_CLIENT --port $PORT"
W="work/ba_game/$PORT"

# 既定の座標（温暖 / 降雪。カタログの README の表と catalog.py --list の位置。高速道路の分岐など、ほかの所は SPOTS_FILE で渡す）
SPOTS_DEFAULT="t_x4 118 309
s_x4 630 309
t_m6 17 309
s_m6 529 309
t_cwalk 421 211
s_cwalk 933 211"

stop_game() {
  local win; win=$(cd "$W" 2> /dev/null && pwd -W) || return 0
  powershell.exe -NoProfile -Command "\$d = '$win'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1; rm -rf "$W"
}
if [ "$STOP" = 1 ]; then stop_game; echo "[ba] stopped"; exit 0; fi

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[ba] ポート $PORT で既にゲームが動いている"; exit 1; }
rm -rf "$W"; mkdir -p "$W/save" "$W/addons/pak128" "$OUT"
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$W/" || exit 1
for d in config font themes text script music pak128; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$W/" || exit 1; }
done
printf '\nday_night_shift = 0\n' >> "$W/config/simuconf.tab"
cp "$GAME_DIR/save/$SAVE.sve" "$W/save/" || exit 1
cp "$GAME_DIR/settings.xml.v64" "$W/settings.xml" || exit 1; chmod u+w "$W/settings.xml"
for p in $PAKS; do cp "$PAKDIR/$p" "$W/addons/pak128/" || { stop_game; exit 1; }; done
(cd "$W" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do timeout 20 $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 3; done
$M --run-squirrel "return 1;" > /dev/null 2>&1 || { echo "[ba] ゲームが起動しなかった"; stop_game; exit 1; }

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

if [ -n "$SPOTS_FILE" ]; then SPOTS=$(grep -v '^#' "$SPOTS_FILE"); elif [ "$CANAL" = 1 ]; then SPOTS=""; else SPOTS="$SPOTS_DEFAULT"; fi
echo "$SPOTS" | while read -r name x y; do [ -n "$name" ] && shot "$name" "$x" "$y"; done
stop_game
echo "[ba] done"
