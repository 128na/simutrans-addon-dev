# 作業ログ: AMI の道路の dat から分岐の絵（1・2）を外す（#21・#22 の続き）

（2026-11-20）

## 目的 / 発端

[2026-11-19_ami-road-switch-ruts.md](2026-11-19_ami-road-switch-ruts.md) で T字の 1・2 を T字の形にした。その後、ユーザーと次のことを確かめた（2026-11-19〜20）:

1. 固定した T字（`sew1`・`sew2`）を正しく見せると、自動の多車線の十字（4×2・6×6）がふさがる
2. ex 画像を足すと直るか（[128na/simutrans#14](https://github.com/128na/simutrans/issues/14) で検討した、pak への直接の継ぎ足しで ex 画像を足す手）
3. 道路の 1・2 は、そもそも T字路の向きを表す絵として想定されていないのではないか（固定の道具ができるまで、T字に「2」を出す手段が無かった）

ユーザーは、KUTA 版から引き継いだ作りで OTRP でも望んだ形ではないこと、線路・道路だけが特別な振る舞いをしていることから、OTRP の分岐の絵の仕様を整理してから直すと決めた。整理するまでの間、AMI の道路は分岐の絵を外して出すことにした（選択肢 1、2026-11-20）。

## 分かったこと（事実）

本体のコードは `128na/simutrans` の `feature/script-save` の `boden/wege/weg.cc` で読んだ。

- 分岐の絵を選ぶ処理は、斜め・近い斜めでない、switch の絵を持つ way だけに入り、`track_wt` なら `select_switch_image`、`road_wt` なら `select_switch_road_image` を呼ぶ（732〜740 行）。ほかの waytype は自動では選ばない
- 道路の「1」は、T字のタイルで、枝の先の隣が三方分岐（T字か十字）で、本線の両隣が三方分岐でないときだけ出る（989〜1093 行）。4 車線（道路 2 本）に 2 車線の道路が T字でつながると、奥の T字のタイルに出る
- 道路の「2」は、T字のタイルには自動では一度も出ない。ex 画像の無い way では、十字のタイルの隣が三方分岐のとき、東 → 西 → 北 → 南の順で最初の向きの「2」（`nse2`・`nsw2`・`new2`・`sew2`）を出す（1145〜1160 行）
- ex 画像のある way の十字（1106〜1142 行）は、隣の三方分岐が「東と南」「東と北」「西と北」「西と南」のどれか 1 組（向かい合う側を含まない）なら十字の 1・2 か ex の十字、それ以外は T字の「2」を出す。十字が 2×2 に並ぶ 4×4 は直るが、4×2（隣が 1 方位だけ）と 6×6 の中の列・行（向かい合う 2 方位）はふさがったまま。ex 画像は `get_child<image_list_t>(2)->get_count() > 26` で有りとされる（`descriptor/reader/way_reader.cc` 50 行）。ex 画像はゲームで足して確かめていない（コードを読んだ結果）
- 固定の道具の T字の名前（`feature/switch-image-override` の `gui/ground_info.cc` の `switch_choice_label`）は線路の分岐の意味で付いていて、道路の自動の使われ方（「1」は渡り口の T字、「2」は多車線の十字）と合わない

## 直したこと

- `addons/ami/blender/ami_dat.py` に `ROAD_SWITCH_IMAGES`（既定は偽）と `SWITCH_IDX` を足した。偽のとき、waytype が `road` の way の dat に `image[nse1]`〜`image[nsew2]` の 10 枚（夏・雪）を書かない。線路の way は変えない
- シートの分岐のセル、`sheetlib` の轍・優先道路の十字・停止線の部品、見本の区画 I・P は消さずに残した（真にすれば戻る）
- `ingame/road_junction_sample.nut` に、4 車線に 2 車線が T字でつながる組み合わせ（`TEES`、`T4x2`・`T4x4`）を足した。撮る場所は `sample_spots.sh` の `JUNCTION_SPOTS`

## 確かめたこと

（2026-11-20、`OTRPv64_3.exe`、`flat_512.sve`、`sample_parallel.sh` で `road_sample.nut`・`road_junction_sample.nut` を温暖側・降雪側に敷いた）

- `makeobj dump dist/ami_road.pak`: 道路の way の画像の並びは、どれも 16 枚（分岐の絵なし）。線路の way は今までどおり分岐の絵を持つ
- `road_sample.nut`: T字 4 種と十字を固定しても `pin1`・`pin2` が通常の絵（`plain`）と同じ。区画 L の十字は東西とも通常の十字（`[check] … L west=… east=… plain=…` が同じ番号）。区画 HV・HH の渡り口は通常の T字（枝の口の点線）が向かい合う
- `road_junction_sample.nut`: 4×2〜6×6 の 8 通りで、十字のタイルはどれも通常の十字（`[check]` の行がすべて `nsew`）。3 種とも、横切る道路はふさがらない（`addons/ami/docs/road_GE_junction_noswitch.png`・`road_junction_noswitch_all.png`）。4×4・6×6 の中ほどの角の丸い四角の枠（角の円弧が閉じたもの）は残る。`T4x2`・`T4x4` は、手前が通常の十字、奥が通常の T字（`addons/ami/docs/road_junction_tee_noswitch.png`）。奥の T字の枝の側は、通常の T字の絵なので枝の口の点線が出る
- 生活道路・一般道路・高速道路の地上の区画（B・L・HV・HH・K・I）の見え方は `addons/ami/docs/road_GE_noswitch_ground.png`

タイルの詳細ダイアログで選ぶときの見た目は見ていない（MCP ではダイアログを開けない）。
