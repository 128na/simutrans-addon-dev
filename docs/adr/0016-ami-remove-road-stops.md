# ADR: AMI から道路の停留所を外す（ADR 0015 の「停留所は残す」を置き換える）

> ステータス: Accepted (2026-11-26)。[ADR 0015](0015-ami-scope-back-to-iss.md) の停留所の扱い（残す）を置き換える。0015 のほかの決定は有効
> 由来: [#297](https://github.com/128na/simutrans-addon-dev/issues/297)・[#277](https://github.com/128na/simutrans-addon-dev/issues/277)・[#292](https://github.com/128na/simutrans-addon-dev/issues/292)・pak256#94

## 背景と問題

ADR 0015 は、道路の停留所（`ami_road_bus_stop`・`ami_road_truck_stop`）を pak256 の間借り用として残し、pak256 が自前の停留所を用意したら外すと決めた。外すのは pak256 の進捗管理から「自前を用意した」と知らせが来てからで、別の issue にするとした。

2026-11-26 に、pak256 の進捗管理から知らせが来た。自前の停留所は pak256#94 で作り、PR #97 でマージ済み。名前は `pak256_bus_stop`（旅客・郵便）と `pak256_truck_stop`（貨物）。AMI の停留所は外してよい。ADR 0015 が置いた外す条件が満たされた。

## 決定

- `ami_road_bus_stop`・`ami_road_truck_stop` を AMI から外す。dat（`src/`・`src256/`）・画像・生成コード（`ami_dat.py`・`catalog.py`・`icons.py`・`render.py`・`lineup.py`・`sheetlib/road_stop.py`）・訳（`ja_ami.tab`）・README・見本のスクリプト（`ingame/road_stop_sample.nut`）・確認画像を消す。
- 作り直さない。停留所は AMI の範囲に入れない（ADR 0015 が決めた「iss にある物に戻す」のとおり）。
- ADR 0015 の、停留所以外の決定（範囲を iss にある物に戻す・閉塞信号を外す・線路の駅などは作らない）は、そのまま有効。

## 検討した代替案と却下理由

- 残したままにする → pak256 が自前を用意したので使われない。pak と訳とカタログに、保つ手間だけが続く
- 非推奨として残す → 同じ理由。ADR 0015 でも信号を同じ理由で消した

## 影響・トレードオフ

- 2 つの名前は pak（`ami_road.pak`・`ami.pak`）から消える。この名前の停留所を置いた保存データは、読み込むと停留所の建物が消える。使う者は pak256 の側にいない（pak256 の進捗管理が、自前に切り替えたと知らせている）
- 停留所の作りで確かめた知見は、本体の決まりとして `docs/reference/script-api.md`（連なりは端から順に建てる）に残る。作りの詳細は #277 の PR と ADR 0014 に残る
- 外した後に停留所が必要になったら、新しい issue と ADR で決める
