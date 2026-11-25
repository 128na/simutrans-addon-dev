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

from sheet_rows import FENCE_FRONT_ROW, SIDEWALK_SNOW_ROWS  # 雪の絵の行のずらしと、柵の手前の絵の行（奥の絵 4 行 → 手前の絵 4 行）。dat を書く側も同じ定義を読む（#302）

from . import sheetlib as _s
from .cells import ROAD_CY, _ground_mask, exits_of, load_rgba8, make_sheet, render_cell, save_rgba
from .core import (H, ONLY, SCALE, TILE, _SNOW, apply_slope, box, clear_models, make_material, mesh_object, named_materials,
                   set_anchor)
from .road_parts import CURB_W, SIDEWALK_H, _M_CURB, _M_PAVING
from .wall_parts import BASE_H, ELEV_BODY_D, ELEV_BODY_INSET, _M_BASE, _M_ELEV_BODY

SIDEWALK_PAD = 1.0       # つながる辺で、板と敷石をタイルの外へ延ばす量（持ち分で切る。隣の歩道との継ぎ目に地面を出さない）
SIDEWALK_FOOT = 0.3      # 板の下端（地面より下。手前の辺の立ち上がりの下の縁を持ち分の縁まで届かせる）
PAVING_TH = 0.02         # 敷石の厚み（道路の歩道の paving と同じ）
# 持ち分を上へ広げる行数。板の上面は地面より SIDEWALK_H 高く、奥の辺（北・西）の縁石の上面の帯が地面の菱形より上に出る
SIDEWALK_RISE = 3 * SCALE

# 高架の版: 板（縁石の色）は道路の高架の路面の下の基盤の上面（ROAD_BASE_DROP 下）まで。その下に基盤（BASE_H）と躯体（ELEV_BODY_D）。
# 深さは道路の高架（sheetlib の road_sheet の elev_body）と同じにし、並べた高架の道路と床の下の縁をそろえる。
# 躯体は、つながらない辺で ELEV_BODY_INSET 内へ下げる（道路の高架の、壁のある側と同じ）。道路用の橋脚（ami_pier_road）の上端もこの深さに合う
SIDEWALK_ELEV_LOWER = math.ceil((BASE_H + ELEV_BODY_D + _s.ROAD_BASE_DROP) * 16 * SCALE / H) + 2  # 持ち分を下へ広げる行数（AMI の道路の高架と同じ）

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
FENCE_RISE = 11 * SCALE          # 柵の持ち分を上へ広げる行数（柵の高さ 約 7px と敷石の高さ 約 2px に余り）
FENCE_ALPHA = 128        # これより覆われていない縁の画素は捨てる（壁と同じく、半透明の縁が暗い点線になるため）
_M_FENCE = ("sidewalk_fence", (0.80, 0.81, 0.80), 0.5, 0.3)
# 版 → 柵を立てる辺
FENCE_SIDES = {"single": "nsew", "back": "nw", "front": "se"}

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
    _own(cname, slope, SIDEWALK_RISE, SIDEWALK_ELEV_LOWER if elevated else 0)
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


# ---------------------------------------------------------------- 電柱（way-object。#120）
# 歩道に立てる電柱と電線。毎タイルに柱を 1 本立て、つながる向きに電線を渡す（iss の電柱 ../refs/iss/src/util/road_misc/pole.dat と同じ考え方）。
# 柵との同居（ami_wall_sidewalk_<版>_pole）は柵の版と同じ辺に柵を立て、柱を柵の側へ寄せる。柱の位置は版ごとに決まった点
# （POLE_SHIFT）で、南北の辺を出る電線は x = 寄せ、東西の辺を出る電線は y = 寄せ の線を通るので、隣のタイルの電線と辺で合う。
# 柱・腕木・電線は手前の絵（frontimage）に描く（iss と同じ。電線は歩行者の上を通る）。柵の奥の辺は奥の絵のまま。
POLE_H = 5.5             # 柱の高さ（敷石の上面から。画面で約 43px。iss の電柱（../refs/iss/src/util/road_misc/pole.png）に合わせた。2026-11-22、ユーザーの指定）
POLE_W = 0.32            # 柱の太さ（画面で約 2.5px。コンクリートの柱）
POLE_TOP_W = 0.24        # 柱の上の太さ（上ほど細い柱を、上下 2 段の箱で表す）
POLE_ARM = (1.9, 0.16, 0.18)  # 腕木の長さ（電線に直角）・厚み・高さ
POLE_ARM_DOWN = 0.45     # 柱の上端から腕木の中心まで
POLE_WIRE_X = (-0.75, 0.0, 0.75)  # 腕木の上の電線の位置（腕木に沿って）
POLE_WIRE = (0.1, 0.14)  # 電線の幅・高さ（画面で約 1px。細いと縁の画素が捨てられて点線になる）
POLE_CABLE_Z = 3.2       # 通信線の高さ（1 本。柱の脇を通る）
POLE_CABLE_OFF = 0.3     # 通信線の柱からのずれ（腕木の向き）
POLE_PAD = 0.6           # 隣のタイルへ続く電線をタイルの外へ延ばす量（持ち分で切る）
POLE_RISE = 58 * SCALE           # 持ち分を上へ広げる行数（柱の高さ 約 43px と腕木・余り）
POLE_IN = 0.6            # 柵つきの版で、柵の中心から柱の中心まで（歩道の内側へ）
_M_SW_POLE = ("sidewalk_pole", (0.66, 0.66, 0.63), 0.7, 0.0)   # コンクリートの柱
_M_SW_POLE_ARM = ("sidewalk_pole_arm", (0.30, 0.30, 0.31), 0.5, 0.3)  # 鋼の腕木
_M_SW_POLE_WIRE = ("sidewalk_pole_wire", (0.10, 0.10, 0.11), 0.6, 0.0)  # 電線


def pole_shift(variant):
    """柱の位置（x, y）。back は北西へ、front は南東へ寄せる（柵の側。柵の無い版も同じ位置）。
    タイルの中心に立てる版は作らない（歩道の中央に電柱は立たない。#120、2026-11-22 のユーザーの指定）"""
    d = TILE / 2 - FENCE_IN - POLE_IN
    return {"back": (-d, d), "front": (d, -d)}[variant]


def _pole_parts(exits, slope, variant):
    """柱・腕木・電線。exits はつながる辺（無ければ柱だけ）"""
    half = TILE / 2
    ox, oy = pole_shift(variant)
    z0 = SIDEWALK_H + PAVING_TH
    pole, arm, wire = (make_material(m, p) for m, p in ((_M_SW_POLE, "pole"), (_M_SW_POLE_ARM, "pole_arm"), (_M_SW_POLE_WIRE, "pole_wire")))
    obs = []
    low = POLE_H * 0.55
    obs.append(mesh_object("pole_low", *box(ox, oy, z0 + low / 2, POLE_W, POLE_W, low), pole))
    obs.append(mesh_object("pole_high", *box(ox, oy, z0 + low + (POLE_H - low) / 2, POLE_TOP_W, POLE_TOP_W, POLE_H - low), pole))
    za = z0 + POLE_H - POLE_ARM_DOWN
    ns = any(d in exits for d in "ns")
    ew = any(d in exits for d in "ew")
    # 腕木は電線に直角。南北の電線なら東西向き、東西の電線なら南北向き。両方（曲がり・T字・十字）なら 2 本の十字。つながりが無ければ東西
    arms = ([("x", "ns")] if ns or not ew else []) + ([("y", "ew")] if ew else [])
    L, T, AH = POLE_ARM
    for axis, _ in arms:
        sx, sy = (L, T) if axis == "x" else (T, L)
        obs.append(mesh_object("pole_arm", *box(ox, oy, za, sx, sy, AH), arm))
    zw = za + AH / 2 + POLE_WIRE[1] / 2
    for d in exits:
        sign = 1 if d in "ne" else -1
        if d in "ns":
            y0, y1 = oy, sign * (half + POLE_PAD)
            lines = [(ox + w, zw) for w in POLE_WIRE_X] + [(ox + POLE_CABLE_OFF, z0 + POLE_CABLE_Z)]
            for x, z in lines:
                obs.append(mesh_object("pole_wire", *box(x, (y0 + y1) / 2, z, POLE_WIRE[0], abs(y1 - y0), POLE_WIRE[1]), wire))
        else:
            x0, x1 = ox, sign * (half + POLE_PAD)
            lines = [(oy + w, zw) for w in POLE_WIRE_X] + [(oy + POLE_CABLE_OFF, z0 + POLE_CABLE_Z)]
            for y, z in lines:
                obs.append(mesh_object("pole_wire", *box((x0 + x1) / 2, y, z, abs(x1 - x0), POLE_WIRE[0], POLE_WIRE[1]), wire))
    if slope:
        for ob in obs:
            apply_slope(ob, slope)
    return obs


def _pole_cell(cname, name, exits, slope, variant, fence):
    """電柱 1 タイルの奥の絵と手前の絵。奥は柵の奥の辺（柵つきの版だけ）、手前は柵の手前の辺と柱・電線"""
    sides = fence_sides(name, variant) if fence else ""
    fmat = make_material(_M_FENCE, "fence")
    out = []
    for part in ("nw", "se"):
        use = "".join(d for d in sides if d in part)
        if part == "nw" and not use:
            out.append(None)
            continue
        clear_models()
        for d in use:
            _fence_edge(d, sides, fmat, slope)
        if part == "se":
            _pole_parts(exits, slope, variant)
        path = render_cell(f"{cname}_{part}")
        im = load_rgba8(path).copy()
        im[..., 3] = np.where(im[..., 3] >= FENCE_ALPHA, 255, 0)
        m = _own(f"{cname}_{part}", slope, POLE_RISE if part == "se" else FENCE_RISE)
        if slope:
            wide = m.copy()  # 坂: 持ち分を左右へ 1 列広げる（柵と同じ）
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


def sidewalk_pole_sheet(sheet, variant, fence=True, label="P", style="road"):
    """電柱の way-object のシート（#120）。variant（back・front）は柱を寄せる側。fence が真ならその版の柵つき
    （ami_wall_sidewalk_<版>_pole）、偽なら電柱だけ（ami_sidewalk_pole_<版>）。並びは柵のシート（sidewalk_fence_sheet）と同じ。
    アイコン（0,0）・カーソル（0,1）は仮の絵（AMI は icons.py が描き直す）"""
    set_anchor(ROAD_CY)
    cells = {}
    for (r, c), (name, exits, slope) in _jobs().items():
        back, front = _pole_cell(f"{sheet}_{name}", name, exits, slope, variant, fence)
        if back:
            cells[(r, c)] = back
        if front:
            cells[(r + FENCE_FRONT_ROW, c)] = front
    clear_models()
    _build("ns", None, False, _M_PAVING, _SNOW, False)
    _pole_parts("ns", None, variant)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style=style)
    cells[(0, 1)] = cells.get((FENCE_FRONT_ROW, 2))
    make_sheet(cells, 2 * FENCE_FRONT_ROW, 10, os.path.join(_s.SRC, sheet + ".png"))
