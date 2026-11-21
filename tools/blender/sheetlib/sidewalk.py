"""歩道の way（道路の隣のタイルに敷く、別の waytype の way。AMI。ADR 0003）と、歩道の柵の way-object のシート。

歩道の way（sidewalk_sheet）:
絵は自分のつながり（隣の歩道とつながる辺）だけで決まる: タイル全面を歩道の高さの板（縁石の色）にし、上に敷石を敷く。
つながらない辺では敷石を縁石の上面の幅だけ内へ下げ、縁石の上面の帯と立ち上がりを見せる（隣が道路なら、道路との境の縁石になる）。
立ち上がりが見えるのは手前の辺（南・東）だけで、奥の辺（北・西）は上面の帯で縁石に見せる。
部品の寸法・材質は道路の歩道（road_parts の curb・paving。SIDEWALK_H・CURB_W）と同じ。雪の絵は道路の歩道と同じく雪の材質（ROAD_SNOW_SKIN）。
敷石と雪の材質は sidewalk_sheet の引数で替えられる（AMI の歩道は敷石の種類ごとに 1 枚と、まだらの雪）。
elevated なら高架の版（dat は system_type=1）: 板の下に、道路の高架と同じ深さの基盤と躯体を足し、持ち分を躯体の下まで広げる。
斜めの絵（diagonal）は持たない（本体は斜めの絵の無い way に、カーブの絵を使う。boden/wege/weg.cc の calc_image）。

歩道の柵（sidewalk_fence_sheet）: 歩道の上に立つ柵の way-object（#119）。柵は経路ではなく、歩道の板の縁（つながらない辺）に沿って立てる
（歩道の絵が四角いタイルなので、カーブでも柵はタイルの辺に沿う L 字になる）。行き止まりの閉じた辺には立てない（横断歩道へ続く口）。
版は single（つながらない辺の全部）・back（奥の辺: 北・西）・front（手前の辺: 南・東）。奥の辺の柵は奥の絵（backimage）、
手前の辺の柵は手前の絵（frontimage）に描く。柵の足元の高さは歩道の敷石の上面で、地上と高架の歩道で同じ way-object を使う。
"""
import math
import os

import numpy as np

from . import sheetlib as _s
from .cells import ROAD_CY, _ground_mask, exits_of, load_rgba8, make_sheet, render_cell, save_rgba
from .core import (H, ONLY, TILE, _SNOW, apply_slope, box, clear_models, make_material, mesh_object, named_materials,
                   set_anchor)
from .road_parts import CURB_W, SIDEWALK_H, _M_CURB, _M_PAVING
from .wall_parts import BASE_H, ELEV_BODY_D, ELEV_BODY_INSET, _M_BASE, _M_ELEV_BODY

SIDEWALK_PAD = 1.0       # つながる辺で、板と敷石をタイルの外へ延ばす量（持ち分で切る。隣の歩道との継ぎ目に地面を出さない）
SIDEWALK_FOOT = 0.3      # 板の下端（地面より下。手前の辺の立ち上がりの下の縁を持ち分の縁まで届かせる）
PAVING_TH = 0.02         # 敷石の厚み（道路の歩道の paving と同じ）
# 持ち分を上へ広げる行数。板の上面は地面より SIDEWALK_H 高く、奥の辺（北・西）の縁石の上面の帯が地面の菱形より上に出る
SIDEWALK_RISE = 3
# 雪の絵の行のずらし（dat を書く側の addons/ami/blender/ami_dat.py の SNOW_ROWS と同じ）
SIDEWALK_SNOW_ROWS = 4

# 高架の版: 板（縁石の色）は道路の高架の路面の下の基盤の上面（ROAD_BASE_DROP 下）まで。その下に基盤（BASE_H）と躯体（ELEV_BODY_D）。
# 深さは道路の高架（sheetlib の road_sheet の elev_body）と同じにし、並べた高架の道路と床の下の縁をそろえる。
# 躯体は、つながらない辺で ELEV_BODY_INSET 内へ下げる（道路の高架の、壁のある側と同じ）。道路用の橋脚（ami_pier_road）の上端もこの深さに合う
ELEV_LOWER = math.ceil((BASE_H + ELEV_BODY_D + _s.ROAD_BASE_DROP) * 16 / H) + 2  # 持ち分を下へ広げる行数（AMI の道路の高架と同じ）

# 歩道の柵（横断防止柵・転落防止柵の形。白く塗った鋼）。寸法の単位は 1 ≈ 1.15m（docs/reference/way-addon.md の 12 章）。
# 画面で 1px を切る部品は消えるので、横木・柱は 1.3px 以上（高さ 1 ≈ 7.8px）にする
FENCE_IN = 0.32          # タイルの辺から柵の中心まで（縁石の上面の帯 CURB_W の内側の縁のあたり）
FENCE_H = 0.85           # 柵の高さ（敷石の上面から。約 1m・約 6.6px）
FENCE_POST = 0.13        # 柱の太さ
FENCE_RAIL_W = 0.11      # 横木の厚み（水平）
FENCE_TOP_H = 0.17       # 上の横木の高さ（縦。約 1.3px）
FENCE_MID = (0.38, 0.15)  # 中の横木の下端と高さ
# 柱の並び: 辺に沿って FENCE_PITCH ごと。タイルの辺の上には置かない（隣のタイルと半分ずつになる）ので、半ピッチずらす。
# 4 本でタイル 1 辺（直線の画面で約 18px ごと）
FENCE_PITCH = TILE / 4
FENCE_PAD = 0.6          # 隣の柵へ続く端で、横木をタイルの外へ延ばす量（持ち分で切る）
FENCE_RISE = 11          # 柵の持ち分を上へ広げる行数（柵の高さ 約 7px と敷石の高さ 約 2px に余り）
FENCE_ALPHA = 128        # これより覆われていない縁の画素は捨てる（壁と同じく、半透明の縁が暗い点線になるため）
_M_FENCE = ("sidewalk_fence", (0.80, 0.81, 0.80), 0.5, 0.3)
# 版 → 柵を立てる辺
FENCE_SIDES = {"single": "nsew", "back": "nw", "front": "se"}
FENCE_FRONT_ROW = 4      # 柵のシートの手前の絵の行（奥の絵 4 行 → 手前の絵 4 行。sheetlib の WALL_FRONT_ROW と同じ並び）

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


def _jobs():
    """描くセル（行, 列）→ (名前, つながる辺, 坂の高さ)。ONLY のときは、その名前と南北の直線だけ"""
    jobs = {pos: (name, exits_of(name), None) for pos, name in _CELLS.items()}
    jobs.update({pos: (name, exits_of(name), slope) for pos, (name, slope) in _slopes().items()})
    if ONLY:
        jobs = {k: v for k, v in jobs.items() if v[0] in ONLY + ("ns",)}
    return jobs


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


def _build(exits, slope, snow, paving_mat, snow_mat, elevated):
    """歩道 1 タイルの形。elevated なら板の下に基盤と躯体を足す"""
    curb = make_material(snow_mat if snow else _M_CURB, "curb")
    paving = make_material(snow_mat if snow else paving_mat, "paving")
    drop = _s.ROAD_BASE_DROP
    _slab(exits, 0.0, -drop if elevated else -SIDEWALK_FOOT, SIDEWALK_H, curb, "curb", slope)
    _slab(exits, CURB_W, SIDEWALK_H, SIDEWALK_H + PAVING_TH, paving, "paving", slope)
    if elevated:
        _slab(exits, 0.0, -drop - BASE_H, -drop, make_material(_M_BASE, "base"), "base", slope)
        _slab(exits, ELEV_BODY_INSET, -drop - BASE_H - ELEV_BODY_D, -drop - BASE_H, make_material(_M_ELEV_BODY, "elev_body"),
              "elev_body", slope)


def _own(cname, slope, rise, lower=0):
    """持ち分: 道路と同じ菱形（ROAD_CY）を上へ rise 行、下へ lower 行広げて書く（cells の make_sheet が当てる）。
    一時フォルダは描くときの sheetlib の WORK を引く（名前で取り込むと、入口が描く前に WORK を切り替えたときに付いていかない。
    cells は切り替えた先から持ち分を読むので、絵がずれた。AMI の round.py の _run。docs/records/2026-11-20_ami-road-refine-round1.md）"""
    m = _ground_mask(slope, None, ROAD_CY, lower=lower)
    base = m.copy()
    for k in range(1, rise + 1):
        m[:-k] |= base[k:]
    own = m.astype(np.uint8) * 255
    save_rgba(os.path.join(_s.WORK, cname + "_own.png"), np.dstack([own, own, own, np.full_like(own, 255)]))
    return m


def _cell(cname, exits, slope, snow, paving_mat, snow_mat, elevated):
    clear_models()
    _build(exits, slope, snow, paving_mat, snow_mat, elevated)
    path = render_cell(cname)
    _own(cname, slope, SIDEWALK_RISE, ELEV_LOWER if elevated else 0)
    return path


def sidewalk_sheet(sheet, label="S", style="road", paving=None, snow=None, elevated=False, mat_skin=None):
    """歩道の way のシート。夏の絵は行 0〜3、雪の絵は行 SIDEWALK_SNOW_ROWS 下。アイコン（0,0）・カーソル（0,1。南北の直線）は仮の絵。
    paving は敷石の材質（無ければ道路の歩道と同じ _M_PAVING）、snow は雪の絵の縁石・敷石の材質（無ければ _SNOW）。make_material に渡せるもの。
    elevated は高架の版（板の下に基盤と躯体）。mat_skin は基盤・躯体の材質の名前による差し替え（road_sheet の mat_skin と同じ）"""
    paving, snow = paving or _M_PAVING, snow or _SNOW
    with named_materials(mat_skin):
        set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
        cells = {}
        for is_snow, dr in ((False, 0), (True, SIDEWALK_SNOW_ROWS)):
            for (r, c), (name, exits, slope) in _jobs().items():
                cname = f"{sheet}_{'snow_' if is_snow else ''}{name}"
                cells[(r + dr, c)] = _cell(cname, exits, slope, is_snow, paving, snow, elevated)
        clear_models()
        _build("ns", None, False, paving, snow, elevated)
        cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style=style)
        cells[(0, 1)] = cells[(0, 2)]
        make_sheet(cells, 2 * SIDEWALK_SNOW_ROWS, 10, os.path.join(_s.SRC, sheet + ".png"))


# ---------------------------------------------------------------- 歩道の柵（way-object。#119）

def fence_sides(name, variant):
    """セルの名前と版から、柵を立てる辺（n/s/e/w の文字列）。つながらない辺のうち版の辺で、行き止まりの閉じた辺（出口の反対）は除く"""
    exits = exits_of(name)
    sides = [d for d in "nsew" if d not in exits and d in FENCE_SIDES[variant]]
    if len(exits) == 1:
        closed = {"n": "s", "s": "n", "e": "w", "w": "e"}[exits]
        sides = [d for d in sides if d != closed]
    return "".join(sides)


def _fence_edge(side, sides, mat, slope):
    """辺 side に沿う柵（柱と上・中の横木）を作る。辺の両端は、隣の辺にも柵があれば角で止め（角に柱を立てる）、
    無ければタイルの外へ延ばす（隣のタイルの柵へ続く。持ち分で切る）"""
    half = TILE / 2
    c = half - FENCE_IN
    z0 = SIDEWALK_H + PAVING_TH
    # 辺に沿う向きの座標 t の範囲と、辺に直角な向きの位置。n・s は x に沿い、e・w は y に沿う
    along_x = side in "ns"
    across = c if side in "ne" else -c
    lo_side, hi_side = ("w", "e") if along_x else ("s", "n")
    t0 = -c if lo_side in sides else -half - FENCE_PAD
    t1 = c if hi_side in sides else half + FENCE_PAD
    obs = []

    def piece(name, tc, length, zc, height, thick):
        if along_x:
            verts = box(tc, across, zc, length, thick, height)
        else:
            verts = box(across, tc, zc, thick, length, height)
        obs.append(mesh_object(name, *verts, mat))

    piece("fence_top", (t0 + t1) / 2, t1 - t0, z0 + FENCE_H - FENCE_TOP_H / 2, FENCE_TOP_H, FENCE_RAIL_W)
    piece("fence_mid", (t0 + t1) / 2, t1 - t0, z0 + FENCE_MID[0] + FENCE_MID[1] / 2, FENCE_MID[1], FENCE_RAIL_W)
    posts = [-half + FENCE_PITCH * (k + 0.5) for k in range(int(TILE / FENCE_PITCH))]
    posts = [t for t in posts if t0 - 1e-6 <= t <= t1 + 1e-6]
    posts += [t for t, d in ((-c, lo_side), (c, hi_side)) if d in sides]  # 角の柱
    for t in posts:
        piece("fence_post", t, FENCE_POST, z0 + FENCE_H / 2, FENCE_H, FENCE_POST)
    if slope:
        for ob in obs:
            apply_slope(ob, slope)
    return obs


def _fence_cell(cname, sides, slope, mat):
    """柵 1 タイルの奥の絵と手前の絵（どちらも無ければ None）"""
    out = []
    for part in ("nw", "se"):
        use = "".join(d for d in sides if d in part)
        if not use:
            out.append(None)
            continue
        clear_models()
        for d in use:
            _fence_edge(d, sides, mat, slope)
        path = render_cell(f"{cname}_{part}")
        im = load_rgba8(path).copy()
        im[..., 3] = np.where(im[..., 3] >= FENCE_ALPHA, 255, 0)
        m = _own(f"{cname}_{part}", slope, FENCE_RISE)
        if slope:
            # 坂: 持ち分を左右へ 1 列広げる（壁と同じ。坂の上がった側の端で柵の最後の 1 列が切れ、隣のタイルとの間にすき間が出る）
            wide = m.copy()
            wide[:, 1:] |= m[:, :-1]
            wide[:, :-1] |= m[:, 1:]
            own = wide.astype(np.uint8) * 255
            save_rgba(os.path.join(_s.WORK, f"{cname}_{part}_own.png"), np.dstack([own, own, own, np.full_like(own, 255)]))
        if not im[..., 3].any():
            out.append(None)
            continue
        save_rgba(path, im)
        out.append(path)
    return out


def sidewalk_fence_sheet(sheet, variant, label="F", style="road"):
    """歩道の柵の way-object のシート。奥の絵（dat の backimage）は行 0〜3、手前の絵（frontimage）は行 FENCE_FRONT_ROW 下。
    セルの位置は歩道の way と同じ（カーブは行 2 の列 5〜8）。雪の絵は無い（way-object には雪のキーが無い）。
    アイコン（0,0）・カーソル（0,1。南北の直線の柵）は仮の絵（AMI は icons.py が描き直す）"""
    set_anchor(ROAD_CY)
    mat = make_material(_M_FENCE, "fence")
    cells = {}
    for (r, c), (name, _exits, slope) in _jobs().items():
        back, front = _fence_cell(f"{sheet}_{name}", fence_sides(name, variant), slope, mat)
        if back:
            cells[(r, c)] = back
        if front:
            cells[(r + FENCE_FRONT_ROW, c)] = front
    clear_models()
    _build("ns", None, False, _M_PAVING, _SNOW, False)
    for d in fence_sides("ns", "single"):
        _fence_edge(d, "ew", mat, None)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style=style)
    cells[(0, 1)] = cells.get((0, 2)) or cells.get((FENCE_FRONT_ROW, 2))
    make_sheet(cells, 2 * FENCE_FRONT_ROW, 10, os.path.join(_s.SRC, sheet + ".png"))
