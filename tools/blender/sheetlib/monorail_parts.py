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


# ================================================================ 懸垂式モノレール（#116）
# 手本は iss の懸垂式（refs の iss/src/way/monorail/suspended.dat と、配布物の suspended_g_<版>_rear/surface.png・suspended_e_<版>_*.png）:
#     - 地上の版（system_type=0）・高架の版（system_type=1）とも、way の絵に柱を持つ（別の柱の物は無い）。版は柱の側で front・center・back
#     - 桁は空中にあり、吊られた車両が桁の下を走る。iss の地上の桁は、下面が地面から約 25px、上面が約 35px、柱の頭（梁の上）が約 37〜40px
#     - 柱は、桁がタイルを出入りする辺ごとに、その辺の角に立つ。柱の頭から桁の上へ梁を渡す（center は両側の柱で門型）
#     - 高架の版は、同じ形の柱を下の地面まで延ばす
# AMI では、跨座式の高架の柱（_supports・_pier_geometry）と同じ並びで、梁を桁の上に渡す。柱はタイルの内側に面を合わせて立てる（跨座式と同じ）。
# 手前の側（南・東）の柱と梁は手前の絵（frontimage。車両の後に描く）、桁と奥の側の柱・梁は奥の絵に描く（iss の rear・surface と同じ分け方）。
# 桁の高さ: 最初は iss の地上の桁（下面 約 25px・上面 約 35px）に合わせたが、ユーザーが渡した懸垂式の車両（Higashiyama_1A）を
# 走らせると、屋根の吊り具の先と桁の下面の間が約 3px 空いた（pak128 の Schwebebahn は桁の下面が車両の屋根に接する）。
# 桁を 0.4（約 3px）下げて、吊り具が桁に届くようにした（2026-11-22。#116 の PR の画面）
SUSP_BEAM_BOT = 2.8       # 桁の下面の高さ（way の高さから。約 22px）
SUSP_BEAM_TOP = 4.1       # 桁の上面の高さ（約 32px）
SUSP_BEAM_W = MONO_BEAM_W  # 桁の幅（跨座式と同じ）
SUSP_ARM_D = 0.6          # 梁の深さ（桁の上に載る。柱の頭は桁の上面 + これ − 食い込み。約 36px）
SUSP_RISE = 50            # 持ち分を上へ広げる行数（柱の頭 約 39px と余り）

_M_SUSP_BEAM = track_noise("susp_beam", MONO_BEAM_LO, MONO_BEAM_HI, MONO_GRAIN)
_M_SUSP_TOP = track_noise("susp_top", MONO_BEAM_LO, MONO_BEAM_HI, MONO_GRAIN)
_M_SUSP_PIER = track_noise("susp_pier", MONO_PIER_LO, MONO_PIER_HI, MONO_GRAIN)


def _susp_beam_shape(path, k):
    u = SUSP_BEAM_W / 2 * k
    return sweep(path, [(-u, SUSP_BEAM_BOT), (u, SUSP_BEAM_BOT), (u, SUSP_BEAM_TOP), (-u, SUSP_BEAM_TOP)])


def _susp_top_shape(path, k):
    u = SUSP_BEAM_W / 2 * k
    return sweep(path, [(-u, SUSP_BEAM_TOP), (u, SUSP_BEAM_TOP), (u, SUSP_BEAM_TOP + MONO_TOP_T), (-u, SUSP_BEAM_TOP + MONO_TOP_T)])


def suspended_parts():
    """懸垂式の桁の部品（高さのある部品。奥の絵に描く）。走行面（rail）の基準面に乗せる（分岐の絵で、分岐の経路の桁が描かれる）"""
    return (
        Part("susp_beam", "rail", "gauge", _M_SUSP_BEAM, _susp_beam_shape, tall=True),
        Part("susp_top", "rail", "gauge", _M_SUSP_TOP, _susp_top_shape, tall=True),
    )


# 雪の絵: 桁の上面の板だけを雪にする（柱・梁は夏と同じ）
SUSP_SNOW_SKIN = {"susp_top": ("susp_snow", MONO_SNOW_RGB, 0.9)}


def _susp_geometry(paths, side, post_bot, near):
    """柱と梁の形のうち、手前の側（near が真）か奥の側（偽）の分。side は front・back・center（柱を立てる側）"""
    half = TILE / 2
    arm_bot = SUSP_BEAM_TOP - MONO_ARM_EMBED
    arm_top = arm_bot + SUSP_ARM_D
    p = MONO_POST
    posts, arms = {}, []
    for q, o in _supports(paths):
        q, o = Vector((q.x, q.y)), Vector((o.x, o.y))
        t = Vector((-o.y, o.x))
        on_edge = abs(abs(q.dot(o)) - half) < 0.01
        line = q - o * (p / 2) if on_edge else q
        for s in (1, -1):
            front = (t * s).dot(_FRONT) > 0
            if side != "center" and front != (side == "front"):
                continue
            if front != near:
                continue
            c = line + t * (s * (half - p / 2) - line.dot(t))
            posts[(round(c.x, 3), round(c.y, 3))] = c
            mid = (c + line) / 2
            length = (c - line).length + p / 2
            arms.append(box(mid.x, mid.y, (arm_top + arm_bot) / 2, length, p, arm_top - arm_bot, rot=math.atan2(t.y, t.x)))
    geo = [box(c.x, c.y, (arm_top + post_bot) / 2, p, p, arm_top - post_bot) for c in posts.values()]
    return merge(geo + arms) if geo or arms else None


def suspended_pier_fills(side, elevated=False):
    """懸垂式の柱と梁（TRACK_PROFILES の "cell_fills"）。手前の側の分は Part.front（手前の絵）、奥の側の分は奥の絵。
    elevated なら、柱を高架の下の地面まで延ばす"""
    post_bot = (-ELEV_STEPS * H if elevated else 0.0) - PIER_FOOT

    def maker(near):
        def make(paths):
            geo = _susp_geometry(paths, side, post_bot, near)
            return None if geo is None else (lambda path, k: geo)
        return make
    return tuple((Part(f"susp_pier_{'front' if near else 'back'}", "rail", "gauge", _M_SUSP_PIER, None, tall=True, front=near), maker(near))
                 for near in (False, True))
