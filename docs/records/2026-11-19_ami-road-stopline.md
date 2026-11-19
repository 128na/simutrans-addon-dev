# 作業ログ: AMI の道路の T字の「2」を十字の形と停止線に（#21 の続き）

（2026-11-19）

## 目的 / 発端

#21 で、十字が隣り合うとき十字のタイルに出る T字の「2」の絵（`nse2`・`nsw2`・`new2`・`sew2`）が T字の形で、横切る道路をふさいで見えた（[2026-11-19_ami-road.md](2026-11-19_ami-road.md)）。ユーザーの決定（2026-11-19）で、「2」を十字の形にして停止線を引く。左側通行で、右側通行へ切り替えられるフラグを持たせる。あわせて、道路を 3 本以上並べた交差点で本体がどの絵を選ぶかを、ゲームで確かめる（ユーザーの依頼）。

## 分かったこと（事実）

- 本体（`../simutrans` の `boden/wege/weg.cc` の `select_switch_road_image` の `ribi_t::all`）は、ex 画像の無い way の十字で、隣を東 → 西 → 北 → 南の順に見て、最初に T字・十字だった向きの「2」を選ぶ。見本で、組み合わせごとの十字の絵は次のとおり（3 種とも同じ。北の行から、西から東へ）:
  - 4×2（南北 2 本 × 東西 1 本）: `nse2 nsw2`
  - 2×4: `sew2 / new2`
  - 6×2: `nse2 nse2 nsw2`
  - 2×6: `sew2 / new2 / new2`
  - 4×4: `nse2 nsw2 / nse2 nsw2`
  - 4×6: `nse2 nsw2` の 3 行、6×4: `nse2 nse2 nsw2` の 2 行、6×6: `nse2 nse2 nsw2` の 3 行
- 南北に並べた隣（東・西）が先に見られるので、南北・東西とも並べた交差点では東西に並べた向きは使われない。停止線が正しく出るのは 4×2・2×4 だけで、ほかは交差点の内側の腕や出ていく車線の側にも出る（`addons/ami/docs/road_GE_4x4_stopline_zoom.png`・`road_GE_2x6_stopline_zoom.png`・`road_GE_6x6_stopline_zoom.png`）。コーディネーターがソースから読んだ予想と同じ
- 停止線を引かず「2」を通常の十字と同じ絵にすると、どの組み合わせも東西の中央線が通り南北が点線の十字が並ぶ（`road_GE_4x2_stopline_off_zoom.png`・`road_GE_6x6_stopline_off_zoom.png`）

## 判断したこと

- 寸法: 幅 0.35（約 2px）、線の中心はタイルの中心から 4.0、端は路側線の中心（3.37）まで。名前の付いた定数（`tools/blender/sheetlib/road_parts.py` の `STOP_LINE_W`・`STOP_LINE_D`・`STOP_LINE_SPAN`）
- 切り替え: `addons/ami/blender/render.py` の `STOP_LINES`・`DRIVE_LEFT`。`sheetlib` の `road_sheet` の `stop_lines` が無いプロファイル（blender-poc）は前と同じ絵（T字の形）
- 「2」の形は、通常の十字と同じ経路（持ち分・走行跡・壁の選び方も十字と同じ）にした
- 停止線を入れるかどうかは、3 本以上並べた交差点の結果を見てユーザーが決める

## 確かめたこと

- `SHEET_LAYOUT=1` のシートで腕と半分の位置を見てから塗った（`road_layout_stopline_cells.png`）
- 道路 3 種のシートは、行 3・7 の列 10〜13（「2」とその雪の絵）だけが変わった（`sheet_diff.py`）。blender-poc の道路のシート 12 枚と、AMI の在来線・高速線の通常の版のシートは、描き直してもバイト列が変わらなかった
- `ingame/road_junction_sample.nut` を `OTRPv64_3.exe`・`flat_512.sve` で敷き、24 画面を撮って 3 倍で見た。`python -X utf8 build.py` は警告なし

## 関連

- アドオン: `addons/ami/README.md`（「T字の「2」の停止線」）、`addons/ami/ACCEPTANCE.md` の 1-3
- 決まり: `docs/reference/way-addon.md` の 9 章
- 見本: `addons/ami/ingame/road_junction_sample.nut`
