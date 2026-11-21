#!/bin/bash
# アイコン・カーソル（#25）をゲームで撮る: 道具のメニュー（鉄道・道路・路面軌道・船）の窓と、道具を選んで地図を押したときのカーソル。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe PORT=47200 bash ingame/icon_capture.sh
# ゲームは work/icon_game/<PORT>/ の写しで起動し、GAME_DIR には書き込まない。写しからは AMI のほかのアドオンの pak を外す
# （検証用のフォルダには、古い AMI の写し amib.pak が入っていて、同じ形のアイコンが混ざる）。終わったらゲームを閉じる。
# 撮った画面は OUT（既定 work/icons/）に、menu_<名前>.png（窓の切り抜きを 2 倍）と cursor_<名前>.png（カーソルの辺りを 2 倍）で置く。
# メニューの中の位置（列, 行）は、pak128 標準と AMI を入れたときの並び（2026-11-21）。並びが変わったら CURSORS を直す
GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE に実行ファイルの名前を指定する}
PORT=${PORT:?PORT に MCP のポートを指定する}
SAVE=${SAVE:-flat_512}
PAK=${PAK:-dist/ami.pak}
OUT=${OUT:-work/icons}
B=${BLENDER:-D:/bin/blender/blender.exe}
source "$(dirname "$0")/mcp_client.sh"
M="python -X utf8 $MCP_CLIENT --port $PORT"
WORK="work/icon_game/$PORT"
[ -f "$PAK" ] || { echo "[icon] $PAK が無い"; exit 1; }
$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[icon] ポート $PORT で既にゲームが動いている"; exit 1; }

stop_game() {
  powershell.exe -NoProfile -Command "\$d = '$WORK_WIN'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}
rm -rf "$WORK"
mkdir -p "$WORK/save" "$OUT"
WORK_WIN=$(cd "$WORK" && pwd -W)
trap stop_game EXIT
trap 'exit 130' INT TERM
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$WORK/" || exit 1
for d in config font themes text script music pak128 addons; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$WORK/" || exit 1; }
done
rm -f "$WORK"/addons/pak128/ami*.pak
cp "$GAME_DIR/save/$SAVE.sve" "$WORK/save/" || exit 1
cp "$PAK" "$WORK/addons/pak128/ami.pak" || exit 1
printf '\nday_night_shift = 0\n' >> "$WORK/config/simuconf.tab"
[ -f "$GAME_DIR/settings.xml" ] && { cp "$GAME_DIR/settings.xml" "$WORK/settings.xml"; chmod u+w "$WORK/settings.xml"; }
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for r in $(seq 1 120); do timeout 10 $M --timeout 5 --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 1; done
sleep 3
OUT_WIN=$(cd "$OUT" && pwd -W)
TMP="$WORK_WIN/_screen.png"  # 画面の一時ファイル（ゲームの写しと一緒に消える）

crop() {  # crop <入力> <出力> <x0> <y0> <x1> <y1>（2 倍の最近傍）
  "$B" -b --factory-startup --python-expr "
import bpy, numpy as np, sys
i = bpy.data.images.load(r'$1'); w, h = i.size; x = np.empty(w * h * 4, np.float32); i.pixels.foreach_get(x)
x = np.flipud(x.reshape(h, w, 4))[max($4, 0):min($6, h), max($3, 0):min($5, w)].repeat(2, 0).repeat(2, 1)
o = bpy.data.images.new('o', x.shape[1], x.shape[0]); o.pixels.foreach_set(np.flipud(x).ravel())
o.filepath_raw = r'$2'; o.file_format = 'PNG'; o.save()" > /dev/null 2>&1
}

open_menu() {  # open_menu <上の道具の列の x> → 窓の x y w h を出す
  $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(40, 40, 0)); return 1;" > /dev/null
  sleep 1
  $M --run-squirrel "gui.click($1, 15); return 1;" > /dev/null
  sleep 1
  $M --run-squirrel 'foreach (w in gui.get_windows()) if (w.top) return w.bounds.x + " " + w.bounds.y + " " + w.bounds.w + " " + w.bounds.h; return "";' |
    python -c "import sys, json; print(json.loads(sys.stdin.read())['result'])"
}

# メニュー: 名前 と 上の道具の列の x
MENUS="rail:145 road:275 tram:240 ship:305"
for e in $MENUS; do
  n=${e%%:*}; tx=${e##*:}
  read wx wy ww wh <<< "$(open_menu "$tx")"
  $M --capture "$TMP" > /dev/null
  crop "$TMP" "$OUT_WIN/menu_$n.png" "$wx" "$wy" $((wx + ww)) $((wy + wh))
  echo "[icon] menu_$n.png ($wx,$wy,$ww,$wh)"
done

# カーソル: 名前 メニュー 列 行。道具を選び、窓の外の地図を 1 回押す（way の道具は始点を置き、その上にカーソルの絵が出る）
CURSORS="rail_ballast:rail:7:0 rail_ballast_base_back:rail:8:0 rail_ballast_elev_back:rail:5:2 rail_ballast_bridge:rail:1:4
rail_ballast_tunnel:rail:18:4 rail_slab:rail:9:1 wall_rail_back:rail:5:6 wall_rail_twin:rail:9:6 wall_rail_single_catenary:rail:13:6
road_local:road:3:0 road_general_base_back:road:1:2 road_expressway_elev_single:road:11:2 road_general_bridge:road:2:3
wall_road_twin:road:2:4 tram:tram:4:0 pier_rail:tram:0:0 pier_rail_gate:tram:1:0 pier_road:tram:2:0 sidewalk:ship:0:0"
for e in $CURSORS; do
  IFS=: read n menu col row <<< "$e"
  for m in $MENUS; do [ "${m%%:*}" = "$menu" ] && tx=${m##*:}; done
  read wx wy ww wh <<< "$(open_menu "$tx")"
  $M --run-squirrel "gui.click($((wx + 16 + 32 * col)), $((wy + 37 + 32 * row))); return 1;" > /dev/null
  sleep 1
  $M --run-squirrel "gui.click(660, 490); return 1;" > /dev/null
  sleep 1
  $M --capture "$TMP" > /dev/null
  crop "$TMP" "$OUT_WIN/cursor_$n.png" 560 400 704 540
  [ -f "$OUT/cursor_$n.png" ] || { echo "[icon] cursor_$n.png を書けない"; exit 1; }
  echo "[icon] cursor_$n.png"
done
