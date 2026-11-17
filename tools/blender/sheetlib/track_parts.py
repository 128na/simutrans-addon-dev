"""線路の部品（道床・まくらぎ・レール・車止め・汚れ）。壁・基盤・橋脚（wall_parts）を足した TRACK_PARTS・TRACK_EXTRAS を作る（共通の描画の道具 sheetlib の一部。tools/README.md）。"""
from dataclasses import dataclass
from typing import Callable
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .core import (  # noqa: F401
    Part,
    TILE,
    _side,
    along,
    box,
    merge,
    noisy_material,
    sweep,
)
from .wall_parts import (  # noqa: F401
    WALL_U,
    _M_BASE,
    _M_WALL,
    _end_wall_shape,
    _pier_shape,
    _ramp_body_shape,
    _wall_shape,
)


# pak128 標準に合わせて低くする: 道床の厚み0.12（画面で約1px）、レール上面0.30（約2px）
BALLAST_H = 0.12

BALLAST = [(-1.9, 0.0), (1.9, 0.0), (1.55, BALLAST_H), (-1.55, BALLAST_H)]

SLEEPER_Z, SLEEPER_H, SLEEPER_LEN = 0.15, 0.08, 2.0
SLEEPER_W = 0.24       # まくらぎ 1 本の線路に沿う幅
SLEEPER_PITCH = 0.62   # まくらぎの間隔
SLEEPER_FIRST = 0.31   # 経路の始点から最初のまくらぎまで

# 車止め（行き止まりの端から線路の側へ STOP_INSET 入った所に、線路を横切る向きで置く）
STOP_INSET = 0.7
STOP_POST = dict(sy=0.16, sz=0.75, back=0.12)   # 柱 2 本（中心線から STOP_POST_U 離れた左右）
STOP_POST_U = 0.47
STOP_BEAM = dict(sy=1.7, sz=0.36, dz=0.68)       # 横木（赤）
STOP_MARK = dict(sy=0.5, sz=0.38, dz=0.68, sx=0.22)  # 中央の白い印

# レールの間隔は iss・SIS に合わせて画面上 6px（直線で 1単位 ≈ 6.4px）
RAIL_IN, RAIL_OUT, RAIL_Z0, RAIL_Z1 = 0.417, 0.517, 0.19, 0.30


# 斜めのタイルの横幅の倍率。3D のまま描くと、斜めは横幅が縮まずに映って直線の約1.6倍太く見える。
# 画面上で直線と同じ太さに見える比率 2/√10 にする（pak128 標準も斜めはレール間隔を細く描く）
DIAG_RAIL = 2 / math.sqrt(10)

# 道床は、直線とのつなぎ目（タイルの辺）で直線と同じ幅になる 1/√2（斜めは辺を 45° で横切る）。
# 以前の 0.8 は辺で直線より約 1.8px 広く、つなぎ目の角に段と草の尖りが出た
DIAG_BALLAST = 1 / math.sqrt(2)


def _bed_shape(path, k):
    return sweep(path, [(u * k, v) for u, v in BALLAST])


def _sleeper_shape(path, k):
    boxes = [box(p.x, p.y, SLEEPER_Z, SLEEPER_W, SLEEPER_LEN * k, SLEEPER_H, rot=ang) for p, ang in along(path, SLEEPER_PITCH, SLEEPER_FIRST)]
    return merge(boxes) if boxes else None


def _rail_shape(side):
    def shape(path, k):
        a, b = RAIL_IN * k, RAIL_OUT * k
        if side < 0:
            return sweep(path, [(-b, RAIL_Z0), (-a, RAIL_Z0), (-a, RAIL_Z1), (-b, RAIL_Z1)])
        return sweep(path, [(a, RAIL_Z0), (b, RAIL_Z0), (b, RAIL_Z1), (a, RAIL_Z1)])
    return shape


_M_RAIL = ("rail", (0.50, 0.36, 0.30), 0.35, 0.6)

# 線路の部品（作る順 = 重なりの下から）
TRACK_PARTS = (
    Part("ballast", "bed", "bed", ("ballast", (0.42, 0.40, 0.37)), _bed_shape),
    Part("sleeper", "rail", "gauge", ("sleeper", (0.62, 0.61, 0.58)), _sleeper_shape),
    Part("railL", "rail", "gauge", _M_RAIL, _rail_shape(-1)),
    Part("railR", "rail", "gauge", _M_RAIL, _rail_shape(1)),
)


def _stop_shape(sy, sz, z, sx=0.2, back=0.0):
    """車止めの箱。行き止まりの端（経路の始点）から線路の側へ STOP_INSET 入った所に、線路を横切る向きで置く。"""
    def shape(path, k):
        d = (path[1] - path[0]).normalized()
        c = path[0] + d * (STOP_INSET - back)
        return box(c.x, c.y, z, sx, sy * k, sz, rot=math.atan2(d.y, d.x))
    return shape


def _strip_shape(u0, u1, z, th=0.004):
    """経路に沿った薄い帯（中心から u0〜u1、左右対称に2本）。面の上の色の違い（さび・わだち・光る頭）に使う。"""
    def shape(path, k):
        return merge([sweep(path, [(s * u0 * k, z), (s * u1 * k, z), (s * u1 * k, z + th), (s * u0 * k, z + th)][::s])
                      for s in (1, -1)])
    return shape


# 立体パーツ・汚れ（TRACK_PROFILES の groups で選ぶ。本体のシートには入れていない）
TRACK_EXTRAS = (
    # 車止め: 柱2本 + 横木（赤）+ 中央の白い印
    Part("stop_postL", "rail", "gauge", ("stop_post", (0.20, 0.20, 0.22)),
         lambda path, k: _stop_shape(STOP_POST["sy"], STOP_POST["sz"], RAIL_Z0 + STOP_POST["sz"] / 2, back=STOP_POST["back"])([path[0] + _side(path, STOP_POST_U * k), path[1] + _side(path, STOP_POST_U * k)], 1),
         "structure", "end"),
    Part("stop_postR", "rail", "gauge", ("stop_post", (0.20, 0.20, 0.22)),
         lambda path, k: _stop_shape(STOP_POST["sy"], STOP_POST["sz"], RAIL_Z0 + STOP_POST["sz"] / 2, back=STOP_POST["back"])([path[0] - _side(path, STOP_POST_U * k), path[1] - _side(path, STOP_POST_U * k)], 1),
         "structure", "end"),
    Part("stop_beam", "rail", "gauge", ("stop_beam", (0.75, 0.10, 0.08)), _stop_shape(STOP_BEAM["sy"], STOP_BEAM["sz"], RAIL_Z0 + STOP_BEAM["dz"]), "structure", "end"),
    Part("stop_mark", "rail", "gauge", ("stop_mark", (0.92, 0.92, 0.90)), _stop_shape(STOP_MARK["sy"], STOP_MARK["sz"], RAIL_Z0 + STOP_MARK["dz"], sx=STOP_MARK["sx"]), "structure", "end"),
    # 汚れ（group "weathering"）は下の TRACK_WEAR から足す
)

def track_noise(name, lo, hi, scale):
    """線路の汚れ・くすみの材質: 2 色のまだら。模様は部品の位置（Object 座標。部品の原点はどれも 0 なのでワールドの位置と同じ）で決める（T字・十字で経路ごとの帯が重なっても同じ模様になり、ちらつかない）。"""
    def make():
        m = noisy_material(name, lo, hi, scale=scale, rough=0.9)
        nt = m.node_tree
        if not any(n.type == "TEX_COORD" for n in nt.nodes):
            tc = nt.nodes.new("ShaderNodeTexCoord")
            nt.links.new(tc.outputs["Object"], next(n for n in nt.nodes if n.type == "TEX_NOISE").inputs["Vector"])
        return m
    return make


def _mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


WEAR_END_TRIM = 0.5  # 汚れの帯の、タイルの中で終わる端（行き止まり）を詰める長さ（走行面は道床より約 2px 手前にずれ、端が道床からはみ出した）


def _trim_inner_ends(path, d=WEAR_END_TRIM):
    """経路の端のうちタイルの中にあるもの（行き止まり）を d だけ詰める。タイルの外へ延ばした端はそのまま。"""
    inside = lambda p: max(abs(p.x), abs(p.y)) < TILE / 2 - 0.01
    out = [Vector(p) for p in path]
    for rev in (False, True):
        if rev:
            out.reverse()
        if inside(out[0]) and len(out) > 1:
            seg = out[1] - out[0]
            out[0] = out[0] + seg.normalized() * min(d, seg.length * 0.9)
    out.reverse()
    return out


def _wear_strip_shape(u0, u1, z, th):
    """汚れの帯（_strip_shape と同じ形で、行き止まりの端を詰める）。"""
    strip = _strip_shape(u0, u1, z, th)
    return lambda path, k: strip(_trim_inner_ends(path), k)


def _sleeper_patch_shape(u0, u1):
    """まくらぎの上面の薄い板（経路の中心から u0〜u1、左右に 1 枚ずつ）。まくらぎと同じ間隔に並べる（間では浮かない）。"""
    z = SLEEPER_Z + SLEEPER_H / 2 + 0.002

    def shape(path, k):
        out = []
        for p, ang in along(path, SLEEPER_PITCH, SLEEPER_FIRST):
            n = Vector((-math.sin(ang), math.cos(ang)))
            for sg in (1, -1):
                c = p + n * (sg * (u0 + u1) / 2 * k)
                out.append(box(c.x, c.y, z, 0.24, (u1 - u0) * k, 0.004, rot=ang))
        return merge(out) if out else None
    return shape


# 線路の汚れ（group "weathering"。道路の WEAR_LAYERS に当たる）: 形ではなく材質の違い。どれも走行面（rail）に乗せ、
# 横位置はレールと同じ倍率（gauge）にする（汚れがレールと一緒に動き、画面でレールとずれない）。道床の上面より少し上の薄い帯で、
# まくらぎの下に入る（まくらぎの間の道床にだけ見える）。層ごとに高さを少しずつ変えて重ねる（ちらつかない）
#   rust0・rust1: レールの両脇の鉄粉。広く薄い帯の上に狭く濃い帯を重ねて縁をぼかす
#   oil: レールの間の中ほどに落ちた油の暗い帯
#   sleeper_rust: まくらぎの上面の、レールの締結の周りのさび（道床の帯とつながって、帯がまくらぎで途切れない）
# まくらぎのくすみは材質の差し替え（TRACK_WEAR_SKIN）。雪の絵では、どれも雪の上の汚れ（灰色）に差し替える（TRACK_SNOW_WEAR_SKIN）
_BALLAST_RGB = (0.42, 0.40, 0.37)

_SLEEPER_RGB = (0.62, 0.61, 0.58)

# さび色は赤みを抑えた茶色にする（赤みが強いと、坂の測り方 slope_measure.py がレール（赤 − 青の大きい行）と取り違えた）
_RUST_LO, _RUST_HI = (0.26, 0.21, 0.16), (0.36, 0.30, 0.23)

_OIL_LO, _OIL_HI = (0.06, 0.055, 0.05), (0.13, 0.12, 0.11)

_DIRT_LO, _DIRT_HI = (0.36, 0.35, 0.34), (0.52, 0.51, 0.50)  # 雪の上の汚れ

_SNOW_LO, _SNOW_HI = (0.70, 0.73, 0.78), (0.90, 0.93, 0.97)

TRACK_WEAR = (  # (部品の名前, 経路の中心からの帯 (u0, u1), 汚れの 2 色, 道床の色からの寄せ具合, 雪の上での寄せ具合)
    ("rust0", (RAIL_IN - 0.32, RAIL_OUT + 0.55), (_RUST_LO, _RUST_HI), 0.50, 0.25),
    ("rust1", (RAIL_IN - 0.14, RAIL_OUT + 0.24), (_RUST_LO, _RUST_HI), 0.85, 0.40),
    ("oil", (0.0, RAIL_IN - 0.12), (_OIL_LO, _OIL_HI), 0.70, 0.55),
)

TRACK_EXTRAS += tuple(Part(n, "rail", "gauge", track_noise(f"track_{n}", _mix(_BALLAST_RGB, lo, t), _mix(_BALLAST_RGB, hi, t), 3.0),
                           _wear_strip_shape(u0, u1, BALLAST_H + 0.0015 * (i + 1), 0.001), "weathering", centre=False)
                      for i, (n, (u0, u1), (lo, hi), t, _) in enumerate(TRACK_WEAR))

TRACK_EXTRAS += (Part("sleeper_rust", "rail", "gauge",
                      track_noise("track_sleeper_rust", _mix(_SLEEPER_RGB, _RUST_LO, 0.45), _mix(_SLEEPER_RGB, _RUST_HI, 0.30), 4.0),
                      _sleeper_patch_shape(RAIL_IN - 0.16, RAIL_OUT + 0.16), "weathering", centre=False),)

# 夏の絵のまくらぎのくすみ（weathering を使う版だけ）
TRACK_WEAR_SKIN = {"sleeper": track_noise("track_sleeper_dull", (0.51, 0.50, 0.47), (0.62, 0.61, 0.58), 5.0)}

# 雪の絵: 汚れの帯を、雪の色から灰色へ寄せた汚れた雪にする（列車の通る所は雪が汚れる。道路の車道を夏と同じにしたのに当たる）
TRACK_SNOW_WEAR_SKIN = dict(
    {n: track_noise(f"track_snow_{n}", _mix(_SNOW_LO, _DIRT_LO, ts), _mix(_SNOW_HI, _DIRT_HI, ts), 3.0)
     for n, _, _, _, ts in TRACK_WEAR},
    sleeper_rust=track_noise("track_snow_sleeper_rust", _mix((0.80, 0.84, 0.90), _DIRT_LO, 0.3), _mix((0.80, 0.84, 0.90), _DIRT_HI, 0.3), 4.0))


# ---------------------------------------------------------------- 差し替え用の形（TRACK_PROFILES の "replace" で使う。本体の部品は変えない）

def _inner(p):
    return max(abs(p.x), abs(p.y)) < TILE / 2 - 0.01


def bed_to_edge_shape(path, k):
    """道床の形（_bed_shape と同じ断面）。行き止まりの経路（始点だけがタイルの中）では、始点を経路の逆向きにタイルの端まで延ばす
    （道床がレールの末端より奥まで続く）。1 タイルだけの軌道（両端がタイルの中）と、通り抜ける経路はそのまま。"""
    if len(path) >= 2 and _inner(path[0]) and not _inner(path[-1]):
        d = (path[1] - path[0]).normalized()
        reach = (TILE / 2 + Vector((path[0].x, path[0].y)).dot(d.to_2d())) / max(abs(d.x), abs(d.y))  # 始点から逆向きのタイルの端まで
        path = [path[0] - d * (reach + 0.5)] + list(path)
    return _bed_shape(path, k)


def bed_fill_shape(paths, widths_by_id):
    """道床の上面（経路から BALLAST の上の幅）の、タイルの中の部分の凸包を、地面から上面の少し下までの板にする。
    widths_by_id は経路の id → 横幅の倍率（斜めの部分）。T字・十字で直線と斜めの道床の間にできるすき間を埋める。"""
    top = BALLAST[2][0]
    lim = TILE / 2 + 1e-4

    def shape(path, k):
        pts = []
        for p in paths:
            w = top * widths_by_id.get(id(p), 1.0)
            for a, b in zip(p[:-1], p[1:]):
                a, b = Vector((a.x, a.y)), Vector((b.x, b.y))
                n = (b - a).normalized()
                n = Vector((n.y, -n.x))
                steps = max(1, int((b - a).length / 0.05))
                for i in range(steps + 1):
                    q = a.lerp(b, i / steps)
                    if max(abs(q.x), abs(q.y)) <= lim:
                        pts += [q + n * w, q - n * w]
        pts = sorted({(round(q.x, 4), round(q.y, 4)) for q in pts})
        if len(pts) < 3:
            return None

        def half(seq):
            h = []
            for q in seq:
                while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (q[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (q[0] - h[-2][0])) <= 0:
                    h.pop()
                h.append(q)
            return h
        hull = half(pts)[:-1] + half(pts[::-1])[:-1]  # 反時計回り
        z0, z1 = 0.001, BALLAST_H - 0.003
        m = len(hull)
        verts = [Vector((x, y, z0)) for x, y in hull] + [Vector((x, y, z1)) for x, y in hull]
        faces = [tuple(range(m - 1, -1, -1)), tuple(range(m, 2 * m))] + [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]
        return verts, faces
    return shape


def centre_strip_shape(u, z, th):
    """経路の中心をまたぐ 1 本の薄い帯（-u〜u）。行き止まりの端は汚れの帯と同じだけ詰める。
    _strip_shape(0, u) は中心で 2 本が辺を分け合い、行き止まりでは切り抜きで消えた（2026-11-17、AMI の在来線）"""
    def shape(path, k):
        return sweep(_trim_inner_ends(path), [(-u * k, z), (u * k, z), (u * k, z + th), (-u * k, z + th)])
    return shape


# ---------------------------------------------------------------- 車止め（group "buffer"。where="end"。AMI の在来線）
# 形は鉄道模型の車止めの写真から書き起こした（ユーザーから受け取った画像、2026-11-17。リポジトリには入れない）:
# レールの上を横切る低い台座、両側のレールの外から奥へ斜めに立ち上がる脚 2 本、上の受けの箱、レールの間の緩衝板、
# 奥の中央に立つ柱と、その上の標識灯の箱。全体は黒、灯は光る色。座標は行き止まりの端（経路の始点）から線路の側へ t、横へ u、高さ z
BUFFER_BEAM = dict(t=0.30, st=0.28, su=1.30, z0=RAIL_Z1, sz=0.12)          # 台座（レールの上を横切る）
BUFFER_LEG = dict(t0=1.05, u0=0.62, t1=0.30, u1=0.32, z1=0.95, w=0.11)     # 斜めの脚（下の端 → 上の端）
BUFFER_HEAD = dict(t=0.28, st=0.30, su=0.80, z=0.98, sz=0.24)               # 受けの箱
BUFFER_PLATE = dict(t=0.62, st=0.06, su=0.46, z0=RAIL_Z1, z1=0.88)          # 緩衝板（レールの間に立つ）
BUFFER_POST = dict(t=-0.12, s=0.14, z0=RAIL_Z0, z1=1.55)                     # 柱（奥の中央）
BUFFER_LAMP = dict(t=-0.12, s=0.34, z0=1.50, sz=0.32)                        # 標識灯の箱
BUFFER_LAMP_FACE = dict(st=0.02, s=0.26, sz=0.24)                           # 灯の光る面（箱の線路の側の面に貼る）
_M_BUFFER = ("buffer", (0.04, 0.04, 0.045), 0.6)
_M_BUFFER_LAMP = ("buffer_lamp", (0.95, 0.93, 0.85), 0.5, 0.0, 0.0, "light_white")


def _end_frame(path):
    """行き止まりの端の座標系: 始点・線路の向き d・横の向き n（sweep と同じ向き）。"""
    p0 = Vector((path[0].x, path[0].y))
    d = (Vector((path[1].x, path[1].y)) - p0).normalized()
    return p0, d, Vector((d.y, -d.x))


def _buffer_box(t, u, z, st, su, sz):
    def shape(path, k):
        p0, d, n = _end_frame(path)
        c = p0 + d * t + n * (u * k)
        return box(c.x, c.y, z, st, su * k, sz, rot=math.atan2(d.y, d.x))
    return shape


def _buffer_legs(path, k):
    """斜めの脚 2 本: レールの外の下の端から、奥（端の側）の上の端へ立ち上がる角柱。"""
    p0, d, n = _end_frame(path)
    g, out = BUFFER_LEG, []
    for s in (1, -1):
        a = p0 + d * g["t0"] + n * (s * g["u0"] * k)
        b = p0 + d * g["t1"] + n * (s * g["u1"] * k)
        h = g["w"] / 2
        verts = [Vector((q.x + n.x * su * h, q.y + n.y * su * h, z + sz * h))
                 for q, z in ((a, RAIL_Z0 + h), (b, g["z1"])) for su, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        out.append((verts, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]))
    return merge(out)


TRACK_EXTRAS += (
    Part("buffer_beam", "rail", "gauge", _M_BUFFER,
         _buffer_box(BUFFER_BEAM["t"], 0, BUFFER_BEAM["z0"] + BUFFER_BEAM["sz"] / 2, BUFFER_BEAM["st"], BUFFER_BEAM["su"], BUFFER_BEAM["sz"]),
         "buffer", "end"),
    Part("buffer_leg", "rail", "gauge", _M_BUFFER, _buffer_legs, "buffer", "end"),
    Part("buffer_head", "rail", "gauge", _M_BUFFER,
         _buffer_box(BUFFER_HEAD["t"], 0, BUFFER_HEAD["z"] + BUFFER_HEAD["sz"] / 2, BUFFER_HEAD["st"], BUFFER_HEAD["su"], BUFFER_HEAD["sz"]),
         "buffer", "end"),
    Part("buffer_plate", "rail", "gauge", _M_BUFFER,
         _buffer_box(BUFFER_PLATE["t"], 0, (BUFFER_PLATE["z0"] + BUFFER_PLATE["z1"]) / 2, BUFFER_PLATE["st"], BUFFER_PLATE["su"],
                     BUFFER_PLATE["z1"] - BUFFER_PLATE["z0"]), "buffer", "end"),
    Part("buffer_post", "rail", "gauge", _M_BUFFER,
         _buffer_box(BUFFER_POST["t"], 0, (BUFFER_POST["z0"] + BUFFER_POST["z1"]) / 2, BUFFER_POST["s"], BUFFER_POST["s"],
                     BUFFER_POST["z1"] - BUFFER_POST["z0"]), "buffer", "end"),
    Part("buffer_lamp", "rail", "gauge", _M_BUFFER,
         _buffer_box(BUFFER_LAMP["t"], 0, BUFFER_LAMP["z0"] + BUFFER_LAMP["sz"] / 2, BUFFER_LAMP["s"], BUFFER_LAMP["s"], BUFFER_LAMP["sz"]),
         "buffer", "end"),
    Part("buffer_light", "rail", "gauge", _M_BUFFER_LAMP,
         _buffer_box(BUFFER_LAMP["t"] + (BUFFER_LAMP["s"] + BUFFER_LAMP_FACE["st"]) / 2, 0,
                     BUFFER_LAMP["z0"] + BUFFER_LAMP["sz"] / 2, BUFFER_LAMP_FACE["st"], BUFFER_LAMP_FACE["s"], BUFFER_LAMP_FACE["sz"]),
         "buffer", "end"),
)


TRACK_EXTRAS += tuple(Part(name, "bed", "bed", _M_WALL, _wall_shape(s), "wall", tall=True, corridor=WALL_U)
                      for name, s in (("wallL", -1), ("wallR", 1)))


TRACK_EXTRAS += (Part("pier", "bed", "bed", ("base", (0.50, 0.50, 0.48)), _pier_shape, "pier"),)

TRACK_EXTRAS += (Part("endw", "bed", "bed", _M_WALL, _end_wall_shape, "wall", "end", tall=True),
                 Part("rampbody", "bed", "bed", _M_BASE, _ramp_body_shape, "ramp", ground=True))
