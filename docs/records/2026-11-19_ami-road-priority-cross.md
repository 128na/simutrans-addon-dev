# 作業ログ: AMI の道路の「2」を通常の十字に戻し、十字の 1・2 を優先道路の十字に（#21 の続き）

（2026-11-19）

## 目的 / 発端

T字の「2」を十字の形にして停止線を引いた作り（[2026-11-19_ami-road-stopline.md](2026-11-19_ami-road-stopline.md)）は、道路を 3 本以上並べた交差点で内側の腕にも停止線が出た。ユーザーの決定（2026-11-19）: 「複雑な十字交差と干渉してしまうので普通の十字交差に戻そう。Standard を十字交差、crossover a/b をどちらが優先道路にする」。

- T字の「2」（`nse2`・`nsw2`・`new2`・`sew2`）は停止線を外し、通常の十字と同じ絵にする
- 十字の分岐の絵（`nsew1`・`nsew2`。固定の道具・タイルの詳細ダイアログでだけ選べる）を、優先道路のある十字にする。Standard（固定しない十字）は通常の十字のまま

## 分かったこと（事実）

- 本体の選択肢: `128na/simutrans` の `feature/switch-image-override` の `gui/ground_info.cc` の選択肢は「Crossing (straight left-right)」「Crossing (straight up-down)」「Double crossover A」「Double crossover B」。`boden/wege/weg.cc` の `apply_switch_image_override` で、値 1 が `image_switch` の `nw` = true（dat の `nsew2`）、値 2 が `nw` = false（`nsew1`）、値 3・4 は ex 画像。ブランチのコミット d0e1db21c の説明は「どちらの対角線が直進に描かれるか（A: 左右、B: 上下）」
- この「左右・上下」は、線路の十字の絵でタイルの左右の角・上下の角を結ぶ直線のこと（`docs/reference/way-addon.md` の 9.2）。道路の南北の軸（画面で左下 → 右上）と東西の軸（左上 → 右下）はどちらも画面で斜めで、言葉からはどちらが優先かは決まらない
- `nsew1` を南北優先、`nsew2` を東西優先にした。前の作り（十字の 1 が南北の中央線と点線）に合わせ、コーディネーターの予想（`nsew2` が東西優先）とも同じ
- シート: 3 種とも「2」の 4 セル（行 3・7 の列 10〜13）が十字のセル（列 9）と画素まで同じ。前のシートと比べて変わったのは「2」の 4 セルと十字の 1・2（行 2・3・6・7 の列 14）だけで、透過の範囲は変わらない（`tools/blender/sheet_diff.py`）。blender-poc の道路 12 枚と、在来線・高速線のシートは描き直してもバイト一致
- ゲーム（`OTRPv64_3.exe`、`flat_512.sve`、温暖側）: `road_junction_sample.nut` の `[check]` の行は、8 通りとも全部の十字が `nsew` と出る（makeobj が同じ絵をまとめるので、「2」も十字と同じ画像番号）。区画 L も `west`・`east`・`plain` が同じ番号。区画 I の十字の固定 1・2 は、3 種とも別の番号（`pin1`・`pin2`）

## 作り

- 優先道路: 中央線を交差点の中も通す（生活道路は中央線なし）。路側線は交差点の口を点線で渡す（高速道路の十字の点線と同じ）
- 従道路: 2 つの口の、交差点へ進入する車線（半分）に停止線。左側通行で、`nsew1` は西の腕の北半分と東の腕の南半分、`nsew2` は北の腕の東半分と南の腕の西半分。中央線は停止線からタイルの辺まで
- 停止線の寸法は前の作りの `STOP_LINE_*`（`tools/blender/sheetlib/road_parts.py`）をそのまま使った
- `sheetlib` の `road_sheet` のキー: `stop_lines` をやめ、`switch2_cross`・`priority_cross` を足した。`drive_left` は残した（右側通行では停止線が反対の半分へ移る）。AMI の `blender/render.py` は `STOP_LINES` をやめ、`DRIVE_LEFT` を残した

## 確かめたこと

- `SHEET_LAYOUT=1` で 3 種を描き、十字の 1・2 のセルで停止線と中央線の位置を見てから塗った
- 区画 I の固定した十字を 3 種とも 3 倍で見た（`addons/ami/docs/road_{LO,GE,EX}_priority_ns_zoom.png`・`_ew_zoom.png`）
- `road_junction_sample.nut` の 4×4・6×6（`road_GE_4x4_cross_zoom.png`・`road_GE_6x6_cross_zoom.png`）と区画 L で、通常の十字が並び停止線が出ないことを見た
- 前の停止線の確認画像（`road_GE_*_stopline*_zoom.png`・`road_layout_stopline_cells.png`・`road_stopline_cells_zoom.png`）は消した。前の記録から引いている画像は、コミット 6188ff3 の版にある

## 見ていないこと

- タイルの詳細ダイアログでの選択（スクリプトの固定の道具で選んだ）と、保存・ロードで固定が残ること
- 優先道路の十字の形と、ダイアログの言葉（左右・上下）との対応がよいかは、ユーザーの確認待ち
