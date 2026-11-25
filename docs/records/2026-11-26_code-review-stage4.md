# 調査ログ: 第 4 弾の終わりのコードの見直し（リファクタの要否、#255）

（2026-11-26。読んだのは main の `e37279e`。行番号はこのコミットのもの）

## 目的 / 発端

段の終わりに、コード面でリファクタをするべきかを確かめる（2026-11-22 のユーザーの決定。進捗管理の手順の「コードの見直し」）。第 4 弾（道路のカーブと分岐、[#255](https://github.com/128na/simutrans-addon-dev/issues/255)）の終わりに、次の段の前に片付ける直しの案をユーザーに出すための材料。

見た観点は、前回（[第 3 弾の見直し](2026-11-24_code-review-stage3.md)）と同じく、重なり（同じことを 2 か所でしている）・肥大（1 ファイル・1 関数が大きすぎる）・ぶつかりやすさ（新しい物を足すたびに同じ所を触る）・読みにくさ。あわせて、前回の直す案 1〜6 が今どうなっているかを確かめた（4〜6 は「第 4 弾で該当の所を触るときに片付ける」ことになっていた。#255 の本文）。

## やったこと

- 対象の PR: 第 4 弾で `addons/ami/`・`tools/` に手が入った 19 件。#258・#262・#265・#267・#270・#271・#272・#273・#274・#280・#281・#283・#284・#286・#289・#290・#293・#294・#295。
  - 進捗管理の依頼の一覧の #257・#259 は issue の番号で、PR はそれぞれ #258（幹線道路）と #262（一般道路・生活道路のカーブ）。
  - 依頼の一覧に無かった #270（pak の大きさの設定。#271〜#274 の前段）と #281（道路の停留所）は、どちらも第 4 弾の期間に `ami_dat.py`・`catalog.py`・`render.py` などを触っているので足した。
  - 文書だけの #269・#276 は数えていない。前回の見直しの対応（#248〜#252）と、第 3 弾の後始末の #254 も入れていない（第 4 弾の物を足す PR が #258 から始まるので、そこからにした。#254 を入れると `icons.py` は 6 件、`way-addon.md` は 11 件になる）。
- 触ったファイルは `gh pr view <番号> --json files` で数えた。画像・dat・`*.txt`・`rounds/`・記録は除いた。
- 19 件のうち、PR のブランチに main の取り込みのコミットが残っていたのは 3 件（#262・#267・#286）。`git show --cc` で中身を見たうえで、`git merge-tree --write-tree --name-only <親 1> <親 2>` で実際にぶつかったファイルを確かめた。
- 表の中身は、Blender を使わずに import して比べた（`catalog.SCALED_SHEETS` と `src/*.dat`、`addon_config.SHEETS` と `ami_dat.BUILT`）。関数の長さは `ast` で数えた。
- ゲームと描画は動かしていない。`check.sh` も流していない（コードは変えていない）。

## 分かったこと（事実）

### 1. 前回の直す案の今

| 前回の案 | 今 |
|---|---|
| 1 dat が空のセルを指していないかを check.sh で見る | 済み（#250、#252 で速くした）。`check_cells.py` |
| 2 ingame の起動・停止の共通化、既定の地図を v64 に | 済み（#249）。`ingame/*.sh` 29 本（`game_lib.sh` 自身を含む）のうち 20 本が `game_lib.sh` を読む。読まない 8 本は、`game.sh` を通して起動する物（`old_base.sh`・`old_seam.sh`）、起動済みのゲームに `mcp_client.sh` でつなぐ物（`ex_capture.sh`・`sample_capture.sh`・`curve_base_study.sh`）、ゲームを起動しない物（`mcp_client.sh`・`sample_spots.sh`・`strip_usage_log.sh`）。`flat_512` を既定に持つスクリプトは無くなった |
| 3 way の絵の並びの性質を catalog.py の 1 か所から引く | 済み（#248）。`catalog.py` の `NO_CLOSE_WAYS`・`ELEVATED_WAYS`・`FRONT_WAYS`（`:313-315`）。第 4 弾の幹線道路（#258）は `addon_config.py` を触らずに `addon_config.SHEETS` に 9 つとも入った（`ami_dat.BUILT` との差は 0。import して確かめた）。効いている |
| 4 render.py の diag_curves・close・front_row を catalog.py から、行のずらしを Blender を使わない 1 か所に | **未着手**。道路のカーブの形だけは `catalog.ROAD_CURVE_SHAPES`（`:148`）を `render.py:550`・`:586`・`:599` が引く形で入った（#262）。線路・モノレールの `"diag_curves": True`（`render.py:259`・`:285`）、`"close": False`（`:285`）、`front_row=4`（`:306`・`:313`）は数字のまま。行のずらしの対は増えた（下の 2） |
| 5 ami_dat.py の dat の頭の行を `_head` に、路面表示の字を catalog.py の隣に | **未着手**。`ami_dat.py` は第 4 弾の 19 件のうち 10 件が触ったが、頭の行を自分で並べる関数は 15 本に増えた（#281 の `road_stop_dat_text`、`:827`）。`_head`（`:258`）を使うのは橋とトンネルの 2 本のまま。`icons.py:87-97` の `MARK_LABELS`・`MARK_PICTURE` もそのまま |
| 6 README の「作り」の節を物ごとの文書に分ける | **未着手**。`addons/ami/README.md` は 1121 行から 1240 行に増えた |

- 4〜6 は「該当の所を触るときに片付ける」としていたが、`ami_dat.py`（10 件）・`render.py`（11 件）・README（13 件）を触った PR があっても、上のとおり片付いていない。触るときに片付ける形では進まなかった（各 PR の差分は読んでいない。PR のタイトルと、今のコードが前回と同じ形であることから見た）。

### 2. 描く側と dat を書く側で、同じ値を注記でそろえている対

前回の表に、車庫・操車場・踏切の分を足して、今の対を並べた。数値はどれも合っている（描く側の定義を grep で見て確かめた）。網羅ではない（下の表の後に、レビューで見つかった物を足した）。

| 値 | 描く側 | dat を書く側 | 第 4 弾で |
|---|---|---|---|
| 手前の絵の行（way） | `render.py:306`・`:313` の `front_row=4` | `ami_dat.py:104` の `FRONT_ROW = 4` | — |
| 壁の手前の絵の行 | `sheetlib.py:755` の `WALL_FRONT_ROW = 4` | `ami_dat.py:190` の `WALL_FRONT_ROW = 4` | — |
| 門型の橋脚の手前の絵の行 | `sheetlib.py:1492` の `PIER_GATE_FRONT_ROW = 4` | `ami_dat.py:177` の `PIER_FRONT_ROW` | — |
| 盛土の雪の行 | `sheetlib.py:1336` の `_EMB_SNOW_ROW = 4` | `ami_dat.py:476` の `EMBANKMENT_SNOW_ROWS = 4` | — |
| 運河の雪の行 | `canal.py:31` の `CANAL_SNOW_ROWS = 4` | `ami_dat.py:39` の `SNOW_ROWS = 4` | — |
| 踏切の雪の行 | `crossing.py:89` の `CROSSING_SNOW_ROW = 2` | `ami_dat.py:664` | — |
| 車庫の雪の行・offset | `depot.py:31` の `DEPOT_SNOW_ROW = 2`、`depot.py:30` の `BUILDING_OFFSET` | `ami_dat.py:737`・`:740` | — |
| 操車場の雪の行 | `yard.py:30` の `YARD_SNOW_ROW = 1` | `ami_dat.py:780` | — |
| 道路の停留所の雪の行 | `road_stop.py:29` の `ROAD_STOP_SNOW_ROW = 2` | `ami_dat.py:821` | **#281 で増えた** |
| 路面表示の雪の種類・空のセル | `marking.py:48`・`:125` | `ami_dat.py:539`・`:537` | — |

- 表に無い対が、ほかにもある: 歩道の柵の手前の絵の行（`sidewalk.py:59` の `FENCE_FRONT_ROW = 4`。dat は `ami_dat.py:652` で壁の `WALL_FRONT_ROW` を借りる）、橋の雪の行（`ami_dat.py:241` の `BRIDGE_SNOW_ROWS = 4`）、手前の絵を持つ way の雪の行（`ami_dat.py:105` の `FRONT_SNOW_ROWS = 8`）、踏切の下の道路の雪の行（`crossing.py:208` の既定 `road_snow_rows=4`）。少なくとも 14 対ある。

- 前回の案 4 は「`sheetlib` は import すると Blender を読むので、`ami_dat.py` からは直接引けない」を前提にしていた。今は `ami_dat.py:32` が `tools/blender/sheet_settings.py`（Blender を使わない。#270 で pak の大きさを足した）を import している。Blender を使わない置き場への道は、既にある。
- 対が食い違ったときに拾う検査は、指す先が空のセルになる形だけ（`check_cells.py`）。行のずらしの食い違いは、指す先に別の絵があると拾えない（前回と同じ）。

### 3. ぶつかり: main の取り込みのコミットから

| PR | ぶつかったファイル（`git merge-tree`） | 相手 | 中身 |
|---|---|---|---|
| #262（一般道路・生活道路のカーブ） | `addons/ami/README.md`、`addons/ami/blender/catalog.py` | #258（幹線道路） | `catalog.py` は `ROADS` の行と `DIAG_CURVE_WAYS` の注記。README は道路の節の同じ段落。`render.py`・`sample_spots.sh`・`sheetlib.py` は両方が触ったが、自動で合わさった |
| #267（道路の基盤・高架を single に） | なし | — | 取り込みだけ |
| #286（カーソルの offset） | `docs/reference/way-addon.md` | #284 など | 8.2 の同じ箇条書きの並びで、#286 は既にある `dat:` の行に cursor の文を足し、相手はその隣に `描画: 踏切…` の行を足した |

- 前回（40 件中 1 件）より多い（19 件中 2 件）。どちらも一覧の表と文書の層で、土台（`sheetlib.py`）は自動で合わさった。
- #271〜#274（256 対応の A〜D）は順に動かしたので、取り込みが無い。squash で入るので、rebase・force-push したブランチは跡が残らない（前回と同じ限界）。
- README の道路のカーブの節（`README.md:179`）に、同じ理由の文（「道路の壁を 3 種で共通の way-object にするため…」）が 2 回ある。後ろの「それでも 3 種をそろえたのは、…」は #259 の前の古い文で、前の「以前（#259 の前）は 3 種をそろえていた。…#260 で直した」と食い違う。古い文は main の側（`e04e32e`）に元からあり、前の文は #259 のブランチ（`7bb9944`）で足した。取り込みで生じた物ではなく、書き足したときに古い文を消し忘れた物（`git show` で両方の README を見て確かめた）。

### 4. 触った回数（19 件。2 件以上の物の抜粋）

| ファイル | 件数 | 層 |
|---|---|---|
| `addons/ami/README.md` | 13 | 文書 |
| `addons/ami/blender/render.py` | 11 | 一覧の表 |
| `docs/reference/way-addon.md` | 10 | 文書 |
| `addons/ami/blender/catalog.py`・`ami_dat.py` | 各 10 | 一覧の表 |
| `tools/blender/sheetlib/sheetlib.py` | 5 | 土台 |
| `addons/ami/release/text/ja_ami.tab`・`check.sh`・`blender/icons.py` | 各 5 | 一覧の表・検査 |
| `addons/ami/build.py` | 4 | 一覧の表 |
| `tools/blender/sheetlib/roadsign.py`・`tools/README.md`・`addons/ami/lineup.py`・`ingame/sample_spots.sh` | 各 3 | — |
| `tools/blender/sheetlib/core.py`・`road_parts.py`・`assemble.py`・`__init__.py` | 各 2 | 土台・描くコード |

- 物を 1 つ足す・消すときに触るファイル: 幹線道路（#258）は 18 ファイル（`ingame/` の見本 8 本を含む。セルの控えの `*.txt` 6 本を含めると 24）、道路の停留所（#281）は 12、閉塞信号の追加（#283）は 12、その削除（#293）は 14（ADR を含む）。足した物を消すのにも、同じ表を全部たどった（#293 の後、`signal` の残りが無いことを grep で確かめた）。
- 土台の `sheetlib.py` は、前回は 40 件中 2 件だったが、今回は 19 件中 5 件（#258・#262・#270・#272・#280）。道路の関数 `_road_sheet`（`sheetlib.py:188-744`）は約 495 行から 557 行に増えた（カーブの形 `curve`・`curve_cells`、pak の大きさ）。線路の `_track_sheet`（`:879-1232`）は 354 行で変わらない。

### 5. pak の大きさ（256）で増えた物

- `catalog.py:321-368` の `SCALED_*`（256 で描き・組める物の表）は、#266〜#274 で段階的に広げたときの「入れた物だけ通す」表。今は `src/*.dat` のうち外れているのは `ex_donors`（分岐の追加画像の提供用で、物ではない）だけで、全部の物が入っている（import して比べた）。新しい物を足すと、この表にも足す（足し忘れは `check_scaled.py` が CI で止める。黙っては誤らない）。
- 模様の細かさ（`core.noisy_material` の `scale`）は部品の座標で決まるので、256 では粒が 2 倍の大きさになる（#288 の本文）。#288 は道路の路面（`road_parts.py:263`、#289）と歩道の舗装（`render.py:724`、#290）を、呼ぶ所で `* SCALE` を掛けて直した。`SCALE` を掛けていない呼び出しが、ほかに残っている: `canal.py:38-40`・`:233`・`:280`・`:283`（水・壁・笠石・暗渠）、`road_parts.py:66`・`:70`・`:75`・`:101`、`track_parts.py:142`（線路のバラスト）、`render.py:519`・`:526`（道路の雪）・`:674`・`:685`・`:747`、ラウンドの `round_road.py`・`round_road4.py`・`round_wave3.py`。
  - #288 の追加のコメント（pak256 の進捗管理）は、走行跡・雪・路面表示は「路面の直しで足りる」としている。#288 の本文は、線路のバラストは元から粒が細かく目立たないとしている。運河などのほかの物が 256 で粗いという報告は、#288 では見ていない（issue の全体は探していない）。どれが 256 で目立つかは見ていない（256 の見た目は pak256 が確かめる取り決め）。
- 256 の検査（#271）は `check_icons.py` を道具の置き場として使っている。`check_cells.py:24`・`check_crossing.py:16`・`check_depot.py:19`・`check_embankment.py:34` が `check_icons` から `CELL`・`SCALE`・`SRC`・`read_rows`・`read_dats` などを import する。
  - 同じ名前で違う物: `offset_of` が `check_icons.py:312`（無ければ `None`。#295 で足した）と `check_depot.py:34`（無ければ `(0, 0)`）にある。
  - 同じ中身の写し: セルの sha256 が `check_icons.py:230` の `source_digest`、`check_crossing.py:34` の `cell_digest`、`blender/icons.py` の `cell_digest`（控えを書く側）の 3 か所にある。並びを変えると 3 か所とも直すことになる（ずれれば検査が落ちるので、黙っては誤らない）。

### 6. そのほか

- 80 行を超える関数: `sheetlib.py` の `_road_sheet`（557 行）・`_track_sheet`（354）・`_tunnel_sheet`（118）・`shoot`（81）、`cells.py` の `render_layers`（107）、`core.py` の `tiled_concrete_material`（105）、`round_tram.py` の `apply`（224）、`check_icons.py` の `main`（108）、`tools/blender/` の測る道具の `main`（`seam_judge.py` 180・`ingame_diff.py` 129・`slope_measure.py` 87）。
- 道路と線路のシートの末尾の写し（壁の way-object のカーソル。前回の 4）は変わっていない。線路の側（`sheetlib.py:1229`）にだけ、側壁の無い版のカーソルに端の壁の絵を使う 1 行がある。道路の側は `:739-741`。
- `round.py` は 2 件（#284・#294）。#294 は知らない引数をエラーにする直しで、設定の写しは増えていない。
- `ingame/` の見本の NUT は、道路の種類を手で並べている。`ami_road_expressway` を含む `.nut` 11 本のうち、`ami_road_trunk` も含むのは 5 本（`crossing_sample`・`divider_sample`・`road_junction_sample`・`road_sample`・`road_struct_sample`）。残りの 6 本（`calib_road.nut`・`canal_crossing.nut`・`expwy_marking_sample.nut`・`sidewalk_sample.nut`・`thumbnail.nut`・`tram_sample.nut`）は、高速道路だけを見る見本か、種類を選んで並べた見本で、足していないのは意図に見える（確かめていない）。

## 推測・未確認事項

- 2 の対は今は合っている。次の種類（建物の形の物）を足すときに、また 1 対増える見込み（#281 で増えた形）。
- 5 の模様の細かさは、#288 で 2 件続いた形なので、pak256 で見ていくとほかの物でも同じ報告が来る見込みと見ている（今は報告が無い）。`noisy_material` の中で `SCALE` を掛ければ、呼ぶ所ごとに直さずに済むと見ている。その場合、5 の残りの呼び出しが全部（線路のバラスト・ラウンドの設定も）256 で変わる。128 では `SCALE` が 1 なので、128 の絵は変わらないはず（#289・#290 と同じく、描き直してバイトで同じことで確かめられる）。既に呼ぶ所で掛けている 2 か所（`road_parts.py:263`・`render.py:724`）は外す。`tiled_concrete_material` の `grain`・`stain_scale` など、ほかの材質の細かさが同じ形かは読んでいない。blender-poc も `noisy_material` を使うが、blender-poc は 128 だけなので変わらない見込み。
- `SCALED_*` を「256 で組まない物」の表に裏返すと、新しい物は既定で 256 にも入る。256 で絵を確かめていない物が入ることになる。今の取り決め（AMI は 128 用で、256 の見た目は pak256 が確かめる）と合うかは、進捗管理とユーザーに確かめる。
- ぶつかりの数は、取り込みのコミットが残った PR だけから数えた。実際はこれより多いかもしれない。
- 次の所は読んでいない、または名前と冒頭だけを見た: `core.py`・`cells.py`・`assemble.py` の中身、`road_ex.py`・`road_stop.py` の中身（新しい物。描く側の対だけを見た）、`build.py` の 256 の分け方、`release.py`、`tools/ci/`、`tools/dat_lint_extra/`、`.nut` の中身、blender-poc。
- README の分け方（下の案 7）の置き場所は、前回と同じく決まっていない。

## 結果どうしたか

コードは変えていない。直す案を、おすすめの順に並べた。起票はしていない（直すかどうかはユーザーが決める。issue のタイトルは案）。開いている issue（#255・#50・#30）に当たる物は無かった（2026-11-26 に `gh issue list --state open` で見た。起票の前にもう一度見る）。

### 直す案（おすすめの順）

| 順 | 何を | issue（タイトル案） | 重さ | 直さないとどう困るか | 確かめ方・注意 |
|---|---|---|---|---|---|
| 1 | 模様の細かさを pak の大きさに合わせる所を 1 か所にする | 「sheetlib: noisy_material の模様の細かさを pak の大きさで掛ける所を 1 か所にする」。`core.noisy_material` の中で `scale * SCALE` にし、呼ぶ所で掛けている 2 か所を外す。5 の残りの呼び出し（線路のバラスト・道路の雪・運河・ラウンドの設定を含む）が、まとめて 256 で細かくなる | 小 | 今わかっている害は、#288 で路面と歩道が粗く見えたことだけ（PR が 2 本に分かれ、issue を開き直した）。ほかの物は報告が無い。直さないと、ほかの物で同じことが見つかるたびに 1 件ずつ報告と PR が要る見込み（推測） | 低い。128 の全シートを描き直し、コミット済みの PNG とバイトで同じことを確かめる（描画は要る）。256 は全部の模様が変わるので、pak256 に見てもらう（バラストのように元から細かい物が細かくなりすぎないか）。`tiled_concrete_material` などほかの材質も同じ形かを、着手のときに読む。pak256 から次の報告が来るまで待ってもよい |
| 2 | README の重複した文を消す | 「ami: README の道路のカーブの節に残った #259 の前の古い文を消す」。`README.md:179` の「それでも 3 種をそろえたのは、…」の文。末尾の「断面も blender-poc の高速道路（斜めの絵）と同じ」を残すかも決める | 小 | 同じ段落に、今の作り（#260 で直した）と食い違う古い文があり、読む人が迷う。文書を触る作業が多いので早めに消すのがよい。案 7 に含めてもよい | docs-lint |
| 3 | dat の頭の行をまとめる（前回の案 5） | 「ami: ami_dat.py の dat の頭の行を _head にまとめ、icons.py の路面表示の字を catalog.py の MARKINGS の隣に置く」。中身は前回と同じ | 小 | 新しい物を足すたびに頭の行を写す（15 本目が #281）。値の並びを変えたいときに 15 か所を直す。`ami_dat.py` は第 4 弾の 19 件のうち 10 件が触る | 低い。dat は `check.sh` の比べで変わらないことを確かめる（Blender 無し）。アイコンは `check_icons.py` |
| 4 | 256 で組める物の表を裏返す | 「ami: catalog.SCALED_SHEETS を、256 で組まない物の表に裏返す」。`SCALED_*` の列挙を消し、外す物（`ex_donors` など）だけを持つ。`check_scaled.py` の見る所も合わせる | 小 | 新しい物を足すたびに触る表が 1 つ多い。足し忘れは CI で止まるので、誤りにはならない。手間だけ | 低い。256 の dat の組み（`SHEET_PAK_SIZE=256 python ami_dat.py`）の出力が変わらないことを比べる。裏返すと、新しい物が既定で 256 に入る。それでよいかを先に決める（推測・未確認事項） |
| 5 | 描く側と dat を書く側の行のずらしを 1 か所にする（前回の案 4） | 「ami: シートの行のずらし・雪の行・offset を Blender を使わない 1 か所に置き、sheetlib と ami_dat.py の両方から引く」。2 の対（少なくとも 14 対。着手のときに洗い出す）と、`render.py` の線路・モノレールの `diag_curves`・`close`・`front_row` を catalog.py の性質から決める。置き場は `sheet_settings.py` の隣（`ami_dat.py` は既にそこを import する）。アドオンごとの値は `tools/` に置かない決まり（`sheet_settings.py` の冒頭）なので、種類ごとの描き方の値（全アドオン共通）と AMI の物の性質（catalog.py）を分けて置く | 中 | 物の種類を足すたびに 1 対増える（#281 で 1 対増えた）。片方だけ直すと、dat が別の行の絵を指す。指す先に別の絵があると検査で拾えない | 中くらい。土台（`sheetlib`）と `render.py` を触るので、ほかの描く作業と並べない。値は変えないので、変更前と後で全シートを描き、バイトで同じことを確かめる |
| 6 | 検査の共通の関数を 1 か所にする | 「ami: 検査の共通の関数（dat の読み・セルの読み・offset・セルの digest）を check_lib.py にまとめる」。`check_icons.py` から、4 本が import している物と、`offset_of`・digest の写しを移す | 小 | 今は誤りにはならない。`offset_of` が 2 つあり、返す物が違う（`None` と `(0, 0)`）ので、別の検査で取り違えやすい。digest の並びを変えると 3 か所を直す | 低い。`check.sh` が通ることで確かめる。`check_cells.py` の自己テスト（`self_test`）も流す。急がない。検査を触る次の作業で一緒にしてもよい |
| 7 | README を分ける（前回の案 6） | 「ami: README の『作り』の節を物ごとの文書に分ける」。中身は前回と同じ。あわせて `docs/reference/way-addon.md` の 8 章の「描画」「dat」の箇条書きを主題ごとに分けるかも決める | 大 | README は 19 件のうち 13 件、`way-addon.md` は 10 件が触り、どちらも取り込みでぶつかった（#262・#286）。並べて動かす作業が増えるほど、合わせ直しが増える。1240 行で、読む所を探しにくい | 中くらい。置き場所をユーザーと決めてから（文書の決まり `docs/README.md`・`addons/README.md`）。ほかの文書からのリンクが切れないかを docs-lint で確かめる。README を触る作業がほぼ毎回あるので、ほかの作業が止まっている段の切れ目にする |

- 1・3・4・6 は、描画もゲームも要らないか、要っても「128 の絵が変わらない」の比べで確かめられる。5 は描画が要る。7 は文書の置き場所の判断が要る。
- 5 と 7 は、ほかの作業と並べにくい（5 は土台、7 は README を触る作業がほぼ毎回ある）。前回「触るときに片付ける」とした 4〜6 は、第 4 弾で進まなかった（1 の事実）。段の切れ目で、issue にして片付けるのがよい。

### やらなくてよいもの

前回の「やらなくてよいもの」を、今回の数で見直した。

| 何を | やらない理由 |
|---|---|
| `sheetlib.py` の `_road_sheet`・`_track_sheet` を分ける | `sheetlib.py` を触ったのは 19 件中 5 件に増え（前回は 40 件中 2 件）、`_road_sheet` は 557 行になった。ただし、取り込みで実際にぶつかったことは無い（#262 では自動で合わさった）。分けると全部の絵に響き、変更前のコードで描いた絵との比べが全種類で要る。道路のカーブ・分岐の作業（第 4 弾）が終わったので、次の段で道路を触らないなら、今は分けない。次の段も道路の形を足すなら、その前に案 5 と一緒に見直す |
| `catalog.py`・`ami_dat.py` をファイルで分ける | ぶつかったのは `catalog.py` の 1 件（#262）で、同じ `ROADS` の行と注記を両方が直したことによる。ファイルを分けても同じ行なら同じようにぶつかる |
| `build.py`・`lineup.py` の名前の頭による振り分け | 漏れは `lineup.py --check` が CI で拾う（前回と同じ） |
| 種類ごとの描くコード（`marking.py`・`road_ex.py`・`road_stop.py` など）を小さくする | その種類の作業しか触らず、ぶつかっていない |
| `catalog.py` の `Track` と `Road` を 1 つの型にする | 前回と同じ。2 つだけで、増える見込みも少ない |
| 測る道具の PNG の読み方・大きな `main` | 1 本ずつ単独で動かす道具で、CI にも入っていない。直近の PR で触っていない |
| `ingame/` の見本の NUT が道路の種類を手で並べている | 見本ごとに見たい種類を選んで並べていて、全部の種類を並べるとは限らない。種類を足すのは数年に 1 回の見込み |
| `round*.py` | 前回と同じ。`render.py` の上に差分を重ねていて、写していない |
