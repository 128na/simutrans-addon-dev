# 調査/作業ログ: 第 2 弾の物の値を iss・pak128 と比べて決める（#110）

（2026-11-21）

## 目的 / 発端

[ADR 0008](../adr/0008-ami-scope-second-phase.md) に、「速度以外の値（費用・維持費・登場年）は、実装の前に一覧で決める」とある。第 2 弾で足す物の値の案を作り、ユーザーに決めてもらった（[#110](https://github.com/128na/simutrans-addon-dev/issues/110)）。案は iss（`refs/iss/src`）と pak128（`refs/pak128`）の同じ種類の値と並べ、第 1 弾の AMI の値と釣り合いが取れるかを見た。決めた値は [addons/ami/README.md](../../addons/ami/README.md) の「今の決まりごと」にある。

## やったこと

- iss と pak128 の dat から、第 2 弾の物と同じ種類の物の値を抜き出した。値は `obj`・`waytype`・`cost`・`maintenance`・`topspeed`・`intro_year` など。
  - iss で見たのは `building/depot`・`util/rail_misc`・`way/monorail`・`way/water`・`crossing`・`sign/road`・`way-object/road`・`util/sidewalk`・`util/road_misc`・`util/embankment`。
  - pak128 で見たのは `infrastructure/` の `depots_rail_road_tram`・`schwebebahn_all`・`water_all`・`*_crossings`・`road_signs`・`rail_tracks`・`roads`・`tram_tracks`。
- pak128 の車両のうち、モノレール（`monorail_track`）と船（`water`）の最高速度を数えた。
- `../simutrans`（OTRP）で、building・crossing・roadsign の値のキーと単位を読んだ。決まりは [way-addon.md](../reference/way-addon.md) の 5 章に足した。

## 分かったこと（事実）

### 比べた値

費用・維持費は 1/100 cr。標識だけは cr 単位で書く。

| 物 | iss | pak128 | AMI 第 1 弾で釣り合いを見る値 |
|---|---|---|---|
| モノレール | `iss_wmg_0120_straddle` ほか（跨座・懸垂とも）: 120 km/h・50000・1000・1900 | `Schwebebahn_p_ground`（懸垂の地上）: 150 km/h・150000・1750・1901。`Suspended_Monorail_Track`（懸垂の高架）: 150 km/h・210000・1500・1901 | 在来線の高架 160 km/h・30000・600。高速線 480 km/h・40000・800 |
| 運河 | `iss_wwg_0050`・`iss_wwg_0100`: 50 と 100 km/h・25000・500・1900 | `canal_020`: 20 km/h・200000・400・1700。`canal_030`: 30 km/h・400000・800・1850 | 在来線 15000・300 |
| 車庫 | `iss_u?d_depot`（7 種）: 費用・維持費を書かない | `TrainDepot`・`CarDepot`・`TramDepot`・`MonorailDepot`・`ShipDepot`: 費用・維持費を書かない | – |
| 操車場 | `iss_uts_yard`（`type=stop`）: 費用・維持費・level を書かない | 無い | – |
| 水路の踏切 | 線路 120×水路 50、道路 50×水路 50 | 線路 160×水路 25、道路 100×水路 25 | – |
| 線路×道路の踏切（参考） | 道路 30・50 × 線路 120・240・360 ほか | 道路 40×線路 80、道路 90×線路 160 | – |
| 中央分離帯・壁 | `iss_or_center_divider_*`・`iss_or_side_wall_*`・`iss_or_side_wall_*_and_center_divider_*`: 65535・1000・100 | 無い | 道路の壁 1000・3000・60 |
| 歩道 | `iss_wwg_sidewalk*`（地上）・`iss_wwe_sidewalk*`（高架）: water・65490・10・1 | 無い | 歩道 1・1000・20 |
| 歩道の壁 | `iss_ow_side_wall_*`: water の way-object・65535・1000・100 | 無い | 道路の壁 |
| 電柱 | `iss_or_utility_pole`: road の way-object・65535・1・1 | 無い | 歩道 |
| 路面表示 | `iss_wsg_intersection*`・`iss_wsg_yellow_line` ほか: tram_track の way・65500〜65502・1000・100 | 無い | 道路 3 種 |
| 道路標識 | `iss_sr_*`: 1000 cr | `NoEntry`・`Minimum80` など: 500 cr。`RoadClosed`: 1000 cr。高速道路の出入口: 1500〜2000 cr | – |
| 盛土 | `iss_wte_embankment*`: track の高架の way・65480・100・10 | 無い | 橋脚 1・1000・100 |

- pak128 の車両の最高速度は、モノレールが 150 km/h（`PMNV_TC-119-Snake`）、船が 53 km/h。
- 第 1 弾の AMI の線路は、pak128 の約半分の費用。在来線は 15000 で、pak128 の `Rail_160_Tracks` は 32000。

### 本体の決まり

詳しくは [way-addon.md](../reference/way-addon.md) の 5 章。

- building の `cost`・`maintenance` は、書かないと pak の `simuconf.tab` から決まる。
  - `level` を書かないときは level 1 になる（車庫・停留所は、writer が 1 を戻す）。
  - pak128 の値は次のとおり。車庫の費用は 8500・7000・9000 cr。停留所の費用は 600 cr × 面積。維持費はどちらも 1800。
- crossing には、費用・維持費のキーが無い。速さは、踏切のタイルの way の速さを縛る。
- roadsign には、維持費のキーと、速さの上限のキーが無い。

## 推測・未確認事項

- 最初の案では、「level を書かないと 0 になり、車庫の維持費と操車場の費用・維持費が 0 になる」と書いた。push の前のレビューで、`building_writer.cc` の 222 行付近の `++level` を見落としていたと分かり、訂正した。
- 車庫・操車場の値がゲームの中でどう効くかは、ソースから読んだだけで、試していない。
- 運河と歩道は、どちらも waytype が water になる。並べて敷いたときにつながるかは、#114 で確かめる（ADR 0008）。

## 結果どうしたか

ユーザーが、#110 のコメントで次のとおり決めた（2026-11-21）。

- 方針と一覧は、案のとおり採る。
- モノレールは 30000・600 にする。iss の 50000・1000 だと、高速線（40000・800）より高くなるため。
- 車庫・操車場は、0 や省略を避けて、pak128 の既定値と同じ値を dat に明示する。省略や 0 は、考慮漏れでクラッシュすることがあるため。
- 一覧は、AMI の README の「今の決まりごと」に置く。

一覧を書いた PR は [#131](https://github.com/128na/simutrans-addon-dev/pull/131)。
