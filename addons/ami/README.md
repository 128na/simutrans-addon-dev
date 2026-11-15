# AMI（AI Marunage Infrastructure）

pak128 用のインフラアドオン集。絵は Blender のスクリプトで描く（作り方は [blender-poc](../blender-poc/README.md) で確かめたもの）。

**今は骨組みまで。** 描画から pak までを、在来線の通常の版（絵は blender-poc の線路と同じ仮の絵）で通した（[#14](https://github.com/128na/simutrans-addon-dev/issues/14)）。下の表の残りは作る予定のもの（開発ステップの一覧は [#27](https://github.com/128na/simutrans-addon-dev/issues/27)）。範囲と作りを決めた理由は次の ADR にある。

- [ADR 0002](../../docs/adr/0002-ami-scope.md): 範囲・対象・ライセンス・配布
- [ADR 0003](../../docs/adr/0003-ami-walls-base-piers-as-separate-objects.md): 壁・基盤・橋脚・歩道の分け方
- [ADR 0004](../../docs/adr/0004-shared-blender-tools.md): 描画の道具を `tools/` で共通にする
- [ADR 0005](../../docs/adr/0005-ami-render-tool-conventions.md): 部品のまとめ方・レイアウト検証用モード・設定値・並列

## 目的と中身

オブジェクト名はどれも `ami_` で始める。名前は次のとおり確定した（2026-11-15）。

| もの | 名前 |
|---|---|
| way（通常の版） | `ami_tram`・`ami_rail_ballast`・`ami_rail_slab`・`ami_road_local`・`ami_road_general`・`ami_road_expressway` |
| 基盤・高架の版 | `<way の名前>_base_<版>`・`<way の名前>_elev_<版>`（版は `single`・`back`・`center`・`front`） |
| 橋・トンネル | `<way の名前>_bridge`・`<way の名前>_tunnel` |
| 線路の壁 | `ami_wall_rail_<版>`（`single`・`back`・`front`）、架線つきは `ami_wall_rail_<版>_catenary`（`center` は架線だけ） |
| 道路の壁 | `ami_wall_road_<版>`（`single`・`back`・`front`） |
| 橋脚・歩道 | `ami_pier_rail`・`ami_pier_road`・`ami_sidewalk` |

dat のファイル名と pak に入る名前は同じ（`src/<名前>.dat`）。今あるのは `ami_rail_ballast` だけ。

### 線路（新描画位置）

| 種類 | 速度 | way | 版 |
|---|---|---|---|
| 路面軌道（tram、コンクリートで固めた線路） | 60 km/h | `ami_tram` | 通常だけ（壁・高架・橋・トンネルなし） |
| 在来線（バラスト軌道） | 160 km/h | `ami_rail_ballast` | 通常・基盤 4 版・高架 4 版・橋・トンネル |
| 高速線（スラブ軌道） | 480 km/h | `ami_rail_slab` | 同上 |

#### 見た目の手本（ユーザーから受け取った画像、2026-11-15）

画像は出典の権利が分からないので、リポジトリに入れず、形だけを書き起こす。

- **高速線（スラブ軌道）**: 下から順に次の層を重ねる。
  - コンクリート道床: 暗い灰色の幅の広い板。
  - てん充層: 道床の上の薄い層。
  - 軌道スラブ: 明るい灰色の板。長手の両端に、円柱の突起が道床から立ち、スラブの端の欠き込みに入る。
  - 締結装置: レールの下に、一定の間隔で並ぶ黒い小さな台。
  - レール: 赤茶色。
- **路面軌道**: 道路のあいだに、縁石と柵で分けた専用の軌道。
  - 床はコンクリートで固めてあり、レールの頭だけが床の面に出る。
  - レールの内側と周りに、さび色の汚れの帯がある。
  - 軌道の縁は明るい色の帯で、道路の白線とは別。
  - 写真では、架線の柱が 2 本の線路のあいだに立つ（架線は範囲外。tram は道路の上に重ねて敷く）。

### 道路

| 種類 | 速度 | 中央線 | way | 版 |
|---|---|---|---|---|
| 生活道路 | 40 km/h | なし | `ami_road_local` | 通常・高架 4 版・橋・トンネル |
| 一般道路 | 120 km/h | 白線 | `ami_road_general` | 同上 |
| 高速道路 | 360 km/h | 破線 | `ami_road_expressway` | 同上 |

- 断面はどれも blender-poc の高速道路と同じ（片側 1 車線、タイル全面が路面、歩道なし）
- 地上の道路に基盤の 4 版が要るか（路面がタイル全面なので、壁を路面の上に立てるだけで足りるか）は、最初の実装で確かめて決める

### 版の並び

- 4 版は `single`（両側に壁）・`back`（奥だけ）・`center`（なし）・`front`（手前だけ）。iss・SIS と同じ並べ方
- 基盤の版: 基盤が壁の位置で止まる。同じ版の壁の way-object と組で使う（`center` は way-object なし）
- 高架の版: 床と床の下の躯体だけ。橋脚は描かない
- 橋: 欄干を描かない。壁の way-object を重ねる
- 分岐の絵（OTRP の switch 画像、1・2 の 10 枚）は全部の way に入れる。近い斜めは壁の無い way に入れる
- 雪の絵と汚れ（blender-poc の 6 章）は全部の way に入れる

### 付属（別の pak にして同梱）

| もの | 作り | 名前（仮） |
|---|---|---|
| 線路の壁と架線 | way-object。架線つき（電化）の `single`・`back`・`center`（架線だけ）・`front` と、壁だけの `single`・`back`・`front` | `ami_wall_rail_*`・`ami_wall_rail_*_catenary` |
| 道路の壁 | way-object。`single`・`back`・`front` | `ami_wall_road_*` |
| 橋脚 | 高架の真下の地面に敷く、別の waytype の way。線路用と道路用 | `ami_pier_rail`・`ami_pier_road` |
| 歩道 | 道路の隣のタイルに敷く、別の waytype の way | `ami_sidewalk` |

橋脚と歩道の waytype は、それぞれを作るステップ（#18・#24）で決める（iss は橋脚が `tram_track`、歩道が `water`）。

### 後で足すもの

- 旧描画位置（SIS に合う）の線路。新描画位置で全部を作り終えてから、まとめて作る（別の PR でよい）

### 範囲に入れないもの

- 建物（blender-poc の料金所 `bpoc_tollbooth` は移さない）

## 対象

- Simutrans 本家 125.0.1 と OTRP（pak128）。OTRP だけの絵（分岐の絵・近い斜め）は本家では使われないだけ
- 画像は 256px セル（`pak256` で切り出し、ゲームは pak128）

## ライセンス

CC BY 4.0。

## 必要なもの

- Blender 4.5 LTS
- makeobj（`PATH` にある）

## ビルド

アドオンのディレクトリ（`addons/ami/`）で、描画の道具は `tools/` にある（[tools/README.md](../../tools/README.md)）。

```powershell
D:inlenderlender.exe -b --factory-startup --python blender/render.py   # シートを src/ へ（対象を絞るなら末尾に -- ami_rail_ballast）
python -X utf8 blender/ami_dat.py                                              # dat を src/ へ
python -X utf8 build.py                                                        # makeobj で dist/ へ
```

- `build.py` は、全部入りのまとめ `dist/ami.pak` と、種類別の `ami_rail.pak`（線路）・`ami_tram.pak`（路面軌道）・`ami_road.pak`（道路）・`ami_extra.pak`（付属）を作る。dat が無い種類は作らない。makeobj の出力に警告かエラーがあれば止まる
- シートを複数描くときは `python -X utf8 ..\..	oolslenderender_parallel.py <対象>...`。レイアウト検証用モードは `SHEET_LAYOUT=1`（`work/layout/` に書く）
- `src/`（dat とシート）はコミットする。`dist/` と `work/` はコミットしない
- 設定は `blender/render.py`（描き分け・シート名）、`blender/ami_dat.py`（dat と値）、`blender/addon_config.py`（判定の道具が読む対応表）

## 導入と検証

ゲームでの確認は blender-poc と同じく、アドオンを確かめるゲームの OTRP 版で `flat_512.sve` を開き、MCP のスクリプトを流す。
makeobj は本家と同じもの（60.12）なので、本家での確認はしない。

```bash
GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe bash ingame/sample_check.sh
```

- `dist/ami.pak` をゲームの `addons/pak128/` に写し、OTRP を MCP つきで起動して `ingame/sample.nut` を流す。見本は温暖側 (20,20) と降雪側 (276,20) に敷く。絵を作った way は `sample.nut` の `WAYS` に足す
- 保存・ロードやダイアログの見た目はスクリプトで確かめられないので、ユーザーが見る

塗りを実装する前に、レイアウト検証用モード（部品ごとに画像で見分けやすい単色で塗る）で、部品の配置とタイルどうしの接合を確かめる（[ADR 0005](../../docs/adr/0005-ami-render-tool-conventions.md)）。

## 今の決まりごと

- 値は次のとおり決めた（2026-11-15）。費用・維持費は pak128 の way と同じ単位（1/100 cr）で、iss の線路（15000・300）を基準にした。`blender/ami_dat.py` の `VALUES` と同じにする

| 種類 | 速度 | 費用 | 維持費 | 登場年 |
|---|---|---|---|---|
| 路面軌道 | 60 km/h | 10000 | 200 | 1900 |
| 在来線 | 160 km/h | 15000 | 300 | 1900 |
| 高速線 | 480 km/h | 40000 | 800 | 2000 |
| 生活道路 | 40 km/h | 5000 | 100 | 1900 |
| 一般道路 | 120 km/h | 8000 | 200 | 1930 |
| 高速道路 | 360 km/h | 20000 | 500 | 1990 |

## 残っていること

- 路面軌道を tram（道路に重ねる）にすると、写真のような縁石と柵で分けた専用の軌道には見えない。どちらに寄せるかは、路面軌道を作るステップ（#23）で絵を見て決める
- できたと言う条件は [ACCEPTANCE.md](ACCEPTANCE.md)
