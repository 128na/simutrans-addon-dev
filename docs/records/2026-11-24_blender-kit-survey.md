# 調査/作業ログ: simutrans-blender-kit を今後の開発で活用できるか（#206）

（2026-11-24）

## 目的 / 発端

外部の Blender アドオン [Dkijas/simutrans-blender-kit](https://github.com/Dkijas/simutrans-blender-kit)（MIT。以下 kit）を、`tools/blender/sheetlib`・`addons/ami/` の今の作りと項目ごとに比べ、置き換え・取り込み・部分的な借用ができるかを調べた（[#206](https://github.com/128na/simutrans-addon-dev/issues/206)）。結果は第 4 弾の作り方の判断に使う。

調べた写しは `refs/simutrans-blender-kit`（コミット `0bc64b7`、`0.10.1`）。写しと `refs/` には書き込んでいない。動かした物は、写しの `core/`・`tools/`・`tests/` を作業用の一時の場所へ写して実行した。ゲームの検証環境・MCP のポートは使っていない。

## 先に結論

- **置き換えは不可、取り込みもしない。** kit の way・橋・トンネル・架線は「平らな 6 つの部品を回して 16 通りの絵を作る」までで、AMI が要る物（持ち分・基盤・壁・高架・雪・分岐の絵・ex 画像・路面表示・盛土・運河）を持たない。camera の決まり・特殊色・坂の高さは、すでに kit と同じ値を `sheetlib` が持っている。
- **借りる価値があるのは「検査」と「文書の中の本体の根拠」。** 次の 4 つを別 issue の案にする（下の「全体の案」）。
  1. 特殊色の近似（1 ずらした色）の検査と、色の位置の報告。
  2. kit の `.dat` linter の考え方（本体のソースからキー表を作る）の突き合わせ。今の `dat_linter` との差分の洗い出し。
  3. 本体（OTRP）を headless でビルドして、pak が読み込めるかだけを見る検査（ゲームを起動する `addon_check` より軽い）。
  4. `sheetlib` の `BLENDER_EEVEE_NEXT` の固定を、kit のように使える識別子を選ぶ形にする（Blender 5.x に上げるときの備え）。
- 上流は小さく若い（2 か月前から更新なし、星 2、貢献者 1 人）。取り込んで追従する前提にしない。「読んで考え方を借りる」扱いにする。

## やったこと

- `README.md`・`LICENSING.md`・`CHANGELOG.md`・`BLENDER_KIT_EVOLUTION_PLAN.md` を読み、`core/ways.py`・`bridges.py`・`tunnels.py`・`colors.py`・`paksets.py`・`sheet.py`・`schema.py`、`addon/rig.py` の描画の設定、`tools/lint_dat.py`・`toolchain.py`・`run_tests.py`、`tests/scenarios/pak/bkitroad/scenario.nut` を読んだ。
- 今の作り方は `tools/blender/sheetlib/core.py`（カメラ・特殊色・設定）、`addons/ami/build.py`・`check.sh`、`docs/reference/way-addon.md`（5・6・9 章）、`tools/README.md` と比べた。
- 動かして確かめたこと（いずれも一時の場所で、Python は `-I`）:
  - kit の linter（`tools/lint_dat.py`）で AMI の `addons/ami/src` の dat 234 本を検査 → エラー 0・警告 0（キー 644 個・本体 124.5.1 の書き手から作った表）。
  - 検査が効くかを、dat の写しに足した行で確かめた。存在しないキーと、値の後ろの `# 注記` は検出する（`unknown-key`・`value-comment`）。`image[zz]` と `image[nse3]`（ribi の綴りの誤り）は検出しない。
  - 写しの純 Python のテスト（`test_colorcheck`・`test_package`・`test_spritemetrics`）は通った。`test_core` は `addon/`（bpy を使う部分）を一時の場所に写さなかったので 1 件が import エラーになり、`test_templates` は import で止まった（どちらも確かめていないことに数える）。
  - kit 側の特殊色の表と、`sheetlib` の `SPECIAL` を並べた（下の表）。
- 上流の活発さは GitHub の API で見た（2026-11-24 時点）。

## 分かったこと（事実）

### 上流の活発さとライセンス

| 項目 | 内容 |
|---|---|
| 作者 | 1 人（`victor_18993`。LICENSE の著作権者）。fork 0・star 2・open issue 0 |
| 期間 | 作成 2026-07-15、最後の push 2026-09-23（調べた時点で約 2 か月更新なし）。コミット 81 本。リリース v0.3〜v0.10.0 は 2026-07-15〜07-17 の 3 日間。`CHANGELOG.md` の先頭は 0.10.1（2026-07-25） |
| テスト | `tests/` に純 Python のテストと、Blender・makeobj・headless の Simutrans を通す統合の試験（`tools/run_tests.py`）。CI は GitHub Actions の `tests.yml` |
| 目標 | 新しい絵描き向け。pak64・pak128 が対象で、OTRP・pak128 の分岐の絵や AMI のような構造物は目標に無い |
| ライセンス | コード（`core/`・`addon/`・`tools/`・`tests/`・`examples/`）は MIT。`LICENSING.md` は、`core/` と `tools/` が `bpy` を使わないので GPL との関係は問われない、と説明している（作者の読みで、判決ではないと自分で書いている） |
| 素材 | `assets/` の車両の 3D モデルは CC BY 4.0（モデルの作者名は LICENSE の著作権者と同じ `victor_18993`。鉄道会社の商標は別）。**これは取り込まない**（AMI は道路・線路が対象で要らない） |

帰属の書き方: コードを取り込むなら、MIT の著作権表示と許諾の文を、取り込んだファイルの先頭か `THIRD_PARTY_LICENSES.md` に残す（MIT の条件）。素材には触れない。今回は取り込まない案なので、実際の書き方は取り込むときの issue で決める。

### way・橋・トンネル・架線の絵の作り

| こと | 今の作り方（AMI・`sheetlib`） | kit | 判断と理由 |
|---|---|---|---|
| 16 通りの絵 | 経路ごとに部品を組み、持ち分（どの画素がそのタイルか）を決めて描く（`way-addon.md` 2 章、`assemble.py`） | 6 つの部品（none・end・straight・curve・tee・cross）を 4 方向に回して 16 通り（`core/ways.py` の `PIECES`・`orbit`） | **使わない。** 回すだけでは、手前/奥の描き分け・基盤・壁・継ぎ目の持ち分を扱えない。ribi の回転の表は読んだだけで、AMI の向きの決まりとは突き合わせていない |
| 坂 | `imageup[3/6/9/12]` と `imageup2`。pak128 は 1 段 16px で、2 段が既定（`way-addon.md` 5 章） | `imageup[n/w/e/s]` を 4 つそろえるか 0 にする検査と、pak128 の `height_conversion_factor` 2 のとき `imageup2` 無しを警告する（`ways.py` の `slope_image_block`・`double_slope_advisory`） | **一部借りる（考え方のみ）。** 「4 つそろえる」検査は、AMI の検査で見ているか調べていない（dat は `ami_dat.py` の生成物で、今の dat は kit の linter を通った）。警告は AMI が `imageup2` を必ず作るので不要 |
| 斜め・手前の絵 | `diagonal`・`frontimage`・`frontdiagonal`・雪（`[1]`）まで持つ | `diagonal[ne/se/nw/sw]` はあるが、手前の絵は架線（way-object）だけ。雪の絵・季節は橋・トンネルも「1 季節のみ」と書いてある（`bridges.py`・`tunnels.py` の docstring） | **使わない。** 雪・手前の絵が AMI には必須 |
| 橋 | 端の坂・坂から始まる端・橋脚・雪の行を持ち、1・2 段の `Start2`・`Ramp2` も扱う（`way-addon.md` 5 章、AMI の橋） | `image`・`start`・`ramp`・`pillar` の 4 組を back/front に（`bridges.py`）。2 段（`image2` など）は「extras」として出さない。向きの回転は「類推で導いた。置いて確かめる」と書いてある（`GROUP_TURNS`） | **使わない。** AMI は本体のソースとゲームで確かめた表を持つ（5 章）。kit の回転の表は「置いて確かめる」段階 |
| トンネル | 坑口の覆い・躯体・壁と架線を通して敷く（`way-addon.md` 6 章、`tunnel_sheet`） | 狭い坑口 4 方向を back/front（`tunnels.py`）。`PORTAL_TURNS` は本体の `slope_indices` から導き、ゲームで置いて確かめる、とある | **使わない。** 同上 |
| 架線 | 柱・梁・吊り金具・トロリ線・ちょう架線・ハンガーを部品で作り、近い斜めまで持つ（`catenary_parts.py`） | 同じ ribi の back/front の 2 層（`ways.py` の `wayobj_dat`）。数値の spelling（`frontimageup[3/6/9/12]`）の指摘は正しい | **使わない。** kit は絵の作りを持たない（dat の枠だけ）。「前/後に分ける」という考えは AMI にもある |
| アイコン | `icon=>`・`cursor` を 1 セル目に持つ | 「アイコンが無いと way は作れない」（`wegbauer.cc:123`）を lint とテンプレートに入れている | 借りる必要なし（AMI は全部持つ）。AMI の `check_icons.py` が見ている |
| 持ち分・つなぎ目・手前/奥 | `near_camera`・`near_frame`・`seam_judge`・`way-calibration` | 該当なし | — |
| 分岐の絵（switch 1・2）・ex 画像 | `image[nse1]`〜`image[nsew2]` を書き、ex 画像（26〜35 番）は pak への継ぎ足し（`ex_graft.py`、`way-addon.md` 9 章） | `RIBI_CODES` に `nse1`〜`nsew2` のキー名はあるが、作る物は無い。OTRP への言及なし（`grep` で `otrp` の該当なし） | **対応できない。** OTRP 固有の絵（分岐の役割・ex）は kit に無い |
| 独自の部品 | 運河・歩道・路面表示・盛土・車庫・標識・モノレール・踏切 | 標識・信号（`roadsigns.py`）はある。ほかは無い | 標識だけ重なるが、AMI の標識は一方通行の向きなどの本体の癖（`way-addon.md`、#200）を持つので使わない |

### 描画・特殊色・pakset の設定

| こと | 今の作り方 | kit | 判断と理由 |
|---|---|---|---|
| カメラ | 平行投影・`rotation_euler=(60°,0,45°)`・`view_transform="Standard"`（`sheetlib/core.py`） | 平行投影・仰角 30° 相当（Blender の `rot_x=60°`）・`Standard`・ディザ 0（`addon/rig.py`、`core/projection.py`） | **同じ。** 借りるものは無い。kit は投影を本体の `get_screen_coord()` と 1e-9 まで突き合わせるテストを持つ（`tests/test_core.py`）。AMI は継ぎ目の実測で合わせている |
| 縁の混ぜ（`filter_size`） | `1.0` | `0.0`（くっきり） | 違う。AMI は縁の画素を `ALPHA_THRESHOLD` で切る後処理を持つ。取り換える理由は見つけていない |
| 特殊色 | 31 色（プレーヤー 16 + 夜の光 15）。意図しない命中は 1 ずらして消す（`sheetlib/cells.py`、`tools/blender/special.py`） | 同じ 31 色（`core/colors.py`）。取り違えやすい紫（描くのは `FF017F`、ゲームが見せるのは `E100E1`）を本体の 2 つの表から区別している | **色の表は一致を確認済み**（kit の 31 色を出して `SPECIAL` と並べ、同じ値）。借りるのは検査の側（下） |
| 特殊色の検査 | 完全一致の数を種類・セルで数える（`special.py`）。1 ずらしの後処理 | 位置の報告と、**近似**（窓が 1 違いで光らない、など）の検出（`core/colorcheck.py`）。同じセルに完全一致があれば近似は出さない | **一部借りる。** 近似の検査は AMI に無い。AMI の今の物（道路・線路・運河など）が窓・灯の特殊色を意図して使っているかは調べていない。効く場面は第 4 弾の内容しだい |
| 色の書き出し | 発光で塗るか、後処理で整える | 特殊色は発光（shadeless）・sRGB→線形の補正で書く | 違う手段で同じ結果を目指している。取り換え不要 |
| pakset の寸法 | 高さ 1 段 16px（`H = 16 / ...`）。pak128 の絵を 256px セルに描き、dat に `-64,-32` のオフセット（`build.py` の `PAKSET = "pak256"`） | `Pakset(tile_px, height_step, height_conversion_factor)`。pak128 は `height_step 8`・係数 2 で 1 段 16px、2 段が既定。pak192・pak256 は未測定。way・橋・トンネルの dat に画像のオフセットを書かない（`core/ways.py`・`bridges.py`・`tunnels.py`） | **値は一致、作りは違う。** 1 段 16px・2 段の既定は kit の測定と合っている。ただし AMI のセル（256px + オフセット）は kit の前提（セル = タイルの幅）と違い、kit のプロファイルでは表せない |

### `.dat` の検査

| こと | 今の作り方 | kit | 判断と理由 |
|---|---|---|---|
| dat の検査 | `dat_linter`（128na/simutrans-dat-linter、`ci.env` の `v0.3.1`、`--tile-size 256`）を CI で回す。生成した dat と `src/` の差も見る（`check.sh`） | `tools/lint_dat.py`。キー表を本体の書き手（`descriptor/writer`）から機械的に作る（`tools/extract_dat_schema.py`、644 キー）。コード付きの指摘（`no-icon`・`value-comment` など）と、`# bkit: ignore=…` | **併用はできるが急がない。** AMI の 234 本は、kit の linter でもエラー 0・警告 0（実行して確認）。足せる検査は `value-comment`（値の後ろの注記）と `unknown-key` だが、今の `dat_linter` が持つか未確認。差分を調べる価値はある（案 2） |
| 本体との整合 | dat と本体のソースの照合は文書で行う | キー表が本体のソースと食い違っていないかをテスト（`tests/test_schema_drift.py`）で見る | 考え方は借りられる。ただしこれは 124.5.1（本家）の表で、OTRP のキー（分岐の絵の `nse1`〜は通る。ex の 26〜35 番は dat に無い）は表に無い |

### makeobj・読み込み・headless

| こと | 今の作り方 | kit | 判断と理由 |
|---|---|---|---|
| makeobj のビルドと配置 | `build.py`（種類別の pak、WARNING/ERROR で止まる）。makeobj の版は `ci.env` で固定（`upstream:125.0`。OTRP の fork の makeobj は近い斜めのキーを知らない） | `core/package.py`・`toolchain.find_makeobj`。パネルから pak を作り `addons/` へ置く | **使わない。** AMI は種類別 pak・ex 画像の継ぎ足し（`ex_graft.py`）・makeobj の版の固定を持つ |
| 読み込みの試験 | `addon_check` のゲーム（OTRP）に、スクリプト（`.nut`）で見本を敷き、スクリーンショットと `[check]` の行で確かめる（`ingame/`） | headless の Simutrans（`-DSIMUTRANS_BACKEND=none` でビルド）に `-scenario` で `.nut` を読ませ、画面無しで「読み込めた・道が敷けた・ribi が期待どおり」を見る（`tests/scenarios/pak/bkitroad/scenario.nut`、`run_tests.py`） | **一部借りる。** 我々の fork（`simutrans/`）の `CMakeLists.txt` にも `SIMUTRANS_BACKEND` の `none` があるので、同じ形の「画面無しで pak が読めるか」の軽い検査は作れる見込み。**ビルドと実行は今回していない**（案 3。見た目・つなぎ目はゲームを起動する `addon_check` のままで、置き換えにはならない） |
| 本体の向きの確認 | ribi と north/east の対応を本体に問い合わせるシナリオ（上のファイル） | — | 考え方は参考になる。AMI は `[check]` の行で同じことをしている |

### 品質の検査（kit の Quality Gate）

kit の `BLENDER_KIT_EVOLUTION_PLAN.md` は、シート 1 枚を方向ごとに測る検査（8 方向の整合・車両の連結）を扱う。AMI は道路・線路で、方向の数と主題が違う。`core/qualitygate.py`・`tools/quality_gate.py` 系は取り込まない。

## 全体の案（採る物と段）

- **取り込まない。置き換えない。** 土台（`sheetlib`・`ami_dat.py`・`build.py`・`check.sh`）は変えない。理由: kit に無い物が AMI の中心（持ち分・基盤・壁・高架・雪・分岐・ex・路面表示・盛土・運河）で、kit の取り込みは AMI の作りを狭めるだけ。上流が小さく、追従の負担が大きい。
- **借りるのは次の 4 つ。** どれも小さく、第 4 弾の作業と並行にできる。起票案は、進捗管理への報告の `next` に書いた。
  1. 段 低: `sheetlib` の `BLENDER_EEVEE_NEXT` の固定を、使える識別子を選ぶ形にする。
  2. 段 低: kit の linter と `dat_linter` の差分を調べる（`value-comment`・`unknown-key`・「坂の絵は 4 つそろえる」）。
  3. 段 中: 特殊色の近似の検査を `special.py` に足すか判断する（窓・灯を使う物を作るときに）。
  4. 段 中: headless の本体で pak が読めるかだけを見る軽い検査を作れるか調べる。

## 確かめていないこと

- kit の Blender の部分（`addon/`・`tests/blender_*.py`）は動かしていない（Blender 5.x が対象で、手元は 4.5。パネルの操作は AMI で使わない）。
- headless の Simutrans のビルドと、kit の `scenario.nut` の実行はしていない。
- `test_core.py`・`test_templates.py` は最後まで動かしていない（`addon/` を一時の場所に写さなかったため）。
- 今の `dat_linter`（128na/simutrans-dat-linter）との差分は、実際に両方で同じ dat を検査して比べていない。
- 「Blender 5.x で `BLENDER_EEVEE_NEXT` の識別子が変わる」ことは、kit のコードのコメントによる（Blender 5.x では動かしていない）。
- kit の主張（本体のソースの行番号など）は、`../simutrans` と突き合わせていない。
