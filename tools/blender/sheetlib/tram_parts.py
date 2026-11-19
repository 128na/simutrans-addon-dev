"""路面軌道（tram）の部品（コンクリートで固めた床・縁の明るい帯・レールの頭・溝と、レールの周りのさび）。
道路の上に重ねて敷く想定で、どれも路面（高さ 0）のすぐ上の薄い板にする。レールの横位置は線路の部品（track_parts）と同じ。
TRACK_PROFILES の "track_parts"・"replace"・"snow_skin" に渡す（共通の描画の道具 sheetlib の一部。tools/README.md）。

見た目の手本は AMI の README の「見た目の手本」（ユーザーから受け取った写真の書き起こし）: 床はコンクリートで固め、レールの頭だけが床の面に出る。
レールの内側と周りにさび色の汚れの帯、軌道の縁は明るい色の帯。
"""
from dataclasses import replace

from .core import Part, merge, sweep
from .track_parts import RAIL_IN, RAIL_OUT, TRACK_EXTRAS, _mix, _trim_inner_ends, track_noise

# ---------------------------------------------------------------- 断面（部品の 1 単位 ≈ 9px。高さは路面 0 から上へ薄く積む）
# 床の上面を路面（道路の asphalt の上面 0）よりわずかに上にし、道路の上に重ねたときに路面を隠す。厚みは画面で 1px 未満（段に見せない）
TRAM_BED_U = 1.05            # コンクリートの床の半幅（レールの外から約 0.5。斜めは線路の道床と同じ 1/√2 倍）
TRAM_BED_Z0, TRAM_BED_Z1 = 0.0, 0.006
TRAM_EDGE_U0 = 0.87          # 縁の明るい帯の内側（外側は床の縁 TRAM_BED_U。画面で約 1.5px。0.93 では 1px に満たず見えなかった）
# 縁の帯は、床の全幅（TRAM_BED_U）の明るい板を床の下に敷き、その上に縁の帯の内側までの床（TRAM_EDGE_U0）を重ねて作る。
# T字・十字では、ほかの経路の床が縁の帯を覆うので、帯はつないだ床の外周にだけ出る（帯を床の上に描くと、分岐の中を横切る明るい線になった）
TRAM_EDGE_Z1 = TRAM_BED_Z1 - 0.001
TRAM_GROOVE_W = 0.11         # レールの内側の溝（車輪のフランジの通り道）の幅。細いと画面で 1px に満たず、レールが床に埋もれて見えた
TRAM_SEAM_W = 0.05           # レールの外側の目地（床とレールの境の暗い線。pak128 の Tram_Track_050_A もレールの両側に暗い縁がある）
TRAM_GROOVE_Z = TRAM_BED_Z1 + 0.001
TRAM_RAIL_Z0, TRAM_RAIL_Z1 = TRAM_BED_Z1, 0.014   # レールの頭（床の面からわずかに出る）
TRAM_TH = 0.001              # 帯の厚み

# 汚れの帯（部品の名前 → 経路の中心からの (u0, u1)、さび色への寄せ具合）。線路の汚れ（rust0・rust1・oil）と同じ名前で差し替える。
# 汚れは床の縁の帯より内に止める
TRAM_WEAR = (
    ("rust0", (RAIL_IN - 0.22, RAIL_OUT + 0.30), 0.40),
    ("rust1", (RAIL_IN - 0.10, RAIL_OUT + 0.12), 0.75),
)
TRAM_OIL_U = 0.18            # レールの間の中ほどの油の帯の半幅（行き来する車両の落とす油。線路より細く薄い）
TRAM_OIL_T = 0.35

# ---------------------------------------------------------------- 色
TRAM_BED_LO, TRAM_BED_HI = (0.42, 0.42, 0.40), (0.50, 0.50, 0.48)   # コンクリート（道路の路面より明るい灰色のまだら）
TRAM_BED_GRAIN = 5.0
TRAM_BED_RGB = tuple((a + b) / 2 for a, b in zip(TRAM_BED_LO, TRAM_BED_HI))
TRAM_EDGE_RGB = (0.80, 0.79, 0.74)       # 縁の明るい帯（道路の白線より黄みのある白。白線と見分ける）
TRAM_GROOVE_RGB = (0.03, 0.03, 0.028)    # 溝（影で暗い）
_M_TRAM_RAIL = ("tram_rail", (0.82, 0.81, 0.79), 0.25, 0.8)   # 車輪で磨かれた頭（在来線のレールの赤茶より明るい鋼の色）
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


def _pair_shape(u0, u1, z0, z1):
    """経路の両側に 1 本ずつの帯（中心から u0〜u1）。"""
    def shape(path, k):
        return merge([sweep(path, [(s * u, z) for u, z in _section(u0 * k, u1 * k, z0, z1)][::s]) for s in (1, -1)])
    return shape


def _rail_shape(side):
    def shape(path, k):
        a, b = RAIL_IN * k, RAIL_OUT * k
        return sweep(path, _section(-b, -a, TRAM_RAIL_Z0, TRAM_RAIL_Z1) if side < 0 else _section(a, b, TRAM_RAIL_Z0, TRAM_RAIL_Z1))
    return shape


# 縁の帯と床は線路の道床と同じ横幅の倍率（bed）で、斜めでも直線と辺で同じ幅になる。溝・目地はレールと同じ倍率（gauge）
TRAM_TRACK_PARTS = (
    Part("tram_edge", "tram_bed", "bed", _M_TRAM_EDGE, _slab_shape(TRAM_BED_U, TRAM_BED_Z0, TRAM_EDGE_Z1)),
    Part("tram_bed", "tram_bed", "bed", _M_TRAM_BED, _slab_shape(TRAM_EDGE_U0, TRAM_BED_Z0, TRAM_BED_Z1)),
    Part("tram_groove", "rail", "gauge", _M_TRAM_GROOVE,
         _pair_shape(RAIL_IN - TRAM_GROOVE_W, RAIL_IN, TRAM_GROOVE_Z, TRAM_GROOVE_Z + TRAM_TH), centre=False),
    Part("tram_seam", "rail", "gauge", _M_TRAM_GROOVE,
         _pair_shape(RAIL_OUT, RAIL_OUT + TRAM_SEAM_W, TRAM_GROOVE_Z, TRAM_GROOVE_Z + TRAM_TH), centre=False),
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
                         shape=_wear_centre(TRAM_OIL_U, _wear_z(len(TRAM_WEAR))))
    out["sleeper_rust"] = replace(by_name["sleeper_rust"], shape=lambda path, k: None)
    return out


TRAM_WEAR_REPLACE = _tram_wear_parts()

# 雪の絵（TRACK_PROFILES の "snow_skin"）: 道路の車道と同じく除雪されている想定で、夏と同じ材質に戻す
# （track_skin は雪の絵で汚れの帯を雪の上の汚れ（灰色）に差し替えるので、ここで上書きする）
TRAM_SNOW_SKIN = {name: part.material for name, part in TRAM_WEAR_REPLACE.items() if name != "sleeper_rust"}
