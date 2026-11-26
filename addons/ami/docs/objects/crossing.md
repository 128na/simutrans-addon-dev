# AMI の踏切の作り

線路と道路の踏切と、水路の踏切の作り。全体の案内は [AMI の README](../../README.md)。文中の `ingame/…`・`blender/…`・`docs/…` などのパスは `addons/ami/` から数える。

## 踏切の作り（#111）

作るもの・見た目・仮の値は、2026-11-21 に進捗管理が推奨案で決めた（[#111 のコメント](https://github.com/128na/simutrans-addon-dev/issues/111#issuecomment-7059345141)。見た目はユーザーが PR で確かめる）。

- 線路 4 種 × 道路 4 種の 16 個（`ami_crossing_<線路>_<道路>`。例 `ami_crossing_rail_ballast_road_general`。`blender/catalog.py` の `CROSSINGS`）。本体は踏切を waytype の組と速さだけで選ぶ（way の名前は見ない。`docs/reference/way-addon.md` の 5 章）ので、組ごとに速さの合う踏切を置く。高速道路の踏切も作る（無いと pak128 の踏切が出る）。pak128 などほかの way との組でも、速さの近い AMI の踏切が選ばれることがある。見本の区画 M で見た組（2026-11-21、`docs/crossing_mixed.png`。左から）: `Rail_100_Tracks`×`Road_050` と `ami_rail_ballast`×`Road_050` は pak128 の踏切、`Rail_100_Tracks`×`ami_road_general`・`Rail_160_Tracks`×`ami_road_local` は AMI の踏切、`ami_rail_slab`×`Road_050` は AMI の一般道路の踏切（pak128 の踏切は 480km/h の線路に足りない）で、pak128 の道路の上に AMI の路面が出る。どの組も way の速さは踏切で下がらなかった（`[check]` の行の `full`）
- 絵は道路の種類ごとに 1 枚（`src/ami_crossing_road_<道路>.png`）で、線路の 4 種で同じ（踏切の中は道床が見えない）。描くのは `tools/blender/sheetlib/crossing.py` の `crossing_sheet`
  - 奥の絵（乗り物より前に描く）は、pak128 の踏切と同じくタイル全面を描き、下の way の絵を隠す（隠さないと AMI の道床が路面の上に出る。iss の踏切は遮断機だけを描く）。その道路の直線のセル（`src/ami_road_<道路>.png` の `0.2`・`0.3`、雪は 4 行下）を下地にそのまま写し、線路に沿うゴムの踏板（黒灰）・レールの頭・溝と、奥の側の遮断機・警報機を重ねる。レールと踏板は線路の way のレールと同じ基準面（`_DATUMS` の `rail`）・横の範囲・上面の高さで、隣の線路のタイルのレールとつなぐ（`render.py` が線路の `RAIL_IN`・`RAIL_OUT`・`RAIL_Z1` を `rail=` で渡す。踏板の上面はレールの頭の高さ。#129）
  - 手前の絵（乗り物の後に描く）は、手前の側の遮断機・警報機だけ。奥・手前は線路で分ける（東西の線路は南の側、南北の線路は東の側が手前）。車は踏切のタイルの外で止まるので、タイルの上を通る列車に合わせた
  - 遮断機・警報機は日本式の第 1 種踏切（黄黒の遮断かん、黄黒の柱に X 字の標識と赤い 2 灯）を、道路の左側（左側通行）に線路を挟んで 2 基。開いた絵は遮断かんが立ち、閉じた絵は進む側の車線をふさいで赤い灯が点く。灯の点滅（絵の切り替え）は無い（OTRP は絵の添字を雪の絵に使う）
- 道路のシートを描いた後に描く（`render.py` の `SHEETS` は登録の順に描く。`render_parallel.py` で並べて描くときは、道路のシートを描き終えてから踏切を描く）。道路の絵を描き直したら踏切も描き直す。描き直し忘れは `check.sh` の `check_crossing.py` が見つける（踏切を描くときに、写した道路のセルの sha256 を `src/ami_crossing_road_<道路>.road_cells.txt` に控え、今の道路のシートと比べる。#130）
- 道具が無いので、アイコン・カーソルは持たない（`blender/icons.py` は dat に `icon` の無い物を飛ばす）
- pak は付属（`ami_extra.pak`）に入れる（線路・道路と組で使う）
- 値（仮。#110 で決める）: 速さは両方の way の最高速度（踏切で速度を落とさない）、登場年は 2 つの way の遅い方、音なし（`sound=-1`。iss と同じ）。`blender/ami_dat.py` の `crossing_dat_text`
- 見本は `ingame/crossing_sample.sh`（`ingame/crossing_sample.nut`・`crossing_train.nut`）。16 組を、道路が南北の向き（H 線）と東西の向き（V 線）で温暖・降雪に敷き、開いた絵と、列車を走らせて閉じた絵を撮る。撮った画面に AMI の踏切の絵が出ているかは `JUDGE=1` で判定する（`ingame/crossing_judge.py`。AMI の遮断機・警報機の黄色と、pak128 の踏切の標識の赤の画素を数え、どちらも無ければ踏切が写っていないとする。script からは踏切の名前が読めず、ほかの pak の踏切が選ばれても way の速さは変わらないため。#128）。撮った画面は `docs/crossing_<気候>_<線>_<開閉>.png`（左上から、行が道路 local・general・expressway、列が線路 ballast・concrete・ladder・slab）

## 水路の踏切の作り（#117）

作るもの・見た目・名前は、2026-11-22 にユーザーが推奨案で決めた（[#117 のコメント](https://github.com/128na/simutrans-addon-dev/issues/117#issuecomment-7065997662)。見た目はユーザーが PR で確かめる）。

- 線路 4 種・道路 3 種 × 運河の 7 個（`ami_crossing_<線路|道路>_canal`。例 `ami_crossing_rail_ballast_canal`・`ami_crossing_road_general_canal`。`blender/catalog.py` の `CANAL_CROSSINGS`）。線路×道路の踏切と同じく、本体は waytype の組と速さだけで踏切を選ぶので、way ごとに速さの合う踏切を置く。路面軌道・モノレールと運河の踏切は作らない（どの pak にも無いので、今は運河を横切れない）
- 跳ね橋。2 枚の桁が両岸（水面の縁）を軸に、タイルの中心へ半分ずつ渡る。開いた絵（線路・道路の乗り物が通る）は桁を下ろし、閉じた絵（船が通る）は 78 度起こす。本体は `waytype[1]`（`water`）の船が来ると閉じる（`dataobj/crossing_logic.cc`）。遮断機は付けない（iss・pak128 の運河の踏切も無い）。描くのは `tools/blender/sheetlib/canal_crossing.py` の `canal_crossing_sheet`
  - 奥の絵は、線路×道路の踏切と同じくタイル全面を描き、下の way の絵を隠す。運河の直線のセル（`src/ami_canal.png` の `0.2`・`0.3`、雪は 4 行下）を下地に写し、その上に桁を描く
  - 道路: 床はタイルの幅いっぱい（運河の笠石の外の縁まで）で、床の縁の下に青灰の桁、両側に白い欄干。床の路面は、その道路の直線のセルを写す。絵は道路の種類ごとに 1 枚（`src/ami_crossing_canal_road_<道路>.png`）。閉じた絵では、岸（軸の外）だけ道路のセルを写す
  - 線路: 半幅 1.6 の鋼の床に、木のまくらぎとレール。レールは線路の way と同じ基準面（`_DATUMS` の `rail`）・横の範囲・高さで、隣の線路のタイルのレールとつなぐ。線路の 4 種で共通の 1 枚（`src/ami_crossing_canal_rail.png`）。岸の部分は、閉じた絵でも床とレールを残す
  - 床と桁の下端は、運河の水面（way の高さから −0.45）より上に置く。初めは桁が深く（床の上面から 0.57 下）水面に食い込んで見えたので、床を薄く（0.08）し、桁を道路 0.20・線路 0.10 にした（2026-11-22、ユーザーの確認。水面の高さは運河の way・#161 の景観の運河と共通なので変えない。`docs/canal_crossing_girder_before_after.png`。左が前、右が後）
  - 手前の絵は、閉じた絵の手前の岸の桁だけ（船の後に描く）。奥・手前は運河で分ける（東西の運河は南の岸、南北の運河は東の岸が手前）。開いた絵の手前の絵は空
- 運河・道路のシートを描いた後に描く。描き直し忘れは `check_crossing.py` が見つける（写した運河・道路のセルの sha256 を `src/ami_crossing_canal_<road_<道路>|rail>.road_cells.txt` に控える。線路×道路の踏切と同じ作り）
- 値（#110 の一覧）: 運河の側は 60 km/h、線路・道路の側は way の最高速度（踏切で速度を落とさない）。登場年は 2 つの way の遅い方、音なし（`sound=-1`）。`blender/ami_dat.py` の `canal_crossing_dat_text`
- 道具が無いので、アイコン・カーソルは持たない。pak は付属（`ami_extra.pak`）
- 歩道（`ami_sidewalk*`）も waytype が `water` なので、AMI の道路が歩道を横切るタイルにも、この跳ね橋が出る（前は pak128 の運河の踏切の跳ね橋が出ていた）。歩道は乗り物が通らないので、桁は下りたまま。これは承知のうえで受け入れた（2026-11-22、ユーザーの決定）。歩道専用の踏切（横断歩道の絵）は [#166](https://github.com/128na/simutrans-addon-dev/issues/166)
- 見本は `ingame/canal_crossing.sh`（`ingame/canal_crossing.nut`）。ゲームの写し（`work/canal_crossing_game/<PORT>/`）を起動し、東西の運河を南北の 7 種が横切る区画 H（`[ns]` の絵）と、南北の運河を東西の 7 種が横切る区画 V（`[ew]` の絵）を敷き、船・列車・車を往復させる。区画 H には pak128 の `Rail_160_Tracks`・`Road_050` との組（M）、別に歩道を一般道路が横切るタイル（W）も敷く。`SNOW=1` で降雪側、`CAPTURE=open|closed` で撮る（閉じた絵は船が踏切のタイルに乗ったとき）、`WATCH=<秒>` で踏切のタイルを船と列車・車が通ったかを数える
  - 確かめたこと（2026-11-22、`OTRPv64_3.exe`、`flat_512.sve`）: 14 か所と M・W がどれも踏切になり（`is_crossing`）、way の速さは踏切で下がらなかった（`[check]` の `full`）。船と、線路の機関車・道路の車が、どの踏切のタイルも通った（`WATCH`。車は桁が下りるまで岸で待ち、船は車が渡り終えるまで待った）。M の `Rail_160_Tracks`×運河は AMI の線路の跳ね橋（pak128 の運河の踏切と速さが同じ 160 で、後に読んだ AMI が選ばれる）、`Road_050`×運河は AMI の一般道路の跳ね橋（pak128 の道路の上に AMI の路面が出る）。W は AMI の一般道路の跳ね橋
  - 確認画像: `docs/canal_crossing_<気候>_<H|V>_<open|closed>.png`（左上から ballast・concrete・ladder・slab・local・general・expressway）、`docs/canal_crossing_mixed.png`（上の段が M の 2 つと W の開いた絵、下の段が M の閉じた絵と降雪側の W）、`docs/canal_crossing_zoom_*.png`（3 倍に拡大した切り抜き）
