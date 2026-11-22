# 作業ログ: AMI の旧描画位置の線路（#26）を作り、SIS との継ぎ目を測る

（2026-11-22）

## 目的 / 発端

[ADR 0008](../adr/0008-ami-scope-second-phase.md) は、線路の描画位置を「新描画位置で作り終えてから、旧描画位置（SIS に合う）をまとめて作る」と決めた。#26 の 1 本目として、線路 4 種の通常の版・基盤 4 版・旧用の壁・架線つきの壁を、旧描画位置で作った。名前・pak・範囲は [ADR 0011](../adr/0011-ami-old-draw-position-separate-pak.md)。

## やったこと

- 手本: blender-poc の旧描画位置（`addons/blender-poc/blender/render.py` の `TRACK_PROFILES["old"]`: `datums=R.FLAT`・`spill=0`）。blender-poc の README の「描画位置の描き分け」（2026-11-12）で SIS と段なくつながると確かめてある
- 試し: 在来線の通常の版だけを旧設定で描いて SIS（`SIS_ST_TGbl_E01-999B`）と東西の直線でつないだところ、旧はレールが段なくつながり、新（今の `ami_rail_ballast`）はレールが数 px 下にずれて見えた。これで、旧は設定を変えるだけで作れると判断した
- 作り: `blender/render.py` の `TRACK_SETTINGS` が、新の設定から旧の設定を導く（`datums=FLAT`・`spill=0`）。基盤・壁・架線は `catalog.OLD_TRACKS` の名前で、新と同じ部品を旧の基準面で描く。行き止まりの道床の止め位置は旧の基準面（動かさない）で計算し直した（`_edge_beds`）
- 壁・架線・橋脚を旧用に分けた理由: 壁は基準面 `bed`（新は 2px 下）に合わせて描かれる。旧の基盤を基準面なしで作ると、共有の壁と足元が 2px 合わない
- pak: 旧の物（30 個）を `dist/ami_rail_old.pak` にまとめる。`ami.pak` と種類別の pak には入れない（`build.py` の `belongs`）

## 測ったこと

2026-11-22、`addon_check` の `OTRPv64_3.exe`、`flat_512.sve` の温暖側。`ingame/seam_slope_check.sh` に `TRACKS_LIST`・`REF=SIS_ST_TGbl_E01-999B`・`PAK=dist/ami_rail_old.pak` を渡した。

- 継ぎ目（`seam_judge.py`）: 旧の 4 種とも、東西の直線 2 か所・南北の直線 2 か所・斜め 1 か所が OK（継ぎ目の草 0px）。坂の継ぎ目（南が低い 1 段の坂、SIS → AMI の側）は在来線・直結が NG（模様のずれ +1.0px・+1.1px。しきい値 1.0px。中心のずれは坂と平地なので参考）、ラダー・スラブは OK
- 坂の十字のレールの寄り（`slope_measure.py`）: 急坂の十字（4 タイル）の合格は、旧が在来線 0・直結 0・ラダー 4・スラブ 2、新が 1・1・2・2。1 段の坂の十字は、旧が 3・3・4・4、新が 1・1・4・4。平地との差が 0.5px を超えるタイルがあるのは新も同じ（旧の在来線・直結の急坂は、新より合格が少ない）
- 新と旧を同じ位置で並べた画像: `addons/ami/docs/old_seam/<種類>.png`（`ingame/old_seam.sh`）。基盤・壁・架線つきの壁の画像: `addons/ami/docs/old_base.png`（`ingame/old_base.sh`）
- 旧の 30 個は、`ami_rail_old.pak` だけを入れた写しで全部が道具で敷けた（`ingame/beta_check.sh`、`PAKS=dist/ami_rail_old.pak`。ログに AMI の警告なし）

## 確かめていないこと

- 雪の側（x=256〜）の継ぎ目・見た目
- 坂の継ぎ目の NG（在来線・直結）の原因。SIS 同士の坂の基準値は測っていない。旧の描き方の問題か、SIS 自身の坂の作りかは分からない
- 旧の基盤・壁・架線の見た目（ゲームで敷いて 1 倍で新と並べただけ。足元の 1〜2px の合い方は見ていない）。旧の架線の高さ（新はレール・基準面の差が違う）
- 本家 125.0.1 での読み込み
- 高架・橋脚・橋・トンネル（2 本目の PR）

## 次に調べること

- 坂の継ぎ目の NG の追跡は #26 のコメントに書く
- `ingame/beta_check.sh` の既定の `PAKS` は、後から足した物（水路・歩道の柵など）に追従しておらず、156 件が NG になる（この作業の前からのもの）
