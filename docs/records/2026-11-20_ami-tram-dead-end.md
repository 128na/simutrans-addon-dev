# 作業ログ: AMI の路面軌道の行き止まりを在来線にそろえる（#23 の続き）

（2026-11-20）

## 目的 / 発端

[2026-11-20_ami-tram.md](2026-11-20_ami-tram.md) の路面軌道は、行き止まりでレールと床をタイルの中心で止めていた。ユーザーの指摘で、在来線と同じく閉じた側のタイルの端から 1/4 にそろえる。

## 分かったこと（事実）

- 在来線の行き止まりの位置は、部品ではなく TRACK_PROFILES の `end_from_edge`（`addons/ami/blender/render.py` の `END_FROM_EDGE` = 0.25）で決まる。在来線・高速線の設定にだけ渡していて、路面軌道の設定には無かった
- 在来線の道床をタイルの端まで延ばすのは、道床の部品を `bed_to_edge_shape` に差し替えて行っている（`_REPLACE`）。路面軌道の床は別の部品なので、同じ考え方の差し替えが要る

## 直したこと

- 路面軌道の設定に `end_from_edge: END_FROM_EDGE` を足した。レール・溝・目地・汚れの帯は経路の始点に合わせて動く
- `tools/blender/sheetlib/tram_parts.py` に `_to_edge` を足し、縁の帯の板を閉じた側のタイルの端まで、床をそこから縁の帯の幅（`TRAM_END_BAND`）だけ手前まで延ばした。閉じた端にも縁の帯が回る

## 確かめたこと

（2026-11-20、`OTRPv64_3.exe`、`flat_512.sve`、`NUT=ingame/tram_sample.nut bash ingame/sample_parallel.sh`）

- 全区画が敷けた（返り値の先頭が `ok`）
- 区画 A の行き止まりで、レールが閉じた側の端から 1/4 で止まり、床と縁の帯がタイルの端まで届く（5 倍。`addons/ami/docs/tram_end_zoom.png`）。土の上と一般道路の上で見た
- `bash addons/ami/check.sh` が通った
