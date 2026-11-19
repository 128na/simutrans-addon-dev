# 作業ログ: AMI の道路の基盤の版・高架の版からも分岐の絵を外す（#22 の続き）

（2026-11-20）

## 目的 / 発端

[2026-11-20_ami-road-no-switch.md](2026-11-20_ami-road-no-switch.md) で、道路の通常の版の dat から分岐の絵（1・2 の 10 枚）を外した（ユーザーの決定）。同じ `ROAD_SWITCH_IMAGES` は、waytype が `road` の way 全部に効くので、基盤の 4 版・高架の 4 版の dat からも外れる。そのことを確かめた。

## 直したこと

- `python -X utf8 blender/ami_dat.py` で dat を書き直した。道路の基盤の版・高架の版の 24 個の dat から、`image[nse1]`〜`image[nsew2]`（夏・雪の 20 行）が消えた
- 橋脚の way（`ami_pier_road`、`tram_track`）は変えていない。分岐の絵は T字・十字と同じ柱のセルを指すので、見た目は変わらない
- 描いたシート（基盤の版・高架の版の分岐のセル）と、見本の区画 IB・IV は残した

## 確かめたこと

（2026-11-20、`OTRPv64_3.exe`、`flat_512.sve`、`sample_parallel.sh` で `road_struct_sample.nut` を温暖側・降雪側に敷いた。210 画面）

- `makeobj dump dist/ami_road.pak`: 道路の way 27 個（通常・基盤・高架）の画像の並びは、どれも 16 枚
- 区画 IB・IV: 3 種とも、T字 4 種と十字を 1・2 に固定しても、1 と 2 が同じ番号（`[check] … IB nse1=… nse2=…`）。画面でも通常の T字・十字（`addons/ami/docs/road_GE_noswitch_struct.png`）
- 高架の区画 L（`elevL`）: 十字は東西とも通常の十字（`west`・`east`・`plain` が同じ番号）。横切る道路はふさがらない（`road_GE_noswitch_struct.png` の `V_L`、生活道路・高速道路と降雪側は `addons/ami/docs/road_LO_EX_noswitch.png`）

タイルの詳細ダイアログで選ぶときの見た目は見ていない（MCP ではダイアログを開けない）。
