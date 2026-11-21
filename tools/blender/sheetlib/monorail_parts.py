"""跨座式モノレールの部品（軌道桁と、高架の柱・腕）。TRACK_PROFILES の "track_parts"・"cell_fills"・"snow_skin" に渡す
（共通の描画の道具 sheetlib の一部。tools/README.md）。

手本は iss の跨座式モノレール（refs の iss/src/way/monorail/straddle.dat と、配布物の straddle_g.png・straddle_e_<版>.png）:
    - 地上の版: 桁だけ。桁の下面は地面、上面は地面から約 0.7（画面で桁の帯の高さ 11px）、幅は約 0.85。
      跨座式の車両（pak128.japan の車両）は、車体の下端が地面の高さに描かれ、裾が桁を隠す
    - 高架の版（front・center・back）: 桁がタイルを出入りする辺ごとに、その辺の角に柱を立て、柱の頭から辺の中点の桁の下へ腕を渡す。
      front は手前（南・東）の側の角、back は奥（北・西）の側の角、center は両側の角。行き止まりは桁の端にも同じ腕と柱
AMI では、柱をタイルの角ちょうどでなく、タイルの内側に面を合わせて立てる（門型の橋脚 PIER_GATE_* と同じ。タイルの角に立てると、
絵がタイルの持ち分で切られて柱が半分になる）。隣のタイルの柱と背中合わせになり、2 本で 1 本の太い柱に見える。
高架の桁は、上面を地上と同じ高さにしたまま、下へ深くする（iss の高架の桁は地上と同じ断面。AMI は実物の桁の高さに寄せた）。
"""
import math

from mathutils import Vector

from .core import H, TILE, Part, box, merge, sweep
from .track_parts import track_noise
from .wall_parts import ELEV_STEPS, PIER_FOOT

# ---------------------------------------------------------------- 寸法（部品の 1 単位 ≈ 9px。高さ 1 単位 ≈ 7.8px）
MONO_BEAM_W = 0.85        # 桁の幅（iss の地上の桁の画面の帯から測った値）
MONO_BEAM_TOP = 0.7       # 桁の上面の高さ（way の高さから。iss の地上の桁は地面からこの高さまで）
MONO_ELEV_BEAM_D = 1.6    # 高架の桁の深さ（上面から。下面は way の高さより MONO_BEAM_TOP − これ だけ下）
MONO_TOP_T = 0.02         # 桁の上面の板（雪の絵で雪にする面）の厚み
MONO_POST = 0.7           # 高架の柱の太さ（正方形の 1 辺）。隣のタイルの柱と背中合わせになる
MONO_ARM_D = 0.6          # 腕（柱の頭から桁の下へ渡す梁）の深さ
MONO_ARM_EMBED = 0.1      # 腕の上面を桁の下面より上へ食い込ませる高さ（桁に隠れる）

# ---------------------------------------------------------------- 色（打ち放しのコンクリートのまだら）
MONO_BEAM_LO, MONO_BEAM_HI = (0.56, 0.56, 0.54), (0.64, 0.64, 0.62)
MONO_PIER_LO, MONO_PIER_HI = (0.50, 0.50, 0.48), (0.58, 0.58, 0.56)
MONO_GRAIN = 4.0
MONO_SNOW_RGB = (0.92, 0.94, 0.97)

_M_MONO_BEAM = track_noise("mono_beam", MONO_BEAM_LO, MONO_BEAM_HI, MONO_GRAIN)
_M_MONO_TOP = track_noise("mono_top", MONO_BEAM_LO, MONO_BEAM_HI, MONO_GRAIN)
_M_MONO_PIER = track_noise("mono_pier", MONO_PIER_LO, MONO_PIER_HI, MONO_GRAIN)

# 手前（画面の下）の向き。南（−y）と東（+x）が手前
_FRONT = Vector((1, -1))


def _beam_shape(z0):
    def shape(path, k):
        u = MONO_BEAM_W / 2 * k
        return sweep(path, [(-u, z0), (u, z0), (u, MONO_BEAM_TOP), (-u, MONO_BEAM_TOP)])
    return shape


def _top_shape(path, k):
    u = MONO_BEAM_W / 2 * k
    return sweep(path, [(-u, MONO_BEAM_TOP), (u, MONO_BEAM_TOP), (u, MONO_BEAM_TOP + MONO_TOP_T), (-u, MONO_BEAM_TOP + MONO_TOP_T)])


def monorail_parts(z0=0.0):
    """桁の部品。z0 は桁の下面の高さ（地上の版は 0、高架の版は MONO_BEAM_TOP − MONO_ELEV_BEAM_D）。
    どれも走行面（rail）の基準面に乗せる（分岐の絵で、分岐の経路の桁が描かれる）"""
    return (
        Part("mono_beam", "rail", "gauge", _M_MONO_BEAM, _beam_shape(z0)),
        Part("mono_top", "rail", "gauge", _M_MONO_TOP, _top_shape),
    )


# 雪の絵（TRACK_PROFILES の "snow_skin"）: 桁の上面の板だけを雪にする
MONO_SNOW_SKIN = {"mono_top": ("mono_snow", MONO_SNOW_RGB, 0.9)}


def _near(path, q, tol=0.3):
    """点 q が折れ線 path の近く（tol 以内）にあるか"""
    for a, b in zip(path, path[1:]):
        d = b - a
        t = max(0.0, min(1.0, (q - a).dot(d) / d.length_squared)) if d.length_squared else 0.0
        if (a + d * t - q).length <= tol:
            return True
    return False


def _supports(paths):
    """腕を渡す所: (桁の上の点, 桁に沿う外向きの向き) の一覧。桁がタイルを出入りする辺の中点と、タイルの中で終わる桁の端"""
    half = TILE / 2
    out = []
    for o in (Vector((0, 1)), Vector((0, -1)), Vector((1, 0)), Vector((-1, 0))):
        if any(_near(p, o * half) for p in paths):
            out.append((o * half, o))
    inside = lambda q: max(abs(q.x), abs(q.y)) < half - 0.1
    for p in paths:
        for end, nxt in ((p[0], p[1]), (p[-1], p[-2])):
            if inside(end):
                out.append((Vector((end.x, end.y)), Vector((end.x - nxt.x, end.y - nxt.y)).normalized()))
    return out


def _pier_geometry(paths, side, z_beam):
    """柱と腕の形。side は front・back・center（柱を立てる側）、z_beam は桁の下面の高さ"""
    half = TILE / 2
    arm_top = z_beam + MONO_ARM_EMBED
    arm_bot = arm_top - MONO_ARM_D
    post_bot = -ELEV_STEPS * H - PIER_FOOT
    p = MONO_POST
    posts, arms = {}, []
    for q, o in _supports(paths):
        q, o = Vector((q.x, q.y)), Vector((o.x, o.y))
        t = Vector((-o.y, o.x))
        # 辺の上の腕は、タイルの内側へ柱の太さの半分だけ下げた線の上（隣のタイルの腕と背中合わせ）。タイルの中の端はその位置
        on_edge = abs(abs(q.dot(o)) - half) < 0.01
        line = q - o * (p / 2) if on_edge else q
        for s in (1, -1):
            front = (t * s).dot(_FRONT) > 0
            if side != "center" and front != (side == "front"):
                continue
            # 柱は、腕の線の上で、タイルの横の辺に面を合わせる（t の向きの位置が s × (half − p/2)）
            c = line + t * (s * (half - p / 2) - line.dot(t))
            key = (round(c.x, 3), round(c.y, 3))
            posts[key] = c
            mid = (c + line) / 2
            length = (c - line).length + p / 2
            rot = math.atan2(t.y, t.x)
            arms.append(box(mid.x, mid.y, (arm_top + arm_bot) / 2, length, p, arm_top - arm_bot, rot=rot))
    geo = [box(c.x, c.y, (arm_top + post_bot) / 2, p, p, arm_top - post_bot) for c in posts.values()]
    return merge(geo + arms) if geo or arms else None


def monorail_pier_fills(side):
    """高架の版の柱と腕（TRACK_PROFILES の "cell_fills"）。セルの全部の経路から、桁が出入りする辺と端を求めて作る"""
    z_beam = MONO_BEAM_TOP - MONO_ELEV_BEAM_D

    def make(paths):
        geo = _pier_geometry(paths, side, z_beam)
        return None if geo is None else (lambda path, k: geo)
    return ((Part("mono_pier", "rail", "gauge", _M_MONO_PIER, None), make),)
