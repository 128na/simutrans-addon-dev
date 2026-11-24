# 調査/作業ログ: 線路の壁（back）のシートの 2 セルが今の描画と違って見えた件（#268）

## 目的 / 発端

#260（PR #267）で AMI の全 213 シートを描き直してコミット済みの PNG と比べたところ、`ami_wall_rail_back`・`ami_wall_rail_old_back` の 2 セル（行 0・列 4 と、行 1・列 4）だけが約 1000 画素違った（2026-11-25）。#260 より前からの食い違いに見えたので、どちらが正しいか、いつ食い違ったかを確かめる。

## 分かったこと（事実）

- **2 セルはタイルの絵ではなく、ツインの壁（`ami_wall_rail_twin`・`ami_wall_rail_old_twin`）のアイコンとカーソルのセル。** `src/ami_wall_rail_twin.dat` の 14〜15 行目が `icon=> ami_wall_rail_back.0.4`・`cursor=ami_wall_rail_back.1.4,-64,-32`（旧は `ami_wall_rail_old_back`）。この 2 つ以外に、back のシートの 0.4・1.4 を指す物は無い（`src/*.dat` と `blender/*.py` を検索）。ゲームのタイルの見た目には関係しない（本体が読むのはアイコン・カーソルのセルで、タイルの絵ではない）。
- ツインの壁には自分のシートが無い。アイコン・カーソルは back のシートに書き、絵は front の版の斜めのセルから作る（`blender/icons.py` の冒頭。`src/ami_wall_rail_back.icon_sources.txt` に front の行 2・6、列 3 の sha256 を控えてある）。
- 再現（`origin/main` の bee768a、Blender 4.5.16。2026-11-25）:
  1. `render_parallel.py` で `ami_rail_ballast_base_back`・`ami_rail_ballast_old_base_back`（壁のシートは基盤の対象が書く）を描く（150 秒）。
  2. コミット済みと `tools/blender/sheet_diff.py`（`ALL=1`）で比べると、`ami_wall_rail_back.png` は 4 セルが違った: 0,0（アイコン。色 691 画素）、0,1（カーソル。透過 224 画素）、0,4（透過 1024 画素）、1,4（透過 941 画素）。old も同じ（0,4 は 1024 画素、1,4 は 940 画素）。ほかのセル（タイルの絵）は透過・色とも 0 画素。0,4 は 32×32 = 1024 画素で、アイコン 1 つ分。
  3. 絵を見ると、コミット済みの 0,4 には「双」のアイコンが、1,4 にはカーソルがあり、描き直しただけのシートではその 2 セルが空だった。
  4. `icons.py`（全部。`blender -b --factory-startup --python blender/icons.py`）を流すと、4 セルとも元に戻り、`ami_wall_rail_back.png`・`ami_wall_rail_old_back.png` はバイトまでコミット済みと一致した（`git status` に PNG が出ない）。`check_icons.py` も通った。`*.icon_sources.txt` に出た差は改行だけだった（`--ignore-space-at-eol` で差が 0）。
- 原因: `render.py` は描いた後で `icons.py --own` を流す。`--own` は、描いた対象の外のシートにあるアイコン・カーソルと、ほかのシートの絵から作る物を書かない（`icons.py` の `main`）。ツインの壁は両方に当たる（書き先は back、絵は front）。壁のシートのアイコンも、対象名（`ami_rail_ballast_base_back`）と書き先のシート名（`ami_wall_rail_back`）が違うので、`--own` では書かれない。描き直すと、ツインの 0.4・1.4 は空になる（壁のシート自身の 0,0・0,1 は `sheetlib` が置く仮の絵「W」と直線の壁のまま）。どれも全部を流すまで戻らない。#229（記録 `2026-11-24_ami-sheet-drift-audit.md`）が見つけた壁 8 枚の違いと同じ仕組み。
- **いつ食い違ったか**: 今のコミット済みのシートは、描画からアイコンの後処理までの全工程の出力と一致する（タイルのセルは 0 画素差、アイコン・カーソルのセルは後処理を流すと一致）。なので、コミット済みが古いのでも、描画が変わったのでもない。過去の各時点の PNG は比べていない。ツインの壁の dat は、新が #35（d2dd4f3、2026-11-18）、旧が #176（b4b5045、2026-11-22）で入った。新の back のシートの最後のコミットは #95（7fa6dcf、2026-11-21。アイコンとカーソルが今の漢字の札になった）、旧の back は #176 の 1 回だけ。
- 道路の壁も同じ作りで、`ami_wall_road_twin.dat` が `ami_wall_road_back.0.4`・`.1.4` を、`ami_wall_road_twin_divider.dat` が `ami_wall_road_front_divider` の同じセルを指す（`icon_sources.txt` もある）。`--own` で書かれない構造は同じ。実際に違って見えるかは確かめていない。

## 推測・未確認事項

- #260 の比べ方は再現していない。#260 では 0,4・1,4 だけが違ったと書かれているが、`icons.py` の条件（書き先のシート名を渡せばツインも書かれる）とは合わず、原因は未確認。この件では、後処理を全部流して一致することを確かめた。
- 線路の壁の front・single・center のシートには、ツインのセルは無い（ツインの壁は back のシートだけに書く）。

## 結果どうしたか

- シートは描き直さず、コミットしない（コミット済みが正しい）。受け入れ条件の「0 画素差」は、アイコンの後処理まで流した状態で満たしている。
- リファレンス `docs/reference/way-addon.md` の 8.2 に、道具の癖として書いた。
