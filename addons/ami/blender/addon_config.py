"""AMI の設定のうち、tools/blender の判定・比較の道具が読むもの（共通とアドオンの分け方は tools/README.md）。"""
import catalog

# ゲームのタイル一覧（seam_judge.py・slope_measure.py）で、このアドオンの道を見分ける名前の接頭辞
PREFIX = catalog.PREFIX

# 道の名前（dat の name）→ シート名（src/<シート名>.png）。絵を作った way だけ。
# 絵を作った way（線路・道路・路面軌道・モノレール・運河。dat と同じ並び）は catalog.BUILT_WAYS から引く（#242。別々に書いて懸垂式が抜けていた）
SHEETS = {_n: _n for _n in catalog.BUILT_WAYS}
SHEETS.update({catalog.pier_rail(_g, _o): catalog.pier_rail(_g, _o) for _o in (False, True) for _g in (False, True)})
SHEETS.update({_m: _m for _m in catalog.MARKINGS})  # 路面表示の way（#187）
SHEETS[catalog.PIER_ROAD] = catalog.PIER_ROAD
SHEETS.update({_s: _s for _s in catalog.SIDEWALKS})
SHEETS.update({_e: _e for _e in catalog.EMBANKMENTS})

# カーブに斜めの絵を使うシート。唯一の定義は catalog.py の DIAG_CURVE_WAYS（dat を書く ami_dat.py の DIAG_CURVES と同じ集まり。#227）
DIAG_CURVE_SHEETS = catalog.DIAG_CURVE_WAYS
