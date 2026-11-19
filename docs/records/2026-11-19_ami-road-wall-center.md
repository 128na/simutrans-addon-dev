# 作業ログ: AMI の道路の構造物（#22）の確定と ami_wall_road_center、開いた十字の描き直し

（2026-11-19）

## 目的 / 発端

- ユーザーの決定（2026-11-19）: 次の 4 つを確定とする。地上の道路の基盤の版、`ami_wall_road_twin` の名前、橋の桁の見せ方（床の縁の下の青い帯）、`ami_pier_road` の waytype を `tram_track` にしたこと
- ユーザーの依頼: 道路の壁の way-object に `ami_wall_road_center` を足す。線路の `ami_wall_rail_center` と同じく、側壁を持たず、行き止まりの端の壁だけを持つ
- 通常の版の開いた十字と角の円弧（[2026-11-19_ami-road-open-cross.md](2026-11-19_ami-road-open-cross.md)）を、基盤の版・高架の版にも入れる

## したこと

- README・ACCEPTANCE・`blender/` の注記の「仮」「確定待ち」を、確定（2026-11-19、ユーザーの決定）に書き換えた。前の記録は書き換えていない（記録は書いたら変えない）。値（費用・維持費など）は仮のまま
- `catalog.ROAD_WALL_VARIANTS` に `center` を足した。シートは `sheetlib` の `road_sheet` の `walls="center"`（端の壁だけ残す。基盤の版の `center` と同じ）で描き、dat は線路の壁と同じ `wall_dat_text`（値・並びは線路の `center` と同じ）。`src/ami_wall_road_center.dat`・`.png` が増えた
- `ingame/road_struct_sample.nut` の区画 W3・WV3（行き止まりの並び）で、`center` の線にも `ami_wall_road_center` を重ねるようにした
- 基盤の版・高架の版の 24 シートを描き直した

## 確かめたこと

- 基盤の版・高架の版の 24 シートで、前のシートと比べて変わったのは通常の版と同じセル（`single`・T字・十字・分岐の絵と、その雪の行）だけで、透過の範囲は変わらない（`tools/blender/sheet_diff.py`）。壁の way-object の `single`・`back`・`front` のシートは描き直しても変わらない
- ゲーム（`OTRPv64_3.exe`、`flat_512.sve`、`road_struct_sample.nut`、温暖側）: 区画 W3（基盤の版）と WV3（高架）で、`center` の線の行き止まりに端の壁が出て、`back`・`front` の端の壁と 1 列につながり、基盤・床の端と合うことを 3 倍で見た（`addons/ami/docs/road_struct_GE_WP3.png`・`road_struct_GE_VP3.png`・`road_wall_center_end_zoom.png`・`road_elev_wall_center_end_zoom.png`）。高架の WV3 の端の壁の下の縁に、小さな明るい点が見える（原因は調べていない）
- 高架の区画 L・区画 V_B と地上の区画 WA_B で、開いた十字と角の円弧を見た（`road_elev_L_cross_zoom.png`・`road_struct_GE_V_B.png`・`road_struct_GE_WA_B.png`・降雪側の `road_struct_snow_GE_V_B.png`）

## 見ていないこと

- `ami_wall_road_center` を道路の行き止まり以外（直線・分岐）に重ねたときの見た目（端の壁以外の絵は空）
- 降雪側の区画 W3・WV3
