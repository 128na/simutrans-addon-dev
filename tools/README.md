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
| `tools/blender/sheetlib/` | 描画の共通部分（パッケージ）。部品をそれが表す物ごとに分けてある: `core`（設定値・シーン・材質・形の部品・基準面 `Datum` と部品 `Part` の型）、`track_parts`（線路: 道床・まくらぎ・レール・車止め・汚れ）、`wall_parts`（壁・基盤・橋・高架の橋脚。線路と道路で共通）、`catenary_parts`（架線: 柱・梁・吊り金具・トロリ線・ちょう架線・ハンガー）、`road_parts`（道路: 路面・縁石・歩道・白線・車線・汚れ・雪）、`assemble`（部品を経路ごとに組み立てる）、`cells`（セルの描画・特殊色・シート化）、`sheetlib`（線路・道路・トンネル・アイコンのシートと `run_targets`）。シート名や、部品をどの版に使うかは持たない |
| `tools/blender/sheet_settings.py` | 設定値: 並列数（`JOBS`、環境変数 `SHEET_JOBS`）・Blender の場所（`SHEET_BLENDER`）・モード（`SHEET_LAYOUT`・`SHEET_ONLY`）。Blender を使わないので `render_parallel.py` も読む |
| `tools/blender/` のそのほか | 判定・比較・確認の道具（`profile_sheet`（描画の時間の内訳を測る）・`compose`・`ingame_diff`・`seam_judge`・`slope_measure`・`sheet_diff`・`special`・`special_preview`・`zoom`・`hcat`・`ref_measure`・`check`）と並列描画（`render_parallel`） |
| `addons/<アドオン>/blender/render.py` | アドオンのシートの入口。`sys.path` に `tools/blender` を足して `sheetlib` を import し、描き分け（`R.TRACK_PROFILES`・`R.ROAD_PROFILES` への登録）と、対象名 → 描く関数の対応（`SHEETS`）を決めて `R.run_targets(SHEETS, 既定の対象)` を呼ぶ |
| `addons/<アドオン>/blender/addon_config.py` | 判定・比較の道具が読む設定。`PREFIX`（ゲームのタイル一覧でこのアドオンの道を見分ける名前の接頭辞）・`SHEETS`（道の名前 → シート名）・`DIAG_CURVE_SHEETS`（カーブに斜めの絵を使うシート） |
| `addons/<アドオン>/blender/` のそのほか | アドオンの dat の書き出し（`track_dat.py` など）・アドオン固有の確認（`preview.py`・`icons_only.py`）。dat の中身はアドオンの値なので共通には置かない |
| `addons/<アドオン>/ingame/` | ゲームで見本を敷くスクリプト。アドオンの名前（`bpoc_*` など）を使うのでアドオンに置く |

- `sheetlib` の `TRACK_PROFILES`・`ROAD_PROFILES` は、入口が登録する。共通の描画が名前で引くのは `TRACK_PROFILES["new"]`（トンネル）と `ROAD_PROFILES["street"]`・`["expressway"]`（道路の部品の選択）。アドオンはこの名前で登録する
- 線路の描き分けのうち、軌道の種類を増やすためのキー（#20 の前準備）。どれも無くてよく、無ければ今の線路と同じ絵になる。`replace`・`skin`・`groups` は今までどおり一緒に使える:
  - `track_parts`: 本体の部品（既定 `TRACK_PARTS`）を丸ごと置き換える。`track_sheet`・`tunnel_sheet`・線路のアイコンは `track_body_parts(prof)` で本体の部品を引く（アイコンには `replace` を当てない）
  - `parts`: 追加の部品。シートに描く部品は `track_sheet_parts(prof)` が決める（本体 + `parts` + `TRACK_EXTRAS` に `replace` を当てたもの）。アドオンの `R.TRACK_EXTRAS += ...` は `R` の名前を付け替えるだけで効かないので、このキーで渡す。足した部品の色は `sheetlib/layout_colors.py` に足す
  - `bed_fills`: 分岐（`diag_curves` の T字・十字）の直線と斜めの間のすき間を埋める層。`{部品の名前: (上面の半幅, 板の下面の高さ, 板の上面の高さ)}` で、書いた順に埋める（複数の層を埋められる）。斜めの部分の横幅の倍率は、その部品の `width` で決まる。無ければ `BED_FILLS`（`ballast` だけ。`ballast` が無い部品の組では何も埋めない）。指定した名前の部品が無いときは止まる
  - `snow_skin`: 雪の絵だけの材質の差し替え（部品の名前 → 材質）。`track_skin` の雪の結果に重ねる（`track_profile_skin`。夏の絵の `skin` と対）。`track_sheet` とトンネルの坑口の両方に効く
- 線路の描き分けのうち、壁を way-object に分けるためのキー（AMI の基盤の版。#16）:
  - `wall_sheet`: 壁を way の絵に描かず、このシート名の壁の way-object のシートに描く。上 4 行が奥、下 4 行（`WALL_FRONT_ROW` から）が手前の絵。`diag_curves` と一緒に使える（斜めの部品は `assemble` の `path_opts` で、直線と斜めの部品を 1 回でまとめて切り分ける）
  - `curve_cells`: `diag_curves` でも、カーブのセルを斜めの形で別に描く（斜めのタイルの切り抜き `_diag_open_cut` をかけない）
  - `wall_sheet` の坂のセルは、壁をタイルの外へ `SLOPE_WALL_PAD` だけ残し、壁の持ち分を左右へ 1 列広げる（坂の上の平らなタイルの壁との 1px のすき間を埋める）。`path_opts` の組み立てでは、ほかの経路の通り道で壁を削るのは、その経路が壁の側にあるときだけにし、斜めの部分の壁はタイルの辺で切る
- 架線（AMI の架線つきの壁。#17）: 部品は `sheetlib/catenary_parts.py`（柱・梁・吊り金具・トロリ線・ちょう架線・ハンガー。名前は `cat_` で始まる）。`groups` に `catenary`（線）と `catenary_support`（柱・梁・吊り金具）を足した版が作る
  - `select_walls` は架線の部品を壁に数えない。柱は壁と同じ決め方で残すか消し（`center` は無し）、梁・トロリ線はいつも残す。`catenary_support` は経路が 1 本のセルだけに作る
  - 梁は `trim_catenary` で、残した側壁の外側を削る（壁の無い側はタイルの端まで延びて、隣の線の梁とつながる）
  - `Part.front` の部品（梁・吊り金具・トロリ線）は、位置に関わらず手前の絵（`frontimage`）に描く（`render_layers`）
  - 細い部品（`Part.thin`。架線のトロリ線・ちょう架線）: 1px ほどの線は、全部の画素が半透明になり、高さのある部品の層で半透明の画素を捨てる処理（不透明度 250 未満）で消える。`render_layers` は細い部品だけをもう 1 回描き、捨てた画素のうち不透明度 `THIN_ALPHA`（128）以上の所を不透明にして足す（細い部品のある層だけ、1 回多く描く）
  - 広げる部品（`Part.widen`。架線の梁）: 斜めのタイルの梁は、タイルの角を通って隣の斜めのタイルの梁とつながる。角でちょうど切ると梁の幅が楔形に細り、菱形の角の列はどちらのタイルの持ち分にも入らないので、隙間が見えた。斜めのタイルでは角の先まで切り残し（`WIDEN_PAD`）、`render_layers` で梁だけをもう 1 回描いて、持ち分を左右へ 1 列広げた範囲で足す（2026-11-18）。斜めの梁の長さは `CAT_BEAM_REACH_DIAG`（反対の角まで）。近い斜めの分け合うタイル用のシートは、`beam_part(CAT_BEAM_REACH_TWIN)`（タイルの中心の先まで）を `"replace"` で差し替えて描く
  - 吊り金具・ハンガーのような 1px の縦線は、画面の横の位置を画素の中心に乗せる（`catenary_parts._snap_x`。セルの中心は画素の境）
  - それでも、線の中心が画素の境に来ると半透明の 2 列（2 行）に分かれて、太く見えるか消える。斜めの線は半画素ずらして画素の中心に乗せる（`CAT_DIAG_SHIFT`・`CAT_DIAG_SHIFT_Z`）。直線は傾き 2:1 なので、太さ（`CAT_WIRE_W`・`CAT_WIRE_H`）で 1 行に 2px ずつの階段になるようにした。上下 2 本の線は、間をちょうど 4px（`H / 4`）にして、画素への乗り方をそろえる（2026-11-18）
  - 高さのある部品の層は、架線を足した版と壁だけの版で、壁の画素が減らないことを確かめた（レイアウト検証用モードのシートで、壁だけの版の不透明な画素が透明になった所は 0。変わった画素は架線と重なる所か、架線と壁の境の混ざった色。2026-11-18）
  - 描き分けのキー: `rise`（高さのある部品の持ち分を上へ広げる行数。既定は壁の `WALL_RISE`。架線は `CAT_RISE`）、`wall_only`（way のシートを書かず、壁の way-object のシートだけを書く。`sheet` は作業ファイルの名前にだけ使うので、同じ way の別の対象と違う名前にする）、`wall_label`（壁の way-object のアイコンの文字。既定は `W`）
- 高架と橋脚（AMI の高架の版。#18）:
  - 描き分けのキー: `elev_body`（基盤の下に躯体を足す。`build_base` を `z0=-BASE_H`・`depth=ELEV_BODY_D`・`wu=WALL_U - ELEV_BODY_INSET` で呼び、基盤と同じ決め方で削る。斜めの壁の無い側は `_diag_open_cut(..., inset=ELEV_BODY_DIAG_INSET)` で、基盤と同じ下ほど中心線へ寄る切り口で切る。縦に切ると、奥の線の躯体の切り口が手前の線の床の上に出た）、`write_walls`（False で壁の way-object のシートを書かない。壁を選ぶ処理は基盤の版と同じなので、基盤・躯体の削り方は壁の way-object と合う）。持ち分を下へ広げる行数は `ELEV_BODY_LOWER`（`lower`）
  - `build_base` の `z0`・`depth`・`name`、`_diag_open_cut` の `inset` は、既定の値で前と同じ形になる（既存のシートは画素単位で変わらないことを、blender-poc の描画対象 29 個（`src/` で追跡しているシート 28 枚と、`work/` に書くアイコンの一覧）と AMI の既存の対象で確かめた。2026-11-18、#36 の時点）
  - `ELEV_BODY_D` を 1.0 から 0.25 に浅くした変更（2 階建てバスを高架の下に通すため。PR #37、2026-11-18）では、AMI の高架の 4 版（`ami_rail_ballast_elev_<版>`）と橋脚の 2 種（`ami_pier_rail`・`ami_pier_rail_gate`）のシートだけが変わる。blender-poc と AMI のほかのシートは画素単位で変わらないことを、描き直して確かめた
  - `pier_sheet(sheet, datums, label, across)`: 橋脚の way のシート（線路と同じセルの並び、4 × 10）。経路の中ほどに柱を 1 本（近い斜めは 2 本）立て、上端を高架の躯体の下面に `PIER_TOP_OVERLAP` 重ね、下端は地面の下 `PIER_FOOT` まで。坂は `apply_slope` で地面の坂を当てる。持ち分は地面の菱形を `PIER_RISE` 行上へ広げたもので、不透明度 250 未満を捨てる
  - `pier_gate_sheet(sheet, datums, label)`: 門型の橋脚の way のシート（8 × 10。行 0〜3 が奥の絵、行 `PIER_GATE_FRONT_ROW`〜 が手前の絵）。部品は `_gate_parts` が経路ごとに決める（経路が出る手前の辺（南・東）に門、行き止まりは閉じた側の辺にも門、斜めは中心の柱と外の角への片持ちの梁）。柱と梁の上端は躯体の下面に `PIER_GATE_BEAM_EMBED` 食い込ませ、梁は躯体の下面より `PIER_GATE_BEAM_SHOW` 下まで。寸法は `PIER_GATE_POST`・`PIER_GATE_CLEAR`（`wall_parts.py`）。手前の絵は北西の角の柱と経路より奥の中心の柱を除く（`_GATE_CENTER_FRONT`）。高さ・坂・持ち分は `pier_sheet` と同じ
- 橋とトンネル（AMI の在来線。#19）:
  - 橋は `track_sheet` の橋の作り（`starts`・`piers`。blender-poc の橋）に、次の描き分けのキーを足した。`pier_box`（橋脚の柱の `(横切る向きの長さ, 沿う向きの長さ, 材質)`。無ければ POC の橋の柱）、`badge`（アイコンの印。無ければ `walls` から引く）。床・端の坂の躯体（`rampbody`）・坂から始まる端の躯体（`build_start_body`）の横幅は、どれも既定の壁の外の面まで（`WALL_U + WALL_W`）。`solid` の描き分けでは、端の坂と坂から始まる端のセルで `lower`（持ち分を下へ広げる行数）を使わない。広げると、坂の低い側で地面より下の基盤・躯体まで描かれ、隣の地上の線路の上に帯が出た（2026-11-18）。`solid` と `lower` を両方持つのは AMI の橋だけなので、ほかのシートは変わらない（blender-poc の `track_bridge` と AMI の `ami_rail_ballast_elev_single`・`ami_pier_rail` を描き直して確かめた）
  - `tunnel_sheet(kind, profile, sheet, label)`: `profile` で道床・レールの描き分け（`TRACK_PROFILES` の名前。`replace`・夏の `skin` も使う）、`sheet` でシート・アイコンの名前、`label` でアイコンの数字を選ぶ。既定は前と同じ（`TRACK_PROFILES["new"]`・`track_tunnel`・`100`）
  - どれも既定の値で前と同じ形になる。blender-poc の `track_bridge`・`track_tunnel`・`expressway_tunnel` と、AMI の既存の対象の一部（`ami_rail_ballast_elev_center`・`ami_rail_ballast_base_single`・`ami_pier_rail`）を描き直し、`src/` のシートが変わらないことを確かめた（2026-11-18）
- アドオンのディレクトリは、道具が `os.getcwd()` で決める。アドオンの外では動かさない
- 入口が `tools/blender` を探す相対パスは、`addons/<アドオン>/blender/` から見た `../../../tools/blender`

## 描画が遅いとき

blender-poc の `src/` のシート 28 枚（描画対象 29 個からアイコンの一覧を除いたもの）を 16 並列で描いて約 2 分（117 秒）。時間のほとんどは Boolean（Exact ソルバー）の演算で、描画と後処理は 1 割に満たない（[記録](../docs/records/2026-11-17_sheet-render-speed.md)）。

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
