#!/bin/bash
# 他のアドオン・pak128 標準とのつなぎ目を撮る（ingame/road_seam.nut・ingame/seam.nut を敷いた後）。
# BASES の「名前:y」ごとに、東西の直線(_ew)・南北の直線(_ns)・斜め(_dg)・坂(_sl)を等倍で撮り work/sis/<名前>_<種類>.png に書く
M="python E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py --port ${PORT:-47123}"
OUT=${OUT:-work/sis}
mkdir -p $OUT
for base in ${BASES:-road:140 expwy:160 def:180 old:100 new:120}; do
  IFS=: read n y <<< "$base"
  for spec in ew:136:0 ns:146:6 dg:133:7 sl:152:2; do
    IFS=: read k x dy <<< "$spec"
    $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($x,$((y + dy)),0)); return 1;" >/dev/null 2>&1
    sleep 1
    $M --capture $OUT/${n}_$k.png >/dev/null 2>&1
  done
done
