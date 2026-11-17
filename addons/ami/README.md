# AMI（AI Marunage Infrastructure）

pak128 用のインフラアドオン集。絵は Blender のスクリプトで描く（作り方は [blender-poc](../blender-poc/README.md) で確かめたもの）。

**今あるのは在来線の通常の版（`ami_rail_ballast`）と、在来線の基盤の 4 版・壁だけの way-object（`ami_rail_ballast_base_*`・`ami_wall_rail_*`）。** 描画から pak までの骨組み（[#14](https://github.com/128na/simutrans-addon-dev/issues/14)）の上に、在来線の壁の無い通常の版を仕上げ（[#15](https://github.com/128na/simutrans-addon-dev/issues/15)。全方位・分岐の絵・近い斜め・雪・汚れ）、基盤の版と壁を足した（[#16](https://github.com/128na/simutrans-addon-dev/issues/16)。下の「壁の敷き方」）。下の表の残りは作る予定のもの（開発ステップの一覧は [#27](https://github.com/128na/simutrans-addon-dev/issues/27)）。範囲と作りを決めた理由は次の ADR にある。

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
| 線路の壁 | `ami_wall_rail_<版>`（`single`・`back`・`center`・`front`。`center` は行き止まりの端の壁だけ）、架線つきは `ami_wall_rail_<版>_catenary`（`center` は架線だけ）。近い斜めの分け合うタイル用に `ami_wall_rail_close`（仮。下の「壁の敷き方」） |
| 道路の壁 | `ami_wall_road_<版>`（`single`・`back`・`front`） |
| 橋脚・歩道 | `ami_pier_rail`・`ami_pier_road`・`ami_sidewalk` |

dat のファイル名と pak に入る名前は同じ（`src/<名前>.dat`）。今あるのは `ami_rail_ballast`・`ami_rail_ballast_base_<版>`（4 版）・`ami_wall_rail_<版>`（4 版）・`ami_wall_rail_close`。

### 線路（新描画位置）

| 種類 | 速度 | way | 版 |
|---|---|---|---|
| 路面軌道（tram、コンクリートで固めた線路） | 60 km/h | `ami_tram` | 通常だけ（壁・高架・橋・トンネルなし） |
| 在来線（バラスト軌道） | 160 km/h | `ami_rail_ballast` | 通常・基盤 4 版・高架 4 版・橋・トンネル |
| 高速線（スラブ軌道） | 480 km/h | `ami_rail_slab` | 同上 |

#### 在来線の手本（blender-poc の線路）

在来線（バラスト軌道）の手本は、[blender-poc](../blender-poc/README.md) の線路（新描画位置の `bpoc_track`）と、カーブ・分岐の作りは pak128 標準の線路（`Rail_100` など）。
道床・まくらぎ・レールの寸法、基準面の下げ幅、持ち分、汚れ・雪は POC の線路を写した。POC で合わせた直線・斜め・坂の位置（手本とのつなぎ目）は測り直していない。

AMI として変えた点（2026-11-17。後半はユーザーの見た目の指摘から）:

- 名前・値: `ami_rail_ballast`、160 km/h（値は下の「今の決まりごと」）。アイコンの数字も 160
- 道床の色: POC は一色の灰色だった。夏の絵では、2 色のまだらにして砕石の粒に見せた（`blender/render.py` の `BALLAST_STONE_*`・`BALLAST_GRAIN`）。平均の色は POC と同じにした（汚れの帯の色が道床の色から混ぜてあり、坂の測り方がレールを赤みで探すため）。雪の絵は POC と同じ
- カーブ: pak128 標準の線路と同じく、曲線ではなく斜めの絵で表す（dat の `image[sw]` などが `diagonal` と同じセルを指す。シートのカーブのセルは描かない）。T字・十字と分岐の絵（switch 画像 1・2）も、カーブの代わりに同じ 2 辺をつなぐ斜めの直線にした。斜めの部分は斜めのタイルと同じ幅・下げ幅で作り、直線と斜めの道床の間のすき間は道床の上面の凸包で埋める（`tools/blender/sheetlib` の `diag_curves`）
- 行き止まり: レールを POC（タイルの中心まで）より延ばし、閉じた側のタイルの端からタイル 1 辺の 1/4 の所を終点にした（`blender/render.py` の `END_FROM_EDGE`）。道床は終点より奥、タイルの端まで敷く。レールの末端に車止めを置く（下の「車止めの手本」）
- 行き止まりのまくらぎが直線より白く見えた: レールの間の油の帯を 2 本に分けて作っていて、中心で辺を分け合う形が、行き止まりのタイルでは切り抜きで消えていた（油の帯が無いぶん白く見えた）。油の帯を中心をまたぐ 1 本にした。blender-poc の線路にも同じ欠けがある（POC のシートは変えないので直していない）

#### 車止めの手本（ユーザーから受け取った画像、2026-11-17）

画像は出典の権利が分からないので、リポジトリに入れず、形だけを書き起こす（鉄道模型の車止めの写真）。

- 全体は黒。線路の終端に置く
- 線路を横切る低い台座が、レールの上と両側に渡る
- 両側のレールの外から奥へ、斜めの脚が 2 本立ち上がり、上で小さな箱（受け）につながる。レールの間に、細い緩衝板が 1 枚立つ
- 受けの奥の中央に四角い柱が 1 本立ち、上に箱形の標識灯（白〜橙に光る面、十字の模様）が付く
- 道床（灰色の砕石）は車止めのさらに奥まで続き、タイルの端で終わる

絵では、台座・斜めの脚 2 本・受けの箱・緩衝板・柱・標識灯の箱に単純にした（`tools/blender/sheetlib/track_parts.py` の `BUFFER_*`、部品のまとまり `buffer`）。灯の面は夜に光る特殊色（`light_white`）。十字の模様は大きさが数 px なので描いていない。

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
- 基盤の版: 基盤が壁の位置で止まる。同じ版の壁の way-object と組で使う（`center` の way-object は行き止まりの端の壁だけ）
- 高架の版: 床と床の下の躯体だけ。橋脚は描かない
- 橋: 欄干を描かない。壁の way-object を重ねる
- 分岐の絵（OTRP の switch 画像、1・2 の 10 枚）は全部の way に入れる。近い斜めは壁の無い way に入れる
- 雪の絵と汚れ（blender-poc の 6 章）は全部の way に入れる

### 壁の敷き方（在来線、#16）

基盤の版の way（`ami_rail_ballast_base_<版>`）を敷き、同じ経路に同じ版の壁の way-object（`ami_wall_rail_<版>`）を重ねる。`center` の壁の way-object（`ami_wall_rail_center`）は側壁が無く、行き止まりの端の壁だけを持つ（ユーザーの指摘、2026-11-17。架線つきの版では `center` も架線の部品を持つので、壁の way-object も 4 版にそろえた）。

- 絵の作り: 基盤の版の way は、通常の版の道床の下に基盤を敷き、壁のある側は壁の位置で、壁の無い側はタイルの端で止める。壁は way の絵に描かず、壁の way-object のシートに描く（`blender/render.py` の `BASE_VARIANTS`、`tools/blender/sheetlib` の `wall_sheet`）。壁のシートは上 4 行が奥（`backimage` など、車両より先に描く）、下 4 行が手前（`frontimage` など、車両より後に描く）。カメラに近い壁が手前の絵になる
- 行き止まり: 側壁を閉じた側のタイルの端まで延ばし、端の壁をタイルの端に立てる（ユーザーの指摘、2026-11-17）。レールの終点と車止めは通常の版と同じ（`END_FROM_EDGE`）。`center` も端の壁はある
- カーブ: 通常の版と同じく斜めの絵で表す。ただし基盤の版は、カーブのセルを斜めのタイルと別に描き、基盤の壁の無い側を削らない（複線の直角の曲がりで、内側の線の外側に草が三角に出たため。`curve_cells`）
- 継ぎ目（ユーザーの指摘、2026-11-17）: 坂の壁は、上がった側の端の最後の 1 列が欠けて、坂の上の十字・T字の壁との間に 1px のすき間が出た。坂のセルだけ、壁をタイルの外へ長めに残し、持ち分を左右へ 1 列広げた。T字・十字では、斜めの部分の通り道が反対側の壁（直線の側の壁）の端まで削り、隣の直線との継ぎ目に 1px の縦線が出た。斜めの部分の通り道は、その部分がある側の壁だけを削り、斜めの部分の壁はタイルの辺で切る（`tools/blender/sheetlib` の `assemble`）
- 奥と手前の決め方（POC の C5）: 版の「奥」「手前」は、南北の線なら西が奥・東が手前、東西の線なら北が奥・南が手前。カーブ・T字・十字のタイルは南北の線（T字は通り抜ける線）の版に合わせる。複線の輪では、角のタイルを南北の辺と同じ版で敷く（`sample.nut` の区画 W1）。斜めのタイルでは、奥の版は `nw`・`sw` の壁がタイルの角の側、`ne`・`se` の壁が中心の側に立つ（手前の版はその逆）
- 近い斜め（POC の C2）: 1 タイルに way-object は waytype ごとに 1 つなので、分け合うタイル（way が 2 本）には `back` と `front` を両方は置けない。分け合うタイルには、`back`・`front` を敷いた後に `ami_wall_rail_close` を 1 タイルずつ重ねる。OTRP は分け合うタイルの way-object 1 つで 2 本の線を、それぞれの斜めの絵で描く（`../simutrans` の `obj/wayobj.cc` の `two_legs`）。`ami_wall_rail_close` は `nw`・`sw` の線に `back` の壁、`ne`・`se` の線に `front` の壁の絵を使うので、近い斜めの複線は西の線（x の小さい方）を `back`、東の線を `front` にする。速さの値を `back`・`front` より 1 大きくしてあり、後から重ねると置き換わる（同じ速さの way-object を重ねても、前の版のまま向きだけ足される。`obj/wayobj.cc` の `extend_wayobj`）。置き換えると、隣のタイルの壁が分け合うタイルの側へつながらなくなる（前の way-object が消えるときに隣の向きを外し、新しい方はつなぎ直さない。`~wayobj_t`）。`close` を置いた後に、`back`・`front` を同じ経路にもう一度敷く（`close` の方が速いので、分け合うタイルは `close` のまま）
- 値（仮）: 壁の way-object は費用 3000・維持費 60・登場 1900、速さ 1000（`blender/ami_dat.py` の `WALL_VALUES`）。架線ではない（`own_waytype=track`）ので、速さの値は列車の速さを縛らない
- 確かめたゲーム: `OTRPv64_3.exe`（2026-11-17）。分け合うタイルの 2 本の線の描き分けは OTRP の機能で、本家での近い斜めの壁の見え方は確かめていない

### 付属（別の pak にして同梱）

| もの | 作り | 名前（仮） |
|---|---|---|
| 線路の壁と架線 | way-object。架線つき（電化）の `single`・`back`・`center`（架線だけ）・`front` と、壁だけの `single`・`back`・`center`（行き止まりの端の壁だけ）・`front` | `ami_wall_rail_*`・`ami_wall_rail_*_catenary` |
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
D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py   # シートを src/ へ（対象を絞るなら末尾に -- ami_rail_ballast）
python -X utf8 blender/ami_dat.py                                              # dat を src/ へ
python -X utf8 build.py                                                        # makeobj で dist/ へ
```

- `build.py` は、全部入りのまとめ `dist/ami.pak` と、種類別の `ami_rail.pak`（線路）・`ami_tram.pak`（路面軌道）・`ami_road.pak`（道路）・`ami_extra.pak`（付属）を作る。dat が無い種類は作らない。makeobj の出力に警告かエラーがあれば止まる
- シートを複数描くときは `python -X utf8 ..\..\tools\blender\render_parallel.py <対象>...`。レイアウト検証用モードは `SHEET_LAYOUT=1`（`work/layout/` に書く）
- レイアウト検証用モードの pak は `SHEET_LAYOUT=1` で描いた後、`SHEET_LAYOUT=1 python -X utf8 build.py`（`work/layout/dist/` に作る）
- 同じシートの通常の描画とレイアウト検証用の描画を同時に動かさない。セルごとの生の絵（`work/<シート>_<セル>.png`）の名前が同じで、互いのセルを取り込んだシートができた（2026-11-17）
- `src/`（dat とシート）はコミットする。`dist/` と `work/` はコミットしない
- 設定は `blender/render.py`（描き分け・シート名）、`blender/ami_dat.py`（dat と値）、`blender/addon_config.py`（判定の道具が読む対応表）

## 導入と検証

ゲームでの確認は blender-poc と同じく、アドオンを確かめるゲームの OTRP 版で `flat_512.sve` を開き、MCP のスクリプトを流す。
makeobj は本家と同じもの（60.12）なので、本家での確認はしない。

```bash
GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe bash ingame/sample_check.sh
```

- `dist/ami.pak` をゲームの `addons/pak128/` に写し、OTRP を MCP つきで起動して `ingame/sample.nut` を流す。見本は温暖側 (20,20) と降雪側 (276,20) に敷く。絵を作った way は `sample.nut` の `WAYS` に足す
- 見本は way の全部の絵を、周りとつながった形で出す（行き止まり・1 タイル・斜め・輪と十字・坂・急坂・近い斜め・十字の分岐の固定・分岐の自動選択 8 通り。区画の表は `sample.nut` の冒頭）。降雪側は敷いた後に一帯を降雪に塗り直す
- 返り値の `[check]` の行に、近い斜めの分け合うタイルが way 1 本か（`two_ways=false` なら近い斜めの絵が使われている）と、分岐の絵を固定する道具があるかを出す
- 基盤の版は `WALLED` に way と壁の組で足す（同じ区画の並びで、壁を同じ経路に重ねる。近い斜めの区画 G は敷かない）。複線と壁の組（輪・近い斜め・行き止まりの並び）は区画 W。`[check]` の行に、区画 W の角と分け合うタイルの way と壁の名前を出す（`(2)` は way が 2 本）
- 撮るのは `bash ingame/sample_capture.sh`（`work/sample/` に温暖側・降雪側の区画ごと）。レイアウト検証用モードの pak は `PAK=work/layout/dist/ami.pak` で入れ、`OUT=work/sample_layout` で撮る。終わったら `dist/ami.pak` を入れ直す
- 同じポートでゲームが動いていると、`sample_check.sh` は止まる（他のゲームに見本を流さない）。閉じるのは自分で起動したゲームだけ
- 確認画像は `docs/`。在来線の通常の版は `rail_ballast_*.png`（温暖側・降雪側の見本、レイアウト検証用モードの見本、行き止まりの拡大、T字・十字・分岐のセル、道床の色の前後。2026-11-17）。基盤の版と壁は `rail_base_*.png`（区画 W1〜W3 と、back・front の輪と十字。`layout` はレイアウト検証用モード。`fix_*` は継ぎ目を直した前後の拡大（`_before` が前）。2026-11-17）
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

- 壁（#16）: 壁の way-object の値（費用・維持費・登場年）は仮。`ami_wall_rail_close` の名前も仮で、確定が要る。線路の上を走る編成と壁の重なり（ACCEPTANCE の 2-3）はユーザーの確認待ち。架線つきの版（2-6）、高架・橋への重ね（2-1）、道路の壁は後のステップ
- 近い斜めの壁は、西の線を `back`、東の線を `front` にした組だけ絵が合う。逆の組（西が `front`）の分け合うタイル用の way-object は作っていない
- 路面軌道（#23）のカーブは今の曲線のままでよい（ユーザーの指摘、2026-11-17）。斜めの絵にするのは在来線（と、作るときに決める高速線）
- 路面軌道を tram（道路に重ねる）にすると、写真のような縁石と柵で分けた専用の軌道には見えない。どちらに寄せるかは、路面軌道を作るステップ（#23）で絵を見て決める
- できたと言う条件は [ACCEPTANCE.md](ACCEPTANCE.md)
