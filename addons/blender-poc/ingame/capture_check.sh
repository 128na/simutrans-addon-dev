#!/bin/sh
# 等倍で見本の各部分を撮り、タイル一覧を書き出して blender/ingame_diff.py で比べる。
# 使い方（アドオンのディレクトリで、ゲームを -mcp-port 47123 で起動しておく）: sh ingame/capture_check.sh
M=${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py}
B=${BLENDER:-D:/bin/blender/blender.exe}
mkdir -p work/check
# 見本の左上 x0（ingame/all_dirs.nut と同じ）、y0=20
for spec in ${SPECS:-track:bpoc_track:20 track_old:bpoc_track_old:46 road:bpoc_road:72 expressway:bpoc_expressway:98}; do
  sheet=${spec%%:*}; rest=${spec#*:}; way=${rest%%:*}; x0=${rest#*:}
  case $sheet in track*) WT=wt_rail;; *) WT=wt_road;; esac
  # 見る場所（見本の中の位置）: 行き止まりと直線 / 輪 / 箱と十字 / 斜め2系統 / 坂
  for area in ${AREAS:-ends:3:2 loop:2:8 box:11:9 dg1:10:2 dg2:16:2 slope:20:9}; do
    an=${area%%:*}; r=${area#*:}; ax=$((x0 + ${r%%:*})); ay=$((20 + ${r#*:}))
    python "$M" --port 47123 --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($ax,$ay,0)); return 1" >/dev/null 2>&1
    sleep 2
    python "$M" --port 47123 --capture "work/check/${sheet}_$an.png" >/dev/null 2>&1
    python "$M" --port 47123 --run-squirrel "local s=\"\"; for(local y=$ay-5;y<=$ay+5;y++) for(local x=$ax-5;x<=$ax+5;x++){ local t=square_x(x,y).get_ground_tile(); local w=t.get_way($WT); if(w!=null && w.get_desc().get_name()==\"$way\") s+=x+\" \"+y+\" \"+t.z+\" \"+t.get_slope()+\" \"+w.get_dirs()+\"\n\"; } return s" 2>/dev/null \
      | python -c "import sys,json; print(json.loads(sys.stdin.read())['result'], end='')" > "work/check/${sheet}_$an.txt"
    "$B" -b --factory-startup --python blender/ingame_diff.py -- "work/check/${sheet}_$an.png" "$sheet" "work/check/${sheet}_$an.txt" "work/check/${sheet}_${an}_diff.png" "$ax,$ay" 2>&1 | grep "^\[" | sed "s/^/$sheet $an /"
  done
done
