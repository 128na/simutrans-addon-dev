# AMI 第 3 弾のベータ版（beta.3）を配る準備

> 由来: [#234](https://github.com/128na/simutrans-addon-dev/issues/234)（管理 issue [#172](https://github.com/128na/simutrans-addon-dev/issues/172)）・[ADR 0007](../adr/0007-ami-beta-distribution.md)・[ADR 0009](../adr/0009-ami-beta-renames-without-readme-notice.md)・[前の版の記録](2026-11-22_ami-beta2-release.md)

## 目的 / 発端

第 3 弾（景観）で足した物・汚しと精細化・#217 の運河の直し・#229 の壁の絵のずれの直しを、beta.3 として配る。前の版は beta.2（`ami-beta.2.zip` と旧描画位置の `ami-beta.2-old.zip`）。

## 分かったこと（事実）

作った zip（2026-11-24、main の 49b5f56。`addons/ami/` で `python -X utf8 build.py` の後）:

- `python -X utf8 release.py --version beta.3 --paks ami_rail ami_road ami_tram ami_extra ami_monorail ami_canal ami_scenery --extract`: `work/release/ami-beta.3.zip`（約 20MB。beta.2 は約 12MB）。7 本、`ami_lineup.txt`（200 行）、`ami_readme.txt`、`ami_license.txt`、`thumbnail.png`、`pak128/text/ja_ami.tab`
- `python -X utf8 release.py --version beta.3-old --paks ami_rail_old --readme release/readme_old.txt --no-thumbnail --extract`: `work/release/ami-beta.3-old.zip`（約 3.9MB）。旧の 56 個

beta.2 の dat（3e0147e）と今の `src/*.dat` の `name=` を比べた物の増減:

- 消えた（14）: `ami_road_general_lane1`〜`7`・`ami_road_expressway_lane1`〜`7`（#187）
- 増えた（19）: `ami_mark_*` の 17 個（#187・#188・#189）、`ami_sign_crosswalk`・`ami_sign_crosswalk_one_way`（#162）、`ami_canal_scenic`（#161）。そのほかは名前を変えていない
- 物の数: beta.2 の 172 から 14 を引き 19 を足して 177。pak ごとは `ami_lineup.txt` の見出しのとおり（rail 46・road 50・tram 2・extra 52・monorail 14・canal 3・scenery 10）

ゲームでの読み込み（`addon_check` の写し、`sim-WinGDI64-OTRPv64.exe`（v64）、`flat_512_left_v64.sve`、設定は `settings.xml.v64`。`--extract` で展開した pak をそのまま `PAKS` に渡した。使用状況は `strip_usage_log.sh` で外した）:

- 種類別の 7 本（ポート 47200）: `ok 177 items`、AMI の物の警告なし
- 旧描画位置（`ami_rail_old.pak`、ポート 47201）: `ok 56 items`、警告なし
- 検証用の写しの置き場は片付けた。`addon_check` には何も置いていない

## 推測・未確認事項

- 本家 125.0.1 での読み込みは確かめていない（スクリプトが使えず、親 `AGENTS.md` の方針で未確認に挙げない。beta.2 のときはユーザーが確かめた）
- readme の「動作確認」の版（OTRP v63.3 以降）は、今回は v64 でだけ確かめた。書き換えていない

## 結果どうしたか

- `release/readme.txt` の主な中身（多車線の路面表示に 6 車線・分岐と合流、運河に景観の運河、景観に横断歩道）と `release/readme_old.txt` の同梱の zip の名前を beta.3 に合わせた。`ami_lineup.txt` は dat から自動で作る
- README の配布の節と ACCEPTANCE（beta.3 の扱い・6-3）を beta.3 に合わせた
- GitHub のプレリリース（タグ `ami-beta.3`）は、この PR のマージの後、ユーザーの承認を得てから作る。zip は `work/release/` に置いてある（git 管理外）
