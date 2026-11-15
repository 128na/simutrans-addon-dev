# tools

複数のアドオンが使う道具。今は Blender でシートを描く道具と、描いた絵・ゲームの画面を測る道具が `blender/` にある（[ADR 0004](../docs/adr/0004-shared-blender-tools.md)）。

使うアドオン: [blender-poc](../addons/blender-poc/README.md)。AMI も使う（[ADR 0005](../docs/adr/0005-ami-render-tool-conventions.md)）。

## 使い方

道具は、**アドオンのディレクトリで**動かす（出力と読み込みは、そのアドオンの `src/`・`work/` 以下）。

```powershell
cd addons\blender-poc
D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py -- track      # アドオンの入口
python -X utf8 ..\..\tools\blender\render_parallel.py --jobs 8 track track_old          # 入口の対象を別プロセスで並列に
D:\bin\blender\blender.exe -b --factory-startup --python ..\..\tools\blender\compose.py -- road work\compose_road.png
```

## 共通とアドオンの設定の分け方

| どこ | 置くもの |
|---|---|
| `tools/blender/sheetlib.py` | 描画の共通部分。カメラ・基準面（`Datum`）・部品（`Part`）・組み立て（`assemble`）・材質・線路と道路の形・壁・高架・橋・トンネル・セルの描画・シート化・アイコン・特殊色。シート名や部品の組み合わせは持たない |
| `tools/blender/` のそのほか | 判定・比較・確認の道具（`compose`・`ingame_diff`・`seam_judge`・`slope_measure`・`sheet_diff`・`special`・`special_preview`・`zoom`・`hcat`・`ref_measure`・`check`）と並列描画（`render_parallel`） |
| `addons/<アドオン>/blender/render.py` | アドオンのシートの入口。`sys.path` に `tools/blender` を足して `sheetlib` を import し、描き分け（`R.TRACK_PROFILES`・`R.ROAD_PROFILES` への登録）と、対象名 → 描く関数の対応（`SHEETS`）を決めて `R.run_targets(SHEETS, 既定の対象)` を呼ぶ |
| `addons/<アドオン>/blender/addon_config.py` | 判定・比較の道具が読む設定。`PREFIX`（ゲームのタイル一覧でこのアドオンの道を見分ける名前の接頭辞）・`SHEETS`（道の名前 → シート名）・`DIAG_CURVE_SHEETS`（カーブに斜めの絵を使うシート） |
| `addons/<アドオン>/blender/` のそのほか | アドオンの dat の書き出し（`track_dat.py` など）・アドオン固有の確認（`preview.py`・`icons_only.py`）。dat の中身はアドオンの値なので共通には置かない |
| `addons/<アドオン>/ingame/` | ゲームで見本を敷くスクリプト。アドオンの名前（`bpoc_*` など）を使うのでアドオンに置く |

- `sheetlib.py` の `TRACK_PROFILES`・`ROAD_PROFILES` は、入口が登録する。共通の描画が名前で引くのは `TRACK_PROFILES["new"]`（トンネル）と `ROAD_PROFILES["street"]`・`["expressway"]`（道路の部品の選択）。アドオンはこの名前で登録する
- アドオンのディレクトリは、道具が `os.getcwd()` で決める。アドオンの外では動かさない
- 入口が `tools/blender` を探す相対パスは、`addons/<アドオン>/blender/` から見た `../../../tools/blender`
