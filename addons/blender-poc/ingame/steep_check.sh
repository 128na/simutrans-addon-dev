#!/bin/bash
# 坂・急坂の十字を撮り、直線の坂のタイルでレールが道床の中ほどにあるか・まくらぎが見えるかを blender/slope_measure.py で測る。
# このアドオンの線路は、ゲームの画面と予想図の違い（blender/ingame_diff.py）も出す。
# 見本: 急坂は ingame/steep.nut（y=60、ゲームを起動し直したら流し直す）、このアドオンの1段の坂は ingame/all_dirs.nut（flat.sve に保存済み）。
# work/steep/<名前>.png（画面）・.txt（タイル一覧）・_measure.png（測ったタイルの拡大）・_diff.png（予想図との違い）を書く。
# 使い方（アドオンのディレクトリで、ゲームを -mcp-port 47123 で起動しておく）: bash ingame/steep_check.sh
# 出力の [slope] の行が坂のタイルごとの結果（寄り・まくらぎの濃淡・OK/NG）。[diff] は 0 px が合格。
M="python ${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py} --port ${PORT:-47123}"
B=${BLENDER:-D:/bin/blender/blender.exe}
OUT=${OUT:-work/steep}
mkdir -p "$OUT"
# 名前:x:y:シート:位置合わせ。シートが - なら手本（測るだけ）。
# 位置合わせが - なら、このアドオンの平らなタイルで画面の位置を探す。名前を書くと、その見本で探したずれを使う
# （手本だけの画面は絵で位置を探せない。地形と jump が同じ見本なら、画面の位置も同じ）
for spec in ${SPECS:-steep_new:20:60:track:- steep_old:30:60:track_old:- steep_rail100:40:60:-:steep_new slope_new:40:29:track:- slope_old:66:29:track_old:- slope_rail100:50:60:-:slope_new}; do
  IFS=: read n x y sheet from <<< "$spec"
  $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($x,$y,0)); return 1;" >/dev/null 2>&1
  sleep 2
  $M --capture "$OUT/$n.png" >/dev/null 2>&1
  # 十字の周りだけ（all_dirs.nut の見本は、隣の輪や箱が同じ画面に入る）
  $M --run-squirrel "local s=\"\"; for(local yy=$y-4;yy<=$y+4;yy++) for(local xx=$x-4;xx<=$x+4;xx++){ local t=square_x(xx,yy).get_ground_tile(); local w=t.get_way(wt_rail); if(w!=null) s+=xx+\" \"+yy+\" \"+t.z+\" \"+t.get_slope()+\" \"+w.get_dirs()+\" \"+w.get_desc().get_name()+\"\n\"; } return s" 2>/dev/null \
    | python -c "import sys,json; print(json.loads(sys.stdin.read())['result'], end='')" > "$OUT/$n.txt"
  off=""
  [ "$from" != "-" ] && off=$(cat "$OUT/$from.off" 2>/dev/null)
  SLOPE_OFFSET=$off "$B" -b --factory-startup --python blender/slope_measure.py -- "$OUT/$n.png" "$OUT/$n.txt" "$x,$y" "$OUT/${n}_measure.png" 2>&1 \
    | grep "^\[" > "$OUT/$n.log"
  sed "s/^/$n /" "$OUT/$n.log"
  sed -n 's/^\[locate\] .*ずれ \(-\{0,1\}[0-9]*,-\{0,1\}[0-9]*\).*/\1/p' "$OUT/$n.log" > "$OUT/$n.off"
  if [ "$sheet" != "-" ]; then
    cut -d" " -f1-5 "$OUT/$n.txt" > "$OUT/${n}_tiles.txt"
    INGAME_OFFSET=$(cat "$OUT/$n.off") "$B" -b --factory-startup --python blender/ingame_diff.py -- "$OUT/$n.png" "$sheet" "$OUT/${n}_tiles.txt" "$OUT/${n}_diff.png" "$x,$y" 2>&1 \
      | grep "^\[" | sed "s/^/$n /"
  fi
done
