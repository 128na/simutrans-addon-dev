# 調査/作業ログ: 箱積み（箱積み駅舎）の寸法と作りを調べる（#140）

（2026-11-21）

## 目的 / 発端

ユーザーから、景観パーツと車庫を作るうえで重要な概念として「箱積み駅舎」を深掘りしてまとめるよう依頼があった（[#140](https://github.com/128na/simutrans-addon-dev/issues/140)）。車庫（#112）と景観パーツ（#118〜#123）を、既存の箱積みパーツと組み合わせて使える大きさに収めたい。決まりは [hakozumi.md](../reference/hakozumi.md) にまとめた。

## やったこと

- ウェブで「箱積」「箱積み駅舎」を検索し、次を読んだ。
  - Simutrans 解説 Wiki「箱積み駅舎の使い方」（由来・積み方・Tips）
  - Calc．のシムトラ紀行「箱積み駅舎の使い方」（見た目の工夫）
  - Simutrans 的な実験室 Wiki の addon/pak128/building2（くるり氏の箱積み駅舎128 の公開と終了）
  - Simutrans Addon Portal のタグ「箱積み駅舎」の一覧（23 件）と、ハーフハイト箱積み駅舎＋ひさし・箱積み駅舎128(斜め対応)・箱積みになんでもヒサシをつけるセットの記事
- Portal の記事は本文がスクリプトで読み込まれるので、取得の道具では読めず、アプリの中のブラウザで読んだ。
- 手元の `../refs/` で「箱積」を検索したが、何も無かった。運河属性を流用する例として、iss の歩道（`../refs/iss/src/util/sidewalk/elevated.dat`）を見た。
- GitHub のコード検索で、M_Kasumi「箱積み拡張アクセサリーセット」のソース（kasu-me/Simutrans-Pak128-Hako-Accessory）を見つけた。
  - dat（箱・天井運河・ひさし・way-object）を API で読んだ。
  - 画像（`glass.png`・`tenjo.png`・`frame2.png` など）を作業用のフォルダに取り、セルごとの不透明な範囲を Blender の numpy で測った。
  - リポジトリにライセンスの指定は無い（README に改造・再配布可とある）。画像と dat はこのリポジトリに入れていない。
- 本体（`../simutrans`）で、高さの単位（`simconst.h`・`settings.cc`・`simmain.cc`）、高架の高さ（`wegbauer.cc`）、建物の高さ制限（`building_desc.cc`・`wegbauer.cc`）、makeobj のオフセットの扱い（`image_writer.cc`）を読んだ。

## 分かったこと（事実）

- 箱は `obj=building`・`type=stop`・`waytype=water`・`dims=1,1,2` で、配置ごとに BackImage が 1 枚ある。オフセットは無い。
- 箱の画像は 128px セルの x0〜127・y32〜127 を埋める。形は、地面の菱形を 32px 上に伸ばした六角形。
- pak128 は高さ 1 マスが 16px で、高架は既定で 2 マス（32px）上になる。箱 1 段の 32px は高架 1 段と同じなので、高架の運河の上に建てた 2 段目の箱が 1 段目にちょうど乗る。
- OTRP の建物の高さ制限（#696、v62_4_1）について。
  - 絵の高さは `floor((64 − 上端の y) / 16)` 段と数える。
  - 絵の高さが高架より高い建物の上には、高架を引けない。
  - 車庫も同じ判定を受ける。
- 箱の寸法は、作業中の車庫の作業者が待っていた。そのため、PR の前に進捗管理へ 2 回に分けて送った（寸法と作り、高さ制限と 256px セルへの読み替え）。

## 推測・未確認事項

- wa 氏・くるり氏の元のアドオンは配布が終わっていて、測っていない。寸法は派生の 1 つ（`Hako128_glass`）で測った。
- 次は確かめていない。
  - pak128.Japan の `tile_height`・`height_conversion_factor`
  - pak64 の箱の寸法
- 次はゲームで確かめていない。
  - 線路の車庫の上に高架の運河を引けるか
  - AMI の物を既存の箱と並べたときの見え方

## 結果どうしたか

- [docs/reference/hakozumi.md](../reference/hakozumi.md) を作り、`tools/docs-policy.json` の `livingDocs` に足した（理由は ADR 0001）。
- 車庫と景観パーツの決まりは、その 4 章に分けて書いた。
