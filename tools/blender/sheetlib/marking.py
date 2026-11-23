"""多車線と交差点の路面表示の way（waytype=tram_track。AMI #187。ADR 0012）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

道路に重ねて敷く路面軌道の way の絵で、白線と、その下の路面（アスファルト。marking_sheet の paving）を描く（SIS 式。路面ごと描いて下の道路の
線と雪を覆う）。路面は、下の道路の路側の雪のまだら（road_parts の SNOW_LAYERS の slush0）が始まる所より内だけに敷き、外の路肩は下の道路の
絵（夏の路面・雪）をそのまま見せる。下の道路は白線のある一般道路のままでよい（その中央線・内の路側線・交差点の中の線は路面が覆い、外の路側線・
角の円弧は表示と同じ位置）。絵はタイルの内に収まるので、draw_as_ding は付けない（0。docs/reference/cityscape.md の 2.1）。
種類（marking_sheet の kind）と、つながる形ごとの絵（左側通行。右側通行の版は作らない）:
  lane4:         4 車線の直線の 1 タイル（2 列とも同じ絵。左右対称なので、地図を回しても崩れない）。直線・坂・行き止まり（直線と同じ絵）。
                 路面は MARKING_PAVE_IN の内だけで、2 つの列のあいだの帯と外の路肩は、下の道路の絵（雪も）を見せる
  junction2:     2 車線の腕（行き止まり）、2 車線どうしの中心（十字・1 タイル）、4 車線 × 2 車線の中心（T字。欠ける向きが相方のタイル）
  junction2_t:   2 車線の腕（行き止まり）、2 車線の T字路の中心（T字。欠ける向きの側に路側線）、十字・1 タイルは junction2 と同じ
  junction4_in:  4 車線の腕の入る側。行き止まり = 2 マス目（導流帯の三角）、T字 = 1 マス目（矢印・停止線・横断歩道）、曲がり = 中心（角の縁石）
  junction4_out: 4 車線の腕の出る側。行き止まり = 2 マス目、T字 = 1 マス目、曲がり = 中心のスクランブル（中心の 4 タイルの対角線に沿う X の横断歩道。
                 iss の intersection2-2 と同じ）
  lane6_m:       6 車線（#189。3 タイル）の真ん中のタイル（分離帯）の直線。外のタイルの直線は lane4、中心の角は junction4_in の曲がりを使う
  junction6_in・junction6_out: 6 車線の腕の入る側・出る側の外の列。行き止まり = 2 マス目、T字 = 1 マス目（欠ける向きが外の側）
  junction6_m:   6 車線の腕の真ん中の列（右折車線）。行き止まり = 2 マス目、T字 = 1 マス目（欠ける向きが交差点の側）
  junction6_c:   6 車線の中心 3×3 の角を除く 5 枚（辺の 4 枚 = 行き止まり、中央 = 十字）。タイル全面の路面だけ（線は無い）
4 車線の腕は 2 マス（iss の 2-1・2-2 と同じ）。右折車線は、2 タイルの境をはさむ 2 本の路側線のあいだの帯をそのまま使い、
通る車線の線は動かさない。腕の 2 列（入る側・出る側）は、2 タイル共通の横位置 V（境が 0、入る側のタイルの中心が +5）で描き、
タイルごとに切り抜く（右折の矢印・停止線・導流帯がタイルの境をまたぐ）。2 車線の腕は 1 マスで、路側線のあいだを 3 等分し直し、
腕の外の端の中央線の一点から 2 本に分けて、あいだに楔の導流帯を置く（iss の intersection1 と同じ）。2 車線の交差点の路面は、
腕の 3 車線の幅の区間と中心を路側線まで覆う（MARKING_W2_PAVE。_wide_pave）。
位置と幅は道路の白線（road_parts の EDGE_LINE・LINE_W・LINE_TOP・EDGE_CORNER_R・CENTER_DASHES）に合わせる。停止線（MARKING_STOP_U）は横断歩道の手前に置く。
雪の絵は持たない（車道は除雪した想定で、路面・白線は夏と同じ。路肩の雪は下の道路の絵。dat は雪の絵に夏のセルを使う）。坂は lane4・lane6_m だけ、斜めは持たない
"""
import functools
import math
import os

import bpy

from . import sheetlib as _s
from .cells import ROAD_CY, make_sheet, render_cell
from .core import H, TILE, apply_slope, clear_models, material, mesh_object, set_anchor
from .road_parts import CENTER_DASHES, CENTER_DASH_FRAC, EDGE_CORNER_R, EDGE_LINE, LINE_TOP, LINE_W, SNOW_LAYERS

# ---------------------------------------------------------------- 寸法（部品の 1 単位 ≈ 1 m。タイル 1 辺 10）
# 腕の位置は、交差点の向き a の座標で、u（a の向き。タイルの中心が 0、交差点の側の辺が +5）と v（a の左を正。左側通行で入る側）で表す
MARKING_HALF = TILE / 2
MARKING_E = LINE_W / 2         # 線の半幅（線の縁に合わせるとき）
MARKING_Z = (0.0, LINE_TOP + 0.004)  # 白線の下面・上面（道路の白線より少しだけ上）
# 路面の板: 白線より下。敷くのは、路側線から MARKING_PAVE_GAP だけ内まで（下の道路の路側の雪のまだらの始まり。そこから外は下の道路の絵）
MARKING_PAVE_Z = (-0.002, 0.008)
MARKING_SNOW_Z = (0.0, 0.0115)          # 雪の板（下の道路の積もった雪 snowbank と同じ厚み。白線より薄い）
MARKING_SLUSH_DZ = 0.0004                # 雪の縁のぼかしの段ごとの厚みの差（外の段ほど低く、板の縁を重ねて見せる）
MARKING_SNOW_KINDS = ("lane6_m",)       # 雪の絵（夏と別のセル）を持つ種類。シートは行を 2 倍にし、雪は MARKING_ROWS 行下
MARKING_PAVE_IN = SNOW_LAYERS[0][1]                # 2.47（2 車線の道路の中心からの半幅）
MARKING_PAVE_GAP = EDGE_LINE - MARKING_PAVE_IN     # 0.9
MARKING_TEE_MOUTH_COVER = EDGE_LINE + 0.2          # junction2_t の T字の、枝の側の角の内を覆う四角の外の端（下の道路の口の点線の端の外）
# 白の材質: 道路の白線と同じ明るさに見えるよう、面で描く表示は色と発光を落とす（#156 の作業でゲームの画面の画素を比べて決めた値。ADR 0012）
MARKING_LINE = ("marking_line", (0.80, 0.80, 0.82), 0.6, 0.0, 0.35)
# 4 車線の腕の停止線（u）と横断歩道の帯（u）。縞は幅 0.5・周期 1.0 で、どれも路側線（±EDGE_LINE）の内に収める。2 車線の腕は MARKING_W2_*
MARKING_STOP_U = (0.43, 0.77)
MARKING_CROSSWALK_U = (1.5, 4.5)
MARKING_STRIPE_W = 0.5
MARKING_STRIPE_PERIOD = 1.0
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
MARKING_ARROW_DU2 = 3.0

# 4 車線の腕（2 タイル共通の V。境 0、入る側のタイルの中心 +5、出る側 -5）
MARKING_W4_EDGE = MARKING_HALF + EDGE_LINE       # 8.37 外の路側線
MARKING_W4_LANE = MARKING_HALF                   # 5 通る車線の境（2 マス目は破線、1 マス目は実線）
MARKING_W4_BAND = MARKING_HALF - EDGE_LINE       # 1.63 中央の帯（右折車線）の縁 = 内の路側線
MARKING_W4_TRI_U = -1.0                          # 導流帯の三角の、帯の出る側の線の上の先（u）。縦の辺は 2 マス目の外の端
# 2 車線の腕（1 マス）: 路側線のあいだを 3 等分し、入る側 2 車線・出る側 1 車線にする。横断歩道は 4 車線の腕の半分ほどの幅で
# 交差点の側の辺に寄せ、停止線もその手前へ寄せて、楔の後の 3 車線の区間（右折車線）を長くとる
MARKING_W2_THIRD = EDGE_LINE / 3  # 1.123 入る側 2 車線の境 = +、寄せた中央線 = -
MARKING_W2_SPLIT_U = (-MARKING_HALF, -3.4)       # 楔の導流帯: 中央線の一点（外の端）から、分かれ終わる所まで
MARKING_W2_DASH = ((-3.0, -2.4), (-2.0, -1.4))   # 入る側 2 車線の境の破線（楔の先から）。この先は実線
MARKING_W2_SOLID_U = -1.0
MARKING_W2_CROSSWALK_U = (3.2, 4.7)
MARKING_W2_STOP_U = (2.13, 2.47)
# 3 車線の幅の区間の路面は、路側線まで覆う（下の道路の路側のまだらの雪を隠し、路肩の寄りまで除雪された見え方にする）。
# 楔の区間で、外の端の MARKING_PAVE_IN から路側線まで広げる。中心のタイルでは、2 車線の腕の両側の角も路側線（角の円弧）まで覆う
MARKING_W2_PAVE = EDGE_LINE

# スクランブル（junction4_out の曲がり）: 中心のタイルの、交差点の中心の角から外の角への対角線に沿う横断歩道（4 枚で X）。
# iss の intersection2-2 の曲がりの絵（release の intersection_kt.png の 8 行目）を測ると、帯の幅は約 3.4、長さは約 10.5 で、タイルの中心に
# 置き、交差点の中心の角から約 1.8 あけていた（2 本の帯が中心で重ならない）。幅は 4 車線の腕の横断歩道（MARKING_CROSSWALK_U）とそろえて 3.0 にし、
# 外の端は角の円弧（路側線）の内に収める。縞は幅 MARKING_STRIPE_W・周期 1.0 で、帯に直角
MARKING_SCRAMBLE_GAP = 1.9    # 内の端の、交差点の中心からの距離（対角線の上）
MARKING_SCRAMBLE_OUT = 4.6    # 縞を置く外の限り（タイルの中心からの距離。対角線の上。角の円弧の中ほどは約 5.1）。
# 外の端の縞は、路面で覆わない角の四角（MARKING_PAVE_IN より外）にかかる（降雪では下の道路のまだらの雪の上に乗る）

# 6 車線（#189。3 タイル。腕の座標は 4 車線と同じく V: 真ん中のタイルの中心が 0、入る側の外のタイルの中心が +10、出る側が -10）
MARKING_W6_TILE = 2 * MARKING_HALF                 # 10 外のタイルの中心（V）
MARKING_W6_EDGE = MARKING_W6_TILE + EDGE_LINE      # 13.37 外の路側線
MARKING_W6_INNER = MARKING_W6_TILE - EDGE_LINE     # 6.63 外のタイルの内の線（B と境の帯 C のあいだ）
MARKING_W6_MEDIAN = EDGE_LINE                      # 3.37 境の帯 C と分離帯のあいだの路側線
MARKING_W6_CURB = EDGE_LINE / 2                    # 1.685 分離帯の縁（真ん中のタイルの直線）

MARKING_KINDS = ("lane4", "junction2", "junction2_t", "junction4_in", "junction4_out",
                 "lane6_a", "lane6_b", "lane6_m", "junction6_in", "junction6_out", "junction6_m", "junction6_c")
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
        self.paves = []
        self.snows = []

    def pave(self, u0, u1, v0, v1):
        """路面の板（長方形）"""
        self.paves.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

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

    def crosswalk(self, centers, span=MARKING_CROSSWALK_U):
        w = MARKING_STRIPE_W / 2
        for c in centers:
            self.quad(*span, c - w, c + w)

    def snow(self, u0, u1, v0, v1):
        """雪の板（長方形。雪の絵だけ。下の道路の中央線を隠して雪を見せる）"""
        self.snows.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def pave_poly(self, pts):
        """路面の板（凸の多角形）"""
        self.paves.append(list(pts))

    def emit(self, a, mat, voff=0.0, pave_mat=None, snow_mat=None, slush=None):
        """向き a（単位ベクトル。None なら (u, v) をそのまま (x, y) とする）のタイルへ、横位置を voff だけずらして
        （タイルの v = V - voff）、タイルの範囲で切り抜いて板にする。pave_mat が有れば路面の板も作る"""
        box = (((1, 0), MARKING_HALF), ((-1, 0), MARKING_HALF), ((0, 1), MARKING_HALF), ((0, -1), MARKING_HALF))
        layers = [("marking", self.polys, mat, MARKING_Z)]
        if pave_mat is not None:
            layers.append(("marking_pave", self.paves, pave_mat, MARKING_PAVE_Z))
        if snow_mat is not None and self.snows:
            # 雪の板の縁のぼかし（#197）: 板を縦（v）に広げた帯を、外が暗く内が明るい順に下から重ねる（slush は外 → 内の (広げる幅, 材質)）
            for i, (d, sm) in enumerate(slush or ()):
                zt = MARKING_SNOW_Z[1] - MARKING_SLUSH_DZ * (len(slush) - i)
                layers.append((f"marking_slush{i}", [[(u, v - d if v < 0 else v + d) for u, v in pts] for pts in self.snows], sm,
                               (MARKING_SNOW_Z[0], zt)))
            layers.append(("marking_snow", self.snows, snow_mat, MARKING_SNOW_Z))
        for tag, polys, m, z in layers:
            for i, pts in enumerate(polys):
                pts = [(u, v - voff) for u, v in pts]
                for n, c in box:
                    pts = _clip(pts, n, c)
                    if len(pts) < 3:
                        break
                if len(pts) >= 3 and abs(_area(pts)) > 1e-4:
                    _prism(f"{tag}{i}", a, pts, m, z)


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
    """4 車線の直線の 1 タイル（向き a の座標）: 両側の路側線（実線）と、中ほどの車線の境（破線）。路面は ±MARKING_PAVE_IN の内
    （下の道路の中央線を覆う。そこから外は、ふつうの一般道路と同じく下の道路の絵で、2 つの列のあいだの帯にも雪が見える）"""
    h, P = MARKING_HALF, MARKING_PAVE_IN
    for v in (-EDGE_LINE, EDGE_LINE):
        plan.line(v, -h, h)
    plan.dashed(0.0)
    plan.pave(-h, h, -P, P)


def _arm4_pave(plan):
    """4 車線の腕の路面（2 タイル共通の V）: 外の路側線の内 MARKING_PAVE_GAP まで。帯（2 タイルの境）は全部覆う"""
    w = MARKING_W4_EDGE - MARKING_PAVE_GAP
    plan.pave(-MARKING_HALF, MARKING_HALF, -w, w)


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
    _arm4_pave(plan)


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
    _arm4_pave(plan)


def _arm2(plan):
    """2 車線の腕（1 マス。向き a の座標）: 路側線、中央線の一点から分かれる 2 本（入る側 2 車線の境と、寄せた中央線）、楔の導流帯、
    矢印・停止線・横断歩道。路面は、外の端の MARKING_PAVE_IN から楔に沿って広げ、3 車線の区間は MARKING_W2_PAVE まで"""
    h, e, stop = MARKING_HALF, MARKING_E, MARKING_W2_STOP_U
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
    plan.crosswalk([i - 3.0 for i in range(7)], MARKING_W2_CROSSWALK_U)
    P, W = MARKING_PAVE_IN, MARKING_W2_PAVE
    plan.pave_poly([(u0, -P), (u1, -W), (h, -W), (h, W), (u1, W), (u0, P)])


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


def _center(plan, arms_pairs, closed=(), wide=()):
    for a, b in arms_pairs:
        _corner(plan, _DIRS[a], _DIRS[b])
    _center_pave(plan, arms_pairs, closed)
    _wide_pave(plan, arms_pairs, closed, wide)


def _wide_pave(plan, corners, closed, wide):
    """中心のタイル（(x, y) の座標）の、2 車線の腕（wide の向き）の側を MARKING_W2_PAVE まで広げる路面（_center_pave に足す）。
    角（a, b）の両方の腕が広いなら、角の四角の路側線の内（角の円弧まで）を全部覆う。片方だけなら、広い腕の辺の MARKING_W2_PAVE から、
    交差点の中心の側の MARKING_PAVE_IN の角へ斜めに狭める（相方の腕の路面の端に合わせる）。閉じた側（closed）は、2 車線の T字路の
    閉じた側の路側線まで覆う"""
    if not wide:
        return
    P, W, h, r = MARKING_PAVE_IN, MARKING_W2_PAVE, MARKING_HALF, EDGE_CORNER_R
    for a, b in corners:
        A, B = _DIRS[a], _DIRS[b]
        xy = lambda d, l: (A[0] * d + B[0] * l, A[1] * d + B[1] * l)   # d: 腕 a の向き、l: 腕 b の向き
        wa, wb = a in wide, b in wide
        if wa and wb:
            plan.pave_poly([xy(P, P), xy(h, P), xy(h, W), xy(P, W)])
            plan.pave_poly([xy(P, P), xy(W, P), xy(W, h), xy(P, h)])
            c, n = W + r, 12
            arc = [(c - r * math.sin(t), c - r * math.cos(t)) for t in (math.pi / 2 * i / n for i in range(n + 1))]
            for p, q in zip(arc, arc[1:]):
                plan.pave_poly([xy(W, W), xy(*p), xy(*q)])
        elif wa or wb:
            sw = (lambda d, l: xy(d, l)) if wa else (lambda d, l: xy(l, d))
            plan.pave_poly([sw(P, P), sw(h, P), sw(h, W), sw(W + r, W)])
    for m in closed:
        mx, my = _DIRS[m]
        px, py = -my, mx
        pts = [(mx * s + px * t, my * s + py * t) for s, t in ((P, -h), (W, -h), (W, h), (P, h))]
        plan.pave_poly(pts)


def _center_pave(plan, corners, closed=()):
    """中心のタイル（(x, y) の座標）の路面: タイルの全面から、角（corners の腕の組）の MARKING_PAVE_IN より外の四角と、
    閉じた側（closed の向き）の MARKING_PAVE_IN より外の帯を除く（下の道路の、角・閉じた側の雪のまだらの始まり）。
    4 つの象限を、|x|・|y| が MARKING_PAVE_IN の内か外かで 4 つに分けて敷く"""
    P, h = MARKING_PAVE_IN, MARKING_HALF
    outer = {(_DIRS[a][0] + _DIRS[b][0], _DIRS[a][1] + _DIRS[b][1]) for a, b in corners}
    shut = {_DIRS[c] for c in closed}
    for sx in (1, -1):
        for sy in (1, -1):
            xo, yo = (sx, 0) in shut, (0, sy) in shut
            for ix, iy, keep in (((0, P), (0, P), True), ((P, h), (0, P), not xo), ((0, P), (P, h), not yo),
                                 ((P, h), (P, h), not (xo or yo or (sx, sy) in outer))):
                if keep:
                    xs = sorted((sx * ix[0], sx * ix[1]))
                    ys = sorted((sy * iy[0], sy * iy[1]))
                    plan.pave(xs[0], xs[1], ys[0], ys[1])


def _scramble(plan, curve):
    """曲がり curve の中心のタイル（4 車線どうしの交差点の 4 枚の 1 枚。外の角が curve）の、交差点の中心の角から外の角への対角線に沿う
    横断歩道（4 枚で X。iss の intersection2-2 と同じ）。縞は帯に直角で、内の端から周期 1.0 で並ぶ"""
    a, b = (_DIRS[c] for c in curve)
    r2 = math.sqrt(2)
    g = ((a[0] + b[0]) / r2, (a[1] + b[1]) / r2)   # 対角線の向き（外の角へ）
    p = (-g[1], g[0])
    w = (MARKING_CROSSWALK_U[1] - MARKING_CROSSWALK_U[0]) / 2
    sw = MARKING_STRIPE_W / 2
    pt = lambda d, s: (g[0] * d + p[0] * s, g[1] * d + p[1] * s)
    c = -(MARKING_HALF * r2 - MARKING_SCRAMBLE_GAP) + sw
    while c + sw <= MARKING_SCRAMBLE_OUT + 1e-9:
        plan.poly([pt(c - sw, -w), pt(c + sw, -w), pt(c + sw, w), pt(c - sw, w)])
        c += MARKING_STRIPE_PERIOD


def _lane6_outer(plan, outer):
    """6 車線の外のタイルの直線（向き a の座標。outer が +1 なら外の側が +v、-1 なら -v）: 外の路側線（実線）、車線の境（破線）、
    内の線（B と境の帯 C のあいだ。破線）。路面は、外の側は下の道路の路肩の雪のまだらの始まり（MARKING_PAVE_IN）まで、内の側は
    タイルの端まで覆う（C の外の半分を除雪し、下の道路の内の路側線を隠す）。左右非対称なので、地図を回すと外の側が逆になる（ADR 0013）"""
    h, E, P = MARKING_HALF, EDGE_LINE, MARKING_PAVE_IN
    plan.line(outer * E, -h, h)
    plan.dashed(0.0)
    plan.dashed(-outer * E)
    if outer > 0:
        plan.pave(-h, h, -h, P)
    else:
        plan.pave(-h, h, -P, h)


def _lane6_a(plan):
    _lane6_outer(plan, 1)


def _lane6_b(plan):
    _lane6_outer(plan, -1)


def _lane6_m(plan, snow=False):
    """6 車線の真ん中のタイルの直線（向き a の座標。左右対称）: 路側線 ±MARKING_W6_MEDIAN（外のタイルの内の線と合わせて、境の帯 C が走行車線）と、
    分離帯の縁 ±MARKING_W6_CURB（実線。中は飾りを置く）。路面はタイルの全面（C の外の半分を除雪し、下の中央線を隠す）。
    雪の絵（snow）は、分離帯の部分（縁のあいだ）に雪を見せる（下の中央線は雪で隠す）"""
    h, C = MARKING_HALF, MARKING_W6_CURB
    for v in (-MARKING_W6_MEDIAN, -C, C, MARKING_W6_MEDIAN):
        plan.line(v, -h, h)
    if snow:
        plan.pave(-h, h, -h, -C)
        plan.pave(-h, h, C, h)
        plan.snow(-h, h, -C, C)
    else:
        plan.pave(-h, h, -h, h)


def _arm6_pave(plan):
    """6 車線の腕の路面（3 タイル共通の V）: 外の路側線の内 MARKING_PAVE_GAP まで。真ん中のタイルも全部覆う（下の中央線・内の路側線を隠す）"""
    w = MARKING_W6_EDGE - MARKING_PAVE_GAP
    plan.pave(-MARKING_HALF, MARKING_HALF, -w, w)


def _arm6_first(plan):
    """6 車線の腕の 1 マス目（3 タイル共通の V）: 線は実線で停止線まで、矢印（A 直進・左、B 直進、C 直進、右折車線 右折）、停止線、
    横断歩道（全幅）。右折車線は分離帯のタイルの入る側の半分（V = 0〜MARKING_W6_MEDIAN）"""
    h, stop = MARKING_HALF, MARKING_STOP_U
    E, I, T, M = MARKING_W6_EDGE, MARKING_W6_INNER, MARKING_W6_TILE, MARKING_W6_MEDIAN
    for v in (-E, E):
        plan.line(v, -h, h)
    for v in (T, I, M, 0.0):                               # 入る側: 停止線の手前まで
        plan.line(v, -h, stop[0])
    for v in (-T, -I, -M):                                 # 出る側: 停止線の向こうの縁まで
        plan.line(v, -h, stop[1])
    plan.quad(stop[0], stop[1], -MARKING_E, E - MARKING_E)
    plan.arrow((T + E) / 2, "straight_left")
    plan.arrow((I + T) / 2, "straight")
    plan.arrow((M + I) / 2, "straight")
    plan.arrow(M / 2, "right")
    plan.crosswalk([i + 0.5 for i in range(-13, 13)])      # -12.5〜12.5（分離帯の真ん中 0 は縞のあいだ）
    _arm6_pave(plan)


def _arm6_second(plan):
    """6 車線の腕の 2 マス目（3 タイル共通の V）: 通る車線の境（A|B・B|C）は破線、右折車線の入る側の縁（C との境）は破線、
    右折車線の出る側の縁（V=0）と、出る側の C の内の線（V=-MARKING_W6_MEDIAN）は実線。右折車線の外の端に導流帯の三角（4 車線の _arm4_second と同じ向き）。出る側の外の列の車線の境（-T・-I）は破線。A は一番外の車線、C は分離帯に近い車線"""
    h, e = MARKING_HALF, MARKING_E
    E, I, T, M = MARKING_W6_EDGE, MARKING_W6_INNER, MARKING_W6_TILE, MARKING_W6_MEDIAN
    for v in (-E, E, 0.0, -M):
        plan.line(v, -h, h)
    for v in (T, I, M, -T, -I):
        plan.dashed(v)
    top, bot, tip = (-h, M), (-h, 0.0), (MARKING_W4_TRI_U, 0.0)
    plan.seg(top, tip)
    plan.seg((-h + e, bot[1]), (-h + e, top[1]))
    plan.zebra([top, bot, tip])
    _arm6_pave(plan)


def _center6_pave(plan):
    """6 車線の交差点の中心 3×3 の、角を除く 5 枚（辺の 4 枚と中央）: タイルの全面を路面で覆う（下の道路の十字の弧・線を隠す）。線は無い"""
    h = MARKING_HALF
    plan.pave(-h, h, -h, h)


# ---------------------------------------------------------------- 種類と形 → 絵
def _tile_v(inbound):
    """4 車線の腕の、入る側（inbound）か出る側のタイルへの横位置のずらし（タイルの中心の V）"""
    return MARKING_W4_LANE if inbound else -MARKING_W4_LANE


def marking_jobs(kind):
    """種類 → {セル: (描く関数, 向き a か None, 横位置のずらし, 坂)}"""
    if kind in MARKING_EXPWY_KINDS:
        return _expwy_jobs(kind)
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
        four = lambda p: _center(p, (("n", "e"), ("e", "s"), ("s", "w"), ("w", "n")), (), "nesw")
        jobs[MARKING_CROSS_CELL] = jobs[MARKING_SINGLE_CELL] = (four, None, 0.0, None)
        for rc, c in MARKING_DEADENDS.items():
            jobs[rc] = (_arm2, d(c), 0.0, None)
        for rc, m in MARKING_TEES.items():
            jobs[rc] = (_tee(m, kind == "junction2_t"), None, 0.0, None)
        return jobs
    if kind in ("lane6_a", "lane6_b", "lane6_m"):
        # 直線・坂・行き止まり。外のタイルは左右非対称なので、向きは南北の線なら南向き・東西の線なら西向きにそろえる（行き止まりも、
        # つながる向きでなく線の向きで決める）。lane6_a は外の側が左（南北の線は東、東西の線は南）、lane6_b は右（西・北）
        draw = {"lane6_a": _lane6_a, "lane6_b": _lane6_b, "lane6_m": _lane6_m}[kind]
        for rc, axis in MARKING_STRAIGHTS.items():
            jobs[rc] = (draw, d(axis[1]), 0.0, None)
        for rc, c in MARKING_DEADENDS.items():
            jobs[rc] = (draw, d("s" if c in "ns" else "w"), 0.0, None)
        for rc, (axis, slope) in MARKING_SLOPES.items():
            jobs[rc] = (draw, d(axis[1]), 0.0, slope)
        return jobs
    if kind == "junction6_c":
        for rc in list(MARKING_DEADENDS) + [MARKING_CROSS_CELL]:
            jobs[rc] = (_center6_pave, None, 0.0, None)
        return jobs
    if kind in ("junction6_in", "junction6_out", "junction6_m"):
        # 3 つの列（入る側の外・分離帯・出る側の外）。つながる形が向きを決める: 行き止まり = 2 マス目（つながる向きが交差点）、
        # T字 = 1 マス目。外の列の T字は欠ける向きが外の側（4 車線と同じ）。分離帯の T字は、左右の列へつなぎ外へつないで、欠ける向きが交差点の側
        v6 = {"junction6_in": MARKING_W6_TILE, "junction6_out": -MARKING_W6_TILE, "junction6_m": 0.0}[kind]
        for rc, c in MARKING_DEADENDS.items():
            jobs[rc] = (_arm6_second, d(c), v6, None)
        for rc, m in MARKING_TEES.items():
            mx, my = d(m)
            a = {"junction6_in": (my, -mx), "junction6_out": (-my, mx), "junction6_m": (mx, my)}[kind]
            jobs[rc] = (_arm6_first, a, v6, None)
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
        # 広げる腕: 2 車線の T字路は 3 本とも、4 車線 × 2 車線の中心は 2 車線の腕（opp）だけ
        _center(plan, ((opp, sides[0]), (opp, sides[1])), (m,) if closed_edge else (),
                (opp, *sides) if closed_edge else (opp,))
        if closed_edge:
            # 下の一般道路の T字は、枝の口を点線で渡す（sheetlib の mouth_dash。太さ 0.3 で口の端 ±EDGE_LINE まで）。点線の端が、路面で
            # 覆わない角の四角（MARKING_PAVE_IN より外）に 1 画素ずつ出るので、枝の側の角の内の小さな四角も路面で覆う
            ox, oy = _DIRS[opp]
            w = MARKING_TEE_MOUTH_COVER
            for sd in sides:
                sx_, sy_ = _DIRS[sd]
                xs = sorted((ox * MARKING_PAVE_IN + sx_ * MARKING_PAVE_IN, ox * w + sx_ * w))
                ys = sorted((oy * MARKING_PAVE_IN + sy_ * MARKING_PAVE_IN, oy * w + sy_ * w))
                plan.pave(xs[0], xs[1], ys[0], ys[1])
            mx, my = _DIRS[m]
            px, py = _DIRS[sides[0]]
            h = MARKING_HALF
            plan.seg((mx * EDGE_LINE - px * h, my * EDGE_LINE - py * h), (mx * EDGE_LINE + px * h, my * EDGE_LINE + py * h))
    return draw


def marking_sheet(sheet, kind, label="M", paving=None, snow=None, line=None, slush=None):
    """多車線と交差点の路面表示の way のシート（4 行 × 10 列）。種類ごとの形 → 絵は marking_jobs。絵の無い形のセル
    （MARKING_EMPTY_CELL ほか）は空。アイコン（0,0）は仮の絵（AMI は icons.py が描き直す）、カーソル（0,1）は MARKING_CURSOR の絵。
    line は白線の材質を返す関数（擦れのまだら。#197。無ければ一色の MARKING_LINE）、slush は雪の板の縁のぼかしの段（外 → 内の (広げる幅, 材質を返す関数)）。
    paving は路面の材質を返す関数（下の道路のアスファルトと同じ物。AMI は render.py の _road_asphalt_skin の "asphalt"）。無ければ白線だけ"""
    assert kind in MARKING_KINDS, kind
    set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
    mat = line() if line else material(*MARKING_LINE)
    pave_mat = paving() if paving else None
    snow_mat = snow() if (snow and kind in MARKING_SNOW_KINDS) else None
    slush_mats = [(d, f()) for d, f in (slush or ())] if snow_mat is not None else None
    seasons = (0, 1) if snow_mat is not None else (0,)
    cells = {}
    jobs = marking_jobs(kind)
    for season in seasons:  # 雪の絵（season 1）は MARKING_ROWS 行下
        for rc, (draw, a, voff, slope) in jobs.items():
            clear_models()
            plan = _Plan()
            (functools.partial(draw, snow=True) if season else draw)(plan)
            plan.emit(a, mat, voff, pave_mat, snow_mat if season else None, slush_mats if season else None)
            if slope:
                for ob in list(bpy.context.scene.objects):
                    if ob.type == "MESH" and ob.name.startswith("marking"):
                        apply_slope(ob, slope)
            row = rc[0] + season * MARKING_ROWS
            cells[(row, rc[1])] = render_cell(f"{sheet}_{row}_{rc[1]}")
    cursor = MARKING_CURSOR[kind]
    cells[(0, 1)] = cells[cursor]
    clear_models()
    draw, a, voff, _ = jobs[cursor]
    plan = _Plan()
    draw(plan)
    plan.emit(a, mat, voff, pave_mat)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style="tram")
    make_sheet(cells, MARKING_ROWS * len(seasons), MARKING_COLS, os.path.join(_s.SRC, sheet + ".png"))


# カーソルの絵のセル: 北南の直線、北へ向かう 2 車線の腕（行き止まり [n]）、北へ向かう 4 車線の腕の 1 マス目（入る側は T字 [nse]、出る側は [nsw]）
MARKING_CURSOR = {"lane4": (0, 2), "junction2": (0, 7), "junction2_t": (0, 7), "junction4_in": (3, 5), "junction4_out": (3, 7),
                  "lane6_a": (0, 2), "lane6_b": (0, 2), "lane6_m": (0, 2), "junction6_in": (3, 5), "junction6_out": (3, 7), "junction6_m": (3, 5), "junction6_c": (3, 9)}


# ---------------------------------------------------------------- 高速道路の分岐・合流（AMI #188。ADR 0012 の作りを高速道路へ広げる）
# 本線の車道（高速道路 1 タイル = 1 方向の 2 車線）の左（外）に、ランプへ出入りする 1 車線を足す。車線は、本線の列とランプの列の境をはさむ
# 2 本の路側線のあいだの帯（#187 の右折車線と同じ帯）。区間は、テーパー 1 マス・平行 0〜n マス・分かれ 1 マス。分かれでは、帯の車線が
# ランプの列へ曲がり、ランプの道路（ふつうの高速道路）の 2 車線へ広がる。本線との境は太い破線、分かれた後のあいだは導流帯。
# 種類と形（左側通行。地図を回しても崩れないよう、1 つの種類は行き止まり・T字・曲がりを 1 役ずつに使う。直線は 180° 回すと側が逆になるので使わない）:
#   diverge_main / merge_main: 本線の列。行き止まり = テーパー（分岐は進む向き、合流は戻る向きへつながる）、T字 = 平行（欠ける向きが右）、
#                              曲がり = 分かれ（分岐は戻る向きと左、合流は進む向きと左）
#   diverge_ramp / merge_ramp: ランプの列（テーパー・平行の下は道路なし、分かれの下はランプの道路の曲がり）。行き止まりと曲がりは本線の列と同じ
#                              向きの決まりで、T字は欠ける向きが左、曲がりの横の向きは右（本線の側）
# 絵は、進む向き u（タイルの中心が 0）と左の横位置 v（本線のタイルの中心が 0、ランプのタイルの中心が TILE）で 1 行分を描き、
# タイルごとに切り抜く。合流は分岐の絵を u について裏返す（ランプから入る導線に沿う向きになる）
MARKING_EXPWY_KINDS = ("diverge_main", "diverge_ramp", "merge_main", "merge_ramp")
MARKING_KINDS = MARKING_KINDS + MARKING_EXPWY_KINDS
MARKING_EXPWY_IN = EDGE_LINE                     # 3.37 本線の左の路側線 = 帯の車線との境（太い破線）
MARKING_EXPWY_OUT = TILE - EDGE_LINE             # 6.63 帯の車線の外の路側線（ランプのタイルの、本線の側の路側線の位置）
MARKING_EXPWY_RAMP_TOP = TILE + EDGE_LINE        # 13.37 分かれの先の端の、ランプの道路の外の路側線
MARKING_EXPWY_SHOULDER = 0.4                     # 帯の車線の外の路側線の外に敷く路面（下が草地の所で、線が草に接しないように）
MARKING_EXPWY_BOUNDARY_W = 2 * LINE_W            # 太い破線の幅（車線境界線。路側線の 2 倍）
MARKING_EXPWY_SPLIT_U = -3.0                     # 分かれで、帯の車線の内の線が本線の路側線から離れ始める所（u）
MARKING_EXPWY_RAMP_DASH_W = 5.5                  # ランプの中央の破線を描き始める、車線の幅（分かれた車線が 2 車線へ広がる所）
MARKING_EXPWY_STEPS = 24                         # 曲がる線・路面を割る数


def _smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def _expwy_upper(u):
    """分かれの、帯の車線の外の線（u -5 → 5 で、OUT からランプの外の路側線へ。両端で向きが u にそろう）"""
    return MARKING_EXPWY_OUT + (MARKING_EXPWY_RAMP_TOP - MARKING_EXPWY_OUT) * _smooth((u + MARKING_HALF) / TILE)


def _expwy_lower(u):
    """分かれの、帯の車線の内の線（SPLIT_U まで本線の路側線、そこから OUT へ）"""
    u0 = MARKING_EXPWY_SPLIT_U
    return MARKING_EXPWY_IN + (MARKING_EXPWY_OUT - MARKING_EXPWY_IN) * _smooth((u - u0) / (MARKING_HALF - u0))


def _expwy_curve(plan, f, u0, u1, w=LINE_W):
    n = MARKING_EXPWY_STEPS
    pts = [(u0 + (u1 - u0) * i / n, f(u0 + (u1 - u0) * i / n)) for i in range(n + 1)]
    for p, q in zip(pts, pts[1:]):
        plan.seg(p, q, w)


def _expwy_dashes(plan, f, w, u0=-MARKING_HALF, u1=MARKING_HALF):
    """v = f(u) に沿う破線。区切りは道路の中央線の破線と同じ（タイルの辺がすき間の中ほど）"""
    for i in range(MARKING_DASHES):
        t0 = -MARKING_HALF + TILE * (i + (1 - MARKING_DASH_FRAC) / 2) / MARKING_DASHES
        t1 = t0 + TILE * MARKING_DASH_FRAC / MARKING_DASHES
        a, b = max(t0, u0), min(t1, u1)
        if b > a:
            pts = [(a + (b - a) * k / 4, f(a + (b - a) * k / 4)) for k in range(5)]
            for p, q in zip(pts, pts[1:]):
                plan.seg(p, q, w)


def _expwy_pave(plan, lo, hi):
    """lo(u)〜hi(u) の路面を、u の短冊（凸の台形）に割って敷く"""
    n, h = MARKING_EXPWY_STEPS, MARKING_HALF
    us = [-h + TILE * i / n for i in range(n + 1)]
    for a, b in zip(us, us[1:]):
        plan.pave_poly([(a, lo(a)), (b, lo(b)), (b, hi(b)), (a, hi(a))])


def _expwy_zebra(plan, lo, hi, u0, u1):
    """lo(u)〜hi(u)（u0〜u1）の導流帯の縞。縞は v = u - k の向き（分岐で出ていく導線に沿う）で、両側の線の内の縁で切る"""
    e, hw = MARKING_E, MARKING_ZEBRA_W / 2
    step = MARKING_ZEBRA_STEP * math.sqrt(2)
    k = u0 - TILE
    while k < u1:
        inside = []
        for i in range(401):
            u = u0 + (u1 - u0) * i / 400
            v = u - k
            if lo(u) + e + hw <= v <= hi(u) - e - hw:
                inside.append(u)
        if inside and (inside[-1] - inside[0]) * math.sqrt(2) >= MARKING_ZEBRA_MIN:
            a, b = inside[0], inside[-1]
            d = hw * math.sqrt(2)
            plan.poly([(a, a - k - d), (b, b - k - d), (b, b - k + d), (a, a - k + d)])
        k += step


def _expwy_main_lines(plan):
    """本線の 2 車線の中央の破線（下の道路の破線を路面で覆うので描き直す）。右の路側線は下の道路の絵のまま"""
    plan.dashed(0.0)


def _expwy_taper(plan):
    """テーパー（分岐の 1 マス目）: 帯の車線が 0 から広がる。本線との境は太い破線、外の線は本線の路側線から OUT へ斜めに"""
    h, I, O, S = MARKING_HALF, MARKING_EXPWY_IN, MARKING_EXPWY_OUT, MARKING_EXPWY_SHOULDER
    outer = lambda u: I + (O - I) * (u + h) / TILE
    _expwy_pave(plan, lambda u: -MARKING_PAVE_IN, lambda u: outer(u) + S)
    _expwy_main_lines(plan)
    _expwy_dashes(plan, lambda u: I, MARKING_EXPWY_BOUNDARY_W)
    plan.seg((-h, I), (h, O))


def _expwy_parallel(plan):
    """平行（減速・加速車線）: 帯の車線。本線との境は太い破線、外は実線"""
    h, I, O, S = MARKING_HALF, MARKING_EXPWY_IN, MARKING_EXPWY_OUT, MARKING_EXPWY_SHOULDER
    plan.pave(-h, h, -MARKING_PAVE_IN, O + S)
    _expwy_main_lines(plan)
    _expwy_dashes(plan, lambda u: I, MARKING_EXPWY_BOUNDARY_W)
    plan.line(O, -h, h)


def _expwy_split(plan):
    """分かれ: 帯の車線がランプの列へ曲がり、ランプの道路の 2 車線（外の路側線 RAMP_TOP、内の路側線 OUT）へ広がる。
    本線との境は SPLIT_U まで太い破線、そこから本線の路側線（実線）。そのあいだが導流帯"""
    h, I, S = MARKING_HALF, MARKING_EXPWY_IN, MARKING_EXPWY_SHOULDER
    u0 = MARKING_EXPWY_SPLIT_U
    _expwy_pave(plan, lambda u: -MARKING_PAVE_IN, lambda u: _expwy_upper(u) + S)
    _expwy_main_lines(plan)
    _expwy_dashes(plan, lambda u: I, MARKING_EXPWY_BOUNDARY_W, u1=u0)
    plan.line(I, u0, h)
    _expwy_curve(plan, _expwy_upper, -h, h)
    _expwy_curve(plan, _expwy_lower, u0, h)
    _expwy_zebra(plan, lambda u: I, _expwy_lower, u0, h)
    # ランプの中央の破線: 車線の幅が RAMP_DASH_W を超えた所から、2 本の線のあいだの中ほどに
    mid = lambda u: (_expwy_upper(u) + _expwy_lower(u)) / 2
    us = [-h + TILE * i / 200 for i in range(201)]
    start = next(u for u in us if _expwy_upper(u) - _expwy_lower(u) >= MARKING_EXPWY_RAMP_DASH_W)
    _expwy_dashes(plan, mid, LINE_W, u0=start)


def _mirror(draw):
    """u について裏返した絵（合流）"""
    def mirrored(plan):
        p = _Plan()
        draw(p)
        plan.polys += [[(-u, v) for u, v in pts] for pts in p.polys]
        plan.paves += [[(-u, v) for u, v in pts] for pts in p.paves]
    return mirrored


def _expwy_jobs(kind):
    merge = kind.startswith("merge")
    ramp = kind.endswith("_ramp")
    voff = TILE if ramp else 0.0
    d = lambda c: _DIRS[c]
    left = lambda a: (-a[1], a[0])
    right = lambda a: (a[1], -a[0])
    side = right if ramp else left              # 分かれで横につながる向き（相方の列の側）
    wrap = _mirror if merge else (lambda f: f)
    jobs = {}
    for rc, c in MARKING_DEADENDS.items():      # テーパー: 分岐は進む向き、合流は戻る向きへつながる
        x, y = d(c)
        jobs[rc] = (wrap(_expwy_taper), (-x, -y) if merge else (x, y), voff, None)
    for rc, m in MARKING_TEES.items():          # 平行: 欠ける向きは、本線の列は右、ランプの列は左
        mx, my = d(m)
        jobs[rc] = (wrap(_expwy_parallel), (my, -mx) if ramp else (-my, mx), voff, None)
    for rc, cv in MARKING_CURVES.items():       # 分かれ: 分岐は戻る向きと横、合流は進む向きと横
        for p, q in ((cv[0], cv[1]), (cv[1], cv[0])):
            a = d(p) if merge else (-d(p)[0], -d(p)[1])
            if side(a) == d(q):
                jobs[rc] = (wrap(_expwy_split), a, voff, None)
                break
    assert len(jobs) == 12, (kind, len(jobs))
    return jobs


# カーソルの絵のセル: 北へつながる行き止まり（分岐は北へ向かうテーパー、合流は南へ向かうテーパーの終わり）
MARKING_CURSOR.update({k: (0, 7) for k in MARKING_EXPWY_KINDS})
