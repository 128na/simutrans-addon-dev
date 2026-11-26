# 作業ログ: AMI の狭軌（30・60）を足した（#370）

## 目的 / 発端

AMI 第 6 弾（管理 #374）の [#370](https://github.com/128na/simutrans-addon-dev/issues/370)。iss の狭軌（`../refs/iss/src/way/rail/narrow.dat` の `iss_wng_0030`・`iss_wng_0060`）に合わせて、狭軌の way を足す。部品は在来線の物を軌間違いで使い回す。256 でも描けるようにする。

## 分かったこと（事実）

- ADR 0008・0014・0015 は「狭軌とリニアを入れない」のまま（0008 の「入れない物」、0014・0015 が引き継いだ）。#370 の範囲は、進捗管理の判断で入れたもの。ADR の書き手は進捗管理に問い合わせた（[#370 のコメント](https://github.com/128na/simutrans-addon-dev/issues/370)）
- iss の狭軌は地上だけ（高架・橋・壁なし）。`iss_wng_0030` と `iss_wng_0060` は費用 15000・維持費 300 が同じで、絵も同じ（分岐の絵の向きだけ違う）。付属にトンネル `iss_tn_0060`（60 km/h、費用 60000・維持費 1200）、地下の way、車庫、留置線、踏切（道路 × 狭軌 3、狭軌 × 線路 1、狭軌 × 水路 1）がある
- iss のレールの間は、ew のセルで狭軌 4px・標準軌 6px（`../refs/iss/release/pak128/way/rail/narrow_kt.png`・`standard_kt.png`）。AMI の在来線は約 6.1px。レールの中心を 0.7 倍に寄せた狭軌は約 4.3px
- refs の pak128・pak128.japan に `waytype=narrowgauge_track` の車両の dat は無い
- pak128 の `config/menuconf.tab` に狭軌の道具の窓（`toolbar[10]`。way・橋・トンネル・車庫）がある。AMI を入れると、窓に 30・60・トンネル・車庫が並び、30 の道具で地図を押して敷けた（`addons/ami/docs/narrow_menu.png`）
- squirrel で、タイルの上の物は `square_x(x, y).get_ground_tile().get_objects()` で引けた（`tile_x` から車庫を直接は引けなかった）。狭軌の waytype は `wt_narrowgauge`
- `catalog.TRACKS` に足すと、旧描画位置（`OLD_TRACKS`）・基盤・高架・橋・踏切・壁の対応まで一緒に増え、それぞれが waytype `track` を前提にしている。狭軌は `TRACKS` に入れず、`catalog.NARROWS` として別に持ち、`render.py` の `TRACK_PROFILES` に直接足した

## 推測・未確認事項

- 本体が狭軌の分岐の絵（1・2）を自動で選ぶかは見ていない。[way-addon.md](../reference/way-addon.md) の 9.2 は「線路と道路だけ」と書き、同じ文書の v64 の ex 画像の節は「`select_switch_image` は way の種類を問わない」と書く
- 256 の pak をゲームに入れては見ていない（シートを描いて見ただけ）
- 本家 125.0.1 での読み込みは見ていない
- 実際の狭軌の車両アドオン（pak128 用の配布物）では走らせていない。走らせたのは、pak128 の気動車 `620_Railcar_Addon` の dat を写して waytype を `narrowgauge_track` にした試しの車両（ゲームの写しの中だけ。リポジトリには入れていない）

## 結果どうしたか

- 物: `ami_narrow_wood`（30）・`ami_narrow_ballast`（60）・`ami_narrow_ballast_tunnel`・`ami_narrow_depot`、pak は `ami_narrow.pak`。作りは [AMI の「狭軌の作り」](../../addons/ami/docs/objects/narrow.md)
- 軌間: まくらぎ・汚れ・車止めの横幅は 0.7 倍、レールは太さを変えずに中心だけを 0.7 倍の位置へ寄せた（太さまで縮めると 1px を割って途切れる）。道床は 0.75 倍
- 試しと直し（同じ箇所の修正の回数）
  - 30 の木のまくらぎが見えない（土の道床が明るすぎ、まくらぎとの差が小さい）: まくらぎを暗くし、道床の色を 2 回直した（3 回）
  - アイコンの背景の色相が、盛土の路面軌道の 102 と近すぎて `check_icons.py`（20 以上離す）で落ちた（緑の 92）: 赤（色相 11）にした（1 回）
- 道具の癖
  - `blender/ami_dat.py` は全部の dat を書き直し、改行が変わるだけの差分が出る。足した物の dat だけを残し、ほかは `git checkout -- src/ src256/` で戻した
  - 256 で `render_parallel.py` に地上の版とトンネルを一緒に渡すと、トンネルのアイコンが地上の 256 のシートを読みに行き、まだ無くて落ちた（シートは書けている）。トンネルだけ描き直して通った。README の「pak の大きさ」の描く順序に、狭軌の 60 → そのトンネルを足した
- 確認画像は `addons/ami/docs/narrow_*.png`
