"""架線（柱・梁・吊り金具・トロリ線）の形と寸法（共通の描画の道具 sheetlib の一部。tools/README.md）。

線路の壁の way-object に架線を持たせた版（AMI の ami_wall_rail_<版>_catenary。ADR 0003）で使う。どれも高さのある部品（tall）で、
壁と同じく way の絵には描かず、壁の way-object のシートに描く。
部品の名前はどれも cat_ で始める（select_walls・trim_catenary が壁と分けて扱う）。

- 柱（cat_poleL・cat_poleR）: 壁の上に立つ。経路の上でタイルの中心にいちばん近い点の横。版の選び方は壁と同じ
  （single は両側、back は奥、front は手前、center は無し。select_walls）
- 梁（cat_beam）: 柱の上を、線路を横切る向きに渡す。壁のある側は壁の外の面で止め、壁の無い側はタイルの端まで延ばす
  （隣の線の梁とつながる。trim_catenary）。center は梁だけ
- 吊り金具（cat_hanger）: 梁からちょう架線を吊る 1px の縦線
- ハンガー（cat_dropper）: ちょう架線からトロリ線へ下ろす 1px の縦線。タイルの中に等間隔（画面の横 16px ごと）
- トロリ線（cat_wire）・ちょう架線（cat_messenger）: 経路に沿う上下 2 本の線。分岐・十字では全部の経路に張る。
  1px ほどの細い線なので Part.thin（高さのある部品の層で、半透明の画素も THIN_ALPHA 以上なら残す）

柱・梁・吊り金具（group "catenary_support"）は経路が 1 本のセルだけに作る（track_sheet。分岐・十字に経路ごとの門ができないように）。
線（group "catenary"）は全部のセルに作る。梁・吊り金具・線は、車両より手前の絵（Part.front）に描く。
"""
import math

from mathutils import Vector

from .core import (  # noqa: F401
    H,
    PX_PER_UNIT,
    Part,
    TILE,
    box,
    merge,
    sweep,
)
from .wall_parts import (  # noqa: F401
    WALL_H,
    WALL_U,
    WALL_W,
)

# 高さは路盤（道床の基準面）から。部品の座標 1 単位は、画面の縦で約 7.8px（H = 16px が 1 段）、横で約 9.05px（PX_PER_UNIT）。
# 線は pak128 の架線（infrastructure/catenary_all の classic_catenary）と同じく上下 2 本: 上がちょう架線、下がトロリ線。
# pak128 はタイルの中心で地面から下 約 24px・上 約 28px、どちらも 1px（2026-11-18 に測った。way-addon.md の 10 章）
CAT_WIRE_Z = 3.0         # トロリ線（下の線）の下の面（線の中ほどで約 24px）
CAT_MESSENGER_Z = CAT_WIRE_Z + H / 4  # ちょう架線（上の線）の下の面（トロリ線のちょうど 4px 上。画素への乗り方を下の線とそろえる）
# 線の太さ。直線は線が画面で 2:1 に傾くので、横幅と縦の厚みの両方が画面の縦の太さになる。合わせて約 1px（1 行に 2px ずつの階段）
CAT_WIRE_W = 0.05        # 線の横幅
CAT_WIRE_H = 0.09        # 線の縦の厚み
# 斜めの線は、線の中心が画素の境に来て、1px の線が半透明の 2 列（2 行）になった（2026-11-18）。半画素ずらして画素の中心に乗せる
# 画面で縦向きの斜め（sw・ne）は、線の横幅だけが画面の幅になる
CAT_WIRE_W_DIAG = 0.12   # 画面で縦向きの斜めの線の横幅（約 1px）
CAT_DIAG_SHIFT = 0.5 / PX_PER_UNIT  # 画面で縦向きの斜めの線を、画面の右へずらす量（半画素）
CAT_DIAG_SHIFT_Z = H / 32  # 画面で横向きの斜め（nw・se）の線を上げる量（半画素）
CAT_POLE_TOP = 5.2       # 柱の上端（約 41px）
CAT_POLE_S = 0.35        # 柱の太さ（約 3px）
CAT_POLE_U = WALL_U + WALL_W / 2  # 柱の横位置（経路の中心から。壁の厚みの真ん中）
CAT_BEAM_H = 0.35        # 梁の高さ（上端は柱の上端にそろえる）
CAT_BEAM_T = 0.25        # 梁の、線路に沿う向きの厚み
CAT_BEAM_REACH = TILE    # 梁の、経路から横への長さ（直線。タイルの外は切り抜きで落とす）
# 斜めの梁の長さ（タイルの角と中心まで。近い斜めの隣の線の梁と中心でつながる）。中心でちょうど止めると、輪郭の画素を捨てる処理で
# 両側が 1〜3px ずつ欠けて、近い斜めの複線の梁の間に隙間が見えた（2026-11-18）。中心の先へ CAT_BEAM_OVERLAP_DIAG だけ重ねる
CAT_BEAM_OVERLAP_DIAG = 0.5
CAT_BEAM_REACH_DIAG = TILE / (2 * math.sqrt(2)) + CAT_BEAM_OVERLAP_DIAG
# 吊り金具（梁からちょう架線へ下ろす）とハンガー（ちょう架線からトロリ線へ下ろす）は、画面で 1px の縦線（Part.thin）。
# 画面の横の位置を画素の中心に乗せる（_snap_x）。pak128 の架線は、直線で画面の横 16px ごとにハンガーがある（2026-11-18 に測った）
CAT_HANGER_PX = 1.0      # 吊り金具・ハンガーの、画面での太さ（px）
CAT_DROPPER_N = 4        # 直線の 1 タイルのハンガーの数（タイルの長さの 1/4 ずつ。画面の横 16px ごと）
CAT_DROPPER_N_DIAG = 4   # 画面で横向きの斜めの 1 タイルのハンガーの数（同じく画面の横 16px ごと）。画面で縦向きの斜めは、2 本の線が重なるので無し

# 架線の部品が使う高さの範囲（render_layers の持ち分を上へ広げる行数を決める。柱の上端 + 余白）
CAT_RISE = int(math.ceil(CAT_POLE_TOP * 7.84)) + 6

_M_POLE = ("cat_pole", (0.55, 0.57, 0.58), 0.6, 0.3)
_M_BEAM = ("cat_beam", (0.50, 0.52, 0.53), 0.6, 0.3)
_M_WIRE = ("cat_wire", (0.16, 0.13, 0.11), 0.5, 0.5)


def _anchor(path):
    """経路の上で、タイルの中心にいちばん近い点と、そこでの経路の向き（平面の単位ベクトル）。"""
    best = None
    for a, b in zip(path[:-1], path[1:]):
        a2, b2 = Vector((a.x, a.y)), Vector((b.x, b.y))
        ab = b2 - a2
        if ab.length < 1e-9:
            continue
        t = max(0.0, min(1.0, -a2.dot(ab) / ab.length_squared))
        p = a2 + ab * t
        if best is None or p.length < best[0].length:
            best = (p, ab.normalized())
    return best


def _diag(k):
    return k < 0.99  # 斜め（横幅の倍率が 1 より小さい）


def _pole_shape(s):
    """柱（s=-1 が左、1 が右。sweep の横の向きと同じ）。壁の上端から CAT_POLE_TOP まで。"""
    def shape(path, k):
        p, d = _anchor(path)
        c = p + Vector((d.y, -d.x)) * (s * CAT_POLE_U * k)
        z0 = WALL_H
        return box(c.x, c.y, (z0 + CAT_POLE_TOP) / 2, CAT_POLE_S, CAT_POLE_S, CAT_POLE_TOP - z0, rot=math.atan2(d.y, d.x))
    return shape


def _beam_shape(path, k):
    """梁: 柱の上端の高さで、経路を横切る向きに両側へ延ばす（壁の外は trim_catenary で削る）。"""
    p, d = _anchor(path)
    reach = CAT_BEAM_REACH_DIAG if _diag(k) else CAT_BEAM_REACH
    return box(p.x, p.y, CAT_POLE_TOP - CAT_BEAM_H / 2, CAT_BEAM_T, 2 * reach, CAT_BEAM_H, rot=math.atan2(d.y, d.x))


def _screen_vertical(d):
    """平面の向き d が、画面で縦向き（sw・ne の斜め）か。画面の横の位置は x + y で決まる（カメラは Z 45°）。"""
    return abs(d.x + d.y) < 1e-6 * d.length


def _line_z(path, k, z):
    """線の下の面の高さ（画面で横向きの斜めは半画素上げる。_line_shape）。"""
    if _diag(k) and not _screen_vertical(path[-1] - path[0]):
        return z + CAT_DIAG_SHIFT_Z
    return z


def _snap_x(p):
    """平面の点 p を、画面の横で画素の中心に来るよう、画面の右（平面の (1, 1) の向き）へ 1 画素未満ずらす。
    セルの中心（平面の原点）は画素の境にある（CELL が偶数）。"""
    sx = (p.x + p.y) / math.sqrt(2) * PX_PER_UNIT
    s = ((0.5 - sx) % 1.0) / PX_PER_UNIT / math.sqrt(2)
    return Vector((p.x + s, p.y + s))


def _thin_post(p, d, z0, z1):
    """画面で 1px（CAT_HANGER_PX）の縦線になる細い角柱。p は平面の点、d は経路の向き。"""
    r = Vector((1, 1)).normalized()
    n = Vector((d.y, -d.x))
    side = CAT_HANGER_PX / (PX_PER_UNIT * (abs(d.dot(r)) + abs(n.dot(r))))
    c = _snap_x(p)
    return box(c.x, c.y, (z0 + z1) / 2, side, side, z1 - z0, rot=math.atan2(d.y, d.x))


def _hanger_shape(path, k):
    """吊り金具: 梁の下の面からちょう架線まで、経路の中心に下がる。"""
    p, d = _anchor(path)
    return _thin_post(p, d, _line_z(path, k, CAT_MESSENGER_Z), CAT_POLE_TOP - CAT_BEAM_H)


def _dropper_shape(path, k):
    """ハンガー: ちょう架線からトロリ線へ下ろす縦線。タイルの中を等間隔に、経路のある所だけ。
    画面で縦向きの斜めは 2 本の線が重なって見えるので作らない（pak128 も無い）。"""
    p, d = _anchor(path)
    if _diag(k) and _screen_vertical(d):
        return None
    n, length = (CAT_DROPPER_N_DIAG, TILE / math.sqrt(2)) if _diag(k) else (CAT_DROPPER_N, TILE)
    along = [(Vector((q.x, q.y)) - p).dot(d) for q in path]
    lo, hi = min(along), max(along)
    z0 = _line_z(path, k, CAT_WIRE_Z)
    z1 = _line_z(path, k, CAT_MESSENGER_Z) + CAT_WIRE_H
    posts = []
    for i in range(n):
        o = (i + 0.5) * length / n - length / 2
        c = p + d * o
        if lo - 1e-6 <= o <= hi + 1e-6 and max(abs(c.x), abs(c.y)) <= TILE / 2:
            posts.append(_thin_post(c, d, z0, z1))
    return merge(posts) if posts else None


def _line_shape(z):
    """架線の線（トロリ線・ちょう架線）: 経路の中心に沿う細い角棒。下の面が z。"""
    def shape(path, k, z=z):
        u = CAT_WIRE_W / 2
        z = _line_z(path, k, z)  # 画面で横向きの斜め: 線の中心が画素の境に来て 2 行になったので、上へ半画素ずらす
        if _diag(k) and _screen_vertical(path[-1] - path[0]):
            # 画面で縦向きの斜め: 画面の右（平面の (1, 1) の向き）へ半画素ずらす
            u = CAT_WIRE_W_DIAG / 2
            s = CAT_DIAG_SHIFT / math.sqrt(2)
            path = [p + Vector((s, s, 0)[:len(p)]) for p in path]
        return sweep(path, [(-u, z), (u, z), (u, z + CAT_WIRE_H), (-u, z + CAT_WIRE_H)])
    return shape


CATENARY_PARTS = (
    Part("cat_poleL", "bed", "bed", _M_POLE, _pole_shape(-1), "catenary_support", tall=True),
    Part("cat_poleR", "bed", "bed", _M_POLE, _pole_shape(1), "catenary_support", tall=True),
    Part("cat_beam", "bed", "bed", _M_BEAM, _beam_shape, "catenary_support", tall=True, front=True, widen=True),
    Part("cat_hanger", "bed", "bed", _M_WIRE, _hanger_shape, "catenary_support", tall=True, front=True, thin=True),
    Part("cat_dropper", "bed", "bed", _M_WIRE, _dropper_shape, "catenary", tall=True, front=True, thin=True),
    Part("cat_wire", "bed", "bed", _M_WIRE, _line_shape(CAT_WIRE_Z), "catenary", tall=True, front=True, thin=True),
    Part("cat_messenger", "bed", "bed", _M_WIRE, _line_shape(CAT_MESSENGER_Z), "catenary", tall=True, front=True, thin=True),
)


def is_catenary(ob):
    return str(ob.get("pname", "")).startswith("cat_")
