"""AMI の設定のうち、tools/blender の判定・比較の道具が読むもの（共通とアドオンの分け方は tools/README.md）。"""
import catalog

# ゲームのタイル一覧（seam_judge.py・slope_measure.py）で、このアドオンの道を見分ける名前の接頭辞
PREFIX = catalog.PREFIX

# 道の名前（dat の name）→ シート名（src/<シート名>.png）。絵を作った way だけ
SHEETS = {}
for _t in catalog.TRACKS:
    SHEETS[_t.way] = _t.way
    SHEETS.update({_t.base(v): _t.base(v) for v in catalog.VARIANTS})
    SHEETS.update({_t.elev(v): _t.elev(v) for v in catalog.VARIANTS})
SHEETS["ami_pier_rail"] = "ami_pier_rail"
SHEETS["ami_pier_rail_gate"] = "ami_pier_rail_gate"
SHEETS.update({_r.way: _r.way for _r in catalog.ROADS})
for _r in catalog.ROADS:
    SHEETS.update({_r.base(v): _r.base(v) for v in catalog.VARIANTS})
    SHEETS.update({_r.elev(v): _r.elev(v) for v in catalog.VARIANTS})
SHEETS[catalog.PIER_ROAD] = catalog.PIER_ROAD
SHEETS[catalog.TRAM] = catalog.TRAM
SHEETS[catalog.SIDEWALK] = catalog.SIDEWALK

# カーブに斜めの絵を使うシート（道路 3 種も）。
# 基盤の版・高架の版（線路・道路）はカーブを斜めの形の別のセル（基盤の壁の無い側を削らない）に描くので、ここには入れない
DIAG_CURVE_SHEETS = {_t.way for _t in catalog.TRACKS} | {_r.way for _r in catalog.ROADS}
