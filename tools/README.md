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
| `tools/blender/` のそのほか | 判定・比較・確認の道具（`profile_sheet`（描画の時間の内訳を測る）・`compose`・`ingame_diff`・`seam_judge`・`slope_measure`・`sheet_diff`・`special`・`special_preview`・`zoom`・`hcat`・`ref_measure`・`check`）と並列描画（`render_parallel`） |
| `addons/<アドオン>/blender/render.py` | アドオンのシートの入口。`sys.path` に `tools/blender` を足して `sheetlib` を import し、描き分け（`R.TRACK_PROFILES`・`R.ROAD_PROFILES` への登録）と、対象名 → 描く関数の対応（`SHEETS`）を決めて `R.run_targets(SHEETS, 既定の対象)` を呼ぶ |
| `addons/<アドオン>/blender/addon_config.py` | 判定・比較の道具が読む設定。`PREFIX`（ゲームのタイル一覧でこのアドオンの道を見分ける名前の接頭辞）・`SHEETS`（道の名前 → シート名）・`DIAG_CURVE_SHEETS`（カーブに斜めの絵を使うシート） |
| `addons/<アドオン>/blender/` のそのほか | アドオンの dat の書き出し（`track_dat.py` など）・アドオン固有の確認（`preview.py`・`icons_only.py`）。dat の中身はアドオンの値なので共通には置かない |
| `addons/<アドオン>/ingame/` | ゲームで見本を敷くスクリプト。アドオンの名前（`bpoc_*` など）を使うのでアドオンに置く |

- `sheetlib` の `TRACK_PROFILES`・`ROAD_PROFILES` は、入口が登録する。共通の描画が名前で引くのは `TRACK_PROFILES["new"]`（トンネル）と `ROAD_PROFILES["street"]`・`["expressway"]`（道路の部品の選択）。アドオンはこの名前で登録する
- アドオンのディレクトリは、道具が `os.getcwd()` で決める。アドオンの外では動かさない
- 入口が `tools/blender` を探す相対パスは、`addons/<アドオン>/blender/` から見た `../../../tools/blender`

## 描画が遅いとき

全 28 枚（blender-poc）を 16 並列で描いて約 5 分。時間のほとんどは Boolean（Exact ソルバー）の演算で、描画と後処理は 1 割に満たない（[記録](../docs/records/2026-11-17_sheet-render-speed.md)）。

- Boolean は `sheetlib/core.py` の `boolean()`・`clip_to_tile()`（中で `_apply_modifier`）を通す。`bpy.ops.object.modifier_apply` を直接呼ぶと、呼ぶたびにシーン全体の更新が走って 2 倍近く遅くなる
- `boolean()` の `use_self = True` は外さない。分岐・十字で重なり合う切り抜きの形が正しく抜けず、絵が大きく変わる（速くはなる。2026-11-17 に確認）
- 時間は、削る側の形の面数で決まる。新しい分岐の形（通り道）を足して遅くなったら、`profile_sheet.py` で測る（アドオンのディレクトリで `SHEET_ONLY=ns,diag_nw,up12 blender -b --factory-startup --python ../../tools/blender/profile_sheet.py -- 対象名`。内訳は `work/profile_<対象>.txt`）
- 並列数は 16 が最速だった（12・24・28 は遅い）。PC を替えたときだけ `SHEET_JOBS` を測り直す
- 絵を変えない改善は、描き直したシートが前と全画素同じ（`git status` の `src/` の差分なし）であることで確かめる

## レイアウト検証用モード

塗り（材質・汚れ・雪）を見る前に、部品の配置・組み合わせ・タイルどうしの接合を確かめるためのモード（[ADR 0005](../docs/adr/0005-ami-render-tool-conventions.md)）。

```powershell
cd addons\blender-poc
$env:SHEET_LAYOUT = "1"; D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py -- track_wall_single
```

- 部品ごとに単色で、光の当たり方に関わらず一様に塗る。色の割り当ては `sheetlib/layout_colors.py`。部品を足したらそこにも足す（無いと `[layout] 色が未登録の部品` と出て、名前から決めた色で描く）
- シートと dat は `work/layout/` に書く。`src/` は変えない
- 通常の出力は変わらない（モードを付けたときだけ働く）
