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
SHEETS[catalog.CANAL_SCENIC] = catalog.CANAL_SCENIC  # 景観の運河（#161）

# カーブに斜めの絵を使うシート。唯一の定義は catalog.py の DIAG_CURVE_WAYS（dat を書く ami_dat.py の DIAG_CURVES と同じ集まり。#227）
DIAG_CURVE_SHEETS = catalog.DIAG_CURVE_WAYS
