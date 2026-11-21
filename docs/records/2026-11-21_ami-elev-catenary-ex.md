# 作業ログ: 高架に架線つきの壁を重ねた分岐の追加画像の確認（#85）

（2026-11-21）

## 目的 / 発端

#82 で、高架の版の way の ex 画像（Y字分岐・三方分岐）は地上の版と同じに選ばれると確かめた。架線つきの壁（way-object）を高架に重ねたときの見た目は、way-object の絵の番号がスクリプトで読めないので対象に入らず、`docs/reference/way-addon.md` の 9.4 に「確かめていない」と残っていた（[#85](https://github.com/128na/simutrans-addon-dev/issues/85)）。高架の 4 版に架線つきの壁を重ね、架線が下の way と同じ経路に張られるかを画面で確かめる。

## 分かったこと（事実）

### 敷いた組と環境

- 環境: `OTRPv64_3.exe`、addon_check の `flat_512.sve` をゲームの写し（`addons/ami/work/study_game/47300/`）で開き、MCP のポートは 47300。pak はこのブランチの `build.py` で作った `dist/ami.pak`
- 見本: `addons/ami/ingame/ex_sample.nut` の `WAYS` を次の 8 組に替えた写しを、`ingame/curve_switch_study.sh` の `NUT` に渡して流した（`ex_check.sh` は検証用のフォルダに書き込むので使わなかった）
  - 区画 0〜3: 在来線の基盤の 4 版（`ami_rail_ballast_base_single`・`_back`・`_center`・`_front`）
  - 区画 4〜7: 高架の 4 版（`ami_rail_ballast_elev_single`・`_back`・`_center`・`_front`）
  - どれにも同じ版の架線つきの壁（`ami_wall_rail_<版>_catenary`）を重ねた。区画の原点は (150, 20+40×区画)、雪の写しは x+256
- `ex_sample.nut` は、way-object を地面の座標（z=0）で敷いていた。高架の way は 2 段上に乗るので、way-object を way の乗る高さ（`lay` の `z`。高架は `ELEV_UP`）で敷くように直した。地上の版は z=0 のままで変わらない
- 敷いた後に、高架の分岐の根元のタイルを `get_tile_at_height(2)` で読み、架線つきの壁がその高さにあり、向き（7・15・14 など）が way と同じだと確かめた

### way の ex の番号

- `[check]` の行は 16 本（8 組 × 温暖・降雪）とも ok。Y字分岐・三方分岐の 4 向きで、自動で選ばれた絵が固定の道具の T字の枠の絵と同じだった（架線つきの壁を重ねても、#82 と同じ）

### 画面の比べ方と結果

- 8 組を、Y字分岐・三方分岐の根元の 4 向き、温暖・降雪で撮った（`ingame/ex_capture.sh`、`BLOCKS="0 1 2 3 4 5 6 7"`、等倍 `gui.set_zoom(3)`。128 枚）
- 高架の絵は、同じ場所へ飛んで撮った地上の絵より 2 段（pak128 の等倍で 32px）上に出る。高架の組（区画 4〜7）の画面を 32px ずらし、同じ版の地上の組（区画 0〜3）と比べた（`tools/blender/shift_diff.py`。このブランチで足した）
  - 物の画素は、何も無い所で撮った背景（平らな草・雪は、どこへ飛んでも同じ位置に同じ模様が出る）と違う画素。差は、片方だけに物がある画素と、両方に物があって色が違う画素
  - 地面に立つ名札のような、高架と一緒に動かない物は数えない
- 64 組（4 版 × 8 形 × 温暖・降雪）の差の画素の数
  - single: 12〜408
  - front: 113〜734
  - back・center: 1420〜7282
- 差を赤にした画像では、差は次の 3 つだけだった（例: `addons/ami/docs/ex85_diff_back_YE.png`、back の Y字の東向き）
  - 高架の床の側面（高架の躯体は地上の基盤より厚い。床の広い back・center で多い）
  - 雪の床の細かい点（雪の模様）
  - 画面の端に入った隣の区画の物
- 分岐のタイルの架線・壁・レールには差が無かった
- 比べ方が差を拾えることの対照
  - 地上の single と高架の back を比べると 20902
  - 地上の Y字の東向きと三方分岐の東向き（同じ版）を比べると 7467
- 地上の版の架線は、way の ex と同じ経路に張られている（#67、[記録](2026-11-21_ami-rail-switch-ex.md)）。高架の架線は地上と同じ絵なので、下の way と同じ経路に張られる

### 画像

`addons/ami/docs/` に置いた。

- `ex85_temperate_Y.png`・`ex85_temperate_3W.png`・`ex85_snow_Y.png`・`ex85_snow_3W.png`
  - 列は左から、地上の single、高架の single・back・center・front
  - 行は上から、東・南・西・北向きの根元
  - 画面の x 10〜570・y 160〜510 を切り出した。地上の列は、高架の列より絵が 32px 下に出る
- `ex85_diff_back_YE.png`: 高架の back と地上の back の差（赤）

## 推測・未確認事項

- 確かめたのは在来線の基盤・高架の版と、その架線つきの壁だけ
  - ラダー軌道の高架、架線の無い壁、道路の高架は並べていない
  - way-object の選び方は線路の種類によらない（`obj/wayobj.cc`）ので、同じ結果になる見込み
- [#101](https://github.com/128na/simutrans-addon-dev/issues/101)（架線つきの壁の T字・十字の柱と梁の直し）の後の絵では見ていない。地上と高架には同じ架線つきの壁（way-object）を重ねるので、この比べ方の結論（高架は地上と同じ絵）は変わらない見込み
- 見た目がよいかの判断はユーザーに残す（PR の画像）

## 結果どうしたか

- `ingame/ex_sample.nut` で、way-object を way の乗る高さで敷くように直した
- `tools/blender/shift_diff.py` を足した（`tools/README.md` に載せた）
- `docs/reference/way-addon.md` の 9.4 の「確かめていない」を、この結果に替えた
- 遊ぶ人向けの `release/readme.txt` の既知の課題から #85 の行を外し、`ACCEPTANCE.md` の後に回した課題から #85 を外した
- 絵・dat は変えていない
