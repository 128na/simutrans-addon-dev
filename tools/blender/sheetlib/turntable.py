"""転車台・遷車台の way のシート（AMI の ami_rail_turntable。#314）。

手本は iss の転車台とトラバーサー（../refs/iss/src/util/rail_misc/table.dat）。本体での種類は道路（waytype=road）の way で、
回る動きは無い。本体は way の絵を、つながる向き（ribi）だけで選ぶ（descriptor/way_desc.h の get_image_id）。なので 1 つの way で
    つながりが無い（image[-]）: 転車台（丸いピットに、東西に渡した桁。桁の西の端に運転室）
    直線・行き止まり: 遷車台（つながる向きに延びるピット。床に台車の走るレール）。北・西の端（image[s]・[e]）に台車を置く
    カーブ・T 字・十字: 遷車台のピットの分かれ目（床にレールを両方の向きに。閉じた辺は壁）
を描く。線路とはつながらない（線路の行き止まりの隣に置く。線路を横切らせると踏切になる。#314 の PR に試しの結果）。
iss はカーブ・T 字の絵を持たず、敷くと見えない way が残るので、AMI はピットの分かれ目を描く。坂の絵は持たない（iss と同じ）。

ピットは地面より PIT_D 低い床と、閉じた辺の壁（上面に黄色の縁）。床は開いた辺でタイルの外へ延ばし（持ち分で切る）、隣のタイルの床と続ける。
床は地面より下なので、画面では下へずれる。手前（南・東）の辺の外へ出た分は持ち分で切れ、隣のタイルが描く。
桁・台車の上の線路は、AMI の線路の way と同じ基準面（datums["rail"]）で動かし、レールの横の範囲と高さ（rail）も線路にそろえる。
全部を奥の絵（image）にし、手前の絵（frontimage）は持たない（iss は奥と手前に同じ絵を置いていた。上に乗る乗り物が無いので要らない）。

シートの並び（ami_dat.py の IMAGES と同じ位置。行 0〜3 が夏、雪の絵は sheet_rows.WAY_SNOW_ROWS 下）:
    行 0: 列 0 アイコン、列 1 カーソル（AMI の blender/icons.py が描き直す）、列 2・3 南北・東西、列 5〜8 行き止まり s・w・n・e、列 9 転車台（-）
    行 2: 列 5〜8 カーブ sw・nw・ne・se、行 3: 列 5〜8 T 字 nse・new・nsw・sew、列 9 十字
"""
import math
import os

import numpy as np
from mathutils import Vector

from sheet_rows import WAY_SNOW_ROWS  # 雪の絵の行のずらし。dat を書く側（ami_dat.py）も同じ定義を読む

from . import sheetlib as _s
from .cells import GROUND_CY, _ground_mask, exits_of, make_sheet, render_cell, save_rgba
from .core import SCALE, TILE, _SNOW, box, clear_models, datum_move, make_material, merge, mesh_object, set_anchor

# ---- 寸法（タイル 1 辺 = 10。高さ 1 段は H ≈ 2.04 で、画面の 16px。1px ≈ 0.13）
PIT_D = 0.5              # ピットの深さ（約 4px）
PIT_PAD = 1.0            # 開いた辺で、床をタイルの外へ延ばす量（持ち分で切る）
WALL_T = 0.3             # 閉じた辺の壁の厚み（タイルの辺から内へ）
COPING_W = 0.36          # 壁・ピットの縁の黄色の帯の幅（約 2.6px。実寸の 0.18 は約 1.3px でまわりに埋もれたので誇張した。#331 の 1cp）
COPING_H = 0.03          # 黄色の帯の厚み
FLOOR_T = 0.1            # 床の板の厚み
# 遷車台の床の、台車の走るレール（ピットに沿う 2 本。iss と同じくタイルの中心から左右に）
TRAV_RAIL_U = 2.6        # タイルの中心からの距離
TRAV_RAIL = (0.16, 0.12)  # レールの幅・高さ
# 遷車台の台車（ピットを横切る向きに線路を載せる。北・西の端のタイルに置く）
CAR_HALF_W = 1.4         # 台車の幅の半分（ピットに沿う向き）
CAR_GAP = 0.1            # 台車の端と壁の内の面とのすき間
CAR_HUT = (1.0, 0.9, 1.0)   # 運転室（台車を横切る向きの長さ・沿う向きの長さ・高さ）
CAR_HUT_ROOF = 0.12      # 運転室の屋根の厚み（運転室より少し大きい）
# 転車台
TT_R = 4.6               # ピットの半径
TT_SEG = 96              # 円を分ける数
TT_RING_R = TT_R - 0.45  # ピットの床の、桁の端の車輪が走る円のレールの半径
TT_PIVOT_R = 0.45        # 中心の支点の半径
TT_BRIDGE_HALF = 1.25    # 桁の幅の半分
TT_BRIDGE_END = TT_R - 0.12  # 桁の端（中心から）
TT_HUT = (0.9, 0.9, 1.0)    # 運転室（桁に沿う向きの長さ・横切る向きの長さ・高さ）
TT_APRON_W = 0.9         # まわりのコンクリートの輪の幅（ピットの縁から。#331 の 2ringd。タイルいっぱいの四角は草の中で浮いたので、角は地面を見せる）
HUT_WINDOW = (0.25, 0.55)  # 運転室の窓の暗い帯（高さ、帯の下の端の高さ ÷ 運転室の高さ。#331 の 2win。転車台・遷車台の両方）
# 線路（桁・台車の上）: まくらぎ（長さ・幅・高さ）と間隔。canal_crossing の線路の床と同じ作り
SLEEPER = (2.4, 0.22, 0.14)
SLEEPER_STEP = 0.65
DECK_UNDER = 0.12        # 線路のまくらぎの下面から、桁・台車の上面までの下げ（まくらぎを載せる板の厚み）
# 持ち分を上へ広げる行数（運転室の高さ 約 8px と屋根・まくらぎ・レールに余り）
TURNTABLE_RISE = 14 * SCALE

_M_APRON = ("turntable_apron", (0.60, 0.60, 0.58), 0.85)      # 転車台のまわりのコンクリート
_M_FLOOR = ("turntable_floor", (0.47, 0.47, 0.46), 0.9)       # ピットの床
_M_WALL = ("turntable_wall", (0.56, 0.56, 0.54), 0.85)        # ピットの壁
_M_COPING = ("turntable_coping", (0.86, 0.74, 0.22), 0.5)     # 縁の黄色の帯（操車場の柵と同じ黄色）
_M_BRIDGE = ("turntable_bridge", (0.30, 0.36, 0.30), 0.6)     # 転車台の桁（濃い緑に塗った鋼。iss の緑の桁に寄せた）
_M_CARRIAGE = ("turntable_carriage", (0.70, 0.30, 0.12), 0.6)  # 遷車台の台車（橙に塗った鋼。iss と同じ色の向き）
_M_HUT = ("turntable_hut", (0.78, 0.78, 0.75), 0.8)           # 運転室の壁
_M_HUT_ROOF = ("turntable_hut_roof", (0.34, 0.35, 0.37), 0.7)  # 運転室の屋根
_M_PIVOT = ("turntable_pivot", (0.36, 0.36, 0.36), 0.6)       # 中心の支点
_M_SLEEPER = ("turntable_sleeper", (0.16, 0.11, 0.07), 0.9)   # まくらぎ（木）
_M_SLEEPER_SNOW = ("turntable_sleeper_snow", (0.80, 0.84, 0.90), 0.9)
_M_RAIL = ("turntable_rail", (0.92, 0.91, 0.88), 0.4)         # レールの頭（AMI の線路と同じ色）
_M_RAIL_SIDE = ("turntable_rail_side", (0.25, 0.18, 0.13), 0.6)  # レールの腹（さび）
# ピットの床の、台車・桁の車輪が走るレール（ゆっくり動くだけで磨かれない。画面で約 1px の幅なので、頭と腹を分けず 1 色）
_M_FLOOR_RAIL = ("turntable_floor_rail", (0.30, 0.26, 0.22), 0.5)
_M_HUT_WINDOW = ("turntable_hut_window", (0.10, 0.12, 0.15), 0.3)  # 運転室の窓

# 材質の差し替え（turntable_sheet の skin。材質の名前（_M_* の先頭）→ 材質を返す関数）。汚し（#331）はアドオンが渡す
_skin = {}

# セル（行, 列）→ 名前（cells の exits_of で、つながる辺に直せる名前）。"single" はつながりが無い（転車台）
TURNTABLE_CELLS = {
    (0, 2): "ns", (0, 3): "ew", (0, 5): "s", (0, 6): "w", (0, 7): "n", (0, 8): "e", (0, 9): "single",
    (2, 5): "curve_sw", (2, 6): "curve_nw", (2, 7): "curve_ne", (2, 8): "curve_se",
    (3, 5): "nse", (3, 6): "new", (3, 7): "nsw", (3, 8): "sew", (3, 9): "nsew",
}
TURNTABLE_CAR_CELLS = ("s", "e")  # 台車を置く行き止まり（北・西の端のタイル。iss と同じ）


def _obj(name, parts, spec):
    if not parts:
        return None
    return mesh_object(name, *merge(parts), make_material(_skin.get(spec[0], spec), spec[0]))


# ---------------------------------------------------------------- 線路（桁・台車の上）
def _track(axis, a, b, top, snow, rail):
    """axis（"x" か "y"）に沿って a〜b の範囲に、まくらぎとレールを置く。top はまくらぎの下面の高さ。
    rail は AMI の線路のレール (内側, 外側, 上面)。部品（頂点, 面）の組を材質ごとに返す"""
    sleepers, webs, heads = [], [], []
    n = max(1, round(abs(b - a) / SLEEPER_STEP))
    for i in range(n):
        s = a + (b - a) * (i + 0.5) / n
        if axis == "x":
            sleepers.append(box(s, 0, top + SLEEPER[2] / 2, SLEEPER[1], SLEEPER[0], SLEEPER[2]))
        else:
            sleepers.append(box(0, s, top + SLEEPER[2] / 2, SLEEPER[0], SLEEPER[1], SLEEPER[2]))
    r_in, r_out, r_top = rail
    z_web0, z_head0 = top + SLEEPER[2], r_top - 0.02
    for sgn in (-1, 1):
        u = sgn * (r_in + r_out) / 2
        w = r_out - r_in
        mid, ln = (a + b) / 2, abs(b - a)
        for lst, z0, z1 in ((webs, z_web0, z_head0), (heads, z_head0, r_top)):
            if axis == "x":
                lst.append(box(mid, u, (z0 + z1) / 2, ln, w, z1 - z0))
            else:
                lst.append(box(u, mid, (z0 + z1) / 2, w, ln, z1 - z0))
    return {"sleeper": sleepers, "web": webs, "head": heads}


def _track_objs(prefix, parts, snow):
    return [ob for ob in (
        _obj(prefix + "_sleeper", parts["sleeper"], _M_SLEEPER_SNOW if snow else _M_SLEEPER),
        _obj(prefix + "_rail_web", parts["web"], _M_RAIL_SIDE),
        _obj(prefix + "_rail_head", parts["head"], _M_RAIL),
    ) if ob is not None]


def _deck_top(rail):
    """桁・台車の上面の高さ（まくらぎの下面から DECK_UNDER 下）"""
    return rail[2] - 0.02 - SLEEPER[2] - DECK_UNDER


def _hut(cx, cy, sx, sy, sz, z0, snow):
    """運転室（箱と、少し大きい屋根と、4 面に回した窓の暗い帯。窓は壁より 0.02 外へ出した薄い箱）"""
    walls = _obj("turntable_hut", [box(cx, cy, z0 + sz / 2, sx, sy, sz)], _M_HUT)
    roof = _obj("turntable_hut_roof", [box(cx, cy, z0 + sz + CAR_HUT_ROOF / 2, sx + 0.16, sy + 0.16, CAR_HUT_ROOF)],
                _SNOW if snow else _M_HUT_ROOF)
    wh, wz = HUT_WINDOW
    window = _obj("turntable_hut_window", [box(cx, cy, z0 + sz * wz + wh / 2, sx + 0.04, sy + 0.04, wh)], _M_HUT_WINDOW)
    return [walls, roof, window]


# ---------------------------------------------------------------- 遷車台（ピット）
def _pit(exits, snow):
    """遷車台のピット: 床（開いた辺でタイルの外へ延ばす）・閉じた辺の壁と黄色の縁・床のレール"""
    half = TILE / 2
    ext = {d: half + PIT_PAD if d in exits else half for d in "nsew"}
    x0, x1, y0, y1 = -ext["w"], ext["e"], -ext["s"], ext["n"]
    floor = [box((x0 + x1) / 2, (y0 + y1) / 2, -PIT_D - FLOOR_T / 2, x1 - x0, y1 - y0, FLOOR_T)]
    walls, coping = [], []
    for d in "nsew":
        if d in exits:
            continue
        # 壁はタイルの辺から内へ WALL_T。両端は隣の辺が開いていればタイルの外へ延ばす（隣のタイルの壁と続く）
        if d in "ns":
            sgn = 1 if d == "n" else -1
            a, b = -ext["w"], ext["e"]
            cy = sgn * (half - WALL_T / 2)
            walls.append(box((a + b) / 2, cy, -PIT_D / 2, b - a, WALL_T, PIT_D))
            coping.append(box((a + b) / 2, sgn * (half - COPING_W / 2), COPING_H / 2, b - a, COPING_W, COPING_H))
        else:
            sgn = 1 if d == "e" else -1
            a, b = -ext["s"], ext["n"]
            cx = sgn * (half - WALL_T / 2)
            walls.append(box(cx, (a + b) / 2, -PIT_D / 2, WALL_T, b - a, PIT_D))
            coping.append(box(sgn * (half - COPING_W / 2), (a + b) / 2, COPING_H / 2, COPING_W, b - a, COPING_H))
    # 床のレール: 南北に開いていれば南北に、東西に開いていれば東西に、それぞれ 2 本（閉じた辺では壁の内の面まで）
    rails = []
    rw, rh = TRAV_RAIL
    zc = -PIT_D + rh / 2
    lim = {d: (half + PIT_PAD if d in exits else half - WALL_T) for d in "nsew"}
    if any(d in exits for d in "ns"):
        a, b = -lim["s"], lim["n"]
        rails += [box(u, (a + b) / 2, zc, rw, b - a, rh) for u in (-TRAV_RAIL_U, TRAV_RAIL_U)]
    if any(d in exits for d in "ew"):
        a, b = -lim["w"], lim["e"]
        rails += [box((a + b) / 2, u, zc, b - a, rw, rh) for u in (-TRAV_RAIL_U, TRAV_RAIL_U)]
    obs = [_obj("turntable_floor", floor, _SNOW if snow else _M_FLOOR),
           _obj("turntable_wall", walls, _M_WALL),
           _obj("turntable_coping", coping, _M_COPING),
           _obj("turntable_floor_rail", rails, _M_FLOOR_RAIL)]
    return [ob for ob in obs if ob is not None]


def _carriage(snow, rail):
    """遷車台の台車。ピットが南北（南へ続き、北が閉じた行き止まり）の向きで作る。台車は東西の壁の間いっぱいに渡し、
    上に東西の線路を載せる（両脇の線路のタイルとつなぐ）。運転室は西の端の北の側"""
    half = TILE / 2
    xa, xb = -(half - WALL_T - CAR_GAP), half - WALL_T - CAR_GAP
    top = _deck_top(rail)
    z0 = -PIT_D + TRAV_RAIL[1]
    body = [box((xa + xb) / 2, 0, (z0 + top) / 2, xb - xa, 2 * CAR_HALF_W, top - z0)]
    hx, hy, hz = CAR_HUT
    # 運転室を載せる張り出し（台車の北の縁から）
    px0 = xa
    body.append(box(px0 + hx / 2 + 0.1, CAR_HALF_W + hy / 2, (z0 + top) / 2, hx + 0.2, hy, top - z0))
    obs = [_obj("turntable_carriage", body, _M_CARRIAGE)]
    obs += _track_objs("turntable_car", _track("x", xa, xb, top, snow, rail), snow)
    obs += _hut(px0 + hx / 2 + 0.1, CAR_HALF_W + hy / 2, hx, hy, hz, top, snow)
    return [ob for ob in obs if ob is not None]


# ---------------------------------------------------------------- 転車台
def _circle(r, n=TT_SEG):
    return [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _ring_faces(n):
    return [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]


def _apron(z):
    """ピットの縁（半径 TT_R）から TT_APRON_W の輪の面（高さ z）。輪の外（タイルの角）は地面が見える"""
    n = TT_SEG
    inner = [Vector((x, y, z)) for x, y in _circle(TT_R, n)]
    outer = [Vector((x, y, z)) for x, y in _circle(TT_R + TT_APRON_W, n)]
    return inner + outer, [tuple(reversed(f)) for f in _ring_faces(n)]


def _flat_ring(r0, r1, z0, z1):
    """厚みのある輪（内の半径 r0・外 r1、高さ z0〜z1）。上面と内・外の側面"""
    n = TT_SEG
    verts, faces = [], []
    for r, z in ((r0, z1), (r1, z1), (r0, z0), (r1, z0)):
        verts += [Vector((x, y, z)) for x, y in _circle(r, n)]
    top_in, top_out, bot_in, bot_out = 0, n, 2 * n, 3 * n
    for i in range(n):
        j = (i + 1) % n
        faces.append((top_in + i, top_out + i, top_out + j, top_in + j))
        faces.append((top_out + i, bot_out + i, bot_out + j, top_out + j))
        faces.append((bot_in + i, top_in + i, top_in + j, bot_in + j))
    return verts, faces


def _cylinder(r, z0, z1, n=TT_SEG):
    pts = _circle(r, n)
    verts = [Vector((x, y, z0)) for x, y in pts] + [Vector((x, y, z1)) for x, y in pts]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return verts, faces


def _turntable(snow, rail):
    """転車台: まわりのコンクリート・丸いピット（壁・床・円のレール・支点）・東西に渡した桁と線路・運転室"""
    apron = _apron(0.0)
    # ピットの壁（円筒の内の面）: 上の縁から床まで
    n = TT_SEG
    pts = _circle(TT_R, n)
    wall_v = [Vector((x, y, 0.0)) for x, y in pts] + [Vector((x, y, -PIT_D)) for x, y in pts]
    wall = (wall_v, [(i, n + i, n + (i + 1) % n, (i + 1) % n) for i in range(n)])
    floor = _cylinder(TT_R + 0.05, -PIT_D - FLOOR_T, -PIT_D)
    coping = _flat_ring(TT_R, TT_R + COPING_W, 0.0, COPING_H)
    ring_rail = _flat_ring(TT_RING_R - TRAV_RAIL[0] / 2, TT_RING_R + TRAV_RAIL[0] / 2, -PIT_D, -PIT_D + TRAV_RAIL[1])
    pivot = _cylinder(TT_PIVOT_R, -PIT_D, -PIT_D + 0.15, 32)
    obs = [_obj("turntable_apron", [apron], _SNOW if snow else _M_APRON),
           _obj("turntable_wall", [wall], _M_WALL),
           _obj("turntable_floor", [floor], _SNOW if snow else _M_FLOOR),
           _obj("turntable_coping", [coping], _M_COPING),
           _obj("turntable_ring_rail", [ring_rail], _M_FLOOR_RAIL),
           _obj("turntable_pivot", [pivot], _M_PIVOT)]
    # 桁（東西）と線路。両端は円のレールに載る（下端はピットの床の上）
    top = _deck_top(rail)
    z0 = -PIT_D + TRAV_RAIL[1]
    bridge = [box(0, 0, (z0 + top) / 2, 2 * TT_BRIDGE_END, 2 * TT_BRIDGE_HALF, top - z0)]
    hx, hy, hz = TT_HUT
    hcx, hcy = -TT_BRIDGE_END + hx / 2 + 0.25, TT_BRIDGE_HALF + hy / 2
    bridge.append(box(hcx, hcy, (z0 + top) / 2, hx + 0.2, hy, top - z0))  # 運転室を載せる張り出し（北の側）
    moving = [_obj("turntable_bridge", bridge, _M_BRIDGE)]
    moving += _track_objs("turntable_tt", _track("x", -TT_BRIDGE_END, TT_BRIDGE_END, top, snow, rail), snow)
    moving += _hut(hcx, hcy, hx, hy, hz, top, snow)
    return [ob for ob in obs if ob is not None], [ob for ob in moving if ob is not None]


# ---------------------------------------------------------------- シート
def _own(cname):
    """持ち分: 地面の菱形（GROUND_CY）を上へ TURNTABLE_RISE 行広げる"""
    m = _ground_mask(None, None, GROUND_CY)
    base = m.copy()
    for k in range(1, TURNTABLE_RISE + 1):
        m[:-k] |= base[k:]
    own = m.astype(np.uint8) * 255
    save_rgba(os.path.join(_s.WORK, cname + "_own.png"), np.dstack([own, own, own, np.full_like(own, 255)]))


def _build(name, snow, datums, rail):
    """セル 1 枚の形を作る。
    遷車台の台車は、上の線路が両脇の線路のタイルのレールと画面で一直線になるよう、線路の基準面（datums["rail"]）の動かし方のうち、
    台車の線路に直角な向きの成分だけ動かす（ピットに沿って動くだけなので、台車は壁の間に収まったまま。線路に沿う成分は線を動かさない）。
    転車台は動かさない（ピットと桁をタイルの中心に置く。動かすと桁がピットの中心から外れる。線路とは車止めをはさんでつながらない）"""
    clear_models()
    exits = exits_of(name)
    if name == "single":
        fixed, moving = _turntable(snow, rail)
        return fixed + moving
    fixed = _pit(exits, snow)
    if name not in TURNTABLE_CAR_CELLS:
        return fixed
    moving = _carriage(snow, rail)
    move = datum_move(datums["rail"])
    ew_pit = name == "e"
    if ew_pit:  # 東西のピット（東へ続く西の端）: 南北の向きで作った台車を 90 度回す（南 → 東）。台車の線路は南北
        for ob in moving:
            ob.rotation_euler.z = math.radians(90)
    if move is not None:
        shift = Vector((move.x, 0, 0)) if ew_pit else Vector((0, move.y, 0))
        for ob in moving:
            ob.location += shift
    return fixed + moving


def turntable_sheet(sheet, datums, rail, label="T", skin=None):
    """転車台・遷車台の way のシート。datums・rail は線路の way の基準面とレール (内側, 外側, 上面)（canal_crossing と同じ渡し方）。
    skin は材質の差し替え（材質の名前 → 材質を返す関数。汚し。#331）"""
    if rail is None or len(rail) != 3:
        raise SystemExit("[turntable] rail（内側, 外側, 上面）が要る")
    _skin.clear()
    _skin.update(skin or {})
    set_anchor(GROUND_CY)  # 線路と同じ位置（dat のオフセット -64,-32）。桁・台車の上の線路を、線路のタイルのレールとそろえる
    cells = {}
    for snow in (False, True):
        for (r, c), name in TURNTABLE_CELLS.items():
            cname = f"{sheet}_{'snow_' if snow else ''}{name}"
            _build(name, snow, datums, rail)
            cells[(r + (WAY_SNOW_ROWS if snow else 0), c)] = render_cell(cname)
            _own(cname)
    _build("single", False, datums, rail)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style="track")
    cells[(0, 1)] = cells[(0, 9)]
    make_sheet(cells, 2 * WAY_SNOW_ROWS, 10, os.path.join(_s.SRC, sheet + ".png"))
