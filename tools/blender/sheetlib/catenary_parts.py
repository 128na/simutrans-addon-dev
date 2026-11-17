"""架線（柱・梁・吊り金具・トロリ線）の形と寸法（共通の描画の道具 sheetlib の一部。tools/README.md）。

線路の壁の way-object に架線を持たせた版（AMI の ami_wall_rail_<版>_catenary。ADR 0003）で使う。どれも高さのある部品（tall）で、
壁と同じく way の絵には描かず、壁の way-object のシートに描く。
部品の名前はどれも cat_ で始める（select_walls・trim_catenary が壁と分けて扱う）。

- 柱（cat_poleL・cat_poleR）: 壁の上に立つ。経路の上でタイルの中心にいちばん近い点の横。版の選び方は壁と同じ
  （single は両側、back は奥、front は手前、center は無し。select_walls）
- 梁（cat_beam）: 柱の上を、線路を横切る向きに渡す。壁のある側は壁の外の面で止め、壁の無い側はタイルの端まで延ばす
  （隣の線の梁とつながる。trim_catenary）。center は梁だけ
- 吊り金具（cat_hanger）: 梁からトロリ線を吊る
- トロリ線（cat_wire）: 経路に沿う。分岐・十字では全部の経路に張る

柱・梁・吊り金具（group "catenary_support"）は経路が 1 本のセルだけに作る（track_sheet。分岐・十字に経路ごとの門ができないように）。
トロリ線（group "catenary"）は全部のセルに作る。梁・吊り金具・トロリ線は、車両より手前の絵（Part.front）に描く。
"""
import math

from mathutils import Vector

from .core import (  # noqa: F401
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

# 高さは路盤（道床の基準面）から。部品の座標 1 単位は、画面の縦で約 7.8px（H = 16px が 1 段）。
# 手本の iss の架線（../iss/src/way-object/rail/catenary_new.dat）は、柱の上端が地面から約 41px、トロリ線が約 27px（2026-11-18 に測った）
CAT_WIRE_Z = 3.5         # トロリ線の下の面（約 27px）
CAT_WIRE_W = 0.22        # トロリ線の太さ（横・縦とも約 2px。細いと半透明の画素を捨てる処理で途切れる）
CAT_WIRE_H = 0.25
# 画面で縦向きの斜め（sw・ne）では、トロリ線の横幅だけが画面の幅になる。2px ちょうどだと画素の境にまたがって半透明の 2 列になり、
# 半透明の画素を捨てる処理で消えた（2026-11-18）。斜めは太くする
CAT_WIRE_W_DIAG = 0.34
CAT_POLE_TOP = 5.2       # 柱の上端（約 41px）
CAT_POLE_S = 0.35        # 柱の太さ（約 3px）
CAT_POLE_U = WALL_U + WALL_W / 2  # 柱の横位置（経路の中心から。壁の厚みの真ん中）
CAT_BEAM_H = 0.35        # 梁の高さ（上端は柱の上端にそろえる）
CAT_BEAM_T = 0.25        # 梁の、線路に沿う向きの厚み
CAT_BEAM_REACH = TILE    # 梁の、経路から横への長さ（直線。タイルの外は切り抜きで落とす）
CAT_BEAM_REACH_DIAG = TILE / (2 * math.sqrt(2))  # 斜めの梁の長さ（タイルの角と中心まで。近い斜めの隣の線の梁と中心でつながる）
CAT_HANGER_S = 0.25      # 吊り金具の太さ（細いと半透明の画素を捨てる処理で途切れる）

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


def _hanger_shape(path, k):
    """吊り金具: 梁の下の面からトロリ線の上の面まで、経路の中心に下がる。"""
    p, d = _anchor(path)
    z0, z1 = CAT_WIRE_Z + CAT_WIRE_H, CAT_POLE_TOP - CAT_BEAM_H
    return box(p.x, p.y, (z0 + z1) / 2, CAT_HANGER_S, CAT_HANGER_S, z1 - z0, rot=math.atan2(d.y, d.x))


def _wire_shape(path, k):
    """トロリ線: 経路の中心に沿う細い角棒。"""
    u = (CAT_WIRE_W_DIAG if _diag(k) else CAT_WIRE_W) / 2
    return sweep(path, [(-u, CAT_WIRE_Z), (u, CAT_WIRE_Z), (u, CAT_WIRE_Z + CAT_WIRE_H), (-u, CAT_WIRE_Z + CAT_WIRE_H)])


CATENARY_PARTS = (
    Part("cat_poleL", "bed", "bed", _M_POLE, _pole_shape(-1), "catenary_support", tall=True),
    Part("cat_poleR", "bed", "bed", _M_POLE, _pole_shape(1), "catenary_support", tall=True),
    Part("cat_beam", "bed", "bed", _M_BEAM, _beam_shape, "catenary_support", tall=True, front=True),
    Part("cat_hanger", "bed", "bed", _M_BEAM, _hanger_shape, "catenary_support", tall=True, front=True),
    Part("cat_wire", "bed", "bed", _M_WIRE, _wire_shape, "catenary", tall=True, front=True),
)


def is_catenary(ob):
    return str(ob.get("pname", "")).startswith("cat_")
