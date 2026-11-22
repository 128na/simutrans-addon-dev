# ADR: AMI の旧描画位置（SIS に合う線路）は `_old` の名前で別の pak にまとめる

> ステータス: Accepted (2026-11-22)
> 由来: [#26](https://github.com/128na/simutrans-addon-dev/issues/26)・[ADR 0002](0002-ami-scope.md)・[ADR 0008](0008-ami-scope-second-phase.md)

## 背景と問題

ADR 0002 と ADR 0008 は、線路の描画位置を「新描画位置（今の pak128・iss に合う）で作り終えてから、旧描画位置（SIS に合う）をまとめて作る」と決めた。新描画位置の線路は、レールが地面より約 4px 下にある。SIS の新幹線の線路は旧描画位置で、レールは地面の位置にある。AMI の線路を SIS の線路につなぐと、レールが数 px ずれて見える。

旧描画位置の線路を作るとき、次の 3 つが決まっていなかった。

- 旧の名前
- 配布の pak への入れ方
- 作る範囲（壁・架線・橋脚を含めるか）

確かめたこと（2026-11-22、`addon_check` の OTRP、SIS の `SIS_ST_TGbl_E01-999B`）:

- 旧の絵は、基準面を動かさず（`datums=FLAT`）、持ち分を手前へはみ出させない（`spill=0`）ことで作れる。blender-poc の旧描画位置（`TRACK_PROFILES["old"]`）と同じ。部品・材質・寸法は新と同じ
- 壁・架線・橋脚は、基準面 `bed`（新は 2px 下）に合わせて描かれている。旧の基盤・高架を基準面なしで作ると、共有の壁・橋脚と 2px 合わない。旧用の壁・架線・橋脚も要る
- 同じ速さの way が複数あると、橋・高架で「橋の上に載る way」が名前のハッシュの順で決まる（[way-addon.md](../reference/way-addon.md) の 5 章）。旧を `ami.pak` に入れると、新の橋に旧の way が載りうる

## 決定

2026-11-22 のユーザーの決定（#26 で、作業者の案のおすすめを採った）。

- 名前: 軌道の種類を足す形で、`rail_ballast_old`・`rail_concrete_old`・`rail_ladder_old`・`rail_slab_old`（`catalog.OLD_TRACKS`）。way は `ami_rail_<種類>_old`、版は今の付け方のまま `_old` の後に付く（`ami_rail_ballast_old_base_<版>`・`_elev_<版>`・`_bridge`・`_tunnel`）。旧用の壁・架線・橋脚は `ami_wall_rail_old_<版>`・`ami_wall_rail_old_<版>_catenary`・`ami_wall_rail_old_twin`・`ami_wall_rail_old_twin_catenary`・`ami_pier_rail_old`・`ami_pier_rail_old_gate`。既存の名前は変えない
- 範囲: 線路 4 種の通常・基盤 4 版・高架 4 版・橋・トンネルと、旧用の壁・架線・橋脚。速さ・費用・維持費・登場年は新と同じ。路面軌道（もともと基準面を動かさない）・モノレール・道路・踏切は旧を作らない。旧の線路には踏切を作らない（踏切のレールは新の基準面）
- pak: 旧の物は、全部入りの `ami.pak` と種類別の pak に入れず、`dist/ami_rail_old.pak` 1 本にまとめる（`build.py` の `belongs`。名前の頭でなく `catalog.is_old` で決める）。SIS と並べて使う人だけが読み込む。旧の way・壁・橋脚が 1 つの pak で完結する
- 作る順: 通常・基盤・壁・架線（1 本目の PR）、高架・橋脚・橋・トンネル（2 本目の PR）
- 受け入れ条件は [ACCEPTANCE.md](../../addons/ami/ACCEPTANCE.md) の 10 章

## 検討した代替案と却下理由

- 旧を `ami.pak` に入れる → SIS を使わない人の道具のメニューに、同じ種類が倍になって出る。橋に載る way が旧になる事故が起きる
- 旧の way だけを作り、共有の壁・橋脚を使う → 基盤・高架で壁・橋脚と 2px ずれる
- 旧の名前を `ami_rail_old_<種類>` にする → `catalog.Track` の名前の導き方（`_base_<版>` など）と、`build.py` の名前の頭の振り分け（`ami_rail_`）をそのまま使えない
- 新と旧を 1 つの描き方の切り替え（同じ名前に版を足す）にする → 同じ名前の way が 2 つになり、ゲームで見分けられない

## 影響・トレードオフ

- 描くシートが線路 4 種 × 14 + 壁・架線・橋脚で、新と同じだけ増える（描画は並列で約 5 分）。新の絵・dat は変えない
- 旧用の壁・橋脚は、新と絵の位置だけが違う。新の壁・橋脚を直したら、旧も描き直す（`render.py` は新から旧を導くので、設定の変更は旧にも効く）
- 旧の線路と新の線路をつなぐと、レールが数 px ずれる（新と旧は別の物として使う）
- `ami_rail_old.pak` を配るかは、配るときに決める（[ADR 0007](0007-ami-beta-distribution.md) は第 1 弾のベータの決定）
