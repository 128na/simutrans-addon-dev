"""精細化のラウンド（#56 の流れ。#331）の、第 5 弾の物（路面の色・黄色の中央線・交差点の中心の印、転車台・遷車台）の描き分け。
blender/round.py が AMI_FAMILY=wave5 のときに読む。

ラウンド 1〜3 は本番（render.py の MARKING_COLOR_ARGS・MARKING_COLOR_LIFT と、sheetlib の marking.py・turntable.py）に入れた（#331）。
今の本番に重ねると二重にかかる（走行跡は本番の口が変わったので落ちる）ので、その鍵と apply の中身（render.py の写しを含む）は #351 で外した。
試した葉と決めた値は docs/records/2026-11-26_ami-wave5-refine-round1.md、外す前の設定と apply は a15b576 のこのファイルにある。

次のラウンドを回すときは、今の本番を土台にした鍵と apply を足す。
ROUND_SETTINGS: ラウンドの鍵 → 設定。apply(cfg, n, R, render): 描く前に、このプロセスの中でだけ本番の設定に cfg を重ねる。
"""

ROUND_SETTINGS = {
    "0null": {},  # 作りの確かめ: 何も変えない（今の src/ と同じ絵になるか）
}


def apply(cfg, n, R, render):
    assert not cfg, f"wave5 の apply が受ける鍵は無い（#351 で外した）: {sorted(cfg)}"
