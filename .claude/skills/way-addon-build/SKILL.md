---
name: way-addon-build
description: Simutrans の way 系アドオン（線路・道路・側壁・高架・橋・トンネル）を Blender のスクリプトで作る・直すときの作業手順。受け入れ条件を先に書く、手本と本体のソースを先に見る、確認用の色で見てからゲームで見る、どのファイルを直すか、確かめ方。「側壁を付けたい」「高架/橋/トンネルを作りたい」「back/center/front を作りたい」「基盤がはみ出す/すき間が出る」「壁に縦線が出る」「手前の絵（frontimage）を分けたい」「雪の絵を足したい」「アイコンを区別したい」「分岐（T字・十字）の絵 / switch 画像 / nse1・nse2 を作りたい」「新しい way アドオンを足したい」と言われたとき、addons/blender-poc の render.py・track_dat.py・ingame/*.nut を直すときに使う。本体の描き方・dat のキー・持ち分などの決まりは docs/reference/way-addon.md（知見）を読む。位置合わせ（つなぎ目のずれ）は way-calibration スキル。
---

# way アドオンを作る・直す手順（Blender のスクリプト）

ここには作業の進め方だけを書く。決まり（本体の描き方、持ち分、dat のキー、手本の作り、側壁・基盤の作り）は
[docs/reference/way-addon.md](../../../docs/reference/way-addon.md) にある。**作業の前に読む。**
位置合わせの手順は [way-calibration](../way-calibration/SKILL.md)、できたと言う条件は [ACCEPTANCE.md](../../../addons/blender-poc/ACCEPTANCE.md)。

## 1. 進め方

1. **受け入れ条件を先に書く。** `ACCEPTANCE.md` に条件・状態・確かめ方を書き、直すたびに表で確かめる
2. **手本を先に見る。** pak128 のソース（`../pak128/`）と iss（`../iss/src/`、ビルド済みは `../iss/release/pak128/`）の絵と dat を、作る前に見る
3. **本体のソースで決まりを確かめる。** dat のキー・絵の番号・建設の条件は `../simutrans/descriptor/`・`bauer/`・`script/api/` を読む。
   リファレンスに無い決まりを確かめたら、リファレンスの表に足す
4. **確認用の色でセルを見る → ゲームで見る。** `BPOC_DEBUG_COLORS=1` で部品を色分けして描き（`work/debug/`）、形が合ってから通常の色で描いてゲームに入れる
5. **本体のシートを崩さない。** 試すものは別のアドオン（別のシート・dat）にする。本体を描き直したら、前のシートと全画素を比べる
6. **分かったことを書き分ける。** 決まりはリファレンスへ、経緯は `docs/records/` へ、手順が変わったらこのスキルへ

## 2. どこを直すか（`addons/blender-poc/blender/render.py`）

絵の元は 3D ファイルではなくスクリプトで、毎回形を組み立てて撮る。

| もの | 役目 |
|---|---|
| `Datum(drop, ground)` | 基準面。描画位置のずれは部品ではなく基準面が持つ。`bed`（路盤: 道床・壁・基盤）と `rail`（走行面: まくらぎ・レール・車止め） |
| `Part` | 部品。乗る基準面・横幅の倍率・材質・形（経路 → 頂点と面）・まとまり（`group`）。`where="end"` は行き止まりの端だけ、`tall` は高さのある部品、`corridor` は分岐で削る幅、`ground` は坂の下を埋める躯体 |
| `assemble` | 部品を経路ごとに作り、基準面の分だけ動かし、坂を当て、タイルの外を切る |
| `datum_move` | 「画面で n px 下げる」の計算はここ 1 か所 |
| `build_base` | 基盤。タイル全面の板から、残した壁の外側だけを削る |
| `render_layers` | 高さのある部品を別の層として描き、カメラに近い側を手前の絵に分ける |
| `_ground_mask`・`rise`・`open_ends`・`solid`・`lower`・`spill`・`NEAR_AXIS` | 持ち分（リファレンスの 2 章）を実装している所 |
| `TRACK_PROFILES` | アドオンごとの設定（シート名・基準面・使う `group`・`walls`・`snow`・`front_row`・`lower`・`band`） |

- 部品を足すときは、乗る基準面を選ぶ。部品ごとに位置を足し引きしない
- dat は手で書かず `python -X utf8 blender/track_dat.py` で書き出す。シートの行の並びは
  「奥の絵 4 行 →（手前の絵 4 行）→ 雪の奥の絵 4 行 →（雪の手前の絵 4 行）」

## 3. 確かめ方

| 何を | どうやって |
|---|---|
| 部品の出方 | `BPOC_DEBUG_COLORS=1 blender ... render.py -- <シート>` → `work/debug/` のセルを見る |
| 全方位の表示 | `bash ingame/full_check.sh`（`ingame/full.nut` のレイアウト。way ごとに 5 か所を並べる） |
| 複線・行き止まりの並び・高架・橋・トンネル | `ingame/wall.nut`・`elev.nut`・`bridge.nut`・`tunnel.nut` |
| 雪 | `flat_snow.sve` で起動して同じ見本を流す |
| 本体が変わっていないこと | 描き直して前のシートと全画素を比べる |
| アイコンだけ直したとき | `blender/icons_only.py`（絵のセルを描き直さない） |
| 車両との重なり | ユーザーに手で編成を走らせてもらう |
| 分岐の絵（OTRP の switch 画像） | T字を作り、タイルの詳細で選択肢を順に選んで絵が変わるかを見る。キーと絵の対応・スクリプトでの選び方はリファレンスの 9 章 |

## 4. 作業の注意

- モジュールの直下のループ変数や、関数の中の変数に、既にある関数・変数と同じ名前を使わない（`_side`・`half` を上書きして形が崩れた）
- 「タイルの境にある面」を探すときは符号を見る（両端が境にある側面まで消した）
- ゲームを名前でまとめて終了させない（ユーザーが開いているゲームも閉じる）。自分が起動したビルドだけを閉じる
- `flat.sve` はユーザーが保存し直していることがある。見本を敷く場所が空いているかを確かめる（「Tile not empty」）
- スクリプトのファイルは heredoc ではなく Write・Edit で書く
