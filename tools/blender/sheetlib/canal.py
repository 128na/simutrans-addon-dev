"""運河の way（waytype=water。AMI #114）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

形: 地面より下がった水面と、水面を囲む石積みの護岸（壁）と、地面の高さの笠石（護岸の上の縁）。水路の外は描かない（地面のまま）。
水路の平面の形は、道路と同じく「腕」の和で決める: タイルの中心の正方形と、つながる辺ごとにタイルの辺の外まで延ばした腕
（幅はタイルの幅から両側の岸 CANAL_BANK を引いたもの）。T字・十字は腕の和で、腕と腕のあいだの角に岸が残る。
斜め（カーブも本体の斜めの絵を使う。AMI の線路・道路と同じ）は、つながる 2 辺の中点を結ぶ線に沿う帯で、タイルの辺で直線の腕と同じ幅になる
（帯の境は、その角の向きの座標 t = ±x ± y で CANAL_BANK < t < TILE − CANAL_BANK）。近い斜めの分け合うタイルは 2 本の帯。

地面より下の形を地面で隠すために、水路の外のタイル全面に holdout の材質の板（地面）を置く。holdout は透明に描かれ、後ろの形を隠す
（手前の岸の壁の内側の面と、手前の岸の陰の水面が、本物の地面と同じく隠れる）。

手本は iss の運河（../refs/iss/src/way/water/canal.dat。タイルいっぱいの水面と、つながらない辺の薄い壁）と、pak128 の canal_020
（水面とつながらない辺の石の縁。斜めは半分のタイル）。坂は iss のような閘門を描かず、水面ごと傾ける（pak128 と同じ）。
"""
import os

import numpy as np

from . import sheetlib as _s
from .cells import ROAD_CY, _ground_mask, exits_of, make_sheet, render_cell, save_rgba
from .core import H, LAYOUT, ONLY, TILE, _SNOW, apply_slope, boolean, clear_models, make_material, mesh_object, noisy_material, set_anchor

# ---------------------------------------------------------------- 寸法（部品の 1 単位 ≈ 9px。高さ 1 単位 ≈ 7.8px）
CANAL_BANK = 0.5         # タイルの辺から水面の縁（護岸の内の面）まで。iss・pak128 と同じく水面をタイルいっぱい近くにする
CANAL_COPING = 0.35      # 笠石の幅（護岸の内の面から外へ）
CANAL_WATER_Z = -0.45    # 水面の高さ（地面から。約 3.5px 下）
CANAL_WALL_BOTTOM = -0.7  # 護岸の下端（水面より下。水面との継ぎ目に穴を出さない）
CANAL_COPING_T = 0.03    # 笠石の厚み（地面より上に出す分）
CANAL_PAD = 1.0          # つながる辺で、腕・帯をタイルの外へ延ばす量（持ち分で切る）
CANAL_EARTH_EPS = 0.02   # 地面（holdout）を水路より広く抜く量（護岸の内の面と重ねない）
CANAL_SNOW_ROWS = 4      # 雪の絵の行のずらし（addons/ami/blender/ami_dat.py の SNOW_ROWS と同じ）

# ---------------------------------------------------------------- 色
# 水面は青緑（iss の運河の色に寄せる）。灰色に寄せると、ゲームの画面でアスファルトの道路と見分けにくかった（2026-11-22）
WATER_LO, WATER_HI = (0.03, 0.13, 0.18), (0.05, 0.19, 0.25)
WALL_LO, WALL_HI = (0.26, 0.25, 0.23), (0.34, 0.33, 0.30)
COPING_LO, COPING_HI = (0.45, 0.44, 0.41), (0.53, 0.52, 0.48)
_M_WATER = lambda: noisy_material("canal_water", WATER_LO, WATER_HI, scale=30, rough=0.35)
_M_WALL = lambda: noisy_material("canal_wall", WALL_LO, WALL_HI, scale=55, rough=0.9)
_M_COPING = lambda: noisy_material("canal_coping", COPING_LO, COPING_HI, scale=55, rough=0.85)

# セル（行, 列）→ 名前。位置は線路の way と同じ（ami_dat.py の IMAGES）。カーブは斜めのセルを使うので、行 2 の列 5〜8 は描かない。
# 分岐の絵（列 10〜14）は持たない
_CELLS = {
    (0, 2): "ns", (0, 3): "ew", (0, 5): "s", (0, 6): "w", (0, 7): "n", (0, 8): "e", (0, 9): "single",
    (2, 0): "diag_sw", (2, 1): "diag_nw", (2, 2): "diag_ne", (2, 3): "diag_se", (2, 4): "close1", (2, 9): "close2",
    (3, 5): "nse", (3, 6): "new", (3, 7): "nsw", (3, 8): "sew", (3, 9): "nsew",
}
# 斜めのセル → 帯の角の向き（つながる 2 辺のあいだの角）
_DIAG_CORNERS = {"diag_sw": [(-1, -1)], "diag_nw": [(-1, 1)], "diag_ne": [(1, 1)], "diag_se": [(1, -1)],
                 "close1": [(-1, 1), (1, -1)], "close2": [(1, 1), (-1, -1)]}
_ARMS = {"n": (0, 1), "s": (0, -1), "e": (1, 0), "w": (-1, 0)}


def _slopes():
    """坂のセル（行 1）→ (名前, 坂の高さ)。単坂は列 0〜3、急坂は列 5〜8（12・9・3・6 の順。歩道と同じ）"""
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


def _jobs():
    """描くセル（行, 列）→ (名前, 坂の高さ)。ONLY のときは、その名前と南北の直線だけ"""
    jobs = {pos: (name, None) for pos, name in _CELLS.items()}
    jobs.update({pos: (name, slope) for pos, (name, slope) in _slopes().items()})
    if ONLY:
        jobs = {k: v for k, v in jobs.items() if v[0] in ONLY + ("ns",)}
    return jobs


def _clip(poly, a, b, c):
    """凸の多角形 poly を半平面 a x + b y <= c で切る（Sutherland–Hodgman）"""
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def canal_water_pieces(name, inset):
    """水路の平面の形（凸の多角形の和）。inset はタイルの辺から縁までの距離（水面は CANAL_BANK、笠石の外の縁は CANAL_BANK − CANAL_COPING）"""
    half, reach = TILE / 2, TILE / 2 + CANAL_PAD
    if name in _DIAG_CORNERS:
        frame = [(-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach)]
        out = []
        for dx, dy in _DIAG_CORNERS[name]:
            # 帯: inset < t < TILE − inset（t = dx·x + dy·y）。タイルの辺で、直線の腕と同じ幅になる
            poly = _clip(frame, -dx, -dy, -inset)
            poly = _clip(poly, dx, dy, TILE - inset)
            out.append(poly)
        return out
    w = half - inset
    out = [[(-w, -w), (w, -w), (w, w), (-w, w)]]
    for d in exits_of(name):
        ax, ay = _ARMS[d]
        if ax:
            x0, x1 = sorted((0.0, ax * reach))
            out.append([(x0, -w), (x1, -w), (x1, w), (x0, w)])
        else:
            y0, y1 = sorted((0.0, ay * reach))
            out.append([(-w, y0), (w, y0), (w, y1), (-w, y1)])
    return out


def _prism(name, poly, z0, z1, mat):
    """多角形 poly（反時計回りでなくてもよい）を z0〜z1 に立てた柱"""
    n = len(poly)
    if sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1])) < 0:
        poly = poly[::-1]
    verts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh_object(name, verts, faces, mat)


def _joined(name, polys, z0, z1, mat):
    """凸の多角形の和を 1 つの形にする（重なりは boolean の UNION で消す）"""
    obs = [_prism(f"{name}{i}", p, z0, z1, mat) for i, p in enumerate(polys)]
    ob = obs[0]
    for o in obs[1:]:
        boolean(ob, o, "UNION")
        _remove(o)
    return ob


def _remove(ob):
    import bpy
    bpy.data.objects.remove(ob, do_unlink=True)


def _holdout():
    import bpy
    m = bpy.data.materials.get("canal_earth_holdout")
    if m is None:
        m = bpy.data.materials.new("canal_earth_holdout")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        ho = nt.nodes.new("ShaderNodeHoldout")
        nt.links.new(ho.outputs[0], out.inputs["Surface"])
    return m


def _shell(name, name_cell, outer_inset, z0, z1, mat):
    """水路の縁の帯（outer_inset の形から水面の形を抜いたもの）"""
    ob = _joined(name, canal_water_pieces(name_cell, outer_inset), z0, z1, mat)
    cut = _joined(name + "_cut", canal_water_pieces(name_cell, CANAL_BANK), z0 - 1.0, z1 + 1.0, mat)
    boolean(ob, cut)
    _remove(cut)
    return ob


def canal_build(name, slope, snow):
    """運河 1 タイルの形"""
    reach = TILE / 2 + CANAL_PAD
    water = make_material(_M_WATER, "canal_water")
    wall = make_material(_M_WALL, "canal_wall")
    coping = make_material(_SNOW if snow else _M_COPING, "canal_coping")
    obs = [_joined("canal_water", canal_water_pieces(name, CANAL_BANK - 0.05), CANAL_WALL_BOTTOM, CANAL_WATER_Z, water)]
    obs.append(_shell("canal_wall", name, CANAL_BANK - CANAL_COPING, CANAL_WALL_BOTTOM, 0.0, wall))
    obs.append(_shell("canal_coping", name, CANAL_BANK - CANAL_COPING, 0.0, CANAL_COPING_T, coping))
    if not LAYOUT:
        earth = _prism("canal_earth", [(-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach)],
                       CANAL_WALL_BOTTOM - 0.5, 0.0, _holdout())
        cut = _joined("canal_earth_cut", canal_water_pieces(name, CANAL_BANK + CANAL_EARTH_EPS), CANAL_WALL_BOTTOM - 1.0, 1.0, water)
        boolean(earth, cut)
        _remove(cut)
        obs.append(earth)
    if slope:
        for ob in obs:
            apply_slope(ob, slope)
    return obs


def _own(cname, slope):
    """持ち分: 道路と同じ菱形（ROAD_CY）を上へ 1 行広げる（笠石の厚み）"""
    m = _ground_mask(slope, None, ROAD_CY)
    m[:-1] |= m[1:]
    own = m.astype(np.uint8) * 255
    save_rgba(os.path.join(_s.WORK, cname + "_own.png"), np.dstack([own, own, own, np.full_like(own, 255)]))


def canal_sheet(sheet, label="C", style="road"):
    """運河の way のシート。夏の絵は行 0〜3、雪の絵（笠石に雪）は行 CANAL_SNOW_ROWS 下。アイコン（0,0）・カーソル（0,1。南北の直線）は
    仮の絵（AMI は icons.py が描き直す）"""
    set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
    cells = {}
    for is_snow, dr in ((False, 0), (True, CANAL_SNOW_ROWS)):
        for (r, c), (name, slope) in _jobs().items():
            cname = f"{sheet}_{'snow_' if is_snow else ''}{name}"
            clear_models()
            canal_build(name, slope, is_snow)
            cells[(r + dr, c)] = render_cell(cname)
            _own(cname, slope)
    clear_models()
    canal_build("ns", None, False)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style=style)
    cells[(0, 1)] = cells[(0, 2)]
    make_sheet(cells, 2 * CANAL_SNOW_ROWS, 10, os.path.join(_s.SRC, sheet + ".png"))
