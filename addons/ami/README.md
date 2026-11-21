# AMI（AI Marunage Infrastructure）

pak128 用のインフラアドオン集。絵は Blender のスクリプトで描く（作り方は [blender-poc](../blender-poc/README.md) で確かめたもの）。

> **ベータ版。** ロードマップ（[#61](https://github.com/128na/simutrans-addon-dev/issues/61)）の第 1 弾を、ベータ版として配る（[#91](https://github.com/128na/simutrans-addon-dev/issues/91)。基準は「多少課題があってもゲーム内で動作すれば OK」）。正式版までに、物の名前・値・見た目が変わることがある。既知の課題（ベータの後に回したもの）は [ACCEPTANCE.md の「ベータ版（第 1 弾）での扱い」](ACCEPTANCE.md#ベータ版第-1-弾での扱い)、遊ぶ人向けの説明は配る zip の `ami_readme.txt`（元は [release/readme.txt](release/readme.txt)。簡潔な説明・導入方法・注意点だけで、物の一覧は「主な中身」として網羅を保証しない。すべての物の一覧は、zip に入れる `ami_lineup.txt`（dat から `lineup.py` が作る。[#138](https://github.com/128na/simutrans-addon-dev/issues/138)）。名前が変わったときのセーブデータの扱いは [ADR 0009](../../docs/adr/0009-ami-beta-renames-without-readme-notice.md)）。敷き方の説明は下の「[遊ぶ人向けの敷き方](#遊ぶ人向けの敷き方)」。

**今あるのは在来線の通常の版（`ami_rail_ballast`）と、在来線の基盤の 4 版・壁だけの way-object・架線つきの壁の way-object（`ami_rail_ballast_base_*`・`ami_wall_rail_*`・`ami_wall_rail_*_catenary`）、高架の 4 版と橋脚の way（`ami_rail_ballast_elev_*`・`ami_pier_rail`・門型の `ami_pier_rail_gate`）、橋とトンネル（`ami_rail_ballast_bridge`・`ami_rail_ballast_tunnel`）、高速線（スラブ軌道）の通常の版・基盤の 4 版・高架の 4 版・橋・トンネル（`ami_rail_slab`・`ami_rail_slab_base_*`・`ami_rail_slab_elev_*`・`ami_rail_slab_bridge`・`ami_rail_slab_tunnel`）、弾性まくらぎ直結軌道（コンクリート道床）とフローティング・ラダー軌道の同じ一式（`ami_rail_concrete`・`ami_rail_concrete_*`・`ami_rail_ladder`・`ami_rail_ladder_*`）、道路 3 種の通常の版（`ami_road_local`・`ami_road_general`・`ami_road_expressway`）と、道路の基盤の 4 版・高架の 4 版・橋・トンネル（`ami_road_*_base_*`・`ami_road_*_elev_*`・`ami_road_*_bridge`・`ami_road_*_tunnel`）、道路の路面表示の版（`ami_road_general_lane<n>`・`ami_road_expressway_lane<n>`）、道路の壁の way-object（`ami_wall_road_*`）と中央分離帯つきの壁（`ami_wall_road_*_divider`）、道路用の橋脚（`ami_pier_road`）、路面軌道の通常の版（`ami_tram`）、歩道（`ami_sidewalk`）と歩道の種類・高架の歩道・歩道の柵（`ami_sidewalk_<舗装>`・`ami_sidewalk_elev`・`ami_wall_sidewalk_<版>`）、線路×道路の踏切（`ami_crossing_*`）、盛土（`ami_embankment_front`・`ami_embankment_back`）、電柱（`ami_sidewalk_pole_<版>`・`ami_wall_sidewalk_<版>_pole`）。** 描画から pak までの骨組み（[#14](https://github.com/128na/simutrans-addon-dev/issues/14)）の上に、在来線の壁の無い通常の版を仕上げ（[#15](https://github.com/128na/simutrans-addon-dev/issues/15)。全方位・分岐の絵・近い斜め・雪・汚れ）、基盤の版と壁を足した（[#16](https://github.com/128na/simutrans-addon-dev/issues/16)。下の「壁の敷き方」）。壁に架線を持たせた版を足した（[#17](https://github.com/128na/simutrans-addon-dev/issues/17)。下の「架線の作り」）。高架の 4 版と、高架の真下の地面に敷く橋脚の way を足した（[#18](https://github.com/128na/simutrans-addon-dev/issues/18)。下の「高架と橋脚の作り」）。橋とトンネルを足した（[#19](https://github.com/128na/simutrans-addon-dev/issues/19)。下の「橋とトンネルの作り」）。高速線を足した（[#20](https://github.com/128na/simutrans-addon-dev/issues/20)。下の「高速線の作り」）。道路 3 種の通常の版を足した（[#21](https://github.com/128na/simutrans-addon-dev/issues/21)。下の「道路の作り」）。道路の壁・基盤の版・高架・橋脚・橋・トンネルを足した（[#22](https://github.com/128na/simutrans-addon-dev/issues/22)。下の「道路の壁・高架・橋脚・橋・トンネルの作り」）。路面軌道を足した（[#23](https://github.com/128na/simutrans-addon-dev/issues/23)。下の「路面軌道の作り」）。歩道を足した（[#24](https://github.com/128na/simutrans-addon-dev/issues/24)。下の「歩道の作り」）。バリエーションの第 1 弾（[#61](https://github.com/128na/simutrans-addon-dev/issues/61)）として、弾性まくらぎ直結軌道を足した（[#62](https://github.com/128na/simutrans-addon-dev/issues/62)。下の「弾性まくらぎ直結軌道の作り」）。続けてフローティング・ラダー軌道を足した（[#67](https://github.com/128na/simutrans-addon-dev/issues/67)。下の「フローティング・ラダー軌道の作り」）。線路×道路の踏切を足した（[#111](https://github.com/128na/simutrans-addon-dev/issues/111)。下の「踏切の作り」）。第 2 弾（[ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md)）の景観として、盛土を足した（[#123](https://github.com/128na/simutrans-addon-dev/issues/123)。下の「盛土の作り」）。4 車線の中央分離帯を足した（[#118](https://github.com/128na/simutrans-addon-dev/issues/118)。下の「中央分離帯の作り」）。第 2 弾（[ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md)）として、歩道の種類・高架の歩道・歩道の柵を足した（[#119](https://github.com/128na/simutrans-addon-dev/issues/119)。下の「歩道の種類・高架の歩道・歩道の柵の作り」）。多車線の路面表示の版を足した（[#121](https://github.com/128na/simutrans-addon-dev/issues/121)。下の「路面表示の版の作り」）。第 2 弾の景観として、電柱を足した（[#120](https://github.com/128na/simutrans-addon-dev/issues/120)。下の「電柱の作り」）。下の表の残りは作る予定のもの（開発ステップの一覧は [#27](https://github.com/128na/simutrans-addon-dev/issues/27)）。範囲と作りを決めた理由は次の ADR にある。

- [ADR 0002](../../docs/adr/0002-ami-scope.md): 範囲・対象・ライセンス・配布（第 1 弾まで。ADR 0008 に置き換えた）
- [ADR 0003](../../docs/adr/0003-ami-walls-base-piers-as-separate-objects.md): 壁・基盤・橋脚・歩道の分け方
- [ADR 0004](../../docs/adr/0004-shared-blender-tools.md): 描画の道具を `tools/` で共通にする
- [ADR 0005](../../docs/adr/0005-ami-render-tool-conventions.md): 部品のまとめ方・レイアウト検証用モード・設定値・並列
- [ADR 0006](../../docs/adr/0006-ami-track-variants-by-track-form.md): 線路のバリエーションを軌道の形式で足す
- [ADR 0007](../../docs/adr/0007-ami-beta-distribution.md): 第 1 弾のベータの配り方（場所・版の名前・zip の中身）
- [ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md): 第 2 弾の範囲（入れる物・入れない物・順番・名前・pak）。ADR 0002 を置き換える

## 目的と中身

オブジェクト名はどれも `ami_` で始める。名前は次のとおり確定した（2026-11-15）。

| もの | 名前 |
|---|---|
| way（通常の版） | `ami_tram`・`ami_rail_ballast`・`ami_rail_concrete`・`ami_rail_ladder`・`ami_rail_slab`・`ami_road_local`・`ami_road_general`・`ami_road_expressway` |
| 基盤・高架の版 | `<way の名前>_base_<版>`・`<way の名前>_elev_<版>`（版は `single`・`back`・`center`・`front`） |
| 橋・トンネル | `<way の名前>_bridge`・`<way の名前>_tunnel` |
| 道路の路面表示の版 | `<道路の way の名前>_lane<n>`（一般道路・高速道路の n = 1〜7。#121。下の「路面表示の版の作り」） |
| 線路の壁 | `ami_wall_rail_<版>`（`single`・`back`・`center`・`front`。`center` は行き止まりの端の壁だけ）、架線つきは `ami_wall_rail_<版>_catenary`（`center` は架線と、行き止まりの端の壁だけ）。近い斜めの分け合うタイル用に `ami_wall_rail_twin`（壁だけ。下の「壁の敷き方」）と `ami_wall_rail_twin_catenary`（架線つき。下の「架線の作り」） |
| 道路の壁 | `ami_wall_road_<版>`（`single`・`back`・`center`・`front`。`center` は行き止まりの端の壁だけ）。近い斜めの分け合うタイル用に `ami_wall_road_twin`（名前は確定。2026-11-19、ユーザーの決定。下の「道路の壁・高架・橋脚・橋・トンネルの作り」）。中央分離帯つきは `ami_wall_road_front_divider`・`ami_wall_road_center_divider`・`ami_wall_road_twin_divider`（下の「中央分離帯の作り」） |
| 橋脚・歩道 | `ami_pier_rail`（門型は `ami_pier_rail_gate`）・`ami_pier_road`・`ami_sidewalk`。歩道の種類は `ami_sidewalk_<舗装>`（`asphalt`・`brick`・`tile`）、高架の歩道は `ami_sidewalk_elev`（#119） |
| 歩道の柵 | `ami_wall_sidewalk_<版>`（`single`・`back`・`front`。#119。名前は作業者が決めた。ユーザーが PR で確かめる） |
| 電柱 | `ami_sidewalk_pole_<版>`（電柱だけ）・`ami_wall_sidewalk_<版>_pole`（柵つき。#120） |
| 景観 | 盛土 `ami_embankment_front`・`ami_embankment_back`（ADR 0008 の `ami_embankment_<版>`） |
| モノレール | 跨座式 `ami_monorail_straddle`、高架 `ami_monorail_straddle_elev_<版>`（`front`・`center`・`back`）、トンネル `ami_monorail_straddle_tunnel`（ADR 0008。#113） |
| 運河 | `ami_canal`（ADR 0008。#114） |
| 車庫 | `ami_rail_depot`・`ami_tram_depot`・`ami_road_depot`・`ami_monorail_depot`・`ami_canal_depot`（ADR 0008） |
| 操車場 | `ami_rail_yard`（#115） |

dat のファイル名と pak に入る名前は同じ（`src/<名前>.dat`）。今あるのは `ami_rail_ballast`・`ami_rail_ballast_base_<版>`（4 版）・`ami_wall_rail_<版>`（4 版）・`ami_wall_rail_twin`・`ami_wall_rail_<版>_catenary`（4 版）・`ami_wall_rail_twin_catenary`・`ami_rail_ballast_elev_<版>`（4 版）・`ami_pier_rail`・`ami_pier_rail_gate`・`ami_rail_ballast_bridge`・`ami_rail_ballast_tunnel`・`ami_rail_slab`・`ami_rail_slab_base_<版>`（4 版）・`ami_rail_slab_elev_<版>`（4 版）・`ami_rail_slab_bridge`・`ami_rail_slab_tunnel`・`ami_rail_concrete`・`ami_rail_concrete_base_<版>`（4 版）・`ami_rail_concrete_elev_<版>`（4 版）・`ami_rail_concrete_bridge`・`ami_rail_concrete_tunnel`・`ami_rail_ladder`・`ami_rail_ladder_base_<版>`（4 版）・`ami_rail_ladder_elev_<版>`（4 版）・`ami_rail_ladder_bridge`・`ami_rail_ladder_tunnel`・`ami_road_local`・`ami_road_general`・`ami_road_expressway`・道路 3 種それぞれの `_base_<版>`（4 版）・`_elev_<版>`（4 版）・`_bridge`・`_tunnel`・`ami_wall_road_<版>`（4 版）・`ami_wall_road_twin`・`ami_wall_road_front_divider`・`ami_wall_road_center_divider`・`ami_wall_road_twin_divider`・`ami_pier_road`・`ami_tram`・`ami_embankment_front`・`ami_embankment_back`・`ami_sidewalk`・`ami_sidewalk_<舗装>`（3 種）・`ami_sidewalk_elev`・`ami_wall_sidewalk_<版>`（3 版）・`ami_sidewalk_pole_<版>`（2 版）・`ami_wall_sidewalk_<版>_pole`（2 版）・`ami_monorail_straddle`・`ami_monorail_straddle_elev_<版>`（3 版）・`ami_monorail_straddle_tunnel`・`ami_canal`・車庫 5 つ・`ami_rail_yard`。

### 線路（新描画位置）

| 種類 | 速度 | way | 版 |
|---|---|---|---|
| 路面軌道（tram、コンクリートで固めた線路） | 60 km/h | `ami_tram` | 通常だけ（壁・高架・橋・トンネルなし） |
| 在来線（バラスト軌道） | 160 km/h | `ami_rail_ballast` | 通常・基盤 4 版・高架 4 版・橋・トンネル |
| 弾性まくらぎ直結軌道（コンクリート道床、#62） | 240 km/h | `ami_rail_concrete` | 同上 |
| フローティング・ラダー軌道（#67） | 360 km/h | `ami_rail_ladder` | 同上 |
| 高速線（スラブ軌道） | 480 km/h | `ami_rail_slab` | 同上 |

#### 在来線の手本（blender-poc の線路）

在来線（バラスト軌道）の手本は、[blender-poc](../blender-poc/README.md) の線路（新描画位置の `bpoc_track`）と、カーブ・分岐の作りは pak128 標準の線路（`Rail_100` など）。
道床・まくらぎ・レールの寸法、基準面の下げ幅、持ち分、汚れ・雪は POC の線路を写した。POC で合わせた直線・斜め・坂の位置（手本とのつなぎ目）は測り直していない。

AMI として変えた点（2026-11-17。後半はユーザーの見た目の指摘から）:

- 名前・値: `ami_rail_ballast`、160 km/h（値は下の「今の決まりごと」）。アイコンの数字も 160
- 道床の色: POC は一色の灰色だった。夏の絵では、2 色のまだらにして砕石の粒に見せた（`blender/render.py` の `BALLAST_STONE_*`・`BALLAST_GRAIN`）。最初は平均の色を POC と同じにし、雪の絵も POC と同じにした。精細化（下の項目）で、まだらを濃くして暗くし、雪の絵も変えた。弾性まくらぎ直結軌道（下の「弾性まくらぎ直結軌道の作り」）と見分けるため、さらに暗く青みの灰にした（#70。2026-11-21、ユーザーの決定。`BALLAST_DARK`・`BALLAST_TINT`）。赤み・緑みは足していない（坂の測り方がレールを「赤 − 青」で、地面を緑の強さで見分けるため）。雪の絵は直結軌道と同じで、雪では見分けない（同じ日、ユーザーの決定）
- カーブ: pak128 標準の線路と同じく、曲線ではなく斜めの絵で表す（dat の `image[sw]` などが `diagonal` と同じセルを指す。シートのカーブのセルは描かない）。T字・十字と分岐の絵（switch 画像 1・2）も、カーブの代わりに同じ 2 辺をつなぐ斜めの直線にした。斜めの部分は斜めのタイルと同じ幅・下げ幅で作り、直線と斜めの道床の間のすき間は道床の上面の凸包で埋める（`tools/blender/sheetlib` の `diag_curves`）
- 行き止まり: レールを POC（タイルの中心まで）より延ばし、閉じた側のタイルの端からタイル 1 辺の 1/4 の所を終点にした（`blender/render.py` の `END_FROM_EDGE`）。道床は終点より奥、タイルの端まで敷く。レールの末端に車止めを置く（下の「車止めの手本」）
- 行き止まりのまくらぎが直線より白く見えた: レールの間の油の帯を 2 本に分けて作っていて、中心で辺を分け合う形が、行き止まりのタイルでは切り抜きで消えていた（油の帯が無いぶん白く見えた）。油の帯を中心をまたぐ 1 本にした。blender-poc の線路にも同じ欠けがある（POC のシートは変えないので直していない）
- 精細化（#56。ラウンド 1〜7 で試し、ラウンド 8 で本番に入れた。2026-11-20）: 砕石のまだらを濃く細かくして暗く（使い込んだ砕石）、まくらぎを明るい PC の色にしてタイル 1 辺に 18 本・継ぎ目でそろう間隔に（#89 で 16 本・タイルの辺の上に変えた）、まくらぎの間を砕石で埋め、レールを暗い側面 1px と磨かれた明るい頭の 2 色に、道床の形をまくらぎの上面の高さの肩とのり面にした。雪の絵は積もったばかりの雪（汚れの帯もまくらぎも雪で、レールだけが出る）で、道床の雪は地面の雪と同じ青み。値は `blender/render.py` の「在来線の精細化」、決め方は `docs/records/2026-11-20_ami-refine-round1.md`〜`round8.md`。壁のある版の行き止まりでは、道床（高速線はコンクリート道床）を端の壁の内側の面で止める（`_EDGE_BED`）

#### 車止めの手本（ユーザーから受け取った画像、2026-11-17）

画像は出典の権利が分からないので、リポジトリに入れず、形だけを書き起こす（鉄道模型の車止めの写真）。

- 全体は黒。線路の終端に置く
- 線路を横切る低い台座が、レールの上と両側に渡る
- 両側のレールの外から奥へ、斜めの脚が 2 本立ち上がり、上で小さな箱（受け）につながる。レールの間に、細い緩衝板が 1 枚立つ
- 受けの奥の中央に四角い柱が 1 本立ち、上に箱形の標識灯（白〜橙に光る面、十字の模様）が付く
- 道床（灰色の砕石）は車止めのさらに奥まで続き、タイルの端で終わる

絵では、台座・斜めの脚 2 本・受けの箱・緩衝板・柱・標識灯の箱に単純にした（`tools/blender/sheetlib/track_parts.py` の `BUFFER_*`、部品のまとまり `buffer`）。灯の面は夜に光る特殊色（`light_white`）。十字の模様は大きさが数 px なので描いていない。

#### 見た目の手本（ユーザーから受け取った画像、2026-11-15）

画像は出典の権利が分からないので、リポジトリに入れず、形だけを書き起こす。

- **高速線（スラブ軌道）**: 下から順に次の層を重ねる。
  - コンクリート道床: 暗い灰色の幅の広い板。
  - てん充層: 道床の上の薄い層。
  - 軌道スラブ: 明るい灰色の板。長手の両端に、円柱の突起が道床から立ち、スラブの端の欠き込みに入る。
  - 締結装置: レールの下に、一定の間隔で並ぶ黒い小さな台。
  - レール: 赤茶色。
- **路面軌道**: 道路のあいだに、縁石と柵で分けた専用の軌道。
  - 床はコンクリートで固めてあり、レールの頭だけが床の面に出る。
  - レールの内側と周りに、さび色の汚れの帯がある。
  - 軌道の縁は明るい色の帯で、道路の白線とは別。
  - 写真では、架線の柱が 2 本の線路のあいだに立つ（架線は範囲外。tram は道路の上に重ねて敷く）。

#### 路面軌道の作り（#23）

`ami_tram`（`waytype=tram_track`。値は下の「今の決まりごと」）は、道路の上に重ねて敷く tram（ADR 0002）。写真の手本（上の「見た目の手本」）のうち、コンクリートで固めた床・レールの頭・さびの帯・縁の帯を描き、縁石と柵は描かない（道路に重ねると、縁石と柵は道路の上に立つことになる）。専用の軌道に見えないこの見せ方のままにする（2026-11-20、ユーザーの決定）。描くのは `tools/blender/sheetlib` の `track_sheet` で、部品は `tram_parts`（設定は `blender/render.py` の「路面軌道」）。

- 断面: レールの頭は在来線より少し太い 0.40〜0.54（`TRAM_RAIL_IN`・`TRAM_RAIL_OUT`。間隔は画面で 6px。pak128 標準の `Tram_Track_050_A` も 6px）。下から、縁の帯の板（床の全幅 `TRAM_BED_U` = 1.05）、コンクリートの床（縁の帯の内側 `TRAM_EDGE_U0` = 0.87 まで）、さびの帯、レールの内側の溝（`TRAM_GROOVE_W`）、レールの頭。どれも路面の高さ 0 のすぐ上の薄い板で、段に見せない
- 精細化（#56。ラウンド 1〜4 で試し、ラウンド 4 を本番に入れた。2026-11-20、ユーザーの決定）: レールの頭を金属でない明るい色（金属の材質は環境を映して暗く写った）にして溝を 0.14 に広げ、外側の目地をやめた（明るい頭と暗い溝の 2 本線）。縁の帯を床より少し明るい灰色に落とした（明るい頭と並んで明るい線が 4 本に見えた）。レールの間の油の帯をやめた（電車は油を落とさない）。画面で横向きの斜めと曲線の横向きの所では、頭を 2.2 倍・溝を 1.4 倍に広げる（`TRAM_HDIAG_HEAD`・`TRAM_HDIAG_GROOVE`。1px に満たず消えた）。T字・十字の曲線と直線のあいだの透明な穴を床で埋める（`TRAM_CELL_FILLS`。`track_sheet` の `cell_fills`）。決め方は `docs/records/2026-11-20_ami-tram-refine-round1.md`〜`round4.md`
- 高さ・位置: 道路と同じ（基準面を動かさない `FLAT`、絵の基準位置と持ち分は `ROAD_CY`、`spill` 0）。線路の新描画位置のように下げない。pak128 標準の `Tram_Track_050_A` もレールは地面の菱形の位置にある（`tools/blender/ref_measure.py` で直線のずれ +0。AMI の在来線は +2）。AMI の一般道路の中央線（+0.25）と路面軌道の溝の中ほど（+0.5）は、シートで 0.5px 以内（2026-11-20）
- 縁の帯: 床の全幅の明るい板を床の下に敷き、その上に床を重ねる。T字・十字では、ほかの経路の床が帯を覆い、帯はつないだ床の外周にだけ出る（帯を床の上に描いていたときは、分岐の中を横切る明るい線になった）
- 溝: レールの頭だけでは床と見分けられず、等倍で線路に見えなかったので、レールの内側に暗い溝を描く。前は外側にも暗い目地を描いていた（pak128 の `Tram_Track_050_A` もレールの両側に暗い縁がある）が、精細化でやめた
- カーブ: 曲線のセル（行 2 の列 5〜8）を描き、dat の `image[sw]` などはそのセルを指す（2026-11-17 のユーザーの指摘。在来線・道路のように斜めの絵にしない）。AMI の道路のカーブは斜めの絵なので、道路の上では、路面軌道の曲線が斜めに切った道路の角の内側を通る（`docs/tram_GE_B.png`）
- 行き止まり: 在来線と同じく、レールと溝は閉じた側のタイルの端からタイル 1 辺の 1/4 の所で止める（`blender/render.py` の `END_FROM_EDGE` を路面軌道の設定にも渡す）。床と縁の帯はタイルの端まで敷き、閉じた端にも縁の帯が回る（`tram_parts` の `_to_edge`。2026-11-20 のユーザーの指摘。前はレールも床もタイルの中心で止めていた）。車止めは置かない（道路の上に立つので）。`docs/tram_GE_AFC.png`・`tram_end_zoom.png`（5 倍）
- 雪: 道路の車道と同じく除雪された想定で、夏と同じ絵（`TRAM_SNOW_SKIN`。線路の汚れは雪の絵で雪の上の汚れに変わるので、夏の材質に戻す）
- 近い斜め: `diagonal[close1]`・`[close2]` を持つ
- 分岐の絵（switch 画像 1・2）: dat に入れている（`blender/ami_dat.py` の `TRAM_SWITCH_IMAGES`。真が既定）。tram は本体で線路と同じ選び方（`weg_t::calc_image` の `track_wt` → `select_switch_image`。[reference](../../docs/reference/way-addon.md) の 9.2）で、道路の 1・2 のような多車線の交差点の意味は無い。見本の区画 H の 8 通りが、どれも通常の T字と違う分岐の絵になり、区画 I で十字の 1・2 を固定できる（`[check]` の行。2026-11-20）。道路（外している）とはそろえず、入れたままにする（2026-11-20、ユーザーの決定）。偽にしたときの絵は `docs/tram_switch_H0_zoom.png` の右（左が今）
- 橋脚の way との関係: 線路用・道路用の橋脚（`ami_pier_*`）も `tram_track` なので、路面軌道とつながる。橋脚の列を路面軌道で横切ると、横切るタイルは路面軌道に置き換わり、両隣の橋脚とつながる（見本の区画 P。`[check] P cross=ami_tram west=ami_pier_rail`。`docs/tram_GR_P.png`。2026-11-20）。高架の下の道路に路面軌道を通すときは、橋脚の無いタイルにする
- 見た手本: pak128 の `Tram_Track_050_A`（`../refs/pak128/infrastructure/tram_tracks/tram_track_050_a.dat`・`.png`。レールの位置と間隔、両側の暗い縁、曲線のカーブ。取り入れた）、iss の `tram.dat`（`../refs/iss/src/way/rail/tram.dat`。`waytype=tram_track` とセルの並び。取り入れた）。iss の路面軌道の絵は層の合成（`standard_kt`）で、元の絵が refs に無いので比べていない

### 道路

| 種類 | 速度 | 中央線 | way | 版 |
|---|---|---|---|---|
| 生活道路 | 40 km/h | なし | `ami_road_local` | 通常・基盤 4 版・高架 4 版・橋・トンネル |
| 一般道路 | 120 km/h | 白線 | `ami_road_general` | 同上 |
| 高速道路 | 360 km/h | 破線 | `ami_road_expressway` | 同上 |

- 断面はどれも blender-poc の高速道路と同じ（片側 1 車線、タイル全面が路面、歩道なし）
- 通常の版は #21、基盤の版・高架・橋・トンネルと道路の壁・橋脚は #22
- 地上の道路の基盤の 4 版は、ゲームの画面で要ると判断して作り、置くことが確定した（2026-11-19、ユーザーの決定。理由は「道路の壁・高架・橋脚・橋・トンネルの作り」）

### 道路の作り（通常の版、#21）

3 種とも blender-poc の高速道路（`../blender-poc/blender/render.py` の `ROAD_PROFILES["expressway"]`）と同じ作りで、`tools/blender/sheetlib` の `road_sheet` で描く（設定は `blender/render.py` の `ROAD_SETTINGS`）。種類ごとに変えたのは中央線・路面の色・アイコンだけ。

| 種類 | 中央線 | 路面の色 | アイコン |
|---|---|---|---|
| 生活道路 | なし | blender-poc の街路の灰色（`road_parts` の `STREET_ASPHALT`）を 2.4 倍明るくした灰色 | 道路の背景・40 |
| 一般道路 | 白の実線 | 同上 | 道路の背景・120 |
| 高速道路 | 白の破線 | blender-poc の高速道路の暗く青みのある色（`EXPWY_ASPHALT`）を 1.6 倍明るくした色 | 高速道路の背景・360 |

- 白線: 路側の白線は 3 種とも実線。T字は枝の側の路側線を点線（分岐の口）にし、十字と 1 タイルだけの道は東西の中央線と東西の点線（blender-poc の高速道路と同じ）。行き止まりは直線と同じ絵
- 中央線の破線（高速道路）: タイルの中の長さを、直線は 4 本、斜めは 3 本に割り、タイルの辺がいつもすき間の中ほどに来るように置く（`road_parts` の `CENTER_DASHES`・`sheetlib` の `tile_dashes`）。直線（長さ 10）と斜め（10/√2）のどちらも割り切れるので、直線と斜め・坂と平地の継ぎ目で間隔がそろう。前の点線の作り（経路の始点から周期 1.6）は 10 を割り切れず、斜めは経路をタイルの外まで延ばすので、継ぎ目で間隔が崩れる。線の幅は実線の中央線と同じ（約 1px）。画面で横向きの斜めは、実線と同じく半画素ずらす
- カーブ: 3 種とも斜めの絵（dat の `image[sw]` などが `diagonal` と同じセル）。手本では、iss の道路は速さで分かれる（`../refs/iss/src/way/road/ground.dat` の `iss_wrg_0030`・`0050`・`0120_*` は `image[ne]` が曲線のセル、`iss_wrg_1200_*` は `diagonal` と同じセル）。pak128 標準の `Road_030`（`../refs/pak128/infrastructure/roads/road_030.dat`）も曲線のセル。それでも 3 種をそろえたのは、道路の壁（`ami_wall_road_<版>`、#22）を 3 種で共通の way-object にするため（way-object のカーブの絵は 1 つなので、種類ごとにカーブの形が違うと壁が合わない）。断面も blender-poc の高速道路（斜めの絵）と同じ
- 路面の色: 生活道路・一般道路は pak128 標準の道路（灰色）とつなぐことが多いので街路の灰色、高速道路は一般の道路と見分けられるよう暗い青み。走行跡と路肩のまだらの雪は、路面と同じ 2 色から作る（`sheetlib` の `asphalt_skin`。路面だけ替えると、暗い路面に明るい帯が乗る）
- 雪: 車道は除雪されて夏と同じ（路面・白線・走行跡）。路側の白線の外から路肩に雪が積もり、白線の内側をまだらの雪でぼかす（blender-poc の道路と同じ `snow` の部品）
- 精細化（#56。ラウンド 1〜4 で試し、ラウンド 3 を本番に入れた。2026-11-20、ユーザーの決定。ラウンド 4 の明るい路面はリアルだが色があせて見えた）: 設定は `blender/render.py` の「道路一式の質感」で、道路 3 種とその版・道路の壁・道路用の橋脚・歩道にだけ渡す（`sheetlib` の既定は blender-poc・在来線・スラブ軌道と共通なので変えない）。決め方は `docs/records/2026-11-20_ami-road-refine-round1.md`〜`round3.md`、入れ方は `2026-11-20_ami-road-refine-production.md`
  - 路面: 照り返しを切り（生活道路・一般道路。前は空の色の映り込みが明るさの大半で、色とまだらが効かなかった）、2 色を明るくして平均から 1.4 倍離し、色の段を 0.47〜0.53 に狭めて 1 画素の骨材の粒を出す（iss の路面と同じ描き方）。走行跡の寄せ具合は半分（高速道路は 4 分の 1）で、明るい縞でなくかすかな帯にする（`asphalt_skin` の `ramp`・`wear_t`）
  - コンクリート（壁・基盤・高架の躯体・橋脚・坑口の躯体）: 元の色を中心に ±12% のまだら（Scale 25）で、打ち放しの肌を出す。形を作る関数の中で材質を作るので、材質の名前で差し替える（`road_sheet`・`tunnel_sheet`・`pier_sheet` の `mat_skin`）
  - 雪の歩道・縁石と路肩の雪: 地面の雪に合わせ、青みの色（0.88・0.86・0.97）を中心に ±10% のまだらと発光 0.15（`road_sheet` の `snow_skin`、`sidewalk_sheet` の `snow`）。一色の雪では、地面の雪の上に灰色の板が置いてあるように見えた
  - 歩道の敷石: 灰色の敷石と暗い目地（`sidewalk_sheet` の `paving`。Brick テクスチャ、約 6 x 3px）。前は緑がかったまだらで、草地か砂利に見えた
- 汚れ: 走行跡（車輪の通る所が磨かれた明るい帯）と油の帯。交差点は右左折の経路にも付ける（blender-poc と同じ）
- 近い斜め: `diagonal[close1]`・`[close2]` を持つ（斜めの 2 片を中心線で切って 1 枚に描く。blender-poc と同じ）

#### 分岐の絵（switch 画像 1・2）

**今は道路の dat に分岐の絵を入れていない（2026-11-20、ユーザーの決定）。** 本体（OTRP）は、道路の「1」を枝の先が分岐の T字に、「2」を十字のタイルにだけ出す（KUTA 版から引き継いだ、多車線の交差点のための使い方）。固定の道具の名前は線路の分岐の意味で付いていて、これと合わない。T字の 1・2 を固定の名前に合わせて描くと、自動の 4×2・6×6 の十字がふさがり、ex 画像を足しても 4×4 しか直らない（[reference](../../docs/reference/way-addon.md) の 9.3）。本体の分岐の絵の仕様を整理するまで、道路の way（waytype が `road` のもの全部。通常の版・基盤の版・高架の版）の dat から 1・2 の 10 枚を外す（戻すのは [#46](https://github.com/128na/simutrans-addon-dev/issues/46)）。

- 切り替え: `blender/ami_dat.py` の `ROAD_SWITCH_IMAGES`（既定は偽 = 外す）。真にすると dat に戻る。シートの分岐のセル（下の絵の作り）と、轍・優先道路の十字・停止線の部品、見本の区画 I・P は消さずに残している
- 外したことで使えないもの: 優先道路の十字（`nsew1`・`nsew2`）と、固定した T字の轍。固定の道具で 1・2 を選んでも通常の絵のまま。2 本並べた道路の渡り口（区画 HV・HH）も通常の T字（枝の口の点線）が向かい合う
- 見えるもの: 十字はどれも通常の十字（開いた十字）、T字は通常の T字。多車線の交差点（4×2・4×4・6×6）も、4 車線に 2 車線が T字でつながる所も、横切る道路はふさがらない（`docs/road_GE_junction_noswitch.png`・`road_junction_noswitch_all.png`・`road_junction_tee_noswitch.png`・`road_GE_noswitch_ground.png`。2026-11-20、`OTRPv64_3.exe`、`flat_512.sve`）。4×4・6×6 の中ほどの角の丸い四角の枠（下の「十字と T字の絵（通常の絵）」）は残る
- 線路と橋脚の way（`ami_pier_road` は `tram_track`。分岐の絵は T字・十字と同じ柱）の分岐の絵は変えていない

分岐の絵を入れていたときの作り（T字の 1・2 の白線と轍、優先道路の十字、開いた十字と角の円弧、停止線）と、ゲームで確かめた結果は記録 [2026-11-20_ami-road-switch-design](../../docs/records/2026-11-20_ami-road-switch-design.md) にある。本体の 1・2 の使われ方は [reference](../../docs/reference/way-addon.md) の 9.3。戻すときは [#46](https://github.com/128na/simutrans-addon-dev/issues/46) で、本体の分岐の絵の仕様の整理（[128na/simutrans#15](https://github.com/128na/simutrans/issues/15)）に合わせる。

#### 十字と T字の絵（通常の絵）

- 通常の十字（`image[nsew]`）は開いた十字: 交差点の中に走行車線を横切る白線を引かない。腕の路側線は角の円弧でつなぎ、中央線は腕の口（円弧の端）まで。3 種とも同じで、1 タイルの道路（`single`）も同じ絵（`docs/road_GE_cross_open_zoom.png`・`road_EX_cross_open_zoom.png`・`road_LO_L_open_zoom.png`）
- 通常の T字: 本線の中央線と、枝の無い側の路側線（実線）を通す。枝の側は、本線の路側線を角の円弧で枝の路側線へつなぎ、枝の口を点線で渡す（`docs/road_GE_tee_arc_zoom.png`）
- 角の円弧: 隣り合う腕の路側線を、角で 4 分の 1 の円弧でつなぐ。半径は `EDGE_CORNER_R` = 0.8（`tools/blender/sheetlib/road_parts.py`）。中心は路側線の交点から角の外へ (0.8, 0.8) で、円弧の中ほどが車道の半幅 3.6 の交点にちょうど来る（それより大きいと路面の角の外へ出る）。枝の口の点線は口の幅（両側の路側線のあいだ、-3.37〜3.37）だけに引き、そこから円弧の端（4.17）までは路面のまま
- 道路を 2 本ずつ並べた交差点（4×4・6×6）では、並べた道路のあいだ（路肩どうし）の角の円弧が交差点の中ほどで閉じ、角の丸い四角の枠が出る（6×6 では 4 つ。`docs/road_GE_junction_noswitch.png`）
- 切り替え: `blender/render.py` から `sheetlib` の `road_sheet` に `open_cross`（開いた十字）・`corner_arcs`（角の円弧）を渡す。分岐の絵の作りの `switch_ruts`・`priority_cross`・`drive_left`（`DRIVE_LEFT`。偽にすると優先道路の十字の停止線が右側通行の位置へ移る）も渡したまま

### 道路の壁・高架・橋脚・橋・トンネルの作り（#22）

道路 3 種に、共有の壁の way-object（`ami_wall_road_<single|back|center|front>`）、地上の基盤の版（`<道路>_base_<版>`。確定。2026-11-19、ユーザーの決定）、高架の 4 版（`<道路>_elev_<版>`）、橋（`<道路>_bridge`）、トンネル（`<道路>_tunnel`）、道路用の橋脚（`ami_pier_road`）を足した。作りは線路の壁・高架・橋（上の「壁の敷き方」「高架と橋脚の作り」「橋とトンネルの作り」）と同じで、断面と壁の形は blender-poc の高速道路の壁の版（`tools/blender/sheetlib` の `road_sheet` の `walls`）。設定は `blender/render.py` の「道路の壁の way-object・高架の 4 版・橋・トンネル・道路用の橋脚」、値は `blender/ami_dat.py`。

- 壁の way-object（`ami_wall_road_<版>`。`waytype=road`・`own_waytype=road`）: iss の都市高速の壁と同じく、タイルの端に立つコンクリートの壁。壁の形は 3 種で同じなので、シートは一般道路（`catalog.WALL_ROAD`）から 1 回だけ描く。上 4 行が奥、下 4 行が手前の絵で、雪の絵は無い（way-object にキーが無い）。`center` は線路の `ami_wall_rail_center` と同じく、側壁を持たず、行き止まりの端の壁だけを持つ（2026-11-19、ユーザーの決定。値・並びは線路の `center` と同じ）。壁の位置の基準は道路の絵と同じ `ROAD_CY`
- 近い斜めの分け合うタイル用の壁（`ami_wall_road_twin`。名前は確定。2026-11-19、ユーザーの決定）: 線路の `ami_wall_rail_twin` と同じ作り（速さ 1001。`nw`・`sw` の線は `back`、`ne`・`se` の線は `front` の絵）。敷き方も線路と同じ（「壁の敷き方」）
- 地上の基盤の版（`<道路>_base_<版>`。判断 1、確定。2026-11-19、ユーザーの決定）: 通常の版の路面から壁の外を削り、近い斜めの絵を持たず、カーブを斜めの形の別のセル（行 2 の列 5〜8）に描いて壁の無い側をタイルの端まで延ばしたもの（`tools/blender/sheetlib` の `road_sheet` の `curve_cells`）。壁は way の絵に描かず、同じ版の壁の way-object を重ねる。値は通常の版と同じ
  - 作った理由（2026-11-19、ゲームで確かめた）: 直線・T字・十字・坂・1 本の斜めは、通常の版に壁を重ねるだけで合う（`docs/road_struct_GE_WA_B.png`）。合わないのは 2 つ
    - 並べた車線の直角の曲がり: 通常の版のカーブは斜めの絵で、タイルの半分で切る。外の線と内の線のカーブのタイルの間に草の三角が出る（`docs/road_layout_pair_corner_plain.png`。レイアウト検証用モード、3 倍）
    - 近い斜め: 通常の版は近い斜めの絵を持つので、分け合うタイルは way 1 本（向きは十字）になる。way-object は 1 タイルに 1 つで、way-object の近い斜めの絵は makeobj が書けない（[reference](../../docs/reference/way-addon.md) の 10 章）。本体はそのタイルの壁を十字の絵で描き、車道の真ん中に壁の切れ端が立つ（`docs/road_wall_close_plain_zoom.png`。`../simutrans` の `obj/wayobj.cc` の `calc_image` の 542 行付近）
  - 基盤の版では、直角の曲がりのすき間が埋まり（`docs/road_base_pair_corner_zoom.png`）、近い斜めの分け合うタイルに way が 2 本置かれて `twin` の壁が合う（`docs/road_wall_close_base_zoom.png`）
  - 手本: iss の地上の道路も版ごとの way を持つ（`../refs/iss/src/way/road/ground.dat` の 139 行〜の `iss_wrg_0120_single`・`front`・`center`・`back`）。近い斜めの絵を持たず、カーブは斜めのセルと別のセル
  - ほかの選択肢: 通常の版から近い斜めの絵を外す（#21 の区画 G の作りが変わり、直角の曲がりのすき間は残る）、地上では近い斜めと並べた車線に壁を重ねない（基盤の版を作らない）
- 行き止まりの白線: 基盤の版・高架の版（壁を way-object に分ける版）は、行き止まりの白線を端の壁の内側の面で止める（`sheetlib` の `road_sheet`）。タイルの辺まで引いていたときは、壁と別に描いた way の絵で白線の端が端の壁の下の縁から 1px 出て、高架の行き止まり（区画 WV3）の手前の端の壁の下に明るい点が並んだ（`docs/road_GE_WV3_end_dot_before.png`・`_after.png`。4 倍。2026-11-19）
- 高架の 4 版（`<道路>_elev_<版>`、`system_type=1`）: 床（路面と基盤）と躯体だけで、橋脚と壁は描かない。基盤と躯体は路面の板の下へ `ROAD_BASE_DROP`（0.05）下げる。カーブは基盤の版と同じくカーブのセルに描く（斜めのセルのままだと、高架の複線の直角の曲がりに三角の穴が開き、下の地面と橋脚が見えた。`docs/road_layout_elev_pair_corner_before.png`・`_after.png`）。近い斜めは線路の高架と同じく way が 2 本で、`twin` の壁が合う（`docs/road_layout_elev_twin_zoom.png`）
- 道路用の橋脚（`ami_pier_road`。判断 3、waytype は確定。2026-11-19、ユーザーの決定）: waytype は線路用と同じ `tram_track`。iss の橋脚は全部 `tram_track` で、道路専用の橋脚は無い（`../refs/iss/src/util/pier/ground/pier.dat` の `iss_wsg_pier1`〜`6`）。本体は `track` の `system_type=7` として読むので（`../simutrans` の `descriptor/reader/way_reader.cc`）、道路のタイルに平行でも直交でも重ねて敷け、踏切は作られない。見本の区画 P で、pak128 の `Road_050`・AMI の道路と同じタイルに way 2 本で置けることと、地上の線路が横切るタイルでは線路とつながる（線路用の橋脚と同じ）ことを、スクリプトでタイルの中身を読んで確かめた
  - 形: 道の全幅を横切る柱（`ROAD_PIER_ACROSS` = 両側の壁の外の面の間。斜めは 1/√2）。上端は道路の高架の躯体の下面（`pier_sheet` の `top_drop`）。絵の位置は道路と同じ `ROAD_CY`
- 橋（`<道路>_bridge`）: 欄干を描かず、`single` の壁の way-object を重ねる（線路の橋と同じ）。床・躯体の高さは高架にそろえ、橋脚は道路用の橋脚と同じ全幅の柱を全部のタイルに立てる
  - 桁（POC の C6、判断 2、見せ方は確定。2026-11-19、ユーザーの決定）: iss の都市高速の橋（`../refs/iss/src/bridge/road/bridge.dat` の `iss_br_0120_bridge1`）と同じく、床の縁の下に青い鋼の帯を見せる。基盤と、その下の桁（`ROAD_GIRDER_D`）を青くし、壁の外の面まで出す（躯体のように内へ下げない）。iss の帯は 256px のセルで 4px（`../refs/iss/release/pak128/bridge/road/0120_bridge1.png` の南北のセル。2026-11-19 に測った）で、AMI も約 4px（`docs/road_bridge_girder_zoom.png`。4 倍）
  - 橋の上の way: 橋の道具を引いて架けると、橋の上の way は本体が選ぶ（橋の速さ以下で一番速い、平地の道路。`../simutrans` の `simtool.cc` の `tool_build_bridge_t::do_work` と `bauer/wegbauer.cc` の `weg_search`）。同じ速さの道路が複数あると、どれになるかは決まらない（見本では、一般道路の橋に blender-poc の `bpoc_expressway_wall_back` が載った）。道路の端のタイルを 1 回押して架けると、その道路が載る（`bauer/brueckenbauer.cc`）。橋の上の way は後から道路を敷いても替わらない。見本は端を押す形（`build_bridge_at`）で架ける
- トンネル（`<道路>_tunnel`）: 坑口の覆いは blender-poc の高速道路のトンネル（iss の都市高速の坑口が手本）で、路面・白線を道路の種類ごとに描く（`tunnel_sheet` の `road_profile`）。壁は坑口とトンネルの中を通して 1 本で敷く
- 分岐の絵: 今は基盤の版・高架の版も dat に入れていない（2026-11-20。上の「分岐の絵（switch 画像 1・2）」の冒頭）。区画 IB・IV で固定しても 1・2 が通常の絵と同じ番号で、高架の区画 L も通常の十字になる（`docs/road_GE_noswitch_struct.png`・`road_LO_EX_noswitch.png`。2026-11-20）。入れていたときの作り: 通常の版と同じ作り。T字の 1・2 は同じ白線の T字で轍のカーブだけが違い（上の「T字の 1・2 の轍」）、十字の 1・2 は優先道路の十字で、角の路側線は円弧でつなぐ。床・躯体・壁の持ち分は、通常の T字・十字と同じ経路（枝つき）で作る。区画 IB（基盤の版 single）・IV（高架 single）で T字 4 種と十字を 1・2 に固定し、3 種とも 10 枚が違う絵になること（`[check]` の行）と、T字の形で枝の口に壁が立たないことを撮って見た（2026-11-19。画像は記録 [2026-11-19_ami-road-structures-pins](../../docs/records/2026-11-19_ami-road-structures-pins.md)）。「2」が T字の形なので、高架の区画 L でも横切る道路の側に路側線が引かれた。開いた十字の「2」のときの絵は `docs/road_elev_L_cross_zoom.png`。橋は直線のセルだけなので出ない
- 値（仮）:

  | もの | 費用 | 維持費 | 速さ |
  |---|---|---|---|
  | 基盤の 4 版 | 通常の版と同じ | 同じ | 同じ |
  | 高架の 4 版（地上の 2 倍） | 10000・16000・40000 | 200・400・1000 | 道路と同じ |
  | 橋・トンネル（地上の 4 倍） | 20000・32000・80000 | 400・800・2000 | 道路と同じ |
  | 道路の壁（線路の壁と同じ） | 3000 | 60 | 1000（`twin` は 1001） |
  | 道路用の橋脚（線路用と同じ） | 1000 | 100 | 1 |

  費用・維持費は生活道路・一般道路・高速道路の順。登場年は道路と同じ（壁と橋脚は 1900）
- 描く対象: `ami_wall_road_<版>`・`<道路>_base_<版>`・`<道路>_elev_<版>`・`<道路>_bridge`・`<道路>_tunnel`・`ami_pier_road`（`blender/render.py`）。`ami_wall_road_twin` は `back`・`front` のシートを指す

### 版の並び

- 4 版は `single`（両側に壁）・`back`（奥だけ）・`center`（なし）・`front`（手前だけ）。iss・SIS と同じ並べ方
- 基盤の版: 基盤が壁の位置で止まる。同じ版の壁の way-object と組で使う（`center` の way-object は行き止まりの端の壁だけ）
- 高架の版: 床と床の下の躯体だけ。橋脚は描かない
- 橋: 欄干を描かない。壁の way-object を重ねる
- 分岐の絵（OTRP の switch 画像、1・2 の 10 枚）は線路の全部の way に入れる。道路は今は入れない（2026-11-20。「道路の作り」の「分岐の絵（switch 画像 1・2）」）。近い斜めは壁の無い way に入れる
- 雪の絵と汚れ（blender-poc の 6 章）は全部の way に入れる

### 高速線の作り（スラブ軌道、#20）

在来線と同じ版（通常・基盤 4 版・高架 4 版・橋・トンネル）を、線路の部品の差し替えで作った。壁・架線・橋脚は在来線と同じ way-object・way（`ami_wall_rail_*`・`ami_pier_rail*`）を重ねるので、高速線用のシートは無い。敷き方も在来線と同じ。

- 部品: `tools/blender/sheetlib/slab_parts.py`。下から `slab_bed`（コンクリート道床）・`slab_fill`（てん充層）・`slab`（軌道スラブ）・`slab_notch`（スラブの端の欠き込み）・`slab_stud`（円柱の突起）・`slab_fastener`（締結装置）で、レールは在来線の部品そのもの。設定は `blender/render.py` の `TRACK_SETTINGS`
- 在来線と同じもの: レールの高さと横位置、基準面 `bed`・`rail` の下げ幅、カーブ（斜めの絵）・T字・十字・分岐の絵・行き止まり・車止めの作り。断面は壁の内側（`WALL_U` = 2.15）に収まる
- コンクリート道床の基準面: 道床だけは `slab_bed`（値は `rail` と同じ下げ幅）に乗せる。`bed` のままだと、スラブが道床の手前へ 2px 寄って見えた。名前を `rail` と分けるのは、分岐の絵で作り直されるのが `rail` の部品だけだから（道床は T字・十字の形のまま）。この分だけ、道床は基盤・壁に対して在来線の道床より 2px 下に見え、pak128 標準の線路とのつなぎ目で帯の中心のずれが在来線の 0〜0.5px から 2.0px になる（`seam_judge.py`、幅が違うので参考の値。草の線は無し。2026-11-19）
- 割り付け: スラブは直線でタイルに 2 枚、斜めも 2 枚で、継ぎ目はタイルの辺に来ない。突起は継ぎ目（スラブの長手の両端）の、レールの間の中央に立つ。締結装置は継ぎ目の間に偶数組を等間隔に置くので、タイルの辺の前後で間隔がそろう。直線（南北・東西）だけは、締結装置をタイルの辺の上から 0.625 おきに置き（画面で 4px おき）、横切る幅を 0.26 にした（1/2 の画面で粒に見えないように。#89）。このため直線では、締結装置が継ぎ目の上にも来る
- 分岐のすき間埋めは道床だけ（`bed_fills`）。スラブまで埋めると、経路の間が大きな明るい三角になる
- 汚れ: 在来線の汚れと同じ名前（`rust0`・`rust1`・`oil`・`sleeper_rust`）の差し替えで、スラブの上面に乗せ、スラブの縁と継ぎ目で止める。帯は在来線より狭く、色はスラブの色から混ぜる。`sleeper_rust` は締結装置の周りのさびになる
- 雪: 道床・てん充層・スラブ・欠き込みは雪の色、突起と締結装置は雪の上に少し見える色（`SLAB_SNOW_SKIN`）。レールと雪の上の汚れは在来線と同じ
- 値: 480 km/h。高架・橋・トンネルの費用の倍率は在来線と同じ（`ELEV_COST_K`・`BRIDGE_COST_K`・`TUNNEL_COST_K`）。アイコン・カーソルは下の「アイコン・カーソル」（数字の 480）

| 層 | 寸法（部品の単位。1 単位 ≈ 9px） | 色 |
|---|---|---|
| コンクリート道床 | 下面の半幅 1.72・上面の半幅 1.68、高さ 0〜0.08 | スラブより暗い灰色のまだら |
| てん充層 | 半幅 1.07、高さ 0.08〜0.11 | ほぼ黒 |
| 軌道スラブ | 半幅 1.02、高さ 0.11〜0.15。長さの目安 5、すき間 0.2 | 明るい灰色のまだら |
| 突起・欠き込み | 半径 0.24・0.36。突起の上面 0.19 | 中間の灰色・てん充層の色 |
| 締結装置 | 沿う向き 0.22 × 横切る向き 0.34（直線は 0.26）、高さ 0.15〜0.20、間隔の目安 0.625 | 黒 |
| レール | 在来線と同じ（中心から 0.417〜0.517、高さ 0.19〜0.30） | 赤茶色 |

手本の扱い: 層の順と形は上の「見た目の手本」の書き起こしから。iss のスラブ（`../refs/iss/src/way/rail/track_slab.dat`・`standard_slab.png`）は、タイル全面が灰色で壁を絵に焼き込む別の作りなので、形は取り入れていない。

確認画像は `docs/rail_slab_*.png`（通常・拡大・分岐・基盤と壁・架線・高架・橋・トンネル・雪、`layout` はレイアウト検証用モード、`seam_standard` は pak128 標準の線路とのつなぎ目の判定）。

### 弾性まくらぎ直結軌道の作り（#62）

在来線と同じ版（通常・基盤 4 版・高架 4 版・橋・トンネル）を、在来線の部品の使い回しで作った。違うのは道床だけで、在来線の砕石を、平らなコンクリートの道床に替えた。本物はまくらぎがゴムの靴（防振材）をはいてコンクリートに埋まる。在来線とは道床で見分ける（2026-11-21、ユーザーの決定。[ADR 0006](../../docs/adr/0006-ami-track-variants-by-track-form.md)）。壁・架線・橋脚は在来線と同じ way-object・way を重ねる。敷き方も在来線と同じ。

- 設定: `blender/render.py` の「弾性まくらぎ直結軌道」（`CONC_*`）。種類は `blender/catalog.py` の `RAIL_CONCRETE`
- 在来線と同じもの: まくらぎ（寸法・間隔・色）・レール・汚れの帯・車止め・基準面（`bed`・`rail`）・道床の底の幅（±1.9）と上面の高さ。カーブ・T字・十字・分岐の絵・行き止まりの作りも同じ
- 道床: 形（上面の半幅 ±1.45 の肩から、底の ±1.9 まで斜面）は在来線と同じで、塗りの範囲も全版で在来線と同じ。最初は上面を ±1.75 まで延ばしてほぼ垂直の縁にしたが、奥の縁が在来線より 1px 外まで塗られ、坂の寄りとつなぎ目の中心のずれが在来線より 0.5px 大きかったので、在来線と同じ所で止めた（2026-11-21、ユーザーの決定。`CONC_BED_HALF`）。色はまくらぎより暗い灰色の細かいまだら（壁・基盤のコンクリートと同じ細かさ）。赤みは足さない（`slope_measure.py` がレールを「赤 − 青」で探す）
- 描かないもの: まくらぎの靴の縁と、中央の排水溝。靴の縁は画面で 1px 未満（[way-addon.md](../../docs/reference/way-addon.md) の 12 章）で、縁を 0.12 単位（約 0.9px）まで広げても、まくらぎの間が暗くなるだけで靴には見えなかった。排水溝は、くどさ（同じリファレンスの 11 章）を増やすので省いた
- 雪: 在来線と同じく、積もったばかりの雪（道床・まくらぎ・汚れは雪、レールだけが出る）。雪の絵は在来線と画素まで同じで、雪では見分けない（#70、2026-11-21、ユーザーの決定）
- 値: 240 km/h。高架・橋・トンネルの費用の倍率は在来線と同じ。アイコン・カーソルは下の「アイコン・カーソル」（数字の 240）

確認画像は `docs/rail_concrete_cmp_<気候>_<区画>.png`。同じ区画を左から在来線・弾性まくらぎ直結軌道・高速線の順に等倍で並べ、黄色の枠の中を下に 4 倍で拡大した（区画は輪と十字 `B`・行き止まりと 1 タイル `AFC`・坂 `DE`・分岐 `H0`・基盤 back `B_B`・高架 single `VS_B`・壁の複線 `W1`・橋 `BT_B1`・トンネル `BT_T2`。降雪側は `B`・`AFC`・`DE`・`VS_B`・`BT_B1`。`seam_dg`・`seam_steep` は `ingame/seam_slope_check.sh` の斜めのつなぎ目と急坂の十字）。上の画面は同じ見本を種類ごとに別に敷いて撮ったもの。経緯とくどさ・つなぎ目・坂の値は記録 [2026-11-21_ami-rail-concrete](../../docs/records/2026-11-21_ami-rail-concrete.md)。在来線の色を変えた（#70）後の見分けは `docs/ballast_color_<気候>_<区画>.png`（左から在来線の変える前・変えた後・弾性まくらぎ直結軌道・高速線（スラブ）。記録 [2026-11-21_ami-ballast-color](../../docs/records/2026-11-21_ami-ballast-color.md)）

手本の扱い: 名前と速度は iss の `iss_wtg_0240_*`（`../refs/iss/src/way/rail/track_concrete.dat`）に当たる。iss はまくらぎの材料（木・コンクリート）で種類を分け、道床は砕石のまま。AMI の在来線はすでに PC まくらぎなので、iss の分け方は取り入れず、道床の形式で分けた。iss の砕石の点描は、くどさの物差しで「くどい」に出る（[way-addon.md](../../docs/reference/way-addon.md) の 11 章）ので、まねていない。

### フローティング・ラダー軌道の作り（#67）

弾性まくらぎ直結軌道と同じ版の一式を、同じ部品の使い回しで作った。路盤は直結軌道のコンクリートの道床で、形・塗りの範囲は在来線と同じ。横に並ぶまくらぎの代わりに、レールの下に PC の縦梁を 2 本通し、梁の間を暗い帯にし、鋼管の継材を渡した。本物は、縦梁と継材を組んだはしご状のまくらぎ（ラダーマクラギ）を、防振材で路盤から浮かせる（鉄道総研のページ。高架橋・橋梁の防振軌道に使う）。どの形式にするか・見分け方・値は、2026-11-21 にユーザーが決めた（[#67](https://github.com/128na/simutrans-addon-dev/issues/67)）。壁・架線・橋脚は在来線と同じ way-object・way を重ねる。

- 設定: `blender/render.py` の「フローティング・ラダー軌道」（`LADDER_*`）。種類は `blender/catalog.py` の `RAIL_LADDER`
- 見分け方: 在来線・直結軌道（まくらぎがタイル 1 辺に 16 本）とは、途切れない 2 本の梁と梁の間の暗い帯で見分ける。スラブ（幅の広い板と黒い締結装置）とは、梁の細さで見分ける
- 寸法:
  - 梁は経路の中心から 0.30〜0.73（幅約 3.1px。梁の間は約 4.3px）で、高さはまくらぎと同じ。梁の間は、1/2 の画面で縁が粒に見えないよう、0.23 から広げた（#89）。
  - 継材はタイル 1 辺に 4 本（2.5 単位おき。タイルの継ぎ目でそろう）で、線路に沿う幅は 0.2（約 1.4px）。
  - 本物の梁の幅・継材の間隔は確かめていない（鉄道総研のページの本文に無い）。画面の見え方から決めた。
  - 本物で 1px 未満の継材は太らせた。暗い帯の上で見えるように、帯より明るい鋼管の灰色にした。
- T字・十字・分岐の絵: 直線の経路は梁、分岐の側（斜めの部分）は在来線のまくらぎにした（`sheetlib` の `diag_replace`）。Y字分岐の絵は分岐の側だけなので、まくらぎだけになる。三方分岐は直進が梁で、両側の枝がまくらぎ
- 雪: 在来線・直結軌道と同じく、積もったばかりの雪の絵で、梁・継材も雪になり、レールだけが出る。雪では見分けない（#70 の決定に合わせた）
- 値:
  - 速度は 360 km/h（iss の `track_ladder.dat` と同じ）。
  - 費用 35000・維持費 700（直結軌道とスラブの間）。
  - 登場年は 1990。ゲームの中の並びで決めた値で、本物の年は確かめていない。
  - アイコン・カーソルは下の「アイコン・カーソル」（数字の 360）。

確認画像は `docs/rail_ladder_cmp_<気候>_<区画>.png`。同じ区画を、左から直結軌道・ラダー・スラブの順に等倍で並べ、黄色の枠の中を下に 4 倍で拡大した（区画は輪と十字 `B`・分岐 `H0`・行き止まりと 1 タイル `AFC`・坂 `DE`・高架 single `VS_B`、降雪は `B`）。分岐の追加画像は `docs/rail_ladder_ex_temperate_E.png`（左から直結軌道の Y字 東、ラダーの Y字 東・三方分岐 東）。経緯と値は記録 [2026-11-21_ami-rail-ladder](../../docs/records/2026-11-21_ami-rail-ladder.md)

手本の扱い: iss の `iss_wtg_0360_ladder_*`（`../refs/iss/src/way/rail/track_ladder.dat`）は、コンクリートの面に明るい梁を 2 本描き、継材は描かない。AMI は継材を太らせて描き、梁の間を暗くした。

### 壁の敷き方（在来線、#16）

基盤の版の way（`ami_rail_ballast_base_<版>`）を敷き、同じ経路に同じ版の壁の way-object（`ami_wall_rail_<版>`）を重ねる。`center` の壁の way-object（`ami_wall_rail_center`）は側壁が無く、行き止まりの端の壁だけを持つ（ユーザーの指摘、2026-11-17。架線つきの版では `center` も架線の部品を持つので、壁の way-object も 4 版にそろえた）。

- 絵の作り: 基盤の版の way は、通常の版の道床の下に基盤を敷き、壁のある側は壁の位置で、壁の無い側はタイルの端で止める。壁は way の絵に描かず、壁の way-object のシートに描く（`blender/render.py` の `BASE_VARIANTS`、`tools/blender/sheetlib` の `wall_sheet`）。壁のシートは上 4 行が奥（`backimage` など、車両より先に描く）、下 4 行が手前（`frontimage` など、車両より後に描く）。カメラに近い壁が手前の絵になる
- 行き止まり: 側壁を閉じた側のタイルの端まで延ばし、端の壁をタイルの端に立てる（ユーザーの指摘、2026-11-17）。レールの終点と車止めは通常の版と同じ（`END_FROM_EDGE`）。`center` も端の壁はある
- カーブ: 通常の版と同じく斜めの絵で表す。ただし基盤の版は、カーブのセルを斜めのタイルと別に描き、基盤の壁の無い側を削らない（複線の直角の曲がりで、内側の線の外側に草が三角に出たため。`curve_cells`）
- 継ぎ目（ユーザーの指摘、2026-11-17）: 坂の壁は、上がった側の端の最後の 1 列が欠けて、坂の上の十字・T字の壁との間に 1px のすき間が出た。坂のセルだけ、壁をタイルの外へ長めに残し、持ち分を左右へ 1 列広げた。T字・十字では、斜めの部分の通り道が反対側の壁（直線の側の壁）の端まで削り、隣の直線との継ぎ目に 1px の縦線が出た。斜めの部分の通り道は、その部分がある側の壁だけを削り、斜めの部分の壁はタイルの辺で切る（`tools/blender/sheetlib` の `assemble`）
- 奥と手前の決め方（POC の C5）: 版の「奥」「手前」は、南北の線なら西が奥・東が手前、東西の線なら北が奥・南が手前。カーブ・T字・十字のタイルは南北の線（T字は通り抜ける線）の版に合わせる。複線の輪では、角のタイルを南北の辺と同じ版で敷く（`sample.nut` の区画 W1）。画面で右と左に曲がる角では外の線と内の線の版が角の前後で入れ替わり、角のタイルを東西の辺の版にすると角に草の穴が開く（[#94](https://github.com/128na/simutrans-addon-dev/issues/94)、記録 [2026-11-21_ami-double-curve-base](../../docs/records/2026-11-21_ami-double-curve-base.md)）。way は東西の辺を先に敷いて南北の辺で角を上書きし、壁は南北の辺を先に敷く（同じ速さの壁を後から敷くと、前の版のまま向きだけ足される）。遊ぶ人向けの説明は下の「[遊ぶ人向けの敷き方](#遊ぶ人向けの敷き方)」。斜めのタイルでは、奥の版は `nw`・`sw` の壁がタイルの角の側、`ne`・`se` の壁が中心の側に立つ（手前の版はその逆）
- 近い斜め（POC の C2）: 1 タイルに way-object は waytype ごとに 1 つなので、分け合うタイル（way が 2 本）には `back` と `front` を両方は置けない。分け合うタイルには、`back`・`front` を敷いた後に `ami_wall_rail_twin` を 1 タイルずつ重ねる。OTRP は分け合うタイルの way-object 1 つで 2 本の線を、それぞれの斜めの絵で描く（`../simutrans` の `obj/wayobj.cc` の `two_legs`）。`ami_wall_rail_twin` は `nw`・`sw` の線に `back` の壁、`ne`・`se` の線に `front` の壁の絵を使うので、近い斜めの複線は西の線（x の小さい方）を `back`、東の線を `front` にする。速さの値を `back`・`front` より 1 大きくしてあり、後から重ねると置き換わる（同じ速さの way-object を重ねても、前の版のまま向きだけ足される。`obj/wayobj.cc` の `extend_wayobj`）。置き換えると、隣のタイルの壁が分け合うタイルの側へつながらなくなる（前の way-object が消えるときに隣の向きを外し、新しい方はつなぎ直さない。`~wayobj_t`）。`twin` を置いた後に、`back`・`front` を同じ経路にもう一度敷く（`twin` の方が速いので、分け合うタイルは `twin` のまま）
- 名前（2026-11-18）: ユーザーの指定で、`single` より後ろに来る `twin` にした。ゲームの道具の一覧は waytype・速さ・名前の順に並ぶ（`../simutrans` の `obj/wayobj.cc` の `compare_wayobj_desc`）ので、`back`・`center`・`front`・`single`（1000）・`twin`（1001）、続いて架線つきの 4 版（1100）・`twin_catenary`（1101）の順になる
- 値（仮）: 壁の way-object は費用 3000・維持費 60・登場 1900、速さ 1000（`blender/ami_dat.py` の `WALL_VALUES`）。架線ではない（`own_waytype=track`）ので、速さの値は列車の速さを縛らない
- 確かめたゲーム: `OTRPv64_3.exe`（2026-11-17）。分け合うタイルの 2 本の線の描き分けは OTRP の機能で、本家での近い斜めの壁の見え方は確かめていない
- 渡り線（#101、2026-11-21）: 並べた線の間に渡り線を敷くと、渡り線の経路のタイル（両端の T字と、端の直線のタイル）の way が、渡り線を敷いた way の版に置き換わる。版はどれも同じ速さなので、Ctrl を押さずに敷いても置き換わる（[reference](../../docs/reference/way-addon.md) の 6 章）。基盤は壁の側を壁で止めるので、置き換わったタイルに草の帯が出て、壁の外へ基盤がはみ出す。**渡り線を敷いた後は、本線をそれぞれの版でもう一度敷き直す**（壁の way-object は敷き直さなくてよい。way-object の絵は way の向きで決まり、渡り線に壁を敷いても敷かなくても画面は同じ）。`docs/rail_crossover_relay.png` は、本線と壁の後に上の線の版で渡り線を敷いたまま（左）と、その後に本線をそれぞれの版で敷き直したもの（右）（壁だけの版、3 本並び、温暖）。敷き直した後は、渡り線の前に本線を敷き直してから壁を敷いたものと、架線つきの壁は画素まで同じ、壁だけの壁は道床の縁の草の 1〜3 画素（敷いた場所の地面の模様の差）だけが違った（4 つの線の並びと温暖・降雪の全部）。見本は `ingame/crossover_wall.sh`（下の「導入と検証」）。基盤の壁の側をタイルの端まで塗れば置き換わっても見えない（iss の作り）が、壁のある全部の線の見た目が変わるので、ベータでは変えない（2026-11-21、進捗管理の判断）

### 架線の作り（在来線、#17）

壁の way-object に架線を持たせた版（`ami_wall_rail_<版>_catenary`、電化）を、壁だけの版と同じ組み方で敷く。基盤の版の way（`ami_rail_ballast_base_<版>`）に、同じ版の架線つきの壁を同じ経路に重ねる。壁の部分は壁だけの版と同じ形（同じ設定で描き、架線の部品を足しただけ）。

- 部品: 柱・梁・吊り金具・線・ハンガー（`tools/blender/sheetlib/catenary_parts.py`。レイアウト検証用モードの色は柱が水色、梁が橙、吊り金具が黄緑、トロリ線が赤紫、ちょう架線が紫、ハンガーが桃）
- 吊り金具とハンガー: 吊り金具は梁の中ほどからちょう架線へ、ハンガーはちょう架線からトロリ線へ下ろす、線と同じ色の 1px の縦線。ハンガーは pak128 と同じく画面の横 16px ごと（直線は 1 タイルに 4 本、画面で横向きの斜めも 4 本）。画面で縦向きの斜めは 2 本の線が重なるので無い（pak128 も無い）
- 線: pak128 の架線（`classic_catenary` など）と同じく上下 2 本。上がちょう架線、下がトロリ線で、どちらも 1px。高さは pak128 にそろえた（タイルの中心で地面から下 約 24px・上 約 28px。[reference](../../docs/reference/way-addon.md) の 10 章）。画面で縦向きの斜めでは 2 本が重なって 1 本に見える（pak128 も同じ）
- 柱の位置: 壁の上（壁の厚みの真ん中）に立つ。線路に沿う向きは、経路の上でタイルの中心にいちばん近い点（直線・行き止まりはタイルの中心、斜めは斜めの部分の中ほど）。1 タイルに 1 組
- 版と柱: 壁と同じ決め方で、`single` は両側、`back` は奥、`front` は手前に柱が立つ。`center` は柱が無く、梁と線だけ（行き止まりの端の壁は、壁だけの版と同じく持つ）
- 梁: 柱の上端の高さで線路を横切り、壁のある側は壁の外の面で止まり、壁の無い側はタイルの端まで延びる。複線で `back`・`center`・`front` を並べると、梁が隣の線の梁とつながって 1 本の門になる（iss の架線と同じ考え方）。斜めの梁は、経路から反対の角まで届く長さ（`CAT_BEAM_REACH_DIAG`。最も遠い角の先まで `CAT_BEAM_OVERLAP_DIAG` 余らせる）で作り、タイルの角の先で切る（壁のある側は壁の外の面）。斜めの線を隣のタイルに並べた複線・3 本並び（線の間が タイル × √2）では、梁が線の間のタイルを横切って、タイルの角で隣の線の梁とつながる。前は梁をタイルの中心の先までにしていて、この並べ方で 1 行おきに梁の間に 30px ほどの隙間が見えた（2026-11-18、ユーザーの確認用の保存データ。その前の、角と中心でちょうど止めて 2〜5px の隙間が見えた指摘も同じ日）。`docs/rail_catenary_diag_beams.png` が直した後
- 分岐・十字（T字・十字・分岐の絵・ex 画像のセル）: 線は全部の経路に張る。柱・梁・吊り金具は、通り抜ける直線の経路にだけ、直線のセルと同じ形で立てる（柱は版の壁の側だけ、梁は壁の無い側へタイルの端まで延び、渡り線の上を横切る。十字は南北・東西の両方の直線に立つ）。前は線だけで柱・梁を立てず（経路ごとに門ができて重なるのを避けた）、壁つきの線の間の渡り線では、渡り線の画面で縦向きの斜めの線が線路の間に立つ細い柱に、横向きの斜めの線とハンガーが梁に見えた（#101。2026-11-21、進捗管理の判断で直した。見た目はユーザーが確かめる）。`docs/rail_crossover_catenary_<temperate|snow|pair>.png` が直す前（左）と後（右）で、等倍の画面（`temperate`・`snow` は 3 本並び、`pair` は back+front）。`zoom` は 3 本並びの T字のタイルを 3 倍に拡大した前と後。iss は T字・十字に single の絵（両側の柱と梁）を使う（`docs/rail_crossover_iss.png` の左が iss、右が AMI の後）
- 奥と手前の絵: 奥の柱は奥の絵（`backimage`、車両より先に描く）、手前の柱・梁・吊り金具・線は手前の絵（`frontimage`、車両より後に描く）。iss の架線と同じ分け方
- 寸法（仮。`catenary_parts.py` の `CAT_*`。高さは路盤から。手本は柱・梁が iss の架線、線が pak128 の架線（[reference](../../docs/reference/way-addon.md) の 10 章））:

  | 値 | 定数 | 今の値 | 画面の目安 |
  |---|---|---|---|
  | 柱の上端の高さ | `CAT_POLE_TOP` | 5.2 | 約 41px |
  | 柱の横位置（経路の中心から） | `CAT_POLE_U` | 2.26（`WALL_U + WALL_W / 2`） | 壁の厚みの真ん中 |
  | 柱の太さ | `CAT_POLE_S` | 0.35 | 約 3px |
  | トロリ線（下の線）の高さ（下の面） | `CAT_WIRE_Z` | 3.0 | タイルの中心で地面から約 24px |
  | ちょう架線（上の線）の高さ（下の面） | `CAT_MESSENGER_Z` | 3.51（`CAT_WIRE_Z + H / 4`） | トロリ線のちょうど 4px 上（約 28px） |
  | 線の太さ（直線・画面で横向きの斜め） | `CAT_WIRE_W`・`CAT_WIRE_H` | 0.05・0.09 | 1px（直線は 1 行に 2px ずつの階段） |
  | 線の横幅（画面で縦向きの斜め） | `CAT_WIRE_W_DIAG` | 0.12 | 1px |
  | 斜めの線のずらし | `CAT_DIAG_SHIFT`・`CAT_DIAG_SHIFT_Z` | 半画素 | 線の中心を画素の中心に乗せる（縦向きは右へ、横向きは上へ） |
  | 梁の高さ・厚み | `CAT_BEAM_H`・`CAT_BEAM_T` | 0.35・0.25 | 約 3px・2px |
  | 斜めの梁の長さ（経路から） | `CAT_BEAM_REACH_DIAG` | 11.1（`TILE * 1.5 / √2 + CAT_BEAM_OVERLAP_DIAG`） | 最も遠い角の先まで |
  | 斜めの梁の長さの余り | `CAT_BEAM_OVERLAP_DIAG` | 0.5 | 約 4px |
  | 吊り金具・ハンガーの太さ | `CAT_HANGER_PX` | 1.0 | 1px（画面の横の位置を画素の中心に乗せる） |
  | 1 タイルのハンガーの数 | `CAT_DROPPER_N`・`CAT_DROPPER_N_DIAG` | 4・4 | 画面の横 16px ごと |

- 描き方: 架線は高さのある部品で、持ち分を上へ `CAT_RISE`（約 47 行）広げる（壁だけの版は 11 行）。線は 1px なので、輪郭の半透明の画素を捨てる処理では消える。線だけを描き直して、半分以上覆われた画素を残す（`Part.thin`。[tools/README.md](../../tools/README.md)）。斜めの線は、中心が画素の境に来ると 2 列（2 行）に分かれるので、半画素ずらす。斜めの梁はタイルの角の先まで残し、持ち分を左右へ 1 列広げて描く（`Part.widen`）
- 値（仮）: 費用 4000・維持費 100・登場 1900、速さ 1100（`blender/ami_dat.py` の `CATENARY_VALUES`）。`own_waytype=electrified_track`（電化）。架線の速さは電化した編成の最高速度を縛るので、いちばん速い線路（高速線 480 km/h）より大きくした。壁だけの版（1000）より速いので、壁だけの版の上に敷くと架線つきに置き換わる。逆に、架線つきの上に壁だけの版を敷いても置き換わらない（撤去してから敷く）
- 壁だけの線の一部を電化するとき: 架線つきの版で置き換えると、境の外側の壁だけのタイルが行き止まりの絵（線路を横切る端の壁）になる（置き換えで、隣の way-object の向きから境の側が外れる。[reference](../../docs/reference/way-addon.md) の 10 章）。架線つきを敷いた後に、壁だけの版を境のタイルまで敷き直す（境のタイルは架線つきの方が速いので置き換わらず、向きだけ足される）。ゲームで確かめた（2026-11-18、`OTRPv64_3.exe`。`docs/rail_catenary_upgrade_before.png` が敷き直す前、`rail_catenary_upgrade.png` が後）
- 近い斜め: 分け合うタイルには、壁だけの版の `ami_wall_rail_twin` の代わりに `ami_wall_rail_twin_catenary`（速さ 1101）を重ね、`back`・`front` の架線つきの版を同じ経路にもう一度敷く（敷き方は「壁の敷き方」と同じ。`sample.nut` の区画 WE）。1101 なので、架線つきの 4 版（1100）と壁だけの `twin`（1001）を置き換える。絵は `twin` と同じ組（`nw`・`sw` の線は `back`、`ne`・`se` の線は `front` の版）で、斜めの梁だけを短くしたシート（`src/ami_wall_rail_twin_catenary_<back|front>.png`。`blender/render.py` の `TWIN_FROM`）を指す
- 分け合うタイルの梁の長さ: 分け合うタイルでは隣の線が タイル / √2 しか離れていないので、通常の 4 版の斜めの梁（反対の角まで。上の「梁」）では、隣の線の外の壁から 5px ほどはみ出した。分け合うタイルと、斜めの線を隣のタイルに並べた複線は同じ斜めのセルを使うので、分け合うタイル用のシートだけ、梁をタイルの中心の先まで（`CAT_BEAM_REACH_TWIN`）にした（2026-11-18、ユーザーの判断）。2 本の線の梁は中心の先で重なってつながり、外の側は壁の外の面で止まる。`twin_catenary` を置く前は、分け合うタイルは先に敷いた `back` の架線つきの版のままで、梁がはみ出し、手前の線の柱が線の間に立った（`docs/rail_catenary_close_pair.png`。直した後は `rail_catenary_WE2a.png`）
- 描く対象: `ami_wall_rail_<版>_catenary`（`blender/render.py`。way のシートは書かない。way は基盤の版の対象が書く）

### 高架と橋脚の作り（在来線、#18）

高架の版の way（`ami_rail_ballast_elev_<版>`、`system_type=1`）を敷き、壁・架線は地上と同じ way-object（`ami_wall_rail_<版>`・`ami_wall_rail_<版>_catenary`。近い斜めの分け合うタイルは `twin`・`twin_catenary`）を、同じ経路の高架の高さに重ねる。高架の真下の地面には、橋脚の way（`ami_pier_rail`）を同じ経路に敷く。

- 絵の作り: 高架の版は、基盤の版と同じ絵（道床・まくらぎ・レール・基盤。基盤は壁の位置で止まり、壁の無い側はタイルの端まで）の下に、躯体（桁）を足したもの。橋脚と壁は描かない（`blender/render.py` の `rail_ballast_elev_*`、`tools/blender/sheetlib` の `elev_body`・`write_walls`）。躯体は基盤と同じ決め方で削り、壁のある側は壁の外の面から `ELEV_BODY_INSET` 内で止め（床の縁が見える）、壁の無い側はタイルの端まで（並べた線の躯体とつながる）。斜めの壁の無い側は、基盤と同じ傾き（`DIAG_OPEN_UNDERCUT`）の下ほど中心線へ寄る切り口で削る。切り口は路盤の面の高さで近い斜めの 2 本の真ん中より `ELEV_BODY_DIAG_INSET` 内を通り、躯体の上面（基盤の下面）では約 1.35 内、下面では線の中心線を越える。この面はカメラから見えない（縦に切ると、近い斜めの複線で、奥の線の躯体の切り口が手前の線の床の上に三角に出た。2026-11-18）。床に隠れて見えないが、壁の無い側の橋脚の上端は躯体に届かない
- 床と躯体の面（#78。2026-11-21、ユーザーの決定）: 線路 4 種の基盤の版・高架の版・橋の、基盤の板と躯体（桁）は、打ち放しのコンクリート。元の色を中心に ±12% のまだら（粒は約 4px。道路のコンクリートと同じ振れ幅）に、約 30px の大きなしみで最大 15% 暗くする。継ぎ目の線は描かない。模様はタイルの 1 辺を周期にしてあり、タイルの辺で切れない（`blender/render.py` の `TRACK_SURFACE`・`TRACK_MAT_SKIN`、`tools/blender/sheetlib` の `tiled_concrete_material`。`track_sheet` が描き分けの `mat_skin` で材質を名前で差し替える）。線路の壁（架線つきの版を含む）・橋脚（単柱・門型）・橋の柱・坑口の躯体も同じ材質にそろえた（#83。2026-11-21、ユーザーの決定。`TRACK_WALL_SKIN`・`TRACK_PIER_SKIN`・`TRACK_GATE_SKIN`。比べた案は `blender/wallpier_calib.py`、記録 `docs/records/2026-11-21_ami-wall-pier-surface.md`）。道路の壁・橋脚は道路のコンクリートのまま。雪の絵では基盤の上面は雪のまま。段を見比べた案は `blender/surface_calib.py`・`ingame/surface_sample.nut`・`ingame/surface_capture.sh` と `rounds/ami_surface_calib.pak`（記録 `docs/records/2026-11-21_ami-surface-detail.md`）
- 橋脚の絵: 経路の中ほど（直線・行き止まり・T字・十字はタイルの中心、斜めは斜めの部分の中ほど）の下に、線路を横切る向きに長い柱を 1 本立てる。上端は高架の躯体の下面に合わせ、高架の床と同じ基準面で動かす。坂は地面の坂を当てる（本体の高架は地面の坂を引き継ぐ。`../simutrans` の `bauer/wegbauer.cc` の `build_elevated`）。近い斜めの絵（close1・close2）は 2 本の柱。分岐の絵は T字・十字と同じ柱（`tools/blender/sheetlib` の `pier_sheet`）
- 門型の橋脚（`ami_pier_rail_gate`。#18 の追加、2026-11-18）: 単柱の橋脚（`ami_pier_rail`）とは別の way で、どちらかを選んで敷く。高架の直下に道路を並行して通せ、十字で横切る道路とも重ならないよう、柱をタイルの角（辺の両端）に立て、上に梁を渡す（`tools/blender/sheetlib` の `pier_gate_sheet`・`_gate_parts`）。高さ・基準面・坂・持ち分は単柱と同じ
  - 直線・坂・T字・十字: 経路が出る手前の辺（南・東）ごとに、その辺に沿う門（両端の角に柱、柱の間に梁）を立てる。奥の辺（北・西）の門は奥のタイルの手前の門が兼ね、継ぎ目ごとに門が 1 つになる（両側のタイルが描くと背中合わせの 2 つになる）。直線では各タイルの四隅に柱が立ち、継ぎ目ごとに線路を横切る梁が渡る。十字は 3 つの角に柱と南・東の梁（北西の角の柱と北・西の梁は奥のタイルが描く）
  - 行き止まり: 閉じた側の辺にも門を立てる（床の端を支える）。1 タイル（single）は北と南の辺
  - 斜め（カーブも同じ絵）: 経路の内側（タイルの中心）に柱を 1 本立て、外側の角の近くまで、経路を横切る片持ちの梁を出す。近い斜め（close1・close2）は中心の柱を 2 本の線で分け合い、梁を両側へ出す。中心の柱は、経路より手前にある `diag_nw` だけ手前の絵にも描き、ほかの斜め（close1 を含む）は奥の絵だけに描く（`tools/blender/sheetlib` の `_GATE_CENTER_FRONT`）
  - 作り: iss の橋脚 5・6（`../refs/iss/src/util/pier/ground/pier.dat` の `iss_wsg_pier5`・`iss_wsg_pier6`、`pier5_rear.png`・`pier5_surface.png`）に合わせ、奥の絵（`image`）に全部の柱と梁、手前の絵（`frontimage`。乗り物の後に描く）に北西の角の柱と経路より奥の中心の柱を除いたものを描く。シートは奥の絵が行 0〜3、手前の絵が行 4〜7（`PIER_GATE_FRONT_ROW`。`blender/ami_dat.py` の `PIER_FRONT_ROW`）
  - 高架下の高さ（2026-11-18）: pak128 の 2 階建てバスが余裕をもって通れるよう、躯体を浅くし（`ELEV_BODY_D` を 1.0 から 0.25 に）、梁の下面を地面から約 26px、躯体の下面を約 27px にした（前は梁が約 19px、躯体が約 21px で、2 階建てバスの屋根より低かった）
    - 車両の高さ: 車両のシートの行 1 の、直線を走る向き（`W`・`N`・`E`・`S`）の絵で、左右の端の列（車体の縦の角）の見える長さを測った。2 階建てバスの `AEC_Aclo_Regent_III`（`../refs/pak128/vehicles/road-psg+mail/aec_aclo_regent_iii.png`）と `CST_Urban_City_DD`（`cst_urban_city_dd.png`）が約 20px で最も高い。2 階建ての観光バス `irisbus_magelys_hdh.png` は約 17px、大型トラック `../refs/pak128/vehicles/road-cargo/big_erztruck.png` は約 13px、`40ft_container_trailer.png` はそれより低い
    - 手本: iss の橋脚 5 は枠の下面が地面から約 27px（`pier5_surface.png` の直線のセルで、手前の柱の見える長さ）。iss の高架（`../refs/iss/release/pak128/way/rail/standard_slab_e_single.png`。`../refs/iss/src/way/rail/track_slab.dat` が指す）は床の下に躯体が無く、絵の下端が床の高さ（地面から 32px）
    - 確かめ方: 区画 R の R1 に車庫を置き、`CST_Urban_City_DD` を高架の下の並行の道路と、横切る道路に走らせて撮った（`docs/rail_elev_gate_bus_*.png`）。梁と柱の上端は躯体に食い込ませる（`PIER_GATE_BEAM_EMBED`）。躯体の下面より下に見える梁の厚みは `PIER_GATE_BEAM_SHOW`
  - 名前と並び: ゲームの道具の一覧は waytype・速さ・登場年・名前の順（`../simutrans` の `bauer/wegbauer.cc` の `compare_ways`）で、値が同じなので `ami_pier_rail` の直後、`ami_pier_road` の前に並ぶ。値（費用・維持費・速さ）は単柱と同じ（仮）
- 寸法（仮。`tools/blender/sheetlib/wall_parts.py`）:

  | 値 | 定数 | 今の値 | 画面の目安 |
  |---|---|---|---|
  | 躯体の深さ（基盤の下面から） | `ELEV_BODY_D` | 0.25 | 約 2px（基盤の板 `BASE_H` 0.35 と合わせて床の下 約 5px。躯体の下面は地面から約 27px。2 階建てバスを通すため 1.0 から浅くした。2026-11-18） |
  | 躯体の側面の下げ幅（壁のある側、壁の外の面から） | `ELEV_BODY_INSET` | 0.45 | 約 4px |
  | 斜めの躯体の切り口の下げ幅（壁の無い側、路盤の面の高さで 2 本の真ん中から） | `ELEV_BODY_DIAG_INSET` | 0.3 | 約 3px |
  | 橋脚の太さ（線路に沿う向き × 横切る向き） | `PIER_SIZE`・`PIER_SIZE * PIER_ACROSS_K` | 1.6 × 3.84 | blender-poc の高架の橋脚と同じ |
  | 門型の橋脚の柱の太さ（正方形の 1 辺。柱はタイルの辺に面を合わせる） | `PIER_GATE_POST` | 1.0 | 約 9px |
  | 門型の橋脚の梁と柱の上端の、躯体の下面からの食い込み（躯体に隠れる。床より幅の広い梁の端は躯体の横に見える） | `PIER_GATE_BEAM_EMBED` | 0.2 | 約 2px |
  | 門型の橋脚の梁の、躯体の下面より下に見える厚み（梁の深さ `PIER_GATE_BEAM_D` は上との和） | `PIER_GATE_BEAM_SHOW` | 0.15 | 約 1px。高架下の通れる高さは地面から約 26px（3.33）。2 階建てバスの屋根（約 20px）より約 6px 高い（2026-11-18） |
  | 門型の柱の内側の面の、タイルの中心からの距離（道路が通れる半幅） | `PIER_GATE_CLEAR` | 4.0 | pak128 の `Road_050` は路肩まで柱の内に収まる（`docs/rail_elev_gate_R1.png`） |
  | 床の高さ（段） | `ELEV_STEPS` | 2 | pak128 の既定（`way_height_clearance` が無い pak は `height_conversion_factor`） |

- 橋脚の waytype（2026-11-18、ユーザーの決定）: `tram_track`（iss と同じ）。本体は `track` の `system_type=7` として読み込む（`../simutrans` の `descriptor/reader/way_reader.cc`）ので、線路の網とつながり、線路の way-object（壁・架線）も載る。AMI の路面軌道（`ami_tram`）と同じ waytype で、路面軌道の道具の一覧に出る。道路のタイルに重ねて敷け（踏切は作られない）、高架の下を道路が横切っても、道路に沿って高架を通しても敷ける。地上の線路が高架の下を横切るときは、そのタイルを飛ばして橋脚を 2 本に分けて敷く。同じタイルに続けて敷くと 1 本の way になり、橋脚の後に線路を敷くとそのタイルは線路の十字（橋脚とつながる）、線路の後に橋脚を敷くと橋脚（速さ 1）の十字に置き換わって線路が切れる（`docs/rail_elev_pier_cross_*.png`。[reference](../../docs/reference/way-addon.md) の 5 章）
- 高架の行き止まり（POC の C7、仮、2026-11-18）: 床（基盤）と躯体を閉じた側のタイルの端まで延ばし、平らな端の面にする（壁は地上と同じく、壁の way-object がタイルの端に立てる）。端の面に模様は描かない。POC の高架の高速道路で見えた白い点線の模様は、このモードの区画 WV3（行き止まりの並び）で出ないことを見た
- 近い斜め: 高架でも、分け合うタイルに高架の way が 2 本置かれる（地上の基盤の版と同じ）。壁は地上と同じく `back`・`front` を敷いた後に `twin`（架線つきは `twin_catenary`）を重ね、`back`・`front` を敷き直す。橋脚の way は近い斜めの絵を持つので、分け合うタイルの地面は橋脚の way 1 本（2 本の柱の絵）か 2 本になる（敷き方による）
- 名前と並び: 高架の 4 版は `ami_rail_ballast_elev_<版>`。ゲームの道具の一覧は高架の道具（`ways(2,1)`）に分かれ、同じ速さ（160）なので名前の順（`back`・`center`・`front`・`single`）に並ぶ。壁の way-object は地上と共通なので、高架のための特例（`twin` のような別の way-object）は作らなかった
- 値（仮）: 高架は地上の 2 倍の費用・維持費（30000・600。iss と同じ考え方。`blender/ami_dat.py` の `ELEV_COST_K`）、橋脚は費用 1000・維持費 100（iss と同じ）・速さ 1（`PIER_VALUES`）
- 敷き方（スクリプト）: 壁の way-object は高架の高さ（地面 + 2 段）の座標で敷く（地面の座標では敷けない）。橋脚の way は地面の座標で敷く。高架と地上の線路は、地面を 2 段上げた台の上で、高架の端のタイルから地上の基盤の版を敷くとつながる（`sample.nut` の区画 J）

### 橋とトンネルの作り（在来線、#19）

橋（`ami_rail_ballast_bridge`）は 1 つだけで、欄干を描かず、床・道床・まくらぎ・レールと橋脚だけを描く。壁・架線は地上と同じ `single` の way-object（`ami_wall_rail_single`・`ami_wall_rail_single_catenary`）を、同じ経路の橋の高さに重ねる前提（橋の版は `single` だけ。2026-11-18、ユーザーの決定）。トンネル（`ami_rail_ballast_tunnel`）は坑口の絵だけを持ち、中と前後の way は地上の通常の版（`ami_rail_ballast`）か基盤の版を使う。

- 手本: iss の橋（`../refs/iss/src/bridge/rail/bridge.dat` の `iss_bt_0120_single`・`back`・`center`・`front`。`pillar_distance=1`、版ごとに別の橋で、壁は橋の手前の絵）とトンネル（`../refs/iss/src/tunnel/rail/tunnel.dat`）、iss の架線（`../refs/iss/src/way-object/rail/catenary_new.dat`）、blender-poc の橋とトンネル（`../blender-poc/src/track_bridge.dat`・`track_tunnel.dat`、`blender/render.py` の `bridge`、`ingame/bridge.nut`・`tunnel.nut`）。シートの並び（端の坂・坂から始まる端・橋脚・雪の行）と dat のキーは blender-poc の橋をそのまま使った
- 壁の way-object の手前の絵と車両（2026-11-18、ゲームで確かめた）: 橋の上でも、way-object の手前の絵（`frontimage`）は車両の後に描かれる。iss の橋 `iss_bt_0120_center` に AMI の架線つきの壁を重ね、編成を置いて撮ると、手前の柱が車両の上に描かれた（本体の `boden/grund.cc` の描く順も、橋のタイルで地上と同じ）。壁を橋の絵に描かず way-object に分ける作り（[ADR 0003](../../docs/adr/0003-ami-walls-base-piers-as-separate-objects.md)）は、橋でもそのまま使える
- 床（2026-11-18、ユーザーの決定）: 床（基盤）と躯体は壁の位置（`single` の壁の外の面）で止める（経路から `WALL_U + WALL_W`）。端の坂の躯体と Start の躯体も同じ幅で、どれも `tools/blender/sheetlib` の既定の幅（`_ramp_body_shape`・`build_start_body`）を使う。床・躯体の作りは高架の `single` の版と同じ（`rail_ballast_elev_single`。躯体は壁の外の面から `ELEV_BODY_INSET` 内）で、高さ・位置（dat のオフセット `-64,-32`）も高架にそろえた。`single` の壁を重ねると、壁の外に床の縁は出ない（`docs/rail_bridge_B1.png`）
- 端: 平地から立ち上がる坂（Ramp）は、坂の躯体を床と同じ幅で地面まで埋める。坂のタイルから始まる端（Start・Start2）は、坂の地面の上に床を描く（blender-poc の橋と同じ）。端の坂と坂から始まる端では、持ち分を下へ広げない（高架の躯体のための `lower` を使わない。`tools/blender/sheetlib` の `track_sheet`）。広げていたときは、坂の低い側で地面より下にある基盤・躯体まで描かれ、隣の地上の線路の上に灰色の帯（基盤の端の面）と、手前の壁の下に三角が出た（2026-11-18、ユーザーの確認用の保存データ。`docs/rail_bridge_ramp_before.png`・`ramp_after.png`。レイアウト検証用モードの `ramp_layout_before.png` で、帯が基盤（青）と道床（黄）だと分かった）
- 端の坂の躯体の上面: 基盤の上面（坂の面）の少し下に下げる（道路の橋と同じ。`blender/render.py` の橋のプロファイルの `ramp_body_under_base`）。下げる前は、坂の低い端の 2 つの角に躯体の上面がのぞき、雪の絵で雪にならない灰色の小片に見えた（2026-11-21、#44。[記録](../../docs/records/2026-11-21_ami-autocheck-candidates.md)、`docs/check44_6_before_*.png`・`after_*.png`）
- 橋脚: 高架の橋脚（`ami_pier_rail`）と同じ寸法の柱（`BRIDGE_PIER`）を、1 段ごとに積む（本体は橋の高さの段数だけ橋脚の絵を重ねる。`../simutrans` の `bauer/brueckenbauer.cc`）。`pillar_distance=1`（iss と同じ。全部のタイルに立つ）。床が壁の位置で止まるので、柱は床の下から地面まで見える
- 高架とのつなぎ目: 2 段の坂から始まる橋（Start2）の床は高架と同じ高さで、高架の端のタイルとつながる。スクリプトでは、高架を橋の両側に先に敷いてから橋を架ける（橋を先に架けると、高架を橋の端へつなげない。`sample.nut` の B4）。壁は高架の高さの座標で、高架と橋を通して 1 本で敷く
- トンネル: 坑口の覆いの形は blender-poc のトンネル（`tools/blender/sheetlib` の `tunnel_sheet`）で、道床・まくらぎ・レールは AMI の在来線の通常の版。壁・架線は、坑口とトンネルの中を通して 1 本で敷く。坑口のタイルに way-object が無いと、隣の壁のタイルが行き止まりの絵（線路を横切る端の壁）になる。坑口のタイルの壁と架線は覆いに隠れ、覆いから突き出さない。iss のトンネルに iss の架線を重ねても、架線は覆いのところで終わる。トンネルの中の way も架線つきの壁で電化される（`[check]` の行の `elec`）
- 名前と並び: 橋の道具の一覧は waytype・速さ・名前の順で、AMI の在来線の橋は 1 つ。トンネルも 1 つ。アイコンは下の「アイコン・カーソル」（数字の 160 と橋・トンネルの帯。版の札は付けない）
- 値（仮）: 橋・トンネルとも地上の 4 倍の費用・維持費（60000・1200。`blender/ami_dat.py` の `BRIDGE_COST_K`・`TUNNEL_COST_K`）、速さ 160
- 描く対象: `ami_rail_ballast_bridge`・`ami_rail_ballast_tunnel`（`blender/render.py`）
- 確かめていないこと・決めること:
  - 橋の高さ・橋脚の位置（POC の C6、仮）: 床の高さ・位置は高架にそろえた（どちらも 2 段、オフセット `-64,-32`）。iss の `iss_bt_0120_single` を隣に架けて比べたのは、床をタイルの幅いっぱいにしていたとき（iss は床が細く、床の縁に青い桁が見え、橋脚が床の下から地面まで見えた）。床を壁の位置で止めた後は並べていない。レールの高さを画素で突き合わせることもしていない

### 分岐の追加画像（ex 画像、#57）

線路（在来線・弾性まくらぎ直結軌道・高速線と、その基盤・高架の版）と路面軌道の way、架線つきの壁（`ami_wall_rail_<版>_catenary`）に、OTRP の ex 画像（26〜35 番）を入れた。本体が選ぶ形は [reference](../../docs/reference/way-addon.md) の 9.4。

| 番号 | 形 | 絵 |
|---|---|---|
| 26〜29 | Y字分岐（T字のタイル。根元が東・北・西・南） | T字の道床・壁のまま、根元から両側の枝へ開く 2 本の斜めのレール |
| 31〜34 | 三方分岐（十字のタイル。1 本側が東・北・西・南） | 十字の道床・壁のまま、1 本側から直進と両側の枝へ開く 3 本のレール |
| 30・35 | 十字の枠（線路では自動で選ばれない） | 通常の十字の絵 |

- 作り: シートのセル（行 0・1、列 10〜13。雪は行 4・5、壁のシートの手前の絵も +4 行）を `tools/blender/sheetlib` の `track_sheet` の `ex_switches` で描く。変えるのはレールと、架線の線だけ。道床・壁・基盤は通常の T字・十字のまま（reference の 9.3「変えるのは走行面だけ」）。Y字のタイルには、T字の直線の分の道床が三角に残る
- pak への入れ方: makeobj は 26 番以降のキーを持たないので、ex の絵を `image[nse1]`〜`[nsew2]` に割り当てた提供用の way（`src/ex_donors.dat`、名前は `<対象>__ex_donor`）を作り、その 10 枚を対象の画像リストの末尾へ写す（`ex_graft.py`。reference の 9.1）。`build.py` が pak を作った後に自動で行う。提供用の way は継ぎ足しにだけ使い、配る pak には入れない
- 架線つきの壁: 本体は、way-object の分岐の絵（16 番）が空でないときだけ、分岐のタイルで ex 画像を探す（reference の 10 章）。そのため 16〜25 番には通常の T字・十字の絵を入れた（見た目は今までと同じ）。壁だけの way-object（`ami_wall_rail_<版>`）は分岐で絵が変わらないので入れていない
- 二重架線（`ami_wall_rail_twin_catenary`）と道路（#46）、高架の橋脚は対象外
- 確認画像は `docs/rail_switch_ex_<気候>_<区画>_<形><根元の向き>.png`（左が前、右が後。2 倍）。壁だけの way-object を重ねたところは `docs/rail_switch_ex_wallonly.png`（壁は通常の T字・十字の絵のまま）。区画は `ingame/ex_sample.nut` の `WAYS` の順で、0 = 在来線、2 = 高速線、3 = 路面軌道、4 = 在来線の基盤 single と架線つきの壁 single。経緯は記録 [2026-11-21_ami-rail-switch-ex](../../docs/records/2026-11-21_ami-rail-switch-ex.md)
- 高架の版（#82）: 在来線・ラダー軌道の高架の 4 版を `ex_sample.nut` で敷き、地上の版と同じく全部の形で ex の絵の番号が選ばれた（画面で見たのは温暖側の single だけ。架線つきの壁を高架に重ねた組は #85 で確かめ、地上と同じ絵だった（`docs/ex85_*.png`、記録 [2026-11-21_ami-elev-catenary-ex](../../docs/records/2026-11-21_ami-elev-catenary-ex.md)）。`docs/ex_elev_temperate_E.png`。左上から在来線の地上の Y字 東、在来線の高架 single の Y字 東、ラダーの高架 single の Y字 東・三方分岐 東。記録 [2026-11-21_ami-ex-elevated](../../docs/records/2026-11-21_ami-ex-elevated.md)）。これからの種類は、高架の版の確認を省く（reference の 9.4）

### 付属（別の pak にして同梱）

| もの | 作り | 名前（仮） |
|---|---|---|
| 線路の壁と架線 | way-object。架線つき（電化）の `single`・`back`・`center`（架線だけ）・`front` と、壁だけの `single`・`back`・`center`（行き止まりの端の壁だけ）・`front` | `ami_wall_rail_*`・`ami_wall_rail_*_catenary` |
| 道路の壁 | way-object。`single`・`back`・`front`。中央分離帯つきの `front_divider`・`center_divider`・`twin_divider`（#118） | `ami_wall_road_*` |
| 橋脚 | 高架の真下の地面に敷く、別の waytype の way。線路用（単柱と門型）と道路用 | `ami_pier_rail`・`ami_pier_rail_gate`・`ami_pier_road` |
| 歩道 | 道路の隣のタイルに敷く、別の waytype の way。舗装の種類と高架の版がある | `ami_sidewalk`・`ami_sidewalk_<舗装>`・`ami_sidewalk_elev` |
| 歩道の柵 | 歩道に重ねる way-object。`single`・`back`・`front` | `ami_wall_sidewalk_*` |
| 電柱 | 歩道に重ねる way-object。タイルのわきに立てる電柱だけと、柵の版ごとの柵つき（#120） | `ami_sidewalk_pole_<版>`・`ami_wall_sidewalk_<版>_pole` |
| 踏切 | 線路 4 種 × 道路 3 種の 12 個の crossing（#111） | `ami_crossing_<線路>_<道路>` |

景観（盛土）は付属と分けて `ami_scenery.pak` に入れる（ADR 0008。#122 の標識もここに入る）。

橋脚の waytype は #18 で `tram_track` に決めた（上の「高架と橋脚の作り」。iss と同じ）。歩道の waytype は #24 で iss と同じ `water` に決めた（2026-11-20、ユーザーの決定。下の「歩道の作り」）。

### 歩道の作り（#24）

- 絵は自分のつながり（隣の歩道とつながる辺）だけで決まる。タイル全面を歩道の高さ（`SIDEWALK_H`、約 2px）の板にし、上に敷石を敷く。つながらない辺では敷石を縁石の上面の幅（`CURB_W`）だけ内へ下げ、縁石の上面の帯と立ち上がりを見せる。隣が道路なら、道路との境の縁石になる。立ち上がりが見えるのは手前の辺（南・東）だけで、奥の辺（北・西）は上面の帯で縁石に見せる。部品の寸法と縁石の材質は blender-poc の一般道の歩道（`road_parts` の `curb`・`paving`）と同じ。敷石は灰色の敷石と暗い目地（精細化。上の「道路の作り」）。描くのは `tools/blender/sheetlib/sidewalk.py` の `sidewalk_sheet`
- 絵の位置と持ち分は道路と同じ（`ROAD_CY`。オフセット `-64,-32`）。持ち分は、奥の辺の縁石の上面の帯が切れないよう、地面の菱形を上へ `SIDEWALK_RISE`（3 行）広げた
- セルは直線・行き止まり・1 タイル・カーブ・T字・十字・坂・急坂（夏と雪）。斜めの絵・近い斜めの絵・分岐の絵は持たない。本体は斜めの絵の無い way にカーブの絵を使う（`../simutrans` の `boden/wege/weg.cc` の `calc_image`。斜めの絵は `has_diagonal_image()` のときだけ選ぶ）
- 雪の絵は、AMI の道路の雪と同じく敷石も縁石もまだらの雪の材質（`blender/render.py` の `ROAD_SNOW`）
- 道路を斜めに敷くと、道路のタイルのうち斜めの絵が覆わない角の三角に草が見える（`docs/sidewalk_GE_D.png`）。三角は道路のタイルの持ち分なので、歩道の絵では埋めない
- waytype（2026-11-20、ゲームで確かめた。iss の歩道の pak `iss_util_sidewalk.pak` にある `water` の `iss_wwg_sidewalk*` と `road` の `iss_wrg_sidewalk*` も並べて見た）:
  - `water`（採用。iss と同じ。2026-11-20、ユーザーの決定）: 道路の隣に敷いても、道路の向き・絵は変わらない。平地・坂・急坂に敷ける。歩道の列を道路が横切ると、そのタイルは歩道と道路の 2 本の way になり、pak128 の運河の踏切（跳ね橋）が立つ（`docs/sidewalk_GE_X.png`）。pak128 の運河（`canal_020`）を横切らせると、そのタイルは運河に置き換わり、隣の歩道とつながる。歩道は交差点のタイルを空けて敷く（見本の区画 R）
  - `road`（iss の `iss_wrg_sidewalk*`）: 横切る道路が歩道のタイルを置き換え、歩道と道路が 1 本の道路としてつながった（`[check]` の向きが 15）ので、使わない
- 値（仮）: 費用 1000・維持費 20・登場 1900、速さ 1（`blender/ami_dat.py` の `SIDEWALK_VALUES`）

### 盛土の作り（#123）

高架の脇の地面に敷く、法面（のりめん）の way。形と範囲は、2026-11-21 に進捗管理が推奨案で決めた（[#123 のコメント](https://github.com/128na/simutrans-addon-dev/issues/123)。見た目はユーザーが PR で確かめる）。手本は iss の法面（`../refs/iss/src/util/embankment`、`../refs/iss/docs/technique/index.md` の「法面」）。

- 作り: 1 タイルの全面を楔（くさび）にした芝の法面。高い辺は高架と同じ 2 段（pak128 で 32px。箱積みの箱 1 段と同じ）、反対の辺は地面。平地と 1 段の坂の絵の上端は 128px 座標の y32 で、[hakozumi.md](../../docs/reference/hakozumi.md) の 4 章の上限（y32 より上に出さない）に収まる。2 段の坂の front（北・西が上がる坂）だけは、坂の高さの分だけ上端が 1px 上に出る（256px のセルで行 31）描くのは `tools/blender/sheetlib/sheetlib.py` の `embankment_sheet`、設定は `blender/render.py` の `EMBANKMENT_GRASS`・`EMBANKMENT_SNOW`
- 版: 高い側の向きで 2 つ
  - `ami_embankment_front`: 法面が手前（南・東）を向く。高い側は北・西。盛り上げたい所（高架の列など）の南・東の辺に敷く
  - `ami_embankment_back`: 法面が奥（北・西）を向く。高い側は南・東。盛り上げたい所の北・西の辺に敷く
- 形（iss と同じ考え方）:
  - 直線・行き止まり: 直線の楔。行き止まりの端は三角の面で閉じる
  - 曲がり: 台の角。外の角（2 つの楔の高い辺が会う角だけが高い）と内の角（低い角だけが地面）を、斜めの稜線で折れる面にした（iss の法面の八角形の角と同じ）。front は北西が外の角・南東が内の角、back は南東が外の角・北西が内の角
  - 北東・南西の角は front と back が会う角で、盛り上げた台の角（外の角）にも窪みの角（内の角）にもなる。front は外の角、back は内の角を描く。台の角には front を、窪みの角には back を後から敷く（同じ速さの way は後から敷いた方が残る。[way-addon.md](../../docs/reference/way-addon.md) の 5 章）
  - T字・十字・1 タイル: 上が平らな箱
  - 坂: 直線の坂（1 段・2 段）だけ。楔の上の辺も地形に沿って上がる（本体の高架は地形の坂を引き継ぐ）
  - 斜めの絵は持たない。本体は斜めの絵の無い way に曲がりの絵を使うので、斜めに敷くと角が階段のように並ぶ（`docs/embankment123_D.png`）
- 雪の絵: 法面を雪のまだらにする
- 芝の色: ゲームの草地（拡大率 1 の画面で平均 約 80・147・53）に合わせた。南向きの法面は平均 約 78・137・52（`docs/embankment123_M.png` の画面で測った。2026-11-21）
- 楔はつながる辺の外へ `EMB_OVERLAP`（約 2px）延ばし、持ち分で切る。延ばさないと、つなぎ目に 1px の暗い線が出た
- 検査: `check.sh` が `check_embankment.py` を回す（#148）。front と back の dat がそろい、絵のキー（夏・雪 各 34）がすべてあり、オフセットが `-64,-32` かを見る。キーごとに、指すセルの絵の塗った範囲が、キーから決まる形（直線・行き止まり・坂は楔、曲がりは外の角・内の角、T字・十字・1 タイルは箱。つながる辺には側面が無い）を画面に写した範囲と、輪郭の 2px の差を除いて合うかを見る。雪の絵が夏の絵の 4 行下を指し、平均の色が雪（夏は芝）かも見る。形は検査の中でこの節から書き直したもの（`sheetlib` を読まない）。輪郭が同じで面の色でしか違わないもの（直線と行き止まり、開いた辺の違いが輪郭に出ない T字・十字、front の内の角と 1 タイル、箱の front と back など。一覧は `check_embankment.py` の冒頭）と、持ち分の外へ延ばす分の有り無しは見ない
- 値: 速さ 1、費用 1000、維持費 100、登場 1900（#110 の一覧。`blender/ami_dat.py` の `EMBANKMENT_VALUES`）。waytype は橋脚と同じ `tram_track`（ADR 0008）。iss の盛土は track の高架の way（速さ 65480）で、高架の線路とつながって列車が速く走れる
- 置けない所（ADR 0008）: 橋脚と同じ tram_track なので、橋脚と同じタイルでは way が 1 本になる。橋脚の列を盛土で横切ると、そのタイルは盛土の十字（箱）に置き換わり、橋脚が切れる（`[check] X`、`docs/embankment123_X.png`）。路面軌道を敷いた道路の上にも置けない。高架の真下のタイルには、橋脚を敷くか何も敷かない
- 見本: `ingame/embankment_sample.nut`（撮る場所は `ingame/sample_spots.sh` の `EMBANKMENT_SPOTS`）。線路の高架（東西・南北）・道路の高架の両脇、台の輪（M）、窪みの輪（P）、坂・急坂、斜め、橋脚との交わりを、温暖側と降雪側に敷く。輪の角に残った版を `[check]` の行で期待と比べる（違えば返り値の先頭が `check`）
- 後から足せるもの（今は作らない。2026-11-21、進捗管理の決定。[#123 のコメント](https://github.com/128na/simutrans-addon-dev/issues/123)）: 半分の高さ（1 段）の版、コンクリートの法面、iss の `distorted` の坂の形、斜めの法面の絵
### 歩道の種類・高架の歩道・歩道の柵の作り（#119）

- 歩道の種類（`ami_sidewalk_<舗装>`）: 形・セル・持ち分・雪の絵は `ami_sidewalk`（上の「歩道の作り」）と同じで、敷石の材質だけが違う。舗装は 3 つ（2026-11-21、作業者が決めた。ユーザーが PR で確かめる）。敷石が画面で約 6 x 3px なので、目地の模様（やはず張りなど）ではなく、色と材質で見分ける（`docs/sidewalk119_P_temperate.png`）。材質は `blender/render.py` の `SIDEWALK_PAVINGS`
  - `asphalt`: アスファルト舗装。道路の路面より明るい灰色のまだら
  - `brick`: 赤れんが色のインターロッキングブロック
  - `tile`: ベージュの平板。敷石が大きい
- 高架の歩道（`ami_sidewalk_elev`。dat は `system_type=1`）: 敷石は `ami_sidewalk` と同じ。板の下に、道路の高架と同じ深さの基盤と躯体を足した（材質も道路の高架と同じ）。躯体はつながらない辺で内へ下げる。柱は描かず、真下の地面に道路用の橋脚（`ami_pier_road`）を敷く。躯体の下面の深さが道路の高架と同じなので、橋脚の上端が合う（`docs/sidewalk119_E_temperate.png`）。描くのは `tools/blender/sheetlib/sidewalk.py` の `sidewalk_sheet(elevated=True)`
  - 高架の道路の隣のタイルに並べて敷け、地上の道路の上を横切って敷ける（2026-11-21、ゲームで確かめた。`ingame/sidewalk_struct.nut` の区画 E1・E2）。床の下の縁は、隣の高架の道路とそろう
  - 運河（`water`）の高架の way なので、箱積みの箱の上面と同じ高さに乗る（[hakozumi.md](../../docs/reference/hakozumi.md) の 4.2）。箱積みのパーツと並べて見てはいない
- 歩道の柵（`ami_wall_sidewalk_<版>`）: 歩道に重ねる way-object（`waytype`・`own_waytype` とも `water`）。地上の歩道（舗装の種類も）と高架の歩道の両方に同じ物を重ねる。柵の足元は敷石の上面
  - 柵は経路ではなく、歩道の板の縁（隣の歩道とつながらない辺）に沿って立てる。歩道の絵が四角いタイルなので、カーブ・L字の角でも柵はタイルの辺に沿って折れる（`docs/sidewalk119_F_temperate.png`）。坂では坂の面に沿う
  - 版: `single` はつながらない辺の全部、`back` は奥の辺（北・西）だけ、`front` は手前の辺（南・東）だけ。道路の両脇の歩道で道路の側の辺だけに立てるなら、道路の東・南の側の歩道に `back`、西・北の側に `front` を重ねる（区画 F1）。外側の辺に立てるなら逆で、高架の道路の両脇の高架の歩道（区画 E1）では、北の歩道に `back`、南の歩道に `front` を重ねて、道路と反対の辺に立てた
  - 行き止まりの閉じた辺には立てない（横断歩道へ続く口として空ける）。高架の歩道の行き止まりの端も開いたまま（2026-11-21、作業者が決めた。ユーザーが PR で確かめる）
  - 形は白く塗った鋼の横断防止柵（柱・上の横木・中の横木）。柱はタイル 1 辺に 4 本で、タイルの辺の上には置かない。高さは約 1m（画面で約 7px）。寸法の単位は [way-addon.md](../../docs/reference/way-addon.md) の 12 章。奥の辺の柵は奥の絵、手前の辺の柵は手前の絵（`frontimage`）に描く。描くのは `sheetlib/sidewalk.py` の `sidewalk_fence_sheet`
  - 斜めの絵の無い way-object なので、斜めにつないだ歩道ではカーブのセルの絵が出る（歩道の way と同じ）
- 値（[#110](https://github.com/128na/simutrans-addon-dev/issues/110) の表から移した。`blender/ami_dat.py` の `SIDEWALK_VALUES`・`SIDEWALK_ELEV_VALUES`・`SIDEWALK_WALL_VALUES`）:

| 物 | 速さ | 費用 | 維持費 | 登場年 |
|---|---|---|---|---|
| 歩道の種類（`ami_sidewalk_<舗装>`） | 1 | 1000 | 20 | 1900 |
| 高架の歩道（`ami_sidewalk_elev`） | 1 | 2000 | 40 | 1900 |
| 歩道の柵（`ami_wall_sidewalk_<版>`） | 1000 | 3000 | 60 | 1900 |

### 電柱の作り（#120）

歩道に立てる電柱と電線の way-object。作りは、2026-11-22 に進捗管理が推奨案で決めた（[#120 のコメント](https://github.com/128na/simutrans-addon-dev/issues/120#issuecomment-7064726322)。見た目はユーザーが PR で確かめる）。手本は iss の電柱（`../refs/iss/src/util/road_misc/pole.dat`。毎タイルに柱、つながる向きに電線）。

- 物: 1 タイルに置ける water の way-object は 1 つだけ（[way-addon.md](../../docs/reference/way-addon.md) の 10 章）なので、柵と同じタイルに立てる物は、柵の版に電柱を足した way-object にした（架線つきの壁・中央分離帯つきの壁と同じ考え方）
  - `ami_sidewalk_pole_<版>`（`back`・`front`）: 電柱だけ（柵なし）。柱をタイルのわきに寄せる（`back` は北西、`front` は南東。柵つきの同じ版と同じ位置）
  - `ami_wall_sidewalk_<版>_pole`（`back`・`front`）: 歩道の柵（`ami_wall_sidewalk_<版>`）と同じ辺に柵を立て、柱を柵の側へ寄せる
  - タイルの中心に立てる版（最初の PR の `ami_sidewalk_pole`・`ami_wall_sidewalk_single_pole`）はやめた（歩道の中央に電柱は立たない。2026-11-22、ユーザーの指定で進捗管理が決めた）。`single` の柵の歩道に電柱を立てる物は無い
- 形: 毎タイルに柱を 1 本立て、つながる向きに電線を渡す。柱はコンクリートの灰色で、高さ約 5.5 単位（画面で約 43px。iss の電柱 `../refs/iss/src/util/road_misc/pole.png` にそろえた。最初は約 70px で、架線の柱より高く見えた。2026-11-22、ユーザーの指定。`docs/pole120_temperate_F.png` で架線つきの壁と並べた）。上に鋼の腕木（電線に直角。曲がり・T字・十字では十字に 2 本）、腕木の上に電線 3 本、柱の脇の低い所に通信線 1 本。柱の位置は版ごとに決まった点（`tools/blender/sheetlib/sidewalk.py` の `pole_shift`）で、南北の辺を出る電線は同じ x、東西の辺を出る電線は同じ y を通るので、同じ版を並べると電線が辺でつながる。`back` と `front` を並べると、境のタイルで電線がずれる（柵の有り無しは同じ版なら同じ位置なのでずれない。`docs/pole120_temperate_A.png` の北の歩道）
- 柱・腕木・電線は手前の絵（`frontimage`）に描く（iss と同じ。電線は歩行者の上を通る）。柵の奥の辺は奥の絵のまま。坂では電線も坂の面に沿って折れる（`docs/pole120_temperate_D.png`）。雪の絵は無い（way-object に季節の絵は無い）。高架の歩道にも重ねられる（`docs/pole120_temperate_E.png`）
- 描くのは `sheetlib/sidewalk.py` の `sidewalk_pole_sheet`、設定は `blender/catalog.py` の `SIDEWALK_POLES`
- 値（#110 の一覧から移した。`blender/ami_dat.py` の `SIDEWALK_POLE_VALUES`・`SIDEWALK_WALL_POLE_VALUES`）:

| 物 | 速さ | 費用 | 維持費 | 登場年 |
|---|---|---|---|---|
| 電柱（`ami_sidewalk_pole_<版>`） | 1000 | 1000 | 20 | 1900 |
| 柵つきの電柱（`ami_wall_sidewalk_<版>_pole`） | 1010 | 4000 | 80 | 1900 |

- 置き換え: 柵つきの電柱は柵（1000）より速いので、柵の上に Ctrl を押さずに重ねると置き換わる。電柱だけの物は柵と同じ速さなので、柵の上に重ねても柵が残る（見本の区画 A の南の歩道。`[check]` の行）。柵つきの電柱の版どうし（例: `front_pole` の上に `back_pole`）は同じ速さなので、置き換えるには Ctrl を押して重ねる。置き換えた区間の端では、隣のタイルの柵・電線とのつながりが切れることがある（本体の `~wayobj_t` が隣の向きを外す。ゲームでは確かめていない）ので、そのときは端をまたいで敷き直す
- 見本: `ingame/pole_sample.nut`（`ingame/game.sh` で流す。降雪側は `OX=276`）。東西・南北の道路の両脇（A・B）、L字・T字・十字（C）、坂・急坂（D）、高架の歩道（E）、架線つきの線路の隣（F。電柱と架線の柱の高さを比べる）。残った way-object を `[check]` の行で期待と比べる（違えば返り値の先頭が `check`）。撮った画面は `docs/pole120_<気候>_<区画>.png`（拡大率 3）

### 中央分離帯の作り（#118）

4 車線（道路を 2 タイル並べた道）の上下線の境に立てる、縁石の帯とガードレール。手前のタイル（東西の道なら南、南北の道なら東）に重ねる壁の way-object で、奥の側壁の位置（2 タイルの境）に立つ（2026-11-21、ユーザーの指定）。手本は iss の中央分離帯（`../refs/iss/src/way-object/road/center_divider_1.dat`・`wall_with_center_divider.dat`。タイルの辺に沿う細いガードレール）。

- 版:
  - `ami_wall_road_front_divider`: 手前の側壁と、奥の側壁の位置の分離帯。壁で囲んだ 4 車線の手前のタイル（基盤の版 `front`）に重ねる。奥のタイルは今までどおり基盤の版 `back` と壁 `ami_wall_road_back`
  - `ami_wall_road_center_divider`: 分離帯だけ（側壁なし。行き止まりの端の壁は `center` と同じく持つ）。壁の無い 4 車線（基盤の版 `center` を 2 本）の手前のタイルや、3 本以上並べた道の中ほどのタイルに重ねる
  - `ami_wall_road_twin_divider`: 近い斜めの分け合うタイル用。西の線（`nw`・`sw`）は `back` の壁、東の線（`ne`・`se`）は `front_divider` の絵。敷き方は `ami_wall_road_twin` と同じ（`back`・`front_divider` を敷いた後に分け合うタイルへ 1 タイルずつ重ね、`back`・`front_divider` を敷き直す）
- 形: 側壁の位置（経路から `EXPWY_WALL_U` の少し内〜側壁の外の面）に低い縁石の帯を置き、帯の中心に両面のガードレール（2 枚の板と支柱）を立てる。寸法は `tools/blender/sheetlib/road_parts.py` の `MEDIAN_*`。側壁と同じく、T字・十字では横切る道の車道の分を削って開け、斜め・坂・高架でも側壁と同じ位置を通る（見本で見た）。1 タイル（どこにもつながらない way）には立てない（十字と同じ経路で作るので、角の切れ端が点で残った）。左右の両側に作り、壁の版を選ぶ処理（`sheetlib.py` の `select_walls`）が奥の側の 1 本だけを残す（奥の絵に描く）。設定は `blender/render.py` の `ROAD_DIVIDER_LABEL` の所、値は `blender/ami_dat.py` の `DIVIDER_VALUES`
- 4 車線の輪（直角の曲がり。見本の区画 R、`docs/divider118_GE_R.png`）: 外の輪は北・西の辺が `back`、南・東の辺が `front`、内の輪は逆にする。角のタイルは南北の辺の版（「遊ぶ人向けの敷き方」）。壁は南北の辺を角まで先に敷き、東西の辺を後から敷くが、`front_divider`（1010）は壁 `back`（1000）より速く、角の `back` を置き換えてしまう。東西の辺の `front_divider` は、角が `back` のタイル（外の輪の南西・内の輪の北東）の 1 つ手前で止める。こう敷くと、北西・南東・南西の角では分離帯が角に沿って曲がる。北東の角（内の輪の角が `back`）では、分離帯が角の 1 タイルで途切れる（内の輪の北の辺の分離帯が角の手前で終わり、外の輪の東の辺の分離帯が角の次のタイルから始まる）
- 値: 速さ 1010（`twin_divider` は 1011）、費用 3000、維持費 60、登場 1900（#110 の一覧）。速さが壁（1000）・`twin`（1001）より大きいので、壁の上に Ctrl を押さずに重ねると分離帯つきに置き換わる。逆に、分離帯つきの上に壁を敷いても置き換わらない（外してから敷く。[way-addon.md](../../docs/reference/way-addon.md) の 10 章）
- 見本: `ingame/divider_sample.nut`（撮る場所は `ingame/sample_spots.sh` の `DIVIDER_SPOTS`）。一般道路と高速道路で、東西の 4 車線と壁の無い道路の十字（P2）、南北の 4 車線の坂（PN）、壁の無い 4 車線（P0）、3 本並べた道（P3）、高架（PE）、4 車線の輪（R）、近い斜め（PD）を温暖側と降雪側に敷く。残った way-object を `[check]` の行で期待と比べる（違えば返り値の先頭が `check`）
- ADR 0008 との違い（2026-11-21、ユーザーの指定による。決めた理由は [ADR 0010](../../docs/adr/0010-ami-divider-between-two-road-tiles.md)）: ADR は「分離帯だけの版を道路の `center` に置く」としていたが、分離帯の位置を 1 タイルの中心線でなく 2 タイルの境にしたので、版は `front_divider`・`center_divider`（と `twin_divider`）にした。`single_divider`・`back_divider` は作らない（1 タイルの道の中心線の分離帯は、一般の道路には要らない）
- 後から足せるもの（今は作らない）: 植え込みの分離帯、暫定 2 車線の高速道路用の、1 タイルの中心線に立てる簡易な柵・ワイヤーの分離帯

### 路面表示の版の作り（#121）

道路を 2〜4 タイル並べた 4・6・8 車線の道で、白線を多車線の並びにした way（`ami_road_<種類>_lane<n>`）。作るもの・線の位置・名前は、2026-11-21 にユーザーが推奨案で決めた（[#121 のコメント](https://github.com/128na/simutrans-addon-dev/issues/121)。見た目はユーザーが PR で確かめる）。

- 一般道路と高速道路の、地上の通常の版だけ（7 版 × 2 種の 14 本。`blender/catalog.py` の `LANE_ROADS`・`LANES`）。生活道路は中央線が無く、多車線にしないので作らない。基盤・高架・橋・トンネルの版は作らない
- 版ごとの線（奥の境・真ん中・手前の境。奥は東西の道なら北、南北の道なら西）:

| n | 奥の境 | 真ん中 | 手前の境 | 使う所 |
|---|---|---|---|---|
| 1 | 路側線 | 車線の境 | 中央線 | 4 車線の奥 |
| 2 | 中央線 | 車線の境 | 路側線 | 4 車線の手前 |
| 3 | 路側線 | 車線の境 | 車線の境 | 6・8 車線の奥 |
| 4 | 車線の境 | 中央線 | 車線の境 | 6 車線の真ん中 |
| 5 | 車線の境 | 車線の境 | 路側線 | 6・8 車線の手前 |
| 6 | 車線の境 | 車線の境 | 中央線 | 8 車線の内側の奥 |
| 7 | 中央線 | 車線の境 | 車線の境 | 8 車線の内側の手前 |

  - 4 車線は 1・2、6 車線は 3・4・5、8 車線は 3・6・7・5 を、奥から並べる
- 線の位置:
  - 路側線は通常の版と同じ位置（経路から ±3.37）
  - 中央線と車線の境はタイルの辺（±5）で、隣のタイルと半分ずつ描く
  - 中央線は実線、車線の境は破線。破線は通常の版の高速道路の中央線と同じ、タイルにそろえた破線
  - 4 車線の中央線は 2 タイルの境で、中央分離帯（#118）の位置と同じ
- 描き方は `tools/blender/sheetlib/sheetlib.py` の `lane_lines`。プロファイルの `lanes` が線を決め、直線・坂・行き止まり・斜め・近い斜めのセルに描く。奥の側は `_far_sign` が経路の向きから決める（直線は北・西、斜めは `select_walls` の奥と同じ側）
- 交差点（T字・十字・分岐の絵・1 タイル）は線なしの路面。横切る道を同じ速さの通常の版で敷くと、交差点のタイルは横切った道に置き換わり、通常の版の交差点の絵になる
- カーブは通常の版と同じく斜めの絵（`ami_dat.py` の `DIAG_CURVES`）
- アイコンは通常の版と同じ速さの札に、右下へ版の番号（1〜7）。道具の一覧（`lineup.py`）では「道路（路面表示）」
- 値は元の道路と同じ（#110 の一覧。`ami_dat.py` の `VALUES` を写す）
- pak は道路の `ami_road.pak`（と全部入りの `ami.pak`）
- 近い斜めの分け合うタイル（並べた 2 本の斜めが 1 タイルに入る所）は、その way の版の線を 2 片とも描く。隣の版は分からないので、切れ目の上に、奥の片の手前の境と、手前の片の奥の境が 2 本並ぶ（4 車線なら中央線と路側線。シートの行 2 の列 4・9）。見た目はユーザーが PR で確かめる
- ADR 0008 との違い（2026-11-21、ユーザーの決定。[#121 のコメント](https://github.com/128na/simutrans-addon-dev/issues/121)）: ADR は路面表示に「多車線の車線と交差点」を入れるとしていたが、交差点には線を描かない（交差点の中の線は、横切る道の向きと車線の数で変わり、way の絵 1 枚では決まらないため）
- 見本: `ingame/lane_sample.nut`（撮る場所は `ingame/sample_spots.sh` の `LANE_SPOTS`）。一般道路と高速道路で、東西の 4・6・8 車線と十字（L4・L6・L8）、南北の 4 車線と十字（LN）、中央分離帯とそろえた 4 車線（LW）、近い斜めの 4 車線・6 車線（LD・LD6）を、温暖側と降雪側に敷く。`[check]` の行で敷いた way の名前を確かめる

### 踏切の作り（#111）

作るもの・見た目・仮の値は、2026-11-21 に進捗管理が推奨案で決めた（[#111 のコメント](https://github.com/128na/simutrans-addon-dev/issues/111#issuecomment-7059345141)。見た目はユーザーが PR で確かめる）。

- 線路 4 種 × 道路 3 種の 12 個（`ami_crossing_<線路>_<道路>`。例 `ami_crossing_rail_ballast_road_general`。`blender/catalog.py` の `CROSSINGS`）。本体は踏切を waytype の組と速さだけで選ぶ（way の名前は見ない。`docs/reference/way-addon.md` の 5 章）ので、組ごとに速さの合う踏切を置く。高速道路の踏切も作る（無いと pak128 の踏切が出る）。pak128 などほかの way との組でも、速さの近い AMI の踏切が選ばれることがある。見本の区画 M で見た組（2026-11-21、`docs/crossing_mixed.png`。左から）: `Rail_100_Tracks`×`Road_050` と `ami_rail_ballast`×`Road_050` は pak128 の踏切、`Rail_100_Tracks`×`ami_road_general`・`Rail_160_Tracks`×`ami_road_local` は AMI の踏切、`ami_rail_slab`×`Road_050` は AMI の一般道路の踏切（pak128 の踏切は 480km/h の線路に足りない）で、pak128 の道路の上に AMI の路面が出る。どの組も way の速さは踏切で下がらなかった（`[check]` の行の `full`）
- 絵は道路の種類ごとに 1 枚（`src/ami_crossing_road_<道路>.png`）で、線路の 4 種で同じ（踏切の中は道床が見えない）。描くのは `tools/blender/sheetlib/crossing.py` の `crossing_sheet`
  - 奥の絵（乗り物より前に描く）は、pak128 の踏切と同じくタイル全面を描き、下の way の絵を隠す（隠さないと AMI の道床が路面の上に出る。iss の踏切は遮断機だけを描く）。その道路の直線のセル（`src/ami_road_<道路>.png` の `0.2`・`0.3`、雪は 4 行下）を下地にそのまま写し、線路に沿うゴムの踏板（黒灰）・レールの頭・溝と、奥の側の遮断機・警報機を重ねる。レールと踏板は線路の way のレールと同じ基準面（`_DATUMS` の `rail`）・横の範囲・上面の高さで、隣の線路のタイルのレールとつなぐ（`render.py` が線路の `RAIL_IN`・`RAIL_OUT`・`RAIL_Z1` を `rail=` で渡す。踏板の上面はレールの頭の高さ。#129）
  - 手前の絵（乗り物の後に描く）は、手前の側の遮断機・警報機だけ。奥・手前は線路で分ける（東西の線路は南の側、南北の線路は東の側が手前）。車は踏切のタイルの外で止まるので、タイルの上を通る列車に合わせた
  - 遮断機・警報機は日本式の第 1 種踏切（黄黒の遮断かん、黄黒の柱に X 字の標識と赤い 2 灯）を、道路の左側（左側通行）に線路を挟んで 2 基。開いた絵は遮断かんが立ち、閉じた絵は進む側の車線をふさいで赤い灯が点く。灯の点滅（絵の切り替え）は無い（OTRP は絵の添字を雪の絵に使う）
- 道路のシートを描いた後に描く（`render.py` の `SHEETS` は登録の順に描く。`render_parallel.py` で並べて描くときは、道路のシートを描き終えてから踏切を描く）。道路の絵を描き直したら踏切も描き直す。描き直し忘れは `check.sh` の `check_crossing.py` が見つける（踏切を描くときに、写した道路のセルの sha256 を `src/ami_crossing_road_<道路>.road_cells.txt` に控え、今の道路のシートと比べる。#130）
- 道具が無いので、アイコン・カーソルは持たない（`blender/icons.py` は dat に `icon` の無い物を飛ばす）
- pak は付属（`ami_extra.pak`）に入れる（線路・道路と組で使う）
- 値（仮。#110 で決める）: 速さは両方の way の最高速度（踏切で速度を落とさない）、登場年は 2 つの way の遅い方、音なし（`sound=-1`。iss と同じ）。`blender/ami_dat.py` の `crossing_dat_text`
- 見本は `ingame/crossing_sample.sh`（`ingame/crossing_sample.nut`・`crossing_train.nut`）。12 組を、道路が南北の向き（H 線）と東西の向き（V 線）で温暖・降雪に敷き、開いた絵と、列車を走らせて閉じた絵を撮る。撮った画面に AMI の踏切の絵が出ているかは `JUDGE=1` で判定する（`ingame/crossing_judge.py`。AMI の遮断機・警報機の黄色と、pak128 の踏切の標識の赤の画素を数え、どちらも無ければ踏切が写っていないとする。script からは踏切の名前が読めず、ほかの pak の踏切が選ばれても way の速さは変わらないため。#128）。撮った画面は `docs/crossing_<気候>_<線>_<開閉>.png`（左上から、行が道路 local・general・expressway、列が線路 ballast・concrete・ladder・slab）

### 跨座式モノレールの作り（#113）

- 物: 地上の `ami_monorail_straddle`、高架の 3 版 `ami_monorail_straddle_elev_front`・`_center`・`_back`（`system_type=1`）、トンネル `ami_monorail_straddle_tunnel`（中の way は地上の版）、車庫 `ami_monorail_depot`（下の「車庫の作り」）。waytype は `monorail_track`。並びは iss の跨座式（`../refs/iss/src/way/monorail/straddle.dat`・`../refs/iss/src/tunnel/monorail/tunnel.dat`）に合わせた（2026-11-21、ユーザーの決定「軌道配置は ISS と合わせる」）。橋・基盤の版・壁は作らない（iss にも無い）
- 桁: 打ち放しのコンクリートの箱。幅 0.85、上面は way の高さから 0.7（iss の地上の桁を画面で測った値。記録）。地上の版は桁の下面が地面、高架の版は桁を下へ深くして高さ 1.6。跨座式の車両（pak128.japan の車両）は車体の下端が地面の高さに描かれ、裾が桁の上の部分を隠す
- 高架の柱: 桁がタイルを出入りする辺ごとに、その辺の角に柱を立て、柱の頭から辺の中点の桁の下へ腕を渡す（iss と同じ並び）。版は柱を立てる側で、`front` は手前（南北の線は東、東西の線は南）、`back` は奥、`center` は両側。行き止まりは桁の端にも同じ柱と腕。iss は柱をタイルの角ちょうどに立てるが、AMI はタイルの内側に面を合わせて立て、隣のタイルの柱と背中合わせにする（門型の橋脚と同じ。角に立てると、絵がタイルの持ち分で切られて柱が半分になる）。複線は、西（北）の線を `back`・東（南）の線を `front` にすると、柱が外側に並ぶ（`docs/monorail_elev_pair.png`）
- 絵の並び: 線路の通常の版と同じシート（`sheetlib` の `track_sheet`。部品は `tools/blender/sheetlib/monorail_parts.py`）。カーブは斜めの絵（iss と同じく、dat の `image[sw]` などが斜めのセルを指す）。近い斜めの絵は無い（iss の dat にキーが無い）。分岐の絵（`image[nse1]` などの 1・2）は iss と同じく入れたが、本体は `monorail_track` では自動で選ばない（[way-addon.md](../../docs/reference/way-addon.md) の 9.2）。分岐の追加画像（ex 画像）は無い
- 雪の絵: 桁の上面だけを白くする（iss の跨座式は雪の絵を持たない。AMI のほかの way にそろえて足した）。柱は夏と同じ
- アイコン: 背景は紫（モノレール。`blender/icons.py` の `WAY_BG`）。高架の版は右下に版の札（前・中・後）と下の帯
- 値: 150 km/h、地上 30000・600、高架 60000・1200（地上の 2 倍）、トンネル 120000・2400（4 倍）、登場 1900（#110 の一覧。`blender/ami_dat.py` の `VALUES`）
- pak は `ami_monorail.pak`（`build.py` の `KINDS`。車庫も入る）
- 見本は `ingame/monorail.sh`（`ingame/monorail.nut`）。ゲームの写し（`work/monorail_game/<PORT>/`）を起動し、地上（車庫と輪・十字・斜め・行き止まり）、高架の 3 版（直線・L 字・T字・斜め・行き止まり）、複線、トンネルを敷き、電化の要らない車両の編成を輪で走らせる。`EXTRA_PAKS` で、借りた車両の pak を写しの中にだけ入れられる。`SNOW=1` で降雪側、`CAPTURE=1` で撮る。使い方はスクリプトの冒頭
  - 確認画像（2026-11-22、`OTRPv64_3.exe`、`flat_512.sve`）: `docs/monorail_ground_temperate.png`（地上の輪・十字・車庫の口の T字）、`monorail_elev_front.png`・`monorail_elev_center.png`・`monorail_elev_back.png`・`monorail_elev_pair.png`、`monorail_tunnel_diag.png`（左がトンネル、右が地上の斜め）、`monorail_snow.png`（降雪側の地上と高架 `front`）、`monorail_vehicle.png`・`monorail_vehicle_zoom.png`（地上を走る編成）、`monorail_depot_vehicle.png`（車庫から出る編成）
  - 車両は、ユーザーが動作の確かめに渡した pak128.japan の跨座式の車両（玉野の 4 両編成。battery）を、写しの中にだけ入れて走らせた。リポジトリには入れていない。高架の上を走る編成は見ていない（地上から高架へ上がる坂を敷いていない）

### 運河の作り（#114）

- 物: 地上の `ami_canal`（waytype `water`）と船の車庫 `ami_canal_depot`（下の「車庫の作り」）。並びは iss の運河（`../refs/iss/src/way/water/canal.dat`。地上だけ）に合わせ、高架・橋・トンネル・基盤の版は作らない（2026-11-22、ユーザーの決定）
- **運河を歩道に突き当てない**。運河と歩道（`ami_sidewalk*`）はどちらも waytype が `water` で、並べて敷くだけならつながらないが、どちらかを相手のタイルに突き当てる（横切らせる）と、そのタイルが後から敷いた方に置き換わってつながり、船が歩道の上を通る（2026-11-22、ゲームで確認。[#114 のコメント](https://github.com/128na/simutrans-addon-dev/issues/114#issuecomment-7065095194)・`docs/canal_link_sidewalk.png`）。本体は way の `max_weight` で経路を絞らないので、dat では止められない。歩道の waytype は今のまま（2026-11-22、ユーザーの決定）
- 形: 地面より下がった水面（地面から 0.45 下）と、水面を囲む石積みの護岸、地面の高さの笠石（幅 0.35）。水面はタイルの辺から 0.5 内まで（iss・pak128 と同じく、タイルいっぱい近く）。水路の外は描かない（地面のまま）。部品は `tools/blender/sheetlib/canal.py`
  - 水路の平面は道路と同じく腕の和（タイルの中心の正方形と、つながる辺ごとの腕）。T字・十字は腕と腕のあいだの角に岸が残る
  - カーブは斜めの絵（AMI の線路・道路と同じ。dat の `image[sw]` などが斜めのセルを指す）。斜めは、つながる 2 辺の中点を結ぶ線に沿う帯で、タイルの辺で直線と同じ幅になる
  - 近い斜め（`diagonal[close1]`・`[close2]`）の絵も持つ。ただし運河の斜め 2 本を 1 タイルずらして敷くと、分け合うタイルには way が 2 本入り（`[check]` の `two_ways=true`）、それぞれの斜めの絵が出る（`docs/canal_close.png`）
  - 坂・急坂は水面ごと傾ける（pak128 と同じ。iss は閘門を描くが、AMI は描かない）
  - 地面より下の形は、水路の外のタイル全面に置いた holdout の材質の板で隠す（手前の岸の陰の水面と、手前の岸の壁が、本物の地面と同じく隠れる）
- 分岐の絵（1・2）は持たない（本体は water の way の分岐の絵を選ばない）
- 雪の絵は笠石だけを雪にする。水面は夏と同じ
- アイコン: 背景は青緑（運河。`blender/icons.py` の `WAY_BG`）
- 値: 60 km/h、費用 25000・維持費 500、登場 1900（#110 の一覧。`blender/ami_dat.py` の `VALUES`）
- pak は `ami_canal.pak`（`build.py` の `KINDS`。船の車庫も入る）
- 見本は `ingame/canal.sh`（`ingame/canal.nut`）。ゲームの写し（`work/canal_game/<PORT>/`）を起動し、地上（車庫と輪・十字・斜め・行き止まり）、坂と急坂、近い斜めを敷き、pak128 の船を輪で走らせる。`SNOW=1` で降雪側、`CAPTURE=1` で撮る。運河と歩道のつながりは `NUT=ingame/canal_link.nut` で見る（使い方はスクリプトの冒頭）
  - 確認画像（2026-11-22、`OTRPv64_3.exe`、`flat_512.sve`）: `docs/canal_ground.png`（輪・十字・車庫の口の T字）、`canal_diag.png`（斜め）、`canal_slope.png`（坂・急坂）、`canal_close.png`（1 タイルずらした斜め 2 本）、`canal_depot.png`（車庫と、出てきた船）、`canal_snow_ground.png`（降雪側）、`canal_link_sidewalk.png`（運河・歩道・運河を一続きに敷き、歩道の上を通る船）

### 車庫の作り（#112）

- 線路・路面軌道・道路の 3 つ（`ami_rail_depot`・`ami_tram_depot`・`ami_road_depot`。`blender/catalog.py` の `DEPOTS`）と、モノレールの `ami_monorail_depot`（#113。入口の幅は線路と同じ 3.4、高さも同じ 26px。玉野の 4 両編成が入口で切れずに出た。`docs/monorail_depot_vehicle.png`）と、船の `ami_canal_depot`（#114。入口の幅 7.0。pak128 の船は幅がタイルの大半あるため。車庫は運河の行き止まりに建てる。pak128 の船が入口から出た。`docs/canal_depot.png`）。[ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md) の第 2 弾の物で、手本は blender-poc の料金所の作り（1 タイルの building に奥と手前の絵）
- 大きさは、箱積み駅舎の箱 1 段（1 タイル × 高さ 2 段 = 32px。[#140](https://github.com/128na/simutrans-addon-dev/issues/140)）に収める（2026-11-21、ユーザーの決定）。屋根は平らで、笠木の上面がちょうど 2 段。軒・屋根・柱形・腰壁を含めて、奥の絵も手前の絵も、128px のセルの六角形 (64,32)(128,64)(128,96)(64,128)(0,96)(0,64) の中に描く。奥の絵の上端は y32 で、本体が絵から出す建物の高さは 2 段になり、高架（2 段）を上に引ける（下の「高架」）
- 形: 壁の面はタイルの端から 0.1 内、壁の上に笠木、壁の中ほどに会社の色の帯（`player1` の色）、角と入口の脇に柱形、側壁と奥の壁に窓、足元に腰壁（タイルの端まで出し、地面より約 1px 下から立ち上げる）。入口の高さは 26px（pak128 の車両の車体はいちばん高いもので 25px。測り方は記録）。入口の幅は線路 3.4・路面軌道 3.2・道路 4.6（タイル 10）。寸法は `tools/blender/sheetlib/depot.py` の定数と `DEPOT_SHAPES`
- 絵: 道の出る向き（layout 0〜3 が南・東・北・西。本体の決まりは [way-addon.md](../../docs/reference/way-addon.md) の 5 章）ごとに、奥の絵（北・西の壁と奥の壁の内側）と手前の絵（南・東の壁と屋根）。手前の絵は車両の後に描かれ、車庫に出入りする車両を隠す。雪の絵は屋根と笠木を白くした版（シートの 3・4 行目）。アイコンとカーソルはシートの 5 行目（`blender/icons.py` が layout 0 の絵から作る。札の字は「庫」）
- 下の way の絵: 道路の行き止まりの絵はタイル全体を塗り、地面より 1px 下に描かれる。腰壁を 1px 下へ延ばして隠したが、2px にすると六角形の外へ出るので、建物の手前の下の縁に道路の端が 1px の点線で残る（`docs/depot_road_temperate.png` の右）。見た目はユーザーが見る
- 路面軌道の車庫は、路面軌道だけの行き止まりに建つ（道路の上の路面軌道の行き止まりは way が 2 本のタイルなので建たない。本体の決まり）
- 高架: AMI の高架の線路（`ami_rail_ballast_elev_single`）を、AMI の車庫と pak128 の `TrainDepot` の上（2 段上のタイル）に敷けた（`docs/depot_elevated.png`）。pak128 には高架の運河が無いので、箱の 2 段目の代わりに高架の線路で見た
- 値: 費用 線路・路面軌道・モノレール 850000・道路 700000・船 900000、維持費 1800、登場年 1900、引退 2999 年（`blender/ami_dat.py` の `DEPOT_VALUES`。値の決め方は「第 2 弾の物の値」）。`noinfo=1`・`needs_ground=1`
- pak は種類ごとの pak（`ami_rail.pak`・`ami_tram.pak`・`ami_road.pak`・`ami_monorail.pak`・`ami_canal.pak`）に入る（`build.py` の `KINDS` の名前の頭）
- 検査: `check.sh` が `check_depot.py` を回す。dat の building の絵の塗った画素が六角形の中か（画素の中心で判定）と、奥の絵の上端が y32 より下かを見る
- 見本は `ingame/depot.sh`（`ingame/depot.nut`）。ゲームの写し（`work/depot_game/<PORT>/`）を起動し、AMI の車庫と pak128 の車庫（`TrainDepot`・`TramDepot`・`CarDepot`）を、AMI の way の上に 4 つの向きで並べ、壁の基盤の版と架線つきの壁の上にも建てる。`SNOW=1` で降雪側、`CAPTURE=1` で撮る、`CAPTURE=1 VEH=1` で車庫から編成を出して続けて撮る。使い方はスクリプトの冒頭
  - 確認画像（2026-11-21、`OTRPv64_3.exe`、`flat_512.sve`）: `docs/depot_<種類>_<気候>.png`（左が pak128 の車庫、右が AMI の車庫。向きは 4 つ）、`depot_rail_wall_catenary.png`（壁の基盤の版と架線つきの壁の上）、`depot_vehicle.png`（降雪側で車庫から出る機関車と牛車。入口の中の車両が壁と屋根に隠れる）、`depot_elevated.png`
  - 1930 年の路面軌道には電化の要らない車両が無いので、路面軌道の車庫から出る車両は見ていない

### 操車場の作り（#115）

- 線路の操車場 `ami_rail_yard` 1 つ（building の `stop`。`blender/catalog.py` の `RAIL_YARD`）。[ADR 0008](../../docs/adr/0008-ami-scope-second-phase.md) の第 2 弾の物。荷を扱わない駅の建物で、線路の上に建てると、乗客も郵便も扱わない駅になる。時刻表に入れた列車はそこへ行って止まり、折り返す。乗客の駅の隣に建てると、その駅の一部になる（2026-11-22 にゲームで見た。本体の決まりは [way-addon.md](../../docs/reference/way-addon.md) の 5 章）
- 見た目は線路の脇の構内通路（2026-11-22、ユーザーの決定。[#115](https://github.com/128na/simutrans-addon-dev/issues/115)）。線路の奥の側（南北の線路なら西、東西の線路なら北）に、低い歩み板（グレーチング）と黄色の柵を置き、隣に駅の建物が無い端には階段を付ける。全部を奥の絵にするので、止まった車両は通路の上に描かれる。通路の線路の側の縁は、pak128 の乗客の駅（`train_platform_early`）のプラットフォームの線路の側の縁（線路の中心から約 1.0。タイル 1 辺 = 10）にそろえ、乗客の駅の隣では一直線に並ぶ（2026-11-22、ユーザーの指摘「プラットフォームの線路寄りに合わせるとよい」。`docs/yard115_pax_edge_zoom.png`）。歩み板は道床の肩の上に載り、柵は線路の壁とほぼ同じ位置に来る。壁つきの線路（基盤の版と壁）の上にも建つ
- 大きさは車庫と同じく箱積み駅舎の箱 1 段に収める（歩み板の上面は約 4px、柵の上端は約 11px）。寸法は `tools/blender/sheetlib/yard.py` の定数
- 絵: `dims=1,1,8` の 8 つの配置（ビット 0 が線路の向き、ビット 1・2 が南・東と北・西の隣に駅の建物が無いこと。並びは `yard.py` の冒頭）ごとに、夏と雪の奥の絵（シートの 1・2 行目）。雪の絵は歩み板を白くした版。アイコンとカーソルはシートの 9 列目（`blender/icons.py` が layout 6 の絵から作る。札の字は「操」）
- 建つのは地上の直線の線路だけ。斜め（「No through station here!」）と坂（「Stops on slope require a slope-capable descriptor!」）には本体が建てない。高架の線路の上には建つが、絵は地上用なので、通路が高架の脇に浮いて見える（`docs/yard115_elevated_zoom.png`。高架用の版を作るかは [#159](https://github.com/128na/simutrans-addon-dev/issues/159)）
- 値: 費用 60000（600 cr）、維持費 1800、登場年 1900、引退 2999 年、`level=1`（`blender/ami_dat.py` の `YARD_VALUES`。値の決め方は「第 2 弾の物の値」）。`noinfo=1`・`noconstruction=1`・`needs_ground=1`。下に敷く線路の費用は別にかかる
- pak は `ami_rail.pak` に入る（`build.py` の `KINDS` の名前の頭）
- 検査: `check.sh` が `check_depot.py` を回す（車庫と同じく、絵が六角形の中か、奥の絵の上端が y32 より下か）
- 見本は `ingame/yard_sample.nut`（撮る場所は `sample_spots.sh` の `YARD_SPOTS`）。`sample_parallel.sh` に `NUT=ingame/yard_sample.nut` を付けて流す。区画は 1 タイルと 3 タイル（南北・東西）、乗客の駅の隣、並べた留置線、壁つきの線路、列車（車庫から出して操車場で止める）、斜め・坂・高架の試し。駅になること・乗客と郵便を扱わないこと・隣の駅とつながることを `[check]` で返す
  - 確認画像（2026-11-22、`OTRPv64_3.exe`、`flat_512.sve`）: `docs/yard115_temperate_Y1.png`（南北の 1 タイルと 3 タイル）、`yard115_snow_YE.png`（東西）、`yard115_pax_snow_zoom.png`（乗客の駅の隣。通路が駅の側へ続き、階段は反対の端だけ）、`yard115_pax_edge_zoom.png`（乗客の駅との境の拡大。プラットフォームと通路の線路の側の縁がそろう）、`yard115_temperate_YG.png`（並べた留置線）、`yard115_temperate_YW.png`（壁つきの線路）、`yard115_train_zoom.png`（止まった機関車が通路の上に描かれる）、`yard115_elevated_zoom.png`（高架の上）
  - 建てたときに引かれた額は 576 cr と 640 cr（2 か所）。本体は dat の `cost` をそのまま使う（[way-addon.md](../../docs/reference/way-addon.md) の 5 章）。600 cr からずれた原因は分かっていない（本体の式 `simtool.cc` の 5816 行付近では 600 cr。[#160](https://github.com/128na/simutrans-addon-dev/issues/160)）

### アイコン・カーソル（#25）

全部の way・way-object（線路 4 種・道路 3 種・路面軌道・歩道と、その基盤・高架の版、壁・架線・橋脚・橋・トンネル）で、同じ決まりで作る（2026-11-21、ユーザーの決定。#25 の案 A。版の字は漢字）。iss（背景色で構造、左上に版の漢字）と pak128 標準（左上に速度の標識、白い印で高架・橋・トンネル）を見比べて、way の一覧で 4 種の線路が並ぶ AMI では速度を大きく出すほうが見分けやすいとして決めた。案と見比べた画像は `docs/icons_compare_x2.png`・`icons_mock_A.png`・`icons_mock_B.png`、全部の dat のアイコンとカーソルの一覧は `docs/icons_all.png`、ゲームの道具のメニューとカーソルは `docs/icons_menu_<メニュー>.png`・`icons_cursor_<名前>.png`。

| 何で見分けるか | アイコン（32px） | カーソル |
|---|---|---|
| 種類 | 背景色（線路 緑・路面軌道 黄土・道路 青・高速道路 紺）と、左上の最高速度 | 札の色と速度 |
| 版 | 右下の黒い札の漢字（単・後・中・前、近い斜めの分け合うタイル用の twin は 双）。通常の版は札なし | 札の速度の後ろの漢字（例 160後） |
| 構造 | 下の帯（高架: 床と柱 2 本、橋: 床と水、トンネル: 暗い帯と口）。橋脚は高架の帯 | 絵（高架の躯体・橋の床・坑口） |
| 物 | 絵がその物（壁・架線・橋脚・歩道）。架線は左上に稲妻、橋脚は「脚」「門」、歩道は「歩」 | 札（架線は稲妻と版、橋脚・歩道は字） |

- 作り: `blender/icons.py` が、描いたシートの絵と dat から作り、dat の `icon`・`cursor` が指すセルに書く（シートの描画とは別に動く。`render.py` は描いたシートについて最後にこれを別の Blender で動かす）。絵は dat の `image[ns]` などが指す直線のセルで、way・橋・トンネルは北と南の隣のタイルの位置にも重ねてつなぎ、半分に縮める（壁・架線・橋脚も同じ。等倍で真ん中を切ると、壁の single は片側しか入らず、橋脚は灰色の塊になった）。歩道はタイル 1 枚を 1/4 にする（等倍・半分では敷石がアイコン全体を覆い、灰色のボタンに埋もれた）。文字は Arial Bold と游ゴシック Bold を 4 倍で描いて縮める（Windows の `C:/Windows/Fonts/arialbd.ttf`・`YuGothB.ttc` を読む。無い環境では止まる）
- 別のシートの絵を読む物がある（トンネルのアイコンは中の way のシート、twin の壁は front のシートの斜め）。`icons.py` にシートの名前を並べると、そのシートに書くアイコン・カーソルと、そのシートの絵から作るアイコン・カーソルを書き直す（#141）。`render.py` は `--own` を付けて呼び、描いたシートにだけ書く（`render_parallel.py` で並べて描くとき、ほかのプロセスが描いている途中のシートを上書きしないため）。ほかのシートにある分（way のシートを描いたときのトンネルのアイコンなど）は書かずに、作り直す命令を `[icon]` の行に出す。描き終えてから、その命令か、`D:/bin/blender/blender.exe -b --factory-startup --python blender/icons.py`（全部）を流す
- 別のシートの絵から作ったアイコン・カーソルは、`icons.py` が絵のセルの sha256 を、書いたシートの横の控え（`src/<シート>.icon_sources.txt`）に書く。`check_icons.py` が今のシートと比べ、絵のシートを描き直してアイコンを作り直し忘れると落ちる（#141。#89 で線路を描き直した後、在来線のトンネルのアイコンが古いままだった）。控えが要る物（トンネルの icon、twin の壁の icon・cursor）と、控えのセルが今の dat の指すセルかも見る。全部を書き直すと、要らなくなった控えは消える
- カーソルは、直線の絵（壁の `center` は行き止まりの端の壁、トンネルは坑口）の上に札を足したもの。前は道路とトンネルだけに札があり、線路・壁・橋脚には無かった。道路の壁の `center` はカーソルが空だった
- 壁だけの twin（`ami_wall_rail_twin`・`ami_wall_road_twin`）は back の版のシートを借りるので、アイコン・カーソルは back の版のセル（0.0・0.1）を指していて、back と同じ「B」が出ていた。今は back の版のシートの使っていないセル（0.4・1.4。`blender/ami_dat.py` の `TWIN_ICON_CELLS`）に置く
- 検査: `check.sh` が `check_icons.py` を回す（#97）。icon・cursor のセルをほかのキーが指していないか（重なると `icons.py` が書いたときに相手の絵が消えるか、同じアイコンになる）、icon の 32px とカーソルに絵があるか、waytype の違う物どうしでアイコンの背景の色相が 20 度以上離れているか、を見る（組は dat の waytype なので、どちらも `road` の道路と高速道路は比べない）。`icons.py` が dat の参照先に書いたかは、そのセルに絵があるかで見る（提供用の物 `__ex_donor` は `icons.py` が書かず、元の物のセルを使う）。色は `icons.py` の表を読まず、描かれた画素で比べる。別のシートの絵から作った物が、今の絵のシートから作られているかも見る（上の控え。#141）。意図して共有・借用するもの（提供用の物 `__ex_donor` のセル、橋脚・歩道の背景色）は、`check_icons.py` の `SHARE_SUFFIX`・`BG_BORROW` に理由と一緒に書く
- 版の札の漢字は、等倍（13px の札に字の高さ 10px）では細部がつぶれるが、雰囲気で読める（2026-11-21、ユーザーの判断）
- ゲームで撮るのは `GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=<ポート> bash ingame/icon_capture.sh`（`work/icons/`。メニューの中の位置はスクリプトの `CURSORS`）

### リリース用のサムネイル（#96）

公開物に使う画像は `docs/thumbnail/` の `thumbnail.png`（文字入り、OGP の 1.91:1）と `ogp.jpg`（同じ絵を Web 用に 1200x628 へ縮めた JPEG）。文字なしの画面は `plain.png`。生成画像は使わず、手本の iss（`docs/thumbnail.png`）と同じく、ゲームの画面に文字を重ねて作る。

いまの画像は、ユーザーが手動で撮影し、文字入れまで済ませたもの（2026-11-21。OTRPv64_3、画面の中心はおよそ (205,261)。構図の考え方は #103 のコメント）。

- 撮った画像は、ゲームの画面（道具欄と状態欄が入った 2560 幅の画面全体）を、別の道具で縦横同じ倍率に拡大して文字を重ねたもの。左右に透明な帯があってもよい
- 切り出す: アドオンのディレクトリで `uv run ingame/thumbnail_compose.py --manual <文字入りの画像> --manual-plain <文字なしの画面>`。左右の透明な帯と、上下の道具欄・状態欄（倍率で換算）を切り落とし、残りの高さで 1.91:1 になる幅を左端から切り出す（拡大・縮小はしない）。`thumbnail.png`・`ogp.jpg`・`plain.png` を書き換える。撮った画面の幅が 2560 でないときは `GAME_WIDTH` で渡す

構図を自動で作る仕組み（#103 で詰める）は、次の手順で 1 枚撮れる。

- 見本の街区は `ingame/thumbnail.nut` が `flat_512.sve` の写しに敷く（保存はしない）。並びはスクリプトの冒頭の表
- どちらもアドオンのディレクトリで動かす。先に `python -X utf8 build.py` で `dist/ami.pak` を作っておく
- 撮る: `GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=<ポート> bash ingame/thumbnail_capture.sh`。ゲームを 2560x1400 の画面で起動し、等倍（`gui.set_zoom(3)`）で `work/thumbnail/shot.png` に撮る。敷けなかったときは撮らずに止まる
- 文字を重ねる: `uv run ingame/thumbnail_compose.py`（`--plain` で文字なしの `plain.png` だけ）。道具欄と状態欄を切り落とすだけで、拡大・縮小はしない。題名・内容・種類の数（`src/` の dat から数える）はスクリプトの頭にある。フォントは Windows の Segoe UI と游ゴシック。`docs/thumbnail/` の画像を書き換える

### 後で足すもの

- 旧描画位置（SIS に合う）の線路。新描画位置で全部を作り終えてから、まとめて作る（別の PR でよい）

### 範囲に入れないもの

- 車庫（#112）・操車場（#115）以外の建物（blender-poc の料金所 `bpoc_tollbooth` は移さない）

## 対象

- Simutrans 本家 125.0.1 と OTRP（pak128）。OTRP だけの絵（分岐の絵・近い斜め・分岐の追加画像）は本家では使われないだけで、本家用の pak は分けない（ベータで決めた。2026-11-21、ユーザーの決定）
- 画像は 256px セル（`pak256` で切り出し、ゲームは pak128）

## 遊ぶ人向けの敷き方

- 導入: zip の中の `pak128` フォルダを、Simutrans の `addons` フォルダ（無ければ作る）に入れる。起動のオプション `-addons` は要らない（付けずに起動すると、アドオンを読み込むかを確かめる画面が出て、そこで選べる。2026-11-21、ユーザーの言葉。#137）
- 線路・道路は「版」を選んで敷く。single（単線・1 本）、back・center・front（複線・3 線の奥・中・手前）。基盤・高架の版と壁は、アイコンの右下の漢字（単・後・中・前。近い斜め用の壁は 双）で版を見分ける。通常の版（壁を重ねない地上の線路・道路）には札が無い
- 基盤の版の線路・道路に、同じ版の壁（way-object）を重ねると、壁つきの線路・道路になる。架線は「架線つきの壁」（壁の無い center の版は架線だけ）
- 版の奥・手前は、南北の線なら西が back・東が front、東西の線なら北が back・南が front。複線のカーブで画面の右と左に曲がる角では、外の線と内の線の版（back・front）が角の前後で入れ替わる。角のタイルは南北の辺と同じ版にする。線路は東西の辺を先に敷き、南北の辺を角のタイルまで後から敷く。壁は逆に、南北の辺を角のタイルまで先に敷き、東西の辺を後から敷く（同じ速さの壁は、後から敷いても前の版のままになるため。作りは「壁の敷き方」）
- 高架の下の地面には、橋脚の way を敷く。橋脚は路面軌道のメニューにある（線路の高架の下を地上の線路が横切るタイルには敷かない。敷くと線路とつながるか、線路が切れる。「高架と橋脚の作り」）
- 歩道は船のメニューにある（waytype が `water`）。道路の隣のタイルに敷く
- 盛土は路面軌道のメニューにある（waytype が `tram_track`）。高架の北・西の脇に `back`（札は 後）、南・東の脇に `front`（札は 前）を敷く。輪にして台を作るときは、北東・南西の角に `front` を後から敷く（「盛土の作り」）
- 電柱は船のメニューの way-object にある（札は 柱 と版。柵なしと柵つきは札が同じで、名前で見分ける）。電柱だけを立てるときは、柱を立てたい側（道路の側など）の版を選ぶ。柵の歩道に立てるときは、同じ版の柵つきの電柱を重ねる（柵が置き換わる）。同じ版を並べると電線がつながる（「電柱の作り」）
- 中央分離帯は道路のメニューの壁（way-object）にある（札は 分前・分中・分双）。4 車線は、奥のタイルに基盤の版 `back` と壁 `back`、手前のタイルに基盤の版 `front` と `front_divider` を敷く。輪にするときは、東西の辺の `front_divider` を、角が `back` のタイルの 1 つ手前で止める（「中央分離帯の作り」）
- 多車線の白線は、道路のメニューの路面表示の版（札の右下が 1〜7）で敷く。4 車線は奥から 1・2、6 車線は 3・4・5、8 車線は 3・6・7・5（「路面表示の版の作り」）
- 操車場は線路のメニュー（駅の道具）にある。地上の直線の線路の上に建てると、乗客も郵便も扱わない駅になり、列車を止めておける。乗客の駅の隣に建てると、その駅の一部になる（「操車場の作り」）
- ベータの既知の課題は [ACCEPTANCE.md の「ベータ版（第 1 弾）での扱い」](ACCEPTANCE.md#ベータ版第-1-弾での扱い)

## ライセンス

CC BY 4.0。

`docs/curve_study_*.png`（#88 の比べ）には、iss（作者 128na、`128na/iss`、CC BY 4.0）のシートのセルとゲームの画面を、AMI と並べるために切り出して含む。

## 必要なもの

- Blender 4.5 LTS
- makeobj（`PATH` にある）

## ビルド

アドオンのディレクトリ（`addons/ami/`）で、描画の道具は `tools/` にある（[tools/README.md](../../tools/README.md)）。

```powershell
D:\bin\blender\blender.exe -b --factory-startup --python blender/render.py   # シートを src/ へ（対象を絞るなら末尾に -- ami_rail_ballast）
python -X utf8 blender/ami_dat.py                                              # dat を src/ へ
python -X utf8 build.py                                                        # makeobj で dist/ へ
```

- `build.py` は、全部入りのまとめ `dist/ami.pak` と、種類別の `ami_rail.pak`（線路）・`ami_tram.pak`（路面軌道）・`ami_road.pak`（道路）・`ami_monorail.pak`（モノレール）・`ami_canal.pak`（運河）・`ami_extra.pak`（付属）・`ami_scenery.pak`（景観）を作る。dat が無い種類は作らない。makeobj の出力に警告かエラーがあれば止まる
- `build.py` は続けて、`src/ex_donors.dat` から提供用の pak（`work/ex/donors.pak`）を作り、各 pak の線路・路面軌道・架線つきの壁へ ex 画像を継ぎ足す（上の「分岐の追加画像」）。継ぎ足した数を出し、pak ごとに名前で当たる提供用の物が全部写ったことと、継ぎ足した絵（26〜29・31〜34 番が空でなく、通常の T字・十字と違うこと、30・35 番が通常の十字と同じこと）を確かめ、違えば止まる。pak の中の ex 画像の数は `python -X utf8 ex_graft.py --list dist/ami.pak` で見られる
- シートを複数描くときは `python -X utf8 ..\..\tools\blender\render_parallel.py <対象>...`。レイアウト検証用モードは `SHEET_LAYOUT=1`（`work/layout/` に書く）
- レイアウト検証用モードの pak は `SHEET_LAYOUT=1` で描いた後、`SHEET_LAYOUT=1 python -X utf8 build.py`（`work/layout/dist/` に作る）
- 同じシートの通常の描画とレイアウト検証用の描画を同時に動かさない。セルごとの生の絵（`work/<シート>_<セル>.png`）の名前が同じで、互いのセルを取り込んだシートができた（2026-11-17）
- `src/`（dat とシート）はコミットする。`dist/` と `work/` はコミットしない
- 配る zip は `python -X utf8 release.py --version <版> --paks <pak>...`（`work/release/ami-<版>.zip`。`--paks` は `dist/` の pak の名前を拡張子なしで並べる）。中身は `pak128/` の pak と、`release/readme.txt`（遊ぶ人向けの説明。`{version}` を版の名前に置き換える）・`release/license.txt`（CC BY 4.0 と帰属）・`ami_lineup.txt`（選んだ pak に入る物の一覧。`lineup.py` が `src/` の dat と `build.py` の `KINDS` から作る。列は名前・種類・最高速度・購入費・維持費・登場年。`python -X utf8 lineup.py --format html` で同じ一覧を HTML でも出せる）。全部入りの `ami` と種類別を同時に選ぶと止まる（同じ物を二重に読む）。`--extract` で `work/release/ami-<版>/` にも展開する
  - 配る形（[ADR 0007](../../docs/adr/0007-ami-beta-distribution.md)）: このリポジトリの GitHub リリース（プレリリース）に、種類別の 4 つを入れた zip を置く。全部入りの `ami.pak` は入れない（同じフォルダに両方を置くと二重に読む）。ベータの版は `beta.<n>`、タグは `ami-beta.<n>`。第 1 弾は `python -X utf8 release.py --version beta.1 --paks ami_rail ami_road ami_tram ami_extra`。第 2 弾の景観（盛土。#123）を作ってからは、種類別の pak に `ami_scenery` が加わる（ADR 0008。`--paks` に `ami_scenery` も並べる。配布の readme にも載せた）
- 精細化のラウンドの版（#56）: `blender/round.py` が、在来線一式を `_round<n>` の名前で描いて `rounds/ami_round<n>.pak` を作る（`src/`・`dist/` は変えない）。ラウンドの描き分けは `round.py` の `ROUND_SETTINGS`（ラウンド 1〜7 の値は、ラウンド 8 で本番に入れる前の `render.py` に重ねる値。今の `render.py` に重ねると二重にかかる）。在来線のほかの系統（`rail_slab`・`tram`・`road`）は `AMI_FAMILY=<系統>` で選び、描き分けは `blender/round_<系統>.py`、pak は `rounds/ami_<系統>_round<n>.pak`。描かずに `python -X utf8 blender/round.py <n>` だけを流すと、今の `src/` の絵を `_round<n>` の名前にした pak を作る（本番の絵をラウンドの版と並べて撮るとき）。`rounds/` の pak は記録としてコミットする。見本は `SUFFIX=_round<n> EXTRA_PAKS=rounds/ami_round<n>.pak bash ingame/sample_parallel.sh`、くどさは `ingame/calib_capture.sh`（`WAYS_NUT`・`PAKS`・`NUT`。検証用のフォルダの写しで起動する。基盤・高架の版は `NUT=ingame/calib_struct.nut`）と `tools/blender/busy_measure.py`（基盤・高架の版は `BUSY_REF` に通常の版の名前を渡し、その範囲に限った値で判定する）。橋・トンネルは `NUT=ingame/calib_bt.nut`（トンネルは地形を作るので `PRE=1`）、壁・橋脚を重ねた版は `NUT=ingame/calib_wall.nut`（重ねる前と比べるのは `BUSY_PAIR`）、拡大率ごとの値は `ZOOMS` と `BUSY_BYZOOM=1`で測る（物差しは [way-addon.md](../../docs/reference/way-addon.md) の 11 章）。回し方はスキル [way-refine-rounds](../../.claude/skills/way-refine-rounds/SKILL.md)
- 設定は `blender/catalog.py`（軌道の種類と、そこから導く way・基盤・高架・橋・トンネルの名前）、`blender/render.py`（描き分け・シート名）、`blender/ami_dat.py`（dat と値）、`blender/addon_config.py`（判定の道具が読む対応表）

## 導入と検証

ゲームでの確認は blender-poc と同じく、アドオンを確かめるゲームの OTRP 版で `flat_512.sve` を開き、MCP のスクリプトを流す。
makeobj は本家と同じもの（60.12）なので、ふだんの確認は OTRP だけで行う。配る pak の本家 125.0.1 での読み込みは、配る前にユーザーが確かめる（スクリプトが使えない。ACCEPTANCE の 6-4）。

```bash
GAME_DIR=F:/Simutrans/addon_check EXE=OTRPv64_3.exe bash ingame/sample_check.sh
# 高速線の見本は TRACK=ami_rail_slab を前に付ける
```

- `dist/ami.pak` をゲームの `addons/pak128/` に写し、OTRP を MCP つきで起動して `ingame/sample.nut` を流す。見本は温暖側 (20,20) と降雪側 (276,20) に敷く。敷く軌道の種類は `sample.nut` の先頭の `TRACK`（通常の版の way の名前）で選ぶ。基盤・高架・橋・トンネルの名前はそこから導く
- 見本は way の全部の絵を、周りとつながった形で出す（行き止まり・1 タイル・斜め・輪と十字・坂・急坂・近い斜め・十字の分岐の固定・分岐の自動選択 8 通り。区画の表は `sample.nut` の冒頭）。降雪側は敷いた後に一帯を降雪に塗り直す
- 返り値の `[check]` の行に、近い斜めの分け合うタイルが way 1 本か（`two_ways=false` なら近い斜めの絵が使われている）と、分岐の絵を固定する道具があるかを出す
- 基盤の版は `WALLED` に way と壁の組で足す（同じ区画の並びで、壁を同じ経路に重ねる。近い斜めの区画 G は敷かない）。複線と壁の組（輪・近い斜め・行き止まりの並び）は区画 W。架線つきの壁は `CATENARY`（区画 W の後に同じ並びで 4 版）と区画 WE（区画 W と同じ並びで、壁を架線つきの版にしたもの）で、`[check]` の行の way の名前の後ろの `elec` は電化されていること。`[check]` の行には、区画 W・WE の角と分け合うタイルの way と壁の名前も出す（`(2)` は way が 2 本）
- 高架は地上の区画の東 80 に敷く（`sample.nut` の `ELEVATED`）。区画の並びは基盤の版と同じで、高架の 4 版に壁の 4 版を重ね、真下に橋脚の way を敷く。その南に区画 WV（区画 W の並びを高架で）・WVE（区画 WE の並びを高架で）・高架に架線つきの壁の single・区画 J（高架と地上のつなぎ目）。`[check]` の行の高架の名前の後ろの ` / ami_pier_rail` は、真下の地面の橋脚の way（`(2)` は 2 本）
- 撮るのは `bash ingame/sample_capture.sh`（`work/sample/` に温暖側・降雪側の区画ごと）。レイアウト検証用モードの pak は `PAK=work/layout/dist/ami.pak` で入れ、`OUT=work/sample_layout` で撮る。終わったら `dist/ami.pak` を入れ直す
- 全区画をまとめて撮るときは `GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> TRACK=ami_rail_slab bash ingame/sample_parallel.sh`。8 台のゲームを `work/parallel/` の写しで起動し、見本を敷いて撮り、閉じる。208 画面が準備込みで約 40 秒。`sample_check.sh` は要らず、`GAME_DIR` には書き込まない。台数は `JOBS`
- pak128 標準の線路（`Rail_160_Tracks`）とのつなぎ目と、坂・急坂でのレールの寄りは `GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=<ポート> bash ingame/seam_slope_check.sh` で測る（#62 で足した）。見本は `ingame/seam_slope.nut`（線路の種類ごとに、東西・南北・斜め・坂のつなぎ目と、急坂・1 段の坂の十字）。ゲームは `work/seam_game/<PORT>/` の写しで起動し、`GAME_DIR` には書き込まない。MCP のクライアントの場所は、ほかの `ingame/` のスクリプトと同じく `ingame/mcp_client.sh` で決める。読み方は `tools/blender/seam_judge.py`・`slope_measure.py` の冒頭。在来線にも、つなぎ目の斜めの 1 か所（草 1px）と、十字の坂のタイル（急坂 3・1 段の坂 2）で寄りの NG が出る（2026-11-21 の値は記録 [2026-11-21_ami-rail-concrete](../../docs/records/2026-11-21_ami-rail-concrete.md)）
- 分岐の追加画像（#57）は `GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=<ポート> bash ingame/ex_check.sh` で確かめる。`dist/ami.pak` を入れて起動し、`ingame/ex_sample.nut` を流して開いたままにする。見本は線路の種類（`WAYS`。在来線・弾性まくらぎ直結軌道・高速線・路面軌道と、在来線の基盤 4 版に架線つきの壁）ごとに、Y字分岐と三方分岐を根元の 4 向きで敷き（温暖側 (150,20)、降雪側は x + 256、区画は南へ 40 ずつ）、固定の道具で 26〜35 番に固定した T字・十字と、何もしない T字・十字を並べる。`[check]` の行は、自動で選ばれた絵が固定と同じなら `ok`、通常の絵のままなら `plain`、違えば `got/want`。撮るのは `PORT=<ポート> OUT=work/ex/after bash ingame/ex_capture.sh`
- 壁つきの線の間の渡り線（#101）は `GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=<ポート> bash ingame/crossover_wall.sh`。ゲームの写し（`work/crossover_game/<PORT>/`）に `dist/ami.pak`（`PAK` で替えられる）と iss の線路・架線の pak を入れて起動し、`ingame/crossover_wall.nut` を温暖側 (20,20) に流す。AMI の壁・架線つきの壁・iss の架線の 3 組を、線の並び（back+front・back+center・center+front・3 本）と敷き方（本線を敷き直す・渡り線にも壁・上の線の版で渡り線・通常の版で渡り線・壁の後に渡り線を敷いてから本線を敷き直す）ごとに敷く。続けて `SNOW=1`（降雪側に同じ見本）・`CAPTURE=1`（撮る。`SNOW=1` と合わせると降雪側）・`STOP=1`（閉じて写しを消す）を渡す
- iss の版ごとのカーブ・分岐の絵と並べる検討（#88。決定は「入れない」で、本番の pak には関わらない）は `GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=<ポート> bash ingame/curve_switch_study.sh`。ゲームの写し（`work/study_game/<PORT>/`）に `dist/ami.pak` と iss の線路の pak を入れて起動し、`ingame/curve_switch_study.nut` を流す。続けて `CLASSIFY=1`（分岐のタイルの自動の絵を読む）・`TRAIN=1`（`ingame/curve_switch_train.nut` で列車を走らせ、渡り線の絵を読む）・`CAPTURE=1`（撮る）・`STOP=1`（閉じて写しを消す）を渡す。結果は記録 `docs/records/2026-11-21_ami-curve-switch-variants-study.md`
- 同じポートでゲームが動いていると、`sample_check.sh` は止まる（他のゲームに見本を流さない）。閉じるのは自分で起動したゲームだけ
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
- 配る pak の読み込みは `GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=<ポート> PAKS="<pak>..." bash ingame/beta_check.sh`。`work/beta_game/<PORT>/` の写しに `PAKS`（既定は `dist/` の種類別の 5 つ（`ami_scenery.pak` は #123 で足した）。zip を確かめるときは `release.py --extract` で展開した pak）だけを入れて起動し、`src/*.dat` の全部の物（way・way-object・橋・トンネル）を 1 つずつ道具で敷いて、タイルの物の名前を読む（`ingame/beta_check.nut`）。先頭が `ok <数> items` なら全部敷けた。続けて、読んだ AMI の pak と、ログ（`-debug 3`）の AMI の物の警告を出す（ACCEPTANCE の 6-3）

道路の見本は線路と別のゲームで敷く（`sample.nut` はコマンドラインの長さの上限に近いので、道路の区画を足さない）:

```bash
GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe NUT=ingame/road_sample.nut OUT=work/road_sample bash ingame/sample_parallel.sh
# 1 台で敷いて開いたままにするなら NUT=ingame/road_sample.nut bash ingame/sample_check.sh（撮るのは NUT=ingame/road_sample.nut OUT=work/road_sample bash ingame/sample_capture.sh）
```

- `ingame/road_sample.nut` は道路 3 種（`ROADS`）を、温暖側 (20,20) と降雪側 (276,20) に 30 ずつ南へずらして敷く（生活道路・一般道路・高速道路の順）。区画は線路の見本と同じ A・F・C・B・D・E・G に、分岐の自動選択（H。2 本の道路を隣り合わせに並べて渡り口でつないだ形。南北と東西）、分岐の絵の固定（I。T字 4 種と十字を選択 2・1 の順に）、pak128 標準の `Road_050` とのつなぎ目（K）、隣り合う十字（L）。表は `road_sample.nut` の冒頭
- `[check]` の行: 近い斜めの分け合うタイルが way 1 本か（`two_ways=false`）と、区画 H（自動選択の `auto`）・I（固定の `pin1`・`pin2`）・L（隣り合う十字の `west`・`east`）の絵。値は `way_x.get_image_id()`。判定は `road_sample.nut` の `SWITCH_IMAGES`（`ami_dat.py` の `ROAD_SWITCH_IMAGES` と同じにする）で変わる。今（偽）は、どれも通常の T字・十字（`plain`）と同じ絵なら `ok`。真にすると、`auto` が `pin1`（dat の「1」）と同じで `plain` と違えば `ok`、`pin1`・`pin2` が同じなら `same12`、L の十字が T字の「2」なら `t2`

道路を何本か並べた交差点の組み合わせ（2×4〜6×6）は別の見本で敷く（温暖側だけ）:

```bash
SEASONS=temperate:20:20 GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe NUT=ingame/road_junction_sample.nut OUT=work/junction bash ingame/sample_parallel.sh
```

- `ingame/road_junction_sample.nut` は道路 3 種を (20,20) から 22 ずつ南へ、組み合わせ 8 つ（南北の本数 × 東西の本数が 2×1・1×2・3×1・1×3・2×2・2×3・3×2・3×3）を東へ 12 ずつ敷く。`[check]` の行に、十字のタイルごとに通常の十字（`nsew`）か T字の「2」（`nse2` など）かを出す（判定は、同じ見本の中で固定の道具で固定した T字の絵と比べる。分岐の絵の無い今は、どれも `nsew`）。撮る場所は `sample_spots.sh` の `JUNCTION_SPOTS`
- `NUT` に `road_sample.nut` を渡すと、撮る場所は `sample_spots.sh` の `ROAD_SPOTS`（`LO_*`・`GE_*`・`EX_*`）になる。`sample_parallel.sh` は全部敷けたときも 1 台目の報告（`[check]` の行）をログ（`work/parallel/<ポート>.log`）と画面に出す
- 道路の確認画像は `road_*.png`（2026-11-19）。`LO`・`GE`・`EX` は生活道路・一般道路・高速道路。`B`（輪と十字）・`AFC`（行き止まり・1 タイル・斜め）・`DE`（坂と急坂の十字）・`G1`（近い斜め）・`HV`・`HH`（分岐の自動選択。2 本並べた道路の渡り口）・`I0`（T字 nse の固定の 1・2）・`I4`（十字の固定の 1・2）・`K`（pak128 標準の `Road_050` とのつなぎ目）、`GE_L_zoom`（隣り合う十字に、前の T字の形の「2」の絵が出たところ。3 倍）、`*_priority_*`（優先道路の十字）・`GE_4x4_cross_zoom`・`GE_6x6_cross_zoom`（隣り合う十字。記録 [2026-11-20_ami-road-switch-design](../../docs/records/2026-11-20_ami-road-switch-design.md)）、`snow_*` は降雪側、`layout_*` はレイアウト検証用モード、`EX_dash_zoom`（直線と斜めの継ぎ目の破線。4 倍）・`EX_slope_zoom`（坂と平地の継ぎ目。4 倍。この 2 枚は、直線と坂の破線が 1 本抜けていたときのもの）、`EX_dash_*`（2026-11-20 に破線の抜けを直した後。`sheet_before`・`sheet_after` はシートの直線のセルを 3 枚つないだもの、`straight_ew`・`straight_ns`・`slope`・`close_diag` はゲームの画面の 4 倍）

道路の壁・基盤の版・高架・橋脚・橋・トンネルの見本も別のゲームで敷く:

```bash
GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe NUT=ingame/road_struct_sample.nut OUT=work/struct bash ingame/sample_parallel.sh
```

- `ingame/road_struct_sample.nut` は道路 3 種を、温暖側 (20,20) と降雪側 (276,20) に 30 ずつ南へずらして敷く。1 種ずつ東へ、地上の壁（通常の版に `single` の壁。近い斜めの区画 G は `back`・`front`）・地上の複線（基盤の版と同じ版の壁。輪 W1・行き止まりの並び W3・近い斜め W2）・高架（`single` と壁と真下の橋脚。隣り合う十字 L）・高架の複線（WV1〜WV3）・分岐の絵の固定（IB は基盤の版、IV は高架）・橋とトンネル（B1・B2・B4・T1・T3）・橋脚のつながり（P1 は `Road_050`、P2 は AMI の道路、P3 は地上の線路）。表は `road_struct_sample.nut` の冒頭
- `[check]` の行: 区画 G の分け合うタイルの way と壁（way 1 本で向きが 15 なら、通常の版の近い斜め）、複線の角と近い斜めの分け合うタイル（`(2)` は way 2 本で、壁が `twin` になっているか）、橋の床・端と坑口・トンネルの中の way と壁（`bridge`・`tunnel`）、橋脚の区画の地面の way（` / ` の後ろが橋脚の way と道路）、区画 IB・IV で固定した絵の番号（`get_image_id`）
- 撮る場所は `sample_spots.sh` の `STRUCT_SPOTS`（種類ごとに `LO_*`・`GE_*`・`EX_*`）。82 か所 × 温暖側・降雪側で 164 画面
- 確認画像は `road_struct_*.png`（2026-11-19。一般道路の `WA_B`（通常の版に壁を重ねた輪と十字）・`WP`（基盤の版の複線の輪）・`V_B`（高架の輪と十字）・`VP2`（高架の近い斜めの複線）・`B1`（平地から立ち上がる橋）・`B4`（高架と橋のつなぎ目）・`P1`（`Road_050` の上の橋脚）、高速道路の `T1`（トンネル）、降雪側の `snow_GE_V_B`）と、判断の材料の拡大（`road_wall_close_plain_zoom`・`road_wall_close_base_zoom`・`road_base_pair_corner_zoom`・`road_bridge_girder_zoom`・`road_elev_L_zoom`）、レイアウト検証用モードの拡大（`road_layout_pair_corner_plain`・`road_layout_elev_pair_corner_before`・`_after`・`road_layout_elev_twin_zoom`）。高速道路の中央線の破線の抜けを直した後（2026-11-20）の 4 倍は `road_EX_dash_bridge_zoom`（橋と坂の継ぎ目）・`road_EX_dash_tunnel_zoom`（トンネルの口の前）・`road_EX_dash_elev_zoom`（高架の複線）

路面軌道の見本も別のゲームで敷く:

```bash
GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe NUT=ingame/tram_sample.nut OUT=work/tram bash ingame/sample_parallel.sh
```

- `ingame/tram_sample.nut` は、線路の見本と同じ区画（A・F・C・B・D・E・G・I・H）を、土の上と、AMI の道路 3 種・pak128 標準の `Road_050` の上（道路を先に敷いて同じ経路に重ねる）に、温暖側 (20,20) と降雪側 (276,20) で 30 ずつ南へずらして敷く。土の上の区画には、橋脚とのつながりの区画 P もある。表は `tram_sample.nut` の冒頭
- `[check]` の行: 区画 G の分け合うタイル（道路の上では道路と路面軌道で `two_ways=true` になる）、区画 I の固定の絵、区画 H の自動選択の絵（通常の T字と同じなら `(plain)`）、道路の上の区画で道路が残っているか（`road=`）、区画 P のタイルの way。判定は `tram_sample.nut` の `SWITCH_IMAGES`（`ami_dat.py` の `TRAM_SWITCH_IMAGES` と同じにする）で変わる
- 撮る場所は `sample_spots.sh` の `TRAM_SPOTS`（`GR`・`LO`・`GE`・`EX`・`ST` は土・生活道路・一般道路・高速道路・`Road_050` の上）。47 か所 × 温暖側・降雪側で 94 画面
- 確認画像は `tram_*.png`（2026-11-20）。`GE_B`・`EX_B`・`ST_B`・`GR_B` は輪と十字（一般道路・高速道路・`Road_050`・土の上）、`GE_B_zoom` はその十字・カーブ・T字の 4 倍、`GE_AFC`・`GR_AFC`（行き止まり・1 タイル・斜め）、`GE_DE`（坂と急坂）、`GR_G1`・`GE_G1`（近い斜め）、`GR_I`（十字の固定の 1・2）、`GR_H0`（分岐の自動選択）、`switch_H0_zoom`（左が分岐の絵あり、右が無し。5 倍）、`GR_P`（橋脚の列を横切る）、`snow_*` は降雪側、`layout_*` はレイアウト検証用モード

歩道の見本も別のゲームで敷く:

```bash
GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe NUT=ingame/sidewalk_sample.nut OUT=work/sidewalk bash ingame/sample_parallel.sh
```

- `ingame/sidewalk_sample.nut` は、道路 4 種（AMI の 3 種と pak128 標準の `Road_050`）ごとに 14 ずつ南へ、温暖側 (20,24) と降雪側 (276,24) に敷く。区画は交差点の四隅（R）・広場と 1 タイル（Q）・坂（S）・急坂（T）・斜めの道路（D）・道路と運河の横切り（X）。表は `sidewalk_sample.nut` の冒頭
- `[check]` の行: 歩道を敷いた後も道路の向きと絵が変わらないか（`road=same`）、歩道の waytype（3 が `water`）、交差点の隣の歩道の向き（`corner(5,1)=9` は西と北）、区画 X の横切ったタイル（`objs` の 29 が踏切、`canal_tile` は運河に置き換わったか）
- 撮る場所は `sample_spots.sh` の `SIDEWALK_SPOTS`（`LO_*`・`GE_*`・`EX_*`・`ST_*`）。24 か所 × 温暖側・降雪側で 48 画面
- 確認画像は `sidewalk_*.png`（2026-11-20）。`GE_R`・`ST_R`・`LO_EX_R`（交差点の四隅。`ST` は `Road_050`）・`GE_R_zoom`（道路との境の 4 か所。5 倍）・`GE_Q`（広場と 1 タイル）・`GE_ST`（坂と急坂）・`GE_D`（斜めの道路）・`GE_X`（横切り）、`snow_GE_R` は降雪側、`layout_*` はレイアウト検証用モード

歩道の種類・高架の歩道・歩道の柵の見本（#119）は、1 台のゲームを開いたままにして敷いて撮る:

```bash
GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=47300 NUT=ingame/sidewalk_struct.nut bash ingame/game.sh
PORT=47300 OX=276 NUT=ingame/sidewalk_struct.nut bash ingame/game.sh RUN   # 降雪側
PORT=47300 OUT=work/sw119 SPOTS="F1:22:37 E1:25:48" bash ingame/game.sh CAPTURE
PORT=47300 bash ingame/game.sh STOP
```

- `ingame/game.sh` は、`work/game/<PORT>/` に検証用のフォルダの写しを作って起動する（`GAME_DIR` には書き込まない）。`RUN` で動いているゲームに見本を流し、`CAPTURE` で場所ごとに撮り、`STOP` で閉じて写しを消す。`OX` を渡すと、見本の行頭の `local OX = <数>;` を置き換える
- `ingame/sidewalk_struct.nut` は、温暖側 (20,20) と降雪側 (276,20) に、舗装の種類（P）、地上の柵（F1 道路の両脇・F2 L字・F3 広場・F4 坂・F5 T字）、高架（E1 高架の道路の両脇・E2 地上の道路を横切る・E3 L字）を敷く。表は `sidewalk_struct.nut` の冒頭
- `[check]` の行: 高架の歩道のタイル（高さ 2）の way と柵、地上の歩道の way と柵
- 確認画像は `sidewalk119_*.png`（2026-11-21）。`P_*` は舗装の種類、`F_*` は地上の柵、`E_*` は高架、末尾が気候（`temperate`・`snow`）

塗りを実装する前に、レイアウト検証用モード（部品ごとに画像で見分けやすい単色で塗る）で、部品の配置とタイルどうしの接合を確かめる（[ADR 0005](../../docs/adr/0005-ami-render-tool-conventions.md)）。

## 今の決まりごと

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
- 登場年は 1900。路面表示つきの道路だけは、元の道路と同じにする
- 新しい waytype の速さは、pak128 の車両が最高速度で走れる値にする（モノレールの車両は最高 150 km/h、船は 53 km/h）

| 物 | 速さ | 費用 | 維持費 |
|---|---|---|---|
| モノレール 懸垂（`ami_monorail_suspended*`） | 150 km/h | 30000 | 600 |
| 水路の踏切 | 運河の側は 60 km/h。線路・道路の側は、線路×道路の踏切（[#111](https://github.com/128na/simutrans-addon-dev/issues/111)）の作りに合わせる | キー無し | キー無し |
| 道路標識（`ami_sign_<名前>`） | – | 500 cr | キー無し |

- モノレールの費用は、在来線の高架と同じにした。iss の値（50000・1000）だと、高速線（40000・800）より高くなるため
- 運河は在来線より高い。pak128 では、運河の費用は線路の 6〜12 倍ある
- 歩道の壁と電柱は、どちらも water の way-object で、1 タイルに 1 つしか置けない。#120 で、柵つきの電柱（速さ 1010）を足して同じタイルに立てられるようにした（「電柱の作り」）
- 踏切・標識の値のキー（踏切に費用が無いこと、標識の費用が cr 単位で維持費と速さの上限が無いこと）は、[way-addon.md](../../docs/reference/way-addon.md) の 5 章。標識の「速度制限」をどう作るかは #122 で決める

## 残っていること

- 架線（#17）: 柱の位置・高さ、線の高さ（今は pak128 にそろえた）、値（費用・維持費・登場年・速さ）は仮（「架線の作り」）。電化の車両が走れることと、車両と架線の重なりは、ユーザーが手で走らせて見る（スクリプトからは編成を走らせられない）。`center` の架線つきの版が行き止まりの端の壁を持つか（今は持つ）は確定が要る。分岐・十字のタイルに柱を立てない作りでよいかは、絵を見て決める。高架・橋・坑口での架線の見え方は、#18・#19 で画面で見た（つながり。車両との重なりは未確認）
- 壁（#16）: 壁の way-object の値（費用・維持費・登場年）は仮。線路の上を走る編成と壁の重なり（ACCEPTANCE の 2-3）はユーザーの確認待ち。高架・橋への重ね（2-1）は地上・高架・橋で確かめた。道路の壁は #22（下）
- 高架と橋脚（#18）: 高架の行き止まりの端（今は平らな端の面）は仮で、確定が要る（「高架と橋脚の作り」）。橋脚は `tram_track` なので、地上の線路が高架の下を横切るタイルには敷かない（敷くと線路とつながるか、線路が切れる）。躯体と橋脚の寸法、高架と橋脚の値も仮。高さが 2 段なので、`back`・`center`・`front` を並べた幅の広い床や 1 タイルの高架では、橋脚の多くが床に隠れ、手前の列だけが見える（区画 VB・WV1）。高架の上を走る編成と壁・架線の重なり、電化した編成が高架を走れることは、ユーザーが手で走らせて見る
- 橋とトンネル（#19）: 橋の高さ・橋脚の位置（POC の C6）、値は仮で、確定が要る（床の幅は壁の位置で止めると決まった）（「橋とトンネルの作り」）。橋の上・トンネルの中を走る編成と壁・架線の重なり、電化した編成が橋とトンネルを走れることは、ユーザーが手で走らせて見る
- 道路（#21）: 分岐の絵（優先道路の十字・T字の轍・多車線の交差点の絵）は、本体の仕様を整理してから戻す（[#46](https://github.com/128na/simutrans-addon-dev/issues/46)。確かめることもそちら）。画面で横向きになる急坂（東西の 2 段の坂）では、白線（実線・破線とも）が灰色に薄く見える（blender-poc の高速道路と同じ作りで、#21 では直していない）。道路を走る車両との重なりは見ていない
- 道路の壁・高架・橋（#22）: 地上の基盤の版（判断 1）、橋の桁の帯（判断 2）、道路用の橋脚の waytype（判断 3）、`ami_wall_road_twin` の名前は確定した（2026-11-19、ユーザーの決定）。値（「道路の壁・高架・橋脚・橋・トンネルの作り」）は仮。道路を走る車両と壁・高架・橋の重なり（2-3）は、ユーザーが見る。橋を引いて架けたときに橋の上に載る道路は、同じ速さの道路の中から本体が選ぶ（「道路の壁・高架・橋脚・橋・トンネルの作り」）
- 近い斜めの壁は、西の線を `back`、東の線を `front` にした組だけ絵が合う。逆の組（西が `front`）の分け合うタイル用の way-object は作っていない
- 路面軌道（#23）: 値は仮。路面軌道を走る車両との重なりは見ていない
- 歩道（#24）: 見た目（敷石の色・縁石の高さ・雪で敷石も縁石も白くする作り）、値は、ユーザーが見る。色はバリエーションを増やすときにまとめて調整する（2026-11-20、ユーザーの判断）
- 車庫（#112）: 見た目（形・色・入口の大きさ）と、道路の車庫の手前の下の縁に残る道路の端（「車庫の作り」）はユーザーが見る。路面軌道の車庫から出る車両は見ていない。本家 125 での読み込みは見ていない
- 盛土（#123）: 見た目（芝の色・法面の傾き・角の形・斜めに敷いたときの階段）はユーザーが見る。高架の上を走る編成との重なり、本家 125 での読み込みは見ていない
- 歩道の種類・高架の歩道・歩道の柵（#119）: 見た目（舗装の色、柵の形・高さ・色）、舗装の 3 つの選び方、柵の名前、行き止まりに柵を立てない作りは、ユーザーが PR で確かめる。レイアウト検証用モードでは見ていない（形は `ami_sidewalk`・道路の高架と同じ部品で、通常の絵をゲームで見た）。箱積みのパーツとの並び、歩道の上を歩く歩行者との重なりは見ていない
- 運河（#114）: 見た目（水面の色、護岸と笠石の幅、雪の絵）はユーザーが PR で確かめる。本家 125 での読み込みは見ていない。運河と歩道は突き当てるとつながり、船が歩道を通る（上の「運河の作り」）
- 跨座式モノレール（#113）: 見た目（桁の幅・高さ、柱の位置と太さ、雪の絵）はユーザーが PR で確かめる。高架の上を走る編成と、本家 125 での読み込みは見ていない。分岐の絵は本体が `monorail_track` で自動では選ばない
- 操車場（#115）: 見た目（通路の形・色・柵の高さ・階段）はユーザーが PR で見る。高架の上に建てたときの浮いた通路（[#159](https://github.com/128na/simutrans-addon-dev/issues/159)）、建設費のずれ（[#160](https://github.com/128na/simutrans-addon-dev/issues/160)）、本家 125 での読み込みは見ていない
- 電柱（#120）: 見た目（柱の高さ・色、腕木と電線の本数・太さ、柱の位置）と、版の違う電柱の境で電線がずれることはユーザーが PR で確かめる。歩行者・車両との重なり、本家 125 での読み込みは見ていない
- 中央分離帯（#118）: 見た目（縁石の帯とガードレールの形・色・細さ）と、4 車線の輪の北東の角で分離帯が途切れることは、ユーザーが見る。道路を走る車両との重なり、本家 125 での読み込みは見ていない
- 踏切（#111）: 見た目（踏板の色、遮断機・警報機の形と位置）はユーザーが見る。値は仮（#110）。列車・車と遮断機の重なりは、閉じた絵を撮ったときの列車でだけ見た（車は見ていない）。本家 125 での読み込みは見ていない
- ベータの既知の課題と、後に回した issue は [ACCEPTANCE.md の「ベータ版（第 1 弾）での扱い」](ACCEPTANCE.md#ベータ版第-1-弾での扱い)
- できたと言う条件は [ACCEPTANCE.md](ACCEPTANCE.md)
