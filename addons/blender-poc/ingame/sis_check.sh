#!/bin/bash
# SIS・pak128 標準の道路とのつなぎ目を撮る（ingame/road_seam.nut を敷いた後）。work/sis/<名前>.png
# e/r/d = 東西の直線（高速道路・一般道・標準の道路）、en/rn/dn = 南北、eg/rg/dg = 斜め、es/rs/ds = 坂
M="python E:/addon_dev/simutrans/.agents/skills/simutrans-mcp-gui-debug/scripts/mcp_client.py --port ${PORT:-47123}"
mkdir -p work/sis
for spec in e:136:160 r:136:140 d:136:180 en:146:166 rn:146:146 dn:146:186 eg:133:167 rg:133:147 dg:133:187 es:152:162 rs:152:142 ds:152:182; do
  IFS=: read n x y <<< "$spec"
  $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($x,$y,0)); return 1;" >/dev/null 2>&1
  sleep 1
  $M --capture work/sis/$n.png >/dev/null 2>&1
done
