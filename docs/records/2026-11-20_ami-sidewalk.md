# 作業ログ: AMI の歩道（#24）

（2026-11-20）

## 目的 / 発端

手順の一覧（#27）の 12 番目。道路の隣のタイルに敷く歩道の way（`ami_sidewalk`）を作り、付属の pak（`ami_extra.pak`）に入れる。ADR 0003 のとおり、歩道は道路に描かず別の way にする。決めることは歩道の waytype（iss は `water`）。

## 分かったこと（事実）

- iss の歩道（`../refs/iss/src/util/sidewalk/`）は、タイル全面の敷石の絵が 2 枚（東西向き・南北向き）だけで、つながりで絵を変えない。縁石は別の way-object（`wall.dat`、`waytype=water`）。`water` の版（`ground.dat`、`iss_wwg_sidewalk*`）と `road` の版（`ground_road.dat`、`iss_wrg_sidewalk*`）がある
- iss のビルド済みの `iss_util_sidewalk.pak` を AMI の道路の隣に敷いて比べた（`OTRPv64_3.exe`、`flat_512.sve`）:
  - `water`: 道路の隣に敷いても道路の向き・絵は変わらない。平地・坂・急坂に敷ける。歩道の列を道路が横切ると、そのタイルは 2 本の way になり、pak128 の運河の踏切（跳ね橋）が立つ。pak128 の運河 `canal_020` を横切らせると、そのタイルは運河に置き換わる
  - `road`: 横切る道路が歩道のタイルを置き換え、歩道と道路がつながる
- 本体は斜めの絵（`diagonal[...]`）の無い way にカーブの絵を使う（`../simutrans` の `boden/wege/weg.cc` の `calc_image`。斜めの絵は `desc->has_diagonal_image()` のときだけ選ぶ）。歩道は斜めの絵を持たなくてよい

## 直したこと

- `tools/blender/sheetlib/sidewalk.py` を足した（`sidewalk_sheet`）。絵は自分のつながりだけで決まり、タイル全面の板（縁石の色）と敷石を、つながらない辺で縁石の上面の幅だけ内へ下げる。寸法・材質は `road_parts` の歩道（`SIDEWALK_H`・`CURB_W`・`curb`・`paving`）、雪は雪の材質。絵の位置は道路と同じ `ROAD_CY` で、持ち分は地面の菱形を上へ 3 行広げた（奥の辺の縁石の上面の帯を残す）
- `addons/ami/blender/` の catalog・render・ami_dat・addon_config に `ami_sidewalk` を足した。waytype は iss と同じ `water`（`SIDEWALK_VALUES`）。dat は直線・行き止まり・1 タイル・カーブ・T字・十字・坂・急坂の夏と雪
- 見本 `ingame/sidewalk_sample.nut` と撮る場所 `sample_spots.sh` の `SIDEWALK_SPOTS`（24 か所）

## 確かめたこと

（2026-11-20、`OTRPv64_3.exe`、`flat_512.sve`、`NUT=ingame/sidewalk_sample.nut bash ingame/sample_parallel.sh`。道路 4 種（`ami_road_local`・`ami_road_general`・`ami_road_expressway`・`Road_050`）、温暖側と降雪側）

- 全区画が敷けた（返り値の先頭が `ok`）。敷いた後も道路の向きと絵が変わらない（`road=same`）。交差点の隣の歩道は西と北の L字（`corner(5,1)=9`）
- 道路との境の 4 方向に縁石の帯が出て、草のすき間が無い（5 倍の拡大。`addons/ami/docs/sidewalk_GE_R_zoom.png`）。手前の辺（南・東）は立ち上がりも見える
- 坂・急坂の継ぎ目で縁石が折れ、段が無い（4 倍の拡大）
- 斜めの道路の隣では、道路のタイルの角の三角に草が見える（`addons/ami/docs/sidewalk_GE_D.png`）。三角は道路のタイルの持ち分なので、歩道の絵では埋めない
- 区画 X: 道路を横切らせたタイルは `two_ways=true` で踏切の物（型 29）が立ち、運河を横切らせたタイルは運河に置き換わる（`addons/ami/docs/sidewalk_GE_X.png`）
- 配置の確認は `SHEET_LAYOUT=1` のシートの歩道だけを通常の pak に入れ替えて行った（`addons/ami/docs/sidewalk_layout_*.png`）。`SHEET_LAYOUT=1 python build.py` は `work/layout` に `ami_wall_road_center.png` が無くて止まる（今回の変更の前から）
- `python -X utf8 build.py`: `ami.pak` に dat 74、`ami_extra.pak` に dat 19、警告なし

## 未確認・ユーザーの判断待ち

- waytype を `water`（iss と同じ）のままにするか。道路が歩道の列を横切ると運河の踏切が立ち、運河を横切らせると歩道が置き換わる
- 見た目（敷石の色・縁石の高さ・雪で敷石も縁石も白くする作り）と値（仮）
