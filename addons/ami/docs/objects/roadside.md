# AMI の歩道・景観・中央分離帯の作り

歩道・盛土・道路標識・横断歩道の標識・歩道の柵・電柱・中央分離帯の作り。全体の案内は [AMI の README](../../README.md)。文中の `ingame/…`・`blender/…`・`docs/…` などのパスは `addons/ami/` から数える。

## 歩道の作り（#24）

- 絵は自分のつながり（隣の歩道とつながる辺）だけで決まる。タイル全面を歩道の高さ（`SIDEWALK_H`、約 2px）の板にし、上に敷石を敷く。つながらない辺では敷石を縁石の上面の幅（`CURB_W`）だけ内へ下げ、縁石の上面の帯と立ち上がりを見せる。隣が道路なら、道路との境の縁石になる。立ち上がりが見えるのは手前の辺（南・東）だけで、奥の辺（北・西）は上面の帯で縁石に見せる。部品の寸法と縁石の材質は blender-poc の一般道の歩道（`road_parts` の `curb`・`paving`）と同じ。敷石は灰色の敷石と暗い目地（精細化。[「道路の作り」](road.md)）。描くのは `tools/blender/sheetlib/sidewalk.py` の `sidewalk_sheet`
- 絵の位置と持ち分は道路と同じ（`ROAD_CY`。オフセット `-64,-32`）。持ち分は、奥の辺の縁石の上面の帯が切れないよう、地面の菱形を上へ `SIDEWALK_RISE`（3 行）広げた
- セルは直線・行き止まり・1 タイル・カーブ・T字・十字・坂・急坂（夏と雪）。斜めの絵・近い斜めの絵・分岐の絵は持たない。本体は斜めの絵の無い way にカーブの絵を使う（`../simutrans` の `boden/wege/weg.cc` の `calc_image`。斜めの絵は `has_diagonal_image()` のときだけ選ぶ）
- 雪の絵は、AMI の道路の雪と同じく敷石も縁石もまだらの雪の材質（`blender/render.py` の `ROAD_SNOW`）
- 道路を斜めに敷くと、道路のタイルのうち斜めの絵が覆わない角の三角に草が見える（`docs/sidewalk_GE_D.png`）。三角は道路のタイルの持ち分なので、歩道の絵では埋めない
- waytype（2026-11-20、ゲームで確かめた。iss の歩道の pak `iss_util_sidewalk.pak` にある `water` の `iss_wwg_sidewalk*` と `road` の `iss_wrg_sidewalk*` も並べて見た）:
  - `water`（採用。iss と同じ。2026-11-20、ユーザーの決定）: 道路の隣に敷いても、道路の向き・絵は変わらない。平地・坂・急坂に敷ける。歩道の列を道路が横切ると、そのタイルは歩道と道路の 2 本の way になり、pak128 の運河の踏切（跳ね橋）が立つ（`docs/sidewalk_GE_X.png`）。pak128 の運河（`canal_020`）を横切らせると、そのタイルは運河に置き換わり、隣の歩道とつながる。歩道は交差点のタイルを空けて敷く（見本の区画 R）
  - `road`（iss の `iss_wrg_sidewalk*`）: 横切る道路が歩道のタイルを置き換え、歩道と道路が 1 本の道路としてつながった（`[check]` の向きが 15）ので、使わない
- 値（仮）: 費用 1000・維持費 20・登場 1900、速さ 1（`blender/ami_dat.py` の `SIDEWALK_VALUES`）

## 盛土の作り（#123）

高架の脇の地面に敷く、法面（のりめん）の way。形と範囲は、2026-11-21 に進捗管理が推奨案で決めた（[#123 のコメント](https://github.com/128na/simutrans-addon-dev/issues/123)。見た目はユーザーが PR で確かめる）。手本は iss の法面（`../refs/iss/src/util/embankment`、`../refs/iss/docs/technique/index.md` の「法面」）。

- 作り: 1 タイルの全面を楔（くさび）にした芝の法面。高い辺は高架と同じ 2 段（pak128 で 32px。箱積みの箱 1 段と同じ）、反対の辺は地面。平地と 1 段の坂の絵の上端は 128px 座標の y32 で、[hakozumi.md](../../../../docs/reference/hakozumi.md) の 4 章の上限（y32 より上に出さない）に収まる。2 段の坂の front（北・西が上がる坂）だけは、坂の高さの分だけ上端が 1px 上に出る（256px のセルで行 31）描くのは `tools/blender/sheetlib/sheetlib.py` の `embankment_sheet`、設定は `blender/render.py` の `EMBANKMENT_GRASS`・`EMBANKMENT_SNOW`
- 版: 高い側の向きで 2 つ
  - `ami_embankment_front`: 法面が手前（南・東）を向く。高い側は北・西。盛り上げたい所（高架の列など）の南・東の辺に敷く
  - `ami_embankment_back`: 法面が奥（北・西）を向く。高い側は南・東。盛り上げたい所の北・西の辺に敷く
- 形（iss と同じ考え方）:
  - 直線・行き止まり: 直線の楔。行き止まりの端は三角の面で閉じる
  - 曲がり: 台の角。外の角（2 つの楔の高い辺が会う角だけが高い）と内の角（低い角だけが地面）を、斜めの稜線で折れる面にした（iss の法面の八角形の角と同じ）。front は北西が外の角・南東が内の角、back は南東が外の角・北西が内の角
  - 北東・南西の角は front と back が会う角で、盛り上げた台の角（外の角）にも窪みの角（内の角）にもなる。front は外の角、back は内の角を描く。台の角には front を、窪みの角には back を後から敷く（同じ速さの way は後から敷いた方が残る。[way-addon.md](../../../../docs/reference/way-addon.md) の 5 章）
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

## 盛土の建物の版の作り（#372）

盛土の way と同じ楔を、地面に建てる建物にした物。手本は iss の `../refs/iss/src/util/embankment/building*.dat`。決めた理由は [ADR 0018](../../../../docs/adr/0018-ami-scenic-aids.md)。

- 物: `ami_embankment_building`（直線。4 向き）と `ami_embankment_building_corner`（台の外の角。4 向き）。どちらも `type=cur`・`dims=1,1,4`・`passengers=0`・`chance=0`・`noconstruction=1`・`needs_ground=1`・費用 1000・登場 1900。`ami_scenery.pak`
- 向き（layout）: 直線は 0 南・1 東・2 北・3 西を法面が向く。角は 0 北西・1 南西・2 南東・3 北東の角が高い。順は、地図を右へ回すと `(layout + 3) % 4` になる本体の回し方に合わせた
- 絵: 盛土の way と同じ形の式と芝・雪の材質（`sheetlib/embankment_building.py`）。雪は 2 つ目の季節の絵。way との違いは、隣とつながらないので側面をどの辺にも持つこと。持ち分は way と同じ（地面の菱形を上へ広げた列）で、箱積みの箱には収めない（`check_depot.py` は `type=cur` を見ない）
- 建て方: 建物の道具（名所の一覧）で選び、向きを回して建てる（本体の `gui/curiosity_edit.cc` は名所をアイコンの有無によらず並べる。コードの読み。一覧の窓から選んで建てることは未確認で、確かめたのはスクリプトの `tool_build_house` だけ）。直線を 4 辺に、外の角を 4 隅に置くと、中心が空いた盛土の輪になる。見本は `ingame/scenic_sample.nut` の区画 MB
- 乗客: `passengers=0` なので行き先にならない。名所の一覧には出る

## 説明用の色の way の作り（#372）

ゲームの中の図解に使う、1 色の帯の way。手本は iss の `../refs/iss/src/util/describe/`。

- 物（8 本）: `ami_describe_<色>`（`tram_track`・地上）と `ami_describe_<色>_elev`（`track`・`system_type=1`）。色は赤・青・緑・黄で、値は iss の画像の色（`blender/catalog.py` の `DESCRIBE_COLORS`）。速さ 1・費用 1・維持費 1・登場 1900。`ami_scenery.pak`
- 絵: タイルの辺の約 1/4 の幅の帯。陰影を付けず、指定の色がそのまま画面に出る材質（黒の下地と発光）で描く（`sheetlib/describe.py`）。直線・行き止まり（端に横棒）・1 タイル・曲がり（中心で折れる）・斜め・T字・十字・坂。近い斜め・分岐の絵は持たない。雪の絵は夏と同じ。地上と高架は同じシート `ami_describe_<色>` を使い、高架のアイコン・カーソルは (0,4)・(1,4) のセル
- 見本: `ingame/scenic_sample.nut` の区画 DG（地上）・DE（高架）

## 道路標識の作り（#122）

道路に置く roadsign の 6 種。数と効き目は、2026-11-21 にユーザーが案 A で決めた（[#122 のコメント](https://github.com/128na/simutrans-addon-dev/issues/122#issuecomment-7060773248)）。本体の roadsign は最高速度を変えられない（dat に速さの上限のキーが無い。[way-addon.md](../../../../docs/reference/way-addon.md) の 5 章）ので、最高速度の標識は飾りにし、効き目のある最低速度の標識を別に置く。形は日本の標識。

| 名前 | 標識 | 効き目（dat のキー） |
|---|---|---|
| `ami_sign_one_way` | 一方通行（326 の B。青い縦の板に白い矢印） | 一方通行（`single_way=1`）。同じタイルにもう一度置くと向きが逆になる |
| `ami_sign_stop` | 一時停止（330。赤い逆三角） | 無し（飾り） |
| `ami_sign_speed_40`・`_60`・`_80` | 最高速度（323。白い円に赤い輪と青い数字） | 無し（飾り。名前の訳に「飾り」「decoration only」と書く） |
| `ami_sign_min_50` | 最低速度（323 の 2。青い円に白い数字と下線） | 最低速度 50 km/h（`min_speed=50`）。それより遅い車は通れない |

- 絵の置き方は本体が決める（`obj/roadsign.cc` の `calc_image`）。絵は 4 枚（`image[0]`〜`[3]` が北・南・西・東の向きの車に向けた標識）で、その向きの車から見て右の側の、タイルの角の近くに描く（右側通行の絵。左側通行の設定では本体が `offset_left`（既定 14px）だけずらし、奥と手前の描き分けも入れ替える）。両方向の標識は 2 枚が出て、画面に表が見えるのは北行き（右の角）と西行き（上の角）、裏が見えるのは南行き（左の角）と東行き（下の角）。位置は pak128 の標識（`pak128/infrastructure/road_signs/p128_sign_road_misc.png`）にそろえた
- 一方通行の向き（#200、2026-11-23）: 本体が置いた向き n の絵（`image[n]`）は、反対の向きの車を通す（北向きの標識は南行き）。柱の角・奥と手前の描き分け・左側通行のずらしは slot n で決まるので、dat の `image[n]` の入れ替えでは左側通行で柱が道路の外へ出る（最初の案で出た）。このため一方通行のシート（`roadsign.py` の `roadsign_sheet`）は、柱を slot n のまま（向き n の車の右の角）に立て、板だけ反対の向きの車に向けて描く（表と裏が入れ替わる。slot 0・2 は裏、1・3 は表が見える）。dat は変えない。アイコンとカーソルは表が見える `image[1]` から作る（`icons.py`）。直す前は、1 回置いた南北の道路で、北向きの車に向けた板が出て、通れるのは南行きだった。ほかの標識は向きで通す車が変わらないので変えていない（6 種を描き直して、一方通行の 1 枚だけが変わることを確かめた）。車で確かめた（`ingame/oneway_dir_check.nut`、OTRPv64_3・`flat_512_left.sve`。直す前後で同じ結果）: 南北に 1 回置くと南行きの車だけが走り、北行きは車庫から出なかった。2 回置くと北行きだけが走った。東西に 1 回置くと西行きだけ、2 回置くと東行きだけが走った（`masked` は順に 4・1・8・2）。撮った画面（拡大率 3）: `docs/roadsign200_before_ns.png`・`roadsign200_before_ew.png`（直す前）、`roadsign200_after_ns.png`・`roadsign200_after_ew.png`（直した後。左側通行。同じ位置で、柱の位置は変わらず板の向きだけが変わる）、`roadsign200_after_ew_right.png`（直した後の右側通行 `flat_512.sve`）。道路は (20,24) から南北 (22,24)・(26,24)・(30,24)・(34,24) と東西 (20,38)・(20,42)・(20,46)・(20,50)。
- 柱は Blender で描き（光と影を道路とそろえる）、板は画面の点に 2D の絵を押す（`tools/blender/sheetlib/roadsign.py` の `roadsign_sheet`）。板は画面で 11px（一時停止は幅 13・一方通行は幅 7）で、数字・矢印は 1px 単位の絵。Blender の面に貼った模様では数字がつぶれた。裏は表と同じ形の灰色の板。板は道路の進行方向に向ける（表がその向きの車に正対する。2026-11-22、ユーザーの指定）。画面では、南北の道路の板が右へ 2px ごとに 1px 下がり、東西の道路の板が右へ 2px ごとに 1px 上がる。絵の列を 1 列ずつ縦にずらして押すので（せん断）、列の数は減らず数字の画素は残る。裏が見える板（南行き・東行き）では、柱の画素を板で消さない
- 高さ: 柱の足元から板の上端まで 30px（128px 座標。上の角の絵で y68 から y38）。高架の高さ（pak128 で 32px。[hakozumi.md](../../../../docs/reference/hakozumi.md) の 4 章）より低い。pak128 の `Minimum80` は 33px
- 雪の絵は無い（roadsign は季節の絵を持たない）。降雪の地面でも同じ絵（`docs/roadsign122_snow.png`）
- アイコンは道路の色に、標識の板を画素のまま 2 倍にした絵だけ（字も札も無い。板の模様で見分ける）。北行きの絵から作るので、板はゲームの中と同じく斜め。カーソルは北行きの絵（`blender/icons.py`）
- 名前の訳: 道具の説明に出る名前を日本語・英語にする訳のファイル `release/text/ja_ami.tab`・`en_ami.tab`（AMI の全部の物。#396）。配る zip の `pak128/text/` に入り、ゲームの `addons/pak128/text/` から読まれる（本体はファイル名の先頭 2 文字で言語を決める。[way-addon.md](../../../../docs/reference/way-addon.md) の 5 章）。「飾り」などの注記は、dat に説明のキーが無いので、訳のファイルにだけ書いた。英語の表示の確かめは [`../en396_names.png`](../en396_names.png)（2026-11-27、OTRP v64、`-lang en`。ポート 47500 の写しで情報の窓を撮った。全 287 件は `translate` が `en_ami.tab` と一致）
- 値: 費用 500 cr、登場 1900（#110 の一覧。`blender/ami_dat.py` の `ROADSIGN_*`）。維持費のキーは無い。`ami_scenery.pak` に入る（ADR 0008）
- 見本: `ingame/roadsign_sample.nut`。6 種を南北・東西の一般道路に置き、一方通行を 1 回・2 回置いて向きを変える。温暖側 (20,24) と降雪側 (276,24)。`[check]` の行で、置いた標識の名前、一方通行か、道の向き（`dirs`）と標識で絞った向き（`masked`）を期待と比べ（飾りの標識は絞らない、一方通行は南北で 4・2 回で 1、東西で 8・2 回で 2）、訳（`translate`）を出す。最低速度は script から読めないので、情報の窓の「最低速度: 50」で見た（`docs/roadsign122_info_min50.png`）
- 左側通行: 左側通行の地図で見た（2026-11-22）。検証用の `flat_512.sve` は右側通行なので、起動した写しのゲームで、`gui.open_dialog_tool(27)`（高度な設定の窓）を開き、`gui.click` で `drive_left` の箱を押して窓を閉じ（`settings.get_drive_on_left()` が `true`）、見本を流した。標識は道路の反対の側の角へずれる（南北の道路では表の見える北行きの板が西の側、東西の道路では西行きの板が南の側）。撮った画面は `docs/roadsign122_left_temperate.png`（拡大率 4）、`roadsign122_left_ns.png`・`roadsign122_left_ew.png`（拡大率 1）、`roadsign122_left_oneway.png`（区画 O、拡大率 3）。車両を走らせての奥・手前の重なりは見ていない
- 撮った画面: `docs/roadsign122_temperate.png`・`roadsign122_snow.png`（拡大率 4。上の 4 本が南北の道路の標識 0〜3、左下に東西の道路の標識の一部）、`roadsign122_temperate_oneway.png`・`roadsign122_snow_oneway.png`（区画 O）、`roadsign122_plates_x4.png`（6 種の表・裏・アイコンを 4 倍）

## 路面の横断歩道の標識の作り（#162）

交差点でない所（直線の道路）の横断歩道を、道路標識（roadsign）で足す。iss の `iss_sr_crosswalk`・`iss_sr_oneway_crosswalk` と同じ使い方で、柱も板も無く、路面に縞と停止線の白だけを描く。交差点の横断歩道は路面表示（`ami_mark_*`。[「路面表示の作り」](marking.md)）が描く。

| 名前 | 内容 | 効き目 |
|---|---|---|
| `ami_sign_crosswalk` | 縞 6 本と、縞の前後の停止線 | 無し（`single_way=0`）。`image[0]`（南北）・`[2]`（東西）だけ（`[1]`・`[3]` は `-`。iss と同じ） |
| `ami_sign_crosswalk_one_way` | 縞 6 本と、進入側だけの停止線 | 一方通行（`single_way=1`）。同じタイルにもう一度置くと向きが逆になる |

- 物を 2 つに分けた理由: `single_way` は物ごとの設定で、1 マスに標識は 1 つしか置けない。一方通行の道に両方向用を重ねても、一方通行にならない（#162 の相談。ユーザーが案どおりに決めた）。矢印は描かない（ユーザーの指定、2026-11-23）。
- 縞は #187・#189 の腕の横断歩道と同じ寸法（幅 0.5・周期 1.0・長さ 3）で、タイルの中心に 6 本（中心 ±0.5・1.5・2.5）、路側線の内に収める。白の材質も路面表示と同じ（`marking.py` の `_Plan`・`MARKING_LINE`）。
- 停止線は、縞の手前（車の来る側）に、腕の横断歩道と停止線のあきと同じ 0.73 をあけて引く。両方向は、縞の前後に、それぞれの進入側の車線の幅だけを引いて互い違いにする（左側通行。北行きは西の車線、南行きは東の車線。東西も同じ）。一方通行は、進入側に 2 車線分の幅を 1 本引く（ユーザーの指定、2026-11-23）。
- 一方通行の `image[n]` は、本体が置いた標識の向き n の絵で、車が通れるのは反対の向き（1 回目に建てた南北の道路は北向きの標識で、通れる向きは南。`masked=4`。2026-11-23、見本で撮って確かめた）。このため `image[0]` は南行き（北側に停止線）、`[1]` は北行き、`[2]` は東行き、`[3]` は西行きの絵（`sheetlib/roadsign.py` の `CROSSWALK_ONE_WAY_DIRS`）。
- `offset_left=0`（左右対称の絵なので、左側通行でずらさない。iss と同じ）。費用 500 cr、登場 1900。`ami_scenery.pak` に入る。名前の訳は `release/text/ja_ami.tab`・`en_ami.tab`。
- 雪の絵は無い（roadsign は季節の絵を持たない）。降雪でも同じ白で、道路の上に敷くので縞は読める（`docs/crosswalk162_snow.png`）。坂では絵が浮く（iss も同じ）。車両との重なり: `offset_left=0` の標識は、向きによって車両の上（北・東の絵）か下（西・南の絵）に描かれる（本体のコード `calc_image` を読んだ。[cityscape.md](../../../../docs/reference/cityscape.md) の 6.1）。縞が車両を覆わないよう、dat に `no_foreground=1`（すべて奥 = 車両の下に描く。OTRP）を書いた。車両を走らせての見え方は見ていない。
- アイコンは、縞と停止線の全体を道路の色に縮めた絵（`blender/icons.py` の `crosswalk_picture`）。カーソルは北行きの絵のセル。
- 停止線の位置（撮った画像で確かめた。左側通行）: 両方向の南北は南端の西側と北端の東側、東西は西端の北側と東端の南側。一方通行は、通れる向きの進入側（南行きは北端、北行きは南端、西行きは東端、東行きは西端）。
- 見本: `ingame/crosswalk_sign_sample.nut`。両方向（南北・東西）と一方通行（1 回・2 回置いた南北・東西）を一般道路に置く。左側通行の `flat_512_left.sve` の温暖側 (20,24)・降雪側 (276,24)。`[check]` の行で、名前・一方通行か・`masked` を期待と比べる。撮った画面は `docs/crosswalk162_temperate.png`・`crosswalk162_snow.png`（拡大率 3）と、等倍の `crosswalk162_temperate_x1.png`・`crosswalk162_snow_x1.png`。
- ゲーム内の見た目（縞と停止線の位置、車の止まる側とのずれ）はユーザーが PR で確かめる。車を走らせての重なりは見ていない。

## 歩道の種類・高架の歩道・歩道の柵の作り（#119）

- 歩道の種類（`ami_sidewalk_<舗装>`）: 形・セル・持ち分・雪の絵は `ami_sidewalk`（上の「歩道の作り」）と同じで、敷石の材質だけが違う。舗装は 3 つ（2026-11-21、作業者が決めた。ユーザーが PR で確かめる）。敷石が画面で約 6 x 3px なので、目地の模様（やはず張りなど）ではなく、色と材質で見分ける（`docs/sidewalk119_P_temperate.png`）。材質は `blender/render.py` の `SIDEWALK_PAVINGS`
  - `asphalt`: アスファルト舗装。道路の路面より明るい灰色のまだら
  - `brick`: 赤れんが色のインターロッキングブロック
  - `tile`: ベージュの平板。敷石が大きい
- 高架の歩道（`ami_sidewalk_elev`。dat は `system_type=1`）: 敷石は `ami_sidewalk` と同じ。板の下に、道路の高架と同じ深さの基盤と躯体を足した（材質も道路の高架と同じ）。躯体はつながらない辺で内へ下げる。柱は描かず、真下の地面に道路用の橋脚（`ami_pier_road`）を敷く。躯体の下面の深さが道路の高架と同じなので、橋脚の上端が合う（`docs/sidewalk119_E_temperate.png`）。描くのは `tools/blender/sheetlib/sidewalk.py` の `sidewalk_sheet(elevated=True)`
  - 高架の道路の隣のタイルに並べて敷け、地上の道路の上を横切って敷ける（2026-11-21、ゲームで確かめた。`ingame/sidewalk_struct.nut` の区画 E1・E2）。床の下の縁は、隣の高架の道路とそろう
  - 運河（`water`）の高架の way なので、箱積みの箱の上面と同じ高さに乗る（[hakozumi.md](../../../../docs/reference/hakozumi.md) の 4.2）。箱積みのパーツと並べて見てはいない
- 歩道の柵（`ami_wall_sidewalk_<版>`）: 歩道に重ねる way-object（`waytype`・`own_waytype` とも `water`）。地上の歩道（舗装の種類も）と高架の歩道の両方に同じ物を重ねる。柵の足元は敷石の上面
  - 柵は経路ではなく、歩道の板の縁（隣の歩道とつながらない辺）に沿って立てる。歩道の絵が四角いタイルなので、カーブ・L字の角でも柵はタイルの辺に沿って折れる（`docs/sidewalk119_F_temperate.png`）。坂では坂の面に沿う
  - 版: `single` はつながらない辺の全部、`back` は奥の辺（北・西）だけ、`front` は手前の辺（南・東）だけ。道路の両脇の歩道で道路の側の辺だけに立てるなら、道路の東・南の側の歩道に `back`、西・北の側に `front` を重ねる（区画 F1）。外側の辺に立てるなら逆で、高架の道路の両脇の高架の歩道（区画 E1）では、北の歩道に `back`、南の歩道に `front` を重ねて、道路と反対の辺に立てた
  - 行き止まりの閉じた辺には立てない（横断歩道へ続く口として空ける）。高架の歩道の行き止まりの端も開いたまま（2026-11-21、作業者が決めた。ユーザーが PR で確かめる）
  - 形は白く塗った鋼の横断防止柵（柱・上の横木・中の横木）。柱はタイル 1 辺に 4 本で、タイルの辺の上には置かない。高さは約 1m（画面で約 7px）。寸法の単位は [way-addon.md](../../../../docs/reference/way-addon.md) の 12 章。奥の辺の柵は奥の絵、手前の辺の柵は手前の絵（`frontimage`）に描く。描くのは `sheetlib/sidewalk.py` の `sidewalk_fence_sheet`
  - 斜めの絵の無い way-object なので、斜めにつないだ歩道ではカーブのセルの絵が出る（歩道の way と同じ）
- 値（[#110](https://github.com/128na/simutrans-addon-dev/issues/110) の表から移した。`blender/ami_dat.py` の `SIDEWALK_VALUES`・`SIDEWALK_ELEV_VALUES`・`SIDEWALK_WALL_VALUES`）:

| 物 | 速さ | 費用 | 維持費 | 登場年 |
|---|---|---|---|---|
| 歩道の種類（`ami_sidewalk_<舗装>`） | 1 | 1000 | 20 | 1900 |
| 高架の歩道（`ami_sidewalk_elev`） | 1 | 2000 | 40 | 1900 |
| 歩道の柵（`ami_wall_sidewalk_<版>`） | 1000 | 3000 | 60 | 1900 |

## 電柱の作り（#120）

歩道に立てる電柱と電線の way-object。作りは、2026-11-22 に進捗管理が推奨案で決めた（[#120 のコメント](https://github.com/128na/simutrans-addon-dev/issues/120#issuecomment-7064726322)。見た目はユーザーが PR で確かめる）。手本は iss の電柱（`../refs/iss/src/util/road_misc/pole.dat`。毎タイルに柱、つながる向きに電線）。

- 物: 1 タイルに置ける water の way-object は 1 つだけ（[way-addon.md](../../../../docs/reference/way-addon.md) の 10 章）なので、柵と同じタイルに立てる物は、柵の版に電柱を足した way-object にした（架線つきの壁・中央分離帯つきの壁と同じ考え方）
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

## 中央分離帯の作り（#118）

4 車線（道路を 2 タイル並べた道）の上下線の境に立てる、縁石の帯とガードレール。手前のタイル（東西の道なら南、南北の道なら東）に重ねる壁の way-object で、奥の側壁の位置（2 タイルの境）に立つ（2026-11-21、ユーザーの指定）。手本は iss の中央分離帯（`../refs/iss/src/way-object/road/center_divider_1.dat`・`wall_with_center_divider.dat`。タイルの辺に沿う細いガードレール）。

- 版:
  - `ami_wall_road_front_divider`: 手前の側壁と、奥の側壁の位置の分離帯。壁で囲んだ 4 車線の手前のタイル（基盤の版 `front`）に重ねる。奥のタイルは今までどおり基盤の版 `back` と壁 `ami_wall_road_back`
  - `ami_wall_road_center_divider`: 分離帯だけ（側壁なし。行き止まりの端の壁は `center` と同じく持つ）。壁の無い 4 車線（基盤の版 `center` を 2 本）の手前のタイルや、3 本以上並べた道の中ほどのタイルに重ねる
  - `ami_wall_road_twin_divider`: 近い斜めの分け合うタイル用。西の線（`nw`・`sw`）は `back` の壁、東の線（`ne`・`se`）は `front_divider` の絵。敷き方は `ami_wall_road_twin` と同じ（`back`・`front_divider` を敷いた後に分け合うタイルへ 1 タイルずつ重ね、`back`・`front_divider` を敷き直す）
- 形: 側壁の位置（経路から `EXPWY_WALL_U` の少し内〜側壁の外の面）に低い縁石の帯を置き、帯の中心に両面のガードレール（2 枚の板と支柱）を立てる。寸法は `tools/blender/sheetlib/road_parts.py` の `MEDIAN_*`。側壁と同じく、T字・十字では横切る道の車道の分を削って開け、斜め・坂・高架でも側壁と同じ位置を通る（見本で見た）。1 タイル（どこにもつながらない way）には立てない（十字と同じ経路で作るので、角の切れ端が点で残った）。左右の両側に作り、壁の版を選ぶ処理（`sheetlib.py` の `select_walls`）が奥の側の 1 本だけを残す（奥の絵に描く）。設定は `blender/render.py` の `ROAD_DIVIDER_LABEL` の所、値は `blender/ami_dat.py` の `DIVIDER_VALUES`
- 4 車線の輪（直角の曲がり。見本の区画 R、`docs/divider118_GE_R.png`）: 外の輪は北・西の辺が `back`、南・東の辺が `front`、内の輪は逆にする。角のタイルは南北の辺の版（[「遊ぶ人向けの敷き方」](../../README.md)）。壁は南北の辺を角まで先に敷き、東西の辺を後から敷くが、`front_divider`（1010）は壁 `back`（1000）より速く、角の `back` を置き換えてしまう。東西の辺の `front_divider` は、角が `back` のタイル（外の輪の南西・内の輪の北東）の 1 つ手前で止める。こう敷くと、北西・南東・南西の角では分離帯が角に沿って曲がる。北東の角（内の輪の角が `back`）では、分離帯が角の 1 タイルで途切れる（内の輪の北の辺の分離帯が角の手前で終わり、外の輪の東の辺の分離帯が角の次のタイルから始まる）
- 値: 速さ 1010（`twin_divider` は 1011）、費用 3000、維持費 60、登場 1900（#110 の一覧）。速さが壁（1000）・`twin`（1001）より大きいので、壁の上に Ctrl を押さずに重ねると分離帯つきに置き換わる。逆に、分離帯つきの上に壁を敷いても置き換わらない（外してから敷く。[way-addon.md](../../../../docs/reference/way-addon.md) の 10 章）
- 見本: `ingame/divider_sample.nut`（撮る場所は `ingame/sample_spots.sh` の `DIVIDER_SPOTS`）。幹線道路と高速道路で（一般道路は基盤・高架が `single` だけなので敷かない。#260）、東西の 4 車線と壁の無い道路の十字（P2）、南北の 4 車線の坂（PN）、壁の無い 4 車線（P0）、3 本並べた道（P3）、高架（PE）、4 車線の輪（R）、近い斜め（PD）を温暖側と降雪側に敷く。残った way-object を `[check]` の行で期待と比べる（違えば返り値の先頭が `check`）
- ADR 0008 との違い（2026-11-21、ユーザーの指定による。決めた理由は [ADR 0010](../../../../docs/adr/0010-ami-divider-between-two-road-tiles.md)）: ADR は「分離帯だけの版を道路の `center` に置く」としていたが、分離帯の位置を 1 タイルの中心線でなく 2 タイルの境にしたので、版は `front_divider`・`center_divider`（と `twin_divider`）にした。`single_divider`・`back_divider` は作らない（1 タイルの道の中心線の分離帯は、一般の道路には要らない）
- 後から足せるもの（今は作らない）: 植え込みの分離帯、暫定 2 車線の高速道路用の、1 タイルの中心線に立てる簡易な柵・ワイヤーの分離帯
