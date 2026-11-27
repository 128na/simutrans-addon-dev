# AMI のモノレールの作り

跨座式・懸垂式のモノレールと、その電化の作り。全体の案内は [AMI の README](../../README.md)。文中の `ingame/…`・`blender/…`・`docs/…` などのパスは `addons/ami/` から数える。

## 跨座式モノレールの作り（#113）

- 物: 地上の `ami_monorail_straddle`、高架の 3 版 `ami_monorail_straddle_elev_front`・`_center`・`_back`（`system_type=1`）、トンネル `ami_monorail_straddle_tunnel`（中の way は地上の版）、車庫 `ami_monorail_depot`（[「車庫の作り」](depot.md)）。waytype は `monorail_track`。並びは iss の跨座式（`../refs/iss/src/way/monorail/straddle.dat`・`../refs/iss/src/tunnel/monorail/tunnel.dat`）に合わせた（2026-11-21、ユーザーの決定「軌道配置は ISS と合わせる」）。橋・基盤の版・壁は作らない（iss にも無い）
- 桁: 打ち放しのコンクリートの箱。幅 0.85、上面は way の高さから 0.7（iss の地上の桁を画面で測った値。記録）。地上の版は桁の下面が地面、高架の版は桁を下へ深くして高さ 1.6。跨座式の車両（pak128.japan の車両）は車体の下端が地面の高さに描かれ、裾が桁の上の部分を隠す
- 高架の柱: 桁がタイルを出入りする辺ごとに、その辺の角に柱を立て、柱の頭から辺の中点の桁の下へ腕を渡す（iss と同じ並び）。版は柱を立てる側で、`front` は手前（南北の線は東、東西の線は南）、`back` は奥、`center` は両側。行き止まりは桁の端にも同じ柱と腕。iss は柱をタイルの角ちょうどに立てるが、AMI はタイルの内側に面を合わせて立て、隣のタイルの柱と背中合わせにする（門型の橋脚と同じ。角に立てると、絵がタイルの持ち分で切られて柱が半分になる）。複線は、西（北）の線を `back`・東（南）の線を `front` にすると、柱が外側に並ぶ（`docs/monorail_elev_pair.png`）
- 絵の並び: 線路の通常の版と同じシート（`sheetlib` の `track_sheet`。部品は `tools/blender/sheetlib/monorail_parts.py`）。斜めの走り（`diagonal[...]`）は斜めの絵（iss と同じ）。直角の曲がり（`image[sw]` など）は、辺の中点から軸向きに 1.0（`MONO_CORNER_STUB`）進んでから斜めに曲がる角の絵（行 2 の列 5〜8。幅は直線と同じ 0.85。斜めの走りの幅は約 0.54。2026-11-27、ユーザーの判断 86。#375）。斜めの絵を指していたときは、直線のタイルの桁がタイルの外へ伸ばした分が角の先に出た。地上・高架・電化（`ami_monorail_power`）で同じ。斜めの走りの端のタイル（`diagonal[...]`）が直線と続く所は、小さな出が残る。近い斜めの絵は無い（iss の dat にキーが無い）。分岐の絵（`image[nse1]` などの 1・2）は iss と同じく入れたが、本体は `monorail_track` では自動で選ばない（[way-addon.md](../../../../docs/reference/way-addon.md) の 9.2）。分岐の追加画像（ex 画像）は無い
- 雪の絵: 桁の上面だけを白くする（iss の跨座式は雪の絵を持たない。AMI のほかの way にそろえて足した）。柱は夏と同じ
- 色と汚し（#154）: 第 1 弾の高架の躯体・橋脚・壁（中性の灰）と見分けるため、桁と柱を少し暖かい灰にし、柱を桁より 8% 暗くした。柱と腕は下ほど暗くする（地際の汚れ。柱の下端〔地面より 0.5 単位下〕で 45%、下端から 3.5 単位で 0。地面の高さでは約 39%）。懸垂式も同じ。値は `sheetlib/monorail_parts.py` の `MONO_*`、作りは `tiled_concrete_material` の汚しの引数。ユーザーが案 A＋C を選んだ（2026-11-22。案の比べは `docs/weather_cases_*.png`、直す前と直した後は `docs/weather_before_after_*.png`。見本は `ingame/weathering_lineup.nut`）
- 高架と地上のつなぎ方（#375）: 高架の版は、置いた所の地面の高さ + `way_height_clearance`（pak128 は 2）に置かれる（本体の決まり）。地面の高さは隣のタイルと縁を共有するので、台地や坂を作っても、高架と地上の軌道は直接はつながらない。つなぐには橋を挟む（橋は高架の上から下り坂で始められる。pak128 の `Schwebebahn_p_bridge` で向きがつながることを見た。車両は走らせていない）。AMI にはモノレールの橋が無い
- アイコン: 背景は紫（モノレール。`blender/icons.py` の `WAY_BG`）。高架の版は右下に版の札（前・中・後）と下の帯
- 値: 150 km/h、地上 30000・600、高架 60000・1200（地上の 2 倍）、トンネル 120000・2400（4 倍）、登場 1900（#110 の一覧。`blender/ami_dat.py` の `VALUES`）
- pak は `ami_monorail.pak`（`build.py` の `KINDS`。車庫も入る）
- 見本は `ingame/monorail.sh`（`ingame/monorail.nut`）。ゲームの写し（`work/monorail_game/<PORT>/`）を起動し、地上（車庫と輪・十字・斜め・行き止まり）、高架の 3 版（直線・L 字・T字・斜め・行き止まり）、複線、トンネルを敷き、電化の要らない車両の編成を輪で走らせる。`EXTRA_PAKS` で、借りた車両の pak を写しの中にだけ入れられる。`SNOW=1` で降雪側、`CAPTURE=1` で撮る。使い方はスクリプトの冒頭
  - 確認画像（2026-11-22、`OTRPv64_3.exe`、`flat_512.sve`）: `docs/monorail_ground_temperate.png`（地上の輪・十字・車庫の口の T字）、`monorail_elev_front.png`・`monorail_elev_center.png`・`monorail_elev_back.png`・`monorail_elev_pair.png`、`monorail_tunnel_diag.png`（左がトンネル、右が地上の斜め）、`monorail_snow.png`（降雪側の地上と高架 `front`）、`monorail_vehicle.png`・`monorail_vehicle_zoom.png`（地上を走る編成）、`monorail_depot_vehicle.png`（車庫から出る編成）
  - 車両は、ユーザーが動作の確かめに渡した pak128.japan の跨座式の車両（玉野の 4 両編成。battery）を、写しの中にだけ入れて走らせた。リポジトリには入れていない。高架の上を走る編成は見ていない（地上から高架へ上がる坂を敷いていない）

## 懸垂式モノレールの作り（#116）

- 物: 地上の 3 版 `ami_monorail_suspended_front`・`_center`・`_back` と、高架の 3 版 `ami_monorail_suspended_elev_front`・`_center`・`_back`（`system_type=1`）。waytype は `monorail_track`（跨座式と同じ。車庫は跨座式の `ami_monorail_depot` を使う。跨座式の way とつながるはずだが、ゲームでは見ていない）。並びは iss の懸垂式（`../refs/iss/src/way/monorail/`）に合わせ、支柱は way の絵に持たせた（iss と同じ。2026-11-22、進捗管理の決定。[#116](https://github.com/128na/simutrans-addon-dev/issues/116)）。版は柱を立てる側で、`front` は手前（南北の線は東、東西の線は南）、`back` は奥、`center` は両側（門型）。複線は、西（北）の線を `back`・東（南）の線を `front` にすると柱が外側に並ぶ（`docs/susp116_temperate_P.png`）
- 形: 桁は打ち放しのコンクリートの箱（幅は跨座式と同じ）で、下面は way の高さから 2.8（画面で約 22px）、上面は 4.1（約 32px）。柱はタイルごとに 1 組で、桁の上に載る梁から下ろす。高架の版は柱を高架の段（2 段）の分だけ下へ延ばす
  - 桁の高さは、最初は iss の地上の桁（下面 約 25px・上面 約 35px）に合わせた。ユーザーが渡した懸垂式の車両（pak128.japan の Higashiyama_1A）を走らせると、屋根の吊り具の先と桁の下面の間が約 3px 空いた（pak128 の懸垂式 `Schwebebahn_p_ground` は桁の下面が車両の屋根に接する）ので、桁を 0.4（約 3px）下げた（2026-11-22。`docs/susp116_vehicle_zoom.png`）
- 絵の並び: 線路の通常の版と同じシート（`sheetlib` の `track_sheet`。部品は `tools/blender/sheetlib/monorail_parts.py` の `suspended_parts`・`suspended_pier_fills`）。桁と奥の柱は奥の絵（`image`）、手前の柱は手前の絵（`frontimage`）に描く。手前の柱が車両の前に、桁と奥の柱が車両の後ろに描かれる（シートは 16 行。夏の 8 行は奥 0〜3・手前 4〜7、雪の 8 行は奥 8〜11・手前 12〜15）。カーブは斜めの絵（跨座式と同じ）。近い斜めの絵・分岐の追加画像は無い
- 雪の絵: 桁の上面だけを白くする（跨座式と同じ）
- 色と汚し: 跨座式と同じ（上の「跨座式モノレールの作り」。#154）。地上の版も柱の下端から汚す
- トンネルは作らない: トンネルの穴の高さ（2 段 − 0.6 ≒ 3.5）に、桁の上面（4.1）が入らない。iss も懸垂式専用のトンネルを持たない（`monorail_track` に共通のトンネルはある）。AMI の跨座式のトンネル（`ami_monorail_straddle_tunnel`）に懸垂式の way をつなぐことはできるはずだが、ゲームでは見ていない
- アイコン: 背景は紫（モノレール）、左上に「懸」、右下に版の札（前・中・後）。高架の版は下の帯
- 値: 150 km/h、地上 30000・600、高架 60000・1200（地上の 2 倍）、登場 1900（#110 の一覧。跨座式と同じ。`blender/ami_dat.py` の `VALUES`）
- pak は `ami_monorail.pak`
- 見本は `ingame/suspended_sample.nut`（`ingame/game.sh` で流す。降雪側は `OX=276`）。地上・高架の 3 版の直線・L 字・T字・斜め（G・E）、複線（P）、坂（S）、車庫と輪（V）を敷き、タイルの way の名前と向き（ribi）を `[check]` の行で期待と比べる。V の輪と車庫の口、G・E の center と S の坂には懸垂式用の電化を張り、V では懸垂式の車両を輪で回す。区画 W（y = 102〜111）には、跨座式の地上の way（南北・東西・L 字・斜め）と高架の center の東西に、跨座式用の電化を張る。電化は、タイルの way-object の名前を `[check]` の行で比べる
  - 確認画像（2026-11-22、`OTRPv64_3.exe`、`flat_512.sve`）: `docs/susp116_temperate_G.png`（地上の center）、`susp116_temperate_E.png`（高架）、`susp116_temperate_P.png`（複線）、`susp116_temperate_S.png`（坂）、`susp116_snow_G.png`・`susp116_snow_E.png`（降雪）、`susp116_vehicle.png`・`susp116_vehicle_snow.png`・`susp116_vehicle_zoom.png`（輪を回る車両。電化の物を足す前の、見えない試験用の電化で撮った）、`susp116_power_suspended.png`（懸垂式用の電化。いちばん寄せた画面）、`susp116_power_vehicle.png`（懸垂式用の電化を張った輪を回る車両）、`susp116_power_straddle.png`・`susp116_power_straddle_elev.png`（跨座式用の電化。地上と高架）
  - 車両は、ユーザーが渡した Higashiyama_1A を、ゲームの写しの中にだけ入れて走らせた（リポジトリには入れていない）。この車両は電車（`engine_type=electric`）で、電化した way しか走れない。pak128 にはモノレールを電化する物が無いので、下の「モノレールの電化の作り」の物を足した。見本の輪に懸垂式用の電化（`ami_monorail_suspended_power`）を張ると、Higashiyama_1A が車庫を出て輪を回った（2026-11-22、温暖側と降雪側。試験用の電化の物は入れずに確かめた。`docs/susp116_power_vehicle.png`）。電化の物を足す前は、配らない見えない試験用の電化の way-object を写しの中にだけ入れて走らせた。比べるために、pak128 の懸垂式の way（`Schwebebahn_p_ground`）の輪に、Higashiyama_1A と電化の要らない pak128 の懸垂式の車両（`yoshi_wup1950`）を走らせた（`yoshi_wup1950` を AMI の懸垂式で走らせては見ていない）。高架の上を走る編成は見ていない（地上から高架へ上がる坂を敷いていない）

## モノレールの電化の作り（#116）

電車のモノレール（Higashiyama_1A など）を走らせるための way-object。pak128 にモノレールを電化する物が無いので足した。透明にせず、電化したタイルが目で分かる軽い装飾にした。物の数と形は、2026-11-22 に進捗管理がユーザーの答え（「81 おすすめで」）を受けて案 1（方式ごとに 1 つ、計 2 つ）で決めた（[#116](https://github.com/128na/simutrans-addon-dev/issues/116)）。

- 物: どちらも `waytype=monorail_track`、`own_waytype=electrified_track`（電化）
  - `ami_monorail_power`（跨座式用）: 跨座式の桁の両の側面に、給電レールと碍子を付ける
  - `ami_monorail_suspended_power`（懸垂式用）: 懸垂式の桁の下面の両脇に給電レールを付け、柱ごとに碍子を付ける
- **見た目が合うのは、それぞれの方式の way の上だけ。** 跨座式の桁と懸垂式の桁は高さが違うので、跨座式用を懸垂式の way に張る（またはその逆）と、給電レールが桁から離れて浮く。電化としては、どちらもどの `monorail_track` の way でも働く
- 形: 部品は `tools/blender/sheetlib/monorail_parts.py` の `power_parts`・`power_insulator_fills`。桁は描かず、桁の形の holdout（描画では透明になり、後ろの物を隠す）を置いて、奥の側のレールが桁に隠れるようにした。手前のレールと碍子は手前の絵（`frontimage`）、奥のものは奥の絵（`backimage`）に描く。シートは 8 行（奥 0〜3・手前 4〜7）。雪の絵は持たない（レールと碍子に雪が積もる面が無い）
- アイコン: 背景は紫（モノレール）で電気の印。懸垂式用は左上に「懸」
- 値（仮）: 費用 4000・維持費 100・登場 1900、速さ 1100（`blender/ami_dat.py` の `MONORAIL_POWER_VALUES`。線路の架線と同じ）。速さは、電化した編成の最高速度を縛らないよう、モノレールの way（150 km/h）より大きくした
- pak は `ami_monorail.pak`
- 見本と確認画像は、上の「懸垂式モノレールの作り」の見本（区画 V・G・E・S に懸垂式用、区画 W に跨座式用）
