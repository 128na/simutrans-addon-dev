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

結果（ユーザーが確かめた。進捗管理から、2026-11-22「動作 OK」）: 本家 125.0.1 で動作した。

## サムネイル（撮り直さない）

ユーザーの決定（進捗管理から、2026-11-22）。#103 の[撮影用レイアウトの記録](2026-11-22_ami-thumbnail-layout-proposal.md)を元に一度撮り直したが、見て「撮り直さない。レイアウト作成も修業が必要そうなので、自動作成は保留にする」と決まった。

- `docs/thumbnail/` は main のまま（第 1 弾でユーザーが手動で撮った画像）。撮り直した試作（見本の nut と画像）はこの PR に入れない
- 試作で分かったこと: 等倍で画面に入るのは、中心のタイルからの (rx,ry) の |rx|+|ry| が約 20 までのひし形で、#103 の案の区画（±24）は縮める必要がある。降雪の境は `tool_set_climate` で好きな位置に塗れる。建てた駅（操車場）の名前のラベルは `halt.set_name(" ")` で隠せる
- `release.py` は `docs/thumbnail.png` を探していて、画像が `docs/thumbnail/` に移った後は zip に入っていなかった。`docs/thumbnail/thumbnail.png` に直した（直したので、beta.2 の zip には第 1 弾のサムネイルが入る）

## 旧描画位置の zip（ami-beta.2-old.zip）

ユーザーの決定（進捗管理から、2026-11-22）で、`ami_rail_old.pak` は別の zip にして同じリリースに付ける。#178 は絵を直さずに閉じることになったので、pak の中身は今のまま。

- 作り方: `python -X utf8 release.py --version beta.2-old --paks ami_rail_old --readme release/readme_old.txt --no-thumbnail`（`release.py` に `--readme`・`--no-thumbnail` を足した）。zip は約 3.9MB（`work/release/ami-beta.2-old.zip`）
- 中身は `pak128/ami_rail_old.pak`・`ami_readme.txt`（旧用 `release/readme_old.txt`）・`ami_license.txt`・`ami_lineup.txt`（56 個）・`pak128/text/ja_ami.tab`（道路標識の訳。旧の pak には要らないが害は無い）
- `ingame/beta_check.sh`（`PAKS=dist/ami_rail_old.pak`、ポート 47302）: `ok 56 items`、警告なし

## 未決（ユーザーの判断待ち）

- タグ `ami-beta.2` とプレリリースは、承認の後に出す
