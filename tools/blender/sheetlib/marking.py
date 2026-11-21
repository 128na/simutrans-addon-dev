"""交差点の路面表示の way（waytype=tram_track。AMI #156）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

道路の上に重ねて敷く路面軌道の way の絵で、白線だけを描く（路面は描かない。下の道路の絵が見える）。
iss の util/road_misc/intersection.dat と同じく、交差点と、その周りの 2 マスだけに使う（その先の道路には被せない）。
道幅・中央線・出る側の車線は変えず、入る側の道幅の中で右折車線を 1 本増やす（2026-11-22、ユーザーの決定。#156）:
  1 マス目（口。交差点の隣）: 車線の境を実線で引き（車線変更できない）、矢印・停止線・横断歩道を描く
  2 マス目（導流帯。口の手前）: 右折車線の遠い端にゼブラの三角を置き、三角の先から右折車線の境を破線で引く（車線変更できる）
役割は way の名前とつながる形で決める（最後に敷いた way の名前がタイルに残り、つながる向きは足される。
1 タイルだけ敷くと、向きはそのままで名前だけが置き換わる。docs/reference/way-addon.md）:
  taper:          2 車線の 2 マス目。行き止まり（向きが交差点の側）
  stop:           2 車線の 1 マス目。行き止まり（向きが 2 マス目の側。交差点はその反対）
  stop_wide:      4 車線（AMI #121 の lane の版の 1・2）の入る側。行き止まり（向きが交差点の側）が 2 マス目、
                  曲がり（2 マス目の側と、進む向きの右の出る側の 1 マス目）が 1 マス目
  crosswalk_wide: 4 車線の出る側の 1 マス目。行き止まり（向きが入る側の 1 マス目。進む向きの左）に横断歩道だけ
  ほかの形と、上に無い組: 何も描かない
敷き方（ingame/marking_sample.nut の approach と同じ。README の「交差点の路面表示の作り」）:
  2 車線: 1. 2 マス目から 1 マス目へ taper  2. 1 マス目だけに stop（1 回クリック）
  4 車線: 1. 出る側の 1 マス目から入る側の 1 マス目へ crosswalk_wide  2. 2 マス目から入る側の 1 マス目へ stop_wide
路側帯（路側線の外）には、どの種類も横断歩道と停止線を描かない（2026-11-22、ユーザーの指摘。#156）
位置と幅は道路の白線（road_parts の EDGE_LINE・LINE_W・LINE_TOP・STOP_LINE_W）に合わせる。雪の絵は持たない（道路は車道を除雪した想定で、
車道の白線は夏と同じ。dat は雪の絵に夏のセルを使う）。坂・斜めの絵は持たない（交差点は平らな所に作る）
"""
import math
import os

from . import sheetlib as _s
from .cells import ROAD_CY, make_sheet, render_cell
from .core import clear_models, material, mesh_object, set_anchor, TILE
from .road_parts import EDGE_LINE, LINE_TOP, LINE_W, STOP_LINE_W

# ---------------------------------------------------------------- 寸法（部品の 1 単位 ≈ 1 m。道路の車線は 1 本 約 3.4）
# 位置は、交差点の向き a の座標で、u（a の向き。タイルの中心が 0、交差点の側の辺が +5）と v（a の左を正）で表す
MARKING_HALF = TILE / 2
MARKING_CROSSWALK_NEAR = 1.5   # 横断歩道の帯の、タイルの中心の側の端（タイルの中心から交差点の向きへ）
MARKING_CROSSWALK_FAR = 4.5    # 横断歩道の帯の、交差点の側の端（タイルの辺 5 の 0.5 手前）
MARKING_STRIPE_W = 0.5         # 横断歩道の縞の幅（縞のあいだも同じ幅。周期 1.0 で、隣のタイルの縞と同じ並びになる）
# 縞の中心の横位置。どれも路側線（±EDGE_LINE）の内に収める。周期 1.0 で、4 車線の入る側と出る側の縞は、2 タイルの境（中央線）を
# またいで同じ並びになる
MARKING_STRIPES = {"narrow": [i - 3.0 for i in range(7)],      # 2 車線: 路側線の内に 7 本
                   "wide_in": [i - 4.5 for i in range(8)],     # 4 車線の入る側: 中央線の側の辺（-5）から左の路側線の内まで 8 本
                   "wide_out": [i - 2.5 for i in range(8)]}    # 4 車線の出る側: 右の路側線の内から中央線の側の辺（+5）まで 8 本
MARKING_STOP_U = 0.6           # 停止線の中心（タイルの中心から交差点の向きへ。横断歩道の帯の手前）
MARKING_STOP_BACK = MARKING_STOP_U - STOP_LINE_W / 2  # 停止線の手前の縁。車線の線はここで止める
MARKING_Z = (0.0, LINE_TOP + 0.004)  # 白線の下面・上面（道路の白線より少しだけ上）
MARKING_DRIVE_LEFT = True      # 左側通行（日本）。右側通行の版は作らない（2026-11-22、ユーザーの決定）
MARKING_STOP_END = EDGE_LINE - LINE_W / 2  # 停止線の路側の端: 路側線の内の縁まで（路側帯へ出さない）
# 入る側の車線の境（v）: (中央線, 右折車線の境, 直進と左折の境, 路側線)。中央線と路側線は道路の線のまま（描かない）。
#   2 車線: 中央線 0 から路側線までの入る側の半分を 2 等分する（右折と、左折・直進）。道路の線は真ん中に無いので、境は新しく引く
#   4 車線: 中央線（タイルの辺 -5）から 2.5 に右折車線の境を足す。直進と左折の境は道路の車線の境（0。破線）のまま使い、1 マス目だけ実線で重ねる
MARKING_LANES = {"stop": (0.0, EDGE_LINE / 2, None, EDGE_LINE),
                 "stop_wide": (-MARKING_HALF, -MARKING_HALF + 2.5, 0.0, EDGE_LINE)}
MARKING_GEOMETRY = {"stop": "stop", "taper": "stop", "stop_wide": "stop_wide"}
# ゼブラの三角（2 マス目）: 右折車線の遠い端（u = -5）に、中央線の側から右折車線の境までの幅の辺を置き、交差点の向きへ MARKING_TRI_LEN で
# 中央線の側へ細くなる。縞は線に 45° の向きで、間隔（縞に直角に測る）と幅。縞の端は三角の線の内の縁で切る
MARKING_TRI_LEN = 3.0
MARKING_ZEBRA_STEP = 0.6
MARKING_ZEBRA_W = 0.25
MARKING_ZEBRA_MIN = 0.2        # これより短い縞（三角の先の細い所）は描かない
# 2 マス目の右折車線の境の破線: 道路の中央線の破線（road_parts の CENTER_DASHES・CENTER_DASH_FRAC）と同じ周期と位置
MARKING_DASHES = 4
MARKING_DASH_FRAC = 0.5
# 矢印（車線の中心 c から）: 軸の幅、軸の始まり（u）、直進の矢じりの付け根と先、曲がる矢印の横の軸の位置（u）と、矢じりの幅と長さ
MARKING_ARROW = dict(shaft_w=0.3, u0=-4.4, head_base=-2.6, head_tip=-1.4, head_w=1.0,
                     turn_u=-3.2, turn_len=0.5, turn_head=0.5, turn_head_w=0.9, shift=0.3)
# 白の材質: 道路の白線（road_parts の _M_LINE。幅 1px で、ゲームの画面では路面と混ざって灰色がかって見える）と同じ明るさに見えるよう、
# 面で描く表示は色と発光を落とす。値は、ゲームの画面（拡大率 1）で道路の白線の画素の平均と、横断歩道の縞の画素の平均を比べて決めた
MARKING_LINE = ("marking_line", (0.80, 0.80, 0.82), 0.6, 0.0, 0.35)

# 種類 → 横断歩道の並び（1 マス目）
MARKING_KINDS = {"stop": "narrow", "taper": None, "stop_wide": "wide_in", "crosswalk_wide": "wide_out"}
# セル（行, 列）→ 形。位置は線路の way と同じ（ami_dat.py の IMAGES の image[s] など）
MARKING_DEADENDS = {(0, 5): (0, -1), (0, 6): (-1, 0), (0, 7): (0, 1), (0, 8): (1, 0)}  # 行き止まり → つながる向き
MARKING_CURVES = {(2, 5): "sw", (2, 6): "nw", (2, 7): "ne", (2, 8): "se"}
MARKING_EMPTY_CELL = (0, 9)    # ほかの形（直線・T字・十字・1 タイル）と、描かない形が使う空のセル
_DIRS = {"n": (0, 1), "e": (1, 0), "s": (0, -1), "w": (-1, 0)}


def marking_curve_dir(kind, curve):
    """曲がりの形 → 1 マス目の交差点の向き a（描かない種類・形は None）。
    stop_wide の 1 マス目は、交差点と反対（2 マス目）と進む向きの右（出る側の 1 マス目）につながる"""
    if kind != "stop_wide":
        return None
    d1, d2 = (_DIRS[c] for c in curve)
    for x, y in ((d1, d2), (d2, d1)):
        a = (-x[0], -x[1])  # x が交差点と反対（2 マス目）、y が進む向きの右
        if y == (a[1], -a[0]):
            return a
    return None


def marking_deadend(kind, d):
    """行き止まり（つながる向き d）→ (描くもの, 交差点の向き a) か None。
    taper・stop_wide は 2 マス目（d が交差点）、stop は 1 マス目（d が 2 マス目）、crosswalk_wide は出る側の 1 マス目（d が進む向きの左）"""
    if kind in ("taper", "stop_wide"):
        return "taper", d
    if kind == "stop":
        return "mouth", (-d[0], -d[1])
    if kind == "crosswalk_wide":
        return "mouth", (d[1], -d[0])  # 左が d になる向き
    return None


# ---------------------------------------------------------------- 形
def _prism(name, a, pts, mat, z=MARKING_Z):
    """交差点の向き a（単位ベクトル）の座標で、(u, v) の凸の多角形 pts を z の厚さの板にする"""
    ax, ay = a
    sx, sy = -ay, ax
    xy = [(ax * u + sx * v, ay * u + sy * v) for u, v in pts]
    area = sum(xy[i][0] * xy[(i + 1) % len(xy)][1] - xy[(i + 1) % len(xy)][0] * xy[i][1] for i in range(len(xy)))
    if area < 0:
        xy = xy[::-1]
    n = len(xy)
    z0, z1 = z
    verts = [(x, y, z0) for x, y in xy] + [(x, y, z1) for x, y in xy]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + \
        [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh_object(name, verts, faces, mat)


def _quad(name, a, u0, u1, v0, v1, mat):
    """u0〜u1（a の向き）× v0〜v1（a の左）の板"""
    return _prism(name, a, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], mat)


def _seg(name, a, p0, p1, mat, w=LINE_W):
    """(u, v) の点 p0 から p1 への幅 w の線"""
    du, dv = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(du, dv)
    nu, nv = -dv / ln * w / 2, du / ln * w / 2
    return _prism(name, a, [(p0[0] - nu, p0[1] - nv), (p1[0] - nu, p1[1] - nv),
                            (p1[0] + nu, p1[1] + nv), (p0[0] + nu, p0[1] + nv)], mat)


def _zebra(name, a, lo, hi, mat):
    """ゼブラの縞: 線 lo（v = lo0 + lo1 u）と hi のあいだ（u は -5〜5）に、v = u - k の向きの縞を並べる。端は線で切る"""
    def span(k):
        # lo(u) <= u - k <= hi(u) と -5 <= u <= 5 を満たす u の範囲
        ua = (k + lo[0]) / (1 - lo[1])
        ub = (k + hi[0]) / (1 - hi[1])
        return max(ua, -MARKING_HALF), min(ub, MARKING_HALF)
    dk = MARKING_ZEBRA_W / 2 * math.sqrt(2)
    step = MARKING_ZEBRA_STEP * math.sqrt(2)
    k = -3 * TILE
    i = 0
    while k < 3 * TILE:
        (a1, b1), (a2, b2) = span(k - dk), span(k + dk)
        if min(b1 - a1, b2 - a2) * math.sqrt(2) >= MARKING_ZEBRA_MIN:
            _prism(f"{name}{i}", a, [(a1, a1 - k + dk), (b1, b1 - k + dk), (b2, b2 - k - dk), (a2, a2 - k - dk)], mat)
            i += 1
        k += step


def _dashed(name, a, v, u0, mat):
    """横位置 v の、u0 から交差点の側の辺までの破線。区切りは道路の中央線の破線と同じ（タイルの辺がすき間の中ほど）"""
    for i in range(MARKING_DASHES):
        t0 = -MARKING_HALF + TILE * (i + (1 - MARKING_DASH_FRAC) / 2) / MARKING_DASHES
        t1 = t0 + TILE * MARKING_DASH_FRAC / MARKING_DASHES
        if t1 > u0:
            _seg(f"{name}{i}", a, (max(t0, u0), v), (t1, v), mat)


def _arrow(name, a, c, turn, mat):
    """車線の中心 c の矢印。turn は "straight"・"right"・"straight_left"。曲がる矢印は、矢じりが車線に収まるよう、軸を
    曲がる向きと反対へ shift だけずらす"""
    A = MARKING_ARROW
    side = {"right": -1, "straight_left": 1}.get(turn, 0)
    s = c - side * A["shift"]
    w = A["shaft_w"] / 2
    if turn in ("straight", "straight_left"):
        _quad(f"{name}_shaft", a, A["u0"], A["head_base"], s - w, s + w, mat)
        _prism(f"{name}_head", a, [(A["head_base"], s - A["head_w"] / 2), (A["head_tip"], s),
                                   (A["head_base"], s + A["head_w"] / 2)], mat)
    else:
        _quad(f"{name}_shaft", a, A["u0"], A["turn_u"] + w, s - w, s + w, mat)
    if side:
        v_end = s + side * A["turn_len"]
        _quad(f"{name}_turn", a, A["turn_u"] - w, A["turn_u"] + w, min(s, v_end), max(s, v_end), mat)
        hw = A["turn_head_w"] / 2
        _prism(f"{name}_thead", a, [(A["turn_u"] - hw, v_end), (A["turn_u"], v_end + side * A["turn_head"]),
                                    (A["turn_u"] + hw, v_end)], mat)


def _crosswalk(a, stripes, mat):
    w = MARKING_STRIPE_W / 2
    for i, c in enumerate(MARKING_STRIPES[stripes]):
        _quad(f"marking_stripe{i}", a, MARKING_CROSSWALK_NEAR, MARKING_CROSSWALK_FAR, c - w, c + w, mat)


def marking_mouth(kind, a):
    """1 マス目 1 枚。a は交差点の側の向き"""
    mat = material(*MARKING_LINE)
    _crosswalk(a, MARKING_KINDS[kind], mat)
    if kind == "crosswalk_wide":
        return
    center, b1, b2, edge = MARKING_LANES[MARKING_GEOMETRY[kind]]
    if b2 is None:  # 2 車線: 右折と、左折・直進の 2 車線
        lanes = ((center, b1, "right"), (b1, edge, "straight_left"))
    else:
        lanes = ((center, b1, "right"), (b1, b2, "straight"), (b2, edge, "straight_left"))
    for i, (_, v, _) in enumerate(lanes[:-1]):
        _seg(f"marking_lane{i}", a, (-MARKING_HALF, v), (MARKING_STOP_BACK, v), mat)
    for i, (v0, v1, turn) in enumerate(lanes):
        _arrow(f"marking_arrow{i}", a, (v0 + v1) / 2, turn, mat)
    _quad("marking_stop", a, MARKING_STOP_BACK, MARKING_STOP_U + STOP_LINE_W / 2, center, MARKING_STOP_END, mat)


def marking_taper(kind, a):
    """2 マス目 1 枚。a は交差点の側の向き。右折車線の遠い端にゼブラの三角、その先から右折車線の境の破線"""
    mat = material(*MARKING_LINE)
    center, b1, _, _ = MARKING_LANES[MARKING_GEOMETRY[kind]]
    e = LINE_W / 2
    c0 = center + e  # 中央線の内の縁
    u0, u1 = -MARKING_HALF, -MARKING_HALF + MARKING_TRI_LEN
    _seg("marking_tri", a, (u0, b1), (u1, c0), mat)  # 三角の斜めの辺
    _seg("marking_tri_end", a, (u0 + e, c0), (u0 + e, b1), mat)  # 三角の遠い辺
    _dashed("marking_lane", a, b1, u0, mat)
    q1 = (c0 - b1) / MARKING_TRI_LEN  # 斜めの辺 v = b1 + q1 (u - u0)
    _zebra("marking_zebra", a, (c0, 0.0), (b1 - q1 * u0 - e * math.hypot(1, q1), q1), mat)


def marking_sheet(sheet, kind, label="M"):
    """交差点の路面表示の way のシート（3 行）。行き止まりのセル（MARKING_DEADENDS）と曲がりのセル（MARKING_CURVES）に、種類ごとの
    2 マス目か 1 マス目（marking_deadend・marking_curve_dir）。アイコン（0,0）は仮の絵（AMI は icons.py が描き直す）、
    カーソル（0,1）は北へ向かう 1 マス目（無ければ 2 マス目）の絵。MARKING_EMPTY_CELL は空"""
    set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
    cells, cursor = {}, {}
    jobs = [(rc, marking_deadend(kind, d)) for rc, d in MARKING_DEADENDS.items()]
    for rc, c in MARKING_CURVES.items():
        a = marking_curve_dir(kind, c)
        jobs.append((rc, ("mouth", a) if a else None))
    for rc, job in jobs:
        if job is None:
            continue
        role, a = job
        clear_models()
        (marking_taper if role == "taper" else marking_mouth)(kind, a)
        cells[rc] = render_cell(f"{sheet}_{rc[0]}_{rc[1]}")
        if a == (0, 1):
            cursor[role] = rc
    cells[(0, 1)] = cells[cursor.get("mouth") or cursor.get("taper")]
    clear_models()
    (marking_mouth if "mouth" in cursor else marking_taper)(kind, (0, 1))
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style="tram")
    make_sheet(cells, 3, 10, os.path.join(_s.SRC, sheet + ".png"))
