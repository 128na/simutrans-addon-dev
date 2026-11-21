# 参照資料の索引（refs）

way 系アドオンを作るときに、既存のアドオンや本家のどこを見ればよいかを引くための索引。

- パスはこのリポジトリの直下から見た相対パス。`../refs/` はこのリポジトリの隣にあり、変更しない
- 中身を確かめた日: 2026-11-19（`../refs/` の各フォルダの dat・文書・画像の一覧。例外は各項目に書く）
- 作業の手順は [way-addon-build](../../.claude/skills/way-addon-build/SKILL.md) にある。本体の描き方と dat の決まりは [way-addon.md](way-addon.md)

## 1. 資料の一覧と使ってよい範囲

見る順の基本は `iss` → 必要なら `pak128` → 構造の参考に `sis`。

| 資料 | 何か | 引くとき | ライセンス | AMI での扱い |
|---|---|---|---|---|
| `../refs/iss` | 新描画位置のインフラ集。層の合成で画像を作り、256px セルで pak にする。ソースとビルド済み pak がある | 最初に見る。way の分け方、壁、架線、高架、橋脚、歩道、dat の実例 | CC BY 4.0 | 出典を示せば流用できる。今は形と数値の参考にしている |
| `../refs/pak128` | pak128 本家のソース。128px セル | 標準の線路・道路とのつなぎ、架線の線、雪の絵、橋・トンネルのキー、車両の大きさ | Artistic License 2.0 | 測定と参照だけ。画像の流用可否は未確認 |
| `../refs/sis` | Project SIS。規格、Blender ソース（`.blend`）、元絵がある | 部材の構造、命名、コストの考え方、way と way-object の分け方 | CC BY-NC-SA 4.0 | 見るだけ。画像・dat を AMI に入れない（AMI は CC BY 4.0） |
| `../refs/trackSet` | 2010 年の軌道セット。バラスト・弾性まくらぎ・スラブ | 古い軌道の命名とコストの感覚 | 改造・再配布は自由と readme にあるが作者名が無い | 参照だけ |
| `../refs/rtx` | 道路・路面の dat をテンプレートから作る | dat の生成方法、速度からコストを出す式、歩道の配置 | CC BY 4.0（`package.json` だけ MIT） | 手法の参考 |
| `../refs/rtg` | 正方形のテクスチャを菱形のタイルへ変換する道具 | 路面の画像変換の実例 | MIT | 手法の参考。線路には使わない |
| `../refs/Simutrans_KUTA_211212` | OTRP v30 系の改造本体の配布物 | 当時の機能の説明（`README.md`） | Artistic License に従うと記載 | 文書だけ読む。exe は動かさない |
| `../refs/image` | 実物の構造の参考画像 | スラブ軌道、架線、車止めの形 | 記載なし | 形を文章に書き起こすだけ。リポジトリにコピーしない |

## 2. 作るものから引く

| 作るもの | 最初に開く | 分かること | 注意 |
|---|---|---|---|
| 線路の通常の way | `../refs/iss/src/way/rail/track_slab.dat`、`../refs/pak128/infrastructure/rail_tracks/rail_100_tracks.dat` | セルの並び、直線・坂・斜め・分岐のキー | iss は 256px（10 × 6 セル）、pak128 は 128px（8 × 9 セル） |
| バラスト | `../refs/iss/src/way/rail/brown.png`・`gray.png`・`noise.png`、`../refs/iss/docs/spec/way.md` | 道床の色とノイズの重ね方 | 手順は Illustrator 前提 |
| スラブ軌道 | `../refs/iss/src/way/rail/track_slab.dat`・`standard_slab.png`、`../refs/sis/track/Shinkansen_Track/track/t2-slab/`、`../refs/image/スラブ軌道.png` | スラブの見え方と実物の層 | iss の速度は 360。AMI の高速線は 480 |
| 分岐 | `../refs/pak128/infrastructure/rail_tracks/rail_100_tracks.dat`、`../refs/iss/docs/spec/way.md` | `NSE1`・`NSE2` などの切替画像。iss は版ごとに切替の有無が違う | 本体の決まりは [way-addon.md](way-addon.md) の 9 章 |
| 架線 | `../refs/iss/src/way-object/rail/catenary_new.dat`、`../refs/pak128/infrastructure/catenary_all/classicalcatenary.dat`、`../refs/sis/track/Shinkansen_Track/catenary/` | iss は版ごとの柱と門、pak128 は上下 2 本の線とハンガー | 測り方と値は [way-addon.md](way-addon.md) の 10 章 |
| 線路の壁 | `../refs/iss/src/way-object/rail/catenary_new.dat`、`../refs/iss/src/definitions.json` | 架線の way-object と高架の絵にある壁 | 壁だけの way-object は線路用には無い |
| 道路の壁 | `../refs/iss/src/way-object/road/wall_1.dat`、`../refs/sis/road/Expressway/sidewall/` | 道路用の壁の way-object | 中央分離帯つきの版は `../refs/iss/src/way-object/road/wall_with_center_divider.dat` |
| 高架 | `../refs/iss/src/way/rail/track_slab.dat`、`../refs/pak128/infrastructure/rail_elevated/rail_100_elevated.dat` | `system_type=1`、壁の焼き込みの有無 | iss は壁を高架の絵に焼き込むので、AMI とは分け方が違う |
| 橋脚 | `../refs/iss/src/util/pier/ground/pier.dat`、`../refs/iss/src/util/pier/elevated/pier.dat`、`../refs/sis/bridge/Steel_Bridge_Pier/` | 橋脚を way にする作り。奥と手前の絵の分け方 | AMI の門型は iss の `pier5`・`pier6` が手本 |
| 橋 | `../refs/iss/src/bridge/rail/bridge.dat`、`../refs/pak128/infrastructure/rail_bridges/rail_100_bridge.dat` | 床・端の坂・坂から始まる端・支柱のキー | `max_lenght` は綴り違いのまま有効 |
| トンネル | `../refs/iss/src/tunnel/rail/tunnel.dat`、`../refs/iss/src/tunnel/rail/under_way.dat`、`../refs/pak128/infrastructure/rail_tunnels/rail_100_tunnel.dat` | 坑口と地下の way | iss は地下用の way を別に作る |
| 道路 | `../refs/iss/src/way/road/ground.dat`・`elevated.dat`、`../refs/pak128/infrastructure/roads/road_030.dat`、`../refs/sis/road/Local_Street/`・`Expressway/`、`../refs/rtx/workspace/road/` | 速度別の種類、高架、路面 | iss は `ns`・`ew` で way を分ける種類がある |
| 歩道 | `../refs/iss/src/util/sidewalk/ground.dat`・`elevated.dat`・`ground_road.dat`、`../refs/rtx/workspace/side/` | 別の waytype を歩道に流用する作り | iss は `water` を使う |
| 跨座式モノレール | `../refs/iss/src/way/monorail/straddle.dat`、`../refs/iss/src/tunnel/monorail/tunnel.dat`、`../refs/iss/src/building/depot/depot.dat` | 地上・高架の版の並び（高架は front・center・back）、カーブが斜めの絵を指すこと、トンネルと車庫のキー | iss の跨座式には雪の絵・近い斜め・橋が無い。動作の確かめの車両は pak128.japan の跨座式（ユーザーが渡した物。リポジトリに入れない） |
| 路面軌道 | `../refs/iss/src/way/rail/tram.dat`、`../refs/pak128/infrastructure/tram_tracks/tram_track_050_a.dat` | waytype の持たせ方 | iss は `tram_track`、pak128 は `track` と `system_type=7` |
| アイコン・カーソル | `../refs/iss/src/icon_way1.png`〜`icon_way3.png`・`icon_bridge.png`、`../refs/pak128/base/misc_GUI/` | 共有シートとシート内蔵の違い | 位置の値は資料ごとに違う |

## 3. 知りたいことから引く

| 知りたいこと | 引く先 |
|---|---|
| 新描画位置の高さ・位置 | iss の元絵を `tools/blender/ref_measure.py` で測る。標準とのつなぎは pak128 も測る |
| 雪の絵 | `../refs/pak128/infrastructure/rail_tracks/rail_100_tracks.dat` の `[1]`。iss・SIS・trackSet の線路には雪の絵が無い |
| 速度・費用の表 | `../refs/iss/docs/spec/way.md`、`../refs/sis/standards/SIS_economy_way.xlsx`、`../refs/rtx/j2class.py` |
| 命名 | `../refs/iss/docs/spec/index.md`、`../refs/sis/standards/SIStandards.xlsx`、`../refs/trackSet/readme.txt` |
| 層の合成の定義 | `../refs/iss/src/definitions.json`、`../refs/iss/docs/spec/definition.md`、`../refs/iss/py/libs/imageManager.py` |
| 同じレールを版ごとに展開する方法 | `../refs/iss/src/definitions.json` の `standard_slab_*`（レール層に配置のマスクと壁の層を重ねる） |
| way と way-object の分け方 | `../refs/sis/bridge/Steel_Bridge_Pier/Metal_p1-01/SIS_SteelBridge_Pier1_E01_ds.dat` |
| dat の生成 | `../refs/rtx/jinja.py`、`../refs/rtx/workspace/dat.j2`、`../refs/rtx/workspace/projects.yml` |
| 車両の大きさ | `../refs/pak128/vehicles/` のシートを測る |

## 4. refs に無いもの

| 探しているもの | 見る所 |
|---|---|
| 箱積み（箱積み駅舎）の寸法と作り。車庫・景観パーツの高さの決まり | refs には無い（「箱積」で検索、2026-11-21）。[hakozumi.md](hakozumi.md) |
| `diagonal[close1]`・`[close2]` などの OTRP の新しいキーの実例 | refs には無い。`../simutrans/descriptor/` と [way-addon.md](way-addon.md) |
| 車止めの専用の dat | 見つからない（`buffer`・`bumper`・`車止` で検索）。形は `../refs/image/` の写真から起こす |
| 新描画位置の pak128 標準の線路 | pak128 は新描画位置ではない。新描画位置の手本は iss |
| dat が読まれるかの確定 | 本体の `../simutrans/descriptor/writer/`。SIS の `overtaking_info` は writer に無い |

## 5. 読むときの注意

- セルの大きさとオフセットは資料ごとに違う。iss・SIS・rtx は 256px、pak128 は 128px。比べる前に dat のセルを確かめる
- AMI の pak は `pak256` で切り出す。手本を試すときも、その手本の dat とシートに合う値で作る
- `.pak` と exe は中身を確かめていない。`../refs/iss/release/pak128/` はゲームに入れて比べる手本として使える
- 未確認: `../refs/iss/docs/spec/position.png`、`../refs/pak128/devdocs/licensing_reasons.odt`、`../refs/image/` の車止めと D 型の画像、SIS の xlsx の値
