---
name: way-addon-build
description: Simutrans の way 系アドオン（AMI・blender-poc の線路・道路・側壁・架線・高架・橋脚・橋・トンネル）を Blender のスクリプトで作る・直すときの作業手順。手本を refs の索引から引く、本体のソースで確かめる、確認用の色で見てからゲームで見る、どのファイルを直すか、確かめ方、サブエージェントへの任せ方。「AMI の次のステップを進めて」「高速線/道路/路面軌道を作りたい」「側壁を付けたい」「高架/橋/トンネルを作りたい」「back/center/front を作りたい」「基盤がはみ出す/すき間が出る」「壁に縦線が出る」「手前の絵（frontimage）を分けたい」「雪の絵を足したい」「分岐の絵 / switch 画像を作りたい」「新しい way アドオンを足したい」と言われたとき、addons/ami・addons/blender-poc の render・dat・ingame を直すときに使う。本体の描き方・dat のキー・持ち分などの決まりは docs/reference/way-addon.md、手本の場所は docs/reference/refs-index.md を読む。位置合わせ（つなぎ目のずれ）は way-calibration スキル。
---

# way アドオンを作る・直す手順（Blender のスクリプト）

ここには作業の進め方だけを書く。作業の前に次を読む。

- 決まり（本体の描き方、持ち分、dat のキー、側壁・基盤の作り）: [docs/reference/way-addon.md](../../../docs/reference/way-addon.md)
- 手本の場所と使ってよい範囲: [docs/reference/refs-index.md](../../../docs/reference/refs-index.md)
- アドオンの今の状態とできたと言う条件: `addons/<アドオン>/README.md`・`ACCEPTANCE.md`
- 位置合わせ: [way-calibration](../way-calibration/SKILL.md)

## 1. 進め方

1. **最新の `main` から始める。** `git status -sb` で今のブランチと遅れを確かめ、issue の範囲と言葉（`close` と `center` など）を自分の言葉で言い直す
2. **手本を先に見る。** `refs-index.md` で作るものを引き、iss の dat と絵を読む。標準とのつなぎ、線の本数や高さ、雪、橋・トンネルのキーは pak128 も見る。数値は手本から測る
3. **本体のソースで決まりを確かめる。** dat のキー・絵の番号・建設の条件は `../simutrans/descriptor/`・`bauer/`・`script/api/` を読む。リファレンスに無い決まりを確かめたら、確かめた場所を付けて足す
4. **受け入れ条件を確かめる。** `ACCEPTANCE.md` の該当の行を確かめ、足りなければ足す
5. **確認用の色でセルを見る → ゲームで見る。** `SHEET_LAYOUT=1` で部品ごとの単色で描き（`work/layout/`）、形が合ってから通常の色で描いてゲームに入れる
6. **自分で見つける。** 描いたセル、ゲームの見本、判定ツールで確かめる。ユーザーに指摘された欠陥は、次から同じものが見える区画か判定に足す
7. **ユーザーが確かめられる形で止まる。** 見本を敷いたゲームを開いたままにし、見る場所の座標と観点を一覧にする。ローカルでコミットして止まる（push・PR・マージは指示を待つ）
8. **分かったことを書き分ける。** 決まりはリファレンスへ、経緯は `docs/records/` へ、手順が変わったらこのスキルへ

作業の報告（PR を作るときは本文）には「見た手本」を書く。

```text
見た手本: <ファイル:行または画像のセル> / 取り入れたこと / 取り入れなかったことと理由
```

## 2. 「できない」と言う前に

「本体の制限」「作れない」と報告するのは、次の 4 つを済ませてからにする。

1. 検証環境の差を除いた（exe の版、`script/`、入れた pak、保存データ）
2. アドオンの `build.py` と同じ設定で作った（AMI は `pak256`。試しの pak も同じ）
3. 同じことをしている手本を、refs の実物でゲームに出して比べた
4. 本体のソースの該当する箇所を示せる

報告には、見た手本のファイルと、試した条件を書く。

## 3. どこを直すか

描画の共通部分は `tools/blender/sheetlib/`。アドオンは設定と名前を持つ。設定の分け方は [tools/README.md](../../../tools/README.md)。

| もの | 役目 |
|---|---|
| `addons/ami/blender/catalog.py` | 軌道の種類の表（Blender を使わない）。way・基盤・高架・橋・トンネルの名前を導く |
| `addons/ami/blender/render.py` | AMI のプロファイル（`TRACK_PROFILES`。種類ごとの設定は `TRACK_SETTINGS`）と描く対象（`SHEETS`） |
| `addons/ami/blender/ami_dat.py` | dat の書き出しと値。dat は手で書かない |
| `addons/ami/blender/addon_config.py` | 判定の道具が読む名前の対応 |
| `addons/ami/build.py` | makeobj で pak を作る |
| `addons/ami/ingame/sample.nut` | ゲームに敷く見本。先頭の `TRACK` で軌道の種類を選ぶ |
| `Datum(drop, ground)` | 基準面。`bed`（路盤）と `rail`（走行面）。描画位置のずれは部品ではなく基準面が持つ |
| `Part` | 部品。基準面・横幅の倍率・材質・形・まとまり（`group`） |
| `assemble` | 部品を経路ごとに作り、基準面の分だけ動かし、坂を当て、タイルの外を切る |
| `build_base` | 基盤と高架の躯体。残した壁の外側を削る |
| `render_layers` | 高さのある部品を別の層として描き、奥と手前の絵に分ける |
| `TRACK_PROFILES` のキー | シート名・基準面・`groups`・`walls`・`snow`・`skin`・`snow_skin`・`replace`・`track_parts`・`parts`・`bed_fills` など。意味は `tools/README.md` と `track_sheet` の説明 |

- AMI の軌道の種類を足すときは、`catalog.py` の `TRACKS`、`render.py` の `TRACK_SETTINGS`（部品と材質は上のキーで渡す）、`ami_dat.py` の `VALUES` に足す。共有の壁・架線・橋脚は足さない。旧描画位置の版（`OLD_TRACKS`。`TRACK_SETTINGS` が新の設定から導き、壁・架線・橋脚も旧用が別にある）も要るので、`TRACKS` に足したら `OLD_TRACKS` の分も増える（ADR 0011）
- 部品を足すときは、乗る基準面を選ぶ。部品ごとに位置を足し引きしない
- 寸法・色は名前の付いた定数にする（ADR 0005）
- 共通部分を直したら、既存のアドオンのシートが変わらないことを確かめる
- 描き直しは `python -X utf8 ../../tools/blender/render_parallel.py [--jobs 16] <対象>...`。ログは `work/render_<対象>.log`。ほかの作業者と同時に描いても、Blender の数は共有の描画の枠（`SHEET_SLOTS`）を超えない（`tools/README.md` の「描画が遅いとき」）
- Boolean は `sheetlib` の `boolean()` を使う（`tools/README.md` の「描画が遅いとき」）

## 4. 確かめ方

| 何を | どうやって |
|---|---|
| 部品の出方 | `SHEET_LAYOUT=1` で描いて `work/layout/` を見る。部品の色は `sheetlib/layout_colors.py` に足す |
| 一部のセルだけ試す | `SHEET_ONLY=ew,nse,diag_nw` を付けて描く。シートは `work/only/` に書かれ、`src/` は変わらない |
| 既存の絵が変わらない | `git status` の `src/` の差分と `tools/blender/sheet_diff.py` |
| AMI の全体 | README の「導入と検証」の順に `blender/ami_dat.py`・`build.py`・`ingame/sample_check.sh`・`ingame/sample_capture.sh`。全区画をまとめて撮るだけなら `ingame/sample_parallel.sh`（8 台） |
| blender-poc の全体 | README の手順と `addons/blender-poc/ingame/` の各スクリプト |
| シート全体の欠陥の候補 | `tools/blender/sheet_audit.py`（参照先の空セル、端の切れ、小さな穴と点、つないだときのすき間）。同じ作りの軌道は `--compare` で塗りの範囲を比べる |
| ドットの欠け・はみ出し・接続部のずれ | 見たい所を `tools/blender/zoom.py` で 3 倍以上に拡大して読む。等倍の画像だけで「問題なし」としない（限界はリファレンスの 8.3） |
| 色加減 | 前後の比較は `ALL=1` を付けた `sheet_diff.py`、タイルどうしの比較は同じ部品の画素の値で見る。小さな色の差は画像を読んでも分からない。最後の見た目はユーザーが見る |
| アイコン・カーソル（AMI） | 書き込みは `addons/ami/blender/icons.py`、ゲームのメニュー・カーソルの撮影は `addons/ami/ingame/icon_capture.sh`。流し方・札の字などの決まりは [AMI の「アイコン・カーソル」](../../../addons/ami/docs/objects/icons.md#アイコンカーソル25)。シートを描き直した後の流し直しの条件もそこにある |
| 雪 | 検証の地図（リファレンスの 8.1）の降雪側（x=256〜）に同じ見本を敷く |
| 車両との重なり | スクリプトで走らせられるものは走らせ、最後の見た目はユーザーが見る |

### 分岐（switch・ex）の絵を直すとき

一つの要素だけ直して終わらせない（#205 で、高速道路の分岐の轍だけを直し、路肩の白線がカーブのまま残った。経緯は `docs/records/2026-11-23_ami-expressway-switch-diagonal.md`）。描き方の決まりは [リファレンス 9 章](../../../docs/reference/way-addon.md#9-分岐switchの絵otrp-専用)。

- 直したセルを、線路の手本（同じ分岐のセル）と並べて、次の要素を 1 つずつ見る: 轍、白線（路側線・中央線）、雪、壁、基盤、高架
- 並べた画像は 3 倍以上に拡大して読む（上の「ドットの欠け…」の行）
- 確かめた要素と、手本と違ったものを、PR の本文に並べる。見ていない要素は「見ていない」と書く

### 検査と修正を自分で回すとき

ユーザーの確認を待たずに「検査 → 修正 → 再検査」を回すときは、無限に続けないよう回数を数える。

- 同じ箇所の修正は 5 回まで。1 つのアドオンの修正は合計 20 回まで
- 上限に達したら修正を止め、残った候補と試したことを報告する
- 修正の回数と、直した箇所は記録（`docs/records/`）に残す
- 最後の見た目の判断はユーザーに残す。自動で確かめられた範囲と、確かめられなかった範囲を分けて報告する

## 5. サブエージェントに任せるとき

| 担当 | 任せること |
|---|---|
| メイン | issue の範囲、設計と名前と値の判断、「できない」の判定、報告の確かめ、ユーザーとのやり取り |
| `worker-basic` | 手本の調査と測定、結果の集計、3 倍以上に拡大した画像の欠陥探し。読み取りが中心 |
| `ticket-worker` | 1 つの issue の実装、描画、ゲームの確認、ローカルコミット。画像を読む作業もここで行う |
| `worker-light` | 変更箇所が決まった置換などの定型作業 |
| `reviewer` | コードと文書の確認。見た目の合否は任せない |

`ticket-worker` への依頼文には次を必ず書く。

- issue の番号と、始めるコミット
- このスキルと、読むリファレンス（`way-addon.md`・`refs-index.md`）
- 見る手本と、報告に「見た手本」を書くこと
- 2 章の「できない」の条件
- 完了条件（`ACCEPTANCE.md` の行、敷く見本、ユーザーに見てもらう座標）
- ローカルコミットで止まること。ゲームは自分で起動した物だけ閉じること

長い作業は確認の区切りごとにコミットする。ユーザーの指摘は同じワーカーに続けて渡す。

## 6. 作業の注意

- モジュールの直下のループ変数や、関数の中の変数に、既にある関数・変数と同じ名前を使わない（`_side`・`half` を上書きして形が崩れた）
- 「タイルの境にある面」を探すときは符号を見る（両端が境にある側面まで消した）
- ゲームを名前でまとめて終了させない。自分が起動したゲームだけを閉じる
- 動作検証のゲームは検証の地図で起動する（地図の名前と決まりはリファレンスの 8.1）。開くたびに空なので、見本は毎回流す
- 画像は必要なセルだけ切り出し、拡大して読む（`tools/blender/zoom.py`・`hcat.py`）。数値で判定できるものは先に数値で見る
- スクリプトのファイルは heredoc ではなく Write・Edit で書く
