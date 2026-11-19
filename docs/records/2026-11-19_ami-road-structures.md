# 作業ログ: AMI の道路の壁・高架・橋脚・橋・トンネル（#22）

（2026-11-19）

## 目的 / 発端

issue #22。AMI の道路 3 種（`ami_road_local`・`ami_road_general`・`ami_road_expressway`）に、共有の壁の way-object（`ami_wall_road_<single|back|front>`）、高架の 4 版、道路用の橋脚（`ami_pier_road`）、橋（欄干なし、壁の way-object を重ねる）、トンネルを足す。値は線路の考え方（高架は地上の 2 倍、橋・トンネルは 4 倍、壁と橋脚は線路と同じ）で仮に置く。決めることが 4 つあった: 地上の基盤の版が要るか、道路の橋の桁（POC の C6）、道路用の橋脚の waytype、近い斜めの壁。

## 分かったこと（事実）

- way-object を、way が 1 本で向きが十字（15）のタイルに置くと、本体は way-object の近い斜めの絵が無ければ十字の絵で描く（`../simutrans` の `obj/wayobj.cc` の `calc_image`、542〜548 行付近）。way-object の近い斜めの絵（絵の一覧の 4・5 番）は本体が読むが（`descriptor/way_obj_desc.h` 205〜216 行、`descriptor/reader/way_obj_reader.cc` 30 行）、makeobj が書けない（`descriptor/writer/way_obj_writer.cc` 108〜118 行は斜め 4 つだけ）
- AMI の道路の通常の版は近い斜めの絵を持つので、近い斜めの分け合うタイルは way 1 本（向き 15）になる。そこに壁を重ねると、車道の真ん中に壁の十字の切れ端が立った（`addons/ami/docs/road_wall_close_plain_zoom.png`。区画 G、`[check] Gse`・`Gne` の `d15`）
- 通常の版のカーブは斜めの絵で、タイルの半分で切る。複線（外の線と内の線）の直角の曲がりで、2 本のカーブのタイルの間に草の三角が出た（`addons/ami/docs/road_layout_pair_corner_plain.png`）。高架でも同じ形で、穴から地面と橋脚が見えた（`road_layout_elev_pair_corner_before.png`）
- iss の地上の道路は版ごとの way を持ち（`../refs/iss/src/way/road/ground.dat` の 139・184・229・274 行の `iss_wrg_0120_single`・`front`・`center`・`back`）、近い斜めの絵を持たず、カーブは斜めと別のセル。iss の道路の側壁は way-object（`waytype=road`・`own_waytype=road`）
- 橋の道具を引いて架けると、橋の上の way は `tool_build_bridge_t::do_work`（`simtool.cc`、3621 行付近）が `weg_search(waytype, 橋の速さ, timeline, type_flat)` で選ぶ。橋の速さ以下で一番速い平地の way で、同じ速さが複数あるとハッシュの順で決まる。`addon_check` では、生活道路の橋に pak128 の `Road_040`、一般道路の橋に blender-poc の `bpoc_expressway_wall_back` が載った。端のタイルを 1 回押して架ける形（スクリプトの `build_bridge_at`、`bauer/brueckenbauer.cc` 774 行付近）は、端のタイルの way を使う（平地では、端のタイルの向きが 1 方向である必要がある）。橋・トンネルのタイルの way は、後から道路を敷いても置き換わらない（`bauer/wegbauer.cc` の 2787・2895 行付近）
- `tram_track` の橋脚は、pak128 の `Road_050`・AMI の道路と同じタイルに way 2 本で置け、道路の十字の向きも残る。地上の線路が横切るタイルでは、線路（`ami_rail_ballast` の向き 15）に置き換わってつながる（線路用の橋脚と同じ）。iss の橋脚は全部 `tram_track`（`../refs/iss/src/util/pier/ground/pier.dat`）
- iss の都市高速の橋（`iss_br_0120_bridge1`）の床の縁の青い帯は、256px のセルで 4px（`../refs/iss/release/pak128/bridge/road/0120_bridge1.png` の南北のセルを測った）
- 降雪側で、敷いた後に塗る `tool_set_climate` は地面のタイルだけを塗り替える。`flat_512.sve` の降雪側はもともと雪の気候で、高架にも雪の絵が出た（`road_struct_snow_GE_V_B.png`）

## 判断したこと（どれも仮。ユーザーの確定待ち）

- 判断 1・4（地上の基盤の版・近い斜めの壁）: 地上の基盤の版 `<道路>_base_<版>` を作った（案 A）。近い斜めの絵を持たず（NO_CLOSE）、カーブを斜めの形の別のセル（行 2 の列 5〜8）に描いて壁の無い側をタイルの端まで延ばす。近い斜めの分け合うタイルが way 2 本になり、線路と同じ `twin` の壁（`ami_wall_road_twin`、仮の名前）が合う。ほかの案: B 通常の版から近い斜めの絵を外す（#21 の区画 G が変わり、直角の曲がりのすき間は残る）、C 基盤の版を作らず、地上の近い斜めと複線には壁を重ねない
- 高架の 4 版も、カーブを別のセルに描いた（`tools/blender/sheetlib` の `road_sheet` の `curve_cells`）。線路の基盤の版・高架はもとから別のセル（`track_sheet` の `curve_cells`）
- 判断 2（橋の桁）: 基盤と、その下の桁（`ROAD_GIRDER_D` = 0.15）を青くし、壁の外の面まで出す。画面で約 4px の帯になり、iss と同じ太さ（`road_bridge_girder_zoom.png`）
- 判断 3（道路用の橋脚の waytype）: `tram_track`。道路と重ねられ、線路と横切ると線路用の橋脚と同じ動き。形は道の全幅の柱（斜めは 1/√2）
- T字の「2」の絵は変えていない（#21 のユーザーの判断待ち）。高架の隣り合う十字でも地上と同じく路側線が横切る道路をふさぐ（`road_elev_L_zoom.png`）。橋は直線のセルだけなので出ない
- `tools/blender/sheetlib` の `road_sheet` に `curve_cells` を足した。既定は無効で、AMI の一般道路・高速道路のシート、blender-poc の高速道路・高速道路の高架（back）を描き直して、変更前とバイト列が同じことを確かめた（在来線・高速線のシートは `road_sheet` を通らない）
- 見本は `ingame/road_struct_sample.nut` に分けた（`sample.nut`・`road_sample.nut` には足していない）

## 確かめたこと

- `SHEET_LAYOUT=1` のシートで作った pak で `road_struct_sample.nut` を温暖側・降雪側に敷き、配置と継ぎ目を見てから塗った
- 通常の pak で 144 枚撮った（`OTRPv64_3.exe`、`flat_512.sve`、`sample_parallel.sh`）。`[check]` の行は 3 種・温暖側と降雪側で同じ: 区画 G の分け合うタイルは通常の版の `d15` に壁 1 つ、W1・WV1 の角は版どおりの壁、W2・WV2 の分け合うタイルは way 2 本で `twin`、橋の床と端は AMI の道路と `single` の壁（B4 の端は高架の版につながる）、坑口とトンネルの中は道路と壁、P1・P2 は橋脚と道路の 2 本、P3 は線路に置き換わる
- `sheet_audit`: 道路の壁の斜めのセルの角に 2px の点（blender-poc の壁にもある形）。線路の壁の点は前からあるもの
- `python -X utf8 build.py` は警告なし（`ami_road.pak` は 33 dat、`ami_extra.pak` は 17 dat）

## 点検と直しの回数

- 絵の直しは 2 回: 地上の基盤の版の直角の曲がりのすき間と、高架の直角の曲がりの穴を、カーブを別のセルに描いて直した
- 見本の直しは 4 回: 区画 G の壁の経路、橋の架け方（道具を引く形から端を押す形へ）、トンネルの中のタイルを高さで引く、降雪側の塗り方を元に戻した
- レイアウト検証用の見本を回したとき、`sample_check.sh` が ゲームの検証環境の `ami.pak` をレイアウトの pak で上書きした。`dist/ami.pak` に戻した

## 関連

- 決まり: `docs/reference/way-addon.md` の 5・6・10 章
- アドオン: `addons/ami/README.md`（「道路の壁・高架・橋脚・橋・トンネルの作り（#22）」）、`addons/ami/ACCEPTANCE.md`
- 見本: `addons/ami/ingame/road_struct_sample.nut`
- 前の記録: [2026-11-19_ami-road.md](2026-11-19_ami-road.md)
