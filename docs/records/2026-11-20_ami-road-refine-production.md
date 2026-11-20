# 作業ログ: 道路一式の精細化のラウンド 3 を本番に入れる（#56）

（2026-11-20）

## 目的 / 発端

道路一式の精細化のラウンド 1〜4（`2026-11-20_ami-road-refine-round1.md`〜`round4.md`）は、`addons/ami/blender/round_road.py` がラウンドの版の pak にだけ入れていた。ユーザーがラウンド 3 を選んだ（「4 のほうがリアルだがだいぶ色あせている」）。その描き分けを本番の絵（`src/`）に入れた。

対象は AMI の道路一式で、次のとおり。

- 道路 3 種（`ami_road_local`・`ami_road_general`・`ami_road_expressway`）
- 道路 3 種の基盤・高架・橋・トンネル
- 道路の壁 `ami_wall_road_*`、道路用の橋脚 `ami_pier_road`、歩道 `ami_sidewalk`

同じときに、スラブ軌道はラウンド 0（本番のまま）、路面軌道はラウンド 4 と決まった（路面軌道は `2026-11-20_ami-tram-refine-production.md`）。

## 入れ方

ラウンドの版は、共有の `tools/blender/sheetlib` のモジュールの値を、描くプロセスの中でだけ書き換えていた。壁・基盤・躯体・橋脚の材質の名前と歩道の部品は、在来線・スラブ軌道と blender-poc も使う。そこで既定は変えず、`sheetlib` に口を足して、AMI の道路一式の描き分けからだけ値を渡した。設定は `addons/ami/blender/render.py` の「道路一式の質感」にまとめた。

| ラウンドの版の書き換え | 本番の口 |
|---|---|
| 路面・走行跡の材質（profile の `skin` を、色の段を渡せる自前の材質で上書き） | `road_parts.asphalt_skin` に `ramp`（まだらの色の段）と `wear_t`（走行跡の寄せ具合の倍率）を足した。`core.noisy_material` に `ramp` を足した（既定は前と同じ 0.35・0.65）。`render.py` の `ROAD_SETTINGS` の `skin` に渡す |
| `sheetlib.ROAD_PARTS` の差し替え（走行跡の寄せ具合と、路肩の雪 `snowbank` の材質） | 走行跡は上の `skin` で足りる（ラウンド 3 は帯の形と並びを変えていない）。`snowbank` は下の `snow_skin` に入れた。`road_sheet` に部品の差し替えの口は足していない |
| `material` を包む（名前が `wall`・`base`・`elev_body`・`pier`・`pier_post`・`pier_beam` の材質をまだらに） | `core` に、材質の名前による差し替え（`named_materials`）を足した。`road_sheet`・`tunnel_sheet` は描き分けの `mat_skin`、`pier_sheet` は引数の `mat_skin` を、描くあいだだけ入れる |
| `road_parts.ROAD_SNOW_SKIN` の書き換え（雪の縁石・敷石） | `road_sheet`・`tunnel_sheet` が、描き分けの `snow_skin` を `ROAD_SNOW_SKIN` に重ねる |
| `sidewalk._SNOW`・`sidewalk._M_PAVING` の差し替え | `sidewalk_sheet` に引数 `snow`・`paving` を足した。敷石の材質は `core.brick_material` にした |
| `sidewalk.WORK` の差し替え | `sidewalk.py` が一時フォルダを、描くときの `sheetlib` の `WORK` から引くようにした（名前で取り込むのをやめた）。`round.py` の `_run` の切り替えに付いていく |

- 材質の名前による差し替えは、部品の名前の `skin` では届かない材質のための口。壁・基盤・躯体・橋脚・坑口の躯体は、形を作る関数の中で `material(*組)` を呼ぶ（`build_base`・`build_start_body`・`pier_box` のセル・`pier_sheet`・坑口の `hood`）。口を 1 つずつ通すより、ラウンドの版（名前で包む）と同じ範囲に効く。差し替えた材質には元と別の名前（`ami_road_concrete_<名前>`）を付けた。同じプロセスで後に描くシートが、名前で同じ材質を拾わないようにするため
- 範囲はラウンド 3 と同じにした。門型の橋脚の材質（`pier_post_<向き>`・`pier_beam_<向き>`）と、橋の桁 `girder`、縁石 `road_curb` は、ラウンド 3 でも名前が合わず変わっていない
- 記録のラウンド 1〜3 の「本番に入れるときに直す所」には、`_M_ROAD_ASPHALT`・`_M_PAVING`・`core._SNOW` そのものを直すと書いた。これらは blender-poc と在来線も使うので、そのものは直さず、描き分けから渡す形にした

## 確かめたこと

- 本番で描いた道路一式の 39 枚（道路 3 種とその基盤・高架・橋・トンネル、壁 4 枚、`ami_pier_road`、`ami_sidewalk`）は、ラウンド 3 のシート（ラウンドのセッションの `work/rounds/road/round3/src/`）とバイト単位で同じだった。違いが出た所は無い
  - 比べる前に、ラウンド 3 のシートが変数の取り違えを直した後の描き直しであることを確かめた（`ami_pier_road` と壁 4 枚が、ラウンド 2 とバイト単位で同じ）
- 変えていないはずのシートを描き直し、どれも HEAD とバイト単位で同じだった
  - AMI: `ami_rail_ballast`・`ami_rail_ballast_base_single`（在来線の壁を含む）・`ami_pier_rail`・`ami_rail_slab`・`ami_tram`
  - blender-poc: `src/` の全 28 枚
- 差し替えが後のシートに漏れないこと: `render_parallel` はシートごとに別のプロセスなので、漏れは見えない。1 つのプロセスで `ami_road_general_elev_single`・`ami_pier_road`・`ami_sidewalk` を描いた後に `ami_pier_rail`・`ami_rail_ballast_base_single`・`ami_rail_ballast_tunnel`・`ami_rail_slab_elev_single` を描き、どれも本番のシートとバイト単位で同じだった
- `sheet_audit.py`（`--skip-holes "_wall_road_"`）の候補は、HEAD（ラウンド 0）と同じ 6 件（壁の斜めのセルの 2px の点。前からある）
- `build.py` で `dist/` を作り直した（makeobj の警告なし）
- ゲームの見本（`road_sample.nut` 84 画面・`road_struct_sample.nut` 210 画面・`sidewalk_sample.nut` 48 画面。`OTRPv64_3.exe`、`flat_512.sve`）を本番の pak で撮り、ラウンド 3 の撮影（`work/compare/road*/round3`・`work/compare/sidewalk/round3`）と画素で比べた。違いは全部の画面で、画面の下の状態の行（y 547〜556。時刻など）だけだった
  - 検証用のフォルダの `addons/pak128/` には、前の歩道の `ami_sidewalk.pak` が入っている。撮影の写しにそのまま写るので、1 回目の歩道の撮影は前の歩道（緑がかったまだら）が写った。撮り直しでは、本番の `ami_sidewalk.dat` から作った `ami_sidewalk.pak`（`pak256`）を `EXTRA_PAKS` で写しの中だけ上書きした。検証用のフォルダは変えていない

## ラウンドの版の扱い

`round_road.py` の `ROUND_SETTINGS` の 1〜4 と `apply` は、入れる前の本番に重ねる作りとして残した（ファイルの冒頭に書いた）。今の本番に重ねると、本番とラウンドの設定が混ざる。路面・走行跡とコンクリートはラウンドの値が勝ち、雪と敷石は本番の値が勝つ。次のラウンドは、今の本番を土台にした設定と `apply` を作り直す。
