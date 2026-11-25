# ADR: AMI の範囲に駅・停留所・線路の信号を入れ、空港・滑走路と電線は第 5 弾の後に回す

> ステータス: Accepted (2026-11-25)。ADR 0008 の範囲の項を置き換える（0008 は Superseded）
> 由来: [#264](https://github.com/128na/simutrans-addon-dev/issues/264)（範囲の見直し）・[#261](https://github.com/128na/simutrans-addon-dev/issues/261)（pak の大きさの対応）・[ADR 0008](0008-ami-scope-second-phase.md)

## 背景と問題

[ADR 0008](0008-ami-scope-second-phase.md) は、way・壁・高架・橋・トンネル・車庫・操車場と景観・補助の物を範囲にした。駅・停留所・信号・空港と港の道・電線は入っていない。

- 2026-11-24 のユーザーの決定で、インフラを土台として使いたい pakset（pak256）の側ではインフラを作らず、AMI にまとめて任せることにした。遊べる状態にするのに先に要るのは、駅とバス停、線路の信号 1 種（ユーザーの判断 18、2026-11-25。作るのは第 5 弾）
- pak256 は、仮のバス停と荷役所を自前で持っている（[pak256#44](https://github.com/128-bit-net/pak256/issues/44)）。pak256 の `docs/stations.md` に、置き換えのための控え（name・obj・type・waytype）がある。仮の車庫（`pak256_road_depot`）は、#261 の D で AMI の `ami_road_depot` が 256 でも組めるようになり、置き換えられる

この ADR を決めるときに、次のことを確かめた（2026-11-25）。

- **建物の生成は車庫と操車場で出来ている。** `addons/ami/blender/ami_dat.py` の `depot_dat_text`（`type=depot`）と `yard_dat_text`（`type=stop`・`waytype=track`・`dims=1,1,8`・夏と雪の絵・アイコンとカーソルのセル）。駅・停留所はこの続きで、`yard_dat_text` は `level`・`noconstruction` も出している。足りないのは `enables_pax`・`enables_post`・`enables_ware` と、前景の絵（`frontimage`）の行。向きごとの絵の並び（8 層）も操車場にある。本体の層の決め方は、操車場も道路の停留所も同じ（`simutrans/bauer/hausbauer.cc` の `build_station_extension_depot`。層が 5 以上の停留所は、隣に停留所の建物があるかでビット 2・4 の端を消す。道路・線路の区別は無い）ので、操車場のシートの並び（`sheetlib/yard.py`）をそのまま道路の停留所に使い回せる見込み。大きさは `sheet_settings.SCALE` を使い、オフセットも `-64 * SCALE` の形で出すので、#261 と同じ道具で 256 でも描ける
- **roadsign の生成も出来ている。** `roadsign_dat_text`（道路標識。`obj=roadsign`・`waytype=road`・アイコンとカーソルのセル・左側通行のずらし `ROADSIGN_OFFSET_LEFT`）。線路の信号は waytype を `track` にして、`is_signal=1` などを足す形
- 手本の pak128（`../refs/pak128/infrastructure`）に、線路の駅（`rail_stations`。`type=stop`・`waytype=track`・`Dims=1,1,2` で向き 2 通り・`enables_pax=1`）、バス停（`road_stops`。向き 8 通り）、線路の信号（`rail_signals`。`is_signal`・`is_presignal`・`is_prioritysignal`・`is_longblocksignal`・選択信号・選択の終わり）がある。iss（`../refs/iss/src`）には駅・停留所・信号が無い（`building/` は車庫だけ）。使える範囲は [refs-index.md](../reference/refs-index.md) のとおり（pak128 は測定と参照だけ。絵は流用しない）
- 本体の `descriptor/writer/roadsign_writer.cc` が読む信号のキーは `is_signal`・`is_presignal`・`is_prioritysignal`・`is_longblocksignal`・`free_route`（選択信号）・`end_of_choose` など。`roadsign_desc.h` の信号の種類も、単純（閉塞）・前方注意・優先・長閉塞・選択・選択の終わり
- pak256 の仮の停留所（旅客・郵便のバス停と貨物のトラックの荷役所）は、`type=stop`・`waytype=road`・1x1・向き 8 通り・`level` 2 で、AMI が置き換える形と同じ

## 決定

2026-11-25 のユーザーの承認（#264 のコメント）。次の 4 点は、作業者の案のおすすめどおりに決まった: (1) 空港・電線は範囲に入れて、作るのは後 (2) 路面軌道の停留所と港は第 5 弾から外して後 (3) 第 5 弾の信号は閉塞信号 1 種 (4) 旧描画位置の駅・信号は作らない（旧の線路の扱いを決めるときに決める）。

### ADR 0008 から引き継ぐこと

この ADR は ADR 0008 の「範囲」の項（入れる物・入れない物）を新しくする。次は ADR 0008（と、それが引き継いだ ADR 0002）のまま有効。

- 名前の頭は `ami_`。`build.py` の名前の頭の振り分け（`ami_rail_`・`ami_road_`・`ami_tram`・`ami_canal`）で種類別の pak に入る。全部入りの `ami.pak` も作る
- ライセンスは CC BY 4.0。対象は pak128 の本家 125.0.1 と OTRP
- 狭軌・リニアは入れない（pak128 に車両が無い）。ADR 0008 の「入れない物」は変えない
- 既存の物の名前は変えない
- 速度以外の値（費用・維持費・登場年）は、実装の前に一覧（#110）で決める
- 線路の描画位置は、新描画位置で作る。駅・信号は新描画位置の線路に合わせる。旧描画位置（ADR 0011）の駅・信号は、旧の線路を作る時期に改めて決める（ここでは作らない）

### 範囲に入れる物

| 物 | 扱い | 着手 |
|---|---|---|
| 駅・停留所（`type=stop`）のうち、バス停・トラックの荷役所・線路の駅（旅客・貨物） | 範囲に入れる | 第 5 弾 |
| 線路の信号（roadsign の `waytype=track`） | 範囲に入れる | 第 5 弾は閉塞信号 1 種だけ。ほかの種類は後 |
| 路面軌道の停留所 | 範囲に入れる | 第 5 弾の後（下の理由） |
| 港（`type=stop`・`waytype=water`） | 範囲に入れる | 第 5 弾の後（下の理由） |
| 空港・滑走路・誘導路（`air`）と空港の建物 | 範囲に入れる | 第 5 弾の後。作る前に、本体で何が置けるかを調べて記録か ADR にする |
| 電線と変電所（`power`） | 範囲に入れる | 第 5 弾の後。モノレールの電化（`ami_monorail_power`）と名前が紛れないかを、作る前に確かめる |

- 空港・電線も範囲に入れる理由は、pak256 がインフラを AMI に任せる方針だから。着手を後にするのは、遊べる状態に先に要るのが駅・バス停・信号だから（ユーザーの判断 18）
- 路面軌道の停留所と港を後にする理由: pak128 に路面軌道の停留所の手本が無い（`refs/pak128` の `type=stop` に `waytype=tram_track` の dat が無い。2026-11-25）。AMI は `tram_track` の way を橋脚・盛土・路面表示の飾りに使い、`water` の way を歩道に使っているので、停留所がそれらの上に建てられないかを作る前に確かめる必要がある
- 旅客・郵便・貨物の扱いは、pak256 の仮の物に合わせる。pak128 の線路の駅（`trainstop`）は旅客だけ（`enables_pax=1`）、バス停も郵便を扱わない物が多い（`bus_stops_11.dat`・`bus_stops_21.dat`）ので、「pak128 と同じ」ではない

### 駅・停留所の形

- 第 5 弾の物: `ami_road_bus_stop`（旅客・郵便）、`ami_road_truck_stop`（貨物）、`ami_rail_station`（旅客・郵便）、`ami_rail_freight_station`（貨物）。pak256 の `pak256_bus_stop`・`pak256_truck_stop` を置き換える
- 旅客・郵便の物と貨物の物は分ける。旅客・郵便は `enables_pax=1`・`enables_post=1`、貨物は `enables_ware=1`（pak256 の仮の物と同じ）
- 形は地上の 1x1 タイルで、屋根の無いホーム（線路の駅）と、脇にホームを描いた停留所（道路）から始める。屋根・長いホーム・駅舎の建物（拡張の建物）は、最初の物が出来てから改めて決める
- ホームの長さは、1 タイルずつ並べて決める（本体の決まり）
- `level`（容量）は種類ごとに、最初の issue で決める。道路の停留所は pak256 の仮の物に合わせて 2。線路の駅は pak128 が旅客 9・貨物 3（`rail_stations/trainstop.dat`・`freighttrainstop.dat`）で、仮の 2 では小さいかもしれないので、ゲームで確かめて決める。費用・維持費は `ami_rail_yard` と同じ考え方で決め、一覧（#110）に足す
- 向き: 道路の停留所は 8 通り（連なりの端の絵を持つ）。操車場の 8 通りと同じ本体の仕組み（上の確認）なので、操車場のシートの並びを使い回す。線路の駅は pak128 と同じ 2 通りから始め、端の絵が要るかは線路の駅の issue で決める。OTRP 独自の層（斜めの駅・坂の駅。`hausbauer.cc`）は第 5 弾では作らない（要るかは後で決める）
- 道路の停留所は、AMI の道路（タイル全面が路面、歩道なし）の上に置く。見える側の脇にホームを描き、道路そのものは描かない（pak256 の仮の物と同じ。pak256#44 の確かめで、歩道が脇の帯に少し重なる所があった）。幅の合わせ方は、最初の issue で測って決める

### 信号の形

- 第 5 弾で作る 1 種は、単純な閉塞信号（`is_signal=1`・`waytype=track`）。名前は `ami_rail_signal`
- 後に足す種類: 前方注意・優先・長閉塞・選択信号と選択の終わり（本体が持つ 6 つ。上の確認）。pak128 の一方通行の信号（`OneWaySignals`。`single_way=1`）は入れるかを、そのときに決める。入換に使う専用の種類は本体に無く、選択信号で足りるかを作る前に確かめる
- 作りは道路標識より重い。信号は状態ごとに向きの絵を持ち、画像の数が 8 を超えると電化の組（`obj/signal.cc` の offset 8・12）を使う。OTRP には斜め・前景・左側用の追加画像のリスト（`descriptor/roadsign_desc.h`）もある。既存の `roadsign_dat_text` は `image[0..3]` の 4 枚だけなので、閉塞信号の issue の最初に、状態と向きの絵の枚数、電化の組を作るか（AMI は架線を壁の way-object に持たせていて、柱と重ならないか）、追加画像を makeobj が書けるか（この checkout の `roadsign_writer.cc` は追加画像のリストを書いていない。未確認）を調べて決める
- 左右: 線路の信号は、道路標識の `ROADSIGN_OFFSET_LEFT`（左側通行 `traffic_left`）ではなく、別の設定 `signals_on_left`（`obj/signal.cc`・`dataobj/settings.cc`。既定は右）で左右が決まる。`ROADSIGN_OFFSET_LEFT` をそのまま使えるかは、閉塞信号の issue で確かめる
- OTRP 独自の信号の機能を使うかは、閉塞信号の issue で追加画像を調べた結果で決める

### 順番

ADR 0008 の第 2 弾（#112〜#123）はすべて閉じていて、列はもう動いていない。駅・信号は新しい物なので、触る部品は重ならない。

第 5 弾は次の 3 つ。駅・停留所は `ami_dat.py` の建物の生成、信号は roadsign の生成と、触る関数が別なので、同時に進められる。描画のシートの対象の一覧（`catalog.py`）は両方が書き足すので、PR でぶつからないよう、足す箇所を分ける。

| 順 | 駅・停留所 | 信号 |
|---|---|---|
| 1 | 道路の停留所（`ami_road_bus_stop`・`ami_road_truck_stop`）。pak256 の仮の物を置き換える | 閉塞信号（`ami_rail_signal`） |
| 2 | 線路の駅（旅客・貨物） | |

第 5 弾の後: 前方注意・優先・長閉塞・選択信号、路面軌道の停留所、港、空港、電線。

### 名前と pak

- 名前は `build.py` の名前の頭の振り分けにそのまま当たる形にする。駅・停留所はその waytype の pak に、信号は線路の pak に入る。路面軌道の停留所は `ami_tram_stop`、港は `ami_canal_port`（どちらも着手は後）。`round.py` の `ami_road_*` の対象に停留所の dat が干渉しないかは、最初の issue で確かめる
- 置き換える名前の対応:

  | pak256 の仮の物 | 控え（`obj`・`type`・`waytype`） | AMI の物 |
  |---|---|---|
  | `pak256_bus_stop` | `building`・`stop`・`road`（旅客・郵便） | `ami_road_bus_stop` |
  | `pak256_truck_stop` | `building`・`stop`・`road`（貨物） | `ami_road_truck_stop` |
  | `pak256_road_depot` | `building`・`depot`・`road` | `ami_road_depot`（#261 の D で組める） |

- 置き換えは pak256 の側で行う（`docs/stations.md` の手順）。保存データは物の名前で引くので、置き換えると置いてあった停留所は消える。配布の前に置き換える

### 大きさ（pak の大きさの対応）

駅・停留所・信号は、#261 と同じ道具で描く。シートの大きさ・オフセットは `sheet_settings.SCALE`、左側通行のずらしは大きさによらない既存の定数を使う。`catalog.SCALED_SHEETS` に足して `check_scaled.py` の検査の対象にする（対象の一覧は `src/*.dat` と突き合わせて作る。シートの無い dat を取りこぼさない。#261 の C のフィードバック）。

## 検討した代替案と却下理由

- 駅・停留所・信号を範囲に入れず、pakset ごとに作る → pak256 が AMI にインフラを任せる方針（2026-11-24）と合わない。仮の物を置き換える先が要る
- 駅と信号だけを入れて、空港・電線は入れない → 範囲の見直しをもう一度要する。入れること自体を今決めておく方が、pakset の側が計画を立てられる
- 旅客と貨物を 1 つの駅にまとめる → pak128・pak256 の仮の物と分け方が違い、駅の見た目で扱う荷が分からなくなる
- 信号を最初から全種類作る → 遊べる状態に先に要るのは 1 種。種類ごとに絵と確認が要るので、閉塞信号で作りを固めてから足す
- 線路の駅も 8 通りの向きで作る → pak128 の線路の駅は 2 通りで足りている。端の絵が要ると分かってから足す

## 影響・トレードオフ

- 建物（`stop`）が増えるので、シートの数と描画の時間が増える。描画は共有の枠（`SHEET_SLOTS`）で順番待ちになる
- 道路の停留所は、道路の向き（左側通行・右側通行）と歩道（`ami_sidewalk`）の有無で見え方が変わる。最初の issue で、道路の 4 種と歩道つきで確かめる
- 信号が路面軌道・標識（`ami_sign_*`）と同じタイルに置けるかは、閉塞信号の issue で確かめる
- 旧描画位置の線路用の駅・信号は作らない。旧の線路を作る時期に改めて決める（ADR 0011）
- 空港・電線は、範囲に入れただけで、種類と形は決めていない。着手の前に、それぞれ記録か ADR を書く
- 第 5 弾を配るときに、配る zip に新しい物を入れるかは、そのときに決める（ADR 0008 と同じ）
