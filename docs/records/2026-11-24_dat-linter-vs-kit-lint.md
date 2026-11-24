# 調査/作業ログ: dat_linter と simutrans-blender-kit の linter の差、足した検査（#224）

（2026-11-24）

## 目的 / 発端

#206 の調査（[blender-kit-survey](2026-11-24_blender-kit-survey.md)）で、kit の `tools/lint_dat.py` は AMI の dat 234 本でエラー 0・警告 0 だった。ただし CI の `dat_linter`（v0.3.1）と同じ dat・同じ誤りで比べていない。差を表にして、足りない検査を `addons/ami/check.sh` に足す（[#224](https://github.com/128na/simutrans-addon-dev/issues/224)）。

## やったこと

- AMI の `ami_canal.dat`（と、その png）から、誤りを 1 つずつ入れた dat を 19 本作り（一時の場所。リポジトリには入れない）、次の 4 つに通した。
  - `dat_linter` v0.3.1（`lint --tile-size 256`）
  - kit の `tools/lint_dat.py`（コミット `0bc64b7`。写しは変えず、`core/`・`tools/` を一時の場所へ写して `python -I` で実行）
  - makeobj 60.12（本家 125.0 用、`makeobj pak256 …`）。`build.py` は出力に warning / error があれば止まる
  - 足した `tools/dat_lint_extra/dat_lint_extra.py`
- 足した検査を AMI の dat 234 本（`addons/ami/src`）と blender-poc の dat 28 本に通した。

## 分かったこと（事実）

### 差の表（○ = 検出、× = 検出しない）

| 入れた誤り | `dat_linter` | kit | makeobj（`build.py` が止める） | 足した検査 |
|---|---|---|---|---|
| キーの綴りの誤り（`bogus_key=1`） | × | ○ `unknown-key` | ○ `Warning: … ignored (check spelling)` | ○ `unknown-key` |
| `image[zz][0]`（ribi の綴りの誤り） | × | × | ○ 同上 | ○ `way-key` |
| `image[nse3][0]` | × | × | ○ 同上 | ○ `way-key` |
| 文字の値の後ろの `# 注記`（`copyright=AMI # note`・`name=… # note`） | × | ○ `value-comment` | ×（`name` は pak の名前が変わる） | ○ `value-comment` |
| 数値の値の後ろの `# 注記`（`topspeed=60 # note`） | × | ×（意図どおり。atoi が読み飛ばす） | × | ×（同じ） |
| 数値のキーに数字でない値（`topspeed=fast`・`cost=1,000`） | × | ○ `bad-int` | ×（0・1 に読む） | ○ `bad-int` |
| 行頭が空白の行（` maintenance=1`） | × | ○ `dropped-indent` | × | ○ `dropped-indent` |
| 知らない obj の種類（`obj=wayy`） | △ 「未対応」と言うだけで、0 エラー | ○ `unknown-obj` | × 黙って飛ばす（pak に入らない） | ○ `unknown-obj` |
| 坂の絵が 1 つだけ（`imageup[12]` だけ） | × | ×（`slope_image_block` は dat を作る側で、linter に無い） | ×（欠けた坂は絵が出ない） | ○ `way-slope` |
| 存在しない png（`image[ns][0]=nofile.0.2`） | ×（way では `image[-]` しか見ない） | × | ○ error | ×（makeobj で足りる） |
| 範囲外の行・列（`ami_canal.0.99`） | × | × | ○ error | ×（同上） |
| 未知の waytype（`waytype=watr`・`bio`） | ○ `unknown-waytype` | ○ `bad-waytype` | ○ error | — |
| 同じキーの 2 回目（`cost=999` を足す） | ○ `duplicate-key` | ○ `dup-key` | × | —（dat_linter で足りる） |
| `name=a/b`（ファイル名に使えない文字） | ○ `name-forbidden-filename-character` | × | × | — |
| アイコン無し（`icon=` の行を消す） | × | ○ `no-icon` | ×（置けない way になる） | ×（`check_icons.py` が見ている。下） |
| 基本の絵 `image[-]` が無い | ○ `missing-base-image` | × | ○ | — |
| 大文字のキー・`=` の前後の空白 | ×（誤りではない） | ×（同） | 同 | ×（同） |

- 上の誤りの入れ方は、`ami_canal.dat` の行を書き換える、または末尾に 1 行足す、のどちらか。足した行が既存のキーと重なると `duplicate-key` になるので、値の書き換えでやり直した（最初に末尾へ足した版は、`dat_linter` と kit の両方が `duplicate-key` だけを報告して、本来の誤りを見ていなかった）。
- `dat_linter` は obj の種類ごとの中身（waytype・重複・基本の絵・車両・工場など 78 規則）を見るが、`obj=way` の絵の参照は `image[-]` しか検証しない。kit の linter は本体のソースから作ったキー表で全キーを見るが、way の絵のキーの綴り（ribi・坂）は見ない。way の絵のキーのうち、両方が見ないのは `image[zz]` の綴りと坂の欠けで、前者は makeobj の warning が拾い、後者は誰も拾わない（存在しない png と範囲外の行・列も両方が見ないが、makeobj の error が拾う。`dat_linter` は way で `image[-]` だけ範囲を見る）。
- 差の中で、makeobj も拾わず `dat_linter` にも無いのは `value-comment`・`bad-int`・`dropped-indent`・`unknown-obj`・坂の欠け。`unknown-key` と `way-key` は makeobj が warning を出すので、`build.py` を回す CI では拾えているが、`SKIP_BUILD` の手元では拾えず、makeobj が入れ物ごとに 1 件で止まる前に一覧で見たい、という程度の価値。
- kit の `value-comment` は `icon=> 絵 # note` も誤りにする（`icon` を text の読み方と見るため）。本体は絵の参照の後ろの注記を許す（kit 自身の docstring も同じ）ので、これは誤検出。足した検査は `icon`・`cursor` を外した。
- kit の `no-icon`（アイコンの無い way・way-object・roadsign・橋・トンネル）は、AMI では `addons/ami/check_icons.py`（アイコン・カーソルの参照先）が見るので、足さなかった。
- AMI の dat 234 本と blender-poc の dat 28 本は、足した検査で誤り 0（誤検出 0）だった。

## 推測・未確認事項

- キー表（`dat_schema.json`）は kit が本体 124.5.1 から作ったもの。レビューで、この fork の `descriptor/writer/*.cc` の `.get*("キー")` と `sprintf` の形が全部キー表に含まれることを機械的に確かめた（欠け 0）。AMI と blender-poc の dat も通った。これから使うキーで `unknown-key` が出たら、キー表の古さか誤検出かを分ける（許可のキーを足す入れ物は、必要になったときに `dat_lint_extra.py` に作る）。
- 足した検査は、`obj=way` の絵のキーの表を、この fork の `descriptor/writer/way_writer.cc`（`../simutrans`、`5505075fd`）の `ribi_codes` と坂（3・6・9・12）から手で写した。橋・トンネルなどのキーの綴りは `dat_schema.json` の型（`image[%s]` など）で任意の名前を許すので、綴りの誤りは見ない。
- makeobj の warning で拾える `unknown-key` は、makeobj の版（OTRP の fork の makeobj は近い斜めのキーを知らず、`ignored` と出る、`tools/README.md`）で変わりうる。足した検査は版に依らない。
- kit の `way-slope` 相当（坂を 4 つそろえる）は、kit では dat を作る側にあり、linter には無い。足した検査は、この fork の綴り（`imageup[3|6|9|12]`）で書き直した（kit の `imageup[n|w|e|s]` は借りていない）。

## 結果どうしたか

- `tools/dat_lint_extra/` に補助の検査を足した（`dat_lint_extra.py`、キー表 `dat_schema.json`、kit の MIT の表示 `LICENSE.simutrans-blender-kit`）。`addons/ami/check.sh` の `dat_linter` の次の段で呼ぶ。標準ライブラリだけで動く。`tools/README.md` に使い方を足した。
- kit から借りたのは、キー表 `dat_schema.json`（そのまま写し）と、規則の名前と考え方、キー展開（`expand_key`）と `%s` の正規表現（`core/schema.py` に由来。コードは書き直した）。出典と MIT の帰属は `dat_lint_extra.py` の先頭と `LICENSE.simutrans-blender-kit`。
- CI で動くことは、PR の CI（`addon-ami`）の結果で確かめる（結果は PR に書く）。
- レビューを受けて、`bad-int` を本体の読み方に合わせ（`get_int` は 16 進と 8 進、`get_int64` は小数を許す）、絵の参照のキー（名前に `image`・`diagonal` を含む）の `# 注記` を許し、`obj=Way` の大文字小文字を区別し、`backimage` を弾き、BOM を許し、`--self-test`（検査自身の退行を見る）を足した。
