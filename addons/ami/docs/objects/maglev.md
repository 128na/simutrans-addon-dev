# AMI のリニアの作り

リニア（`maglev_track`）の 3 種（超電導・常電導・チューブ式）と、超電導のガイドの作り。全体の案内は [AMI の README](../../README.md)。文中の `ingame/…`・`blender/…`・`docs/…` などのパスは `addons/ami/` から数える。

## リニアの作り（#371）

- 範囲: 第 6 弾。ADR 0017「狭軌とリニアを範囲に入れる」（#370 で書く）による。pak128 にリニアの車両は無く、車両は別のアドオンに任せる。AMI には車両を入れない
- 手本: iss のリニア（`../refs/iss/src/way/maglev/`・`../refs/iss/src/way-object/maglev/linear_guide.dat`・`../refs/iss/src/tunnel/maglev/`）。合成済みの絵の切り抜きは `docs/maglev371_iss_reference.png`。名前・版・値・断面は、案をユーザーが決めた（2026-11-26、判断 75「おすすめの案で描く」。[#371](https://github.com/128na/simutrans-addon-dev/issues/371) のコメント）
- 名前: 形で付けた。iss の「transrapid」は商品名、「marine」は作品名なので使わない

| 種類 | 地上 | 高架（`system_type=1`） | そのほか |
|---|---|---|---|
| 超電導 | `ami_maglev_guideway_<版>`（`single`・`back`・`center`・`front`） | `ami_maglev_guideway_elev_<版>`（同じ 4 版） | ガイド `ami_maglev_guide`、トンネル `ami_maglev_guideway_tunnel`（中の way は `center` の版） |
| 常電導 | `ami_maglev_beam` | `ami_maglev_beam_elev_<版>`（`front`・`center`・`back`） | トンネル `ami_maglev_beam_tunnel`（中の way は地上の way） |
| チューブ式 | `ami_maglev_tube` | `ami_maglev_tube_elev_<版>`（`front`・`center`・`back`） | トンネル `ami_maglev_tube_tunnel`（中の way は地上の way） |

- 車庫 `ami_maglev_depot`（[「車庫の作り」](depot.md)。入口は線路と同じ幅）。橋と留置線は作らない（iss にも橋は無い。高架で渡る）
- 値: 1200 km/h（iss と同じ）。費用・維持費は地上 60000・1200（高速線の 1.5 倍）、高架はその 2 倍、トンネルは 4 倍。ガイドは 4000・100（架線と同じ）で、`topspeed` 1300（電化した編成の速さを縛るので way より大きい）。車庫は 850000・1800（モノレールと同じ）。登場 1900。値は `blender/ami_dat.py` の `MAGLEV_VALUES`・`MAGLEV_GUIDE_VALUES`
- pak は `ami_maglev.pak`（`build.py` の `KINDS`。ガイドと車庫も入る）
- 部品: `tools/blender/sheetlib/maglev_parts.py`。寸法は iss の配布物の東西のセルを縦に走査し、上面と側面の色の境目で測った。常電導・チューブ式の桁の幅とチューブの径は、測った値ではゲームで細すぎたので、AMI のシートを手本の切り抜きと同じ倍率で並べて合わせ直した（タイルの 1 辺は 10 単位）
- アイコン: 背景は紅（`blender/icons.py` の `WAY_BG` の `maglev`。色相 349）。版のある物は右下に版の札、高架は下の帯

### 超電導

- 床: 線路の基盤の版と同じ基準面・基盤・版（`single` は両側、`back`・`front` は片側、`center` は壁なし）。基盤の上に床の板と、車両の走る溝の暗い帯を置く
- 防音壁: iss と同じく way の絵に描く（線路のように壁の way-object に分けない）。way-object は waytype ごとに 1 タイルに 1 つで、ガイドと重ねられないため。壁の位置は線路の側壁と同じで、高さだけ iss に合わせて 1.9（線路の側壁は 1.2）。手前の側の壁は手前の絵（`frontimage`）に描く
- ガイド `ami_maglev_guide`: U 字の側壁（厚さ 0.3、床からの高さ 0.4、壁の中心の間 1.56）と、内側の面のコイル。`own_waytype=electrified_track` で電化を兼ねる（iss の `linear_guide` と同じ）。並びはモノレールの電化と同じ（奥の絵 4 行 → 手前の絵 4 行。雪の絵は無い）。手前の側の側壁は手前の絵、奥の側は奥の絵。画面で手前と奥の決まらない向きは、両側とも奥の絵
- 高架: 基盤の版と同じ絵の下に、線路の高架と同じ躯体を足す。下の地面には線路の橋脚の way（`ami_pier_rail`）を敷く
- カーブ: 線路の基盤の版と同じく、カーブのセルを斜めの形で描く。近い斜めの絵・分岐の追加画像は無い

### 常電導とチューブ式

- 並び: 跨座式モノレールと同じ（地上 1 つ・高架の 3 版・トンネル。カーブは斜めの絵。近い斜めの絵は無い）。高架の柱と腕は跨座式と同じ並びで、`monorail_parts.monorail_pier_fills` に桁の下面の高さを渡して作る
- 常電導の桁: T 字（上の板の幅 1.2、上面は way の高さから 0.4）。高架の版は腹を下へ深くする（上面から 1.6。跨座式と同じ深さ）
- チューブ式の桁: 上面に溝のある桁（幅 1.2、上面 0.45）
- チューブ: 高架の版だけ（iss と同じ）。径 5.6（中心は way の高さから 2.3。桁の上面より上だけを描く）。iss のチューブは半透明のガラスだが、AMI のシートは 2 値（透明か不透明）なので、輪（2.5 おき）と縦の線の骨組みで描く。手前の側の半分は手前の絵
- 雪の絵: 桁の上面だけを白くする（跨座式と同じ）

### 見本と確かめたこと

- 見本は `ingame/maglev.sh`（`ingame/maglev.nut`）。ゲームの写し（`work/maglev_game/<PORT>/`）を起動し、3 種の地上（車庫と輪・十字・斜め・行き止まり。超電導はガイドを重ねる）、超電導の複線（地上と高架）、トンネル 3 本、高架（超電導の 4 版は真下に橋脚の way、常電導・チューブ式の 3 版）を敷き、車両を輪で走らせる。AMI には車両が無いので、試しの車両の pak を `EXTRA_PAKS` で写しの中にだけ入れる。`SNOW=1` で降雪側、`CAPTURE=1` で撮る。使い方はスクリプトの冒頭
- 2026-11-27 に OTRP（v64）で確かめた: 全部の物が敷けた。ガイドを重ねたタイルは電化され（`[check]` の行の `elec`）、電化の要る試しの車両が超電導の輪を、要らない車両が常電導・チューブ式の輪を回った。試しの車両（色の箱の絵の dat を makeobj した pak。コミットしない）は写しの中にだけ入れ、検証の後に写しと一緒に消した
- 確認画像は `docs/maglev371_*.png`（`iss_reference` は手本の切り抜き）。`guideway`（超電導の地上の輪と十字。ガイドつき）・`guideway_run`（電化の要る試しの車両が走るところ）・`guideway_pair`・`guideway_pair_elev`（複線の地上と高架）・`guideway_elev`（高架の single の東西）・`beam_run`（常電導の地上と試しの車両）・`beam_elev`・`tube_elev`（高架の front の版）・`tunnel`（3 種のトンネル）・`snow_guideway`・`snow_tube_elev`（降雪側）
- `monorail_parts.monorail_pier_fills` に引数を足した前後で、跨座式の高架 3 版のシートが 128（コミット済みの絵）・256（変更前に描いた控え）ともバイトで同じ
- 256 は全部の物を描き、`SHEET_PAK_SIZE=256` のアイコン・空のセルの検査と 256 の pak の組み立てを通した（256 の PNG はコミットしない）
