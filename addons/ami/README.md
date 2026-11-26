# AMI（AI Marunage Infrastructure）

pak128 用のインフラアドオン集。絵は Blender のスクリプトで描く（作り方は [blender-poc](../blender-poc/README.md) で確かめたもの）。

> **ベータ版。** ロードマップ（[#61](https://github.com/128na/simutrans-addon-dev/issues/61)）の第 1 弾を、ベータ版として配る（[#91](https://github.com/128na/simutrans-addon-dev/issues/91)。基準は「多少課題があってもゲーム内で動作すれば OK」）。正式版までに、物の名前・値・見た目が変わることがある。既知の課題（ベータの後に回したもの）は [ACCEPTANCE.md の「ベータ版（第 1 弾）での扱い」](ACCEPTANCE.md#ベータ版第-1-弾での扱い)、遊ぶ人向けの説明は配る zip の `ami_readme.txt`（元は [release/readme.txt](release/readme.txt)。簡潔な説明・導入方法・注意点だけで、物の一覧は「主な中身」として網羅を保証しない。すべての物の一覧は、zip に入れる `ami_lineup.txt`（dat から `lineup.py` が作る。[#138](https://github.com/128na/simutrans-addon-dev/issues/138)）。名前が変わったときのセーブデータの扱いは [ADR 0009](../../docs/adr/0009-ami-beta-renames-without-readme-notice.md)）。敷き方の説明は下の「[遊ぶ人向けの敷き方](#遊ぶ人向けの敷き方)」。

**今あるのは在来線の通常の版（`ami_rail_ballast`）と、在来線の基盤の 4 版・壁だけの way-object・架線つきの壁の way-object（`ami_rail_ballast_base_*`・`ami_wall_rail_*`・`ami_wall_rail_*_catenary`）、高架の 4 版と橋脚の way（`ami_rail_ballast_elev_*`・`ami_pier_rail`・門型の `ami_pier_rail_gate`）、橋とトンネル（`ami_rail_ballast_bridge`・`ami_rail_ballast_tunnel`）、高速線（スラブ軌道）の通常の版・基盤の 4 版・高架の 4 版・橋・トンネル（`ami_rail_slab`・`ami_rail_slab_base_*`・`ami_rail_slab_elev_*`・`ami_rail_slab_bridge`・`ami_rail_slab_tunnel`）、弾性まくらぎ直結軌道（コンクリート道床）とフローティング・ラダー軌道の同じ一式（`ami_rail_concrete`・`ami_rail_concrete_*`・`ami_rail_ladder`・`ami_rail_ladder_*`）、道路 3 種の通常の版（`ami_road_local`・`ami_road_general`・`ami_road_expressway`）と、道路の基盤の 4 版・高架の 4 版・橋・トンネル（`ami_road_*_base_*`・`ami_road_*_elev_*`・`ami_road_*_bridge`・`ami_road_*_tunnel`）、多車線・交差点の路面表示（`ami_mark_*`）、道路の壁の way-object（`ami_wall_road_*`）と中央分離帯つきの壁（`ami_wall_road_*_divider`）、道路用の橋脚（`ami_pier_road`）、路面軌道の通常の版（`ami_tram`）、歩道（`ami_sidewalk`）と歩道の種類・高架の歩道・歩道の柵（`ami_sidewalk_<舗装>`・`ami_sidewalk_elev`・`ami_wall_sidewalk_<版>`）、線路×道路の踏切と水路の踏切（`ami_crossing_*`）、盛土（`ami_embankment_front`・`ami_embankment_back`）、電柱（`ami_sidewalk_pole_<版>`・`ami_wall_sidewalk_<版>_pole`）、道路標識 6 種（`ami_sign_<名前>`）、懸垂式モノレール（`ami_monorail_suspended_<版>`・`ami_monorail_suspended_elev_<版>`）と、モノレールの電化（`ami_monorail_power`・`ami_monorail_suspended_power`）、リニアの 3 種（超電導 `ami_maglev_guideway_<版>`・常電導 `ami_maglev_beam`・チューブ式 `ami_maglev_tube_<版>` と、それぞれの高架・トンネル）、ガイド（`ami_maglev_guide`）とチューブ（`ami_maglev_tube_cover`）。** 描画から pak までの骨組み（[#14](https://github.com/128na/simutrans-addon-dev/issues/14)）の上に、在来線の壁の無い通常の版を仕上げ（[#15](https://github.com/128na/simutrans-addon-dev/issues/15)。全方位・分岐の絵・近い斜め・雪・汚れ）、基盤の版と壁を足した（[#16](https://github.com/128na/simutrans-addon-dev/issues/16)。[「壁の敷き方」](docs/objects/rail.md)）。壁に架線を持たせた版を足した（[#17](https://github.com/128na/simutrans-addon-dev/issues/17)。[「架線の作り」](docs/objects/rail.md)）。高架の 4 版と、高架の真下の地面に敷く橋脚の way を足した（[#18](https://github.com/128na/simutrans-addon-dev/issues/18)。[「高架と橋脚の作り」](docs/objects/rail.md)）。橋とトンネルを足した（[#19](https://github.com/128na/simutrans-addon-dev/issues/19)。[「橋とトンネルの作り」](docs/objects/rail.md)）。高速線を足した（[#20](https://github.com/128na/simutrans-addon-dev/issues/20)。[「高速線の作り」](docs/objects/rail.md)）。道路 3 種の通常の版を足した（[#21](https://github.com/128na/simutrans-addon-dev/issues/21)。[「道路の作り」](docs/objects/road.md)）。道路の壁・基盤の版・高架・橋脚・橋・トンネルを足した（[#22](https://github.com/128na/simutrans-addon-dev/issues/22)。[「道路の壁・高架・橋脚・橋・トンネルの作り」](docs/objects/road.md)）。路面軌道を足した（[#23](https://github.com/128na/simutrans-addon-dev/issues/23)。[「路面軌道の作り」](docs/objects/rail.md)）。歩道を足した（[#24](https://github.com/128na/simutrans-addon-dev/issues/24)。[「歩道の作り」](docs/objects/roadside.md)）。バリエーションの第 1 弾（[#61](https://github.com/128na/simutrans-addon-dev/issues/61)）として、弾性まくらぎ直結軌道を足した（[#62](https://github.com/128na/simutrans-addon-dev/issues/62)。[「弾性まくらぎ直結軌道の作り」](docs/objects/rail.md)）。続けてフローティング・ラダー軌道を足した（[#67](https://github.com/128na/simutrans-addon-dev/issues/67)。[「フローティング・ラダー軌道の作り」](docs/objects/rail.md)）。線路×道路の踏切を足した（[#111](https://github.com/128na/simutrans-addon-dev/issues/111)。[「踏切の作り」](docs/objects/crossing.md)）。第 2 弾（[ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md)）の景観として、盛土を足した（[#123](https://github.com/128na/simutrans-addon-dev/issues/123)。[「盛土の作り」](docs/objects/roadside.md)）。4 車線の中央分離帯を足した（[#118](https://github.com/128na/simutrans-addon-dev/issues/118)。[「中央分離帯の作り」](docs/objects/roadside.md)）。第 2 弾（[ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md)）として、歩道の種類・高架の歩道・歩道の柵を足した（[#119](https://github.com/128na/simutrans-addon-dev/issues/119)。[「歩道の種類・高架の歩道・歩道の柵の作り」](docs/objects/roadside.md)）。多車線の路面表示の版を足した（[#121](https://github.com/128na/simutrans-addon-dev/issues/121)）が、路面軌道の景観の way で多車線と交差点の白線を描く路面表示に置き換えた（[#187](https://github.com/128na/simutrans-addon-dev/issues/187)。[「路面表示の作り」](docs/objects/marking.md)）。線路・道路と運河の水路の踏切（跳ね橋）を足した（[#117](https://github.com/128na/simutrans-addon-dev/issues/117)。[「水路の踏切の作り」](docs/objects/crossing.md)）。第 2 弾の景観として、電柱を足した（[#120](https://github.com/128na/simutrans-addon-dev/issues/120)。[「電柱の作り」](docs/objects/roadside.md)）。第 2 弾の景観として、道路標識を足した（[#122](https://github.com/128na/simutrans-addon-dev/issues/122)。[「道路標識の作り」](docs/objects/roadside.md)）。第 2 弾の軌道として、懸垂式モノレールを足した（[#116](https://github.com/128na/simutrans-addon-dev/issues/116)。[「懸垂式モノレールの作り」](docs/objects/monorail.md)）。狭軌（30・60）とそのトンネル・車庫を足した（[#370](https://github.com/128na/simutrans-addon-dev/issues/370)。[「狭軌の作り」](docs/objects/narrow.md)）。第 6 弾として、リニアを足した（[#371](https://github.com/128na/simutrans-addon-dev/issues/371)。[「リニアの作り」](docs/objects/maglev.md)）。下の表の残りは作る予定のもの（開発ステップの一覧は [#27](https://github.com/128na/simutrans-addon-dev/issues/27)）。範囲と作りを決めた理由は次の ADR にある。

- [ADR 0002](../../docs/adr/0002-ami-scope.md): 範囲・対象・ライセンス・配布（第 1 弾まで。ADR 0008 に置き換えた）
- [ADR 0003](../../docs/adr/0003-ami-walls-base-piers-as-separate-objects.md): 壁・基盤・橋脚・歩道の分け方
- [ADR 0004](../../docs/adr/0004-shared-blender-tools.md): 描画の道具を `tools/` で共通にする
- [ADR 0005](../../docs/adr/0005-ami-render-tool-conventions.md): 部品のまとめ方・レイアウト検証用モード・設定値・並列
- [ADR 0006](../../docs/adr/0006-ami-track-variants-by-track-form.md): 線路のバリエーションを軌道の形式で足す
- [ADR 0007](../../docs/adr/0007-ami-beta-distribution.md): 第 1 弾のベータの配り方（場所・版の名前・zip の中身）
- [ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md): 第 2 弾の範囲（入れる物・入れない物・順番・名前・pak）。ADR 0002 を置き換える。ADR 0014 に置き換えられ、0014 は ADR 0015 に置き換えられた
- [ADR 0014](../../docs/adr/0014-ami-scope-stations-and-signals.md): 駅・停留所・線路の信号を範囲に入れていた。ADR 0015 に置き換えられた
- [ADR 0015](../../docs/adr/0015-ami-scope-back-to-iss.md): 範囲を iss にある物に戻す。閉塞信号 `ami_rail_signal` を外し、ADR 0014 を置き換える
- [ADR 0016](../../docs/adr/0016-ami-remove-road-stops.md): 道路の停留所を外す（pak256 が自前を用意した）。ADR 0015 の「停留所は残す」を置き換える
- [ADR 0017](../../docs/adr/0017-ami-scope-narrow-gauge-and-linear.md): 狭軌とリニアを範囲に入れる（車両は別のアドオンに任せる）。ADR 0015 の「狭軌とリニアを入れない」を置き換える

## 目的と中身

オブジェクト名はどれも `ami_` で始める。名前は次のとおり確定した（2026-11-15）。

| もの | 名前 |
|---|---|
| way（通常の版） | `ami_tram`・`ami_rail_ballast`・`ami_rail_concrete`・`ami_rail_ladder`・`ami_rail_slab`・`ami_road_local`・`ami_road_general`・`ami_road_trunk`・`ami_road_expressway` |
| 基盤・高架の版 | `<way の名前>_base_<版>`・`<way の名前>_elev_<版>`（版は `single`・`back`・`center`・`front`。一般道路・生活道路は `single` だけ。#260） |
| 橋・トンネル | `<way の名前>_bridge`・`<way の名前>_tunnel` |
| 路面表示 | `ami_mark_<種類>`（`lane4`・`junction2`・`junction2_t`・`junction4_in`・`junction4_out`・`junction4_c`、6 車線の `lane6_a`・`lane6_b`・`lane6_m`・`junction6_in`・`junction6_out`・`junction6_m`・`junction6_c`。一般道路に重ねる。#187・#189。[「路面表示の作り」](docs/objects/marking.md)）。高速道路の分岐・合流は `diverge_main`・`diverge_ramp`・`merge_main`・`merge_ramp`（高速道路に重ねる。#188。[「高速道路の分岐・合流の路面表示の作り」](docs/objects/marking.md)）。路面の色は `paving_red`・`paving_blue`・`paving_green`・`paving_red_striped`、黄色の中央線は `center_yellow`（一般道路に重ねる。#313。[「路面の色と黄色の中央線の作り」](docs/objects/marking.md)） |
| 線路の壁 | `ami_wall_rail_<版>`（`single`・`back`・`center`・`front`。`center` は行き止まりの端の壁だけ）、架線つきは `ami_wall_rail_<版>_catenary`（`center` は架線と、行き止まりの端の壁だけ）。近い斜めの分け合うタイル用に `ami_wall_rail_twin`（壁だけ。[「壁の敷き方」](docs/objects/rail.md)）と `ami_wall_rail_twin_catenary`（架線つき。[「架線の作り」](docs/objects/rail.md)） |
| 道路の壁 | `ami_wall_road_<版>`（`single`・`back`・`center`・`front`。`center` は行き止まりの端の壁だけ）。カーブの形ごとの `single` の壁 `ami_wall_road_single_arc`（一般道路の円弧用）・`ami_wall_road_single_ell`（生活道路の L 字用。#260）。近い斜めの分け合うタイル用に `ami_wall_road_twin`（名前は確定。2026-11-19、ユーザーの決定。[「道路の壁・高架・橋脚・橋・トンネルの作り」](docs/objects/road.md)）。中央分離帯つきは `ami_wall_road_front_divider`・`ami_wall_road_center_divider`・`ami_wall_road_twin_divider`（[「中央分離帯の作り」](docs/objects/roadside.md)） |
| 橋脚・歩道 | `ami_pier_rail`（門型は `ami_pier_rail_gate`）・`ami_pier_road`・`ami_sidewalk`。歩道の種類は `ami_sidewalk_<舗装>`（`asphalt`・`brick`・`tile`）、高架の歩道は `ami_sidewalk_elev`（#119） |
| 歩道の柵 | `ami_wall_sidewalk_<版>`（`single`・`back`・`front`。#119。名前は作業者が決めた。ユーザーが PR で確かめる） |
| 電柱 | `ami_sidewalk_pole_<版>`（電柱だけ）・`ami_wall_sidewalk_<版>_pole`（柵つき。#120） |
| 景観 | 盛土 `ami_embankment_front`・`ami_embankment_back`（ADR 0008 の `ami_embankment_<版>`）、道路標識 `ami_sign_<名前>`（6 種。#122）、路面の横断歩道の標識 `ami_sign_crosswalk`・`ami_sign_crosswalk_one_way`（#162） |
| モノレール | 跨座式 `ami_monorail_straddle`、高架 `ami_monorail_straddle_elev_<版>`（`front`・`center`・`back`）、トンネル `ami_monorail_straddle_tunnel`（ADR 0008。#113）。懸垂式 `ami_monorail_suspended_<版>`、高架 `ami_monorail_suspended_elev_<版>`（どちらも `front`・`center`・`back`。#116）。電化 `ami_monorail_power`（跨座式用）・`ami_monorail_suspended_power`（懸垂式用。#116） |
| リニア | 超電導 `ami_maglev_guideway_<版>`（`single`・`back`・`center`・`front`。防音壁は way の絵）、高架 `ami_maglev_guideway_elev_<版>`、ガイド `ami_maglev_guide`（電化を兼ねる way-object）、トンネル `ami_maglev_guideway_tunnel`。常電導 `ami_maglev_beam`、高架 `ami_maglev_beam_elev_<版>`（`front`・`center`・`back`）、トンネル `ami_maglev_beam_tunnel`。チューブ式 `ami_maglev_tube_<版>`（超電導と同じ 4 版）、高架 `ami_maglev_tube_elev_<版>`、チューブ `ami_maglev_tube_cover`（way-object）、トンネル `ami_maglev_tube_tunnel`（[ADR 0017](../../docs/adr/0017-ami-scope-narrow-gauge-and-linear.md)。#371） |
| 狭軌 | 30 km/h の `ami_narrow_wood`・60 km/h の `ami_narrow_ballast`、トンネル `ami_narrow_ballast_tunnel`（#370） |
| 運河 | `ami_canal`（ADR 0008。#114）、景観の運河 `ami_canal_scenic`（#161） |
| 水路の踏切 | `ami_crossing_<線路\|道路>_canal`（例 `ami_crossing_rail_ballast_canal`・`ami_crossing_road_general_canal`。#117） |
| 車庫 | `ami_rail_depot`・`ami_tram_depot`・`ami_road_depot`・`ami_monorail_depot`・`ami_canal_depot`（ADR 0008）・`ami_maglev_depot`（#371）・`ami_narrow_depot`（#370） |
| 操車場 | `ami_rail_yard`（#115） |
| 転車台・遷車台 | `ami_rail_turntable`（#314。道路の way。1 タイルで転車台、直線に敷くと遷車台） |

dat のファイル名と pak に入る名前は同じ（`src/<名前>.dat`）。今あるのは `ami_rail_ballast`・`ami_rail_ballast_base_<版>`（4 版）・`ami_wall_rail_<版>`（4 版）・`ami_wall_rail_twin`・`ami_wall_rail_<版>_catenary`（4 版）・`ami_wall_rail_twin_catenary`・`ami_rail_ballast_elev_<版>`（4 版）・`ami_pier_rail`・`ami_pier_rail_gate`・`ami_rail_ballast_bridge`・`ami_rail_ballast_tunnel`・`ami_rail_slab`・`ami_rail_slab_base_<版>`（4 版）・`ami_rail_slab_elev_<版>`（4 版）・`ami_rail_slab_bridge`・`ami_rail_slab_tunnel`・`ami_rail_concrete`・`ami_rail_concrete_base_<版>`（4 版）・`ami_rail_concrete_elev_<版>`（4 版）・`ami_rail_concrete_bridge`・`ami_rail_concrete_tunnel`・`ami_rail_ladder`・`ami_rail_ladder_base_<版>`（4 版）・`ami_rail_ladder_elev_<版>`（4 版）・`ami_rail_ladder_bridge`・`ami_rail_ladder_tunnel`・`ami_road_local`・`ami_road_general`・`ami_road_expressway`・道路それぞれの `_base_<版>`（幹線道路・高速道路は 4 版、一般道路・生活道路は `single` だけ。#260）・`_elev_<版>`（4 版）・`_bridge`・`_tunnel`・`ami_wall_road_<版>`（4 版）・`ami_wall_road_twin`・`ami_wall_road_front_divider`・`ami_wall_road_center_divider`・`ami_wall_road_twin_divider`・`ami_pier_road`・`ami_tram`・`ami_embankment_front`・`ami_embankment_back`・`ami_sidewalk`・`ami_sidewalk_<舗装>`（3 種）・`ami_sidewalk_elev`・`ami_wall_sidewalk_<版>`（3 版）・`ami_sidewalk_pole_<版>`（2 版）・`ami_wall_sidewalk_<版>_pole`（2 版）・`ami_monorail_straddle`・`ami_monorail_straddle_elev_<版>`（3 版）・`ami_monorail_straddle_tunnel`・`ami_monorail_suspended_<版>`（3 版）・`ami_monorail_suspended_elev_<版>`（3 版）・`ami_monorail_power`・`ami_monorail_suspended_power`・`ami_maglev_guideway_<版>`（4 版）・`ami_maglev_guideway_elev_<版>`（4 版）・`ami_maglev_guide`・`ami_maglev_guideway_tunnel`・`ami_maglev_beam`・`ami_maglev_beam_elev_<版>`（3 版）・`ami_maglev_beam_tunnel`・`ami_maglev_tube_<版>`（4 版）・`ami_maglev_tube_elev_<版>`（4 版）・`ami_maglev_tube_cover`・`ami_maglev_tube_tunnel`・`ami_canal`・`ami_canal_scenic`・水路の踏切 7 つ（`ami_crossing_<線路|道路>_canal`）・`ami_narrow_wood`・`ami_narrow_ballast`・`ami_narrow_ballast_tunnel`・車庫 6 つ・`ami_rail_yard`・`ami_rail_turntable`。

### 線路（新描画位置）

| 種類 | 速度 | way | 版 |
|---|---|---|---|
| 路面軌道（tram、コンクリートで固めた線路） | 60 km/h | `ami_tram` | 通常だけ（壁・高架・橋・トンネルなし） |
| 在来線（バラスト軌道） | 160 km/h | `ami_rail_ballast` | 通常・基盤 4 版・高架 4 版・橋・トンネル |
| 弾性まくらぎ直結軌道（コンクリート道床、#62） | 240 km/h | `ami_rail_concrete` | 同上 |
| フローティング・ラダー軌道（#67） | 360 km/h | `ami_rail_ladder` | 同上 |
| 高速線（スラブ軌道） | 480 km/h | `ami_rail_slab` | 同上 |
| 狭軌（waytype `narrowgauge_track`、#370） | 30・60 km/h | `ami_narrow_wood`・`ami_narrow_ballast` | 通常だけ。60 だけトンネル（[「狭軌の作り」](docs/objects/narrow.md)） |

### 道路

| 種類 | 速度 | 中央線 | way | 版 |
|---|---|---|---|---|
| 生活道路 | 40 km/h | なし | `ami_road_local` | 通常・基盤 single・高架 single・橋・トンネル（#260） |
| 一般道路 | 120 km/h | 白線 | `ami_road_general` | 同上 |
| 幹線道路 | 240 km/h | 破線 | `ami_road_trunk` | 同上 |
| 高速道路 | 360 km/h | 広い破線 | `ami_road_expressway` | 同上 |

- 一般道路・生活道路の基盤と高架は `single`（両側に壁）だけ（#260。#209 の 3 本目。2026-11-24、ユーザーの判断「バリエーションを減らして整理したい。center などの 4 種類→single のみ、橋、トンネルは残しカーブはそろえる」）。消したのは `ami_road_<general|local>_<base|elev>_<back|center|front>` の 12 個（`catalog.py` の `Road.variants`）。幹線道路・高速道路は 4 版のまま。奥だけ・手前だけ・壁なしの複線や 4 車線の分離帯（`ami_wall_road_*_divider`）は、幹線道路・高速道路で組む。消した物を使った保存データは読み込めなくなる。代わりの物への置き換えはしない（ベータ版のため。リリースの readme に書いた）
- 断面はどれも blender-poc の高速道路と同じ（片側 1 車線、タイル全面が路面、歩道なし）
- 通常の版は #21、基盤の版・高架・橋・トンネルと道路の壁・橋脚は #22
- 地上の道路の基盤の 4 版は、ゲームの画面で要ると判断して作り、置くことが確定した（2026-11-19、ユーザーの決定。理由は[「道路の壁・高架・橋脚・橋・トンネルの作り」](docs/objects/road.md)）

### 版の並び

- 4 版は `single`（両側に壁）・`back`（奥だけ）・`center`（なし）・`front`（手前だけ）。iss・SIS と同じ並べ方
- 基盤の版: 基盤が壁の位置で止まる。同じ版の壁の way-object と組で使う（`center` の way-object は行き止まりの端の壁だけ）
- 高架の版: 床と床の下の躯体だけ。橋脚は描かない
- 橋: 欄干を描かない。壁の way-object を重ねる
- 分岐の絵（OTRP の switch 画像、1・2 の 10 枚）は線路の全部の way に入れる。道路は 2026-11-23 に戻した（#46。外していた間の経緯は 2026-11-20。[「道路の作り」](docs/objects/road.md)の[「分岐の絵（switch 画像 1・2）」](docs/objects/road.md)）。近い斜めは壁の無い way に入れる
- 雪の絵と汚れ（blender-poc の 6 章）は全部の way に入れる

### 付属（別の pak にして同梱）

| もの | 作り | 名前（仮） |
|---|---|---|
| 線路の壁と架線 | way-object。架線つき（電化）の `single`・`back`・`center`（架線だけ）・`front` と、壁だけの `single`・`back`・`center`（行き止まりの端の壁だけ）・`front` | `ami_wall_rail_*`・`ami_wall_rail_*_catenary` |
| 道路の壁 | way-object。`single`・`back`・`front`。中央分離帯つきの `front_divider`・`center_divider`・`twin_divider`（#118） | `ami_wall_road_*` |
| 橋脚 | 高架の真下の地面に敷く、別の waytype の way。線路用（単柱と門型）と道路用 | `ami_pier_rail`・`ami_pier_rail_gate`・`ami_pier_road` |
| 歩道 | 道路の隣のタイルに敷く、別の waytype の way。舗装の種類と高架の版がある | `ami_sidewalk`・`ami_sidewalk_<舗装>`・`ami_sidewalk_elev` |
| 歩道の柵 | 歩道に重ねる way-object。`single`・`back`・`front` | `ami_wall_sidewalk_*` |
| 電柱 | 歩道に重ねる way-object。タイルのわきに立てる電柱だけと、柵の版ごとの柵つき（#120） | `ami_sidewalk_pole_<版>`・`ami_wall_sidewalk_<版>_pole` |
| 踏切 | 線路 4 種 × 道路 4 種の 16 個の crossing（#111。幹線道路は #257） | `ami_crossing_<線路>_<道路>` |
| 水路の踏切 | 線路 4 種・道路 3 種 × 運河の 7 個の crossing（#117） | `ami_crossing_<線路\|道路>_canal` |

景観（盛土・道路標識）は付属と分けて `ami_scenery.pak` に入れる（ADR 0008）。

橋脚の waytype は #18 で `tram_track` に決めた（[「高架と橋脚の作り」](docs/objects/rail.md)。iss と同じ）。歩道の waytype は #24 で iss と同じ `water` に決めた（2026-11-20、ユーザーの決定。[「歩道の作り」](docs/objects/roadside.md)）。

### 物ごとの作り

物ごとの作り（形・寸法・材質・セル・dat の値の決め方・汚しと精細化・見本と確かめたこと）は、物の種類ごとの文書に分けた（#304）。ほかの文書やコードの注記は、節を `docs/objects/<文書>.md` の「節の名前」の形で直接指す（README を経由しない。#350）。

| 文書 | 中身 |
|---|---|
| [rail.md](docs/objects/rail.md) | 線路 5 種と旧描画位置の線路、手本、壁・架線・高架と橋脚・橋とトンネル、分岐の追加画像 |
| [road.md](docs/objects/road.md) | 道路、分岐・十字・T字の絵、道路の壁・高架・橋脚・橋・トンネル、道路の ex 画像 |
| [roadside.md](docs/objects/roadside.md) | 歩道とその種類・柵、盛土、道路標識、横断歩道の標識、電柱、中央分離帯 |
| [marking.md](docs/objects/marking.md) | 路面表示、高速道路の分岐・合流の路面表示、路面の色と黄色の中央線、路面表示の汚し |
| [crossing.md](docs/objects/crossing.md) | 踏切、水路の踏切 |
| [monorail.md](docs/objects/monorail.md) | 跨座式・懸垂式のモノレールと、その電化 |
| [maglev.md](docs/objects/maglev.md) | リニア（超電導・常電導・チューブ式）とガイド・チューブ |
| [narrow.md](docs/objects/narrow.md) | 狭軌（30・60）とそのトンネル |
| [canal.md](docs/objects/canal.md) | 運河、景観の運河、運河の汚しと景観の運河の斜め・行き止まり |
| [depot.md](docs/objects/depot.md) | 車庫、操車場、転車台・遷車台 |
| [icons.md](docs/objects/icons.md) | アイコン・カーソル、リリース用のサムネイル |

### 後で足すもの

- なし（旧描画位置の線路は、高架・橋・トンネル・橋脚まで作った。#26）

### 範囲に入れないもの

- 車庫（#112）・操車場（#115）以外の建物（blender-poc の料金所 `bpoc_tollbooth` は移さない）

## 対象

- Simutrans 本家 125.0.1 と OTRP（pak128）。OTRP だけの絵（分岐の絵・近い斜め・分岐の追加画像）は本家では使われないだけで、本家用の pak は分けない（ベータで決めた。2026-11-21、ユーザーの決定）
- 画像は 256px セル（`pak256` で切り出し、ゲームは pak128）

## 遊ぶ人向けの敷き方

- 導入: zip の中の `pak128` フォルダを、Simutrans の `addons` フォルダ（無ければ作る）に入れる。起動のオプション `-addons` は要らない（付けずに起動すると、アドオンを読み込むかを確かめる画面が出て、そこで選べる。2026-11-21、ユーザーの言葉。#137）
- 線路・道路は「版」を選んで敷く。single（単線・1 本）、back・center・front（複線・3 線の奥・中・手前）。基盤・高架の版と壁は、アイコンの右下の漢字（単・後・中・前。近い斜め用の壁は 双）で版を見分ける。通常の版（壁を重ねない地上の線路・道路）には札が無い
- 基盤の版の線路・道路に、同じ版の壁（way-object）を重ねると、壁つきの線路・道路になる。架線は「架線つきの壁」（壁の無い center の版は架線だけ）
- 版の奥・手前は、南北の線なら西が back・東が front、東西の線なら北が back・南が front。複線のカーブで画面の右と左に曲がる角では、外の線と内の線の版（back・front）が角の前後で入れ替わる。角のタイルは南北の辺と同じ版にする。線路は東西の辺を先に敷き、南北の辺を角のタイルまで後から敷く。壁は逆に、南北の辺を角のタイルまで先に敷き、東西の辺を後から敷く（同じ速さの壁は、後から敷いても前の版のままになるため。作りは[「壁の敷き方」](docs/objects/rail.md)）
- 高架の下の地面には、橋脚の way を敷く。橋脚は路面軌道のメニューにある（線路の高架の下を地上の線路が横切るタイルには敷かない。敷くと線路とつながるか、線路が切れる。[「高架と橋脚の作り」](docs/objects/rail.md)）
- 歩道は船のメニューにある（waytype が `water`）。道路の隣のタイルに敷く
- 盛土は路面軌道のメニューにある（waytype が `tram_track`）。高架の北・西の脇に `back`（札は 後）、南・東の脇に `front`（札は 前）を敷く。輪にして台を作るときは、北東・南西の角に `front` を後から敷く（[「盛土の作り」](docs/objects/roadside.md)）
- 電柱は船のメニューの way-object にある（札は 柱 と版。柵なしと柵つきは札が同じで、名前で見分ける）。電柱だけを立てるときは、柱を立てたい側（道路の側など）の版を選ぶ。柵の歩道に立てるときは、同じ版の柵つきの電柱を重ねる（柵が置き換わる）。同じ版を並べると電線がつながる（[「電柱の作り」](docs/objects/roadside.md)）
- 中央分離帯は道路のメニューの壁（way-object）にある（札は 分前・分中・分双）。4 車線は、奥のタイルに基盤の版 `back` と壁 `back`、手前のタイルに基盤の版 `front` と `front_divider` を敷く。輪にするときは、東西の辺の `front_divider` を、角が `back` のタイルの 1 つ手前で止める（[「中央分離帯の作り」](docs/objects/roadside.md)）
- 多車線と交差点の白線は、路面軌道のメニューの路面表示（札は 奥・前・交・丁・入・出）を、一般道路に重ねて敷く。路面軌道・線路のタイルには置かない。手順は[「路面表示の作り」](docs/objects/marking.md)
- 高速道路の分岐・合流の白線は、同じメニューの路面表示（札は 分・岐・合・流）を、高速道路と、その左のランプの列に重ねて敷く。手順は[「高速道路の分岐・合流の路面表示の作り」](docs/objects/marking.md)
- 操車場は線路のメニュー（駅の道具）にある。地上の直線の線路の上に建てると、乗客も郵便も扱わない駅になり、列車を止めておける。乗客の駅の隣に建てると、その駅の一部になる（[「操車場の作り」](docs/objects/depot.md)）
- 道路標識は道路のメニューの標識の道具にある。最高速度・一時停止の標識は飾りで、車の速さは変わらない。最低速度の標識は、それより遅い車を通さない。一方通行の標識は、同じタイルにもう一度置くと向きが逆になる（[「道路標識の作り」](docs/objects/roadside.md)）
- ベータの既知の課題は [ACCEPTANCE.md の「ベータ版（第 1 弾）での扱い」](ACCEPTANCE.md#ベータ版第-1-弾での扱い)

## ライセンス

CC BY 4.0。

`docs/curve_study_*.png`（#88 の比べ）には、iss（作者 128na、`128na/iss`、CC BY 4.0）のシートのセルとゲームの画面を、AMI と並べるために切り出して含む。

## 必要なもの

- Blender 4.5 LTS（`PATH` には無い。場所は `D:/bin/blender/blender.exe` で、`tools/blender/sheet_settings.py` の既定なので `render_parallel.py` には渡さなくてよい。別の場所は `--blender` か環境変数 `SHEET_BLENDER` で渡す）
- makeobj（`PATH` にある）

## ビルド

アドオンのディレクトリ（`addons/ami/`）で、描画の道具は `tools/` にある（[tools/README.md](../../tools/README.md)）。

```powershell
D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py   # シートを src/ へ（対象を絞るなら末尾に -- ami_rail_ballast）
python -X utf8 blender/ami_dat.py                                              # dat を src/ へ
python -X utf8 build.py                                                        # makeobj で dist/ へ
```

- `build.py` は、全部入りのまとめ `dist/ami.pak` と、種類別の `ami_rail.pak`（線路）・`ami_tram.pak`（路面軌道）・`ami_road.pak`（道路と路面表示 `ami_mark_*`）・`ami_monorail.pak`（モノレール）・`ami_canal.pak`（運河）・`ami_maglev.pak`（リニア）・`ami_narrow.pak`（狭軌）・`ami_extra.pak`（付属）・`ami_scenery.pak`（景観）と、旧描画位置の物（#26）だけを集めた `ami_rail_old.pak` を作る。旧の物は `ami.pak` と種類別の pak（旧の `ami_rail_old.pak` 以外）に入らない（`build.py` の `belongs`）。dat が無い種類は作らない。makeobj の出力に警告かエラーがあれば止まる
- `build.py` は続けて、`src/ex_donors.dat` から提供用の pak（`work/ex/donors.pak`）を作り、各 pak の線路・路面軌道・道路の way と架線つきの壁へ ex 画像を継ぎ足す（[「分岐の追加画像」](docs/objects/rail.md)）。継ぎ足した数を出し、pak ごとに名前で当たる提供用の物が全部写ったことと、継ぎ足した絵（26〜29・31〜34 番が空でなく、通常の T字・十字と違うこと、30・35 番が通常の十字と同じこと）を確かめ、違えば止まる。pak の中の ex 画像の数は `python -X utf8 ex_graft.py --list dist/ami.pak` で見られる
- シートを複数描くときは `python -X utf8 ..\..\tools\blender\render_parallel.py <対象>...`。レイアウト検証用モードは `SHEET_LAYOUT=1`（`work/layout/` に書く）
  - `render.py` に対象を並べて 1 本で順に描かず、`render_parallel.py` で並列に描く。ほかの作業者と同時に描いても、マシン全体で共有する描画の枠（`SHEET_SLOTS`）を取って順番待ちにするので、`--jobs` と `SHEET_SLOTS` は既定のままにする（`SHEET_SLOTS` を変えるときは全員でそろえる）
  - 全対象の名前は `catalog.SCALED_TARGETS` で取る。`src/*.png` から作らない（壁の `ami_wall_rail_*` の 8 枚は基盤の対象 `ami_rail_*_base_*` が一緒に書くので、対象に渡すと「unknown target」で止まる）。全対象の描画は約 14 分かかる（ほかの作業者の描画と重なると、枠の順番待ちでさらに延びる）
  - `render_parallel.py` は `render.py` を `--own` で描くので、描いたシートの外にあるアイコン・カーソル（トンネルのアイコンなど）は書かない（[アイコン・カーソル](docs/objects/icons.md)）。シートを描き直して前後で比べるときは、描いた後に `icons.py`（全部）を流してから比べる（流さないと、アイコンだけの違いが描画のずれに見える）
  - `icons.py` は Blender で流す（`D:/bin/blender/blender.exe -b --factory-startup --python blender/icons.py`）。`python` で流すと `bpy` が無く終了コード 1 で終わり、出力をログに向けていると見落とす
  - シートの PNG をコミットするときは、`icons.py` が書いたセルの控え `src/<シート>.icon_cells.txt` も一緒にコミットする（#330）。描画はアイコン・カーソルのセルに仮の絵を描き、`icons.py` がそれを描き直して、書いたセルの sha256 をこの控えに書く（`render.py` は描いたシートの分だけ `icons.py --own` を自分で呼ぶ。ほかのシートにある分は、上のとおり描き終えてから `icons.py` を流す）。`check.sh` の `check_icons.py` が控えと今のシートを比べるので、仮の絵のままのセルや、控えをコミットし忘れたシートは落ちる
  - 描き直すと `src/*.road_cells.txt`・`*.icon_sources.txt`・`*.icon_cells.txt` の改行（LF/CRLF）だけが変わることがある。比べるためだけに描いたときは、比べた後に `git checkout -- addons/ami/src` で戻す
- `build.py`・`blender/ami_dat.py`・`check.sh` は、1 つの作業ツリーの中で同時に 1 つしか動かない（`blender/src_lock.py` のロック。`work/src.lock`。#326）。先に動いている物があれば、その持ち主を 1 行出して終わるまで待つ（上限は環境変数 `SRC_LOCK_WAIT` の秒数。既定 1800。超えたら止まる）。ロックは OS のファイルロックなので、強制終了しても残らない。`check.sh` が中で呼ぶ `ami_dat.py`・`build.py` は取り直さない。シートの描画（`render.py`・`render_parallel.py`・`icons.py`）はロックを取らない
  - `check.sh` は dat の書き忘れを、`src/` の dat を消さずに、`ami_dat.py --out <一時のフォルダ>` の出力と比べて見る
- `ami_dat.py` は dat を LF で書くので、CRLF で取り出した作業ツリーでは改行だけの差分が出る。`git add -A src` でステージすると、本当に変わった物だけが残る
- レイアウト検証用モードの pak は `SHEET_LAYOUT=1` で描いた後、`SHEET_LAYOUT=1 python -X utf8 build.py`（`work/layout/dist/` に作る）
- 同じシートの通常の描画とレイアウト検証用の描画を同時に動かさない。セルごとの生の絵（`work/<シート>_<セル>.png`）の名前が同じで、互いのセルを取り込んだシートができた（2026-11-17）
- `src/`（dat とシート）はコミットする。`dist/` と `work/` はコミットしない
- 配る zip は `python -X utf8 release.py --version <版> --paks <pak>...`（`work/release/ami-<版>.zip`。`--paks` は `dist/` の pak の名前を拡張子なしで並べる）。中身は `pak128/` の pak と、`release/readme.txt`（遊ぶ人向けの説明。`{version}` を版の名前に置き換える）・`release/license.txt`（CC BY 4.0 と帰属）・`ami_lineup.txt`（選んだ pak に入る物の一覧。`lineup.py` が `src/` の dat と `build.py` の `KINDS` から作る。列は名前・種類・最高速度・購入費・維持費・登場年。`python -X utf8 lineup.py --format html` で同じ一覧を HTML でも出せる）・`release/text/` の訳のファイル（`pak128/text/` に入れる。#122）。全部入りの `ami` と種類別を同時に選ぶと止まる（同じ物を二重に読む）。readme の元に固定の版名（`beta.3`・`ami-beta.3.zip` など）が書いてあっても止まる（版ごとの変更は Release の説明に書き、readme には `{version}` だけを書く。`check.sh` も `release.py --check` で `release/readme*.txt` を確かめる。#345）。`--extract` で `work/release/ami-<版>/` にも展開する
  - 版ごとの変更（増えた物・無くなった物・保存データへの影響）は、`release/readme.txt`・`release/readme_old.txt` に書かず、GitHub のリリースの説明に書く（readme は版をまたいで同じ文にし、版の名前は `{version}` だけで入れる。古い版の変更の節が残ったため。#341）
  - 配る形（[ADR 0007](../../docs/adr/0007-ami-beta-distribution.md)）: このリポジトリの GitHub リリース（プレリリース）に、種類別の 4 つを入れた zip を置く。全部入りの `ami.pak` は入れない（同じフォルダに両方を置くと二重に読む）。ベータの版は `beta.<n>`、タグは `ami-beta.<n>`。第 1 弾は `python -X utf8 release.py --version beta.1 --paks ami_rail ami_road ami_tram ami_extra`。第 2 弾（beta.2。#170）は `python -X utf8 release.py --version beta.2 --paks ami_rail ami_road ami_tram ami_extra ami_monorail ami_canal ami_scenery`（7 本、約 12MB の zip。旧描画位置の `ami_rail_old` は入れない。[記録](../../docs/records/2026-11-22_ami-beta2-release.md)）。第 3 弾（beta.3。#234）は同じ 7 本（約 20MB の zip）で `python -X utf8 release.py --version beta.3 --paks ami_rail ami_road ami_tram ami_extra ami_monorail ami_canal ami_scenery`、旧描画位置は別の zip に `python -X utf8 release.py --version beta.3-old --paks ami_rail_old --readme release/readme_old.txt --no-thumbnail`（[記録](../../docs/records/2026-11-24_ami-beta3-release.md)）
- 精細化のラウンドの版（#56）: `blender/round.py` が、系統（`AMI_FAMILY`。既定は在来線一式の `rail_ballast`。ほかは `round.py` の `FAMILIES`）ごとに、物を `_round<n>` の名前で描いて pak（在来線は `rounds/ami_round<n>.pak`、ほかは `rounds/ami_<系統>_round<n>.pak`）を作る（`src/`・`dist/` は変えない）。描き分けは `blender/round_<系統>.py` の `ROUND_SETTINGS` と `apply`（今の `render.py` に重ねる）。本番に入れたラウンドの鍵は、重ねると二重にかかるので外してある（#351。在来線・路面軌道・道路・第 3 弾の一部・第 5 弾。決めた値は記録）。描かずに `python -X utf8 blender/round.py 0` だけを流すと、今の `src/` の絵を `_round0` の名前にした pak を作る（本番の絵をラウンドの版と並べて撮るとき）。描いた絵（`work/rounds/…/round<n>/src/`）があれば、`round.py <n>` でその pak を作り直せる。`rounds/` の pak は記録としてコミットする。見本は `SUFFIX=_round<n> EXTRA_PAKS=rounds/ami_round<n>.pak bash ingame/sample_parallel.sh`、くどさは `ingame/calib_capture.sh`（`WAYS_NUT`・`PAKS`・`NUT`。検証用のフォルダの写しで起動する。基盤・高架の版は `NUT=ingame/calib_struct.nut`）と `tools/blender/busy_measure.py`（基盤・高架の版は `BUSY_REF` に通常の版の名前を渡し、その範囲に限った値で判定する）。橋・トンネルは `NUT=ingame/calib_bt.nut`（トンネルは地形を作るので `PRE=1`）、壁・橋脚を重ねた版は `NUT=ingame/calib_wall.nut`（重ねる前と比べるのは `BUSY_PAIR`）、拡大率ごとの値は `ZOOMS` と `BUSY_BYZOOM=1`で測る（物差しは [way-addon.md](../../docs/reference/way-addon.md) の 11 章）。回し方はスキル [way-refine-rounds](../../.claude/skills/way-refine-rounds/SKILL.md)
- 設定は `blender/catalog.py`（軌道の種類と、そこから導く way・基盤・高架・橋・トンネルの名前）、`blender/render.py`（描き分け・シート名）、`blender/ami_dat.py`（dat と値）、`blender/addon_config.py`（判定の道具が読む対応表）

### pak の大きさ（pak256 などで組む。#261・#266）

pak の大きさは、環境変数 `SHEET_PAK_SIZE`（タイルの幅の画素数。既定は 128 = pak128。いまは 128 の整数倍だけで、整数でない倍率は未対応）の 1 つで選ぶ（`tools/blender/sheet_settings.py` が読む。`PAK_SIZE`・`SCALE`・`PAKSET`・`SUFFIX`）。

- 世界の単位（タイル 1 辺 = 10）で決めた形は変わらず、画素数だけが `SCALE` 倍になる。画素で書いた値（pak128 で測ったもの）には `SCALE` を掛ける。`SCALE` が 1 のとき、掛けた式は掛けない式と同じ値なので、pak128 のシートは変わらない（全シートを変更前のコードで描いた絵と全画素で比べて確かめた。#266）。
- 大きさに比例させた値:

  | 場所 | pak128 → 256 |
  |---|---|
  | `sheetlib/core.py` | セル `CELL` 256 → 512、高さ 1 段 16px → 32px（`H` は世界の単位なので同じ）。まだらの粒の細かさ（`noisy_material` の模様は #298、`tiled_concrete_material` の粒は #355。画素で 128 と同じ大きさの粒にする）。コンクリートのしみ・雨だれは物の大きさの模様なので掛けない（タイルに対する大きさを 128 と同じにする） |
  | `sheetlib/cells.py` | 地面の菱形の中心 `GROUND_CY` 127 → 254、道路 `ROAD_CY` 128 → 256。持ち分マスクは、その大きさで直接作る（下） |
  | `sheetlib/sheetlib.py` | 絵の基準位置 128 → 256、`BALLAST_DY` −1 → −2、`DIAG_PX`、持ち分を上へ広げる行数（`WALL_RISE`・`TUNNEL_RISE`） |
  | `render.py` | 基準面の下げ幅 `_DATUMS`、`spill` |
  | `sheetlib/depot.py` | 建物の絵のタイルの中心を置く位置 `BUILDING_DROP` 64 → 128、dat のオフセット `BUILDING_OFFSET` −64,−96 → −128,−192（車庫・操車場。#261 の D）。入口の高さ `DOOR_PX` は世界の単位なので同じ |
  | `sheetlib/canal.py` | 景観の運河の水面の深さ `SCENIC_DEPTH_PX` 13 → 26、笠石の厚みの持ち分を上へ広げる行数 1 → 2（#261 の D） |
  | `sheetlib/roadsign.py` | 標識の板（画素の絵）を最近傍で `SCALE` 倍に拡大して押す（#261 の B）。柱の高さ・太さは世界の単位なので同じ |
  | dat（`ami_dat.py`） | 位置合わせ `-64,-32` → `-128,-64`。標識の左側通行のずらし `offset_left` は 14 のまま（単位がタイルの幅の 1/64 で、pak の大きさによらない。倍にすると標識が道路の外へずれる） |
  | `build.py` | makeobj の大きさ `pak256` → `pak512`（セルの一辺） |
  | `icons.py` | アイコンは 32px のまま。絵（直線のセル）を切る大きさ・カーソルの札の位置と大きさを `SCALE` 倍 |

  持ち分マスク（`_ground_mask`）は、256 では pak256 の地面と同じ決まり（列ごとに上の辺と下の辺の間。縁の段は 2×1）で、その大きさで直接作る（`_ground_mask_direct`。#321）。平らと坂の 65 形すべてで、pak256 の地面の形と画素で一致する。縦の位置（`GROUND_PHASE`）は、pak256 の地面のゲームで坂の継ぎ目と平らなタイルの継ぎ目に草が出ない値に決めた。以前（#266）は、地面が pak128 を画素ごとに 2 倍にした pak256poc（段が 4×2）だったので、pak128 の大きさで作ったマスクを最近傍で拡大していた。pak256 の地面ではそれが道路の縁の 4×2 の階段になった（pak256#111）。経緯は [記録](../../docs/records/2026-11-26_ami-ground-mask-256.md)。広げるときは、ずらした形の和を 1 行刻みで足す（道路の坂の地面の位置から道路の位置まで、橋の端の坂の面から地面まで）。128 の刻みのまま 2 倍にすると間の 1 行が抜け、薄い列に穴ができて、台の上の十字の奥の角に草の線が出た。また、道路の位置（`ROAD_CY`）で描く物（道路・路面軌道・運河・踏板）は、256 では平らでも地面の位置まで塗る（奥の縁が地面の菱形の縁とそろう。pak128 は平らの奥の 2 辺を 1 行空けて、奥のタイルのはみ出しに任せる。そのままだと坂と平らの境で奥の縁が 2 行跳んだ。pak256 の判断で入れた）（#333、[記録](../../docs/records/2026-11-26_ami-ground-mask-256-holes.md)）。ただし平らなタイルの、つながる奥の辺（北・西）の上は空け、奥のタイルの絵に任せる（塗ると、白線が向きを変える所で奥の線の端を覆った。#354、[記録](../../docs/records/2026-11-26_ami-white-line-seam-256.md)）。路面軌道は空けずに塗る（道路がつながらない辺に塗った道路の端を、レールで覆う。#365、[記録](../../docs/records/2026-11-26_ami-tram-band-365.md)。路面軌道の版の印は `check_tram_band.py` が `check.sh` で見る）。地面との一致と列の穴は `tools/blender/check_ground_mask.py` が `check.sh` で見る。pak128 のマスクは変えていない。確かめたのは倍率 2（256）だけで、3 以上の持ち分マスク（縦の位置と半行の画素数）は未確認。

  半画素の位置を画素の行の境にそろえる値（`DIAG_CENTER_SHIFT`・斜めの路側線の丸め）は、倍率を掛けず、倍率の偶奇で決める（`DIAG_HALF_PX`）: 画面で横向きの斜めの白線は太さが約 1px × `SCALE` で、奇数の画素（128）は行の中心に置くので 0.5px ずらし、偶数の画素（256）は行の境に置くのでずらさない（ずらすと白線が 1 行の白と半端な 2 行に割れて細く灰色に見えた）。確かめたのは倍率 1・2 だけで、3 以上は決めていない（太さが 0.68px × `SCALE` なので、偶奇だけで足りるかは未確認）。
- 出力は pak128 と分ける（混ざらず、同時に描いても途中のセルの名前がぶつからない）: シート・dat は `src256/`、途中のセルは `work256/`、pak は `dist256/`、zip は `work/release/ami-256-<版>.zip`。
- 256 でも、pak128 の絵（`src/<名前>.png`）か dat がある物は全部描き・組む。物を足したときに表へ書き足さなくてよい（#301 で、組む物の表 `SCALED_SHEETS` から、組まない物の表 `catalog.SCALED_EXCLUDED`（名前 → 理由。今は空）に裏返した）。256 の絵が合わない物（画素で書いた値を大きさに合わせていない物など）だけをそこへ書く。`render.py` は、対象を渡さなければ `catalog.SCALED_TARGETS`（`src/` の絵のある物から、壁の単独の名前と組まない物を除いた物）を描き、`SCALED_EXCLUDED` の物を 256 で描こうとすると止まる。`ami_dat.py` は `SCALED_EXCLUDED` の dat だけを 256 では書かずに飛ばす（`put`）。`check_scaled.py` が、`src256/` の dat の名前が `src/` の dat と（組まない物を除いて）同じかを CI で確かめる（足した物の 256 の dat のコミット忘れを止める）。`build.py` は `BUILD_SKIP_MISSING=1` で、絵のシートが無い dat を組まない（256 の PNG は生活道路だけをコミットするので、CI はこれで絵のある物だけを組み、`check.sh` の 256 の dat_linter も絵のある dat だけに掛ける。`build.py --stage-sheeted <フォルダ>` が絵のある dat とシートをコピーする）。雪（シートの行 4〜7 と dat の `[1]`）は同じ作りで描く。ゲームで確かめたのは、線路の高架・架線つきの壁の坂の降雪側（#261 の C）だけで、路面表示・標識・歩道・路面軌道・道路の高架・運河・踏切・車庫・モノレールの雪は確かめていない。整数でない倍率は #261 の範囲外。分岐の追加画像（ex）は、全部のシートがある 256 でも `build.py` が継ぎ足す（`BUILD_SKIP_MISSING=1` で提供用の dat のシートが欠けているときは継ぎ足さない）。全部のシートを描いた手元で `CHECK_256_FULL=1 bash addons/ami/check.sh` が通る（#261 の D）。`SCALED_EXCLUDED` の名前の実在と理由、`src/` の名前が `ami_` で始まること、`src256/` と `src/` の dat の名前が（組まない物を除いて）同じことは、`check_scaled.py` が、256 の PNG が無い CI でも見る。`SCALED_TARGETS` が `render.py` の `SHEETS` のキーであることは、Blender（bpy）が要るので CI では見ず、256 で `render.py` を流すときに止める（`src/` に `SHEETS` に無い絵が紛れると、そこで初めて落ちる）。`SCALED_EXCLUDED` に物を入れるときは、その物を指す dat（分岐の追加画像の提供用 `ex_donors.dat`・twin の壁・踏切の dat）が 256 に残らないかも確かめる（今は空なので未確認）。256 で描く順序は、道路 → 踏切、運河 → 水路の踏切、跨座式の地上の版 → そのトンネル、狭軌の 60 → そのトンネル（後の物が前のシートの絵・アイコンを読む）。`SCALED_TARGETS` の並びは名前順で、描く順は `render.py` の `SHEETS` の登録順が決める。
- 256 で組む手順（アドオンのディレクトリで）:

```powershell
$env:SHEET_PAK_SIZE = "256"
python -X utf8 blender/ami_dat.py                                           # src256/ に dat
python -X utf8 ..\..\tools\blender\render_parallel.py ami_road_local      # src256/ にシート（アイコン・カーソルも。約 2 分）
python -X utf8 build.py                                                    # dist256/ に pak（makeobj pak512。警告があれば止まる）
python -X utf8 release.py --version alpha.1 --paks ami_road               # work/release/ami-256-alpha.1.zip
Remove-Item Env:SHEET_PAK_SIZE
```

  zip は 256 の pak（`ami_road.pak`）だけを直下に入れる（readme・許諾・一覧は入れない。pak256 の `tools/fetch_ami.py` は zip の中の `.pak` を全部取る）。許諾の文は `release/license.txt`（CC BY 4.0）で、pak256 が写しを持つ。pak128 の zip（`ami-<版>.zip`）とは名前が違い、混ざらない。
- 256 のシートの検査（#261）: 256 の PNG は、dat と生活道路だけをコミットする（生活道路はシートと一緒に `icons.py` が書いたセルの控え `ami_road_local.icon_cells.txt` もコミットする。#330。全部を描くと約 3.5 倍の大きさで、描き直すたびにリポジトリが増える。ユーザーの決定、2026-11-25）。ほかの物の 256 のシートは、手元で描いて検査し、結果を PR に書く。`check_icons.py`・`check_cells.py`・`check_crossing.py`・`check_depot.py`・`check_embankment.py` は、環境変数 `SHEET_PAK_SIZE=256` を付けると、`src256/` を 256 のセル（512px）・座標で見る（引数にフォルダを渡せば、ほかの場所のシートも見る）。`check_cells.py` は、シートの大きさがセルの倍数でないとき（128 のシートを 256 で見たなど）も落ちる。`CHECK_SKIP_MISSING=1` を付けると、`check_icons.py`・`check_cells.py`・`check_snow_edge.py` は絵のシートが無い物を飛ばす（CI の 256 の検査はこれで生活道路だけを見る）。全部のシートを描いた後は、`CHECK_256_FULL=1 bash check.sh` で、5 つの検査（と `check_snow_edge.py`）を全部の物に厳しく流す（`check.sh` の「256 のシートの検査」）。検査の道具の確かめは、128 の `src/` を最近傍で 2 倍にして（dat の位置合わせも 2 倍に）256 で流し、128 と同じ結果になることで行った（車庫の六角形だけは、2 倍の縁の階段で外の画素が出るので半画素の許しを付けて確かめたが、本物の 256 のシートでは許し無しで 96 枚とも通った。#261 の D）。
- 雪の基盤の版の下の端（#366）: `check_snow_edge.py` が、道路の地上の基盤の版（`ami_road_<種類>_base_<版>`）の雪の行で、タイルの下の端の暗い列（路面の板の切り口が雪の下に出た点線。#360）を数え、同じ種類の通常の版（`ami_road_<種類>`）の同じセルより多いセルがあれば落ちる。数え方はファイルの先頭。`check.sh` は 128 と 256 で流す（CI の 256 は基盤の版の PNG が無いので何も見ない。`CHECK_256_FULL=1` か `SHEET_PAK_SIZE=256 python -X utf8 check_snow_edge.py` で見る）。
- 道路のカーブのつなぎ（#378）: `check_curve_join.py` が、道路の dat（`ami_road_*.dat`）ごとに温帯と雪のカーブ 4 つを隣の直線と本体と同じ並びに重ね、タイルの辺に透ける画素（地面が見える点線）を数え、1 つのつなぎで 3 画素以上なら落ちる（タイルの菱形の頂点の近くは数えない。数え方はファイルの先頭）。`check.sh` は 128 と 256 で流す。CI の 256 は生活道路の通常の版だけを見る（基盤の版の 256 の PNG はコミットしない）ので、#378 が出た 256 の基盤の版は `CHECK_256_FULL=1` か `SHEET_PAK_SIZE=256 python -X utf8 check_curve_join.py`（シートの無い dat が落ちるので、生活道路だけ描いた手元は `CHECK_SKIP_MISSING=1` を付ける）で見る。128 では直す前の絵がちょうど 3 画素で、しきい値の余裕が無い。
- 256 のゲームでの確認: 地面は pak128 を 2 倍にした `addon_check/pak256poc/`（`-objects pak256poc/`。作り方は親の `AGENTS.md`）。`ingame/game_lib.sh` に `PAKSET=pak256poc`・`PAKSET_SRC=<pak256poc の元>`（1.6GB なので写さずジャンクションにする）を渡すと、その pak と `addons/pak256poc/` で起動する。例: `GAME_DIR=<addon_check> PAKSET=pak256poc PAKSET_SRC=E:\addon_dev\pak256\work\pak256poc PORT=47200 PAK=dist256/ami_road.pak NUT=ingame/road_sample.nut ROAD_NAMES=ami_road_local CLIMATES=temperate bash ingame/game.sh`。撮る・閉じるも同じスクリプト（`PAKSET`・`PAKSET_SRC` を同じ値で渡す）。

## 導入と検証

ゲームでの確認は、検証用のフォルダ（`addon_check`。親フォルダの `AGENTS.md`）の写しを OTRP（v64）で起動し、MCP のスクリプトを流す。`ingame/` のスクリプトの起動・停止は `ingame/game_lib.sh` の共通の関数で、実行ファイル・地図・設定の既定は v64（`sim-WinGDI64-OTRPv64.exe`・`flat_512_left_v64.sve`・`settings.xml.v64`）。`GAME_DIR` は必ず渡し（絶対パスを既定に持たない）、`PORT` は作業ごとに割り当てられた範囲の中を渡す。
makeobj は本家と同じもの（60.12）なので、ふだんの確認は OTRP だけで行う。配る pak の本家 125.0.1 での読み込みは、配る前にユーザーが確かめる（スクリプトが使えない。ACCEPTANCE の 6-4）。

```bash
GAME_DIR=<検証用のフォルダ> PORT=<ポート> bash ingame/sample_check.sh   # 閉じるのは PORT=<ポート> STOP=1 を付けて同じスクリプト
# 高速線の見本は TRACK=ami_rail_slab を前に付ける
```

- `dist/ami.pak` をゲームの `addons/pak128/` に写し、OTRP を MCP つきで起動して `ingame/sample.nut` を流す。見本は温暖側 (20,20) と降雪側 (276,20) に敷く。敷く軌道の種類は `sample.nut` の先頭の `TRACK`（通常の版の way の名前）で選ぶ。基盤・高架・橋・トンネルの名前はそこから導く
- 見本は way の全部の絵を、周りとつながった形で出す（行き止まり・1 タイル・斜め・輪と十字・坂・急坂・近い斜め・十字の分岐の固定・分岐の自動選択 8 通り。区画の表は `sample.nut` の冒頭）。降雪側は敷いた後に一帯を降雪に塗り直す
- 返り値の `[check]` の行に、近い斜めの分け合うタイルが way 1 本か（`two_ways=false` なら近い斜めの絵が使われている）と、分岐の絵を固定する道具があるかを出す
- 基盤の版は `WALLED` に way と壁の組で足す（同じ区画の並びで、壁を同じ経路に重ねる。近い斜めの区画 G は敷かない）。複線と壁の組（輪・近い斜め・行き止まりの並び）は区画 W。架線つきの壁は `CATENARY`（区画 W の後に同じ並びで 4 版）と区画 WE（区画 W と同じ並びで、壁を架線つきの版にしたもの）で、`[check]` の行の way の名前の後ろの `elec` は電化されていること。`[check]` の行には、区画 W・WE の角と分け合うタイルの way と壁の名前も出す（`(2)` は way が 2 本）
- 高架は地上の区画の東 80 に敷く（`sample.nut` の `ELEVATED`）。区画の並びは基盤の版と同じで、高架の 4 版に壁の 4 版を重ね、真下に橋脚の way を敷く。その南に区画 WV（区画 W の並びを高架で）・WVE（区画 WE の並びを高架で）・高架に架線つきの壁の single・区画 J（高架と地上のつなぎ目）。`[check]` の行の高架の名前の後ろの ` / ami_pier_rail` は、真下の地面の橋脚の way（`(2)` は 2 本）
- 撮るのは `PORT=<ポート> bash ingame/sample_capture.sh`（`work/sample/ に温暖側・降雪側の区画ごと）。レイアウト検証用モードの pak は `PAK=work/layout/dist/ami.pak` で入れ、`OUT=work/sample_layout` で撮る。終わったら `dist/ami.pak` を入れ直す
- 全区画をまとめて撮るときは `GAME_DIR=<検証用のフォルダ> TRACK=ami_rail_slab bash ingame/sample_parallel.sh`。8 台のゲームを `work/parallel/` の写しで起動し、見本を敷いて撮り、閉じる。208 画面が準備込みで約 40 秒。`sample_check.sh` は要らず、`GAME_DIR` には書き込まない。台数は `JOBS`
- pak128 標準の線路（`Rail_160_Tracks`）とのつなぎ目と、坂・急坂でのレールの寄りは `GAME_DIR=<検証用のフォルダ> PORT=<ポート> bash ingame/seam_slope_check.sh` で測る（#62 で足した）。見本は `ingame/seam_slope.nut`（線路の種類ごとに、東西・南北・斜め・坂のつなぎ目と、急坂・1 段の坂の十字）。ゲームは `work/seam_game/<PORT>/` の写しで起動し、`GAME_DIR` には書き込まない。MCP のクライアントの場所は、ほかの `ingame/` のスクリプトと同じく `ingame/mcp_client.sh` で決める。読み方は `tools/blender/seam_judge.py`・`slope_measure.py` の冒頭。在来線にも、つなぎ目の斜めの 1 か所（草 1px）と、十字の坂のタイル（急坂 3・1 段の坂 2）で寄りの NG が出る（2026-11-21 の値は記録 [2026-11-21_ami-rail-concrete](../../docs/records/2026-11-21_ami-rail-concrete.md)）
- 分岐の追加画像（#57）は `GAME_DIR=<検証用のフォルダ> PORT=<ポート> bash ingame/ex_check.sh` で確かめる。`dist/ami.pak` を入れて起動し、`ingame/ex_sample.nut` を流して開いたままにする。見本は線路の種類（`WAYS`。在来線・弾性まくらぎ直結軌道・高速線・路面軌道と、在来線の基盤 4 版に架線つきの壁）ごとに、Y字分岐と三方分岐を根元の 4 向きで敷き（温暖側 (150,20)、降雪側は x + 256、区画は南へ 40 ずつ）、固定の道具で 26〜35 番に固定した T字・十字と、何もしない T字・十字を並べる。`[check]` の行は、自動で選ばれた絵が固定と同じなら `ok`、通常の絵のままなら `plain`、違えば `got/want`。撮るのは `PORT=<ポート> OUT=work/ex/after bash ingame/ex_capture.sh`
- 壁つきの線の間の渡り線（#101）は `GAME_DIR=<検証用のフォルダ> PORT=<ポート> bash ingame/crossover_wall.sh`。ゲームの写し（`work/crossover_game/<PORT>/`）に `dist/ami.pak`（`PAK` で替えられる）と iss の線路・架線の pak を入れて起動し、`ingame/crossover_wall.nut` を温暖側 (20,20) に流す。AMI の壁・架線つきの壁・iss の架線の 3 組を、線の並び（back+front・back+center・center+front・3 本）と敷き方（本線を敷き直す・渡り線にも壁・上の線の版で渡り線・通常の版で渡り線・壁の後に渡り線を敷いてから本線を敷き直す）ごとに敷く。続けて `SNOW=1`（降雪側に同じ見本）・`CAPTURE=1`（撮る。`SNOW=1` と合わせると降雪側）・`STOP=1`（閉じて写しを消す）を渡す
- iss の版ごとのカーブ・分岐の絵と並べる検討（#88。決定は「入れない」で、本番の pak には関わらない）は `GAME_DIR=<検証用のフォルダ> PORT=<ポート> bash ingame/curve_switch_study.sh`。ゲームの写し（`work/study_game/<PORT>/`）に `dist/ami.pak` と iss の線路の pak を入れて起動し、`ingame/curve_switch_study.nut` を流す。続けて `CLASSIFY=1`（分岐のタイルの自動の絵を読む）・`TRAIN=1`（`ingame/curve_switch_train.nut` で列車を走らせ、渡り線の絵を読む）・`CAPTURE=1`（撮る）・`STOP=1`（閉じて写しを消す）を渡す。結果は記録 `docs/records/2026-11-21_ami-curve-switch-variants-study.md`
- 同じポートでゲームが動いていると、`sample_check.sh` は止まる（他のゲームに見本を流さない）。閉じるのは自分で起動したゲームだけ（`STOP=1`。写しの中の exe だけを止める）
- 斜めと行き止まりの角の壁の暗い縦線を消した前後は `docs/wallseam63_*.png`（`C_*` は区画 C の下の端の角、`B_*` は区画 B の T字・十字の角。上が前|後の画面の切り抜き、下が拡大。#63。経緯は記録 [2026-11-21_ami-wall-diag-end-seam](../../docs/records/2026-11-21_ami-wall-diag-end-seam.md)）
- 確認画像は `docs/`。在来線の通常の版は `rail_ballast_*.png`（温暖側・降雪側の見本、レイアウト検証用モードの見本、行き止まりの拡大、T字・十字・分岐のセル、道床の色の前後。2026-11-17）。基盤の版と壁は `rail_base_*.png`（区画 W1〜W3 と、back・front の輪と十字。`layout` はレイアウト検証用モード。`fix_*` は継ぎ目を直した前後の拡大（`_before` が前）。2026-11-17）
- 架線つきの壁は `rail_catenary_*.png`（区画 SE（single）・BE（back）の輪と十字、SE の坂と急坂（`SE_DE`）、区画 WE1（複線の輪）・WE2a（近い斜めの複線）・WE3（行き止まりの並び）、降雪側の WE1（`snow_WE1`）、一部だけ電化した線の境（`upgrade`）、pak128 の `classic_catenary`（上）と並べた直線（`vs_pak128`。画面を 2 倍に拡大）、斜めの線を隣のタイルに並べた 3 本並び（上）と複線（下）の梁のつながり（`diag_beams`。ユーザーの確認用の保存データの (40,346) の辺り。2 倍）、近い斜めの複線で、`twin_catenary` を置く前の分け合うタイルの梁のはみ出しと線の間の柱（`close_pair`。同じ保存データ。2 倍。置いた後は `WE2a`）。`layout` はレイアウト検証用モードで、線を上下 2 本・1px にしてハンガーを足す前の絵（柱・梁の配置とつながりは今と同じ）。2026-11-18）
- 高架と橋脚は `rail_elev_*.png`（区画 VS（single）・VB（back）の輪と十字、VS の行き止まり・1 タイル・坂（`VS_AFC`）、区画 WV1（複線の輪）・WVE1（架線つきの複線の輪）・WV2a・WV2b（近い斜めの複線。画面で縦向き・横向き）・WV3（行き止まりの並び）、区画 J（高架と地上のつなぎ目）、降雪側の VB（`snow_VB`）。`WV2b_before` は斜めの躯体の切り口を直す前で、奥の線の躯体の切り口が手前の線の床の上に三角に出ていた。`layout` はレイアウト検証用モードで、切り口を直す前の絵（配置とつながりは今と同じ）。`pier_cross_*` は高架の下を横切る道路（`road`）と地上の線路（`pier_first` は橋脚の後に線路、`rail_first` は線路の後に橋脚、`split` は線路のタイルを飛ばして橋脚を 2 本に分けたもの。`split` は高架を敷かず橋脚だけ。どれも躯体を浅くする（`ELEV_BODY_D` 1.0 → 0.25）前の形）。2026-11-18）
- 門型の橋脚は、高架の区画のさらに東 80（`sample.nut` の `lay_gate`。原点 (ox + 160, oy)）に、高架の single の区画・区画 WV の並び・道路の区画 R（`Road_050` を高架の直下に並行して通し、十字で横切る。斜めの道路の上の斜めの高架）を、真下の橋脚を門型にして敷く。`GATE_ONLY` を true にすると温暖側の門型の区画だけを敷く。撮るのは `sample_capture.sh` の `G*` の場所
- 門型の橋脚は `rail_elev_gate_*.png`（`AFC`・`B`・`DE`・`IH` は高架の single の区画、`WV1`〜`WV3` は区画 WV の並び、`R1`（南北の高架の下の道路と十字。`R1_zoom` は拡大）・`R2`（東西）・`R3`（斜め）。`layout_*` はレイアウト検証用モードで、梁を躯体に食い込ませる前の高さ（配置とつながりは今と同じ）。`bus_parallel`・`bus_cross` は 2 階建てバスが高架の下の並行の道路と横切る道路を通るところ。2026-11-18）
- 橋とトンネルは、門型の橋脚の区画の南（`sample.nut` の `lay_bt`。原点 (ox + 160, oy + 130)）に、平地から立ち上がる橋（B1。東西・南北）・坂から始まる橋（B2。1 段・2 段）・高架と橋のつなぎ目（B4）・壁だけのトンネル（T1。東西・南北）・架線つきのトンネル（T2）・複線のトンネル（T3）を敷く。`BT_ONLY` を true にすると橋とトンネルの区画だけを敷く（写しを作って `NUT=` で渡す）。`[check] BT` の行は、橋の床・坑口・トンネルの中のタイルの way（`d` の後ろは向き）と壁、電化（`elec`）、橋かトンネルか。撮るのは `sample_capture.sh` の `BT_*` の場所
- `sample_check.sh` は `sample.nut` をコマンドラインの引数で渡すので、Windows のコマンドラインの長さの上限（32,767 文字）に収まるよう、行頭のコメント・字下げ・空行を除いて渡す（橋とトンネルを足して 34,230 バイトになり、そのままでは `Argument list too long` で渡せなかった。2026-11-18）。行頭の空白と `//` で始まる行を消すので、`sample.nut` に複数行の文字列（`@"..."`）を足すと中身が変わる（足すときは 1 行の文字列にする）
- 橋とトンネルは `rail_bridge_*.png`・`rail_tunnel_*.png`（`B1`（平地から立ち上がる橋。拡大）・`B2`（坂から始まる橋の 1 段・2 段）・`B4`（高架と橋のつなぎ目。拡大）・`snow_B2`（降雪側）・`T1`（壁だけのトンネル）・`T2`（架線つき。拡大）・`T3`（複線）、`ramp_before`・`ramp_after`（坂の低い側の灰色の帯を直す前と後。ユーザーの確認用の保存データの (190,184) の辺り。拡大）、`ramp_layout_before`・`ramp_layout_after`（同じ所のレイアウト検証用モード）。`rail_tunnel_layout_*` はレイアウト検証用モード。2026-11-18）
- 保存・ロードやダイアログの見た目はスクリプトで確かめられないので、ユーザーが見る
- 配る pak の読み込みは `GAME_DIR=<検証用のフォルダ> PORT=<ポート> PAKS="<pak>..." bash ingame/beta_check.sh`。`work/beta_game/<PORT>/` の写しに `PAKS`（既定は `build.py` の `KINDS` の種類別の pak 全部から旧描画位置の `ami_rail_old.pak` を除いた 7 つ（ラインナップが増えても追従する。#177）。旧は新と同じ橋・高架に載る way が混ざるので既定に入れず、`PAKS=dist/ami_rail_old.pak` で別に確かめる。zip を確かめるときは `release.py --extract` で展開した pak）だけを入れて起動し、`src/*.dat` の全部の物（way・way-object・橋・トンネル・踏切・車庫・操車場・道路標識）を 1 つずつ道具で敷いて（行は 1 列に収まらなければ東へ列を増やす）、タイルの物の名前を読む（`ingame/beta_check.nut`）。先頭が `ok <数> items` なら全部敷けた。続けて、読んだ AMI の pak と、ログ（`-debug 3`）の AMI の物の警告を出す（ACCEPTANCE の 6-3）

道路の見本は線路と別のゲームで敷く（`sample.nut` はコマンドラインの長さの上限に近いので、道路の区画を足さない）:

```bash
GAME_DIR=<検証用のフォルダ> NUT=ingame/road_sample.nut OUT=work/road_sample bash ingame/sample_parallel.sh
# 1 台で敷いて開いたままにするなら NUT=ingame/road_sample.nut PORT=<ポート> bash ingame/sample_check.sh（撮るのは PORT=<ポート> NUT=ingame/road_sample.nut OUT=work/road_sample bash ingame/sample_capture.sh）
```

- 絞って敷く（#208）: `ingame/game.sh` に `ROAD_NAMES`（敷く道路。空白区切り。例 `"ami_road_expressway"`）・`CLIMATES`（`temperate` と `snow`。空白区切り）を渡すと、その種類・気候だけ敷く（game.sh が `road_sample.nut` の `ROADS`・`ORIGINS` の行を置き換える。既定は全部）。降雪だけでも塗り直す。`SETTINGS` で、写しに入れる GAME_DIR の設定ファイルを替えられる（v64 は `SETTINGS=settings.xml.v64`）。例: `ROAD_NAMES=ami_road_expressway CLIMATES=temperate GAME_DIR=<検証用のフォルダ> PORT=<ポート> NUT=ingame/road_sample.nut bash ingame/game.sh`。`sample_check.sh`・`sample_parallel.sh` には効かない。区画の名前での絞り込みは無い。絞ると残った道路は先頭の枠（南へのずれ 0）に詰まって敷かれるので、`ROAD_SPOTS` の `GE_*`・`EX_*` の座標とはずれる（撮るなら `SPOTS` を自分で指定する）。`road_sample.nut` 以外の NUT に渡すと止まる。`SETTINGS` は #208 の測定のために足した（v64 の設定で起動する）。v64（`flat_512_left_v64`）で、高速道路・温暖だけは起動から敷設まで 14.8 秒、全部は 30.8 秒（1 回ずつ）
- `ingame/road_sample.nut` は道路 3 種（`ROADS`）を、温暖側 (20,20) と降雪側 (276,20) に 30 ずつ南へずらして敷く（生活道路・一般道路・高速道路の順）。区画は線路の見本と同じ A・F・C・B・D・E・G に、分岐の自動選択（H。2 本の道路を隣り合わせに並べて渡り口でつないだ形。南北と東西）、分岐の絵の固定（I。T字 4 種と十字を選択 2・1 の順に）、pak128 標準の `Road_050` とのつなぎ目（K）、隣り合う十字（L）。表は `road_sample.nut` の冒頭
- `[check]` の行: 近い斜めの分け合うタイルが way 1 本か（`two_ways=false`）と、区画 H（自動選択の `auto`）・I（固定の `pin1`・`pin2`）・L（隣り合う十字の `west`・`east`）の絵。値は `way_x.get_image_id()`。判定は `road_sample.nut` の `SWITCH_IMAGES`（`ami_dat.py` の `ROAD_SWITCH_IMAGES` と同じにする）で変わる。今（真。v64 の仕様）は、H（隣が T字・十字）の自動選択（`auto`）が通常の T字と同じで、固定の `pin1`・`pin2` が通常とも互いとも違えば `ok`、L の十字が通常の十字なら `ok`、M（枝の隣がカーブの T字）の自動選択が `pin1` なら `is1`（`pin2` なら `is2`、通常なら `plain`）

道路を何本か並べた交差点の組み合わせ（2×4〜6×6）は別の見本で敷く（温暖側だけ）:

```bash
SEASONS=temperate:20:20 GAME_DIR=<検証用のフォルダ> NUT=ingame/road_junction_sample.nut OUT=work/junction bash ingame/sample_parallel.sh
```

- `ingame/road_junction_sample.nut` は道路 3 種を (20,20) から 22 ずつ南へ、組み合わせ 8 つ（南北の本数 × 東西の本数が 2×1・1×2・3×1・1×3・2×2・2×3・3×2・3×3）を東へ 12 ずつ敷く。`[check]` の行に、十字のタイルごとに通常の十字（`nsew`）か T字の「2」（`nse2` など）かを出す（判定は、同じ見本の中で固定の道具で固定した T字の絵と比べる。分岐の絵の無い今は、どれも `nsew`）。撮る場所は `sample_spots.sh` の `JUNCTION_SPOTS`
- `NUT` に `road_sample.nut` を渡すと、撮る場所は `sample_spots.sh` の `ROAD_SPOTS`（`LO_*`・`GE_*`・`EX_*`）になる。`sample_parallel.sh` は全部敷けたときも 1 台目の報告（`[check]` の行）をログ（`work/parallel/<ポート>.log`）と画面に出す
- 道路の確認画像は `road_*.png`（2026-11-19）。`LO`・`GE`・`EX` は生活道路・一般道路・高速道路。`B`（輪と十字）・`AFC`（行き止まり・1 タイル・斜め）・`DE`（坂と急坂の十字）・`G1`（近い斜め）・`HV`・`HH`（分岐の自動選択。2 本並べた道路の渡り口）・`I0`（T字 nse の固定の 1・2）・`I4`（十字の固定の 1・2）・`K`（pak128 標準の `Road_050` とのつなぎ目）、`GE_L_zoom`（隣り合う十字に、前の T字の形の「2」の絵が出たところ。3 倍）、`*_priority_*`（優先道路の十字）・`GE_4x4_cross_zoom`・`GE_6x6_cross_zoom`（隣り合う十字。記録 [2026-11-20_ami-road-switch-design](../../docs/records/2026-11-20_ami-road-switch-design.md)）、`snow_*` は降雪側、`layout_*` はレイアウト検証用モード、`EX_dash_zoom`（直線と斜めの継ぎ目の破線。4 倍）・`EX_slope_zoom`（坂と平地の継ぎ目。4 倍。この 2 枚は、直線と坂の破線が 1 本抜けていたときのもの）、`EX_dash_*`（2026-11-20 に破線の抜けを直した後。`sheet_before`・`sheet_after` はシートの直線のセルを 3 枚つないだもの、`straight_ew`・`straight_ns`・`slope`・`close_diag` はゲームの画面の 4 倍）

道路の壁・基盤の版・高架・橋脚・橋・トンネルの見本も別のゲームで敷く:

```bash
GAME_DIR=<検証用のフォルダ> NUT=ingame/road_struct_sample.nut OUT=work/struct bash ingame/sample_parallel.sh
```

- `ingame/road_struct_sample.nut` は道路 3 種を、温暖側 (20,20) と降雪側 (276,20) に 30 ずつ南へずらして敷く。1 種ずつ東へ、地上の壁（通常の版に `single` の壁。近い斜めの区画 G は `back`・`front`）・地上の複線（基盤の版と同じ版の壁。輪 W1・行き止まりの並び W3・近い斜め W2）・高架（`single` と壁と真下の橋脚。隣り合う十字 L）・高架の複線（WV1〜WV3）・分岐の絵の固定（IB は基盤の版、IV は高架）・橋とトンネル（B1・B2・B4・T1・T3）・橋脚のつながり（P1 は `Road_050`、P2 は AMI の道路、P3 は地上の線路）。表は `road_struct_sample.nut` の冒頭
- `[check]` の行: 区画 G の分け合うタイルの way と壁（way 1 本で向きが 15 なら、通常の版の近い斜め）、複線の角と近い斜めの分け合うタイル（`(2)` は way 2 本で、壁が `twin` になっているか）、橋の床・端と坑口・トンネルの中の way と壁（`bridge`・`tunnel`）、橋脚の区画の地面の way（` / ` の後ろが橋脚の way と道路）、区画 IB・IV で固定した絵の番号（`get_image_id`）
- 撮る場所は `sample_spots.sh` の `STRUCT_SPOTS`（種類ごとに `LO_*`・`GE_*`・`EX_*`）。82 か所 × 温暖側・降雪側で 164 画面
- 確認画像は `road_struct_*.png`（2026-11-19。一般道路の `WA_B`（通常の版に壁を重ねた輪と十字）・`WP`（基盤の版の複線の輪）・`V_B`（高架の輪と十字）・`VP2`（高架の近い斜めの複線）・`B1`（平地から立ち上がる橋）・`B4`（高架と橋のつなぎ目）・`P1`（`Road_050` の上の橋脚）、高速道路の `T1`（トンネル）、降雪側の `snow_GE_V_B`）と、判断の材料の拡大（`road_wall_close_plain_zoom`・`road_wall_close_base_zoom`・`road_base_pair_corner_zoom`・`road_bridge_girder_zoom`・`road_elev_L_zoom`）、レイアウト検証用モードの拡大（`road_layout_pair_corner_plain`・`road_layout_elev_pair_corner_before`・`_after`・`road_layout_elev_twin_zoom`）。高速道路の中央線の破線の抜けを直した後（2026-11-20）の 4 倍は `road_EX_dash_bridge_zoom`（橋と坂の継ぎ目）・`road_EX_dash_tunnel_zoom`（トンネルの口の前）・`road_EX_dash_elev_zoom`（高架の複線）

路面軌道の見本も別のゲームで敷く:

```bash
GAME_DIR=<検証用のフォルダ> NUT=ingame/tram_sample.nut OUT=work/tram bash ingame/sample_parallel.sh
```

- `ingame/tram_sample.nut` は、線路の見本と同じ区画（A・F・C・B・D・E・G・I・H）を、土の上と、AMI の道路 3 種・pak128 標準の `Road_050` の上（道路を先に敷いて同じ経路に重ねる）に、温暖側 (20,20) と降雪側 (276,20) で 30 ずつ南へずらして敷く。土の上の区画には、橋脚とのつながりの区画 P もある。表は `tram_sample.nut` の冒頭
- `[check]` の行: 区画 G の分け合うタイル（道路の上では道路と路面軌道で `two_ways=true` になる）、区画 I の固定の絵、区画 H の自動選択の絵（通常の T字と同じなら `(plain)`）、道路の上の区画で道路が残っているか（`road=`）、区画 P のタイルの way。判定は `tram_sample.nut` の `SWITCH_IMAGES`（`ami_dat.py` の `TRAM_SWITCH_IMAGES` と同じにする）で変わる
- 撮る場所は `sample_spots.sh` の `TRAM_SPOTS`（`GR`・`LO`・`GE`・`EX`・`ST` は土・生活道路・一般道路・高速道路・`Road_050` の上）。47 か所 × 温暖側・降雪側で 94 画面
- 確認画像は `tram_*.png`（2026-11-20）。`GE_B`・`EX_B`・`ST_B`・`GR_B` は輪と十字（一般道路・高速道路・`Road_050`・土の上）、`GE_B_zoom` はその十字・カーブ・T字の 4 倍、`GE_AFC`・`GR_AFC`（行き止まり・1 タイル・斜め）、`GE_DE`（坂と急坂）、`GR_G1`・`GE_G1`（近い斜め）、`GR_I`（十字の固定の 1・2）、`GR_H0`（分岐の自動選択）、`switch_H0_zoom`（左が分岐の絵あり、右が無し。5 倍）、`GR_P`（橋脚の列を横切る）、`snow_*` は降雪側、`layout_*` はレイアウト検証用モード

歩道の見本も別のゲームで敷く:

```bash
GAME_DIR=<検証用のフォルダ> NUT=ingame/sidewalk_sample.nut OUT=work/sidewalk bash ingame/sample_parallel.sh
```

- `ingame/sidewalk_sample.nut` は、道路 4 種（AMI の 3 種と pak128 標準の `Road_050`）ごとに 14 ずつ南へ、温暖側 (20,24) と降雪側 (276,24) に敷く。区画は交差点の四隅（R）・広場と 1 タイル（Q）・坂（S）・急坂（T）・斜めの道路（D）・道路と運河の横切り（X）。表は `sidewalk_sample.nut` の冒頭
- `[check]` の行: 歩道を敷いた後も道路の向きと絵が変わらないか（`road=same`）、歩道の waytype（3 が `water`）、交差点の隣の歩道の向き（`corner(5,1)=9` は西と北）、区画 X の横切ったタイル（`objs` の 29 が踏切、`canal_tile` は運河に置き換わったか）
- 撮る場所は `sample_spots.sh` の `SIDEWALK_SPOTS`（`LO_*`・`GE_*`・`EX_*`・`ST_*`）。24 か所 × 温暖側・降雪側で 48 画面
- 確認画像は `sidewalk_*.png`（2026-11-20）。`GE_R`・`ST_R`・`LO_EX_R`（交差点の四隅。`ST` は `Road_050`）・`GE_R_zoom`（道路との境の 4 か所。5 倍）・`GE_Q`（広場と 1 タイル）・`GE_ST`（坂と急坂）・`GE_D`（斜めの道路）・`GE_X`（横切り）、`snow_GE_R` は降雪側、`layout_*` はレイアウト検証用モード

歩道の種類・高架の歩道・歩道の柵の見本（#119）は、1 台のゲームを開いたままにして敷いて撮る:

```bash
GAME_DIR=<検証用のフォルダ> PORT=47300 NUT=ingame/sidewalk_struct.nut bash ingame/game.sh
PORT=47300 OX=276 NUT=ingame/sidewalk_struct.nut bash ingame/game.sh RUN   # 降雪側
PORT=47300 OUT=work/sw119 SPOTS="F1:22:37 E1:25:48" bash ingame/game.sh CAPTURE
PORT=47300 bash ingame/game.sh STOP
```

- `ingame/game.sh` は、`work/game/<PORT>/` に検証用のフォルダの写しを作って起動する（`GAME_DIR` には書き込まない）。`RUN` で動いているゲームに見本を流し、`CAPTURE` で場所ごとに撮り、`STOP` で閉じて写しを消す。`OX` を渡すと、見本の行頭の `local OX = <数>;` を置き換える
- `game.sh` は、起動・`RUN`・`CAPTURE`・`STOP` のどれも `PORT` が要る（無いと何もせずに止まる。閉じるときも、起動したときと同じ `PORT` を渡す）。ほかの起動スクリプトと同じ形の環境変数 `STOP=1`・`RUN=1`・`CAPTURE=1` も、引数と同じに扱う（#326）。`before_after.sh` の `STOP=1` も `PORT` を要る（既定の 47200 で閉じに行かない）
- ゲームを起動するスクリプト（`game.sh`・`sample_check.sh` など）の出力を、パイプ（`| tail`・`| cut` など）でつながない。子のゲームがパイプを握り続けて、コマンドが終わらない。出力はファイルに向けて（`> work/x.log 2>&1`）、終わってから読む
- 相対パスの `ingame/…`（`NUT` など）は、アドオンのディレクトリで使う
- 前後の撮り方、前の pak の作り方、作業の注意（片付け・ブランチへの道具の取り込み）は、スキル [way-addon-build](../../.claude/skills/way-addon-build/SKILL.md) の [4 章](../../.claude/skills/way-addon-build/SKILL.md#4-確かめ方) と [6 章](../../.claude/skills/way-addon-build/SKILL.md#6-作業の注意)
- `ingame/sidewalk_struct.nut` は、温暖側 (20,20) と降雪側 (276,20) に、舗装の種類（P）、地上の柵（F1 道路の両脇・F2 L字・F3 広場・F4 坂・F5 T字）、高架（E1 高架の道路の両脇・E2 地上の道路を横切る・E3 L字）を敷く。表は `sidewalk_struct.nut` の冒頭
- `[check]` の行: 高架の歩道のタイル（高さ 2）の way と柵、地上の歩道の way と柵
- 確認画像は `sidewalk119_*.png`（2026-11-21）。`P_*` は舗装の種類、`F_*` は地上の柵、`E_*` は高架、末尾が気候（`temperate`・`snow`）

塗りを実装する前に、レイアウト検証用モード（部品ごとに画像で見分けやすい単色で塗る）で、部品の配置とタイルどうしの接合を確かめる（[ADR 0005](../../docs/adr/0005-ami-render-tool-conventions.md)）。

## 画面を出さない本体での読み込みの検査（#236）

`check.sh` の最後（pak を作った後）で、画面を出さない OTRP 本体（Makefile の `BACKEND=posix`）に配る pak を読ませ、出力の文字列で失敗を見つける（`tools/ci/check_pak_load.py`。調査と判定の表は記録 [2026-11-24_headless-pak-load](../../docs/records/2026-11-24_headless-pak-load.md)）。

- 種類別の pak（`dist/ami_*.pak`）を全部一緒に読み、全部入りの `ami.pak` は単独で読む（一緒に置くと名前が重複する）。pakset は本体の `tests/simutrans-test-base.zip`。所要は 1 回 3〜5 秒
- 失敗にするのは、`FATAL ERROR`（参照切れ・ROOT の大きさ）・`ERROR:` で始まる行（空・壊れたファイルなど。画面がないことを知らせる `modal_dialogue` の行は除く）・`skipping unknown`・`is overlaid`・`Reading addon object data failed`・`sent query:`（使用状況の送信）など。時間切れ・合図なしの終了（異常終了）・渡した pak ごとの「読んだ」行が無いとき・使用状況を送らない印（`statistics log is not send.`）が無いときも失敗にする。見つけられない物（絵の画素・必須の絵の書き忘れなど）は記録の表のとおり（半分で切れた pak は、下の名前の一覧の比較が見つける）。見た目とつなぎ目は `addon_check` のゲームで見る
- 検査の自己確認として、`ami_monorail.pak` から壊した pak を作り、6 種（空・ROOT の大きさ・参照切れ・名前の重複・登録されない物・半分で切れた pak）と、余る物の 1 種とも失敗することを、疑似の本体でのハング・すぐ終了・異常終了・合図なしの判定と合わせて毎回確かめる（`--self-test`）
- **名前の一覧の比較（#245）**: `--makeobj makeobj` を渡すと、scenario（`tools/ci/pak_names_scenario/`）で本体に登録された way・way-object・tunnel・bridge・roadsign・building の名前を出し、`makeobj list` の名前と比べる。pak にあるのに登録されない名前、pak に無いのに登録された名前があれば失敗にする。出力に何も出さずに物を捨てる壊れ方（半分で切れた pak など）を見つける。crossing と、駅系（駅・車庫・桟橋・駅の拡張）以外の building は、本体に一覧の API が無い（または一覧が駅系だけ）ので比べない。アイコンの無い way は本体の一覧に出ないので、「登録されていない」と出たら、dat のアイコン（cursor・icon）も疑う。調査は記録 [2026-11-24_pak-names-compare](../../docs/records/2026-11-24_pak-names-compare.md)
- 起動の前に毎回 `settings.xml` を消し、作業フォルダは毎回新しく作る（本体は `settings.xml` の記録で使用状況を外へ送るため）
- **CI（Linux）**: 本体を `ci.env` の `HEADLESS_SIM`（`otrp:<128na/simutrans のコミット>`）から `tools/ci/setup-headless-sim.sh` でビルドし、`actions/cache` に載せる
- **手元（Windows）**: 本体を MinGW でビルドして渡したときだけ動かす（渡さないと飛ばす）。本体の一時の worktree で `config.default` に `BACKEND = posix`・`OSTYPE = mingw` などを書いて PowerShell から `make`（作り方は親フォルダの `otrp-dev/dev/build.md`）、`HEADLESS_SIM_BIN=<sim.exe> HEADLESS_PAKSET=<本体の tests/simutrans-test-base.zip> bash addons/ami/check.sh`。`sim.exe` の DLL は MSYS2 を入れた場所の `mingw64/bin` から探すので、`PATH` に足しておく。ゲームの検証環境とポートは使わない

## カタログ（見て回る保存データ。#203）

作成済みの AMI の物を一か所で見て回る保存データ `ami_catalog.sve` を、スクリプトで作る。**v64（`sim-WinGDI64-OTRPv64.exe`）用**（OTRPv64_3 は保存形式が違い読めない）。土台は `addon_check/save/flat_1024_left.sve`（1024 四方・左側通行・平ら。x<512 が温暖、x≥512 が降雪）。

- 作り方（アドオンのディレクトリで。`python -X utf8 build.py` で `dist/` に pak を作っておく）:
  `GAME_DIR=<検証用のフォルダ> PORT=47500 bash ingame/catalog.sh ALL`
  写し（`work/catalog_game/<PORT>/`）を `settings.xml.v64` で起動し、AMI の pak（`ami.pak` と `ami_rail_old.pak`）だけを入れて、[`ingame/catalog.py`](ingame/catalog.py) で棚を敷き、`world.save_game` で保存して `GAME_DIR/save/ami_catalog.sve` に置く（読み取り専用。既にあれば止まる）。終わったら `PORT=47500 STOP=1 bash ingame/catalog.sh` で閉じる。
- 置き方: 温暖側は x=8〜、降雪側は同じ配置を x+512。棚の 1 マスは 14×10 マスで、東西 10 マスの直線に 1 つの物（と、重ねる壁・橋脚・橋・トンネル）を置く。`python -X utf8 ingame/catalog.py --list` で、棚の 1 マスごとの座標と名前の一覧が出る。`--coverage` は、`src/` の名前が棚に出てくるか確かめる（路面の色の 5 個（#313）を除いて、今は 266 個）。
- 新しい物を足したら、`catalog.py` の棚（`rail_cells`・`road_cells`・`misc_cells`・`REUSE`）に足して、流し直す。

| 区画 | y（原点） | x の並び（温暖側。1 マス 14 ごと） |
|---|---|---|
| 線路 新（ballast・concrete・ladder・slab） | 8, 22, 36, 50 | way、基盤 4 版（single・back・center・front）＋同じ版の壁、同じ 4 版＋架線つきの壁、高架 4 版（壁・橋脚つき）、橋、トンネル、複線の壁（single の上に twin・twin 架線） |
| 線路 旧描画位置（`_old`。同じ 4 種） | 64, 78, 92, 106 | 同上 |
| 道路（local・general・trunk・expressway） | 120, 134, 148, 162 | way、基盤 4 版＋壁、基盤＋複線の壁、中央分離帯つきの壁 3 種、高架 4 版、橋、トンネル |
| 路面軌道・橋脚・歩道 | 190 | `ami_tram`（土・道路 3 種の上）、橋脚 5 種（門型・旧を含む）、歩道 4 種と歩道の柵 |
| 景観の見本（既存の見本を原点を替えて流す） | 206 | 歩道（x=8）、盛土（110）、電柱（212）、道路標識（314）、横断歩道の標識（416） |
| 路面表示・操車場・運河 | 300 | 6 車線の路面表示（8）、交差点の路面表示（110）、高速道路の分岐・合流（212）、操車場（314）、運河（416） |
| 車庫・モノレール・景観の運河 | 390 | 車庫（8）、跨座式モノレール（110）、懸垂式モノレール（212）、景観の運河（314） |
| 踏切・リニア | 480 | 線路 4 種×道路 3 種（8）、リニア 3 種とガイド・チューブ（110。約 152×58 マスなので 2 区画ぶん） |

- 前後を撮る: [`ingame/before_after.sh`](ingame/before_after.sh)（#197）。カタログの保存データを、前と後の pak の組で別々に起動し、同じ座標を等倍で撮る（`SPOTS_FILE` で座標を渡す。`CANAL=1` で運河・景観の運河を空き地に敷いて、温暖・降雪の両方を撮る）。使い方はスクリプトの冒頭。
  - 複数か所を前後一度に撮る（#227）: `PAKDIR_BEFORE`・`PAKDIR_AFTER` を渡すと、同じ `PORT` で順に 2 回起動して `OUT/before`・`OUT/after` に撮り、`OUT/pairs/` に横に並べる。敷き方は `LAYOUTS_FILE`（NUT と原点・降雪かを 1 行ずつ）、撮る場所は `SPOTS_FILE`（`名前 x y [cx0 cy0 cx1 cy1]`。後ろ 4 つは切り抜きの画素の座標で、最近傍で拡大する。差分から自動では探さない）。書式はスクリプトの冒頭。
- **地図の大きさに注意**: `ingame/game.sh` の既定の地図（`flat_512_left_v64` など。512 四方）と、`before_after.sh` の地図（`ami_catalog.sve`。1024 四方）は大きさが違う。降雪側は `game.sh` が x=256〜、カタログが x=512〜。見本の座標（`SPOTS` など）を一方から他方へ流用すると、範囲外で止まるか別の所を撮る。座標は、撮る地図で決め直す
- 運河の見本（`canal.nut`）は、以前は `OX >= 256` で降雪に塗っていたので、カタログの温暖側（x=416）の運河も降雪に塗られていた。降雪に塗るかを `local SNOW`（0 で塗る。`canal.sh` は `SNOW=1`、`catalog.py` は降雪側で 0 に書き換える）で決めるように直した。保存済みの `ami_catalog.sve` の温暖側の運河は、まだ降雪に塗られたまま（作り直すときに直る。#197）。
- 流用した見本は `sidewalk_sample.nut`・`embankment_sample.nut`・`pole_sample.nut`・`roadsign_sample.nut`・`crosswalk_sign_sample.nut`・`marking6_sample.nut`・`marking_sample.nut`・`expwy_marking_sample.nut`・`yard_sample.nut`・`canal.nut`・`depot.nut`・`monorail.nut`・`suspended_sample.nut`・`crossing_sample.nut`・`maglev.nut`。原点（`ORIGINS`・`OX`・`OY`）を `catalog.py` が書き換えて流す。
- 分岐の絵の網羅（全方位・近い斜め・坂）は入れていない（撮影用の見本の役目）。ゲーム内の見た目はユーザーが確かめる。

## 今の決まりごと

- 起動スクリプトは、写した `settings.xml` から使用状況の送信用の記録（`<![CDATA[/registerOTRPUsage?...]]>`）を、起動の前に毎回 [`ingame/strip_usage_log.sh`](ingame/strip_usage_log.sh) で空にする（#235）。OTRP の本体は、この記録が空でないと起動のたびに使用状況を外へ送る（記録は終了のたびに書き出される）。空だと、起動のログ（`-debug 3`）に `statistics log is not send.` が出る。ログは `GAME_ARGS="-debug 3" GAME_LOG=<ファイルの絶対パス>` で残せる（相対パスは写しの中に書かれて、写しと一緒に消える）（`game.sh`・`before_after.sh`・`sample_parallel.sh`。並列は台ごとに `.<台番号>` が付く）。検証環境（GAME_DIR）の `settings.xml` は変えない。起動と停止（写しの作成・上の記録の除去・起動・待ち・閉じる）は `ingame/game_lib.sh` の 1 か所にあり、`ingame/` の起動するスクリプトは全部これを使う（#243）。以前 GAME_DIR で直接起動して使用状況を送っていた `sample_check.sh`・`ex_check.sh` は、写し（`work/sample_game/<PORT>/`・`work/ex_game/<PORT>/`）で起動する形にし、blender-poc の `ingame/switch_check.sh` は（`flat2` と GAME_DIR の直接起動の前提で、今は使えないので）消した。新しく起動するスクリプトも `game_lib.sh` を source して `game_start`・`game_stop` を使う

- 値は次のとおり決めた（2026-11-15）。費用・維持費は pak128 の way と同じ単位（1/100 cr）で、iss の線路（15000・300）を基準にした。`blender/ami_dat.py` の `VALUES` と同じにする

| 種類 | 速度 | 費用 | 維持費 | 登場年 |
|---|---|---|---|---|
| 路面軌道 | 60 km/h | 10000 | 200 | 1900 |
| 在来線 | 160 km/h | 15000 | 300 | 1900 |
| 弾性まくらぎ直結軌道 | 240 km/h | 30000 | 600 | 1960 |
| フローティング・ラダー軌道 | 360 km/h | 35000 | 700 | 1990 |
| 高速線 | 480 km/h | 40000 | 800 | 2000 |
| 生活道路 | 40 km/h | 5000 | 100 | 1900 |
| 一般道路 | 120 km/h | 8000 | 200 | 1930 |
| 幹線道路 | 240 km/h | 14000 | 350 | 1960 |
| 高速道路 | 360 km/h | 20000 | 500 | 1990 |

### 第 2 弾の物の値

[ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md) で足す物の値は、作る前に次のとおり決めた（2026-11-21、ユーザーの決定。[#110](https://github.com/128na/simutrans-addon-dev/issues/110)）。物を作ったら、その値をこの表から物の節へ移す。iss・pak128 の値と並べた比べ方は、記録 [2026-11-21_ami-second-phase-values](../../docs/records/2026-11-21_ami-second-phase-values.md)。

決め方:

- way・way-object は、iss の値を基準にする。iss の補助の物は値が目印（費用 10、速度 65480 など）なので、第 1 弾の同じ種類（壁・歩道・橋脚）の値に合わせる。基準にした第 1 弾の値は、まだ仮のものを含む
- 高架・橋・トンネルの版は、第 1 弾と同じ倍率にする（高架 ×2、橋・トンネル ×4）。モノレール・運河に版を作るかは、それぞれの issue で決める
- 車庫・操車場（building）は、`cost`・`maintenance` を省いたり 0 にしたりせず、pak128 の既定値と同じ値を dat に明示する（2026-11-21、ユーザーの決定。省略や 0 は、考慮漏れでクラッシュすることがあるため）。書かないときの値の決まりは [way-addon.md](../../docs/reference/way-addon.md) の 5 章。iss・pak128 は書いていない
  - dat の値は 1/100 cr。車庫の費用は pak128 の `cost_depot_<種類>`（線路・路面軌道・モノレールが 8500 cr、道路が 7000 cr、船が 9000 cr）。
  - 操車場の費用は `cost_multiply_station`（600 cr。面積 1 タイル、level 1 のとき）。維持費は、どちらも `maintenance_building`（1800）。
  - 操車場の下に敷く線路の費用は、別にかかる。
- 登場年は 1900
- 新しい waytype の速さは、pak128 の車両が最高速度で走れる値にする（モノレールの車両は最高 150 km/h、船は 53 km/h）

| 物 | 速さ | 費用 | 維持費 |
|---|---|---|---|

- モノレールの費用は、在来線の高架と同じにした。iss の値（50000・1000）だと、高速線（40000・800）より高くなるため
- 運河は在来線より高い。pak128 では、運河の費用は線路の 6〜12 倍ある
- 歩道の壁と電柱は、どちらも water の way-object で、1 タイルに 1 つしか置けない。#120 で、柵つきの電柱（速さ 1010）を足して同じタイルに立てられるようにした（[「電柱の作り」](docs/objects/roadside.md)）
- 踏切・標識の値のキー（踏切に費用が無いこと、標識の費用が cr 単位で維持費と速さの上限が無いこと）は、[way-addon.md](../../docs/reference/way-addon.md) の 5 章。標識の「速度制限」は、#122 で最高速度を飾りにし、効き目のある最低速度の標識を別に置くと決めた（[「道路標識の作り」](docs/objects/roadside.md)）

## 残っていること

- できたと言う条件と、その状態（未確認・仮のものを含む）は [ACCEPTANCE.md](ACCEPTANCE.md)。ベータの既知の課題と、後に回した issue は [ACCEPTANCE.md の「ベータ版（第 1 弾）での扱い」](ACCEPTANCE.md#ベータ版第-1-弾での扱い)
- やり残し・未解決の課題は、このリポジトリの [issue（ラベル `AMI`）](https://github.com/128na/simutrans-addon-dev/issues?q=is%3Aissue+is%3Aopen+label%3AAMI) で追う（[AGENTS.md](../../AGENTS.md) の「TODO・未解決の課題」）。物ごとの作りで値が仮のものは、物ごとの文書（上の「物ごとの作り」）の各節に書く
