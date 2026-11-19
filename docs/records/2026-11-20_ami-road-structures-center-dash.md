# 作業ログ: 高速道路の構造物の版で、中央線の破線の抜けを直す（#22 の続き）

（2026-11-20）

## 目的 / 発端

高速道路の通常の版で、直線と坂のタイルの中央線の破線が 1 本抜けていた（4 本のはずが 3 本で、タイルの継ぎ目で 2 周期あいた）。原因と直し方は [2026-11-20_ami-road-center-dash.md](2026-11-20_ami-road-center-dash.md)（`tools/blender/sheetlib/core.py` の `tile_dashes` の範囲の誤り）。同じ道具で描く構造物の版も描き直した。

## 直したこと

- 描き直したシート: `ami_road_expressway_base_<single|back|center|front>`・`ami_road_expressway_elev_<single|back|center|front>`・`ami_road_expressway_bridge`・`ami_road_expressway_tunnel`（`render_parallel.py` で 10 枚、57 秒）
- 前のシートとセルごとに比べ、違うのは中央線の破線の 1 本ぶんだけだった（1 セル 44 px 以下。基盤・高架は 57 セル、橋は 37 セル、トンネルは 7 セル）。dat は変わらない

## 確かめた絵

ゲーム（2026-11-20、`OTRPv64_3.exe`、`flat_512.sve`、`NUT=ingame/road_struct_sample.nut SEASONS=temperate:20:20 bash ingame/sample_parallel.sh`、拡大率 3 の画面を 4 倍）で、高速道路の区画を撮った。

- 橋（区画 B1）: 平地 → 坂 → 橋の床 → 坂 → 平地で、継ぎ目でも破線の間隔がそろっていた（`addons/ami/docs/road_EX_dash_bridge_zoom.png`）
- トンネル（区画 T1）: 口の前の掘り割りから坑口まで、間隔がそろっていた（`road_EX_dash_tunnel_zoom.png`）
- 高架の複線（区画 WV1）: 直線と斜めの継ぎ目を含め、間隔がそろっていた（`road_EX_dash_elev_zoom.png`）
- 高架の区画 AFC・DE（斜め・坂）と橋の区画 B1ns・B2、トンネルの区画 T1ns も撮って、目で見た（画像は残していない）
- 画面で横向きの坂（東西の 2 段の坂）で破線が灰色に薄く見えるのは、前から知られている作り（README の「未確認・未対応」）で、今回の直しとは関係ない
