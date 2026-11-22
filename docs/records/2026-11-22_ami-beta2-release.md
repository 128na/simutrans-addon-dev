# AMI 第 2 弾のベータ版（beta.2）を配る準備

> 由来: [#170](https://github.com/128na/simutrans-addon-dev/issues/170)・[ADR 0007](../adr/0007-ami-beta-distribution.md)・[ADR 0008](../adr/0008-ami-scope-second-phase.md)・[ADR 0011](../adr/0011-ami-old-draw-position-separate-pak.md)

## 作った zip

`addons/ami/` で `python -X utf8 build.py` の後に、`python -X utf8 release.py --version beta.2 --paks ami_rail ami_road ami_tram ami_extra ami_monorail ami_canal ami_scenery --extract`（2026-11-22）。

- 入れた pak は 7 本（第 1 弾の 4 本に `ami_monorail`・`ami_canal`・`ami_scenery` を足した）。zip は約 12MB。全部入りの `ami.pak` と、旧描画位置の `ami_rail_old.pak` は入れない
- 配布 readme（`release/readme.txt`）に `ami_monorail.pak`・`ami_canal.pak` の行を足した。`ami_lineup.txt` は dat から自動で作られる（#138）

## 確かめたこと（OTRP）

展開した 7 本と同じ pak を、`addon_check` の OTRP（`OTRPv64_3.exe`）で `ingame/beta_check.sh`（既定の `PAKS`）に通した。`ok 172 items`、AMI の物の警告は無し（ポート 47300）。

## 本家 125.0.1 での読み込み（ユーザーに頼む）

スクリプトでは動かせない。次の手順で確かめてもらう。

1. 本家 Simutrans 125.0.1（pak128）のフォルダを複製する（既存の環境を汚さないため）
2. `work/release/ami-beta.2.zip`（`release.py` で作る。PR の本文に場所を書く）を展開し、中の `pak128` フォルダの 7 本の pak を、複製した `addons/pak128/` に入れる（`pak128/text/ja_ami.tab` は `addons/pak128/text/` へ）
3. 本家を起動し、新しい地図を作って、ログ（`simu.log`）に AMI の pak の読み込みエラーが無いか見る
4. 道具のメニューで、線路・道路・路面軌道・モノレール・運河・盛土・道路標識の AMI の物が出て、敷けるかを見る。OTRP だけの絵（分岐の絵・近い斜め）は本家では標準の絵になるだけで、エラーにならなければよい
5. 起動しない、物が出ない、敷くと落ちる、のどれかがあれば、その物の名前と `simu.log` を知らせる

## サムネイル（撮り直した）

ユーザーの決定（進捗管理から、2026-11-22「提案通りでOK」）で、[#103 の撮影用レイアウトの記録](2026-11-22_ami-thumbnail-layout-proposal.md)を元に撮り直した。

- 見本は `addons/ami/ingame/thumbnail_b2.nut`（#96 の `thumbnail.nut` は第 1 弾の街区）。撮り方は `NUT=ingame/thumbnail_b2.nut GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe PORT=47301 OUT=work/thumbnail/b2.png bash ingame/thumbnail_capture.sh` の後に `uv run ingame/thumbnail_compose.py work/thumbnail/b2.png`（`docs/thumbnail/` の `thumbnail.png`・`ogp.jpg` を書く。`--plain` で文字なし）
- 記録の案からの違い: 画面に入るのは (rx,ry) の |rx|+|ry| が約 20 までのひし形なので、案の区画（±24）を縮めた。案の「温暖と降雪の境」は x=256 でなく、`tool_set_climate` で画面中央の東（rx>=2）を降雪にした。踏切・Y 字・三方分岐・電柱・標識は小さくしか置いていない。駅名のラベルは空白に変えて隠した
- 置いた物: 複線の在来線と直結軌道（丘のトンネルから東の構内へ。車庫・操車場・側線）、高架の高速線+ラダー軌道（地上の複線と幹線の上をまたぐ）、分離帯つきの壁の高速道路の高架、懸垂式・跨座式のモノレールの高架（電化）、運河と船の車庫と水路の踏切、4 車線の幹線（路面表示）、歩道の種類（煉瓦・タイル・アスファルト）と電柱、道路標識、路面軌道
- 文字（題名と内容の箇条書き）は `thumbnail_compose.py` の `BODY` を第 2 弾の物に合わせた。第 1 弾の `thumbnail.png`（ユーザーが手動で文字入れしたもの）は置き換わる（git の履歴に残る）
- `release.py` は `docs/thumbnail.png` を探していて、画像が `docs/thumbnail/` に移った後は zip に入っていなかった。`docs/thumbnail/thumbnail.png` に直した

## 未決（ユーザーの判断待ち）

- サムネイルの出来（構図・文字の重なり。題名が高速道路の高架に、内容の文字が高架の高速線にかかる）。直す所があれば指示をもらう
- 旧描画位置の `ami_rail_old.pak` は、#178 のマージを待って、同じリリースに別の zip（`ami-beta.2-old.zip`）で付ける（ユーザーの決定。進捗管理から、2026-11-22）
- タグ `ami-beta.2` とプレリリースは、承認の後に出す
