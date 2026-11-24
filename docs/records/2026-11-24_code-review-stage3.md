# 調査ログ: 第 3 弾の終わりのコードの見直し（リファクタの要否、#172）

（2026-11-24。読んだのは main の `d4bb626`。行番号はこのコミットのもの）

## 目的 / 発端

段の終わりに、コード面でリファクタをするべきかを確かめる（2026-11-22 のユーザーの決定）。第 3 弾（景観、[#172](https://github.com/128na/simutrans-addon-dev/issues/172)）の終わりに、次の第 4 弾の前に片付ける直しの案をユーザーに出すための材料。

見た観点は、重なり（同じことを 2 か所でしている）・肥大（1 ファイル・1 関数が大きすぎる）・ぶつかりやすさ（新しい物を足すたびに同じ所を触る）・読みにくさ。特に、#217・#227 で見つかった「設定が 2 か所に分かれていて片方を直し忘れた」の類いを探した（#227 では、斜めのカーブを使うシートの集まりが `ami_dat.py` の `DIAG_CURVES` と `addon_config.py` の `DIAG_CURVE_SHEETS` に別々に書かれ、懸垂式モノレールを片方にだけ足していた。PR #232 で `catalog.py` の `DIAG_CURVE_WAYS` に一本化した）。

## やったこと

- 対象: `tools/blender/sheetlib/`・`tools/blender/*.py`・`tools/ci/`・`addons/ami/blender/`・`addons/ami/ingame/`・`addons/ami/*.py`・`addons/ami/check.sh`。層は進捗管理の手順の「割り当て」の表（描くコード・土台・一覧の表・文書）に、ゲームのスクリプト（`ingame/`）を足した。
- 直近にマージした 40 件の PR（#165〜#232）の変更したファイルを数えた（`gh pr view <番号> --json files`。画像・`rounds/`・記録・`src/` の dat は除く）。
- 40 件のうち、PR のブランチに main を取り込んだマージのコミットがある 4 件（#185・#194・#202・#214）は、`git show --cc` で手で合わせ直した所があるかを見た。
- `addons/ami/blender/` の表（`ami_dat.BUILT`・`addon_config.SHEETS`）は、Blender を使わずに import して差を出した。`check_icons.py` を流した（通った）。ゲーム・描画は動かしていない。

## 分かったこと（事実）

### 1. 一覧の表: 同じ性質を別々の所に書いている

「way ごとに、どんな絵の並びを持つか」という同じ性質を、描く側（`render.py` の設定と `sheetlib`）と dat を書く側（`ami_dat.py`）と判定の道具の側（`addon_config.py`）が別々に持っている。合っているかを見る検査は無く、注記（「〜と同じにする」）でそろえている。

| 性質 | 描く側 | dat を書く側 | 判定の道具の側 |
|---|---|---|---|
| カーブに斜めの絵を使う | `render.py:259`・`:285` の `"diag_curves": True`（高架・懸垂式・電化はこれを引き継ぐ）。道路は旗が無く、カーブのセルも描く（`sheetlib.py:312-315`。dat は使わない）。運河は `canal.py:62`・`:89-98` に固定 | `catalog.py:252-258` の `DIAG_CURVE_WAYS`（#227 で一本化）。壁・電化・橋脚の way-object は `ami_dat.py:408`・`:450`・`:483` で無条件に斜めのセル | `addon_config.py:28`（`DIAG_CURVE_WAYS` を引く） |
| 近い斜めの絵を持たない | `render.py:285` の `"close": False`（`sheetlib.py:937-941`） | `ami_dat.py` の `NO_CLOSE`（`:101` から、物ごとに `add`） | — |
| 手前の絵の行のずらし | `render.py:306`・`:313` の `front_row=4`、`sheetlib.py:683` の `WALL_FRONT_ROW = 4`、`sheetlib.py:1420` の `PIER_GATE_FRONT_ROW = 4` | `ami_dat.py:96` の `FRONT_ROW = 4`、`:209` の `WALL_FRONT_ROW = 4`、`:196` の `PIER_FRONT_ROW` | — |
| 雪の絵の行のずらし | `sheetlib.py:1264` の `_EMB_SNOW_ROW = 4`、`canal.py:31` の `CANAL_SNOW_ROWS = 4` | `ami_dat.py:493` の `EMBANKMENT_SNOW_ROWS = 4`、`:32` の `SNOW_ROWS = 4` | — |
| 路面表示の、雪の絵を別に持つ種類・絵のあるセル・空のセル | `marking.py:48` の `MARKING_SNOW_KINDS`、`:550` の `marking_jobs`、`:122` の `MARKING_EMPTY_CELL` | `ami_dat.py:556`・`:537-553`・`:554` に同じ物を写している | — |
| 作った way の名前 → シート | `render.py` の `SHEETS` | `ami_dat.py` の `BUILT`（`:99` から） | `addon_config.py:8-25` の `SHEETS` |

- 今の値はどれも合っている（数値の対は同じ値、路面表示の雪の種類は同じ 6 つ）。
- `addon_config.SHEETS` には、`ami_dat.BUILT` にある懸垂式モノレールの 6 つ（`ami_monorail_suspended_<版>` と高架の 3 版）が無い。#227 で `DIAG_CURVE_SHEETS` から漏れていたのと同じ #116 の追加で、`SHEETS` にも足していない（#227 では直していない別の漏れ）。`seam_judge.py:167`・`slope_measure.py:54` は `SHEETS[name]` で引くので、懸垂式で継ぎ目を測ると `KeyError` で止まる（黙って誤ることは無い）。`addon_config.SHEETS` が橋脚・路面表示・歩道・盛土を持つのは、`BUILT` とは別の表（`PIERS`・`MARKINGS` など）から作っているため。
- 路面表示の字と絵のセル（`icons.py:85-95` の `MARK_LABELS`・`MARK_PICTURE`）は、`catalog.py:142-153` の `MARKINGS` と同じ 16 個の名前を手で並べている。

### 2. 一覧の表: 新しい物を足すたびに同じ所を触る

直近 40 件の PR で、触った回数の多いファイル（画像・dat などを除く）:

| ファイル | 件数 | 層 |
|---|---|---|
| `addons/ami/README.md` | 21 | 文書 |
| `addons/ami/blender/ami_dat.py` | 12 | 一覧の表 |
| `addons/ami/blender/render.py` | 11 | 一覧の表 |
| `docs/reference/way-addon.md`・`docs/reference/cityscape.md` | 各 8 | 文書 |
| `addons/ami/blender/catalog.py` | 8 | 一覧の表 |
| `addons/ami/ACCEPTANCE.md` | 7 | 文書 |
| `addons/ami/blender/icons.py`・`addon_config.py` | 各 6 | 一覧の表 |
| `tools/blender/sheetlib/marking.py` | 4 | 描くコード |
| `tools/blender/sheetlib/sheetlib.py`・`core.py` | 各 2 | 土台 |

- 新しい物を足す PR（#194・#195・#198・#199 など）は、`catalog.py`（名前）・`render.py`（描き分け）・`ami_dat.py`（dat）・`icons.py`（アイコン）をほぼ毎回触り（#199 は `icons.py` を触らない）、多くは `addon_config.py` と `ingame/sample_spots.sh` も触る。
- PR のブランチに残った main の取り込みのコミットから見える範囲では、手で合わせ直したのは 40 件中 1 件だった。#194（6 車線の路面表示）と #195（高速道路の分岐・合流の路面表示）を並べて動かし、#194 の main の取り込み（`86c1be981`）で、`catalog.py` の `MARKINGS`、`ami_dat.py` の `MARKING_CELLS`、`icons.py` の `MARK_LABELS`・`MARK_PICTURE`、`sample_spots.sh`、`marking.py`、README、ACCEPTANCE の 7 ファイルがぶつかった。コードの 4 つ（`catalog.py`・`ami_dat.py`・`icons.py`・`marking.py`）は、同じ辞書の末尾に両方が足したことによる。ほかの 3 件（#185・#202・#214）の取り込みには、手で合わせた所が無かった。
- `ami_dat.py`（995 行）は物の種類ごとの dat の関数（`:293-866` に 16 本）を持ち、そのうち 14 本が似た頭の行（`obj=`・`name=`・`copyright=`・`intro_year=`・`retire_year=2999` など）を自分で並べている。並びは同じではない（車庫・操車場は `type=`・`waytype=` を途中に挟む）。共通の頭の関数 `_head`（`:275`）を使うのは、橋とトンネルの 2 本だけ。dat の中身は `check.sh` が `ami_dat.py` を流し直して `src/` と比べている（`check.sh:33-56`。`diff --strip-trailing-cr` なので、改行の違いは見ない）。

### 3. ゲームのスクリプト（`ingame/`）: 起動の決まりが 20 本に写してある

- ゲームの写しを作って `-mcp-port` で起動する行は 20 本のスクリプトにある（`game.sh:83`・`canal.sh:75`・`monorail.sh:75`・`depot.sh:88`・`crossing_sample.sh:178` など）。止める関数 `stop_game()` は 16 本にある。
- PR #216 は `game.sh:66` の地図の既定を `flat_512` から `flat_512_left_v64` に、設定の既定を `settings.xml.v64` に直した。直した理由は、検証用のフォルダに `flat_512.sve` が無くなり、v64 の実行ファイルは古い地図と設定を読めないため（PR #216 の本文と、作業の置き場の `AGENTS.md` の検証環境の節）。検証用のフォルダの `save/` には、今も `flat_512.sve` が無い（2026-11-24 に一覧で確かめた）。
- それでも `SAVE=${SAVE:-flat_512}` を既定に持つスクリプトが 17 本残っている（`canal.sh:61`・`monorail.sh:60`・`depot.sh:75`・`crossing_sample.sh:165`・`sample_check.sh:9`・`sample_parallel.sh:14`・`seam_slope_check.sh:16` など）。`settings.xml.v64` に差し替えるのは `game.sh`・`before_after.sh`・`catalog.sh` の 3 本だけ。#227 と同じく、1 か所だけ直して、写した所が残っている。ただし、これらの多くは `EXE` を必ず渡させ（例の注記は `OTRPv64_3.exe`）、`OTRPv64_3.exe` と `flat_512.sve` を組で使う古い手順としては一貫している。v64 の地図は左側通行の物しか作らない方針（作業の置き場の `AGENTS.md`）。
- 検証用のフォルダの絶対パスを既定に書いたスクリプトが 3 本ある（`before_after.sh:40`・`catalog.sh:17`・`cost_probe.sh:6`）。使い方の注記やエラーの文にも同じパスがある（`beta_check.sh:4`・`ex_check.sh:5`・`sample_check.sh:5` など）。作業の置き場の `AGENTS.md` は、個人の絶対パスを各リポジトリの中に書かないことにしている。
- 見本の NUT の原点などは、スクリプトが NUT の行を書き換えて流す（`canal.sh:24` の `NUT_SED`、`ingame/catalog.py:158-163` の `re.sub`・`replace`）。書き換えの型が NUT の行に当たらなくても止まらず、元の値のまま流れる。並びの値を `.sh` と `.nut` の両方に書き、注記でそろえている所もある（`crossing_sample.sh:19`・`canal_crossing.sh:16`・`crossing_train.nut:3`）。

### 4. 土台（`sheetlib.py`・`core.py`）: 大きい関数と、写した末尾

- `sheetlib.py` は 1795 行。道路のシートの `_road_sheet`（`:182-676`、約 495 行）と線路のシートの `_track_sheet`（`:807-1162`、約 355 行）が 1 本の関数で大きい。
- 2 つの関数は、同じ形の塊を写している: 坂の地面（`:490-493` ↔ `:949-951`）、背の高い壁を持つときの壁の取り出し（`:567` ↔ `:1078`）、橋の柱のセル（`:641` ↔ `:1105`）、壁の way-object のシートを書く末尾（`:663-672` ↔ `:1150-1160`）。
- 末尾の写しは、片方にだけ直しが入っている。線路の側は、側壁の無い版（center）のカーソルに行き止まりの端の壁の絵を使う 1 行（`:1157`）があり、道路の側（`:669-671`）には無い。`check_icons.py` は通る（道路の center の壁のカーソルが空でないかは、ここでは描いて確かめていない）。
- 直近 40 件で `sheetlib.py` を触ったのは 2 件（#190・#207）、`core.py` は 2 件。触る回数は少ない。

### 5. 検査: 描く側と dat を書く側のずれを拾う検査が CI に少ない

- `check.sh` の検査のうち、dat の絵の参照先のセルの中身を見るのは `check_icons.py`（アイコン・カーソルのセルだけ）と `check_embankment.py`（盛土だけ。`check.sh:72`）。`dat_lint_extra.py`（`check.sh:87`）は way の絵のキーの綴りと坂のそろいを見るが、セルの中身は見ない。way の絵（`image[...]` など）一般が空のセルを指していないかは見ない。
- `tools/blender/sheet_audit.py` は「参照先のセルが空・シートの外」を見るが（`sheet_audit.py:8`）、Blender で動くので `check.sh` と CI には入っていない。
- `check_icons.py` は Blender を使わずに PNG を読む（`check_icons.py:141` の `pixel`）。同じ読み方で way の絵の参照先も見られる。1 の表の対のずれのうち、「dat が描いていないセルを指す」形になるもの（例: 斜めのカーブの集まりから漏れた way の dat は、描いていないカーブのセルを指す）は、この検査で拾える。行のずらしの数値の対（指す先に別の絵がある）や、`addon_config.SHEETS` の漏れは拾えない。

### 6. 描くコード・そのほか

- 種類ごとのファイル（`marking.py` 845 行・`canal.py` 372 行・`sidewalk.py` 375 行など）は、直近で触ったのがその種類の作業だけで、ほかの作業とぶつかっていない（`marking.py` の 4 件は全部路面表示の作業）。
- `round.py` と `round_*.py`（精細化のラウンド）は、`render.py` の設定の上に差分を重ねる作りで、設定を写していない。
- `build.py`・`lineup.py` は名前の頭で pak と種類に振り分ける。漏れは `lineup.py --check`（`check.sh` が流す）が拾う。
- `catalog.py` の `Track` と `Road`（`:15-66`）は同じ 5 つの名前の作り方を持つ同じ形の型。
- `tools/blender/` の測る道具は、PNG を読む小さな関数 `load` を 7 本がそれぞれ持つ（`busy_measure.py:40`・`check.py:17`・`compose.py:78`・`hcat.py:14`・`ref_measure.py:33`・`sheet_diff.py:17`・`shift_diff.py:27`）。どれも 5〜10 行で、返す形（RGB か RGBA か）が道具ごとに違う。

## 推測・未確認事項

- 1 の表の対は、今は合っているが、次の物を足すときに片方だけ直すおそれがある、と見ている。#227 と同じ形だが、実際に誤ったのは `addon_config.DIAG_CURVE_SHEETS`（#227 で直した）と `addon_config.SHEETS`（残っている）だけ。
- ぶつかりの数（40 件中 1 件）は、PR のブランチに残った main の取り込みのコミットから数えた。main は squash でマージするので、取り込みの代わりに rebase したブランチや、force-push したブランチでは、合わせ直した跡が残らない。実際のぶつかりはこれより多いかもしれない。
- `ingame/*.sh` の地図の既定を `flat_512_left_v64` にそろえると、左側通行の地図になるので、道路の見本の向きなど撮れる絵が変わるかもしれない（未確認）。
- 道路の center の壁のカーソル（4 の片方にだけある 1 行）は、`icons.py` が後で書き直すために問題が出ていないと見ているが、確かめていない。
- `flat_512` を既定に持つ 17 本は、既定のまま流すと地図が無くて止まると見ている（`game.sh` が直す前にそうだった）。実際に流しては確かめていない。どれも `SAVE` を渡せば動く。
- 次の所は読んでいない、または名前と冒頭だけを見た: `core.py` の中身、`render.py`（772 行）と `icons.py`（562 行）の、引いた所のほかの中身、`sheetlib/__init__.py` が全モジュールの名前を 1 つの名前空間に集める作り（名前のぶつかりを個別に避けている。読みにくさの候補になりうる）、`release.py`・`ex_graft.py`・`check_crossing.py`・`check_depot.py`・`check_embankment.py`、`tools/ci/`、`tools/dat_lint_extra/`、`.nut` の中身、blender-poc（`sheetlib` を使う 2 本目のアドオン）。blender-poc は直近 5 件の変更が #108 まで遡り、今は動いていない。
- README の分け方（下の案 6）は、文書の決まり（`docs/README.md`・`addons/README.md`）に合う置き場所があるかを確かめていない。

## 結果どうしたか

コードは変えていない。直す案を、確かめやすい順に並べた。起票はしていない（直すかどうかはユーザーが決める）。

### 直す案（おすすめの順）

| 順 | 何を | issue のタイトル（案）と中身の要点 | 効果 | 危うさ・確かめ方 |
|---|---|---|---|---|
| 1 | 検査 | 「ami: dat の way の絵が描いていないセルを指していないかを check.sh で見る」。`check_icons.py` の PNG の読み方で、way・way-object・橋・トンネルの dat が指すセルが空でないかを見る（手前の絵は空でよい）。`sheet_audit.py` の「参照先が空」の判定を Blender 無しで回す形 | 1 の表のずれのうち「描いていないセルを指す」形のものと、これからの描き忘れを CI で拾う（行のずらしの数値の対や `addon_config.SHEETS` の漏れは拾えない）。ほかの直しの安全網になるので最初にする。盛土は `check_embankment.py` が既に見ているので重ねない | 低い。コードの絵も dat も変えない。既存のシートで誤検出が無いかを確かめる（意図して空のセルを指す路面表示の `MARKING_EMPTY_CELL` などは外す） |
| 2 | ゲームのスクリプト | 「ami: ingame の起動・停止を共通の関数にし、既定の地図を v64 にそろえる」。写しを作る・起動して待つ・止める・NUT の行を書き換える処理を 1 本（例 `ingame/lib.sh`）にまとめ、17 本の `flat_512` の既定と設定の差し替えをそろえる。検証用のフォルダの絶対パスの既定を外す。NUT の書き換えが当たらなければ止める | 地図の既定の直し忘れ（3 の事実）が消える。新しい見本のスクリプトが短くなる | 中くらい。ゲームを使うので、作業者に `uses:addon_check` とポートが要る。全部を一度に移さず、まず `canal.sh`・`monorail.sh`・`depot.sh` など同じ形の物から移し、移した物は見本を敷いて撮れることを確かめる。地図の既定だけを先に直す小さい issue に分けてもよい。`OTRPv64_3.exe` と `flat_512` の古い手順を捨てるか（既定を v64 にそろえるか、古い手順の既定のまま `SAVE` を必ず渡させるか）は、ユーザーが決める。v64 の地図は左側通行なので、撮れる絵が変わるかもしれない |
| 3 | 一覧の表 | 「ami: way の絵の並びの性質（斜めのカーブ・近い斜め・手前の絵・高架・シート名）を catalog.py の 1 か所から引く」。`ami_dat.py` の `NO_CLOSE`・`FRONT_WAYS`・`ELEVATED`・`NO_DIAG`・`NO_SWITCH`、`addon_config.SHEETS` を、catalog.py の物ごとの性質から作る。懸垂式モノレールを `addon_config.SHEETS` に足す（1 行で直り、`seam_judge.py`・`slope_measure.py` が止まる不具合なので、表の作り直しと切り離して先に直してもよい） | 新しい物を足すときに書く所が減り、片方だけ直す誤りが起きにくくなる | 低い。dat は `check.sh` の比べで変わらないことを確かめられる（Blender 無し。改行の違いは見ない）。`addon_config` は、今の `SHEETS` との差が懸垂式の 6 つだけになることを確かめる |
| 4 | 一覧の表と描く側 | 「ami: render.py の diag_curves・close・front_row を catalog.py の性質から決める」と「sheetlib: シートの行のずらしを Blender を使わない 1 つのモジュールに置く」。行のずらし（`WALL_FRONT_ROW`・`PIER_GATE_FRONT_ROW`・`_EMB_SNOW_ROW`・`CANAL_SNOW_ROWS`）と路面表示の `MARKING_SNOW_KINDS`・`MARKING_EMPTY_CELL` を、`sheet_settings.py` のような Blender を使わない所に置き、`ami_dat.py` と `sheetlib` の両方から引く（`sheetlib` は import すると Blender を読むので、`ami_dat.py` からは直接引けない） | 描く側と dat を書く側の注記でそろえている対が無くなる | 中くらい。土台（`sheetlib`）と `render.py` を触るので、ほかの描く作業と並べない。値は変えないが、変更前のコードで描いた絵を基準に、数枚を描いて同じになることを確かめる。#229（壁の絵のずれ）が終わってからにする |
| 5 | 一覧の表 | 「ami: ami_dat.py の dat の頭の行を _head にまとめ、icons.py の路面表示の字を catalog.py の MARKINGS の隣に置く」。14 本の頭の行のうち、並びが同じ物を共通にする（車庫・操車場のように途中に行を挟む物は、挟む行を引数で受けるか、まとめない）。`MARK_LABELS`・`MARK_PICTURE` を、`MARKINGS` の名前 → 種類の表と同じ所（種類ごとの字と絵のセル）にする | `ami_dat.py` が短くなり、路面表示を足すときの辞書が 1 つ減る（#194・#195 でぶつかった所） | 低い。dat は `check.sh` で、アイコンは `check_icons.py` と、描いたアイコンのシートの比べで確かめる |
| 6 | 文書 | 「ami: README の『作り』の節を物ごとの文書に分ける」。1121 行の README のうち、物ごとの「〜の作り」（`README.md:41-853` の 27 節など）を分け、README は目的・対象・ビルド・検証と各文書への案内にする | 直近 40 件の 21 件が README を触る。分ければ、並べた作業のぶつかりが減り、読む所を探しやすくなる | 中くらい。文書の決まりとの相談が要る（置き場所・docs-lint の対象）。ほかの文書からのリンクが切れないかを docs-lint で確かめる。ユーザーと置き場所を決めてから |

- 1 と 3 と 5 は、Blender もゲームも使わずに「変わっていない」ことを確かめられる。2 はゲーム、4 は描画が要る。
- 4 と 6 は、ほかの作業と並べにくい（4 は土台、6 は README を触る作業がほぼ毎回ある）。段の切れ目でまとめて片付けるのが向いている。

### やらなくてよいもの

| 何を | やらない理由 |
|---|---|
| `sheetlib.py` の `_road_sheet`・`_track_sheet` を分ける | 大きいが、直近 40 件で触ったのは 2 件で、ぶつかっていない。分けると全部の絵に響き、変更前のコードで描いた絵との比べが全種類で要る。blender-poc も使う。写した末尾（4 の事実）は、案 4 の後で、壁の way-object のシートを書く末尾だけを共通の関数にするなら小さく済む（その時に道路の center のカーソルを確かめる） |
| `catalog.py`・`ami_dat.py` をファイルで分けて、ぶつかりを減らす | 見える範囲で手で合わせ直したのは 40 件中 1 件（#194）で、コードは同じ辞書の末尾に足したことによる（跡が残らない形のぶつかりもありうる）。ファイルを分けても同じ辞書なら同じようにぶつかる。案 3・5 で辞書を減らすほうが効く |
| `build.py`・`lineup.py` の名前の頭による振り分け | 漏れは `lineup.py --check` が CI で拾う |
| 種類ごとの描くコード（`marking.py` など）を小さくする | その種類の作業しか触らず、ぶつかっていない。大きさは物の複雑さによる |
| `catalog.py` の `Track` と `Road` を 1 つの型にする | 同じ形だが 2 つだけで、増える見込みも少ない。直す効果が小さい |
| 測る道具の PNG の読み方をそろえる | 1 本ずつ単独で動かす道具で、5〜10 行の関数。そろえても読みやすさはほとんど変わらない |
| `round*.py` | `render.py` の上に差分を重ねていて、写していない |
