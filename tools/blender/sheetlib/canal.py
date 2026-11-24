"""運河の way（waytype=water。AMI #114）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

形: 地面より下がった水面と、水面を囲む石積みの護岸（壁）と、地面の高さの笠石（護岸の上の縁）。水路の外は描かない（地面のまま）。
水路の平面の形は、道路と同じく「腕」の和で決める: タイルの中心の正方形と、つながる辺ごとにタイルの辺の外まで延ばした腕
（幅はタイルの幅から両側の岸 CANAL_BANK を引いたもの）。T字・十字は腕の和で、腕と腕のあいだの角に岸が残る。
斜め（カーブも本体の斜めの絵を使う。AMI の線路・道路と同じ。景観の運河は除く: 斜めを持たず、カーブは L 字のセル `_CURVE_CELLS`。#217）は、つながる 2 辺の中点を結ぶ線に沿う帯で、タイルの辺で直線の腕と同じ幅になる
（帯の境は、その角の向きの座標 t = ±x ± y で CANAL_BANK < t < TILE − CANAL_BANK）。近い斜めの分け合うタイルは 2 本の帯。

地面より下の形を地面で隠すために、水路の外のタイル全面に holdout の材質の板（地面）を置く。holdout は透明に描かれ、後ろの形を隠す
（手前の岸の壁の内側の面と、手前の岸の陰の水面が、本物の地面と同じく隠れる）。

手本は iss の運河（../refs/iss/src/way/water/canal.dat。タイルいっぱいの水面と、つながらない辺の薄い壁）と、pak128 の canal_020
（水面とつながらない辺の石の縁。斜めは半分のタイル）。実用の運河の坂は iss のような閘門を描かず、水面ごと傾ける（pak128 と同じ）。景観の運河（SCENIC_STYLE）の坂は閘門（_lock_build）。
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

CULVERT_LINTEL = 0.45    # 暗渠の蓋（まぐさ）の幅（閉じた側のタイルの辺から。周りの護岸と笠石と同じくらい）
CULVERT_THICK = 1.0      # まぐさの厚み（地面から下へ。約 8px）。この下に暗い口が見える
# 景観の運河（#161）: iss の運河と同じ見せ方。水面は 13px 下（高さ 1 段 = 16px）で、タイルの辺近くまで広げ、縁は細い笠石。
# 坂は閘門（iss と同じく、上下の水面を扉枠で分ける。LOCK）。実用の運河（ROAD_STYLE。#114）の寸法は変えない
ROAD_STYLE = dict(pad=CANAL_PAD, bank=CANAL_BANK, coping=CANAL_COPING, water_z=CANAL_WATER_Z, wall_bottom=CANAL_WALL_BOTTOM, lock=False)
SCENIC_STYLE = dict(bank=0.35, coping=0.3, water_z=-13 / 16 * H, wall_bottom=-13 / 16 * H - 0.35, lock=True, pad=2.6, earth_eps=-0.03,
                    wall_col=((0.70, 0.70, 0.68), (0.80, 0.80, 0.77)), coping_col=((0.74, 0.74, 0.71), (0.84, 0.84, 0.81)),
                    # 護岸の水際の染み（#197。精細化のラウンド 1 の 1wl2）: 水面から height だけ上へ薄れる暗い帯（色, 高さ, 強さ）。物の座標の高さで付けるので、
                    # タイルをまたいで連続する
                    waterline=((0.06, 0.12, 0.10), 1.2, 1.0),
                    # 行き止まりの暗渠（#217。iss の運河に倣う）: 閉じた側の辺に、笠石・護岸（辺から 0.35）より 0.1 広い（辺から 0.45）蓋（まぐさ）を付け、その下に暗い口を描いて、水が奥へ続いて見えるようにする（だまし絵）。
                    # 蓋は地面の高さから厚み分だけ下まで（口は暗く見える）
                    culvert=(CULVERT_LINTEL, CULVERT_THICK))
CANAL_STYLES = {"road": ROAD_STYLE, "scenic": SCENIC_STYLE}
SCENIC_DEPTH_PX = 13      # 景観の運河の水面の深さ（画素。つなぎ目の持ち分を下へ広げる量）
LOCK_GATE = 0.25         # 閘門の扉の半分の厚み（坂の向きの座標 u = ±LOCK_GATE の間）
LOCK_PILLAR = 0.5        # 扉枠の柱の幅（水路の幅の端から）
LOCK_FRAME_Z = 2.2       # 扉枠の柱の高さ（上の水面側の縁から）
_LOCK_DIR = {"12": (0, 1), "9": (-1, 0), "3": (0, -1), "6": (1, 0)}  # 坂の名前 → 上りの向き（_slopes の高さの式と同じ）

# セル（行, 列）→ 名前。位置は線路の way と同じ（ami_dat.py の IMAGES）。カーブは斜めのセルを使うので、行 2 の列 5〜8 は描かない（景観の運河は逆に、斜めのセルを描かず列 5〜8 に L 字のカーブを描く）。
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


# 景観の運河（#217）のカーブのセル（行 2 の列 5〜8。iss の運河と同じ L 字）。斜めのセル（行 2 の列 0〜4・9）の代わりに描く。
# 斜めは壁が画面の縦の線になって面が見えず、直線の壁（面が見える）とのつなぎ目で壁が連続しない（iss も斜めを諦めて L 字のジグザグにしている）
_CURVE_CELLS = {(2, 5): "curve_sw", (2, 6): "curve_nw", (2, 7): "curve_ne", (2, 8): "curve_se"}


def _jobs(scenic=False):
    """描くセル（行, 列）→ (名前, 坂の高さ)。ONLY のときは、その名前と南北の直線だけ。景観の運河（scenic）は斜めのセルでなく L 字のカーブのセル"""
    cells = {pos: name for pos, name in _CELLS.items() if not (scenic and name in _DIAG_CORNERS)}
    if scenic:
        cells.update(_CURVE_CELLS)
    jobs = {pos: (name, None) for pos, name in cells.items()}
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


def canal_water_pieces(name, inset, pad=None):
    """水路の平面の形（凸の多角形の和）。inset はタイルの辺から縁までの距離（水面は CANAL_BANK、笠石の外の縁は CANAL_BANK − CANAL_COPING）"""
    half, reach = TILE / 2, TILE / 2 + (CANAL_PAD if pad is None else pad)
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


def _pieces(name, inset, half_plane=None, pad=None):
    """canal_water_pieces を、半平面 a x + b y <= c で切ったもの（閘門の上下の水面・壁を分ける）"""
    pieces = canal_water_pieces(name, inset, pad)
    if half_plane:
        pieces = [q for q in (_clip(p, *half_plane) for p in pieces) if len(q) >= 3]
    return pieces


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


def _shell(name, name_cell, outer_inset, z0, z1, mat, bank=CANAL_BANK, half_plane=None, pad=None):
    """水路の縁の帯（outer_inset の形から水面の形を抜いたもの）。half_plane=(a, b, c) なら a x + b y <= c の側だけ"""
    ob = _joined(name, _pieces(name_cell, outer_inset, half_plane, pad), z0, z1, mat)
    cut = _joined(name + "_cut", _pieces(name_cell, bank, half_plane, pad), z0 - 1.0, z1 + 1.0, mat)
    boolean(ob, cut)
    _remove(cut)
    return ob


def canal_build(name, slope, snow, st=ROAD_STYLE, slope_name=None):
    """運河 1 タイルの形。st は寸法（ROAD_STYLE・SCENIC_STYLE）。景観の坂（st["lock"] と slope_name）は閘門"""
    bank, cop, wz, wb = st["bank"], st["coping"], st["water_z"], st["wall_bottom"]
    pad = st["pad"]
    reach = TILE / 2 + pad
    water, wall, coping = _materials(st, snow)
    lock = bool(slope and st["lock"] and slope_name)
    if lock:
        return _lock_build(name, slope, slope_name, st, water, wall, coping)
    obs = [_joined("canal_water", canal_water_pieces(name, bank - 0.05, pad), wb, wz, water)]
    obs.append(_shell("canal_wall", name, bank - cop, wb, 0.0, wall, bank, None, pad))
    obs.append(_shell("canal_coping", name, bank - cop, 0.0, CANAL_COPING_T, coping, bank, None, pad))
    if "culvert" in st and name in _ARMS and not slope:
        obs += _culvert(name, st, coping)
    if not LAYOUT:
        obs.append(_earth(name, bank, wb, reach, water, pad, st.get("earth_eps", CANAL_EARTH_EPS)))
    if slope:
        for ob in obs:
            apply_slope(ob, slope)
    return obs


def _culvert(name, st, coping):
    """行き止まりのセル（name は つながる辺の 1 文字）の暗渠。閉じた側の辺に、笠石の材質のまぐさ（幅 lintel、厚み thick）を付け、
    その下（水面から まぐさの下端まで）に暗い口の板を置く。口の前の面はまぐさと同じ位置で、水路の護岸の奥の面より少し手前に出す"""
    lintel, thick = st["culvert"]
    ax, ay = _ARMS[name]
    half = TILE / 2
    reach = half + st["pad"]
    edge = half - lintel  # 閉じた側の辺（u = −half）から lintel だけ内側の位置（u = −edge）
    wwidth = half - st["bank"]  # 水面の半幅
    dark = make_material(lambda: noisy_material("canal_culvert_dark", (0.01, 0.03, 0.04), (0.025, 0.06, 0.07), scale=30, rough=0.5), "canal_culvert_dark")

    def box(w, z0, z1, mat, nm):
        a, b = sorted((-ax * reach, -ax * edge)) if ax else sorted((-ay * reach, -ay * edge))
        poly = [(a, -w), (b, -w), (b, w), (a, w)] if ax else [(-w, a), (w, a), (w, b), (-w, b)]
        return _prism(nm, poly, z0, z1, mat)

    return [box(half - (st["bank"] - st["coping"]), -thick, CANAL_COPING_T, coping, "canal_culvert_lintel"),
            box(wwidth, st["wall_bottom"], -thick, dark, "canal_culvert_mouth")]


def _waterline_wall(wall, water_z, stain, height, k):
    """壁の材質の複製に、水面（water_z）から height だけ上へ薄れる暗い帯（stain の色、強さ k）を、物の座標の高さで重ねる。
    壁は発光（emit 0.6）で明るく見せているので、発光の色にも同じ帯を掛ける。"""
    import bpy
    name = "canal_wall_waterline"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = wall.copy()
    m.name = name
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = bsdf.inputs["Base Color"].links[0].from_socket
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], sep.inputs["Vector"])
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.clamp = True
    rng.inputs["From Min"].default_value = water_z
    rng.inputs["From Max"].default_value = water_z + height
    rng.inputs["To Min"].default_value = k
    rng.inputs["To Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], rng.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(rng.outputs["Result"], mix.inputs["Factor"])
    nt.links.new(base, mix.inputs["A"])
    mix.inputs["B"].default_value = (*stain, 1)
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    if bsdf.inputs["Emission Color"].links:
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Emission Color"])
    return m


def _materials(st, snow):
    """水面・壁・笠石の材質。景観の運河（wall_col・coping_col がある）は iss のように明るいコンクリート"""
    water = make_material(_M_WATER, "canal_water")
    if "wall_col" in st:
        wall = make_material(lambda: noisy_material("canal_wall_s", *st["wall_col"], scale=55, rough=0.9, emit=0.6), "canal_wall_s")
        if "waterline" in st:
            wall = make_material(lambda: _waterline_wall(wall, st["water_z"], *st["waterline"]), "canal_wall_waterline") if not LAYOUT else wall
        cop = make_material(_SNOW if snow else (lambda: noisy_material("canal_coping_s", *st["coping_col"], scale=55, rough=0.85)), "canal_coping_s")
        return water, wall, cop
    return water, make_material(_M_WALL, "canal_wall"), make_material(_SNOW if snow else _M_COPING, "canal_coping")


def _earth(name, bank, wb, reach, water, pad=CANAL_PAD, eps=CANAL_EARTH_EPS):
    """地面（holdout）。水路の形に抜く"""
    earth = _prism("canal_earth", [(-reach, -reach), (reach, -reach), (reach, reach), (-reach, reach)],
                   wb - 0.5, 0.0, _holdout())
    cut = _joined("canal_earth_cut", canal_water_pieces(name, bank + eps, pad), wb - 1.0, 1.0, water)
    boolean(earth, cut)
    _remove(cut)
    return earth


def _lock_build(name, slope, slope_name, st, water, wall, coping):
    """景観の運河の坂（閘門）。下半分は地面に沿う運河、上半分は 1 段（急坂は 2 段）上の平らな水面と、上の縁の高さの平らな壁。
    境に扉（壁）を立て、両岸に柱と、上に梁の扉枠を付ける。船が通る水面は扉で分かれる（絵だけ。経路は way がつなぐ）"""
    bank, cop, wz, wb = st["bank"], st["coping"], st["water_z"], st["wall_bottom"]
    n = 2 if slope_name.startswith("up2_") else 1
    a, b = _LOCK_DIR[slope_name.split("_")[-1] if slope_name.startswith("up2_") else slope_name[2:]]
    top = n * H
    lo, hi = (a, b, -LOCK_GATE), (-a, -b, -LOCK_GATE)  # u <= −扉 / u >= 扉（u = a x + b y）
    outer = bank - cop
    pad = st["pad"]
    obs = [_joined("canal_water_lo", _pieces(name, bank - 0.05, lo, pad), wb, wz, water),
           _joined("canal_water_hi", _pieces(name, bank - 0.05, hi, pad), wb + top, wz + top, water)]
    # 下半分の壁・笠石は地面に沿って傾ける。水面は傾けず平らなので、壁の下端は傾けても水面より下に残るよう top だけ深く取る（レビューの指摘）
    lo_obs = [_shell("canal_wall_lo", name, outer, wb - top, 0.0, wall, bank, lo, pad),
              _shell("canal_coping_lo", name, outer, 0.0, CANAL_COPING_T, coping, bank, lo, pad)]
    for ob in lo_obs:
        apply_slope(ob, slope)
    obs += lo_obs
    # 上半分の壁・笠石は、上の縁の高さで平ら
    obs.append(_shell("canal_wall_hi", name, outer, wb, top, wall, bank, hi, pad))
    obs.append(_shell("canal_coping_hi", name, outer, top, top + CANAL_COPING_T, coping, bank, hi, pad))
    # 扉: 水路全体の幅を、扉の厚みで切った板。下の水面の下から上の水面の少し上まで
    gate = [q for q in (_clip(_clip(p, a, b, LOCK_GATE), -a, -b, LOCK_GATE) for p in canal_water_pieces(name, outer)) if len(q) >= 3]
    obs.append(_joined("canal_gate", gate, wb, top + wz + 0.3, wall))
    # 扉枠: 両岸の柱（水路の幅の端から LOCK_PILLAR）と、上の梁
    w_out = TILE / 2 - outer
    for sgn in (1, -1):
        pil = [q for q in (_clip(p, -sgn * b, sgn * a, -(w_out - LOCK_PILLAR)) for p in gate) if len(q) >= 3]
        obs.append(_joined(f"canal_pillar{sgn}", pil, top, top + LOCK_FRAME_Z, coping))
    obs.append(_joined("canal_lintel", gate, top + LOCK_FRAME_Z - 0.4, top + LOCK_FRAME_Z, coping))
    if not LAYOUT:
        obs.append(_earth_sheared(name, bank, wb, slope, water, pad, st.get("earth_eps", CANAL_EARTH_EPS)))
    return obs


def _earth_sheared(name, bank, wb, slope, water, pad=CANAL_PAD, eps=CANAL_EARTH_EPS):
    """傾けた地面（holdout）。坂の面に沿い、水路の形に抜く"""
    reach = TILE / 2 + pad
    ob = _earth(name, bank, wb, reach, water, pad, eps)
    apply_slope(ob, slope)
    return ob


def _own(cname, slope, depth_px=0):
    """持ち分: 道路と同じ菱形（ROAD_CY）を上へ 1 行広げる（笠石の厚み）。depth_px > 0 のとき（景観の運河。水面が深い）は、
    菱形を depth_px だけ下へずらした分も足す: つながる辺の向こうの水面は、深いぶん手前のタイルの菱形の上の端へはみ出して見えるため
    （足さないと、タイルのつなぎ目に地面の帯が出る）"""
    m = _ground_mask(slope, None, ROAD_CY)
    m[:-1] |= m[1:]
    if depth_px:
        base = m.copy()
        for k in range(1, depth_px + 1):
            m[k:] |= base[:-k]
    own = m.astype(np.uint8) * 255
    save_rgba(os.path.join(_s.WORK, cname + "_own.png"), np.dstack([own, own, own, np.full_like(own, 255)]))


def canal_sheet(sheet, label="C", style="road", variant="road"):
    """運河の way のシート。夏の絵は行 0〜3、雪の絵（笠石に雪）は行 CANAL_SNOW_ROWS 下。アイコン（0,0）・カーソル（0,1。南北の直線）は
    仮の絵（AMI は icons.py が描き直す）"""
    set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
    st = CANAL_STYLES[variant]  # "scenic" は景観の運河（#161）
    cells = {}
    for is_snow, dr in ((False, 0), (True, CANAL_SNOW_ROWS)):
        for (r, c), (name, slope) in _jobs(variant == "scenic").items():
            cname = f"{sheet}_{'snow_' if is_snow else ''}{name}"
            clear_models()
            canal_build(name, slope, is_snow, st, name)
            cells[(r + dr, c)] = render_cell(cname)
            _own(cname, slope, SCENIC_DEPTH_PX if variant == "scenic" else 0)
    clear_models()
    canal_build("ns", None, False, st)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style=style)
    cells[(0, 1)] = cells[(0, 2)]
    make_sheet(cells, 2 * CANAL_SNOW_ROWS, 10, os.path.join(_s.SRC, sheet + ".png"))
