"""精細化のラウンド（#56）の、道路 3 種一式（基盤・高架・橋・トンネル・道路の壁・道路用の橋脚・歩道）の描き分け。blender/round.py が AMI_FAMILY=road のときに読む。

ROUND_SETTINGS: ラウンドの鍵（"1"・葉の試しの "1xxx" など）→ 設定。値の決め方は docs/records/ の各ラウンドの記録。
apply(cfg, n, R, render): 描く前に、render.py の設定（R.TRACK_PROFILES など）に cfg を重ねる。土台は今の render.py。
共有の tools/blender/sheetlib の値をモジュールごと書き換えない（ほかの系統の絵が変わる）。要るときは、描き分けの辞書の中で差し替える。
"""

ROUND_SETTINGS = {
    "1": {},
}


def apply(cfg, n, R, render):
    pass
