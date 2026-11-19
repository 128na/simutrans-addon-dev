# sample_capture.sh と sample_parallel.sh が読む、撮る区画の一覧。SPOTS を渡すとそれだけ撮る
# 名前:区画の原点からの x:y（sample.nut の区画）
#   H0〜H7 は分岐の自動選択の 8 通り（nse2・nse1・nsw2・nsw1・new2・new1・sew2・sew1 の順。sample.nut の AUTO）
#   S・B・C・F は基盤の版の single・back・center・front の区画（AFC・B・DE と、分岐 H0）。W1〜W3 は区画 W（y=150〜）
WALLED_SPOTS=""
for v in S:30 B:60 C:90 F:120; do
  IFS=: read n dy <<< "$v"
  WALLED_SPOTS="$WALLED_SPOTS ${n}_AFC:8:$((2 + dy)) ${n}_B:3:$((7 + dy)) ${n}_DE:14:$((7 + dy)) ${n}_H0:3:$((22 + dy))"
done
# 架線つきの壁（sample.nut の CATENARY）: SE・BE・CE・FE は single・back・center・front の区画（y=180〜）、WE1〜WE3 は区画 WE（y=300〜）
for v in SE:180 BE:210 CE:240 FE:270; do
  IFS=: read n dy <<< "$v"
  WALLED_SPOTS="$WALLED_SPOTS ${n}_AFC:8:$((2 + dy)) ${n}_B:3:$((7 + dy)) ${n}_DE:14:$((7 + dy)) ${n}_H0:3:$((22 + dy))"
done
# 高架（sample.nut の ELEVATED。地上の区画の東 80）: VS・VB・VC・VF は single・back・center・front の区画（y=0〜）、
# WV1〜WV3 は区画 WV（y=120〜）、WVE1〜WVE3 は区画 WVE（y=150〜）、VSE は架線つきの壁の single（y=180〜）、J はつなぎ目（y=210〜）
for v in VS:0 VB:30 VC:60 VF:90 VSE:180; do
  IFS=: read n dy <<< "$v"
  WALLED_SPOTS="$WALLED_SPOTS ${n}_AFC:88:$((2 + dy)) ${n}_B:83:$((7 + dy)) ${n}_DE:94:$((7 + dy)) ${n}_IH:85:$((18 + dy))"
done
# 門型の橋脚（sample.nut の lay_gate。地上の区画の東 160）: G_* は高架の single の区画、GWV1〜GWV3 は区画 WV の並び（y=30〜）、
# GR1〜GR3 は道路の区画 R（y=63〜）
WALLED_SPOTS="$WALLED_SPOTS G_AFC:168:2 G_B:163:7 G_DE:174:7 G_IH:165:18 GWV1:166:35 GWV2a:179:33 GWV2b:179:43 GWV3:162:43 GR1:166:68 GR2:177:65 GR3:188:65"
WALLED_SPOTS="$WALLED_SPOTS WV1:86:125 WV2a:99:123 WV2b:99:133 WV3:82:133 WVE1:86:155 WVE2a:99:153 WVE2b:99:163 WVE3:82:163 J:88:214"
# 橋とトンネル（sample.nut の lay_bt。原点は地上の区画から東 160・南 130）: BT_B1 は平地から立ち上がる橋（東西）、BT_B1ns は南北、
# BT_B2 は坂から始まる橋（東西の 1 段・2 段）、BT_B2ns は南北、BT_B4 は高架と橋のつなぎ目、
# BT_T1・BT_T1ns は壁だけのトンネル、BT_T2・BT_T2ns は架線つき、BT_T3 は複線
BT_SPOTS="BT_B1:167:131 BT_B1ns:179:137 BT_B2:164:151 BT_B2ns:186:150 BT_B4:168:168 BT_T1:164:174 BT_T1ns:182:172 BT_T2:164:180 BT_T2ns:187:178 BT_T3:164:186"
# 道路の見本（ingame/road_sample.nut。NUT に渡すと、SPOTS を渡さなければこちらを撮る）: 種類ごとに 30 ずつ南（LO 生活道路・GE 一般道路・EX 高速道路）。
#   AFC・B・DE・G1・G2 は線路と同じ区画、HV・HH は分岐の自動選択（2 本を並べた渡り口。南北・東西）、K は pak128 標準の道路とのつなぎ目、L は隣り合う十字、
#   I0〜I4 は分岐の絵の固定（nse・new・nsw・sew・nsew の 1・2）
ROAD_SPOTS=""
for v in LO:0 GE:30 EX:60; do
  IFS=: read n dy <<< "$v"
  ROAD_SPOTS="$ROAD_SPOTS ${n}_AFC:8:$((2 + dy)) ${n}_B:3:$((7 + dy)) ${n}_DE:14:$((7 + dy)) ${n}_G1:25:$((3 + dy)) ${n}_G2:25:$((15 + dy))"
  ROAD_SPOTS="$ROAD_SPOTS ${n}_HV:34:$((4 + dy)) ${n}_HH:38:$((12 + dy)) ${n}_K:52:$((3 + dy)) ${n}_L:50:$((15 + dy))"
  for j in 0 1 2 3 4; do ROAD_SPOTS="$ROAD_SPOTS ${n}_I$j:$((5 + 12 * j)):$((23 + dy))"; done
done
# 交差点の組み合わせ（ingame/road_junction_sample.nut）: 種類ごとに 22 ずつ南。名前は「南北の車線数x東西の車線数」（道路 1 本が 2 車線）
JUNCTION_SPOTS=""
for v in LO:0 GE:22 EX:44; do
  IFS=: read n dy <<< "$v"
  k=0
  for cb in 2:1 1:2 3:1 1:3 2:2 2:3 3:2 3:3; do
    IFS=: read a b <<< "$cb"
    JUNCTION_SPOTS="$JUNCTION_SPOTS ${n}_$((2 * a))x$((2 * b)):$((12 * k + 3 + a / 2)):$((4 + b / 2 + dy))"
    k=$((k + 1))
  done
  # T字の組み合わせ（road_junction_sample.nut の TEES。x=96 から 12 ずつ）
  JUNCTION_SPOTS="$JUNCTION_SPOTS ${n}_T4x2:100:$((4 + dy)) ${n}_T4x4:112:$((5 + dy))"
done
# 道路の構造物の見本（ingame/road_struct_sample.nut）: 種類ごとに 30 ずつ南（LO・GE・EX）。
#   WA_* は地上の壁（AFC・B・DE・G1・G2）、WP・WP3・WP2 は地上の複線（基盤の版）、V_* は高架（AFC・B・DE と隣り合う十字 L）、VP1〜VP3 は高架の複線、
#   B1・B1ns・B2・B4 は橋、T1・T1ns・T3 はトンネル、P1〜P3 は橋脚のつながり（pak128 の道路・AMI の道路・線路）、
#   IB0〜IB4・IV0〜IV4 は分岐の絵の固定（基盤の版 single・高架 single。nse・new・nsw・sew・nsew の 1 と 2 を 1 画面に 2 つずつ）
STRUCT_SPOTS=""
for v in LO:0 GE:30 EX:60; do
  IFS=: read n dy <<< "$v"
  STRUCT_SPOTS="$STRUCT_SPOTS ${n}_WA_AFC:8:$((2 + dy)) ${n}_WA_B:3:$((7 + dy)) ${n}_WA_DE:14:$((7 + dy)) ${n}_WA_G1:25:$((3 + dy)) ${n}_WA_G2:25:$((15 + dy))"
  STRUCT_SPOTS="$STRUCT_SPOTS ${n}_WP:38:$((5 + dy)) ${n}_WP3:34:$((13 + dy)) ${n}_WP2:40:$((15 + dy)) ${n}_V_AFC:58:$((2 + dy)) ${n}_V_B:53:$((7 + dy)) ${n}_V_DE:64:$((7 + dy)) ${n}_V_L:72:$((4 + dy))"
  STRUCT_SPOTS="$STRUCT_SPOTS ${n}_VP1:96:$((5 + dy)) ${n}_VP2:109:$((3 + dy)) ${n}_VP3:92:$((13 + dy)) ${n}_B1:132:$((1 + dy)) ${n}_B1ns:144:$((7 + dy)) ${n}_B2:129:$((19 + dy))"
  STRUCT_SPOTS="$STRUCT_SPOTS ${n}_B4:133:$((24 + dy)) ${n}_T1:153:$((19 + dy)) ${n}_T1ns:162:$((5 + dy)) ${n}_T3:153:$((24 + dy)) ${n}_P1:170:$((5 + dy)) ${n}_P2:181:$((2 + dy)) ${n}_P3:190:$((5 + dy))"
  for j in 0 1 2 3 4; do STRUCT_SPOTS="$STRUCT_SPOTS ${n}_IB$j:$((53 + 12 * j)):$((20 + dy)) ${n}_IV$j:$((53 + 12 * j)):$((25 + dy))"; done
done
case "${NUT:-}" in
  *road_sample.nut) SPOTS=${SPOTS:-$ROAD_SPOTS} ;;
  *road_junction_sample.nut) SPOTS=${SPOTS:-$JUNCTION_SPOTS} ;;
  *road_struct_sample.nut) SPOTS=${SPOTS:-$STRUCT_SPOTS} ;;
esac
SPOTS=${SPOTS:-"AFC:8:2 B:3:7 DE:14:7 G1:25:3 G2:25:15 I:5:14 H0:3:22 H1:11:22 H2:19:22 H3:27:22 H4:35:22 H5:43:22 H6:51:22 H7:59:22$WALLED_SPOTS W1:6:155 W2a:19:153 W2b:19:163 W3:2:163 WE1:6:305 WE2a:19:303 WE2b:19:313 WE3:2:313 $BT_SPOTS"}
