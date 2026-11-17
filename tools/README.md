# tools

複数のアドオンが使う道具。今は Blender でシートを描く道具と、描いた絵・ゲームの画面を測る道具が `blender/` にある（[ADR 0004](../docs/adr/0004-shared-blender-tools.md)）。

使うアドオン: [blender-poc](../addons/blender-poc/README.md)。AMI も使う（[ADR 0005](../docs/adr/0005-ami-render-tool-conventions.md)）。

## 使い方

道具は、**アドオンのディレクトリで**動かす（出力と読み込みは、そのアドオンの `src/`・`work/` 以下）。

```powershell
cd addons\blender-poc
D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py -- track      # アドオンの入口
python -X utf8 ..\..\tools\blender\render_parallel.py --jobs 16 track track_old          # 入口の対象を別プロセスで並列に
D:\bin\blender\blender.exe -b --factory-startup --python ..\..\tools\blender\compose.py -- road work\compose_road.png
```

## 共通とアドオンの設定の分け方

| どこ | 置くもの |
|---|---|
| `tools/blender/sheetlib/` | 描画の共通部分（パッケージ）。部品をそれが表す物ごとに分けてある: `core`（設定値・シーン・材質・形の部品・基準面 `Datum` と部品 `Part` の型）、`track_parts`（線路: 道床・まくらぎ・レール・車止め・汚れ）、`wall_parts`（壁・基盤・橋・高架の橋脚。線路と道路で共通）、`catenary_parts`（架線: 柱・梁・吊り金具・トロリ線・ちょう架線）、`road_parts`（道路: 路面・縁石・歩道・白線・車線・汚れ・雪）、`assemble`（部品を経路ごとに組み立てる）、`cells`（セルの描画・特殊色・シート化）、`sheetlib`（線路・道路・トンネル・アイコンのシートと `run_targets`）。シート名や、部品をどの版に使うかは持たない |
| `tools/blender/sheet_settings.py` | 設定値: 並列数（`JOBS`、環境変数 `SHEET_JOBS`）・Blender の場所（`SHEET_BLENDER`）・モード（`SHEET_LAYOUT`・`SHEET_ONLY`）。Blender を使わないので `render_parallel.py` も読む |
| `tools/blender/` のそのほか | 判定・比較・確認の道具（`profile_sheet`（描画の時間の内訳を測る）・`compose`・`ingame_diff`・`seam_judge`・`slope_measure`・`sheet_diff`・`special`・`special_preview`・`zoom`・`hcat`・`ref_measure`・`check`）と並列描画（`render_parallel`） |
| `addons/<アドオン>/blender/render.py` | アドオンのシートの入口。`sys.path` に `tools/blender` を足して `sheetlib` を import し、描き分け（`R.TRACK_PROFILES`・`R.ROAD_PROFILES` への登録）と、対象名 → 描く関数の対応（`SHEETS`）を決めて `R.run_targets(SHEETS, 既定の対象)` を呼ぶ |
| `addons/<アドオン>/blender/addon_config.py` | 判定・比較の道具が読む設定。`PREFIX`（ゲームのタイル一覧でこのアドオンの道を見分ける名前の接頭辞）・`SHEETS`（道の名前 → シート名）・`DIAG_CURVE_SHEETS`（カーブに斜めの絵を使うシート） |
| `addons/<アドオン>/blender/` のそのほか | アドオンの dat の書き出し（`track_dat.py` など）・アドオン固有の確認（`preview.py`・`icons_only.py`）。dat の中身はアドオンの値なので共通には置かない |
| `addons/<アドオン>/ingame/` | ゲームで見本を敷くスクリプト。アドオンの名前（`bpoc_*` など）を使うのでアドオンに置く |

- `sheetlib` の `TRACK_PROFILES`・`ROAD_PROFILES` は、入口が登録する。共通の描画が名前で引くのは `TRACK_PROFILES["new"]`（トンネル）と `ROAD_PROFILES["street"]`・`["expressway"]`（道路の部品の選択）。アドオンはこの名前で登録する
- 線路の描き分けのうち、壁を way-object に分けるためのキー（AMI の基盤の版。#16）:
  - `wall_sheet`: 壁を way の絵に描かず、このシート名の壁の way-object のシートに描く。上 4 行が奥、下 4 行（`WALL_FRONT_ROW` から）が手前の絵。`diag_curves` と一緒に使える（斜めの部品は `assemble` の `path_opts` で、直線と斜めの部品を 1 回でまとめて切り分ける）
  - `curve_cells`: `diag_curves` でも、カーブのセルを斜めの形で別に描く（斜めのタイルの切り抜き `_diag_open_cut` をかけない）
  - `wall_sheet` の坂のセルは、壁をタイルの外へ `SLOPE_WALL_PAD` だけ残し、壁の持ち分を左右へ 1 列広げる（坂の上の平らなタイルの壁との 1px のすき間を埋める）。`path_opts` の組み立てでは、ほかの経路の通り道で壁を削るのは、その経路が壁の側にあるときだけにし、斜めの部分の壁はタイルの辺で切る
- 架線（AMI の架線つきの壁。#17）: 部品は `sheetlib/catenary_parts.py`（柱・梁・吊り金具・トロリ線・ちょう架線。名前は `cat_` で始まる）。`groups` に `catenary`（線）と `catenary_support`（柱・梁・吊り金具）を足した版が作る
  - `select_walls` は架線の部品を壁に数えない。柱は壁と同じ決め方で残すか消し（`center` は無し）、梁・トロリ線はいつも残す。`catenary_support` は経路が 1 本のセルだけに作る
  - 梁は `trim_catenary` で、残した側壁の外側を削る（壁の無い側はタイルの端まで延びて、隣の線の梁とつながる）
  - `Part.front` の部品（梁・吊り金具・トロリ線）は、位置に関わらず手前の絵（`frontimage`）に描く（`render_layers`）
  - 細い部品（`Part.thin`。架線のトロリ線・ちょう架線）: 1px ほどの線は、全部の画素が半透明になり、高さのある部品の層で半透明の画素を捨てる処理（不透明度 250 未満）で消える。`render_layers` は細い部品だけをもう 1 回描き、捨てた画素のうち不透明度 `THIN_ALPHA`（128）以上の所を不透明にして足す（細い部品のある層だけ、1 回多く描く）
  - それでも、線の中心が画素の境に来ると半透明の 2 列（2 行）に分かれて、太く見えるか消える。斜めの線は半画素ずらして画素の中心に乗せる（`CAT_DIAG_SHIFT`・`CAT_DIAG_SHIFT_Z`）。直線は傾き 2:1 なので、太さ（`CAT_WIRE_W`・`CAT_WIRE_H`）で 1 行に 2px ずつの階段になるようにした。上下 2 本の線は、間をちょうど 4px（`H / 4`）にして、画素への乗り方をそろえる（2026-11-18）
  - 高さのある部品の層は、架線を足した版と壁だけの版で、壁の画素が減らないことを確かめた（レイアウト検証用モードのシートで、壁だけの版の不透明な画素が透明になった所は 0。変わった画素は架線と重なる所か、架線と壁の境の混ざった色。2026-11-18）
  - 描き分けのキー: `rise`（高さのある部品の持ち分を上へ広げる行数。既定は壁の `WALL_RISE`。架線は `CAT_RISE`）、`wall_only`（way のシートを書かず、壁の way-object のシートだけを書く。`sheet` は作業ファイルの名前にだけ使うので、同じ way の別の対象と違う名前にする）、`wall_label`（壁の way-object のアイコンの文字。既定は `W`）
- アドオンのディレクトリは、道具が `os.getcwd()` で決める。アドオンの外では動かさない
- 入口が `tools/blender` を探す相対パスは、`addons/<アドオン>/blender/` から見た `../../../tools/blender`

## 描画が遅いとき

全 28 枚（blender-poc）を 16 並列で描いて約 2 分（117 秒）。時間のほとんどは Boolean（Exact ソルバー）の演算で、描画と後処理は 1 割に満たない（[記録](../docs/records/2026-11-17_sheet-render-speed.md)）。

- Boolean は `sheetlib/core.py` の `boolean()`・`clip_to_tile()`（中で `_apply_modifier`）を通す。`bpy.ops.object.modifier_apply` を直接呼ぶと、呼ぶたびにシーン全体の更新が走って 2 倍近く遅くなる
- `boolean()` の `use_self`（既定 True）は、削る形が自分自身と重なるときに要る。外すだけだと、分岐・十字で重なり合う帯が正しく抜けず絵が壊れる（2026-11-17 に確認）。重ならない形（帯 1 本）を 1 つずつ削るなら `use_self=False` でよく、同じ絵で速い（`assemble._place` の通り道の切り抜き）。道路の車道の型（`assemble._carve`）と壁の外側の切り抜き（`sheetlib.road_sheet` の `roadcut`）も 1 つずつ削る（絵は路面のざらつきが最大 5 ほど変わるだけ）。基盤の切り抜き（`build_base`）は `use_self` が要る（外すと絵が変わる）。新しく Boolean を足すときは、削る形が自己交差しないよう 1 つずつに分けられないかを先に考える
- 時間は、削る側の形の面数で決まる。新しい分岐の形（通り道）を足して遅くなったら、`profile_sheet.py` で測る（アドオンのディレクトリで `SHEET_ONLY=ns,diag_nw,up12 blender -b --factory-startup --python ../../tools/blender/profile_sheet.py -- 対象名`。内訳は `work/profile_<対象>.txt`）
- 並列数は 16 が最速だった（12・24・28 は遅い）。PC を替えたときだけ `SHEET_JOBS` を測り直す
- 絵を変えない改善は、描き直したシートが前と全画素同じ（`git status` の `src/` の差分なし）であることで確かめる。形（透明の範囲）が同じで色の差が数程度のノイズなら、差分図（`sheet_diff.py`）で見て許す

## レイアウト検証用モード

塗り（材質・汚れ・雪）を見る前に、部品の配置・組み合わせ・タイルどうしの接合を確かめるためのモード（[ADR 0005](../docs/adr/0005-ami-render-tool-conventions.md)）。

```powershell
cd addons\blender-poc
$env:SHEET_LAYOUT = "1"; D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py -- track_wall_single
```

- 部品ごとに単色で、光の当たり方に関わらず一様に塗る。色の割り当ては `sheetlib/layout_colors.py`。部品を足したらそこにも足す（無いと `[layout] 色が未登録の部品` と出て、名前から決めた色で描く）
- シートと dat は `work/layout/` に書く。`src/` は変えない
- 通常の出力は変わらない（モードを付けたときだけ働く）
