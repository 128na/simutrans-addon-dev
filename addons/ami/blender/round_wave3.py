"""精細化のラウンド（#56 の流れ。#197）の、第 3 弾の物（路面表示・運河と景観の運河）の描き分け。blender/round.py が AMI_FAMILY=wave3 のときに読む

ROUND_SETTINGS: ラウンドの鍵（葉の試しの "1xxx"）→ 設定。値の決め方は docs/records/ の記録。
apply(cfg, n, R, render): 描く前に、render.py の設定と sheetlib の材質を、このプロセスの中でだけ差し替える（描くプロセスは対象ごとに別。
共有の sheetlib の値をモジュールごと書き換えない）。

ユーザーが選んだ葉（1wl2・2slush6）は PR #218 で本番（render.py の `MARKING_SLUSH_T`、canal.py の `SCENIC_STYLE` の `waterline`）に入った。
今の本番に重ねると二重にかかるので、その葉（水際の染み 1wl・1wl2・2wl3、雪の縁 2slush6）とラウンド "1"・"2"、apply のその分は #351 で外した
（外す前の設定と apply は a15b576 のこのファイル）。残した 1chip・1chip2 は本番に入っていない葉で、今の本番に重ねて描き直せる。
入れなかった葉: 1chip2（1px の路側線が点々に切れる）、2wl3（染みが長くてくどい）、1rip（さざ波。PR #214 で取り下げた）。

意味の木（第 3 弾の物）: docs/records/2026-11-23_ami-wave3-refine-round1.md

設定のキー（どれも無くてよい）:
    chip: 白線の塗料の欠け。(欠けの色, 欠けの段の位置の上端, Scale)。路面表示の白線の材質（render.MARKING_LINE_WORN）を、
        2 色の段の下端が欠け（路面の色）になるまだらに替える
"""

ROUND_SETTINGS = {
    "0null": {},  # 作りの確かめ: 何も変えない（今の src/ と同じ絵になるか）
    # 葉ごとの試し
    "1chip": {"chip": ((0.30, 0.30, 0.32), 0.43, 12.0)},
    "1chip2": {"chip": ((0.30, 0.30, 0.32), 0.41, 12.0)},
}


def apply(cfg, n, R, render):
    if "chip" in cfg:
        rgb, top, scale = cfg["chip"]
        worn = render.MARKING_WORN
        render.MARKING_LINE_WORN = lambda: R.noisy_material(
            f"r{n}_marking_chip", rgb, worn[1], scale=scale, rough=0.6, emit=0.35, ramp=(top - 0.03, top))
