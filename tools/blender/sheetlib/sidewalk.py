"""歩道の way（道路の隣のタイルに敷く、別の waytype の way。AMI。ADR 0003）のシート。

絵は自分のつながり（隣の歩道とつながる辺）だけで決まる: タイル全面を歩道の高さの板（縁石の色）にし、上に敷石を敷く。
つながらない辺では敷石を縁石の上面の幅だけ内へ下げ、縁石の上面の帯と立ち上がりを見せる（隣が道路なら、道路との境の縁石になる）。
立ち上がりが見えるのは手前の辺（南・東）だけで、奥の辺（北・西）は上面の帯で縁石に見せる。
部品の寸法・材質は道路の歩道（road_parts の curb・paving。SIDEWALK_H・CURB_W）と同じ。雪の絵は道路の歩道と同じく雪の材質（ROAD_SNOW_SKIN）。
敷石と雪の材質は sidewalk_sheet の引数で替えられる（AMI の歩道は灰色の敷石と、まだらの雪）。
斜めの絵（diagonal）は持たない（本体は斜めの絵の無い way に、カーブの絵を使う。boden/wege/weg.cc の calc_image）。
"""
import os

import numpy as np

from . import sheetlib as _s
from .cells import ROAD_CY, _ground_mask, exits_of, make_sheet, render_cell, save_rgba
from .core import H, ONLY, TILE, _SNOW, apply_slope, box, clear_models, make_material, mesh_object, set_anchor
from .road_parts import CURB_W, SIDEWALK_H, _M_CURB, _M_PAVING

SIDEWALK_PAD = 1.0       # つながる辺で、板と敷石をタイルの外へ延ばす量（持ち分で切る。隣の歩道との継ぎ目に地面を出さない）
SIDEWALK_FOOT = 0.3      # 板の下端（地面より下。手前の辺の立ち上がりの下の縁を持ち分の縁まで届かせる）
PAVING_TH = 0.02         # 敷石の厚み（道路の歩道の paving と同じ）
# 持ち分を上へ広げる行数。板の上面は地面より SIDEWALK_H 高く、奥の辺（北・西）の縁石の上面の帯が地面の菱形より上に出る
SIDEWALK_RISE = 3
# 雪の絵の行のずらし（dat を書く側の addons/ami/blender/ami_dat.py の SNOW_ROWS と同じ）
SIDEWALK_SNOW_ROWS = 4

# セル（行, 列）→ 名前。位置は線路の way と同じ（ami_dat.py の IMAGES）。カーブは行 2 の列 5〜8（斜めのセルは無い）
_CELLS = {
    (0, 2): "ns", (0, 3): "ew", (0, 5): "s", (0, 6): "w", (0, 7): "n", (0, 8): "e", (0, 9): "single",
    (2, 5): "curve_sw", (2, 6): "curve_nw", (2, 7): "curve_ne", (2, 8): "curve_se",
    (3, 5): "nse", (3, 6): "new", (3, 7): "nsw", (3, 8): "sew", (3, 9): "nsew",
}


def _slopes():
    """坂のセル（行 1）→ (名前, 坂の高さ)。単坂は列 0〜3、急坂は列 5〜8（12・9・3・6 の順。橋脚のシートと同じ）"""
    half = TILE / 2
    up = lambda n, f: (lambda x, y: n * H * f(x, y) / TILE)
    out = {}
    for n, base in ((1, 0), (2, 5)):
        pre = "up" if n == 1 else "up2_"
        out[(1, base)] = (f"{pre}12", up(n, lambda x, y: y + half))
        out[(1, base + 1)] = (f"{pre}9", up(n, lambda x, y: half - x))
        out[(1, base + 2)] = (f"{pre}3", up(n, lambda x, y: half - y))
        out[(1, base + 3)] = (f"{pre}6", up(n, lambda x, y: x + half))
    return out


def _side_extent(exits, side, inset):
    """辺 side（n/s/e/w）の端の座標の絶対値。つながる辺はタイルの外へ SIDEWALK_PAD 延ばし、つながらない辺は inset だけ内へ"""
    half = TILE / 2
    return half + SIDEWALK_PAD if side in exits else half - inset


def _slab(exits, inset, z0, z1, mat, name, slope):
    w, e = -_side_extent(exits, "w", inset), _side_extent(exits, "e", inset)
    s, n = -_side_extent(exits, "s", inset), _side_extent(exits, "n", inset)
    ob = mesh_object(name, *box((w + e) / 2, (s + n) / 2, (z0 + z1) / 2, e - w, n - s, z1 - z0), mat)
    if slope:
        apply_slope(ob, slope)
    return ob


def _cell(cname, exits, slope, snow, paving_mat, snow_mat):
    clear_models()
    curb = make_material(snow_mat if snow else _M_CURB, "curb")
    paving = make_material(snow_mat if snow else paving_mat, "paving")
    _slab(exits, 0.0, -SIDEWALK_FOOT, SIDEWALK_H, curb, "curb", slope)
    _slab(exits, CURB_W, SIDEWALK_H, SIDEWALK_H + PAVING_TH, paving, "paving", slope)
    path = render_cell(cname)
    # 持ち分: 道路と同じ菱形（ROAD_CY）を上へ SIDEWALK_RISE 行広げる（奥の辺の縁石の上面の帯を残す）
    m = _ground_mask(slope, None, ROAD_CY)
    base = m.copy()
    for k in range(1, SIDEWALK_RISE + 1):
        m[:-k] |= base[k:]
    own = m.astype(np.uint8) * 255
    # 一時フォルダは描くときの sheetlib の WORK を引く（名前で取り込むと、入口が描く前に WORK を切り替えたときに付いていかない。
    # cells は切り替えた先から持ち分を読むので、絵がずれた。AMI の round.py の _run。docs/records/2026-11-20_ami-road-refine-round1.md）
    save_rgba(os.path.join(_s.WORK, cname + "_own.png"), np.dstack([own, own, own, np.full_like(own, 255)]))
    return path


def sidewalk_sheet(sheet, label="S", style="road", paving=None, snow=None):
    """歩道の way のシート。夏の絵は行 0〜3、雪の絵は行 SIDEWALK_SNOW_ROWS 下。アイコン（0,0）・カーソル（0,1。南北の直線）は仮の絵。
    paving は敷石の材質（無ければ道路の歩道と同じ _M_PAVING）、snow は雪の絵の縁石・敷石の材質（無ければ _SNOW）。make_material に渡せるもの"""
    paving, snow = paving or _M_PAVING, snow or _SNOW
    set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
    jobs = {pos: (name, exits_of(name), None) for pos, name in _CELLS.items()}
    jobs.update({pos: (name, exits_of(name), slope) for pos, (name, slope) in _slopes().items()})
    if ONLY:
        jobs = {k: v for k, v in jobs.items() if v[0] in ONLY + ("ns",)}
    cells = {}
    for is_snow, dr in ((False, 0), (True, SIDEWALK_SNOW_ROWS)):
        for (r, c), (name, exits, slope) in jobs.items():
            cname = f"{sheet}_{'snow_' if is_snow else ''}{name}"
            cells[(r + dr, c)] = _cell(cname, exits, slope, is_snow, paving, snow)
    clear_models()
    _slab("ns", 0.0, -SIDEWALK_FOOT, SIDEWALK_H, make_material(_M_CURB, "curb"), "curb", None)
    _slab("ns", CURB_W, SIDEWALK_H, SIDEWALK_H + PAVING_TH, make_material(paving, "paving"), "paving", None)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style=style)
    cells[(0, 1)] = cells[(0, 2)]
    make_sheet(cells, 2 * SIDEWALK_SNOW_ROWS, 10, os.path.join(_s.SRC, sheet + ".png"))
