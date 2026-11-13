#!/bin/bash
# 全方位の表示確認: ingame/full.nut のレイアウトを敷き、way ごとに 5 か所を撮って work/full/<way>.png に横に並べる。
# 使い方（アドオンのディレクトリで、ゲームを -mcp-port 47123 で起動しておく。雪は -load flat_snow で起動して OUT=work/full_snow）:
#   bash ingame/full_check.sh
# 並べた画像を目で見る（絵の欠け・縦線・段・すき間・基盤の突き抜け）。見る観点は ACCEPTANCE.md の「全方位の表示確認」。
M="python ${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py} --port ${PORT:-47123}"
B=${BLENDER:-D:/bin/blender/blender.exe}
OUT=${OUT:-work/full}
mkdir -p "$OUT/shots"
$M --run-squirrel "$(cat ingame/full.nut)" | head -c 2000; echo
WAYS="bpoc_track bpoc_track_old bpoc_track_trial bpoc_track_wall_single bpoc_track_wall_back bpoc_track_wall_center bpoc_track_wall_front bpoc_track_elev_single bpoc_track_elev_back bpoc_track_elev_center bpoc_track_elev_front"
i=0
for w in $WAYS; do
  ox=$((5 + (i % 4) * 22)); oy=$((130 + (i / 4) * 14)); i=$((i + 1))
  files=""
  for spot in A:2:1 B:3:7 C:10:2 D:11:7 E:17:7; do
    IFS=: read k x y <<< "$spot"
    $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((ox + x)),$((oy + y)),0)); return 1;" >/dev/null 2>&1
    sleep 1
    $M --capture "$OUT/shots/${w}_$k.png" >/dev/null 2>&1
    files="$files $OUT/shots/${w}_$k.png"
  done
  "$B" -b --factory-startup --python blender/hcat.py -- "$OUT/$w.png" $files >/dev/null 2>&1
  echo "[full] $OUT/$w.png"
done
