# 調査/作業ログ: スクリプトで編成のダイヤを設定できない原因（検証用フォルダの script/ が古い）

（2026-11-18。[2026-11-13_otrp-script-change-schedule.md](2026-11-13_otrp-script-change-schedule.md) の原因調査。結論: 本体のバグではなく、検証環境の不備）

## 結論

アドオンを確かめるゲームのフォルダ（`addon_check`）の `script/` が、本家 125.0.1 のものと同一だった。
本家の `script_base.nut` の `schedule_entry_x` は `coord3d` を継承するだけで、`(pos, load, wait)` を受ける作りが無い。
OTRP の `script_base.nut`（`schedule_entry_x` は座標・load・wait・flags を持ち、`constructor(pos, l, w, f = 0)`）と食い違い、座標が壊れる。

## 経緯

1. 前回の見立て（本体で `schedule_t::append` が失敗するか）と、次の仮説（`lookup` が高さ z を厳密に見るので z=0 が合わない）を立てた。
2. z の仮説は外れた。`flat_512` の地面は z=0 で、同じ手順を流しても同じエラーになった（OTRP v64_3、plain な線路・駅・車庫）。
3. `-debug 4` で起動して標準出力を取ると、`schedule_t::append(): forbidden stop at 0,0,0` が 2 回出た。項目の座標が壊れて 0 になり、停留できない場所として捨てられ、項目数が 0 になって例外になる。
4. `schedule_entry_x(coord3d(103,40,0), 5, 7)` の `x`・`y`・`z` を読むと、`x=103,40,0`（座標のオブジェクトそのもの）、`y=5`、`z=7`、`load=0`、`wait=0` だった。コンストラクタの引数が `coord3d` の `(x, y, z)` に入っている。
5. `addon_check/script/` は 125.0.1 の `script/` と同一で、`otrp_dev/script/` とは `script_base.nut`・`scenario_base.nut`・`new_scenario_template.nut` の 3 つが（行末を除いて）違った。リポジトリの `simutrans/simutrans/script/script_base.nut` と `otrp_dev` のものは同じだった。

## 直したこと

- `addon_check/script/` の `script_base.nut`・`scenario_base.nut`・`new_scenario_template.nut` を `otrp_dev/script/` のものに差し替えた。元のファイルは `addon_check/script/_stock_125.0.1/` に退避した。
- 直した後、`blender-poc` の `ingame/train.nut`（線路は pak128 の標準の線路に替えて流した）で、ダイヤの設定が通り、編成が出発して走った（`flat_512`、OTRP v64_3。数秒後に `111,40,0`、速度 75）。

## 確かめていないこと

- OTRP v63_3 の exe で、差し替え後の `script/` が動くか。`script_base.nut` は Squirrel だけの変更だが、v63_3 を新しい `script/` で動かす確認はしていない。
- `125.0.1` 側（本家）は変えていない。本家には OTRP の `schedule_entry_x` の作りが無いので、本家の確認でダイヤを付けるスクリプトは使えない。
