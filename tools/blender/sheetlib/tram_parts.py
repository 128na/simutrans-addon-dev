"""路面軌道（tram）の部品（コンクリートで固めた床・縁の明るい帯・レールの頭・溝と、レールの周りのさび）。
道路の上に重ねて敷く想定で、どれも路面（高さ 0）のすぐ上の薄い板にする。レールの横位置は線路の部品（track_parts）と同じ。
TRACK_PROFILES の "track_parts"・"replace"・"snow_skin" に渡す（共通の描画の道具 sheetlib の一部。tools/README.md）。

見た目の手本は AMI の README の「見た目の手本」（ユーザーから受け取った写真の書き起こし）: 床はコンクリートで固め、レールの頭だけが床の面に出る。
レールの内側と周りにさび色の汚れの帯、軌道の縁は明るい色の帯。
"""
from dataclasses import replace

from mathutils import Vector

from .core import Part, merge, sweep
from .track_parts import RAIL_IN, RAIL_OUT, TRACK_EXTRAS, _edge_reach, _mix, _trim_inner_ends, track_noise

# ---------------------------------------------------------------- 断面（部品の 1 単位 ≈ 9px。高さは路面 0 から上へ薄く積む）
# 床の上面を路面（道路の asphalt の上面 0）よりわずかに上にし、道路の上に重ねたときに路面を隠す。厚みは画面で 1px 未満（段に見せない）
TRAM_BED_U = 1.05            # コンクリートの床の半幅（レールの外から約 0.5。斜めは線路の道床と同じ 1/√2 倍）
TRAM_BED_Z0, TRAM_BED_Z1 = 0.0, 0.006
TRAM_EDGE_U0 = 0.87          # 縁の明るい帯の内側（外側は床の縁 TRAM_BED_U。画面で約 1.5px。0.93 では 1px に満たず見えなかった）
# 縁の帯は、床の全幅（TRAM_BED_U）の明るい板を床の下に敷き、その上に縁の帯の内側までの床（TRAM_EDGE_U0）を重ねて作る。
# T字・十字では、ほかの経路の床が縁の帯を覆うので、帯はつないだ床の外周にだけ出る（帯を床の上に描くと、分岐の中を横切る明るい線になった）
TRAM_EDGE_Z1 = TRAM_BED_Z1 - 0.001
# レールの頭（経路の中心からの横位置）。線路のレール（track_parts の RAIL_IN・RAIL_OUT、0.41〜0.55）より少し太く、頭が画面で 1px を超えて見える幅
# （精細化のラウンド 1、#56。docs/records/2026-11-20_ami-tram-refine-round1.md）
TRAM_RAIL_IN, TRAM_RAIL_OUT = 0.40, 0.54
TRAM_GROOVE_W = 0.14         # レールの内側の溝（車輪のフランジの通り道）の幅。細いと画面で 1px に満たず、レールが床に埋もれて見えた（ラウンド 1 で 0.11 → 0.14）
# レールの外側の目地は描かない（ラウンド 1。明るい頭と溝の 2 本線で読ませ、頭の外の暗い線で灰色の帯に見えるのを避けた）
# 画面で横向きの斜め（北東–南西へ走る経路。diag_nw・diag_se・close1 と、曲線の中ほど）では、経路に直角な向きが画面の縦になり、1 単位が約 4.5px
# （直線・縦向きの斜めは約 9px）で、頭と溝が 1px に満たず消える。そこだけ頭と溝の幅を広げる（頭の中心は同じ。ラウンド 4）
TRAM_HDIAG_HEAD = 2.2
TRAM_HDIAG_GROOVE = 1.4
TRAM_GROOVE_Z = TRAM_BED_Z1 + 0.001
TRAM_RAIL_Z0, TRAM_RAIL_Z1 = TRAM_BED_Z1, 0.014   # レールの頭（床の面からわずかに出る）
TRAM_TH = 0.001              # 帯の厚み

# 汚れの帯（部品の名前 → 経路の中心からの (u0, u1)、さび色への寄せ具合）。線路の汚れ（rust0・rust1・oil）と同じ名前で差し替える。
# 汚れは床の縁の帯より内に止める
TRAM_WEAR = (
    ("rust0", (RAIL_IN - 0.22, RAIL_OUT + 0.30), 0.40),
    ("rust1", (RAIL_IN - 0.10, RAIL_OUT + 0.12), 0.75),
)
# レールの間の油の帯は描かない（電車は油を落とさず、レールの間だけが暗い理由が無い。ラウンド 3）。線路の油の部品（oil）を差し替えて消すために、材質だけ残す
TRAM_OIL_T = 0.35

# ---------------------------------------------------------------- 色
TRAM_BED_LO, TRAM_BED_HI = (0.42, 0.42, 0.40), (0.50, 0.50, 0.48)   # コンクリート（道路の路面より明るい灰色のまだら）
TRAM_BED_GRAIN = 5.0
TRAM_BED_RGB = tuple((a + b) / 2 for a, b in zip(TRAM_BED_LO, TRAM_BED_HI))
TRAM_EDGE_RGB = (0.66, 0.65, 0.61)       # 縁の帯（床より明るい灰色。明るい頭と並んで明るい線が 4 本に見えたので暗くした。ラウンド 2）
TRAM_GROOVE_RGB = (0.03, 0.03, 0.028)    # 溝（影で暗い）
# 車輪で磨かれた頭（明るい鋼の色）。金属の材質は環境を映して暗く写るので、金属 0 の明るい色にする（在来線の頭の帯と同じ。ラウンド 1）
_M_TRAM_RAIL = ("tram_rail", (0.92, 0.91, 0.88), 0.4, 0.0)
_RUST_LO, _RUST_HI = (0.26, 0.21, 0.16), (0.36, 0.30, 0.23)   # track_parts の汚れのさびと同じ
_OIL_LO, _OIL_HI = (0.06, 0.055, 0.05), (0.13, 0.12, 0.11)

_M_TRAM_BED = track_noise("tram_bed", TRAM_BED_LO, TRAM_BED_HI, TRAM_BED_GRAIN)
_M_TRAM_EDGE = ("tram_edge", TRAM_EDGE_RGB, 0.8)
_M_TRAM_GROOVE = ("tram_groove", TRAM_GROOVE_RGB, 0.9)


def _section(u0, u1, z0, z1):
    return [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]


def _slab_shape(u, z0, z1):
    def shape(path, k):
        return sweep(path, _section(-u * k, u * k, z0, z1))
    return shape


def _to_edge(shape, inset=0.0):
    """形 shape(path, k) を、行き止まりの経路（始点だけがタイルの中）では始点を閉じた側のタイルの端から inset 手前まで延ばして作る。
    レールの終点（TRACK_PROFILES の end_from_edge）より奥まで床を敷く（在来線の道床 bed_to_edge_shape と同じ考え方）"""
    def f(path, k):
        e = _edge_reach(path)
        if e is not None:
            reach, d = e
            path = [path[0] - d * (reach - inset)] + list(path)
        return shape(path, k)
    return f


def _pair_shape(u0, u1, z0, z1):
    """経路の両側に 1 本ずつの帯（中心から u0〜u1）。"""
    def shape(path, k):
        return merge([sweep(path, [(s * u, z) for u, z in _section(u0 * k, u1 * k, z0, z1)][::s]) for s in (1, -1)])
    return shape


def _widen(t, f):
    """経路の向き t での、頭と溝の幅の倍率。画面で横向きの斜め（経路の座標 x は東・y は北で、t.x * t.y > 0）で f、軸の向きと縦向きの斜めで 1。
    曲線は点ごとの向きで倍率が変わる"""
    if f == 1.0:
        return 1.0
    h = max(0.0, 2 * t.x * t.y / max(t.length_squared, 1e-12))
    return 1.0 + (f - 1.0) * h


def _var_sweep(path, section):
    """core.sweep と同じ押し出しで、断面を点ごとの向き t から section(t) で決める"""
    rings = []
    for i, p in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, len(path) - 1)]
        t = (b - a).normalized()
        nv = Vector((t.y, -t.x, 0))
        rings.append([Vector((p.x, p.y, 0)) + nv * u + Vector((0, 0, v)) for u, v in section(t)])
    n = len(rings[0])
    verts = [v for ring in rings for v in ring]
    faces = []
    for i in range(len(rings) - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j))
    faces.append(tuple(reversed(range(n))))
    last = (len(rings) - 1) * n
    faces.append(tuple(last + j for j in range(n)))
    return verts, faces


def _head_span(t):
    """レールの頭の (u0, u1)。頭の中心のまま、画面で横向きの所で幅を広げる"""
    c, h = (TRAM_RAIL_IN + TRAM_RAIL_OUT) / 2, (TRAM_RAIL_OUT - TRAM_RAIL_IN) / 2 * _widen(t, TRAM_HDIAG_HEAD)
    return c - h, c + h


def _rail_shape(side):
    def shape(path, k):
        def section(t):
            a, b = (u * k for u in _head_span(t))
            return _section(-b, -a, TRAM_RAIL_Z0, TRAM_RAIL_Z1) if side < 0 else _section(a, b, TRAM_RAIL_Z0, TRAM_RAIL_Z1)
        return _var_sweep(path, section)
    return shape


def _groove_shape(path, k):
    """レールの頭の内側の溝（両側）。頭と同じく、画面で横向きの所で幅を広げる（倍率は TRAM_HDIAG_GROOVE）"""
    def side_section(sg):
        def section(t):
            a, _ = _head_span(t)
            w = TRAM_GROOVE_W * _widen(t, TRAM_HDIAG_GROOVE)
            return [(sg * u, z) for u, z in _section((a - w) * k, a * k, TRAM_GROOVE_Z, TRAM_GROOVE_Z + TRAM_TH)][::sg]
        return section
    return merge([_var_sweep(path, side_section(sg)) for sg in (1, -1)])


# 縁の帯と床は線路の道床と同じ横幅の倍率（bed）で、斜めでも直線と辺で同じ幅になる。溝・目地はレールと同じ倍率（gauge）
# 行き止まりでは、レールと溝はタイルの中（end_from_edge の所）で止め、縁の帯は閉じた側のタイルの端まで、床はそこから縁の帯の幅だけ手前まで
# 延ばす（閉じた端にも縁の帯が回る。在来線の道床もタイルの端まで。2026-11-20 のユーザーの指摘）
TRAM_END_BAND = TRAM_BED_U - TRAM_EDGE_U0
TRAM_TRACK_PARTS = (
    Part("tram_edge", "tram_bed", "bed", _M_TRAM_EDGE, _to_edge(_slab_shape(TRAM_BED_U, TRAM_BED_Z0, TRAM_EDGE_Z1))),
    Part("tram_bed", "tram_bed", "bed", _M_TRAM_BED, _to_edge(_slab_shape(TRAM_EDGE_U0, TRAM_BED_Z0, TRAM_BED_Z1), TRAM_END_BAND)),
    Part("tram_groove", "rail", "gauge", _M_TRAM_GROOVE, _groove_shape, centre=False),
    Part("railL", "rail", "gauge", _M_TRAM_RAIL, _rail_shape(-1)),
    Part("railR", "rail", "gauge", _M_TRAM_RAIL, _rail_shape(1)),
)


# ---------------------------------------------------------------- 汚れ（線路の汚れと同じ名前で差し替える。TRACK_PROFILES の "replace"）
# 床の上面のすぐ上に乗せ、溝・レールの下に入れる。まくらぎのさび（sleeper_rust）は、まくらぎが無いので作らない
def _wear_z(i):
    return TRAM_BED_Z1 + 0.0002 * (i + 1)


def _wear_pair(u0, u1, z):
    pair = _pair_shape(u0, u1, z, z + TRAM_TH / 4)
    return lambda path, k: pair(_trim_inner_ends(path), k)


def _wear_centre(u, z):
    return lambda path, k: sweep(_trim_inner_ends(path), _section(-u * k, u * k, z, z + TRAM_TH / 4))


def _tram_wear_parts():
    by_name = {p.name: p for p in TRACK_EXTRAS}
    out = {}
    for i, (name, (u0, u1), t) in enumerate(TRAM_WEAR):
        out[name] = replace(by_name[name], material=track_noise(f"tram_{name}", _mix(TRAM_BED_RGB, _RUST_LO, t),
                                                                _mix(TRAM_BED_RGB, _RUST_HI, t), 3.0),
                            shape=_wear_pair(u0, u1, _wear_z(i)))
    out["oil"] = replace(by_name["oil"], material=track_noise("tram_oil", _mix(TRAM_BED_RGB, _OIL_LO, TRAM_OIL_T),
                                                              _mix(TRAM_BED_RGB, _OIL_HI, TRAM_OIL_T), 3.0),
                         shape=lambda path, k: None)
    out["sleeper_rust"] = replace(by_name["sleeper_rust"], shape=lambda path, k: None)
    return out


TRAM_WEAR_REPLACE = _tram_wear_parts()

# 雪の絵（TRACK_PROFILES の "snow_skin"）: 道路の車道と同じく除雪されている想定で、夏と同じ材質に戻す
# （track_skin は雪の絵で汚れの帯を雪の上の汚れ（灰色）に差し替えるので、ここで上書きする）
TRAM_SNOW_SKIN = {name: part.material for name, part in TRAM_WEAR_REPLACE.items() if name != "sleeper_rust"}


# ---------------------------------------------------------------- T字・十字のすき間（TRACK_PROFILES の "cell_fills"）
# T字・十字の、曲線と 2 本の直線のあいだ（三角の所）を床で埋める。床は経路ごとの帯なので届かず、透明な穴（2〜5px）が残った
# （sheet_audit の holes。T字・分岐の絵の 24 セル。精細化のラウンド 2、#56）。
# 中心を通る直線があり、曲線の片端がその直線に来ているときだけ埋める（ふつうの曲線のセルは変えない）。T字は直線 + 枝の向きへの
# 曲線 2 本で、2 つの多角形を合わせると、直線と 2 本の曲線に囲まれた所になる。
# 高さは縁の帯より上・床より下（床と同じ材質。縁の帯は覆うが、汚れ・溝・レールは上に出る）
def _is_curve(p):
    return len(p) > 2


def _near_line(q, p):
    a, b = p[0], p[-1]
    d = b - a
    t = max(0.0, min(1.0, (q - a).dot(d) / d.length_squared))
    return (a + d * t - q).length < 0.3


def _gore_shape(paths):
    """セルの経路 paths から、すき間を埋める形（path, k → 形）を作る。埋める所が無ければ None"""
    straights = [p for p in paths if not _is_curve(p)]
    if not any(_near_line(Vector((0, 0)), s) for s in straights):
        return None
    z0, z1 = TRAM_BED_Z0, TRAM_BED_Z1 - 0.0005

    def shape(path, k):
        verts, faces = [], []
        for c in (p for p in paths if _is_curve(p)):
            pts = [Vector((q.x, q.y)) for q in c if max(abs(q.x), abs(q.y)) <= 5.0 + 1e-6]
            if len(pts) < 2:
                continue
            ends = (Vector((c[0].x, c[0].y)), Vector((c[-1].x, c[-1].y)))
            if not any(any(_near_line(e, s) for s in straights) for e in ends):
                continue
            # 曲線がタイルの辺に出る所（辺の中点）を両端に足す（隣の曲線の多角形と、中心から辺の中点への線でぴったり接する）
            mids = [Vector(m) for m in ((0, 5), (0, -5), (5, 0), (-5, 0))]
            m0, m1 = (min(mids, key=lambda m: (m - e).length) for e in ends)
            poly = [Vector((0.0, 0.0)), m0] + pts + [m1]
            o = len(verts)
            m = len(poly)
            verts += [Vector((v.x, v.y, z0)) for v in poly] + [Vector((v.x, v.y, z1)) for v in poly]
            faces += [(o, o + i + 1, o + i) for i in range(1, m - 1)]
            faces += [(o + m, o + m + i, o + m + i + 1) for i in range(1, m - 1)]
            faces += [(o + i, o + (i + 1) % m, o + m + (i + 1) % m, o + m + i) for i in range(m)]
            # 隣の曲線の多角形と接する線（中心から辺の中点）に細い帯を重ねる。接する線の上の画素が、どちらの多角形にも
            # 半分ずつしか掛からず、透明のまま残った（南向きの T字の 1px）
            for mid in (m0, m1):
                d = mid.normalized()
                nrm = Vector((-d.y, d.x)) * 0.15
                quad = [-nrm, nrm, mid + nrm, mid - nrm]
                o = len(verts)
                verts += [Vector((v.x, v.y, z0)) for v in quad] + [Vector((v.x, v.y, z1)) for v in quad]
                faces += [(o, o + 1, o + 2, o + 3), (o + 7, o + 6, o + 5, o + 4)]
                faces += [(o + i, o + (i + 1) % 4, o + 4 + (i + 1) % 4, o + 4 + i) for i in range(4)]
        return (verts, faces) if faces else None
    return shape


TRAM_CELL_FILLS = ((Part("tram_gore", "tram_bed", "bed", _M_TRAM_BED, None, centre=False), _gore_shape),)
