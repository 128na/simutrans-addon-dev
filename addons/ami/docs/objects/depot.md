# AMI の車庫・操車場の作り

車庫と操車場（building）の作り。全体の案内は [AMI の README](../../README.md)。文中の `ingame/…`・`blender/…`・`docs/…` などのパスは `addons/ami/` から数える。

## 車庫の作り（#112）

- 線路・路面軌道・道路の 3 つ（`ami_rail_depot`・`ami_tram_depot`・`ami_road_depot`。`blender/catalog.py` の `DEPOTS`）と、モノレールの `ami_monorail_depot`（#113。入口の幅は線路と同じ 3.4、高さも同じ 26px。玉野の 4 両編成が入口で切れずに出た。`docs/monorail_depot_vehicle.png`）と、船の `ami_canal_depot`（#114。入口の幅 7.0。pak128 の船は幅がタイルの大半あるため。車庫は運河の行き止まりに建てる。pak128 の船が入口から出た。`docs/canal_depot.png`）。[ADR 0008](../../../../docs/adr/0008-ami-scope-second-phase.md) の第 2 弾の物で、手本は blender-poc の料金所の作り（1 タイルの building に奥と手前の絵）
- 大きさは、箱積み駅舎の箱 1 段（1 タイル × 高さ 2 段 = 32px。[#140](https://github.com/128na/simutrans-addon-dev/issues/140)）に収める（2026-11-21、ユーザーの決定）。屋根は平らで、笠木の上面がちょうど 2 段。軒・屋根・柱形・腰壁を含めて、奥の絵も手前の絵も、128px のセルの六角形 (64,32)(128,64)(128,96)(64,128)(0,96)(0,64) の中に描く。奥の絵の上端は y32 で、本体が絵から出す建物の高さは 2 段になり、高架（2 段）を上に引ける（下の「高架」）
- 形: 壁の面はタイルの端から 0.1 内、壁の上に笠木、壁の中ほどに会社の色の帯（`player1` の色）、角と入口の脇に柱形、側壁と奥の壁に窓、足元に腰壁（タイルの端まで出し、地面より約 1px 下から立ち上げる）。入口の高さは 26px（pak128 の車両の車体はいちばん高いもので 25px。測り方は記録）。入口の幅は線路 3.4・路面軌道 3.2・道路 4.6（タイル 10）。寸法は `tools/blender/sheetlib/depot.py` の定数と `DEPOT_SHAPES`
- 絵: 道の出る向き（layout 0〜3 が南・東・北・西。本体の決まりは [way-addon.md](../../../../docs/reference/way-addon.md) の 5 章）ごとに、奥の絵（北・西の壁と奥の壁の内側）と手前の絵（南・東の壁と屋根）。手前の絵は車両の後に描かれ、車庫に出入りする車両を隠す。雪の絵は屋根と笠木を白くした版（シートの 3・4 行目）。アイコンとカーソルはシートの 5 行目（`blender/icons.py` が layout 0 の絵から作る。札の字は「庫」）
- 下の way の絵: 道路の行き止まりの絵はタイル全体を塗り、地面より 1px 下に描かれる。腰壁を 1px 下へ延ばして隠したが、2px にすると六角形の外へ出るので、建物の手前の下の縁に道路の端が 1px の点線で残る（`docs/depot_road_temperate.png` の右）。見た目はユーザーが見る
- 路面軌道の車庫は、路面軌道だけの行き止まりに建つ（道路の上の路面軌道の行き止まりは way が 2 本のタイルなので建たない。本体の決まり）
- 高架: AMI の高架の線路（`ami_rail_ballast_elev_single`）を、AMI の車庫と pak128 の `TrainDepot` の上（2 段上のタイル）に敷けた（`docs/depot_elevated.png`）。pak128 には高架の運河が無いので、箱の 2 段目の代わりに高架の線路で見た
- 値: 費用 線路・路面軌道・モノレール 850000・道路 700000・船 900000、維持費 1800、登場年 1900、引退 2999 年（`blender/ami_dat.py` の `DEPOT_VALUES`。値の決め方は[「第 2 弾の物の値」](../../README.md)）。`noinfo=1`・`needs_ground=1`
- pak は種類ごとの pak（`ami_rail.pak`・`ami_tram.pak`・`ami_road.pak`・`ami_monorail.pak`・`ami_canal.pak`）に入る（`build.py` の `KINDS` の名前の頭）
- 検査: `check.sh` が `check_depot.py` を回す。dat の building の絵の塗った画素が六角形の中か（画素の中心で判定）と、奥の絵の上端が y32 より下かを見る
- 見本は `ingame/depot.sh`（`ingame/depot.nut`）。ゲームの写し（`work/depot_game/<PORT>/`）を起動し、AMI の車庫と pak128 の車庫（`TrainDepot`・`TramDepot`・`CarDepot`）を、AMI の way の上に 4 つの向きで並べ、壁の基盤の版と架線つきの壁の上にも建てる。`SNOW=1` で降雪側、`CAPTURE=1` で撮る、`CAPTURE=1 VEH=1` で車庫から編成を出して続けて撮る。使い方はスクリプトの冒頭
  - 確認画像（2026-11-21、`OTRPv64_3.exe`、`flat_512.sve`）: `docs/depot_<種類>_<気候>.png`（左が pak128 の車庫、右が AMI の車庫。向きは 4 つ）、`depot_rail_wall_catenary.png`（壁の基盤の版と架線つきの壁の上）、`depot_vehicle.png`（降雪側で車庫から出る機関車と牛車。入口の中の車両が壁と屋根に隠れる）、`depot_elevated.png`
  - 1930 年の路面軌道には電化の要らない車両が無いので、路面軌道の車庫から出る車両は見ていない

## 操車場の作り（#115）

- 線路の操車場 `ami_rail_yard` 1 つ（building の `stop`。`blender/catalog.py` の `RAIL_YARD`）。[ADR 0008](../../../../docs/adr/0008-ami-scope-second-phase.md) の第 2 弾の物。荷を扱わない駅の建物で、線路の上に建てると、乗客も郵便も扱わない駅になる。時刻表に入れた列車はそこへ行って止まり、折り返す。乗客の駅の隣に建てると、その駅の一部になる（2026-11-22 にゲームで見た。本体の決まりは [way-addon.md](../../../../docs/reference/way-addon.md) の 5 章）
- 見た目は線路の脇の構内通路（2026-11-22、ユーザーの決定。[#115](https://github.com/128na/simutrans-addon-dev/issues/115)）。線路の奥の側（南北の線路なら西、東西の線路なら北）に、低い歩み板（グレーチング）と黄色の柵を置き、隣に駅の建物が無い端には階段を付ける。全部を奥の絵にするので、止まった車両は通路の上に描かれる。通路の線路の側の縁は、pak128 の乗客の駅（`train_platform_early`）のプラットフォームの線路の側の縁（線路の中心から約 1.0。タイル 1 辺 = 10）にそろえ、乗客の駅の隣では一直線に並ぶ（2026-11-22、ユーザーの指摘「プラットフォームの線路寄りに合わせるとよい」。`docs/yard115_pax_edge_zoom.png`）。歩み板は道床の肩の上に載り、柵は線路の壁とほぼ同じ位置に来る。壁つきの線路（基盤の版と壁）の上にも建つ
- 大きさは車庫と同じく箱積み駅舎の箱 1 段に収める（歩み板の上面は約 4px、柵の上端は約 11px）。寸法は `tools/blender/sheetlib/yard.py` の定数
- 絵: `dims=1,1,8` の 8 つの配置（ビット 0 が線路の向き、ビット 1・2 が南・東と北・西の隣に駅の建物が無いこと。並びは `yard.py` の冒頭）ごとに、夏と雪の奥の絵（シートの 1・2 行目）。雪の絵は歩み板を白くした版。アイコンとカーソルはシートの 9 列目（`blender/icons.py` が layout 6 の絵から作る。札の字は「操」）
- 建つのは地上の直線の線路だけ。斜め（「No through station here!」）と坂（「Stops on slope require a slope-capable descriptor!」）には本体が建てない。高架の線路の上には建つが、絵は地上用なので、通路が高架の脇に浮いて見える（`docs/yard115_elevated_zoom.png`。高架用の版を作るかは [#159](https://github.com/128na/simutrans-addon-dev/issues/159)）
- 値: 費用 60000（600 cr）、維持費 1800、登場年 1900、引退 2999 年、`level=1`（`blender/ami_dat.py` の `YARD_VALUES`。値の決め方は[「第 2 弾の物の値」](../../README.md)）。`noinfo=1`・`noconstruction=1`・`needs_ground=1`。下に敷く線路の費用は別にかかる
- pak は `ami_rail.pak` に入る（`build.py` の `KINDS` の名前の頭）
- 検査: `check.sh` が `check_depot.py` を回す（車庫と同じく、絵が六角形の中か、奥の絵の上端が y32 より下か）
- 見本は `ingame/yard_sample.nut`（撮る場所は `sample_spots.sh` の `YARD_SPOTS`）。`sample_parallel.sh` に `NUT=ingame/yard_sample.nut` を付けて流す。区画は 1 タイルと 3 タイル（南北・東西）、乗客の駅の隣、並べた留置線、壁つきの線路、列車（車庫から出して操車場で止める）、斜め・坂・高架の試し。駅になること・乗客と郵便を扱わないこと・隣の駅とつながることを `[check]` で返す
  - 確認画像（2026-11-22、`OTRPv64_3.exe`、`flat_512.sve`）: `docs/yard115_temperate_Y1.png`（南北の 1 タイルと 3 タイル）、`yard115_snow_YE.png`（東西）、`yard115_pax_snow_zoom.png`（乗客の駅の隣。通路が駅の側へ続き、階段は反対の端だけ）、`yard115_pax_edge_zoom.png`（乗客の駅との境の拡大。プラットフォームと通路の線路の側の縁がそろう）、`yard115_temperate_YG.png`（並べた留置線）、`yard115_temperate_YW.png`（壁つきの線路）、`yard115_train_zoom.png`（止まった機関車が通路の上に描かれる）、`yard115_elevated_zoom.png`（高架の上）
  - 建てたときに引かれた額は 576 cr と 640 cr（2 か所）。本体は dat の `cost` をそのまま使う（[way-addon.md](../../../../docs/reference/way-addon.md) の 5 章）。600 cr からのずれは測り方の問題で、建設費はずれていない（スクリプトの所持金が 32 ビット float で、残高が大きく負の `flat_512` では 64 cr 刻みに丸められる。純資産の差は 60000。記録 [2026-11-22_ami-yard-cost-float32.md](../../../../docs/records/2026-11-22_ami-yard-cost-float32.md)、[#160](https://github.com/128na/simutrans-addon-dev/issues/160)）
