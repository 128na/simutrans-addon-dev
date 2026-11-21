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
| `tools/blender/sheetlib/` | 描画の共通部分（パッケージ）。部品をそれが表す物ごとに分けてある: `core`（設定値・シーン・材質・形の部品・基準面 `Datum` と部品 `Part` の型）、`slab_parts`（スラブ軌道の部品。コンクリート道床・てん充層・スラブ・突起・締結装置と、スラブの上の汚れ。レールは `track_parts` のものを使う）、`tram_parts`（路面軌道の部品。コンクリートの床・縁の帯・レールの頭・溝・さびと、T字・十字のすき間埋め。レールの横位置は `track_parts` と同じ）、`track_parts`（線路: 道床・まくらぎ・レール・車止め・汚れ）、`wall_parts`（壁・基盤・橋・高架の橋脚。線路と道路で共通）、`catenary_parts`（架線: 柱・梁・吊り金具・トロリ線・ちょう架線・ハンガー）、`road_parts`（道路: 路面・縁石・歩道・白線・車線・汚れ・雪）、`assemble`（部品を経路ごとに組み立てる）、`cells`（セルの描画・特殊色・シート化）、`sheetlib`（線路・道路・トンネル・アイコンのシートと `run_targets`）、`sidewalk`（歩道の way のシート `sidewalk_sheet`。道路の隣のタイルに敷く別の way で、絵は自分のつながりだけで決まる。部品の寸法・材質は `road_parts` の歩道と同じ。引数 `paving`・`snow` で敷石と雪の絵の材質を替えられる）。シート名や、部品をどの版に使うかは持たない |
| `tools/blender/sheet_settings.py` | 設定値: 並列数（`JOBS`、環境変数 `SHEET_JOBS`）・描画の枠（`SLOTS`・`SLOT_DIR`、`SHEET_SLOTS`・`SHEET_SLOT_DIR`）・描画の優先度（`PRIORITY`、`SHEET_PRIORITY`。既定は低）・Blender の場所（`SHEET_BLENDER`）・モード（`SHEET_LAYOUT`・`SHEET_ONLY`）。Blender を使わないので `render_parallel.py` も読む |
| `tools/blender/` のそのほか | 判定・比較・確認の道具（`profile_sheet`（描画の時間の内訳を測る）・`busy_measure`（画面のくどさの数値。物差しは `docs/reference/way-addon.md` の 11 章）・`compose`・`ingame_diff`・`seam_judge`・`slope_measure`・`sheet_diff`・`sheet_audit`（dat が参照するセルの欠陥の候補を数値で探す）・`special`・`special_preview`・`zoom`・`hcat`・`ref_measure`・`check`）と並列描画（`render_parallel`。作業者どうしで共有する描画の枠は `render_slots`） |
| `addons/<アドオン>/blender/render.py` | アドオンのシートの入口。`sys.path` に `tools/blender` を足して `sheetlib` を import し、描き分け（`R.TRACK_PROFILES`・`R.ROAD_PROFILES` への登録）と、対象名 → 描く関数の対応（`SHEETS`）を決めて `R.run_targets(SHEETS, 既定の対象)` を呼ぶ |
| `addons/<アドオン>/blender/addon_config.py` | 判定・比較の道具が読む設定。`PREFIX`（ゲームのタイル一覧でこのアドオンの道を見分ける名前の接頭辞）・`SHEETS`（道の名前 → シート名）・`DIAG_CURVE_SHEETS`（カーブに斜めの絵を使うシート） |
| `addons/<アドオン>/blender/` のそのほか | アドオンの dat の書き出し（`track_dat.py` など）・アドオン固有の確認（`preview.py`・`icons_only.py`）。dat の中身はアドオンの値なので共通には置かない |
| `addons/<アドオン>/ingame/` | ゲームで見本を敷くスクリプト。アドオンの名前（`bpoc_*` など）を使うのでアドオンに置く |

- `sheetlib` の `TRACK_PROFILES`・`ROAD_PROFILES` は、入口が登録する。共通の描画が名前で引くのは `TRACK_PROFILES["new"]`（トンネル）と、プロファイルを渡されなかったときの `ROAD_PROFILES["street"]`・`["expressway"]`（`build_road` の `prof`・`tunnel_sheet` の `road_profile` の既定。blender-poc が登録する）。`road_sheet` は自分のプロファイルを `build_road` に渡すので、ほかの名前で登録した道路（AMI の `road_local` など）でもこの名前は要らない
- 道路の描き分けのキー（AMI の道路 3 種。#21）。どれも無くてよく、無ければ blender-poc の道路と同じ絵になる:
  - `center`: 中央線の種類。`"solid"`（実線。既定）・`"dash"`（破線）・`None`（中央線なし）。破線は白線の種類 `"cdash"` で、タイルの中の長さ（直線 10・斜め 10/√2）を `road_parts.CENTER_DASHES` 本に割り、タイルの辺がすき間の中ほどに来るように置く（`core.tile_dashes`）。直線・斜め・坂の継ぎ目で区切りがそろう。分岐の口の路側線の点線（`"dash"`）は今までどおり
  - `switches`: 真なら分岐の絵（OTRP の switch 画像）のセルを行 2・3 の列 10〜14 に描き、シートを 15 列にする（`expressway` の道路だけ。中身は `road_sheet` の `switch_lines`）
  - `switch_ruts`: T字の分岐の絵の 1・2 を、どちらも枝の無い側を実線でふさいだ T字の白線にし、轍（走行跡）を直進と枝へのカーブ 1 本だけにする（カーブの向きは `road_parts.SWITCH_RUT_ARCS`）
  - `priority_cross`: 十字の分岐の絵（`nsew1`・`nsew2`）を、優先道路のある十字にする（`nsew1` は南北、`nsew2` は東西が優先。従道路に停止線。`road_sheet` の `priority_lines`）
  - `drive_left`: `priority_cross` の停止線の通行の側。真（既定）は左側通行、偽は右側通行
  - `open_cross`: 通常の十字を、交差点の中に白線を通さない開いた十字にする。無ければ、東西の中央線と両側の点線（blender-poc の高速道路の十字）
  - `corner_arcs`: 分岐の絵（T字・十字・1・2・優先道路の十字）で、隣り合う腕の路側線を角で円弧（`road_parts.EDGE_CORNER_R`）でつなぐ
  - 壁を way-object に分ける版（AMI の道路の壁・基盤の版・高架・橋。#22）のキー。意味は線路の同じ名前のキーと同じ（下の「壁を way-object に分けるためのキー」「高架と橋脚」）: `wall_sheet`・`write_walls`・`wall_only`・`curve_cells`・`elev_body`（躯体の深さ `body_d`、壁の外の面から内へ止める幅 `body_inset`、材質 `body_mat`。既定は高架の `ELEV_BODY_D`・`ELEV_BODY_INSET`・`_M_ELEV_BODY`。橋の桁は `body_inset=0` と桁の材質）・`pier_box`（橋の柱。無ければ POC の橋の柱）。`wall_sheet` の坂のセルは、`build_road` の `tall_pad` で壁をタイルの外へ `SLOPE_WALL_PAD` だけ残す（線路と同じ）
  - `switches` 以外のこの 5 つは、AMI の道路の分岐の絵の作り（記録 [2026-11-20_ami-road-switch-design](../docs/records/2026-11-20_ami-road-switch-design.md)）。AMI は今、分岐の絵を dat に入れていないが、シートには描く
  - 路面の色を替えるときは `skin` に `road_parts.asphalt_skin(tag, 暗い色, 明るい色, spec, ramp, wear_t)` を渡す。アスファルト・走行跡・路肩のまだらの雪を同じ 2 色から作る（blender-poc と AMI の高速道路は `EXPWY_ASPHALT`）。`ramp` は路面のまだらの色の段の位置、`wear_t` は走行跡の寄せ具合の倍率で、既定は前と同じ絵
  - `snow_skin`: 雪の絵の材質の差し替え（部品の名前 → 材質）。`ROAD_SNOW_SKIN` に重ねる。道路の坑口（`tunnel_sheet`）も使う
  - `mat_skin`: 材質の名前（`material()` に渡す名前）→ 材質を返す関数。壁・基盤・躯体など、部品の名前の `skin` で届かない材質を、描くあいだだけ替える（`core.named_materials`）。`road_sheet` と道路の坑口が使う。橋脚は `pier_sheet`・`pier_gate_sheet` の引数 `mat_skin` で渡す
- 線路の描き分けのうち、軌道の種類を増やすためのキー（#20 の前準備）。どれも無くてよく、無ければ今の線路と同じ絵になる。`replace`・`skin`・`groups` は今までどおり一緒に使える:
  - `track_parts`: 本体の部品（既定 `TRACK_PARTS`）を丸ごと置き換える。`track_sheet`・`tunnel_sheet`・線路のアイコンは `track_body_parts(prof)` で本体の部品を引く（アイコンには `replace` を当てない）
  - `parts`: 追加の部品。シートに描く部品は `track_sheet_parts(prof)` が決める（本体 + `parts` + `TRACK_EXTRAS` に `replace` を当てたもの）。アドオンの `R.TRACK_EXTRAS += ...` は `R` の名前を付け替えるだけで効かないので、このキーで渡す。足した部品の色は `sheetlib/layout_colors.py` に足す
  - `bed_fills`: 分岐（`diag_curves` の T字・十字）の直線と斜めの間のすき間を埋める層。`{部品の名前: (上面の半幅, 板の下面の高さ, 板の上面の高さ)}` で、書いた順に埋める（複数の層を埋められる）。斜めの部分の横幅の倍率は、その部品の `width` で決まる。無ければ `BED_FILLS`（`ballast` だけ。`ballast` が無い部品の組では何も埋めない）。指定した名前の部品が無いときは止まる
  - `cell_fills`: セルの経路全部から形を作る部品。`(部品, make)` の組の並びで、`make(経路の並び)` が形（None なら描かない）を返す。その部品と同じ基準面の部品がセルにあるときだけ描く（路面軌道の `TRAM_CELL_FILLS`）
  - `snow_skin`: 雪の絵だけの材質の差し替え（部品の名前 → 材質）。`track_skin` の雪の結果に重ねる（`track_profile_skin`。夏の絵の `skin` と対）。`track_sheet` とトンネルの坑口の両方に効く
  - `anchor`・`cy`: 絵の基準位置（タイルの中心をセルの何行目に映すか）と、持ち分の菱形の中心の行。無ければ線路と同じ `128 + BALLAST_DY`・`GROUND_CY`。道路の上に重ねる路面軌道（AMI の `ami_tram`。#23）は道路と同じ `ROAD_CY` にし、`spill` を 0 にする
- 路面軌道の部品（`tram_parts`。AMI の `ami_tram`）: `TRAM_TRACK_PARTS`（`track_parts` に渡す。縁の帯の板・コンクリートの床・溝・レールの頭。どれも路面の高さ 0 のすぐ上の薄い板。画面で横向きの斜めでは頭と溝を太くする）、`TRAM_CELL_FILLS`（`cell_fills` に渡す。T字・十字の床のすき間を埋める）、`TRAM_WEAR_REPLACE`（`replace` に渡す。線路の汚れ `rust0`・`rust1`・`oil` を床の上の帯に差し替え、まくらぎのさびを消す）、`TRAM_SNOW_SKIN`（`snow_skin` に渡す。雪の絵でも汚れを夏の材質のままにする）。床と縁の帯は基準面 `tram_bed`（`FLAT` にある。スラブ軌道の `slab_bed` と同じく、分岐の絵で作り直さない）に乗る。縁の帯は床の全幅の明るい板を床の下に敷いて作るので、T字・十字ではつないだ床の外周にだけ出る
- 線路の描き分けのうち、壁を way-object に分けるためのキー（AMI の基盤の版。#16）:
  - `wall_sheet`: 壁を way の絵に描かず、このシート名の壁の way-object のシートに描く。上 4 行が奥、下 4 行（`WALL_FRONT_ROW` から）が手前の絵。`diag_curves` と一緒に使える（斜めの部品は `assemble` の `path_opts` で、直線と斜めの部品を 1 回でまとめて切り分ける）
  - `cull_diag_wall_ends`: 壁の way-object のシートで、画面で縦向きの斜め（北東⇔南西）のタイルの側壁（`wallL`・`wallR` のうち横幅の倍率が 1 より小さいもの）を、裏面を描かずに描く（`render_layers` の `cull_diag_wall_ends`）。タイルの境で切り口の面を取った（`open_ends`）壁の口から、壁の中（影で暗い）が見えなくなり、口は透明になる。斜めのタイルの手前の絵が、隣の行き止まりのタイルの奥の壁の絵より後に描かれ、角に暗い縦線が出た（AMI #63）。ほかの部品には当てない（行き止まりの端の壁は、基準面の分だけタイルの外へ動いて外の面ごと切り口として取られ、口から見える壁の中が外の面の代わりになっている。画面で横向きの斜めの側壁は、口が長い面の端より画面で約 2px 先へ出ていて、消すと隣の壁との間に草が出た）。既定は偽（blender-poc のシートは変えない）
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
  - `pier_sheet(sheet, datums, label, across, anchor, cy, top_drop, diag_k, style)`: 橋脚の way のシート（線路と同じセルの並び、4 × 10）。経路の中ほどに柱を 1 本（近い斜めは 2 本）立て、上端を高架の躯体の下面に `PIER_TOP_OVERLAP` 重ね、下端は地面の下 `PIER_FOOT` まで。坂は `apply_slope` で地面の坂を当てる。持ち分は地面の菱形を `PIER_RISE` 行上へ広げたもので、不透明度 250 未満を捨てる。道路用の橋脚（AMI の `ami_pier_road`。#22）のために次の引数を足した。`anchor`・`cy`（絵の基準位置と持ち分の菱形の中心。既定は線路の way と同じで、道路は `ROAD_CY`）、`top_drop`（上端を下げる量。道路の高架は基盤を路面の板の下へ `ROAD_BASE_DROP` 下げてある）、`diag_k`（斜めの柱の横切る向きの長さの倍率。道路は 1/√2）、`style`（アイコンの背景）、`mat_skin`（描くあいだだけの材質の名前による差し替え。道路の描き分けの `mat_skin` と同じ）。既定の値で前と同じ形になる
  - `pier_gate_sheet(sheet, datums, label, mat_skin)`: 門型の橋脚の way のシート（8 × 10。行 0〜3 が奥の絵、行 `PIER_GATE_FRONT_ROW`〜 が手前の絵）。部品は `_gate_parts` が経路ごとに決める（経路が出る手前の辺（南・東）に門、行き止まりは閉じた側の辺にも門、斜めは中心の柱と外の角への片持ちの梁）。柱と梁の上端は躯体の下面に `PIER_GATE_BEAM_EMBED` 食い込ませ、梁は躯体の下面より `PIER_GATE_BEAM_SHOW` 下まで。寸法は `PIER_GATE_POST`・`PIER_GATE_CLEAR`（`wall_parts.py`）。手前の絵は北西の角の柱と経路より奥の中心の柱を除く（`_GATE_CENTER_FRONT`）。高さ・坂・持ち分は `pier_sheet` と同じ。`mat_skin` は `pier_sheet` と同じ材質の名前による差し替え（#83）。柱と梁の材質の名前は角・辺ごとに `pier_post_<角>`・`pier_beam_<辺>` なので、差し替えの表にはその名前で入れる
- 橋とトンネル（AMI の在来線。#19）:
  - 橋は `track_sheet` の橋の作り（`starts`・`piers`。blender-poc の橋）に、次の描き分けのキーを足した。`pier_box`（橋脚の柱の `(横切る向きの長さ, 沿う向きの長さ, 材質)`。無ければ POC の橋の柱）、`badge`（アイコンの印。無ければ `walls` から引く）。床・端の坂の躯体（`rampbody`）・坂から始まる端の躯体（`build_start_body`）の横幅は、どれも既定の壁の外の面まで（`WALL_U + WALL_W`）。`solid` の描き分けでは、端の坂と坂から始まる端のセルで `lower`（持ち分を下へ広げる行数）を使わない。広げると、坂の低い側で地面より下の基盤・躯体まで描かれ、隣の地上の線路の上に帯が出た（2026-11-18）。`solid` と `lower` を両方持つのは AMI の橋だけなので、ほかのシートは変わらない（blender-poc の `track_bridge` と AMI の `ami_rail_ballast_elev_single`・`ami_pier_rail` を描き直して確かめた）
  - `tunnel_sheet(kind, profile, sheet, label, road_profile, mat_skin)`: `profile` で道床・レールの描き分け（`kind="track"` のときだけ。`TRACK_PROFILES` の名前。`replace`・夏の `skin` も使う）、`sheet` でシート・アイコンの名前、`label` でアイコンの数字を選ぶ。既定は前と同じ（`TRACK_PROFILES["new"]`・`track_tunnel`・`100`）。`kind="expressway"` では `profile` を引かず、`road_profile`（`ROAD_PROFILES` の名前かその値の辞書）の `groups`・`skin`・`label`・`style` で路面を描き、`sheet` を渡したときは中央線を `center` に合わせる（無ければ blender-poc の `expressway_tunnel` と同じ白線）。`sheet` を渡すと道路の種類ごとの坑口のシートを作れる（AMI の `ami_road_*_tunnel`。#22）。`mat_skin` は `kind="track"` のときの材質の名前による差し替え（AMI の線路の坑口の躯体。#83）。道路の坑口は `road_profile` の `mat_skin` を使い、この引数は見ない
  - どれも既定の値で前と同じ形になる。blender-poc の `track_bridge`・`track_tunnel`・`expressway_tunnel` と、AMI の既存の対象の一部（`ami_rail_ballast_elev_center`・`ami_rail_ballast_base_single`・`ami_pier_rail`）を描き直し、`src/` のシートが変わらないことを確かめた（2026-11-18）
- アドオンのディレクトリは、道具が `os.getcwd()` で決める。アドオンの外では動かさない
- 入口が `tools/blender` を探す相対パスは、`addons/<アドオン>/blender/` から見た `../../../tools/blender`

## 描画が遅いとき

blender-poc の `src/` のシート 28 枚（描画対象 29 個からアイコンの一覧を除いたもの）を 16 並列で描いて約 2 分（117 秒）。時間のほとんどは Boolean（Exact ソルバー）の演算で、描画と後処理は 1 割に満たない（[記録](../docs/records/2026-11-17_sheet-render-speed.md)）。

- Boolean は `sheetlib/core.py` の `boolean()`・`clip_to_tile()`（中で `_apply_modifier`）を通す。`bpy.ops.object.modifier_apply` を直接呼ぶと、呼ぶたびにシーン全体の更新が走って 2 倍近く遅くなる
- `boolean()` の `use_self`（既定 True）は、削る形が自分自身と重なるときに要る。外すだけだと、分岐・十字で重なり合う帯が正しく抜けず絵が壊れる（2026-11-17 に確認）。重ならない形（帯 1 本）を 1 つずつ削るなら `use_self=False` でよく、同じ絵で速い（`assemble._place` の通り道の切り抜き）。道路の車道の型（`assemble._carve`）と壁の外側の切り抜き（`sheetlib.road_sheet` の `roadcut`）も 1 つずつ削る（絵は路面のざらつきが最大 5 ほど変わるだけ）。基盤の切り抜き（`build_base`）は `use_self` が要る（外すと絵が変わる）。新しく Boolean を足すときは、削る形が自己交差しないよう 1 つずつに分けられないかを先に考える
- 時間は、削る側の形の面数で決まる。新しい分岐の形（通り道）を足して遅くなったら、`profile_sheet.py` で測る（アドオンのディレクトリで `SHEET_ONLY=ns,diag_nw,up12 blender -b --factory-startup --python ../../tools/blender/profile_sheet.py -- 対象名`。内訳は `work/profile_<対象>.txt`）
- 並列数は 16 が最速だった（12・24・28 は遅い）。PC を替えたときだけ `SHEET_JOBS` を測り直す
- 複数の作業者（別の worktree・セッション）が同時に描いても、マシン全体で動く Blender の数は描画の枠の合計（`SHEET_SLOTS`。既定は論理コア数 − 4、このマシンで 20）を超えない（#74）。`render_parallel.py` は Blender を 1 本起こす前に共有の場所（既定は `%LOCALAPPDATA%\simutrans-addon-dev\render-slots`、`SHEET_SLOT_DIR`）の枠を 1 つ取り、終わったら返す。空きが無ければ待ち、待っている本数を `[render] 枠待ち` で出す。`--jobs` はその回だけの上限として今までどおり効く
  - 止めたり落ちたりした回の枠は OS が返す（ロックファイルのロックで数えるので、プロセスが消えれば外れる）。Windows では、強制終了した回の Blender も道連れに止まる（Job Object）
  - `SHEET_SLOTS` を変えるときは、同時に描く全員で同じ値にする（値が違うと、大きいほうが実効の上限になる）。今どれだけ使われているかは `python -X utf8 tools/blender/render_slots.py`
  - 論理コアが 20 より少ない PC では、既定の枠が `SHEET_JOBS` の 16 を下回り、1 本だけでも枠で抑えられる。PC を替えたら `SHEET_JOBS` と合わせて決め直す
  - 枠を取るのはこの仕組みが入った後の `render_parallel.py` だけ。古いブランチの worktree で描くと枠を数えない
- `render_parallel.py` は Blender を優先度「低」で起動する（`--priority`、環境変数 `SHEET_PRIORITY`。`low`・`below_normal`・`normal`）。描画が CPU を使い切っても、ほかの作業が重くならないようにするため（ほかの作業が CPU を使う間は、描画のほうが遅くなる）。Blender を直接 `blender -b` で動かすときは、優先度は下がらない（PowerShell なら `Start-Process -Priority` は無いので、起動後に `(Get-Process blender).PriorityClass = 'Idle'`）
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

## CI の道具（`ci/`）

アドオンごとのワークフロー（`.github/workflows/addon-<アドオン>.yml`）は、アドオンの `check.sh` を呼ぶだけ。同じ `check.sh` を手元（Windows は Git Bash）で回せば、CI と同じ検査になる（GitHub Actions を使えないときの代わり）。道具の版はアドオンの `ci.env` に書く（[#50](https://github.com/128na/simutrans-addon-dev/issues/50)）。

```bash
bash addons/ami/check.sh                 # ruff・dat の書き忘れ・dat_linter・pak のビルド
SKIP_BUILD=1 bash addons/ami/check.sh    # pak のビルドを飛ばす
bash addons/blender-poc/check.sh         # ruff だけ
```

- 手元で要るもの: Python、gh（サインイン済み。道具を取るとき）、uvx か pipx（ruff）。makeobj と dat_linter は `~/.cache/simutrans-addon-dev/ci-tools` に取ってくる（`TOOLS_DIR` で変えられる）。`MAKEOBJ_FROM_PATH=1` で `PATH` の makeobj を使う
- AMI の pak は、CI（本家 125.0 の Linux 版 60.10）と手元（Windows 版 60.12）でバイト単位で同じだった（2026-11-20）
- OTRP の fork の makeobj（`OTRP-KUTAv6` の `20ed249`。60.5、「Simutrans 122.0.1 Nightly」用）は、`otrp:` でビルドできるが、近い斜めの画像のキー（`diagonal[close1]`・`[close2]`）を知らず、AMI の pak は作れなかった（2026-11-20）。今の AMI には本家の makeobj が要る
- `ci/setup-makeobj.sh <指定> <置き場所>`: makeobj を用意する。`upstream:<tag>` は本家のリリースの配布物（Linux 版か Windows 版）、`otrp:<ref>` は OTRP の fork を `<ref>` で取り出して makeobj だけをビルドする（Linux だけ）。キャッシュのキーに指定を使うので、`<ref>` はタグかコミットにする
- `ci/setup-dat-linter.sh <版> <置き場所>`: dat_linter（Linux 版か Windows 版）を用意する。`fmt`（整形）は使わない（dat は生成するので、整形しても次の生成で戻る）
- ruff は、動かすと止まる誤りだけを見る（各アドオンと `tools/` の `ruff.toml`）
