"""交差点の路面表示の way（waytype=tram_track。AMI #156）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

道路の上に重ねて敷く路面軌道の way の絵で、白線を描く（路面は、下の道路の線を消す細い帯のほかは描かない。下の道路の絵が見える）。
iss の util/road_misc/intersection.dat と同じく、交差点の手前の 2 タイルに右折レーンを作る（2026-11-22、ユーザーの決定「案 B」）。
口のタイル S は交差点の隣、導流帯のタイル T は S の手前。役割は way の名前とつながる形で決める:
  導流帯（taper・stop_wide の行き止まり n・e・s・w）: 行き止まりの向き（つながる辺）が交差点の側。右折レーンが開く所で、線が分かれ、
      そのあいだに導流帯（斜めの縞）を描く
  2 車線の口（stop の行き止まり）: 行き止まりの向きは導流帯の側で、交差点はその反対。車線の線・矢印・停止線・横断歩道を描く
  4 車線の口（stop_wide の曲がり ne・se・sw・nw）: 曲がりの一方は導流帯、もう一方は進む向きの右（出る側の口）。
  4 車線の出る側の口（crosswalk_wide の曲がり）: 曲がりの一方は交差点、もう一方は進む向きの左（入る側の口）。横断歩道だけ
  ほかの形（直線・T字・十字・1 タイル）と、上に無い組: 何も描かない
敷き方（ingame/marking_sample.nut の approach と同じ順。README の「交差点の路面表示の作り」）。最後に敷いた way の名前がタイルに残り、
向きは足される。1 タイルだけ敷くと、向きはそのままで名前だけが置き換わる（2026-11-22、ゲームで確かめた）:
  2 車線: 1. T から S へ taper を敷く（ドラッグ）  2. S だけに stop を敷く（1 回クリック）
      口の右の隣のタイルは歩道（別の waytype の way）や建物のことが多く、そこへは way を敷けないので、2 車線は道路のタイルだけで作る
      （2026-11-22、進捗管理の決定「案 B2」）
  4 車線: 1. S（入る側の口）から右の隣の出る側の口へ branch  2. 出る側の口から交差点のタイルへ crosswalk_wide
      3. T から S へ stop_wide。どれも道路のタイルの上
種類（kind）:
  stop:           2 車線の道路（1 タイルに片側 1 車線ずつ）の口。路側線のあいだを 3 車線（入る 2・出る 1）に分ける
  taper:          2 車線の道路の導流帯
  stop_wide:      4 車線の道路（1 タイルに同じ向きの 2 車線。AMI #121 の lane の版の 1・2）の入る側の導流帯と口。中央線（タイルの辺）から
                  路側線までを 3 車線に分ける
  crosswalk_wide: 4 車線の道路の出る側の口。横断歩道だけ
  branch:         4 車線の口の向きを決める枝。どの形も何も描かない
路側帯（路側線の外）には、どの種類も横断歩道と停止線を描かない（2026-11-22、ユーザーの指摘。#156）
位置と幅は道路の白線（road_parts の EDGE_LINE・LINE_W・LINE_TOP・STOP_LINE_W）に合わせる。雪の絵は持たない（道路は車道を除雪した想定で、
車道の白線と路面は夏と同じ。dat は雪の絵に夏のセルを使う）。坂・斜めの絵は持たない（交差点は平らな所に作る）
"""
import math
import os

from . import sheetlib as _s
from .cells import ROAD_CY, make_sheet, render_cell
from .core import clear_models, material, mesh_object, noisy_material, set_anchor, TILE
from .road_parts import EDGE_LINE, LINE_TOP, LINE_W, STOP_LINE_W, STREET_ASPHALT

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
MARKING_STOP_BACK = MARKING_STOP_U - STOP_LINE_W / 2  # 停止線の手前の縁。車線の線と矢印はここで止める
MARKING_Z = (0.0, LINE_TOP + 0.004)  # 白線の下面・上面（道路の白線より少しだけ上）
MARKING_PATCH_Z = (0.0, LINE_TOP + 0.002)  # 下の道路の線を消す路面の帯の下面・上面（道路の白線より上、表示の白線より下）
MARKING_PATCH_W = 0.5          # 下の道路の線（v = 0 の中央線・車線の境の破線。幅 LINE_W）を消す路面の帯の幅
MARKING_DRIVE_LEFT = True      # 左側通行（日本）。右側通行の版は作らない（2026-11-22、ユーザーの決定）
MARKING_STOP_END = EDGE_LINE - LINE_W / 2  # 停止線の路側の端: 路側線の内の縁まで（路側帯へ出さない）
# 車線の境（v）。2 車線は路側線のあいだを 3 等分（入る 2・出る 1）、4 車線の入る側は中央線（タイルの辺 -5）から路側線までを 3 等分。
# 線は (外の境, 右折レーンと直進の境, 直進と左折の境) の順。2 車線の 1 つ目は新しい中央線
_W2 = 2 * EDGE_LINE / 3
_W4 = (MARKING_HALF + EDGE_LINE) / 3
MARKING_LANES = {"stop": (-EDGE_LINE, -EDGE_LINE + _W2, -EDGE_LINE + 2 * _W2, EDGE_LINE),
                 "stop_wide": (-MARKING_HALF, -MARKING_HALF + _W4, -MARKING_HALF + 2 * _W4, EDGE_LINE)}
MARKING_CENTER_END = MARKING_CROSSWALK_NEAR - 0.5  # 2 車線の新しい中央線の、交差点の側の端（横断歩道の 0.5 手前）
# 導流帯の縞: 線に 45° の向きで、間隔（縞に直角に測る）と幅。縞の端は導流帯の線の内の縁で切る
MARKING_ZEBRA_STEP = 1.0
MARKING_ZEBRA_W = 0.3
MARKING_ZEBRA_MIN = 0.25       # これより短い縞（導流帯の先の細い所）は描かない
# 導流帯のタイルの車線の境の破線（4 車線）: 道路の中央線の破線（road_parts の CENTER_DASHES・CENTER_DASH_FRAC）と同じ周期と位置
MARKING_DASHES = 4
MARKING_DASH_FRAC = 0.5
# 矢印（車線の中心 c から）: 軸の幅、軸の始まり（u）、直進の矢じりの付け根と先、曲がる矢印の横の軸の位置（u）と、矢じりの幅と長さ
MARKING_ARROW = dict(shaft_w=0.3, u0=-4.4, head_base=-2.6, head_tip=-1.4, head_w=1.0,
                     turn_u=-3.2, turn_len=0.5, turn_head=0.5, turn_head_w=0.9, shift=0.3)
# 白の材質: 道路の白線（road_parts の _M_LINE。幅 1px で、ゲームの画面では路面と混ざって灰色がかって見える）と同じ明るさに見えるよう、
# 面で描く表示は色と発光を落とす。値は、ゲームの画面（拡大率 1）で道路の白線の画素の平均と、横断歩道の縞の画素の平均を比べて決めた
MARKING_LINE = ("marking_line", (0.80, 0.80, 0.82), 0.6, 0.0, 0.35)
# 下の道路の線を消す路面の材質の既定（AMI は render.py から一般道路の路面の材質を渡す）
MARKING_PATCH = lambda: noisy_material("marking_patch", *STREET_ASPHALT, scale=60, rough=0.9)

# 種類 → 横断歩道の並び（口のタイル）
MARKING_KINDS = {"stop": "narrow", "taper": None, "stop_wide": "wide_in", "crosswalk_wide": "wide_out", "branch": None}
# 車線の境の寸法（MARKING_LANES のキー）
MARKING_GEOMETRY = {"stop": "stop", "taper": "stop", "stop_wide": "stop_wide"}
# セル（行, 列）→ 形。位置は線路の way と同じ（ami_dat.py の IMAGES の image[s] など）
MARKING_DEADENDS = {(0, 5): (0, -1), (0, 6): (-1, 0), (0, 7): (0, 1), (0, 8): (1, 0)}  # 行き止まり → つながる向き
MARKING_CURVES = {(2, 5): "sw", (2, 6): "nw", (2, 7): "ne", (2, 8): "se"}
MARKING_EMPTY_CELL = (0, 9)    # ほかの形（直線・T字・十字・1 タイル）と、描かない形が使う空のセル
_DIRS = {"n": (0, 1), "e": (1, 0), "s": (0, -1), "w": (-1, 0)}


def marking_curve_dir(kind, curve):
    """曲がりの形 → 口の交差点の向き a（描かない種類・形は None）。
    stop_wide の口は、交差点と反対（導流帯）と進む向きの右（出る側の口）、crosswalk_wide の口は、交差点と進む向きの左（入る側の口）"""
    d1, d2 = (_DIRS[c] for c in curve)
    for x, y in ((d1, d2), (d2, d1)):
        if kind == "stop_wide":
            a = (-x[0], -x[1])  # x が交差点と反対（導流帯）、y が進む向きの右
            if y == (a[1], -a[0]):
                return a
        elif kind == "crosswalk_wide":
            a = x  # x が交差点、y が進む向きの左
            if y == (-a[1], a[0]):
                return a
    return None


def marking_deadend_role(kind):
    """行き止まりの形に描くもの: "taper"（つながる向きが交差点）、"mouth"（つながる向きが導流帯。2 車線の口）か None"""
    return {"taper": "taper", "stop_wide": "taper", "stop": "mouth"}.get(kind)


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


def _quad(name, a, u0, u1, v0, v1, mat, z=MARKING_Z):
    """u0〜u1（a の向き）× v0〜v1（a の左）の板"""
    return _prism(name, a, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], mat, z)


def _seg(name, a, p0, p1, mat, w=LINE_W):
    """(u, v) の点 p0 から p1 への幅 w の線"""
    du, dv = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(du, dv)
    nu, nv = -dv / ln * w / 2, du / ln * w / 2
    return _prism(name, a, [(p0[0] - nu, p0[1] - nv), (p1[0] - nu, p1[1] - nv),
                            (p1[0] + nu, p1[1] + nv), (p0[0] + nu, p0[1] + nv)], mat)


def _line_at(p0, p1):
    """2 点を通る線の v = q0 + q1 * u の (q0, q1)"""
    q1 = (p1[1] - p0[1]) / (p1[0] - p0[0])
    return p0[1] - q1 * p0[0], q1


def _zebra(name, a, lo, hi, mat):
    """導流帯の縞: 線 lo（v = lo0 + lo1 u）と hi のあいだ（u は -5〜5）に、v = u - k の向きの縞を並べる。端は線で切る"""
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


def _dashed(name, a, p0, p1, mat):
    """p0 から p1（u は -5〜5）への破線。区切りは道路の中央線の破線と同じ（タイルの辺がすき間の中ほど）"""
    for i in range(MARKING_DASHES):
        t0 = (i + (1 - MARKING_DASH_FRAC) / 2) / MARKING_DASHES
        t1 = t0 + MARKING_DASH_FRAC / MARKING_DASHES
        q0 = (p0[0] + (p1[0] - p0[0]) * t0, p0[1] + (p1[1] - p0[1]) * t0)
        q1 = (p0[0] + (p1[0] - p0[0]) * t1, p0[1] + (p1[1] - p0[1]) * t1)
        _seg(f"{name}{i}", a, q0, q1, mat)


def _arrow(name, a, c, turn, mat):
    """車線の中心 c の矢印。turn は "straight"・"left"・"right"・"straight_left"。曲がる矢印は、矢じりが車線に収まるよう、軸を
    曲がる向きと反対へ shift だけずらす"""
    A = MARKING_ARROW
    side = {"left": 1, "right": -1, "straight_left": 1}.get(turn, 0)
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


def _patch(a, mat):
    """下の道路の v = 0 の線（2 車線の中央線・4 車線の車線の境の破線）を、路面の色の帯で消す"""
    _quad("marking_patch", a, -MARKING_HALF, MARKING_HALF, -MARKING_PATCH_W / 2, MARKING_PATCH_W / 2, mat, MARKING_PATCH_Z)


def _crosswalk(a, stripes, mat):
    w = MARKING_STRIPE_W / 2
    for i, c in enumerate(MARKING_STRIPES[stripes]):
        _quad(f"marking_stripe{i}", a, MARKING_CROSSWALK_NEAR, MARKING_CROSSWALK_FAR, c - w, c + w, mat)


def marking_mouth(kind, a, patch=MARKING_PATCH):
    """口のタイル 1 枚。a は交差点の側の向き"""
    mat = material(*MARKING_LINE)
    _crosswalk(a, MARKING_KINDS[kind], mat)
    if kind == "crosswalk_wide":
        return
    pm = patch()
    _patch(a, pm)
    outer, b1, b2, edge = MARKING_LANES[MARKING_GEOMETRY[kind]]
    if kind == "stop":  # 新しい中央線（右折レーンと出る車線の境）。横断歩道の手前まで
        _seg("marking_center", a, (-MARKING_HALF, outer + _W2), (MARKING_CENTER_END, outer + _W2), mat)
        stop0, lanes = b1, ((b1, b2, "right"), (b2, edge, "straight_left"))
    else:
        stop0, lanes = outer, ((outer, b1, "right"), (b1, b2, "straight"), (b2, edge, "straight_left"))
    for i, (v0, v1, _) in enumerate(lanes[:-1]):
        _seg(f"marking_lane{i}", a, (-MARKING_HALF, v1), (MARKING_STOP_BACK, v1), mat)
    for i, (v0, v1, turn) in enumerate(lanes):
        _arrow(f"marking_arrow{i}", a, (v0 + v1) / 2, turn, mat)
    _quad("marking_stop", a, MARKING_STOP_BACK, MARKING_STOP_U + STOP_LINE_W / 2, stop0, MARKING_STOP_END, mat)


def marking_taper(kind, a, patch=MARKING_PATCH):
    """導流帯のタイル 1 枚。a は交差点の側の向き。タイルの手前の辺（u = -5）で道路の線（v = 0 の線、4 車線は中央線）から始まり、
    交差点の側の辺（u = +5）で口のタイルの車線の境に着く"""
    mat = material(*MARKING_LINE)
    _patch(a, patch())
    h = MARKING_HALF
    outer, b1, b2, edge = MARKING_LANES[MARKING_GEOMETRY[kind]]
    e = LINE_W / 2
    if kind == "taper":  # v = 0 の中央線が、新しい中央線（b1）と右折レーンの境（b2）に分かれる
        p_lo, p_hi = ((-h, 0.0), (h, b1)), ((-h, 0.0), (h, b2))
        _seg("marking_center", a, *p_lo, mat)
        _seg("marking_lane", a, *p_hi, mat)
        lo, hi = _line_at(*p_lo), _line_at(*p_hi)
    else:  # 車線の境の破線（v = 0）が b2 へ寄り、中央線（-5）から右折レーンの境（b1）が分かれる
        _dashed("marking_lane", a, (-h, 0.0), (h, b2), mat)
        p_hi = ((-h, outer), (h, b1))
        _seg("marking_taper", a, *p_hi, mat)
        lo, hi = (outer, 0.0), _line_at(*p_hi)
    _zebra("marking_zebra", a, (lo[0] + e, lo[1]), (hi[0] - e, hi[1]), mat)


def marking_sheet(sheet, kind, label="M", patch=MARKING_PATCH):
    """交差点の路面表示の way のシート（3 行）。行き止まりのセル（MARKING_DEADENDS）に導流帯か 2 車線の口、曲がりのセル
    （MARKING_CURVES）に 4 車線の口、アイコン（0,0）は仮の絵（AMI は icons.py が描き直す）、カーソル（0,1）は北へ向かう口の絵。MARKING_EMPTY_CELL は空。
    patch は下の道路の線を消す路面の材質（関数）"""
    set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
    cells = {}
    role = marking_deadend_role(kind)
    cursor_a = None
    for rc, d in MARKING_DEADENDS.items():
        if role is None:
            break
        a = d if role == "taper" else (-d[0], -d[1])
        clear_models()
        (marking_taper if role == "taper" else marking_mouth)(kind, a, patch)
        cells[rc] = render_cell(f"{sheet}_{rc[0]}_{rc[1]}")
        if a == (0, 1):
            cursor_a = rc
    for rc, curve in MARKING_CURVES.items():
        a = marking_curve_dir(kind, curve)
        if a is None:
            continue
        clear_models()
        marking_mouth(kind, a, patch)
        cells[rc] = render_cell(f"{sheet}_{rc[0]}_{rc[1]}")
        if a == (0, 1):
            cursor_a = rc
    if cursor_a:  # カーソルは北へ向かう口（無ければ導流帯）。アイコンの仮の絵も同じ物から描く
        cells[(0, 1)] = cells[cursor_a]
    clear_models()
    if kind in ("stop", "stop_wide", "crosswalk_wide"):
        marking_mouth(kind, (0, 1), patch)
    elif kind == "taper":
        marking_taper(kind, (0, 1), patch)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style="tram")
    make_sheet(cells, 3, 10, os.path.join(_s.SRC, sheet + ".png"))
