# AMI の狭軌の作り

狭軌（waytype `narrowgauge_track`）の way・トンネル・車庫の作り。全体の案内は [AMI の README](../../README.md)。文中の `ingame/…`・`blender/…`・`docs/…` などのパスは `addons/ami/` から数える。

## 狭軌の作り（#370）

- 物: 地上の 2 種 `ami_narrow_wood`（30 km/h。木のまくらぎと土の道床の軽便）・`ami_narrow_ballast`（60 km/h。在来線と同じ砕石と PC まくらぎ）、60 のトンネル `ami_narrow_ballast_tunnel`（中の way は `ami_narrow_ballast`）、車庫 `ami_narrow_depot`（[「車庫の作り」](depot.md)）。並びは iss の狭軌（`../refs/iss/src/way/rail/narrow.dat` の `iss_wng_0030`・`iss_wng_0060`。地上だけ）とトンネル（`iss_tn_0060`）に合わせた。基盤・高架・橋・壁・架線・旧描画位置の版は作らない（iss にも無い。線路の壁・架線は waytype が `track` の way-object で、狭軌には重ならない）
- 部品: 在来線（`ami_rail_ballast`）の部品（まくらぎ・レール・頭頂面の帯・汚れ・車止め・道床）を使い回し、軌間だけを内へ寄せる（`blender/render.py` の `NARROW_*`。土台の `sheetlib` は変えていない）
  - まくらぎ・汚れ・まくらぎの間の砕石・車止めは、横幅を `NARROW_GAUGE_K`（0.7）倍にする
  - レールと頭頂面の帯は、太さを変えずに中心だけを 0.7 倍の位置へ寄せる（太さまで縮めると 1px を割って途切れる）
  - 道床は幅を `NARROW_BED_K`（0.75）倍にする
  - レールの間は、ew のセルで在来線 約 6.1px に対して狭軌 約 4.3px（iss は標準軌 6px・狭軌 4px。`../refs/iss/release/pak128/way/rail/standard_kt.png`・`narrow_kt.png`）。並べた画像は `docs/narrow_compare.png`（手前から在来線・60・30）
- 30 の材質: 木のまくらぎ（暗い茶）と土の道床（`NARROW_WOOD_SLEEPER_RGB`・`NARROW_EARTH_RGB`）。土の道床は、まくらぎが見分けられるよう、在来線の砕石より暗い灰褐色にした
- 絵の並び: 在来線の通常の版と同じシート（`sheetlib` の `track_sheet`）。カーブは斜めの絵、近い斜めの絵も持つ（`catalog.DIAG_CURVE_WAYS`）。分岐の絵（1・2）は持つ（iss と同じ）。本体が狭軌で自動で選ぶかは見ていない（[way-addon.md](../../../../docs/reference/way-addon.md) の 9.2 は「線路と道路だけ」と書くが、同じ文書の v64 の ex 画像の節は「`select_switch_image` は way の種類を問わない」と書く）。分岐の追加画像（ex 画像）は無い（`blender/ami_dat.py` の `EX_WAYS` が waytype で絞る）
- 雪の絵: 在来線の雪の材質を使う。雪の側では 30 と 60 がほぼ同じに見える（まくらぎと道床が雪に隠れる。`docs/narrow_compare_snow.png`）
- トンネル: 在来線のトンネルの坑口と同じ作りで、中の道床を狭軌にした（`render.py` の `SHEETS[catalog.NARROW_TUNNEL]`）。30 のトンネルは作らない（iss も 60 だけ）
- 車庫: 線路の車庫と同じ形で、入口の幅を 3.0 にした（線路は 3.4。`tools/blender/sheetlib/depot.py` の `DEPOT_SHAPES["narrow"]`）。狭い軌間に合わせた見た目の選び方で、車両の幅は測っていない（pak128 に狭軌の車両が無い）。試しの車両（線路の気動車の写しで、線路の車両と同じ幅）は入口から出た
- アイコン: 背景は赤（狭軌。`blender/icons.py` の `WAY_BG`。色相 11）。札は 30・60
- 値（仮。PR でユーザーが確かめる）: 下の表（`blender/ami_dat.py` の `VALUES`・`TUNNELS`・`DEPOT_VALUES`）。iss は 30・60 とも費用 15000・維持費 300 なので、30 を安くした。トンネルは第 1 弾と同じく地上の 4 倍（iss の `iss_tn_0060` と同じ 60000・1200）、車庫は線路の車庫と同じ

| 物 | 速さ | 費用 | 維持費 | 登場 |
|---|---|---|---|---|
| `ami_narrow_wood` | 30 km/h | 10000 | 200 | 1900 |
| `ami_narrow_ballast` | 60 km/h | 15000 | 300 | 1900 |
| `ami_narrow_ballast_tunnel` | 60 km/h | 60000 | 1200 | 1900 |
| `ami_narrow_depot` | – | 850000 | 1800 | 1900 |

- pak は `ami_narrow.pak`（`build.py` の `KINDS`。名前の頭 `ami_narrow_`。トンネル・車庫も入る）。全部入りの `ami.pak` にも入る
- 名前の表示（日本語）は `release/text/ja_ami.tab`
- 見本は `ingame/narrow.sh`（`ingame/narrow.nut`）。ゲームの写し（`work/narrow_game/<PORT>/`）を起動し、30 と 60 のそれぞれに、車庫と輪（北の辺に車庫の口の T字と輪を横切る十字）・斜め・行き止まり・1 段の坂を敷き、60 にはトンネルを敷く。30・60・在来線を平行に並べた比べも敷く。狭軌の車両があれば、両方の輪で 1 両ずつ走らせる。`SNOW=1` で降雪側、`CAPTURE=1` で撮る。使い方はスクリプトの冒頭
  - pak128 には狭軌の車両が無い。動作の確かめには、pak128 の気動車（`620_Railcar_Addon`）の dat を写して waytype を `narrowgauge_track`・速さを 60 にした試しの車両を作り、`EXTRA_PAKS` でゲームの写しの中にだけ入れた（リポジトリには入れていない）。30 と 60 の輪を、それぞれ 30 km/h・60 km/h で回った
  - 確認画像（2026-11-26、`OTRPv64_3.exe`、`flat_512_left_v64.sve`）: `docs/narrow_wood_ground.png`（30 の車庫と輪・十字）、`narrow_ballast_ground.png`（60）、`narrow_diag.png`（斜め）、`narrow_slope.png`（坂）、`narrow_tunnel.png`（トンネル）、`narrow_snow.png`（降雪側）、`narrow_compare.png`・`narrow_compare_snow.png`（30・60・在来線を並べた所。雪の側は走る試しの車両も写る）、`narrow_256_cells.png`（256 で描いたシートのセル。上が 30、下が 60）、`narrow_menu.png`（pak128 の狭軌の道具の窓に 30・60・トンネル・車庫が並び、30 の道具で地図を押して敷いた所。2026-11-27）
- 256: `catalog.SCALED_TARGETS` に自動で入る（README の「pak の大きさ」）。256 で描いたシートを見た（`docs/narrow_256_cells.png`）。256 の pak をゲームに入れては見ていない
- 入れていない物（必要なら別の issue）: 道路 × 狭軌・狭軌 × 線路・狭軌 × 運河の踏切、地下の way、留置線（iss にはある）、基盤・高架・橋
