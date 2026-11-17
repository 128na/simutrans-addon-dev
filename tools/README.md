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
| `tools/blender/sheetlib/` | 描画の共通部分（パッケージ）。部品をそれが表す物ごとに分けてある: `core`（設定値・シーン・材質・形の部品・基準面 `Datum` と部品 `Part` の型）、`track_parts`（線路: 道床・まくらぎ・レール・車止め・汚れ）、`wall_parts`（壁・基盤・橋・高架の橋脚。線路と道路で共通）、`road_parts`（道路: 路面・縁石・歩道・白線・車線・汚れ・雪）、`assemble`（部品を経路ごとに組み立てる）、`cells`（セルの描画・特殊色・シート化）、`sheetlib`（線路・道路・トンネル・アイコンのシートと `run_targets`）。シート名や、部品をどの版に使うかは持たない |
| `tools/blender/sheet_settings.py` | 設定値: 並列数（`JOBS`、環境変数 `SHEET_JOBS`）・Blender の場所（`SHEET_BLENDER`）・モード（`SHEET_LAYOUT`・`SHEET_ONLY`）。Blender を使わないので `render_parallel.py` も読む |
| `tools/blender/` のそのほか | 判定・比較・確認の道具（`compose`・`ingame_diff`・`seam_judge`・`slope_measure`・`sheet_diff`・`special`・`special_preview`・`zoom`・`hcat`・`ref_measure`・`check`）と並列描画（`render_parallel`） |
| `addons/<アドオン>/blender/render.py` | アドオンのシートの入口。`sys.path` に `tools/blender` を足して `sheetlib` を import し、描き分け（`R.TRACK_PROFILES`・`R.ROAD_PROFILES` への登録）と、対象名 → 描く関数の対応（`SHEETS`）を決めて `R.run_targets(SHEETS, 既定の対象)` を呼ぶ |
| `addons/<アドオン>/blender/addon_config.py` | 判定・比較の道具が読む設定。`PREFIX`（ゲームのタイル一覧でこのアドオンの道を見分ける名前の接頭辞）・`SHEETS`（道の名前 → シート名）・`DIAG_CURVE_SHEETS`（カーブに斜めの絵を使うシート） |
| `addons/<アドオン>/blender/` のそのほか | アドオンの dat の書き出し（`track_dat.py` など）・アドオン固有の確認（`preview.py`・`icons_only.py`）。dat の中身はアドオンの値なので共通には置かない |
| `addons/<アドオン>/ingame/` | ゲームで見本を敷くスクリプト。アドオンの名前（`bpoc_*` など）を使うのでアドオンに置く |

- `sheetlib` の `TRACK_PROFILES`・`ROAD_PROFILES` は、入口が登録する。共通の描画が名前で引くのは `TRACK_PROFILES["new"]`（トンネル）と `ROAD_PROFILES["street"]`・`["expressway"]`（道路の部品の選択）。アドオンはこの名前で登録する
- 線路の描き分けのうち、壁を way-object に分けるためのキー（AMI の基盤の版。#16）:
  - `wall_sheet`: 壁を way の絵に描かず、このシート名の壁の way-object のシートに描く。上 4 行が奥、下 4 行（`WALL_FRONT_ROW` から）が手前の絵。`diag_curves` と一緒に使える（斜めの部品は `assemble` の `path_opts` で、直線と斜めの部品を 1 回でまとめて切り分ける）
  - `curve_cells`: `diag_curves` でも、カーブのセルを斜めの形で別に描く（斜めのタイルの切り抜き `_diag_open_cut` をかけない）
  - `wall_sheet` の坂のセルは、壁をタイルの外へ `SLOPE_WALL_PAD` だけ残し、壁の持ち分を左右へ 1 列広げる（坂の上の平らなタイルの壁との 1px のすき間を埋める）。`path_opts` の組み立てでは、ほかの経路の通り道で壁を削るのは、その経路が壁の側にあるときだけにし、斜めの部分の壁はタイルの辺で切る
- アドオンのディレクトリは、道具が `os.getcwd()` で決める。アドオンの外では動かさない
- 入口が `tools/blender` を探す相対パスは、`addons/<アドオン>/blender/` から見た `../../../tools/blender`

## レイアウト検証用モード

塗り（材質・汚れ・雪）を見る前に、部品の配置・組み合わせ・タイルどうしの接合を確かめるためのモード（[ADR 0005](../docs/adr/0005-ami-render-tool-conventions.md)）。

```powershell
cd addons\blender-poc
$env:SHEET_LAYOUT = "1"; D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py -- track_wall_single
```

- 部品ごとに単色で、光の当たり方に関わらず一様に塗る。色の割り当ては `sheetlib/layout_colors.py`。部品を足したらそこにも足す（無いと `[layout] 色が未登録の部品` と出て、名前から決めた色で描く）
- シートと dat は `work/layout/` に書く。`src/` は変えない
- 通常の出力は変わらない（モードを付けたときだけ働く）
