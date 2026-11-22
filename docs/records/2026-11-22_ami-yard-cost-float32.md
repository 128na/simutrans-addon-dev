# 操車場の建設費が 576 cr・640 cr に見えた理由（#160）

操車場 `ami_rail_yard` の dat は `cost=60000`（600 cr）だが、ゲームで建てると所持金の減りが 576 cr・640 cr になった（記録 `2026-11-22_ami-rail-yard.md`）。理由を調べた。

## 結論

建設費はずれていない。測り方が原因だった。スクリプトの `get_current_cash()` は 32 ビット浮動小数で、検証用の保存データ `flat_512` は残高が大きく負（測ったときの値は -6.54877×10^8 cr）なので、この大きさでは数値の刻みが 64 cr になり、差が 64 の倍数に丸められる。

## 調べたこと

- 本体（`E:\addon_dev\simutrans`、2026-11-22）の費用の式: `simtool.cc` の駅の建設（5816 行付近）は `-desc->get_price(welt) * get_x() * get_y() * platforms`。`building_desc_t::get_price`（`descriptor/building_desc.cc`）は、dat に `cost` があればその値をそのまま返す（`building_reader.cc` が読んだ値を持つ）。建てるプレイヤーが公共プレイヤーでなく、かつ駅の持ち主でもないときだけ、維持費 × 60 が足される（`simtool.cc` 5822 行）。自分の駅には掛からない。式からは 600 cr になる
- 仮説: 残高が大きくて float の刻みに丸められる。`get_current_cash()` は `player_t::get_account_balance_as_double`（`player/simplay.cc` 947 行。`get_account_balance() / 100.0`）で、`script/api/api_player.cc` 280 行が Squirrel に登録していて、Squirrel の float は 32 ビット。5.4×10^8〜1.07×10^9 は 1 刻みが 2^6 = 64、576 = 9×64、640 = 10×64
- 実測（`OTRPv64_3.exe`、`flat_512`、dist/ami.pak、`addons/ami/ingame/cost_probe.sh`）。同じ線路に連続して建てた結果:

  | 建物 | 所持金（float）の差 | 純資産（整数）の差 |
  |---|---|---|
  | 操車場 1 個目 | 640 cr | 60000（600 cr） |
  | 操車場 2・3・4 個目 | 576 cr | 60000 |
  | 乗客の駅（pak128 の一覧の先頭。`get_cost()` も 60000） | 640 cr | 60000 |
| 車庫 `ami_rail_depot`（dat `cost=850000`） | 8512 cr（= 133×64） | 850000（8500 cr） |

  - 所持金の差は建てる前の残高で変わり（位置・順序で 640 と 576 に分かれた）、純資産の差は毎回 60000。乗客の駅も同じずれ方をしたので、操車場の値の問題ではない
  - 線路 31 タイルの建設費も 4608 cr（= 72×64）と、64 の倍数で出た
  - 降雪側（原点 276,20）の 640 cr は測り直していない。残高が同じ範囲なら同じ丸めで説明できる
- 維持費: dat の `maintenance=1800` が、スクリプトの `get_maintenance()` では 3600 になる。API が月の長さで掛ける（`scale_with_month_length`、`script/api/api_obj_desc.cc`）。保存データの月の長さの設定のためで、dat の値は変わっていない

## ほかの駅・車庫

- 乗客の駅と車庫（式は別。`tool_build_depot_t`、`simtool.cc` 7018 行は `-get_price` のみ）も、純資産の差は dat の値のとおりだった。所持金の差のずれは同じ丸めで説明できる。dat の `cost` を直す必要は無い
- 車庫の AMI の dat は 5 種ある。測ったのは `ami_rail_depot` だけで、ほかは式が同じなので測っていない

## 確かめていないこと

- 降雪側の実測
- 残高が小さい保存データでの、所持金の差そのもの（純資産の差で足りるため）
