"""精細化のラウンド（#56）の、路面軌道の描き分け。blender/round.py が AMI_FAMILY=tram のときに読む。

ROUND_SETTINGS: ラウンドの鍵 → 設定。apply(cfg, n, R, render): 描く前に、render.py の設定（R.TRACK_PROFILES など）に cfg を重ねる。土台は今の render.py。
共有の tools/blender/sheetlib の値をモジュールごと書き換えない（ほかの系統の絵が変わる）。要るときは、描き分けの辞書の中で差し替える。

ラウンド 4（2026-11-20）を本番（sheetlib の tram_parts と track_sheet の cell_fills）に入れた。ラウンド 1〜4 の鍵と apply は、入れる前の本番に
重ねる作りで、本番で無くした定数（TRAM_SEAM_W・TRAM_OIL_U）を読むので今の本番では動かなかった。#351 で外した。
試した葉と決めた値は docs/records/2026-11-20_ami-tram-refine-round<n>.md、外す前の設定と apply は a15b576 のこのファイルにある。

次のラウンドを回すときは、今の本番を土台にした鍵と apply を足す。路面軌道の部品（sheetlib の tram_parts）は、寸法を部品を作るときに形へ
焼き込んでいるので、定数を書き換えても効かない。apply は cfg の値で部品（TRAM_TRACK_PARTS と汚れの TRAM_WEAR_REPLACE に当たるもの）を
作り直し、描き分けの辞書の写しに入れる。雪の絵は夏と同じ（docs/objects/rail.md の「路面軌道の作り」。除雪された想定）なので、
汚れの帯を作り直したら snow_skin も同じ材質にする。
"""

ROUND_SETTINGS = {
    "0check": {},  # 描き直しが本番の src/ と同じになるかを確かめる（設定なし）
}


def apply(cfg, n, R, render):
    assert not cfg, f"tram の apply が受ける鍵は無い（#351 で外した）: {sorted(cfg)}"
