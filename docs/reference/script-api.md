# 本体のスクリプト API（Squirrel）の控え

ゲームの見本（`addons/*/ingame/*.nut`）で、建てた物を確かめるときに使う本体のスクリプト API と、駅の建て方の癖。作業の手順は書かない。

- 本体のソースは `E:\addon_dev\simutrans\script\api\`（OTRP の fork）。名前を探すときは、`register_method` や `create_class` の行を `grep` する
- 各項目に確かめた場所と日付を書く。ゲームで動かして確かめたものは「ゲームで確認」と書く

## 1. 貨物

| 使い方 | 意味 | 確かめた場所（日付） |
|---|---|---|
| `foreach (g in good_desc_list_x()) { … }` | 全貨物（`good_desc_x`）を回す。貨物の名前を決め打ちしなくてよい | `script/api/api_obj_desc.cc` の 683〜699 行（`good_desc_list_x`。`_nexti` が `get_next_ware_desc`）。ゲームで確認（2026-11-25） |
| `g.get_catg_index()` | 貨物の分類。0 = 旅客、1 = 郵便、2 = なし、3 以上 = それ以外（貨物） | `api_obj_desc.cc` の 726〜729 行（2026-11-25） |
| `good_desc_x.passenger`・`good_desc_x.mail` | 旅客・郵便 | `api_obj_desc.cc` の 720〜721 行（2026-11-25） |

貨物を「名前の決め打ち」で探すと、pakset によって名前が違い、1 つも引けないまま「受け取らない」と判定して通ってしまう。`good_desc_list_x` を回し、`get_catg_index() > 2` の貨物が 1 つ以上あることを確かめてから、駅が受け取るかを見る。

## 2. 駅（halt）と建物

| 使い方 | 意味 | 確かめた場所（日付） |
|---|---|---|
| `square_x(x, y).get_tile_at_height(z).get_halt()` | そのタイルの駅（無ければ null） | `script/api/api_tiles.cc` の 185 行（`get_halt`）。ゲームで確認（2026-11-25） |
| `halt.accepts_good(good_desc_x)` | その貨物を扱うか（旅客・郵便・貨物とも） | `script/api/api_halt.cc` の 301 行。ゲームで確認（2026-11-25） |
| `halt.get_tile_list()` | 駅のタイルの一覧。`foreach` でも `.len()` でも数えられる | `api_halt.cc` の 360 行。ゲームで確認（`.len()` が 2 を返した。2026-11-25） |
| `halt.get_name()` | 駅の名前。建物の名前ではない | ゲームで確認（2026-11-25） |
| `tile.find_object(mo_building)` | タイルの建物（`building_x`）。停留所・車庫など | `api_tiles.cc` の 168 行、`script/api/api_const.cc` の 254 行（`mo_building`）。ゲームで確認（2026-11-25） |
| `building.get_desc().get_name()` | 建物の `dat` の `name`（例 `ami_road_bus_stop`） | `script/api/api_map_objects.cc` の 615 行（`gebaeude_t::get_tile` を `get_desc` の名前で公開している）。ゲームで確認（2026-11-25）。`get_desc().get_desc()` は無い（「index 'get_desc' does not exist」） |
| `building.get_name()` | 常に `Gebaeude`（建物の種類の名前）で、`dat` の名前ではない | ゲームで確認（2026-11-25） |

## 3. 3 タイルの連なりは、端から順に建てる

`command_x.build_station(pl, coord3d, building_desc)` で連なりの停留所（道路の停留所や操車場）を並べるとき、**端から順に建てる**。真ん中を最後に建てる並び（4 → 6 → 5）にすると、5 は片側の駅にしかつながらず、もう片側は別の駅の飛び地になる。

- ゲームで確認（2026-11-25、`addons/ami/ingame/road_stop_sample.nut`、`flat_512_left_v64`）: 4 → 6 → 5 の順で建てると、`halt.get_tile_list().len()` が 2 で、駅の名前が 2 つに分かれた（建設後の画面でも隣り合う 2 つの駅名の札が出た）。4 → 5 → 6 の順で建てると 3 になり、1 つの駅になった（道路 3 種 × 温暖・降雪の 30 か所）
- 原因は、本体の駅の建て方の読みでは未確認（推測: 建てるタイルに隣り合う駅が複数あるとき、つなげるのは 1 つだけ）。つなげたい操作は、端から順に建てて回避する
