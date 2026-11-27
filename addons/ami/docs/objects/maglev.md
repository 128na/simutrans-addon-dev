# AMI のリニアの作り

リニア（`maglev_track`）の 3 種（超電導・常電導・チューブ式）と、超電導のガイド・チューブ式のチューブの作り。全体の案内は [AMI の README](../../README.md)。文中の `ingame/…`・`blender/…`・`docs/…` などのパスは `addons/ami/` から数える。

## リニアの作り（#371）

- 範囲: 第 6 弾。[ADR 0017](../../../../docs/adr/0017-ami-scope-narrow-gauge-and-linear.md)（狭軌とリニアを範囲に入れる）による。pak128 にリニアの車両は無く、車両は別のアドオンに任せる。AMI には車両を入れない
- 手本: 超電導・常電導は iss のリニア（`../refs/iss/src/way/maglev/`・`../refs/iss/src/way-object/maglev/linear_guide.dat`・`../refs/iss/src/tunnel/maglev/`。合成済みの絵の切り抜きは `docs/maglev371_iss_reference.png`）。チューブ式は marine_express（`../refs/marine_express_1.1/marine_express/`。ユーザーのアドオン、WTFPL）。名前・版・値・断面は、案をユーザーが決めた（2026-11-26、判断 75「おすすめの案で描く」。[#371](https://github.com/128na/simutrans-addon-dev/issues/371) のコメント）。チューブ式は、その後のユーザーの指示（2026-11-27「チューブ式リニアのアドオンはこれを参考に」）で、iss の溝の桁から marine_express の作りに替えた
- 名前: 形で付けた。iss の「transrapid」は商品名、「marine」は作品名なので使わない

| 種類 | 地上 | 高架（`system_type=1`） | そのほか |
|---|---|---|---|
| 超電導 | `ami_maglev_guideway_<版>`（`single`・`back`・`center`・`front`） | `ami_maglev_guideway_elev_<版>`（同じ 4 版） | ガイド `ami_maglev_guide`、トンネル `ami_maglev_guideway_tunnel`（中の way は `center` の版） |
| 常電導 | `ami_maglev_beam` | `ami_maglev_beam_elev_<版>`（`front`・`center`・`back`） | トンネル `ami_maglev_beam_tunnel`（中の way は地上の way） |
| チューブ式 | `ami_maglev_tube_<版>`（`single`・`back`・`center`・`front`） | `ami_maglev_tube_elev_<版>`（同じ 4 版） | チューブ `ami_maglev_tube_cover`、トンネル `ami_maglev_tube_tunnel`（中の way は `center` の版） |

- 車庫 `ami_maglev_depot`（[「車庫の作り」](depot.md)。入口は線路と同じ幅）。橋と留置線は作らない（iss にも橋は無い。高架で渡る）。marine_express の開削トンネルとトンネル専用の way も作らない
- 値: 1200 km/h（iss と同じ）。費用・維持費は地上 60000・1200（高速線の 1.5 倍）、高架はその 2 倍、トンネルは 4 倍。ガイドは 4000・100（架線と同じ）で、`topspeed` 1300（電化した編成の速さを縛るので way より大きい）。チューブは 240000・4800（marine_express のチューブと軌道の費用の比（約 4 倍）に合わせて、維持費も地上の way の 4 倍）で、`topspeed` 1300。車庫は 850000・1800（モノレールと同じ）。登場 1900。値は `blender/ami_dat.py` の `MAGLEV_VALUES`・`MAGLEV_GUIDE_VALUES`・`MAGLEV_TUBE_COVER_VALUES`
- pak は `ami_maglev.pak`（`build.py` の `KINDS`。ガイド・チューブと車庫も入る）
- 部品: `tools/blender/sheetlib/maglev_parts.py`。寸法は iss の配布物の東西のセルを縦に走査し、上面と側面の色の境目で測った。常電導の桁の幅とチューブの径は、測った値ではゲームで細すぎたので、AMI のシートを手本の絵と同じ倍率で並べて合わせ直した（タイルの 1 辺は 10 単位）
- アイコン: 背景は紅（`blender/icons.py` の `WAY_BG` の `maglev`。色相 349）。版のある物は右下に版の札、高架は下の帯

### 超電導

- 床: 線路の基盤の版と同じ基準面・基盤・版（`single` は両側、`back`・`front` は片側、`center` は壁なし）。基盤の上に床の板と、車両の走る溝の暗い帯を置く
- 防音壁: iss と同じく way の絵に描く（線路のように壁の way-object に分けない）。way-object は waytype ごとに 1 タイルに 1 つで、ガイドと重ねられないため。壁の位置は線路の側壁と同じで、高さだけ iss に合わせて 1.9（線路の側壁は 1.2）。手前の側の壁は手前の絵（`frontimage`）に描く
- ガイド `ami_maglev_guide`: U 字の側壁（厚さ 0.3、床からの高さ 0.4、壁の中心の間 1.56）と、内側の面のコイル。`own_waytype=electrified_track` で電化を兼ねる（iss の `linear_guide` と同じ）。並びはモノレールの電化と同じ（奥の絵 4 行 → 手前の絵 4 行。雪の絵は無い）。手前の側の側壁は手前の絵、奥の側は奥の絵。画面で手前と奥の決まらない向きは、両側とも奥の絵
- 高架: 基盤の版と同じ絵の下に、線路の高架と同じ躯体を足す。下の地面には線路の橋脚の way（`ami_pier_rail`）を敷く
- カーブ: 線路の基盤の版と同じく、カーブのセルを斜めの形で描く。近い斜めの絵・分岐の追加画像は無い
- 雪の絵: 床と溝を雪にする（防音壁と高架の躯体は夏と同じ）。ガイドに雪の絵は無い

### 常電導

- 並び: 跨座式モノレールと同じ（地上 1 つ・高架の 3 版・トンネル。カーブは斜めの絵。近い斜めの絵は無い）。高架の柱と腕は跨座式と同じ並びで、`monorail_parts.monorail_pier_fills` に桁の下面の高さを渡して作る
- 桁: T 字（上の板の幅 1.2、上面は way の高さから 0.4）。高架の版は腹を下へ深くする（上面から 1.6。跨座式と同じ深さ）
- 雪の絵: 桁の上面だけを白くする（跨座式と同じ）

### チューブ式

- 軌道: marine_express と同じく、広い床と中央の溝 1 本。版・基盤・高架の躯体と真下の橋脚の way は超電導と同じで、側壁は線路の側壁と同じ高さ（1.2）で way の絵に描く（手前の側は手前の絵）
- チューブ `ami_maglev_tube_cover`: marine_express の `marine_express_tube` と同じく、軌道に重ねる way-object（`waytype`・`own_waytype` とも `maglev_track`。電化しない。marine_express の車両は水素で走る）。地上・高架のどちらにも重ねられる。way-object は waytype ごとに 1 タイルに 1 つなので、ガイドと同じタイルには重ねられず、チューブのタイルは電化されない（電化の要る車両はチューブ式を走れない）。径 6.4（中心は床の上面から 1.2。側壁を包む。床の上面より上だけを描く）。手本のチューブは透ける輪だが、AMI のシートは 2 値（透明か不透明）なので、輪（2.5 おき）と縦の線の骨組みで描く。並びはガイドと同じで、手前の側の半分は手前の絵
- 雪の絵: 床と溝を雪にする（側壁とチューブは夏と同じ）

### 見本と確かめたこと

- 見本は `ingame/maglev.sh`（`ingame/maglev.nut`）。ゲームの写し（`work/maglev_game/<PORT>/`）を起動し、3 種の地上（車庫と輪・十字・斜め・行き止まり。超電導はガイド、チューブ式はチューブを重ねる）、複線（超電導の地上と高架、チューブ式の地上）と center の版の直線、トンネル 3 本、高架（超電導・チューブ式の 4 版は真下に橋脚の way、常電導の 3 版）を敷き、車両を輪で走らせる。AMI には車両が無いので、別のアドオンの車両の pak を `EXTRA_PAKS` で写しの中にだけ入れる。`SNOW=1` で降雪側、`CAPTURE=1` で撮る。使い方はスクリプトの冒頭
- カタログ（`ingame/catalog.py`）でも同じ見本を流す（y=520・x=110。約 152×58 マスなので 2 区画ぶん。y=480 の列は踏切の見本と重なる。#392）。カタログでは車両が無いので、`[v]` の行で知らせるだけにする
- 2026-11-27 に OTRP（v64）で確かめた: 全部の物が敷けた。ガイドを重ねたタイルは電化され（`[check]` の行の `elec`）、チューブを重ねたタイルは電化されない。marine_express の 3 両編成（`MarineExpress_Msc1`・`Ms1`・`Msc2`。電化は要らない）が、常電導とチューブ式の輪を温暖・降雪の両方で回り、チューブの中に見えた（手前の輪が車両の上に出る）。超電導の輪は、電化の要る試しの車両（色の箱の絵の dat を makeobj した pak）で回した。どちらの pak もコミットせず、写しの中にだけ入れ、検証の後に写しと一緒に消した
- カタログの地図（`flat_1024_left.sve`）でも、温暖側と降雪側の maglev の区画が失敗なく敷けた（2026-11-27）
- 確認画像は `docs/maglev371_*.png`（`iss_reference` は手本の切り抜き）。`guideway`（超電導の地上の輪と十字。ガイドつき）・`guideway_run`（電化の要る試しの車両が走るところ）・`guideway_pair`・`guideway_pair_elev`（複線の地上と高架）・`guideway_elev`（高架の single の東西）・`beam_run`（常電導の地上と車両）・`beam_elev`・`tube`（チューブ式の地上の輪と十字。チューブつき）・`tube_run`（marine_express の車両がチューブの中を走るところ）・`tube_elev`（高架の single）・`tube_elev_curve`（高架のカーブ）・`tunnel`（3 種のトンネル）・`snow_guideway`・`snow_tube`（降雪側）
- `monorail_parts.monorail_pier_fills` に引数を足した前後で、跨座式の高架 3 版のシートが 128（コミット済みの絵）・256（変更前に描いた控え）ともバイトで同じ
- 256 は全部の物を描き、`SHEET_PAK_SIZE=256` のアイコン・空のセルの検査と 256 の pak の組み立てを通した（256 の PNG はコミットしない）
