#!/bin/bash
# 他のアドオン・pak128 標準とのつなぎ目を撮って、blender/seam_judge.py で判定する（ingame/seam.nut・ingame/road_seam.nut を敷いた後）。
# BASES の「名前:y」ごとに、東西の直線(_ew)・南北の直線(_ns)・斜め(_dg)・坂(_sl)を等倍で撮り、
# work/seam/<名前>_<種類>.png（画面）・.txt（タイル一覧）・_judge.png（継ぎ目の拡大）を書く。
# 使い方（アドオンのディレクトリで、ゲームを -mcp-port 47123 で起動しておく）: bash ingame/seam_check.sh
M="python ${MCP_CLIENT:-E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py} --port ${PORT:-47123}"
B=${BLENDER:-D:/bin/blender/blender.exe}
OUT=${OUT:-work/seam}
mkdir -p "$OUT"
for base in ${BASES:-road:140 expwy:160 def:180 old:100 new:120}; do
  IFS=: read n y <<< "$base"
  case $n in old|new) WT=wt_rail;; *) WT=wt_road;; esac
  for spec in ${KINDS:-ew:136:0 ns:146:6 dg:133:7 sl:152:2}; do
    IFS=: read k x dy <<< "$spec"
    jy=$((y + dy))
    $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($x,$jy,0)); return 1;" >/dev/null 2>&1
    sleep 1
    $M --capture "$OUT/${n}_$k.png" >/dev/null 2>&1
    $M --run-squirrel "local s=\"\"; for(local yy=$jy-6;yy<=$jy+6;yy++) for(local xx=$x-6;xx<=$x+6;xx++){ local t=square_x(xx,yy).get_ground_tile(); local w=t.get_way($WT); if(w!=null) s+=xx+\" \"+yy+\" \"+t.z+\" \"+t.get_slope()+\" \"+w.get_dirs()+\" \"+w.get_desc().get_name()+\"\n\"; } return s" 2>/dev/null \
      | python -c "import sys,json; print(json.loads(sys.stdin.read())['result'], end='')" > "$OUT/${n}_$k.txt"
    "$B" -b --factory-startup --python blender/seam_judge.py -- "$OUT/${n}_$k.png" "$OUT/${n}_$k.txt" "$OUT/${n}_${k}_judge.png" "$x,$jy" 2>&1 \
      | grep "^\[" | sed "s/^/$n $k /"
  done
done
