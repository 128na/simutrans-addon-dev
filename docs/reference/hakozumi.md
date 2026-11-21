# 箱積み（箱積み駅舎）の知見（寸法・作り・組み合わせる物の決まり）

「箱積み」は、1 タイル・高さ 2 マスの箱の形をした運河属性の停留所の建物を積み重ねて、任意の形の駅舎や建物を表すコミュニティの手法。AMI の車庫と景観パーツを、既存の箱積みパーツと組み合わせて使える大きさに収めるための決まりをまとめる。

- 調べた経緯は [2026-11-21_hakozumi-survey.md](../records/2026-11-21_hakozumi-survey.md) にある。作業の手順は書かない
- 各項目に確かめた場所と日付を書く。推測は「推測」と書く
- 座標は、断りが無ければ pak128 の 128px セルの画面の座標（左上が 0,0。地面の菱形は x0〜127・y64〜127、中心は 64,96）。AMI の 256px セルへの読み替えは 3 章

## 1. 由来と広がり

| 事実 | 確かめた場所（日付） |
|---|---|
| 最初に wa 氏が pak64 で公開した、部品を組んで駅舎を作るアドオン。レゴブロックのようなものと説明されている | [Simutrans 解説 Wiki「箱積み駅舎の使い方」](https://wikiwiki.jp/simucom/Control/Rail/Hakozumi)（最終更新 2017-06-24。2026-11-21 に読んだ） |
| pak128 へは「128な人」がリサイズして移植し、まかさんがリサイズのギザギザを直したレタッチ版を出した | 同上 |
| 久留里 Kuururi Ahojanen 氏の「箱積み駅舎128（HAKO128）」が pak128 の主な土台。2014-07-16 公開、2020-01-19 公開終了 | [Simutrans 的な実験室 Wiki の addon/pak128/building2](https://wikiwiki.jp/twitrans/addon/pak128/building2)（2026-11-21） |
| 派生が多い。Simutrans Addon Portal のタグ「箱積み駅舎」は 23 件（pak64 と pak128・pak128.Japan）。タグの説明は「景観を整える目的の運河・運河港属性の駅舎」 | [Portal のタグ 22](https://www.simutrans-portal.128-bit.net/tags/22)（2026-11-21） |

主な派生（Portal のタグと解説 Wiki から。2026-11-21）:

| 種類 | 例 |
|---|---|
| 色・素材違いの箱 | グレー箱積み駅舎、プレイヤーカラー箱積み駅舎（M_Kasumi）、sazanami-building2（壁の素材の差し替え） |
| 屋根・屋上 | pak128 箱積みガラス丸屋根（tku）、天井運河・屋上の機器（M_Kasumi のアクセサリーセット） |
| ひさし・ベランダ | 箱積みになんでもヒサシをつけるセット（休日自衛隊、CC0）、ハーフハイト箱積み駅舎＋ひさし（Simu_poppo、OTRP 向け） |
| 斜め | 箱積み駅舎128(斜め対応)（Take。くるり氏の箱積み駅舎128 を OTRP の斜めタイル停留所に対応させたもの） |
| 装飾の way-object | 箱積み拡張アクセサリーセット（M_Kasumi。入口・駅名表示・時計・窓・溝・エレベーターなど） |
| 建物の再現 | 箱積み駅舎対応型八乙女駅、本郷ステーションデパート、百貨店・スーパー・ビジネスホテルのセット |
| 周りの物 | 緩急坂対応ペデストリアンデッキ、箱積み道路壁 |

## 2. 作り

### 2.1 箱（建物）

M_Kasumi「箱積み拡張アクセサリーセット」の [src/hako_glass/Hako128_glass.dat](https://github.com/kasu-me/Simutrans-Pak128-Hako-Accessory/blob/main/src/hako_glass/Hako128_glass.dat)（[GitHub kasu-me/Simutrans-Pak128-Hako-Accessory](https://github.com/kasu-me/Simutrans-Pak128-Hako-Accessory)、2026-11-21 に読んだ）の作り:

| キー | 値 | 意味 |
|---|---|---|
| `obj` | `building` | |
| `type` | `stop` | 停留所。way の上にだけ建てられる |
| `waytype` | `water` | 運河の上に建てる。駅名は「○○港」になる（解説 Wiki） |
| `dims` | `1,1,2` | 1×1 タイル。3 つ目は配置（向き）の数で、高さではない |
| `BackImage[配置][0][0][0][0]` | 配置ごとに 1 枚。オフセットは無し | 高さ方向の行は 0 だけ |
| `NoConstruction` | `1` | 建設中の絵を出さない |
| `enables_pax`・`enables_post` | `1` | |
| `Level` | `2` | |

- 同じセットの README に、本体 120.2 以上が要る、Simutrans 122.0.1 と OTRP v29.6 の pak128.Japan で動いた、とある
- wa 氏・くるり氏の元のアドオンは配布が終わっていて、dat と画像を確かめていない（未確認）

### 2.2 寸法（実測）

`Hako128_glass` の画像（`glass.png`、128px セル、768×128）の不透明な画素を測った（2026-11-21）。

| 部分 | 画面の座標 |
|---|---|
| 箱の外形（六角形） | x0〜127・y32〜127。不透明は 8320px（地面の菱形 4096px ＋側面 128×32px に近い） |
| 上面（菱形） | 上の頂点 (63〜64, 32)、左右の角 (0, 63〜64)・(127, 63〜64)、下の頂点 (64, 96) |
| 左右の縦の辺 | x0 と x127 で y63〜96（高さ 32px） |
| 下の頂点 | (64, 127)。地面の菱形と同じ |

つまり、**箱は地面の菱形をそのまま 32px 上へ伸ばした形**。上面は地面の菱形を 32px 上げた位置にある。

### 2.3 高さの単位（本体）

| 事実 | 確かめた場所（2026-11-21） |
|---|---|
| 高さ 1 マスの画素数は `tile_raster_scale_y(TILE_HEIGHT_STEP, セル幅)` = `tile_height × セル幅 / 64`。pak128 は `tile_height = 8` なので 16px | `../simutrans/simconst.h` の `tile_raster_scale_y`、`../refs/pak128/pak128.prototype/config/simuconf.tab` |
| pak128 は `height_conversion_factor = 2`。高架の高さ `way_height_clearance` は、simuconf.tab に書かなければ `height_conversion_factor` と同じになる。pak128 は書いていないので 2 マス（32px） | `../simutrans/simmain.cc`（`set_way_height_clearance( pak_height_conversion_factor )`）、pak128 の simuconf.tab |
| よって pak128 では、**箱 1 段 = 高さ 2 マス = 32px = 高架 1 段**。2 段目の箱は高架の運河の上に建てると、1 段目の上面にちょうど乗る | 上の 2 つから。解説 Wiki の「1 層で 2 階分の高さ」「2 層目以降は運河の高架で 1 層分高く敷く」とも合う |
| pak64 の箱は、同じ計算なら 16px（pak64 の `tile_height` を 8 とした場合） | 推測。pak64 の箱と simuconf は確かめていない |
| pak128.Japan の `tile_height`・`height_conversion_factor` | 未確認。同じ箱の絵が pak128 と pak128.Japan の両方に対応と書かれているので、同じ値と推測 |

### 2.4 積み方と屋上

- 1 段目: 地面に運河を敷き、その上に箱を建てる。2 段目より上: 運河の高架（`system_type=1`）を 1 段上に敷き、その上に箱を建てる（解説 Wiki）
- 屋上は運河の高架の way で表す。例: アクセサリーセットの `mk_tenjo_ungaroad_*`（`waytype=water`・`system_type=1`）の画像は y65〜127 で、地面の菱形の位置に描いてある。高架は本体が 32px 上げて描くので、箱の上面に重なる（[src/way/tenjo.dat](https://github.com/kasu-me/Simutrans-Pak128-Hako-Accessory/blob/main/src/way/tenjo.dat)・`tenjo.png`、2026-11-21 に測った）
- 箱の面の装飾は運河の way-object（`waytype=water`・`own_waytype=water`）で、運河の上の箱に重ねる。装飾の画像の 1 つ `frame2.png`（枠）は y28〜127 にあり、箱の外形とほぼ同じ範囲（[src/wayobj/mk_keikan_wayobj.dat](https://github.com/kasu-me/Simutrans-Pak128-Hako-Accessory/blob/main/src/wayobj/mk_keikan_wayobj.dat)・`frame2.png`、2026-11-21）
- ひさし・ベランダは運河の way（地上用と高架用の 2 つ）で、BackImage と FrontImage に分けて描く（同セットの [src/way/veranda/mk_veranda.dat](https://github.com/kasu-me/Simutrans-Pak128-Hako-Accessory/blob/main/src/way/veranda/mk_veranda.dat)、Portal の「箱積みになんでもヒサシをつけるセット」の dat 一覧。2026-11-21）
- 運河を平行に 4 マス以上まっすぐ敷くと隣と自動でつながるので、Ctrl を押しながら敷く（解説 Wiki）
- 見た目の工夫として、上の段をずらす・色を混ぜすぎない・屋根に半分の高さの部品やドーム・三角・半円を使う、が挙がっている（[Calc．のシムトラ紀行「箱積み駅舎の使い方」](https://calcdanny.hatenablog.com/entry/2018/12/21/151130)、2018-12-21 公開。2026-11-21 に読んだ）

### 2.5 OTRP の機能で広がったこと

| 機能 | 箱積みへの効き方 | 確かめた場所（2026-11-21） |
|---|---|---|
| 高さ 1 の高架（高架のオフセット `-1`） | 16px（半段）上に運河を敷ける。ハーフハイトの箱・ひさしが使う。下に way が無いときだけ | `../otrp-knowledge/docs/spec/way.md`（#281）、Portal の「ハーフハイト箱積み駅舎＋ひさし」（2026-08-13 公開） |
| 速度 0 の way は 1 段上の高架を通せる | 速度 0 のひさしの way の上に、すぐ高架を敷ける | 同じ文書（#689）、同 Portal の説明 |
| 斜めタイル停留所 | 斜めの線に沿った箱 | Portal の「箱積み駅舎128(斜め対応)」 |
| 建物の上空の高さ制限（height clearance） | 絵の低い建物の上に高架の運河、つまり箱を積める。4.1 | `../simutrans/bauer/wegbauer.cc`・`descriptor/building_desc.cc`、`../otrp-knowledge/docs/spec/way.md`（#696、v62_4_1） |

## 3. AMI の 256px セルへの読み替え

makeobj は、画像の切り抜きの上端・左端に dat のオフセットを足して pak に書く（`../simutrans/descriptor/writer/image_writer.cc`、2026-11-21）。よって **128px 座標 = 256px セルの座標 ＋ dat のオフセット**。

| オフセット | 使っている物 | 箱の外形（256px セル） | 地面の菱形の上の頂点 |
|---|---|---|---|
| `-64,-96` | blender-poc の料金所（building）、iss の歩道（`../refs/iss/src/util/sidewalk/elevated.dat`） | x64〜191・y128〜223 | y160 |
| `-64,-32` | AMI の way（[way-addon.md](way-addon.md)） | x64〜191・y64〜159 | y96 |

## 4. AMI が従う寸法の決まり

### 4.1 車庫（#112）

- 建物の絵（`BackImage` の行 0）の上端は、**128px 座標で y32**（地面の菱形の上の頂点から 32px）にそろえる。箱 1 段と同じ高さになり、隣に箱を並べたとき屋根の高さがそろう
- 上端を y17 より上（y16 以下）に出さない。本体は建物の絵の高さを `floor((64 − 上端の y) / 16)` 段と数え（`building_desc_t::get_drawn_height`、上端は切り抜きの上端＋オフセット）、絵の高さが高架の高さより高い建物の上には高架を引けない（`wegbauer.cc`。車庫も `get_depot()` で同じ判定を受ける）。y17〜y32 なら 2 段以下で、2 段目の箱（高架の運河）を車庫の上に積める余地が残る（OTRP v62_4_1 以降）
- 高さに数えるのは `BackImage` だけで、`FrontImage` は数えない（`get_drawn_height` は背景の画像の列だけを見る）。ただし手前の絵も y32 より上に出すと、上に積んだ箱と重なって見える（推測）
- 横は地面の菱形の幅（128px 座標の x0〜127）の中に収める。はみ出すと隣のタイルの箱と重なる（推測）
- 2 段分の高さの車庫にするなら上端は y0（64px）。このときは上に箱を積めない（3 段以上になるため。計算から）
- 未確認: 線路の車庫の上に高架の運河を実際に引けるか、所有者の判定に引っかからないか（ゲームで試していない）

### 4.2 景観パーツ（#118〜#123）

- 高さは 16px（半段）か 32px（1 段）の倍数にする。屋上・デッキ・ひさしなど上に乗る物は、運河の高架（+32px）と高さ 1 の高架（+16px）の位置に合わせる
- 箱積みの屋上やデッキとつなげたい歩道・デッキは、運河（`waytype=water`）の高架の way にすると、箱の上面と同じ高さに乗り、既存の天井運河・ペデストリアンデッキとつながる。iss の歩道も `water` を使っている（[refs-index.md](refs-index.md)）
- 箱の面に重ねる装飾（看板・窓・照明など）は、運河の way-object にし、絵は箱の外形（128px 座標の x0〜127・y32〜127）の中に描く。既存のアクセサリーセットと同じ範囲になる
- 運河の上に置く物は、その運河に建てた箱（停留所）と同じタイルに重なる。way・way-object・建物の描く順と持ち分は [way-addon.md](way-addon.md) の 2 章に従う
- 地面に置く景観パーツ（標識・電柱・盛土など）は、絵の上端を y32 より下に収めると、箱 1 段の高さを超えず、隣の箱と並べても上に飛び出さない（推測。way・way-object の絵の高さを制限する本体の決まりがあるかは確かめていない）

## 5. 未確認のこと

- wa 氏・くるり氏の元のアドオンの dat と画像（配布終了）。2 章の寸法は派生の 1 つ（`Hako128_glass`）で測った
- pak128.Japan の高さの単位
- ゲームでの確かめ（車庫の上の高架の運河、AMI の物と既存の箱の並び）
