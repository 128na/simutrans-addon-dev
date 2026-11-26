"""精細化のラウンド（#56）の、道路 3 種一式（基盤・高架・橋・トンネル・道路の壁・道路用の橋脚・歩道）の描き分け。blender/round.py が AMI_FAMILY=road のときに読む。

ROUND_SETTINGS: ラウンドの鍵 → 設定。apply(cfg, n, R, render): 描く前に、render.py の設定（R.ROAD_PROFILES など）に cfg を重ねる。土台は今の render.py。
共有の tools/blender/sheetlib の値をモジュールごと書き換えない（ほかの系統の絵が変わる）。要るときは、描き分けの辞書の中で差し替える。

ラウンド 3（2026-11-20）を本番（render.py の「道路一式の質感」と、sheetlib の asphalt_skin の ramp・wear_t、road_sheet・tunnel_sheet・
pier_sheet の mat_skin、road_sheet の snow_skin、sidewalk_sheet の paving・snow）に入れた。ラウンド 1〜4 の鍵と apply は、入れる前の本番に
重ねる作りで、今の本番に重ねると本番とラウンドの設定が混ざる（今の本番を土台にした比べにならない）ので、#351 で外した。
試した葉と決めた値は docs/records/2026-11-20_ami-road-refine-round<n>.md、外す前の設定と apply は a15b576 のこのファイルにある。
第 4 弾の物は、今の本番を土台にした系統 road4（blender/round_road4.py）で回した。

次のラウンドを回すときは、今の本番を土台にした鍵と apply を足す。道路の描き分け（sheetlib の road_sheet）は、プロファイルの辞書から材質（skin）しか
差し替えられない（部品の形を差し替える口が無い）。形を変える試しは、この系統を描くプロセスの中でだけ sheetlib.sheetlib の ROAD_PARTS を
差し替える（render_parallel は対象ごとに別のプロセス）。本番に入れるときは、road_sheet に部品の差し替えの口を足して置き換える。
"""

ROUND_SETTINGS = {
    "0null": {},  # 作りの確かめ: 何も変えない（今の src/ と同じ絵になるか）
}


def apply(cfg, n, R, render):
    assert not cfg, f"road の apply が受ける鍵は無い（#351 で外した）: {sorted(cfg)}"
