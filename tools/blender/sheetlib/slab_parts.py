"""スラブ軌道の部品（コンクリート道床・てん充層・軌道スラブ・突起・締結装置と、スラブの上の汚れ）。
レールの形と高さ・横位置は線路の部品（track_parts）のものをそのまま使う。TRACK_PROFILES の "track_parts"・"replace"・"bed_fills"・"snow_skin" に渡す
（共通の描画の道具 sheetlib の一部。tools/README.md）。"""
from dataclasses import replace
import math

from mathutils import Vector

from .core import Part, TILE, _SNOW, box, merge, sweep
from .track_parts import (
    RAIL_IN,
    RAIL_OUT,
    TRACK_EXTRAS,
    TRACK_PARTS,
    TRACK_WEAR,
    _RUST_HI,
    _RUST_LO,
    _OIL_HI,
    _OIL_LO,
    _edge_reach,
    _inner,
    _mix,
    _trim_inner_ends,
    track_noise,
)

# ---------------------------------------------------------------- 断面（部品の 1 単位 ≈ 9px。高さは下から順に積む）
# どれもレールと同じだけ動かす。コンクリート道床は基準面 slab_bed（値は rail と同じにする。名前を分けるのは、分岐の絵で rail の部品だけが
# 分岐の経路で作り直されるため。道床は bed の道床と同じく、T字・十字の形のままにする）。bed のままだと、スラブが道床の手前へ 2px 寄って見えた
SLAB_BED_U = 1.72                   # 道床の下面の半幅（在来線の道床の下面 1.9 より狭く、上面 1.55 より広い）
SLAB_BED_TOP_U = 1.68               # 道床の上面の半幅
SLAB_BED_H = 0.08                   # 道床の厚み
SLAB_FILL_Z0, SLAB_FILL_Z1 = 0.08, 0.11   # てん充層の下面・上面
SLAB_FILL_OVER = 0.05               # てん充層がスラブの縁から出る幅（黒い線に見える）
SLAB_Z0, SLAB_Z1 = SLAB_FILL_Z1, 0.15     # 軌道スラブの下面・上面（レールの下面 0.19 との間に締結装置が入る）
SLAB_U = 1.02                       # 軌道スラブの半幅（在来線のまくらぎの半分の長さ 1.0 に合わせる）

# ---------------------------------------------------------------- 線路に沿った割り付け
SLAB_PITCH = 5.0       # スラブ 1 枚の長さの目安（直線はタイルに 2 枚。継ぎ目はタイルの辺から 2.5 の所で、辺には来ない）
SLAB_GAP = 0.2         # スラブどうしのすき間
SLAB_OVERHANG = 0.45   # タイルの中で終わる端で、レールの末端からスラブが延びる長さ（車止めの柱が乗る）
SLAB_BED_PAD = 1.1     # 1 タイルだけの軌道で、道床がレールの末端から延びる長さ（突起の外まで）
SLAB_END_MARGIN = 1.0  # 行き止まりで、レールの末端にこれより近い継ぎ目は作らない

STUD_R = 0.24          # 突起の半径
STUD_TOP = SLAB_Z1 + 0.04   # 突起の上面（スラブの上面より少し高い）
STUD_SIDES = 12
NOTCH_R = 0.36         # スラブの端の欠き込みの半径（てん充層の色の円で表す）
NOTCH_TH = 0.002

FASTENER_PITCH = 0.625   # 締結装置の間隔の目安（直線でタイルに 16 組）
FASTENER_ALONG = 0.22    # 線路に沿う幅
FASTENER_ACROSS = 0.34  # 線路を横切る幅
FASTENER_Z0, FASTENER_Z1 = SLAB_Z1, 0.20   # 下面はスラブの上面、上面はレールの下面より少し上
RAIL_CENTRE = (RAIL_IN + RAIL_OUT) / 2

# ---------------------------------------------------------------- 色
SLAB_BED_LO, SLAB_BED_HI = (0.13, 0.13, 0.13), (0.20, 0.20, 0.195)   # コンクリート道床（暗い灰色のまだら）
SLAB_BED_GRAIN = 5.0
SLAB_LO, SLAB_HI = (0.60, 0.60, 0.57), (0.68, 0.68, 0.65)           # 軌道スラブ（明るい灰色）
SLAB_GRAIN = 2.5
SLAB_RGB = tuple((a + b) / 2 for a, b in zip(SLAB_LO, SLAB_HI))     # 汚れの色を混ぜる元
_M_FILL = ("slab_fill", (0.09, 0.09, 0.09))
_M_STUD = ("slab_stud", (0.40, 0.40, 0.38))
_M_FASTENER = ("slab_fastener", (0.05, 0.05, 0.06), 0.5)
_M_BED = track_noise("slab_bed", SLAB_BED_LO, SLAB_BED_HI, SLAB_BED_GRAIN)
_M_SLAB = track_noise("slab", SLAB_LO, SLAB_HI, SLAB_GRAIN)


# ---------------------------------------------------------------- 経路の上の位置（始点からの距離）
def _lengths(path):
    return [(b - a).length for a, b in zip(path[:-1], path[1:])]


def _point(path, s):
    """始点から距離 s の点と向き（経路の外は、端の向きのまま延ばす）。"""
    lens = _lengths(path)
    acc = 0.0
    for i, L in enumerate(lens):
        if s <= acc + L or i == len(lens) - 1:
            d = (path[i + 1] - path[i]).normalized()
            return path[i] + d * (s - acc), d
        acc += L


def _slice(path, a, b):
    """経路の、距離 a〜b の部分（経路の外は延ばす）。"""
    acc, pts = 0.0, [_point(path, a)[0]]
    for i, L in enumerate(_lengths(path)[:-1]):
        acc += L
        if a < acc < b:
            pts.append(path[i + 1].copy())
    return pts + [_point(path, b)[0]]


def _tile_span(path):
    """経路のうちタイルの中にある部分の、始点からの距離 (s0, s1)。"""
    lim = TILE / 2
    acc, s0, s1 = 0.0, None, None
    for a, b, L in zip(path[:-1], path[1:], _lengths(path)):
        t0, t1 = 0.0, 1.0
        for p, q in ((a.x, b.x), (a.y, b.y)):
            d = q - p
            if abs(d) < 1e-9:
                if abs(p) > lim:
                    t0, t1 = 1.0, 0.0
                continue
            u0, u1 = sorted(((-lim - p) / d, (lim - p) / d))
            t0, t1 = max(t0, u0), min(t1, u1)
        if t0 <= t1:
            s0 = acc + t0 * L if s0 is None else s0
            s1 = acc + t1 * L
        acc += L
    return s0, s1, acc


def _even(n):
    return max(2, 2 * round(n / 2))


def _layout(path):
    """スラブの継ぎ目と締結装置の位置（始点からの距離）。どちらもタイルの辺に対して対称に置くので、隣のタイルと間隔がそろう。
    通り抜ける経路: タイルの中を等分する。継ぎ目はスラブの中ほどがタイルの辺に来る位置。
    行き止まり: 開いた側の辺から直線と同じ間隔で測る。1 タイルだけの軌道: 継ぎ目なし。"""
    s0, s1, total = _tile_span(path)
    start_in, end_in = _inner(path[0]), _inner(path[-1])
    L = s1 - s0
    if start_in and end_in:
        n = max(1, round(L / FASTENER_PITCH))
        return [], [s0 + (i + 0.5) * L / n for i in range(n)], total
    if start_in or end_in:
        # 開いた側の辺からの距離 → 始点からの距離
        at = (lambda d: s1 - d) if start_in else (lambda d: s0 + d)
        step = SLAB_PITCH / _even(SLAB_PITCH / FASTENER_PITCH)
        joints = [at((j + 0.5) * SLAB_PITCH) for j in range(int(L / SLAB_PITCH) + 1)
                  if (j + 0.5) * SLAB_PITCH < L - SLAB_END_MARGIN]
        return sorted(joints), sorted(at((i + 0.5) * step) for i in range(int(L / step + 0.5))), total
    n = max(1, math.ceil(L / SLAB_PITCH - 1e-6))
    span = L / n
    m = _even(span / FASTENER_PITCH)   # 偶数にすると、継ぎ目が締結装置の間に来る
    return ([s0 + (j + 0.5) * span for j in range(n)],
            [s0 + (i + 0.5) * span / m for i in range(n * m)], total)


def _extent(path, pad):
    """経路の端の位置: タイルの中で終わる端は pad だけ延ばし、タイルの外へ出る端はそのまま。"""
    total = sum(_lengths(path))
    return (-pad if _inner(path[0]) else 0.0), (total + pad if _inner(path[-1]) else total)


def _pieces(path, pad=SLAB_OVERHANG):
    """スラブ 1 枚ごとの経路（継ぎ目ですき間を空ける）。"""
    joints, _, _ = _layout(path)
    a, end = _extent(path, pad)
    out = []
    for j in joints:
        out.append(_slice(path, a, j - SLAB_GAP / 2))
        a = j + SLAB_GAP / 2
    return out + [_slice(path, a, end)]


def _stud_points(path):
    """突起の位置: 継ぎ目と、タイルの中で終わるスラブの端。"""
    joints, _, _ = _layout(path)
    a, b = _extent(path, SLAB_OVERHANG + SLAB_GAP / 2)
    ss = list(joints) + [s for s, inner in ((a, _inner(path[0])), (b, _inner(path[-1]))) if inner]
    return [_point(path, s)[0] for s in ss]


# ---------------------------------------------------------------- 形
def _section(u, z0, z1):
    return [(-u, z0), (u, z0), (u, z1), (-u, z1)]


def _cylinder(c, r, z0, z1):
    ring = [(c.x + r * math.cos(2 * math.pi * i / STUD_SIDES), c.y + r * math.sin(2 * math.pi * i / STUD_SIDES))
            for i in range(STUD_SIDES)]
    verts = [Vector((x, y, z)) for z in (z0, z1) for x, y in ring]
    n = STUD_SIDES
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return verts, faces


def _bed_shape(path, k):
    """コンクリート道床。行き止まりはタイルの端まで、1 タイルだけの軌道は突起の外まで敷く。"""
    edge = _edge_reach(path)
    if edge is not None:
        reach, d = edge
        pts = [path[0] - d * (reach + 0.5)] + list(path)
    else:
        pts = _slice(path, *_extent(path, SLAB_BED_PAD))
    return sweep(pts, [(-SLAB_BED_U * k, 0.0), (SLAB_BED_U * k, 0.0), (SLAB_BED_TOP_U * k, SLAB_BED_H), (-SLAB_BED_TOP_U * k, SLAB_BED_H)])


def _fill_shape(path, k):
    return sweep(_slice(path, *_extent(path, SLAB_OVERHANG)), _section((SLAB_U + SLAB_FILL_OVER) * k, SLAB_FILL_Z0, SLAB_FILL_Z1))


def _slab_shape(path, k):
    return merge([sweep(p, _section(SLAB_U * k, SLAB_Z0, SLAB_Z1)) for p in _pieces(path)])


def _notch_shape(path, k):
    pts = _stud_points(path)
    return merge([_cylinder(c, NOTCH_R, SLAB_Z1, SLAB_Z1 + NOTCH_TH) for c in pts]) if pts else None


def _stud_shape(path, k):
    pts = _stud_points(path)
    return merge([_cylinder(c, STUD_R, SLAB_BED_H / 2, STUD_TOP) for c in pts]) if pts else None


def _fastener_boxes(path, k, along, across, z, sz):
    out = []
    for s in _layout(path)[1]:
        p, d = _point(path, s)
        n = Vector((d.y, -d.x))
        for sg in (1, -1):
            c = p.to_2d() + n * (sg * RAIL_CENTRE * k)
            out.append(box(c.x, c.y, z, along, across * k, sz, rot=math.atan2(d.y, d.x)))
    return merge(out) if out else None


def _fastener_shape(path, k):
    return _fastener_boxes(path, k, FASTENER_ALONG, FASTENER_ACROSS, (FASTENER_Z0 + FASTENER_Z1) / 2, FASTENER_Z1 - FASTENER_Z0)


# 線路の部品（作る順 = 重なりの下から）。レールは在来線の部品そのもの
SLAB_TRACK_PARTS = (
    Part("slab_bed", "slab_bed", "bed", _M_BED, _bed_shape),
    Part("slab_fill", "rail", "gauge", _M_FILL, _fill_shape),
    Part("slab", "rail", "gauge", _M_SLAB, _slab_shape),
    Part("slab_notch", "rail", "gauge", _M_FILL, _notch_shape, centre=False),
    Part("slab_stud", "rail", "gauge", _M_STUD, _stud_shape, centre=False),
    Part("slab_fastener", "rail", "gauge", _M_FASTENER, _fastener_shape),
) + tuple(p for p in TRACK_PARTS if p.name in ("railL", "railR"))

# 分岐のすき間埋め（TRACK_PROFILES の "bed_fills"）: 部品の名前 → (上面の半幅, 板の下面の高さ, 板の上面の高さ)。
# 埋めるのはコンクリート道床だけ（スラブまで埋めると、経路の間が大きな明るい三角になる）
SLAB_BED_FILLS = {"slab_bed": (SLAB_BED_TOP_U, 0.001, SLAB_BED_H - 0.003)}


# ---------------------------------------------------------------- 汚れ（在来線の汚れと同じ名前で差し替える。雪の絵の材質 TRACK_SNOW_WEAR_SKIN がそのまま効く）
# スラブの上面に乗せ、スラブの縁と継ぎ目で止める。色はスラブの色から混ぜる。締結装置の下に入る
WEAR_Z_STEP = 0.0015
WEAR_TH = 0.001
WEAR_EDGE = 0.05          # スラブの縁から空ける幅
FASTENER_RUST_OVER = 0.07  # 締結装置のさびが装置の周りに広がる幅
FASTENER_RUST_T = 0.45, 0.30   # 締結装置のさびの、さび色への寄せ具合（暗い側・明るい側）
SLAB_WEAR_K = 0.75        # 明るいスラブの上で帯が強く見えすぎないよう、在来線の寄せ具合に掛ける
# 帯の位置（部品の名前 → 経路の中心からの (u0, u1)）。在来線より狭く、スラブの大部分はきれいなまま残す
SLAB_WEAR_BANDS = {"rust0": (RAIL_IN - 0.10, RAIL_OUT + 0.18), "rust1": (RAIL_IN - 0.04, RAIL_OUT + 0.08), "oil": (0.0, 0.14)}


def _wear_z(i):
    return SLAB_Z1 + WEAR_Z_STEP * (i + 1)


def _clamp_u(u):
    return min(u, SLAB_U - WEAR_EDGE)


def _wear_band_shape(u0, u1, z):
    """レールの両脇の帯（左右 2 本）。"""
    u1 = _clamp_u(u1)

    def shape(path, k):
        return merge([sweep(p, [(s * u0 * k, z), (s * u1 * k, z), (s * u1 * k, z + WEAR_TH), (s * u0 * k, z + WEAR_TH)][::s])
                      for p in _pieces(_trim_inner_ends(path), 0.0) for s in (1, -1)])
    return shape


def _wear_centre_shape(u, z):
    """レールの間の、中心をまたぐ 1 本の帯。"""
    def shape(path, k):
        return merge([sweep(p, _section(u * k, z, z + WEAR_TH)) for p in _pieces(_trim_inner_ends(path), 0.0)])
    return shape


def _fastener_rust_shape(z):
    def shape(path, k):
        return _fastener_boxes(path, k, FASTENER_ALONG + 2 * FASTENER_RUST_OVER, FASTENER_ACROSS + 2 * FASTENER_RUST_OVER, z + WEAR_TH / 2, WEAR_TH)
    return shape


def _slab_wear_parts():
    by_name = {p.name: p for p in TRACK_EXTRAS}
    out = {}
    for i, (name, _, (lo, hi), t, _) in enumerate(TRACK_WEAR):
        u0, u1 = SLAB_WEAR_BANDS[name]
        t *= SLAB_WEAR_K
        z = _wear_z(i)
        form = _wear_centre_shape(u1, z) if name == "oil" else _wear_band_shape(u0, u1, z)
        out[name] = replace(by_name[name], material=track_noise(f"slab_{name}", _mix(SLAB_RGB, lo, t), _mix(SLAB_RGB, hi, t), 3.0), shape=form)
    out["sleeper_rust"] = replace(
        by_name["sleeper_rust"],
        material=track_noise("slab_fastener_rust", _mix(SLAB_RGB, _RUST_LO, FASTENER_RUST_T[0]), _mix(SLAB_RGB, _RUST_HI, FASTENER_RUST_T[1]), 4.0),
        shape=_fastener_rust_shape(_wear_z(len(TRACK_WEAR))))
    return out


# TRACK_PROFILES の "replace" に渡す（在来線のまくらぎのさびは、締結装置の周りのさびになる）
SLAB_WEAR_REPLACE = _slab_wear_parts()

# 雪の絵（TRACK_PROFILES の "snow_skin"）: 道床とスラブは雪をかぶる。締結装置・突起は雪の上に少し見える
SLAB_SNOW_SKIN = {
    "slab_bed": _SNOW,
    "slab_fill": _SNOW,
    "slab": _SNOW,
    "slab_notch": _SNOW,
    "slab_stud": ("snow_slab_stud", (0.80, 0.84, 0.90), 0.9),
    "slab_fastener": ("snow_slab_fastener", (0.62, 0.65, 0.70), 0.9),
}
