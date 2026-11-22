# 作業ログ: AMI の旧描画位置の線路に、高架・橋脚・橋・トンネルを足す（#26 の 2 本目）

（2026-11-22）

## 目的 / 発端

1 本目（PR #176。[記録](2026-11-22_ami-old-draw-position-seam.md)）で、旧描画位置の通常の版・基盤・壁・架線つきの壁を作った。2 本目で、高架 4 版・橋・トンネルと旧用の橋脚（単柱・門型）を足した（[ADR 0011](../adr/0011-ami-old-draw-position-separate-pak.md)）。

## やったこと

- `catalog.ALL_TRACKS`（新と旧）を、`render.py`・`ami_dat.py` の高架・橋・トンネルの導き方に広げた。旧の高架・橋は旧の基盤の版の設定から導かれるので、基準面を動かさない（`datums=FLAT`）ことが引き継がれる
- 旧用の橋脚（`ami_pier_rail_old`・`ami_pier_rail_old_gate`）は、`R.pier_sheet`・`R.pier_gate_sheet` に旧の基準面（`R.FLAT`）を渡して描く。dat・アイコンの背景色・一覧の種類は新の橋脚と同じ扱い
- ラウンドの道具 `blender/round.py` の glob（`ami_wall_rail_*`・`ami_rail_slab_*` など）が旧の dat・シートに合ってしまうのを、旧を除くようにして直した（#26 の 1 本目のレビューの指摘）
- 見本 `ingame/sample.nut` は、`TRACK` が旧のとき橋脚の名前も旧にする
- 旧の 56 個（way・基盤・高架・橋・トンネル 4 種分 + 壁・架線・橋脚）は `ami_rail_old.pak` に入る（`build.py` が警告なしで通り、分岐の追加画像 40 個を継ぎ足す）

## 測ったこと・確かめたこと

2026-11-22、`addon_check` の `OTRPv64_3.exe`、`flat_512.sve` の温暖側。

- `ingame/beta_check.sh`（`PAKS=dist/ami_rail_old.pak`）: 旧の 56 個が全部、道具で敷けた。ログに AMI の警告なし
- 新の描き直し（`render_parallel.py` で `ami_pier_rail`・`ami_pier_rail_gate`・`ami_rail_ballast_base_single`・`ami_rail_slab_elev_back`・`ami_rail_concrete_bridge`）で、src/ の新のシートが 1 画素も変わらないことを `git status` で見た（橋脚のラムダを書き直した退行の確認。ACCEPTANCE の 10-3）。なお `ami_rail_ballast_base_single` だけを描くと壁のシート `ami_wall_rail_single.png` のアイコンが描画時の仮の物に戻る（アイコンの書き込みは壁のシートを対象に指定したときだけ。この変更の前からの動き）ので、戻した
- `ingame/sample_parallel.sh`（`TRACK=ami_rail_ballast_old`・`PAK=dist/ami_rail_old.pak`）で、高架（VS・VF）・門型の橋脚（G）・橋（BT_B1・B2・B4）・トンネル（BT_T1・T2）の区画を敷き、新（`TRACK=ami_rail_ballast`・`PAK=dist/ami.pak`）と同じ区画を並べた（`addons/ami/docs/old_elev_a.png`・`old_elev_b.png`）。撮り方: アドオンのディレクトリで `GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> TRACK=ami_rail_ballast_old PAK=dist/ami_rail_old.pak SEASONS=temperate:20:20 OUT=<旧の出力> SPOTS="VS_AFC:88:32 VF_AFC:88:122 G_AFC:168:2 BT_B1:167:131 BT_B2:164:151 BT_B4:168:168 BT_T1:164:174 BT_T2:164:180" bash ingame/sample_parallel.sh`、新は `TRACK=ami_rail_ballast PAK=dist/ami.pak` で同じ SPOTS。並べるのは `uv run ingame/old_sample_compare.py <新の出力> <旧の出力> docs/old_elev_a.png VS_AFC VF_AFC G_AFC`（橋・トンネルは `docs/old_elev_b.png` に BT_B1 BT_B2 BT_B4 BT_T1 BT_T2）。旧は、柱・橋・坑口が新と同じ形で、床と橋脚がつながって見える。見本の敷設は失敗なし

## 確かめていないこと

- 雪の側（x=256〜）、足元・柱の上端の 1〜2px の合い方、車両との重なり、本家 125.0.1 での読み込み
- 旧の高架・橋と SIS の継ぎ目（SIS に高架・橋の手本の pak を入れていない）
- 在来線以外の 3 種（直結・ラダー・スラブ）の高架・橋・トンネルの見た目（在来線だけ画像で見た。描画と敷設は 4 種とも通った）
