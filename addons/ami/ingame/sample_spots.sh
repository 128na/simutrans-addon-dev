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
SPOTS=${SPOTS:-"AFC:8:2 B:3:7 DE:14:7 G1:25:3 G2:25:15 I:5:14 H0:3:22 H1:11:22 H2:19:22 H3:27:22 H4:35:22 H5:43:22 H6:51:22 H7:59:22$WALLED_SPOTS W1:6:155 W2a:19:153 W2b:19:163 W3:2:163 WE1:6:305 WE2a:19:303 WE2b:19:313 WE3:2:313 $BT_SPOTS"}
