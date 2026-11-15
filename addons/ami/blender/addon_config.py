"""AMI の設定のうち、tools/blender の判定・比較の道具が読むもの（共通とアドオンの分け方は tools/README.md）。"""

# ゲームのタイル一覧（seam_judge.py・slope_measure.py）で、このアドオンの道を見分ける名前の接頭辞
PREFIX = "ami_"

# 道の名前（dat の name）→ シート名（src/<シート名>.png）。絵を作った way だけ
SHEETS = {"ami_rail_ballast": "ami_rail_ballast"}

# カーブに斜めの絵を使うシート（道路は作るステップで足す）
DIAG_CURVE_SHEETS = set()
