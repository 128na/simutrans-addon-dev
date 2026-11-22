# 作業ログ: 多車線と交差点の路面表示を路面軌道の景観の way で作り、路面表示の版の道路を外す（#187）

（2026-11-22）

## 目的 / 発端

[#187](https://github.com/128na/simutrans-addon-dev/issues/187) は、交差点の路面表示を路面軌道（`tram_track`）の way で道路に重ねて入れる作業で、#156 の作り直し。#156 で差し戻された点（白の明るさ、停止線・横断歩道を路側線の内に収める、景観の雪の絵、README の注意、ADR、描く道具の置き場）を引き継いだ。

部品の一覧の案を 3 回出した。

- v1: #121 の路面表示の版（中央線が 1 本）を前提にした。NG。ユーザーの言葉は、版の道路を前提にすると判断を誤るので削除して、というもの。
- v2: 車線の割り方（0.5 路側帯 / 1.0 上り A / 1.0 上り B / 0.5 路側帯 x2 → 中央分離帯や右折レーン）を取り入れた。続けてユーザーが「この道路アドオン自体が不要。車線を増やす表現は景観アドオンの仕事でトラム属性になる」と判断した。
- v3: 下の道路を白線の無い一般道路にし、白線をすべて景観の way で描く案（案 a）。途中で 2 つ直した。
  - 導流帯の三角の向きを、左側通行で右折車線へ入る導線に沿う形にした（ユーザーの指摘）。
  - 2 車線の腕を、路側線のあいだの 3 等分と、中央線の一点から分かれる楔のガイドにした（ユーザーの指摘。iss の intersection1 と同じ）。

v3 が承認された（「36 推奨案でOK」）。路面表示の版を外すことも、この issue で行う（「35 187で合わせて対応して」）。

## やったこと

- 路面表示の版 14 本を外した（dat・シート・`catalog.py` の `LANE_ROADS`・`LANES`、`render.py`・`ami_dat.py`・`addon_config.py`・`icons.py`・`lineup.py` の分岐、`ingame/lane_sample.nut`、`sample_spots.sh` の `LANE_SPOTS`、`docs/lane121_*.png`）。`tools/blender/sheetlib/sheetlib.py` の `lane_lines`・`_far_sign` と、プロファイルの `lanes` も外した。
- 白線の無い一般道路 `ami_road_general_blank` を足した。プロファイルの `no_lines` で、道路の白線を 1 本も描かない。
- 景観の way 5 本（`ami_mark_lane4`・`junction2`・`junction2_t`・`junction4_in`・`junction4_out`）を、`tools/blender/sheetlib/marking.py` で描いた。
  - 線の位置は、まず Blender を使わない 2D の検算（上から見た図）で、腕・中心のつながりを確かめた。
- ゲームで見本を敷いた（`ingame/marking_sample.nut`、`OTRPv64_3.exe`、`flat_512.sve` の写し）。対象は 4 車線どうしの十字（ふつう・スクランブル）、4 車線 × 2 車線、2 車線の十字・T字路で、温暖と降雪の両方。
  - `[check]` で、道路と表示の名前と向きが手順どおりなのを確かめた（返り値は ok）。
  - 一般道路の上に `ami_road_general_blank` を敷くと置き換わることも、見本で確かめた。

## 結果

- 温暖では、どの形も白線が途切れずにつながった。
- 降雪では、下の道路（blank）の雪が残った。場所は、4 車線の中央の帯（右折車線）と、交差点の中心の 4 タイル。中心では、十字の形のタイルの角に雪の塊が出る。帯の中の白線（右折の矢印・導流帯）は雪に埋もれる。帯の雪は案で予想していたが、中心のタイルの雪の塊は案に書いていなかった。

## 案からの逸れ

- 2 車線の T字路の中心は、閉じた側に路側線が要る。一方、4 車線 × 2 車線の中心（T字の形）では、欠ける側は相方のタイルで、線を引かない。同じ way の T字の形では両方を描けないので、`ami_mark_junction2_t` を足した。承認された一覧には無かった。
- 案では「2 車線の道路は今の `ami_road_general` のまま」としていた。実際には、2 車線の交差点も、中心と腕を `ami_road_general_blank` にした。腕は中央線を寄せ、楔の導流帯を置くので、下の中央線が透けると合わないため。

## 外した名前（ADR 0009 のための記録）

ベータ版 beta.2 で配った物のうち、次の 14 本の名前が消えた。正式版で compat.tab を用意するときの材料にする。

- `ami_road_general_lane1`〜`ami_road_general_lane7`
- `ami_road_expressway_lane1`〜`ami_road_expressway_lane7`

置き換え先は、道路が `ami_road_general_blank`（高速道路は #188 で決める）、白線が `ami_mark_*`。1 対 1 には対応しない。

## 推測・未確認事項

- 坂の `lane4`、車両が走るときの重なり、斜めの道路は、見本で確かめていない（見本の地図が平らで、斜めの絵は作っていない）。
- スクランブルの帯（交差点の中心線に沿う + の帯）が、iss の 2-2 と同じ並びかは確かめきれていない。iss のシートの絵は、セルの並びと向きが読み取りにくかった。

## 関連

- ADR: [0012](../adr/0012-ami-lane-and-junction-marking-as-tram-way.md)
- 作りと手順: `addons/ami/README.md` の「路面表示の作り」
- 手本: `../refs/iss/src/util/road_misc/intersection.dat`
- 交差点の部品の決まりと描く順: [2026-11-22_cityscape-sis-parts-and-draw-as-ding.md](2026-11-22_cityscape-sis-parts-and-draw-as-ding.md)
