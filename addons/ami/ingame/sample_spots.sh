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
# 路面軌道の見本（ingame/tram_sample.nut）: 下敷きごとに 30 ずつ南（GR 土の上・LO 生活道路・GE 一般道路・EX 高速道路・ST pak128 標準の Road_050）。
#   区画は sample.nut と同じ（AFC・B・DE・G1・G2・I・H0〜H7）。H0〜H7 は土の上と一般道路の上だけ撮る。P は橋脚とのつながり（土の上だけ）
TRAM_SPOTS="GR_P:42:0"
for v in GR:0 LO:30 GE:60 EX:90 ST:120; do
  IFS=: read n dy <<< "$v"
  TRAM_SPOTS="$TRAM_SPOTS ${n}_AFC:8:$((2 + dy)) ${n}_B:3:$((7 + dy)) ${n}_DE:14:$((7 + dy)) ${n}_G1:25:$((3 + dy)) ${n}_G2:25:$((15 + dy)) ${n}_I:5:$((14 + dy))"
  case $n in GR | GE) for j in 0 1 2 3 4 5 6 7; do TRAM_SPOTS="$TRAM_SPOTS ${n}_H$j:$((3 + 8 * j)):$((22 + dy))"; done ;; esac
done
# 歩道の見本（ingame/sidewalk_sample.nut。区画の原点は温暖側・降雪側の原点の 4 南）: 道路の種類ごとに 14 ずつ南（LO 生活道路・GE 一般道路・
#   EX 高速道路・ST pak128 標準の Road_050）。R は交差点の四隅、Q は広場と 1 タイル、S は坂、T は急坂、D は斜めの道路、X は道路・運河の横切り
SIDEWALK_SPOTS=""
for v in LO:0 GE:14 EX:28 ST:42; do
  IFS=: read n dy <<< "$v"
  SIDEWALK_SPOTS="$SIDEWALK_SPOTS ${n}_R:6:$((6 + dy)) ${n}_Q:16:$((5 + dy)) ${n}_S:22:$((7 + dy)) ${n}_T:27:$((7 + dy)) ${n}_D:34:$((7 + dy)) ${n}_X:44:$((6 + dy))"
done
# 盛土の見本（ingame/embankment_sample.nut。区画の原点は温暖側・降雪側の原点の 4 南）: A 線路の高架（東西）、B 線路の高架（南北）、R 道路の高架、
#   M 台の輪、P 窪みの輪、S 坂、T 急坂、D 斜め、X 橋脚と同じタイル
EMBANKMENT_SPOTS="A:8:8 B:20:9 R:8:14 M:28:7 P:36:7 S:45:8 T:51:8 D:58:7 X:37:13"
# 中央分離帯の見本（ingame/divider_sample.nut。道路 2 種を 16 ずつ南へ。GE 一般道路・EX 高速道路）: P2 東西の 4 車線と十字、PN 南北の坂、
#   P0 壁の無い 4 車線、P3 6 車線、PE 高架、R 4 車線の輪（カーブ）、PD 近い斜め
DIVIDER_SPOTS=""
for v in GE:0 EX:16; do
  IFS=: read n dy <<< "$v"
  DIVIDER_SPOTS="$DIVIDER_SPOTS ${n}_P2:5:$((1 + dy)) ${n}_PN:13:$((4 + dy)) ${n}_P0:5:$((5 + dy)) ${n}_P3:5:$((9 + dy)) ${n}_PE:23:$((1 + dy)) ${n}_R:22:$((7 + dy)) ${n}_PD:35:$((3 + dy))"
done
# 路面表示の見本（ingame/marking_sample.nut。#187）: X4 4 車線どうしの十字、X4S スクランブル、X42 4 車線 × 2 車線、X2 2 車線の十字、T2 2 車線の T字路
MARKING_SPOTS="X4:9:9 X4S:31:9 X42:53:8 X2:5:27 T2:19:27"
# 操車場の見本（ingame/yard_sample.nut）: Y1 南北の 1・3 タイル、YP 乗客の駅の隣、YE 東西の 1・3 タイル、YG 並べた留置線、
#   YW 壁つきの基盤の版、YT 列車を止めた操車場、YX 斜め・坂・高架に建てる試し
YARD_SPOTS="Y1:2:3 YP:6:4 YE:3:13 YG:11:4 YW:15:3 YT:19:5 YX:30:4"
case "${NUT:-}" in
  *tram_sample.nut) SPOTS=${SPOTS:-$TRAM_SPOTS} ;;
  *road_sample.nut) SPOTS=${SPOTS:-$ROAD_SPOTS} ;;
  *road_junction_sample.nut) SPOTS=${SPOTS:-$JUNCTION_SPOTS} ;;
  *road_struct_sample.nut) SPOTS=${SPOTS:-$STRUCT_SPOTS} ;;
  *sidewalk_sample.nut) SPOTS=${SPOTS:-$SIDEWALK_SPOTS} ;;
  *embankment_sample.nut) SPOTS=${SPOTS:-$EMBANKMENT_SPOTS} ;;
  *divider_sample.nut) SPOTS=${SPOTS:-$DIVIDER_SPOTS} ;;
  *marking_sample.nut) SPOTS=${SPOTS:-$MARKING_SPOTS} ;;
  *yard_sample.nut) SPOTS=${SPOTS:-$YARD_SPOTS} ;;
esac
SPOTS=${SPOTS:-"AFC:8:2 B:3:7 DE:14:7 G1:25:3 G2:25:15 I:5:14 H0:3:22 H1:11:22 H2:19:22 H3:27:22 H4:35:22 H5:43:22 H6:51:22 H7:59:22$WALLED_SPOTS W1:6:155 W2a:19:153 W2b:19:163 W3:2:163 WE1:6:305 WE2a:19:303 WE2b:19:313 WE3:2:313 $BT_SPOTS"}
