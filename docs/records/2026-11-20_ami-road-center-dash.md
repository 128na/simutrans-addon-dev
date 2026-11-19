# 作業ログ: 高速道路の中央線の破線がタイルの継ぎ目で途切れるのを直す（#21・#22 の続き）

（2026-11-20）

## 目的 / 発端

ユーザーがゲームで高速道路（`ami_road_expressway`）の直線を見て、「直線の中央線の破線がタイル間で連続的になっていない」と指摘した。継ぎ目のところだけ、破線のすき間が他より広く見えた。

## 分かったこと（事実）

- シート `addons/ami/src/ami_road_expressway.png` の直線のセル（`image[ew]`）を 3 枚つないで見ると、どのタイルも破線が 3 本で、継ぎ目のすき間が 2 周期ぶんあった。直線は、タイルの中に 4 本を等間隔に置く作り（`tools/blender/sheetlib/road_parts.py` の `CENTER_DASHES = (4, 3)`）
- 原因は `tools/blender/sheetlib/core.py` の `tile_dashes`。線の中心は `mid = span/2 - (j + 0.5) * period` で、j が増えるほど負の側へ寄る。それなのに、j の範囲を `j0 = floor((ta - span/2) / period) - 1`、`j1 = ceil((tb - span/2) / period) + 1` と、経路の両端 `ta`（負の端）・`tb`（正の端）を逆に使って求めていた
- 直線の経路は `straight` でタイルの外へ `PATH_EXT` = 1.5 延ばすので、TILE = 10 の直線は ta = -6.5、tb = 6.5。このとき j1 = 2 になり、mid = -3.75（負の端に近い 1 本）が抜けていた。坂の直線も同じ（3 本）
- 斜めは、タイルの中の 3 本が前の式でもそろっていた（経路の延長の先の分だけ違う）

## 直したこと

- 範囲を mid の向きに合わせた: `j0 = floor((span/2 - tb) / period - 0.5) - 1`、`j1 = ceil((span/2 - ta) / period - 0.5) + 1`
- bpy なしで同じ式を写して回し、タイルの中の線を確かめた:

  | 経路 | 前の式 | 直した式 |
  |---|---|---|
  | 直線（南北・東西・逆向き。-6.5〜6.5） | 3 本（-4.375〜-3.125 が抜ける） | 4 本（±0.625〜1.875、±3.125〜4.375） |
  | 斜め（延長なし・延長あり・逆向き） | 3 本 | 3 本（同じ位置。延長の先は両端とも続く） |

- 描き直したシート: `ami_road_expressway`（通常の版）。前のシートとセルごとに比べ、違うのは中央線の破線の 1 本ぶん（1 セル 20〜43 px）だけだった。dat は変わらない
- `tile_dashes` を使うのは `assemble.py` の中央線（`"cdash"`）だけ。中央線が破線なのは高速道路だけで、生活道路・一般道路のシートは変わらない
- 基盤・高架・橋・トンネルの版は、別のブランチ（道路の構造物、#22）で描き直す

## 確かめた絵

- シート: 直線のセル（`image[ew]`）を 3 枚つないだ絵で、前はタイルごとに 3 本と 2 周期のすき間（`addons/ami/docs/road_EX_dash_sheet_before.png`）、後は 4 本ずつ等間隔（`road_EX_dash_sheet_after.png`。下の段は坂のセルの前と後で、3 本から 4 本になった）
- ゲーム（2026-11-20、`OTRPv64_3.exe`、`flat_512.sve`、`NUT=ingame/road_sample.nut SEASONS=temperate:20:20 bash ingame/sample_parallel.sh`、拡大率 3 の画面を 4 倍）: 高速道路の区画 K の東西の直線（`road_EX_dash_straight_ew_zoom.png`）、区画 AFC の南北の直線（`road_EX_dash_straight_ns_zoom.png`）、区画 DE の坂と平地の継ぎ目（`road_EX_dash_slope_zoom.png`）、区画 G1 の近い斜め（`road_EX_dash_close_diag_zoom.png`）。どれも継ぎ目で破線の間隔がそろっていた
- 2026-11-19 の受け入れの記録（ACCEPTANCE の 1-1）では「途切れない」と書いていたが、前の確認画像（`road_EX_dash_zoom.png`）は直線と斜めの継ぎ目を見たもので、直線どうしの継ぎ目のすき間を見落としていた
