"""blender-poc の設定のうち、tools/blender の判定・比較の道具が読むもの（共通とアドオンの分け方は tools/README.md）。"""

# ゲームのタイル一覧（seam_judge.py・slope_measure.py）で、このアドオンの道を見分ける名前の接頭辞
PREFIX = "bpoc_"

# 道の名前（dat の name）→ シート名（src/<シート名>.png）
SHEETS = {"bpoc_track": "track", "bpoc_track_old": "track_old", "bpoc_road": "road", "bpoc_expressway": "expressway"}

# カーブに斜めの絵を使うシート（高速道路。SIS と同じ。expressway.dat の image[sw] など）
DIAG_CURVE_SHEETS = {"expressway"}
