"""多車線と交差点の路面表示の way（waytype=tram_track。AMI #187。ADR 0012）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

道路に重ねて敷く路面軌道の way の絵で、白線だけを描く（路面は描かない。下の道路の絵が見える。iss の intersection と同じ draw_as_ding=0）。
下の道路は白線の無い道路（AMI の ami_road_general_blank。sheetlib の no_lines）にし、白線はすべてこの way が描く。
種類（marking_sheet の kind）と、つながる形ごとの絵（左側通行。右側通行の版は作らない）:
  lane4:         4 車線の直線の 1 タイル（2 タイル並べて使う。どちらも同じ絵）。直線・坂・行き止まり（直線と同じ絵）
  junction2:     2 車線の腕（行き止まり）、2 車線どうしの中心（十字・1 タイル）、4 車線 × 2 車線の中心（T字。欠ける向きが相方のタイル）
  junction2_t:   2 車線の腕（行き止まり）、2 車線の T字路の中心（T字。欠ける向きの側に路側線）、十字・1 タイルは junction2 と同じ
  junction4_in:  4 車線の腕の入る側。行き止まり = 2 マス目（導流帯の三角）、T字 = 1 マス目（矢印・停止線・横断歩道）、曲がり = 中心（角の縁石）
  junction4_out: 4 車線の腕の出る側。行き止まり = 2 マス目、T字 = 1 マス目、曲がり = 中心のスクランブル（交差点の中心線に沿う + の帯）
4 車線の腕は 2 マス（iss の 2-1・2-2 と同じ）。右折車線は、2 タイルの境をはさむ 2 本の路側線のあいだの帯をそのまま使い、
通る車線の線は動かさない。腕の 2 列（入る側・出る側）は、2 タイル共通の横位置 V（境が 0、入る側のタイルの中心が +5）で描き、
タイルごとに切り抜く（右折の矢印・停止線・導流帯がタイルの境をまたぐ）。2 車線の腕は 1 マスで、路側線のあいだを 3 等分し直し、
腕の外の端の中央線の一点から 2 本に分けて、あいだに楔の導流帯を置く（iss の intersection1 と同じ）。
位置と幅は道路の白線（road_parts の EDGE_LINE・LINE_W・LINE_TOP・STOP_LINE_W・EDGE_CORNER_R・CENTER_DASHES）に合わせる。
雪の絵は持たない（車道は除雪した想定で、白線は夏と同じ。dat は雪の絵に夏のセルを使う）。坂は lane4 だけ、斜めは持たない
"""
import math
import os

import bpy

from . import sheetlib as _s
from .cells import ROAD_CY, make_sheet, render_cell
from .core import H, TILE, apply_slope, clear_models, material, mesh_object, set_anchor
from .road_parts import CENTER_DASHES, CENTER_DASH_FRAC, EDGE_CORNER_R, EDGE_LINE, LINE_TOP, LINE_W, STOP_LINE_W

# ---------------------------------------------------------------- 寸法（部品の 1 単位 ≈ 1 m。タイル 1 辺 10）
# 腕の位置は、交差点の向き a の座標で、u（a の向き。タイルの中心が 0、交差点の側の辺が +5）と v（a の左を正。左側通行で入る側）で表す
MARKING_HALF = TILE / 2
MARKING_E = LINE_W / 2         # 線の半幅（線の縁に合わせるとき）
MARKING_Z = (0.0, LINE_TOP + 0.004)  # 白線の下面・上面（道路の白線より少しだけ上）
MARKING_DRIVE_LEFT = True      # 左側通行（日本）。右側通行の版は作らない（#156 の決定を引き継ぐ）
# 白の材質: 道路の白線と同じ明るさに見えるよう、面で描く表示は色と発光を落とす（#156 でゲームの画面の画素を比べて決めた値）
MARKING_LINE = ("marking_line", (0.80, 0.80, 0.82), 0.6, 0.0, 0.35)
# 停止線（u）と横断歩道の帯（u）。縞は幅 0.5・周期 1.0 で、どれも路側線（±EDGE_LINE）の内に収める
MARKING_STOP_U = (0.43, 0.77)
MARKING_CROSSWALK_U = (1.5, 4.5)
MARKING_STRIPE_W = 0.5
# 中央の破線: 道路の中央線の破線と同じ周期と位置（タイルの辺がすき間の中ほど）
MARKING_DASHES = CENTER_DASHES[0]
MARKING_DASH_FRAC = CENTER_DASH_FRAC
# 導流帯の縞: 線に 45° の向きで、間隔（縞に直角に測る）と幅。これより短い縞（三角の先の細い所）は描かない
MARKING_ZEBRA_STEP = 0.6
MARKING_ZEBRA_W = 0.25
MARKING_ZEBRA_MIN = 0.2
# 矢印（車線の中心 c から）: 軸の幅、軸の始まり（u）、直進の矢じりの付け根と先、曲がる矢印の横の軸の位置（u）と、矢じりの幅と長さ。
# 2 車線の腕（1 マス）は、楔の導流帯の先から停止線の手前に収まるよう、交差点の側へ du だけずらす
MARKING_ARROW = dict(shaft_w=0.3, u0=-4.4, head_base=-2.6, head_tip=-1.4, head_w=1.0,
                     turn_u=-3.2, turn_len=0.5, turn_head=0.5, turn_head_w=0.9, shift=0.3)
MARKING_ARROW_DU2 = 1.4

# 4 車線の腕（2 タイル共通の V。境 0、入る側のタイルの中心 +5、出る側 -5）
MARKING_W4_EDGE = MARKING_HALF + EDGE_LINE       # 8.37 外の路側線
MARKING_W4_LANE = MARKING_HALF                   # 5 通る車線の境（2 マス目は破線、1 マス目は実線）
MARKING_W4_BAND = MARKING_HALF - EDGE_LINE       # 1.63 中央の帯（右折車線）の縁 = 内の路側線
MARKING_W4_TRI_U = -1.0                          # 導流帯の三角の、帯の出る側の線の上の先（u）。縦の辺は 2 マス目の外の端
# 2 車線の腕（1 マス）: 路側線のあいだを 3 等分し、入る側 2 車線・出る側 1 車線にする
MARKING_W2_THIRD = EDGE_LINE / 3  # 1.123 入る側 2 車線の境 = +、寄せた中央線 = -
MARKING_W2_SPLIT_U = (-MARKING_HALF, -3.0)       # 楔の導流帯: 中央線の一点（外の端）から、分かれ終わる所まで
MARKING_W2_DASH = ((-2.6, -2.0),)                # 入る側 2 車線の境の破線（楔の先から）。この先は実線
MARKING_W2_SOLID_U = -1.6

# スクランブル（junction4_out の曲がり）: 交差点の中心線（中心の 4 タイルの内の辺）に沿う横断歩道の帯の、片側の幅
MARKING_SCRAMBLE_W = 1.5

MARKING_KINDS = ("lane4", "junction2", "junction2_t", "junction4_in", "junction4_out")
_DIRS = {"n": (0, 1), "e": (1, 0), "s": (0, -1), "w": (-1, 0)}
# セル（行, 列）→ 形。位置は ami_dat.py の IMAGES と同じ（iss・blender-poc の線路の並び）
MARKING_DEADENDS = {(0, 5): "s", (0, 6): "w", (0, 7): "n", (0, 8): "e"}       # 行き止まり → つながる向き
MARKING_CURVES = {(2, 5): "sw", (2, 6): "nw", (2, 7): "ne", (2, 8): "se"}
MARKING_TEES = {(3, 5): "w", (3, 6): "s", (3, 7): "e", (3, 8): "n"}            # T字（nse・new・nsw・sew）→ 欠ける向き
MARKING_CROSS_CELL = (3, 9)
MARKING_SINGLE_CELL = (0, 9)
MARKING_STRAIGHTS = {(0, 2): "ns", (0, 3): "ew"}
MARKING_SLOPES = {(1, 0): ("ns", lambda x, y: H * (y + MARKING_HALF) / TILE),
                  (1, 1): ("ew", lambda x, y: H * (MARKING_HALF - x) / TILE),
                  (1, 2): ("ns", lambda x, y: H * (MARKING_HALF - y) / TILE),
                  (1, 3): ("ew", lambda x, y: H * (x + MARKING_HALF) / TILE),
                  (1, 5): ("ns", lambda x, y: 2 * H * (y + MARKING_HALF) / TILE),
                  (1, 6): ("ew", lambda x, y: 2 * H * (MARKING_HALF - x) / TILE),
                  (1, 7): ("ns", lambda x, y: 2 * H * (MARKING_HALF - y) / TILE),
                  (1, 8): ("ew", lambda x, y: 2 * H * (x + MARKING_HALF) / TILE)}
MARKING_EMPTY_CELL = (0, 4)    # 絵の無い形が使う空のセル（ami_dat.py の MARKING_EMPTY_CELL）
MARKING_ROWS, MARKING_COLS = 4, 10


# ---------------------------------------------------------------- 多角形（(u, v) の凸の多角形を集め、切り抜いてから板にする）
def _clip(poly, n, c):
    """凸の多角形 poly のうち n・p <= c の側を残す"""
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        fp, fq = n[0] * p[0] + n[1] * p[1] - c, n[0] * q[0] + n[1] * q[1] - c
        if fp <= 0:
            out.append(p)
        if (fp < 0 < fq) or (fq < 0 < fp):
            t = fp / (fp - fq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def _area(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly))) / 2


def _inset_planes(poly, e):
    """凸の多角形の各辺を内へ e だけ寄せた半平面（n, c）の並び。縞を線の内の縁で切るのに使う"""
    if _area(poly) < 0:
        poly = poly[::-1]
    planes = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        dx, dy = q[0] - p[0], q[1] - p[1]
        ln = math.hypot(dx, dy)
        n = (dy / ln, -dx / ln)  # 外向き
        planes.append((n, n[0] * p[0] + n[1] * p[1] - e))
    return planes


class _Plan:
    """白線の多角形を (u, v) で集める。emit で、向き a のタイルへ横位置をずらし、切り抜いて板にする"""

    def __init__(self):
        self.polys = []

    def poly(self, pts):
        self.polys.append(list(pts))

    def quad(self, u0, u1, v0, v1):
        self.poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def seg(self, p0, p1, w=LINE_W):
        du, dv = p1[0] - p0[0], p1[1] - p0[1]
        ln = math.hypot(du, dv)
        nu, nv = -dv / ln * w / 2, du / ln * w / 2
        self.poly([(p0[0] - nu, p0[1] - nv), (p1[0] - nu, p1[1] - nv), (p1[0] + nu, p1[1] + nv), (p0[0] + nu, p0[1] + nv)])

    def line(self, v, u0, u1):
        self.seg((u0, v), (u1, v))

    def dashed(self, v, u0=-MARKING_HALF, u1=MARKING_HALF):
        """横位置 v の破線。区切りは道路の中央線の破線と同じ（タイルの辺がすき間の中ほど）"""
        for i in range(MARKING_DASHES):
            t0 = -MARKING_HALF + TILE * (i + (1 - MARKING_DASH_FRAC) / 2) / MARKING_DASHES
            t1 = t0 + TILE * MARKING_DASH_FRAC / MARKING_DASHES
            if t1 > u0 and t0 < u1:
                self.line(v, max(t0, u0), min(t1, u1))

    def zebra(self, region):
        """凸の多角形 region（線の中心で囲んだ形）の内に、v = u - k の向きの縞を並べる。端は線の内の縁で切る"""
        planes = _inset_planes(region, MARKING_E)
        dk = MARKING_ZEBRA_W / 2 * math.sqrt(2)
        step = MARKING_ZEBRA_STEP * math.sqrt(2)
        far = 3 * TILE
        k = -far
        while k < far:
            st = [(-far, -far - k - dk), (far, far - k - dk), (far, far - k + dk), (-far, -far - k + dk)]
            for n, c in planes:
                st = _clip(st, n, c)
                if len(st) < 3:
                    break
            if len(st) >= 3 and abs(_area(st)) / MARKING_ZEBRA_W >= MARKING_ZEBRA_MIN:
                self.poly(st)
            k += step

    def arrow(self, c, turn, du=0.0):
        """車線の中心 c の矢印。turn は "straight"・"right"・"straight_left"。曲がる矢印は、矢じりが車線に収まるよう、
        軸を曲がる向きと反対へ shift だけずらす"""
        A = {k: (v + du if k in ("u0", "head_base", "head_tip", "turn_u") else v) for k, v in MARKING_ARROW.items()}
        side = {"right": -1, "straight_left": 1}.get(turn, 0)
        s = c - side * A["shift"]
        w = A["shaft_w"] / 2
        if turn in ("straight", "straight_left"):
            self.quad(A["u0"], A["head_base"], s - w, s + w)
            self.poly([(A["head_base"], s - A["head_w"] / 2), (A["head_tip"], s), (A["head_base"], s + A["head_w"] / 2)])
        else:
            self.quad(A["u0"], A["turn_u"] + w, s - w, s + w)
        if side:
            v_end = s + side * A["turn_len"]
            self.quad(A["turn_u"] - w, A["turn_u"] + w, min(s, v_end), max(s, v_end))
            hw = A["turn_head_w"] / 2
            self.poly([(A["turn_u"] - hw, v_end), (A["turn_u"], v_end + side * A["turn_head"]), (A["turn_u"] + hw, v_end)])

    def crosswalk(self, centers):
        w = MARKING_STRIPE_W / 2
        for c in centers:
            self.quad(*MARKING_CROSSWALK_U, c - w, c + w)

    def emit(self, a, mat, voff=0.0):
        """向き a（単位ベクトル。None なら (u, v) をそのまま (x, y) とする）のタイルへ、横位置を voff だけずらして
        （タイルの v = V - voff）、タイルの範囲で切り抜いて板にする"""
        box = (((1, 0), MARKING_HALF), ((-1, 0), MARKING_HALF), ((0, 1), MARKING_HALF), ((0, -1), MARKING_HALF))
        for i, pts in enumerate(self.polys):
            pts = [(u, v - voff) for u, v in pts]
            for n, c in box:
                pts = _clip(pts, n, c)
                if len(pts) < 3:
                    break
            if len(pts) >= 3 and abs(_area(pts)) > 1e-4:
                _prism(f"marking{i}", a, pts, mat)


def _prism(name, a, pts, mat, z=MARKING_Z):
    """向き a の座標の (u, v) の凸の多角形 pts を z の厚さの板にする（a が None なら (u, v) = (x, y)）"""
    if a is None:
        xy = list(pts)
    else:
        ax, ay = a
        sx, sy = -ay, ax
        xy = [(ax * u + sx * v, ay * u + sy * v) for u, v in pts]
    if _area(xy) < 0:
        xy = xy[::-1]
    n = len(xy)
    z0, z1 = z
    verts = [(x, y, z0) for x, y in xy] + [(x, y, z1) for x, y in xy]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + \
        [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return mesh_object(name, verts, faces, mat)


# ---------------------------------------------------------------- 絵（どれも 1 タイル 1 枚。_Plan に集めて emit する）
def _lane4(plan):
    """4 車線の直線の 1 タイル（向き a の座標）: 両側の路側線（実線）と、中ほどの車線の境（破線）"""
    for v in (-EDGE_LINE, EDGE_LINE):
        plan.line(v, -MARKING_HALF, MARKING_HALF)
    plan.dashed(0.0)


def _arm4_first(plan):
    """4 車線の腕の 1 マス目（2 タイル共通の V）: 線は実線で停止線まで、矢印、停止線、横断歩道。外の路側線は交差点の辺まで"""
    h, stop = MARKING_HALF, MARKING_STOP_U
    for v in (-MARKING_W4_EDGE, MARKING_W4_EDGE):
        plan.line(v, -h, h)
    for v in (MARKING_W4_LANE, MARKING_W4_BAND):           # 入る側: 停止線の手前まで
        plan.line(v, -h, stop[0])
    for v in (-MARKING_W4_LANE, -MARKING_W4_BAND):         # 出る側: 停止線の向こうの縁まで
        plan.line(v, -h, stop[1])
    plan.quad(stop[0], stop[1], -MARKING_W4_BAND - MARKING_E, MARKING_W4_EDGE - MARKING_E)
    plan.arrow((MARKING_W4_LANE + MARKING_W4_EDGE) / 2, "straight_left")
    plan.arrow((MARKING_W4_BAND + MARKING_W4_LANE) / 2, "straight")
    plan.arrow(0.0, "right")
    plan.crosswalk([i + 0.5 for i in range(-8, 8)])        # -7.5〜7.5（境 0 は縞のあいだ）


def _arm4_second(plan):
    """4 車線の腕の 2 マス目（2 タイル共通の V）: 通る車線の境は破線、帯の入る側の線は破線、出る側の線は実線。
    帯の外の端に導流帯の三角（縦の辺が外の端、下の辺が出る側の線、斜めの辺が左上から右下へ）"""
    h, e = MARKING_HALF, MARKING_E
    for v in (-MARKING_W4_EDGE, MARKING_W4_EDGE, -MARKING_W4_BAND):
        plan.line(v, -h, h)
    for v in (-MARKING_W4_LANE, MARKING_W4_LANE, MARKING_W4_BAND):
        plan.dashed(v)
    top, bot, tip = (-h, MARKING_W4_BAND), (-h, -MARKING_W4_BAND), (MARKING_W4_TRI_U, -MARKING_W4_BAND)
    plan.seg(top, tip)
    plan.seg((-h + e, bot[1]), (-h + e, top[1]))
    plan.zebra([top, bot, tip])


def _arm2(plan):
    """2 車線の腕（1 マス。向き a の座標）: 路側線、中央線の一点から分かれる 2 本（入る側 2 車線の境と、寄せた中央線）、楔の導流帯、
    矢印・停止線・横断歩道"""
    h, e, stop = MARKING_HALF, MARKING_E, MARKING_STOP_U
    t = MARKING_W2_THIRD
    u0, u1 = MARKING_W2_SPLIT_U
    for v in (-EDGE_LINE, EDGE_LINE):
        plan.line(v, -h, h)
    plan.seg((u0, 0.0), (u1, -t))                          # 寄せた中央線（実線）
    plan.line(-t, u1, stop[1])
    plan.seg((u0, 0.0), (u1, t))                           # 入る側 2 車線の境: 楔の辺、破線、実線
    for d0, d1 in MARKING_W2_DASH:
        plan.line(t, d0, d1)
    plan.line(t, MARKING_W2_SOLID_U, stop[0])
    plan.seg((u1, -t), (u1, t))                            # 楔の閉じる辺
    plan.zebra([(u0, 0.0), (u1, -t), (u1, t)])
    plan.quad(stop[0], stop[1], -t - e, EDGE_LINE - e)
    plan.arrow((t + EDGE_LINE) / 2, "straight_left", MARKING_ARROW_DU2)
    plan.arrow(0.0, "right", MARKING_ARROW_DU2)
    plan.crosswalk([i - 3.0 for i in range(7)])


def _corner(plan, a, b):
    """中心のタイル（(x, y) の座標）の、腕 a と腕 b のあいだの角: 路側線の円弧と、その両側の腕の路側線（円弧の端からタイルの辺まで）。
    道路の corner_arc（sheetlib の road_sheet）と同じ形"""
    E_, r, h = EDGE_LINE, EDGE_CORNER_R, MARKING_HALF
    c = ((a[0] + b[0]) * (E_ + r), (a[1] + b[1]) * (E_ + r))
    n = 12
    pts = [(c[0] - a[0] * r * math.cos(t) - b[0] * r * math.sin(t), c[1] - a[1] * r * math.cos(t) - b[1] * r * math.sin(t))
           for t in (math.pi / 2 * i / n for i in range(n + 1))]
    for p, q in zip(pts, pts[1:]):
        plan.seg(p, q)
    for x, y in ((a, b), (b, a)):  # 腕 x の、y の側の路側線
        plan.seg((x[0] * (E_ + r) + y[0] * E_, x[1] * (E_ + r) + y[1] * E_), (x[0] * h + y[0] * E_, x[1] * h + y[1] * E_))


def _center(plan, arms_pairs):
    for a, b in arms_pairs:
        _corner(plan, _DIRS[a], _DIRS[b])


def _scramble(plan, curve):
    """曲がり curve の中心のタイル（4 車線どうしの交差点の 4 枚の 1 枚。外の角が curve）の、内の 2 辺に沿う横断歩道の帯
    （4 枚で交差点の中心線に沿う + の帯になる）。縞は帯の向きに周期 1.0 で並ぶ。帯が交わる所は北南の帯が描く"""
    a, b = (_DIRS[c] for c in curve)
    h, w, sw = MARKING_HALF, MARKING_SCRAMBLE_W, MARKING_STRIPE_W / 2
    for along, across in ((a, b), (b, a)):
        # 内の辺（-across の側）から across の向きへ幅 w の帯。座標 s（across の向き）・t（along の向き）は、どちらも内の辺が -h
        start = -h if along[1] != 0 else -h + w + 0.25  # 東西の帯は、交わる所の先から
        xy = lambda s_, t_: (across[0] * s_ + along[0] * t_, across[1] * s_ + along[1] * t_)
        k = 0
        while -h + 0.5 + k + sw <= h - 0.25:
            c = -h + 0.5 + k
            if c - sw >= start:
                plan.poly([xy(-h, c - sw), xy(-h + w, c - sw), xy(-h + w, c + sw), xy(-h, c + sw)])
            k += 1


# ---------------------------------------------------------------- 種類と形 → 絵
def _tile_v(inbound):
    """4 車線の腕の、入る側（inbound）か出る側のタイルへの横位置のずらし（タイルの中心の V）"""
    return MARKING_W4_LANE if inbound else -MARKING_W4_LANE


def marking_jobs(kind):
    """種類 → {セル: (描く関数, 向き a か None, 横位置のずらし, 坂)}"""
    jobs = {}
    d = lambda c: _DIRS[c]
    if kind == "lane4":
        for rc, axis in MARKING_STRAIGHTS.items():
            jobs[rc] = (_lane4, d(axis[1]), 0.0, None)
        for rc, c in MARKING_DEADENDS.items():
            jobs[rc] = (_lane4, d(c), 0.0, None)
        for rc, (axis, slope) in MARKING_SLOPES.items():
            jobs[rc] = (_lane4, d(axis[1]), 0.0, slope)
        return jobs
    if kind in ("junction2", "junction2_t"):
        four = lambda p: _center(p, (("n", "e"), ("e", "s"), ("s", "w"), ("w", "n")))
        jobs[MARKING_CROSS_CELL] = jobs[MARKING_SINGLE_CELL] = (four, None, 0.0, None)
        for rc, c in MARKING_DEADENDS.items():
            jobs[rc] = (_arm2, d(c), 0.0, None)
        for rc, m in MARKING_TEES.items():
            jobs[rc] = (_tee(m, kind == "junction2_t"), None, 0.0, None)
        return jobs
    inbound = kind == "junction4_in"
    for rc, c in MARKING_DEADENDS.items():
        jobs[rc] = (_arm4_second, d(c), _tile_v(inbound), None)
    for rc, m in MARKING_TEES.items():
        mx, my = d(m)
        a = (my, -mx) if inbound else (-my, mx)  # 欠ける向き（外の側）が、入る側は a の左、出る側は a の右
        jobs[rc] = (_arm4_first, a, _tile_v(inbound), None)
    for rc, c in MARKING_CURVES.items():
        jobs[rc] = ((lambda cc: lambda p: _center(p, ((cc[0], cc[1]),)))(c) if inbound else
                    (lambda cc: lambda p: (_center(p, ((cc[0], cc[1]),)), _scramble(p, cc)))(c), None, 0.0, None)
    return jobs


def _tee(m, closed_edge):
    """T字（欠ける向き m）の中心: 欠ける向きと反対の側の 2 つの角の円弧。closed_edge なら、欠ける向きの側に路側線（2 車線の T字路の
    閉じた側）。偽なら弧だけ（4 車線 × 2 車線の中心。欠ける向きは相方のタイルで、線を引かない）"""
    opp = {"n": "s", "s": "n", "e": "w", "w": "e"}[m]
    sides = [c for c in "nesw" if c not in (m, opp)]

    def draw(plan):
        _center(plan, ((opp, sides[0]), (opp, sides[1])))
        if closed_edge:
            mx, my = _DIRS[m]
            px, py = _DIRS[sides[0]]
            h = MARKING_HALF
            plan.seg((mx * EDGE_LINE - px * h, my * EDGE_LINE - py * h), (mx * EDGE_LINE + px * h, my * EDGE_LINE + py * h))
    return draw


def marking_sheet(sheet, kind, label="M"):
    """多車線と交差点の路面表示の way のシート（4 行 × 10 列）。種類ごとの形 → 絵は marking_jobs。絵の無い形のセル
    （MARKING_EMPTY_CELL ほか）は空。アイコン（0,0）は仮の絵（AMI は icons.py が描き直す）、カーソル（0,1）は MARKING_CURSOR の絵"""
    assert kind in MARKING_KINDS, kind
    set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
    mat = material(*MARKING_LINE)
    cells = {}
    jobs = marking_jobs(kind)
    for rc, (draw, a, voff, slope) in jobs.items():
        clear_models()
        plan = _Plan()
        draw(plan)
        plan.emit(a, mat, voff)
        if slope:
            for ob in list(bpy.context.scene.objects):
                if ob.type == "MESH" and ob.name.startswith("marking"):
                    apply_slope(ob, slope)
        cells[rc] = render_cell(f"{sheet}_{rc[0]}_{rc[1]}")
    cursor = MARKING_CURSOR[kind]
    cells[(0, 1)] = cells[cursor]
    clear_models()
    draw, a, voff, _ = jobs[cursor]
    plan = _Plan()
    draw(plan)
    plan.emit(a, mat, voff)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style="tram")
    make_sheet(cells, MARKING_ROWS, MARKING_COLS, os.path.join(_s.SRC, sheet + ".png"))


# カーソルの絵のセル: 北南の直線、北へ向かう 2 車線の腕（行き止まり [n]）、北へ向かう 4 車線の腕の 1 マス目（入る側は T字 [nse]、出る側は [nsw]）
MARKING_CURSOR = {"lane4": (0, 2), "junction2": (0, 7), "junction2_t": (0, 7), "junction4_in": (3, 5), "junction4_out": (3, 7)}
