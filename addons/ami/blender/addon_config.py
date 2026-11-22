"""AMI の設定のうち、tools/blender の判定・比較の道具が読むもの（共通とアドオンの分け方は tools/README.md）。"""
import catalog

# ゲームのタイル一覧（seam_judge.py・slope_measure.py）で、このアドオンの道を見分ける名前の接頭辞
PREFIX = catalog.PREFIX

# 道の名前（dat の name）→ シート名（src/<シート名>.png）。絵を作った way だけ
SHEETS = {}
for _t in catalog.ALL_TRACKS:
    SHEETS[_t.way] = _t.way
    SHEETS.update({_t.base(v): _t.base(v) for v in catalog.VARIANTS})
    SHEETS.update({_t.elev(v): _t.elev(v) for v in catalog.VARIANTS})
SHEETS.update({catalog.pier_rail(_g, _o): catalog.pier_rail(_g, _o) for _o in (False, True) for _g in (False, True)})
SHEETS.update({_r.way: _r.way for _r in catalog.ROADS})
for _r in catalog.ROADS:
    SHEETS.update({_r.base(v): _r.base(v) for v in catalog.VARIANTS})
    SHEETS.update({_r.elev(v): _r.elev(v) for v in catalog.VARIANTS})
SHEETS.update({_m: _m for _m in catalog.MARKINGS})  # 路面表示の way（#187）
SHEETS[catalog.PIER_ROAD] = catalog.PIER_ROAD
SHEETS[catalog.TRAM] = catalog.TRAM
SHEETS.update({_s: _s for _s in catalog.SIDEWALKS})
SHEETS.update({_e: _e for _e in catalog.EMBANKMENTS})
SHEETS.update({_m: _m for _m in (catalog.MONORAIL, *catalog.MONORAIL_ELEVS)})  # 跨座式モノレール（#113）
SHEETS[catalog.CANAL] = catalog.CANAL  # 運河（#114）

# カーブに斜めの絵を使うシート（道路 3 種も）。
# 基盤の版・高架の版（線路・道路）はカーブを斜めの形の別のセル（基盤の壁の無い側を削らない）に描くので、ここには入れない
DIAG_CURVE_SHEETS = {_t.way for _t in catalog.ALL_TRACKS} | {_r.way for _r in catalog.ROADS}
DIAG_CURVE_SHEETS |= {catalog.MONORAIL, *catalog.MONORAIL_ELEVS}  # 跨座式モノレールは高架の版もカーブを斜めの絵（#113）
DIAG_CURVE_SHEETS.add(catalog.CANAL)  # 運河もカーブは斜めの絵（#114）
