# 作業ログ: 路面軌道の精細化のラウンド 4 を本番に入れる（#56）

（2026-11-20）

## 目的 / 発端

路面軌道の精細化のラウンド 1〜4（`2026-11-20_ami-tram-refine-round1.md`〜`round4.md`）は、`addons/ami/blender/round_tram.py` がラウンドの版の pak にだけ入れていた。全ラウンドを同じ区画で撮り直して並べたところ、ユーザーがラウンド 4 を選んだ（「色味が落ち着いている」）。その描き分けを本番の絵（`src/`）に入れた。

同じときに、スラブ軌道はラウンド 0（本番のまま。ラウンド 3 で締結装置を省いたが、あったほうがよい）、道路はラウンド 3（ラウンド 4 はリアルだが路面の色があせて見える）と決まった。

## 入れたもの

路面軌道の部品（`tools/blender/sheetlib/tram_parts.py`）は AMI の路面軌道だけが使う（blender-poc は使わない）ので、部品の値と形そのものをラウンド 4 にした。

- レールの頭: 0.40〜0.54（`TRAM_RAIL_IN`・`TRAM_RAIL_OUT`。前は線路と同じ 0.41〜0.55）。材質は金属 0 の明るい色（0.92・0.91・0.88、粗さ 0.4）
- 溝: 幅 0.14（前は 0.11）。外側の目地（`tram_seam`）は描かない
- 縁の帯: 0.66・0.65・0.61（前は 0.80・0.79・0.74）
- 油の帯: 描かない（線路の `oil` の部品を差し替えて形を空にする。材質は残す）
- 画面で横向きの斜めと曲線の横向きの所: 頭を 2.2 倍・溝を 1.4 倍（`TRAM_HDIAG_HEAD`・`TRAM_HDIAG_GROOVE`。点ごとの向きで断面を変える押し出し `_var_sweep`）
- T字・十字のすき間埋め: `round_tram.py` は組み立て（`sheetlib.assemble`）を包んでセルの経路を得ていた。本番では `track_sheet` に、セルの経路全部から作る部品の口（`prof["cell_fills"]`。(部品, make) の組）を足し、`tram_parts` の `TRAM_CELL_FILLS` を `render.py` の路面軌道の設定に渡した。口の無い描き分けの絵は変わらない

## 確かめたこと

- 本番で描いた `src/ami_tram.png` は、ラウンド 4 のシート（ラウンドのセッションの `work/rounds/tram/round4/src/`）とバイト単位で同じだった。ゲームの見本は、ラウンド 4 の版で撮った 94 画面（`work/compare/tram/round4`）と同じ絵になる
- 変えていないはずのシート（`ami_rail_ballast`・`ami_rail_slab`・`ami_road_general`・`ami_rail_ballast_base_single` と在来線の壁・`ami_pier_rail`、blender-poc の `track`・`road`）を描き直し、どれも HEAD とバイト単位で同じだった
- `build.py` で `dist/` を作り直した（makeobj の警告なし）

## ラウンドの版の扱い

`round_tram.py` の `ROUND_SETTINGS` の 1〜4 と `apply` は、入れる前の本番に重ねる作りとして残した。`apply` は本番で無くした定数（`TRAM_SEAM_W`・`TRAM_OIL_U`）を読むので、今の本番では動かない（ファイルの冒頭に書いた）。
