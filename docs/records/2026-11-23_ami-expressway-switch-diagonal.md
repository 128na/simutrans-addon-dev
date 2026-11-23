# 作業ログ: AMI の高速道路の分岐で、斜めにつながる枝の轍を直線にする（#205）

（2026-11-23）

## 目的 / 発端

#46 で道路の T字の分岐の絵（switch 画像 1・2）を戻し、ユーザーが確認した（2026-11-23）: 「T字路だと曲線カーブで自然だが、diagonal接続する場合は直線にしたい感じ。高速道路のみ鉄道同様の直線にするとよいかな」。

## 直したこと

高速道路（`ami_road_expressway_*`）の T字の 1・2 の轍を、カーブ 1 本から、線路の `diag_curves` と同じ斜めの直線に替えた。一般道・生活道路は変えない（曲線のまま）。

- `tools/blender/sheetlib/road_parts.py`: `WearPath` に `diag`（斜めの直線の経路）を足し、カーブの角 → 斜めの直線がつなぐ 2 辺の対応 `SWITCH_DIAG_EDGES` を足した。
- `tools/blender/sheetlib/sheetlib.py`: プロファイルのキー `switch_diag` が真なら、`switch_ruts` の枝の轍を `SWITCH_DIAG_EDGES` の 2 辺の中点を結ぶ直線（斜めのセルと同じ経路）にする。`build_road` は斜めの轍を、斜めのセルと同じ幅の倍率（`ROAD_DIAG`・`DIAG_EDGE`）で別に組む。
- `addons/ami/blender/render.py`: 高速道路の設定に `switch_diag=True`。dat は変わらない。

白線（路側線の角の円弧）は変えていない。直したのは轍だけ。

## 確かめたこと

高速道路の通常の版・基盤 4 版・高架 4 版（`ami_road_expressway*.png` 9 枚）を `render_parallel.py` で描き直した（橋は分岐の絵を持たず変わらない）。HEAD と比べると、色が変わったセルは分岐のセル（行 2・3・6・7 の列 10〜13）だけで、透過の範囲の差は 0。ほかに `base_single`・`elev_back`・`elev_front` の先頭のセル（0,0）（0,1）に色の差が出た（#46 の記録と同じ、原因は未確認のアイコンのセル）。

ゲーム内: v64（`sim-WinGDI64-OTRPv64.exe`）、`flat_512_left_v64.sve`（2026-11-23 16:26 の版）、`road_sample.nut` の高速道路だけ（区画 M・M2）。見本は全部敷けた（`ok`）。自動選択はどちらも分岐の絵「1」で、枝の隣がカーブ（斜め）の T字に、斜めの直線の轍が通ることを確かめた（画像 `addons/ami/docs/road205_v64_EX_M_M2_zoom.png`、左が M、右が M2。前後のシートのセルは `road205_sheet_before_after.png`、上が前・下が後）。左側通行の地図だけ。右側通行・降雪側・直す前のゲーム内の画像は撮っていない（前はシートのセルで比べた）。
