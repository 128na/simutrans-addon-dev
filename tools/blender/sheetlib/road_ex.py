"""道路の分岐の追加画像（ex 画像。OTRP の絵の番号 26〜35。Y字分岐・三方分岐）の白線と轍の経路（共通の描画の道具 sheetlib の一部。tools/README.md）。

sheetlib の road_sheet が、プロファイルの "ex_switches" が真のときに使う（docs/reference/way-addon.md の 9.4。#210）。
線路の ex 画像（track_sheet の ex_switches）と同じ形を、道路の白線と轍で表す:
    Y字分岐: T字のタイルで、根元（1 本側）から 2 本の腕（T字の本線の両端）へ開く。直進の絵は無い（腕のカーブだけ）
    三方分岐: 十字のタイルで、根元の軸を通り抜ける直線に、根元と 2 本の腕をつなぐカーブを足す
腕の形は道路の種類のカーブに合わせる（#209）: "arc"（一般道路。4 分の 1 の円弧）、"diag"（幹線道路・高速道路。斜めの直線）。
"ell"（生活道路。L 字）は、2 本の L 字を重ねると T字・十字の形そのものになるので、ここでは作らず、road_sheet が T字・十字の白線を使う。

腕の白線は、腕の中心線から両側へ車道の半幅だけ離れた線（内側と外側）。内側（角の側）の線は、根元の道の路側線へそのままつながる。
外側の線（腕と腕の間の線）は、ほかの道の帯の縁（分かれ切った所）まで引いて、隣の線と鋭角（V 字）につなぐ。腕・通り抜ける道の中央線は、根元から各腕へ
進む車の通り道を点線で塞がないように、ほかの道の帯の中と、その縁から GORE_GAP 以内に入る所を落とし、分かれ切った所から先だけに引く（ユーザーの指摘、#210。実際の道路の分流部の標示も、分かれる手前には
線を引かず、導流帯の縁を分かれ切った所から引く。実物の標示の規則書は引いていない）。内側の線は道の外の縁なので、そのまま引く。
"""
import math

from mathutils import Vector

from .core import TILE, arc, straight
from .road_parts import EDGE_LINE, SWITCH_DIAG_EDGES, WearPath

HALF = TILE / 2
AX = {"n": (0, 1), "s": (0, -1), "e": (1, 0), "w": (-1, 0)}

# T字の名前 → (根元の向き, 腕のカーブの角 2 つ)。線路の track_sheet の ex_switches（switch_arcs）と同じ並び
EX_TEES = {"nse": ("e", ("ne", "se")), "new": ("n", ("ne", "nw")), "nsw": ("w", ("sw", "nw")), "sew": ("s", ("sw", "se"))}

# 円弧の腕: 角 → (円の中心, 始まりの角度, 終わりの角度)。sheetlib の road_sheet の arc_sw・arc_nw・arc_ne・arc_se と同じ
_ARC_ARGS = {"ne": ((HALF, HALF), 180, 270), "se": ((HALF, -HALF), 90, 180), "sw": ((-HALF, -HALF), 0, 90), "nw": ((-HALF, HALF), -90, 0)}

# 帯の内側かどうかを測るときの余裕（ちょうど帯の縁にある線を落とさない）と、線を刻む間隔
BAND_EPS = 0.06
# 腕と腕の間の線（Y字の外側の線・三方分岐の通り抜ける道の縁）は、根元から各腕へ進む車の通り道を実線で塞がないように、
# 腕が分かれ切った所（ほかの道の帯の縁）からさらにこの距離だけ離れた所から先だけに引く（ユーザーの指摘、#210）
GORE_GAP = 1.5
# 腕と腕の間の線は、分かれ切った所（隣の腕の帯の縁）で、隣の線と鋭角（V 字）につなぐ。帯の縁をこの距離だけ越えて引いて、継ぎ目を重ねる
# （ユーザーの指摘、#210: 途切れていた線をつなぐ。V 字の頂点は分かれ切った所で、根元の側へは伸ばさない）
GORE_JOIN = 0.15
STEP = 0.15


class Arm:
    """分岐の腕 1 本: center（中心線）・halfw（車道の半幅）・inner（角の側の線）・outer（反対側の線）・wear（轍の経路）"""

    def __init__(self, center, halfw, inner, outer, wear):
        self.center, self.halfw, self.inner, self.outer, self.wear = center, halfw, inner, outer, wear


def make_arm(corner, shape, diag_ext, diag_d=None):
    """角 corner（"ne" など。arc_ne は北と東をつなぐ）の腕。shape は "arc" か "diag"。
    diag_ext は斜めの経路の延長（sheetlib の DIAG_EXT）、diag_d は斜めの白線の経路からの距離（無ければ EDGE_LINE の 1/√2 倍。
    画面で横向きの斜め se・nw は、1 行に収めるために画素へ丸めた値を渡す）"""
    if shape == "arc":
        c, a0, a1 = _ARC_ARGS[corner]
        path = arc(c, a0, a1)
        # 円の中心は角にある。中心に近い側（半径が小さい）が角の側の線
        return Arm(path, EDGE_LINE, arc(c, a0, a1, radius=HALF - EDGE_LINE), arc(c, a0, a1, radius=HALF + EDGE_LINE), path)
    ea, eb = SWITCH_DIAG_EDGES[corner]
    a, b = Vector(AX[ea]), Vector(AX[eb])
    pa, pb = a * HALF, b * HALF
    t = (pb - pa).normalized()
    nrm = (a + b).normalized()  # 角の側（腕の中心線に直角）
    d = EDGE_LINE / math.sqrt(2) if diag_d is None else diag_d
    ends = lambda off: [pa - t * diag_ext + off, pb + t * diag_ext + off]
    return Arm(straight(pa, pb, ext=diag_ext), EDGE_LINE / math.sqrt(2), ends(nrm * d), ends(-nrm * d),
               WearPath(straight(pa, pb, ext=diag_ext), diag=True))


def _dist(p, poly):
    """点 p から折れ線 poly までの距離"""
    best = 1e9
    for i in range(len(poly) - 1):
        a, b = poly[i], poly[i + 1]
        ab = b - a
        t = 0.0 if ab.length < 1e-9 else max(0.0, min(1.0, (p - a).dot(ab) / ab.dot(ab)))
        best = min(best, (p - (a + ab * t)).length)
    return best


def _dense(poly, step=STEP):
    """折れ線を step ごとに刻んだ点列"""
    out = []
    for i in range(len(poly) - 1):
        a, b = Vector(poly[i]), Vector(poly[i + 1])
        n = max(1, int(math.ceil((b - a).length / step)))
        out += [a.lerp(b, k / n) for k in range(n)]
    out.append(Vector(poly[-1]))
    return out


def outside_runs(poly, bands, eps=BAND_EPS):
    """折れ線 poly のうち、bands（(中心線, 半幅) の並び）のどの帯の中にも入らない連続した区間（点列）の並びを返す"""
    runs, cur = [], []
    for p in _dense(poly):
        if any(_dist(p, c) < w - eps for c, w in bands):
            if len(cur) > 1:
                runs.append(cur)
            cur = []
        else:
            cur.append(p)
    if len(cur) > 1:
        runs.append(cur)
    return runs


def center_paths(arms, through=None):
    """腕と通り抜ける道（through = (中心線, 半幅)。三方分岐だけ）の中央線の経路（(番号, 点列) の並び。番号は腕の位置、通り抜ける道は -1）。
    ほかの道の帯の中（と、そこから GORE_GAP 以内）に入る所は落とし、根元から各腕へ進む車の通り道を中央線で横切らない"""
    roads = [(a.center, a.halfw) for a in arms] + ([through] if through else [])
    out = []
    for i, (c, _w) in enumerate(roads):
        others = [r for j, r in enumerate(roads) if j != i]
        out += [(i if i < len(arms) else -1, run) for run in outside_runs(c, others, -GORE_GAP)]
    return out


def edge_lines(arms, through=None):
    """腕と通り抜ける道（through = (中心線, 半幅)。三方分岐だけ）の白線（(点列, 0.0) の並び）。
    それぞれの外側・内側の線から、ほかの道の帯の中に入る所を落とす"""
    roads = [(a.center, a.halfw) for a in arms] + ([through] if through else [])
    out = []
    for i, a in enumerate(arms):
        others = [r for j, r in enumerate(roads) if j != i]
        # 内側（角の側）の線は道の外の縁。外側の線は腕と腕の間の線で、分かれ切った所から先だけ
        out += [(run, 0.0) for run in outside_runs(a.inner, others)]
        out += [(run, 0.0) for run in outside_runs(a.outer, others, GORE_JOIN)]
    if through:
        # 通り抜ける道の両側の線（半幅だけ離れた線）も、腕の帯の中に入る所を落とす
        c, w = through
        p0, p1 = Vector(c[0]), Vector(c[-1])
        t = (p1 - p0).normalized()
        n = Vector((t.y, -t.x))
        for s in (1, -1):
            line = [p0 + n * (w * s), p1 + n * (w * s)]
            out += [(run, 0.0) for run in outside_runs(line, [(a.center, a.halfw) for a in arms], GORE_JOIN)]
    return out
