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

from .core import H, SCALE, TILE, Part, box, merge, sweep, tiled_concrete_material
from .wall_parts import ELEV_STEPS, PIER_FOOT

# ---------------------------------------------------------------- 寸法（部品の 1 単位 ≈ 9px。高さ 1 単位 ≈ 7.8px）
MONO_BEAM_W = 0.85        # 桁の幅（iss の地上の桁の画面の帯から測った値）
MONO_BEAM_TOP = 0.7       # 桁の上面の高さ（way の高さから。iss の地上の桁は地面からこの高さまで）
MONO_ELEV_BEAM_D = 1.6    # 高架の桁の深さ（上面から。下面は way の高さより MONO_BEAM_TOP − これ だけ下）
MONO_TOP_T = 0.02         # 桁の上面の板（雪の絵で雪にする面）の厚み
MONO_POST = 0.7           # 高架の柱の太さ（正方形の 1 辺）。隣のタイルの柱と背中合わせになる
MONO_ARM_D = 0.6          # 腕（柱の頭から桁の下へ渡す梁）の深さ
MONO_ARM_EMBED = 0.1      # 腕の上面を桁の下面より上へ食い込ませる高さ（桁に隠れる）
# 跨座式の桁の持ち分を上へ広げる行数（桁の上面は地面から 0.72 = 画面で約 6px。余りを含む。#375）
MONO_RISE = 24 * SCALE

# ---------------------------------------------------------------- 色（打ち放しのコンクリートのまだらと汚し）
# 第 1 弾の高架の躯体・橋脚・壁（中性の灰 0.56〜0.60）と見分けるため、汚し（#154）を掛ける。ユーザーが案 A＋C を選んだ（2026-11-22。
# 見比べた案の絵は addons/ami/rounds/ami_weather_calib.pak。案を描いた道具 weather_calib.py は #351 で消した。a15b576 にある）:
#   A 色味: 桁と柱を少し暖かい灰（MONO_TINT）にし、柱を桁より 8% 暗くする
#   C 地際の汚れ: 柱・腕を、柱の下端（地面より PIER_FOOT 下）から MONO_GRIME_SPAN の高さまで、下ほど暗くする（下端で 1 − MONO_GRIME 倍）
# まだら（±MONO_AMP、粒 MONO_GRAIN）は sheetlib の tiled_concrete_material（タイルの 1 辺を周期にした模様）で作る
MONO_BEAM_RGB = (0.60, 0.60, 0.58)
MONO_PIER_RGB = (0.497, 0.497, 0.478)   # 前の柱（0.54）の 0.92 倍
MONO_TINT = (1.04, 1.00, 0.92)
MONO_AMP = 0.067
MONO_GRAIN = 4.0
MONO_GRIME = 0.45
MONO_GRIME_SPAN = 3.5   # 部品の座標（高さ 1 単位 ≈ 7.8px）
MONO_SNOW_RGB = (0.92, 0.94, 0.97)


def mono_concrete(name, rgb, ground=None):
    """モノレールのコンクリートの材質を返す関数。ground（柱の下端の高さ）を渡すと地際の汚れを掛ける"""
    grime = {} if ground is None else dict(grime=MONO_GRIME, grime_z=(ground, ground + MONO_GRIME_SPAN))
    return lambda: tiled_concrete_material(name, rgb, MONO_AMP, MONO_GRAIN, rough=0.9, tint=MONO_TINT, **grime)


_M_MONO_BEAM = mono_concrete("mono_beam", MONO_BEAM_RGB)
_M_MONO_TOP = mono_concrete("mono_top", MONO_BEAM_RGB)

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
    どれも走行面（rail）の基準面に乗せる（分岐の絵で、分岐の経路の桁が描かれる）。
    高さのある部品（tall）にして、タイルの辺で切り、各タイルが自分の桁を地面より上まで描く（#375）。地面より高い桁を、奥のタイルが
    手前の隣の分まで延ばして描くと、隣との向きが違う並び（直角の曲がりの角、曲がりが続く所、T字・十字の隣）で、桁の端が出たり段が
    できたりする。横幅の扱いは "bed"（斜めは 1/√2）: 斜めと直線がタイルの辺で同じ幅の断面になる。thin は、半分だけ覆われた縁の画素を残す"""
    return (
        Part("mono_beam", "rail", "bed", _M_MONO_BEAM, _beam_shape(z0), tall=True, thin=True),
        Part("mono_top", "rail", "bed", _M_MONO_TOP, _top_shape, tall=True, thin=True),
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


def monorail_pier_fills(side, z_beam=None):
    """高架の版の柱と腕（TRACK_PROFILES の "cell_fills"）。セルの全部の経路から、桁が出入りする辺と端を求めて作る。
    z_beam は腕を渡す桁の下面の高さ（無ければ跨座式の高架の桁 MONO_BEAM_TOP − MONO_ELEV_BEAM_D。リニアの桁は maglev_parts が渡す。#371）"""
    if z_beam is None:
        z_beam = MONO_BEAM_TOP - MONO_ELEV_BEAM_D

    def make(paths):
        geo = _pier_geometry(paths, side, z_beam)
        return None if geo is None else (lambda path, k: geo)
    pier = mono_concrete("mono_pier", MONO_PIER_RGB, ground=-ELEV_STEPS * H - PIER_FOOT)   # 柱の下端（_pier_geometry の post_bot）
    return ((Part("mono_pier", "rail", "gauge", pier, None), make),)


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
SUSP_RISE = 50 * SCALE            # 持ち分を上へ広げる行数（柱の頭 約 39px と余り）

_M_SUSP_BEAM = mono_concrete("susp_beam", MONO_BEAM_RGB)
_M_SUSP_TOP = mono_concrete("susp_top", MONO_BEAM_RGB)


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
    # 地上と高架で柱の下端が違うので、材質を分ける（地際の汚れの高さ）
    pier = mono_concrete(f"susp_pier{'_elev' if elevated else ''}", MONO_PIER_RGB, ground=post_bot)

    def maker(near):
        def make(paths):
            geo = _susp_geometry(paths, side, post_bot, near)
            return None if geo is None else (lambda path, k: geo)
        return make
    return tuple((Part(f"susp_pier_{'front' if near else 'back'}", "rail", "gauge", pier, None, tall=True, front=near), maker(near))
                 for near in (False, True))


# ---------------------------------------------------------------- モノレールの電化の way-object（給電レールと碍子。#116）
# 電車のモノレールの車両（ユーザーが渡した Higashiyama_1A など）は、電化した way でしか走らない。電化は own_waytype=electrified_track の
# way-object で付ける（本体の weg_t の IS_ELECTRIFIED）。物は方式ごとに 2 つ（2026-11-22、進捗管理の決定。#116）:
#   ami_monorail_power（跨座式用）: 桁の両の側面に給電レールと碍子
#   ami_monorail_suspended_power（懸垂式用）: 桁の下面の両脇に給電レールと、柱の所ごとに碍子
# way-object の絵は way の高さを基準に描かれ、桁の高さは方式で違うので、見た目が合うのはそれぞれの方式の way の上だけ（README）。
# 手前の側のレール・碍子は手前の絵（frontimage。車両の後に描く）、奥の側は奥の絵。桁は holdout（透明に描いて、後ろを隠す）で置き、
# 桁の向こうの奥のレールを隠す（way の絵の桁の上に、奥のレールが描かれないように）。画面で手前と奥の決まらない向き（経路が _FRONT に沿う）の
# レールは、両側とも奥の絵に描く
POWER_RAIL_W = 0.1        # 給電レールの横幅（画面で約 1px）
POWER_RAIL_H = 0.16       # 給電レールの高さ
POWER_INS = (0.16, 0.18, 0.26)  # 碍子（経路に沿う長さ・横幅・高さ）
POWER_INS_IN = 0.35       # 碍子をタイルの辺の中点からタイルの内へ寄せる量（辺ちょうどだと持ち分で半分に切られる）
POWER_STRADDLE_Z = 0.28   # 跨座式: 給電レールの下面の高さ（桁の側面の中ほど。桁の上面は MONO_BEAM_TOP）
POWER_SUSP_DROP = 0.04    # 懸垂式: 給電レールを桁の下面より下げる量（下面の縁にぶら下げる）
POWER_RISE = SUSP_RISE    # 持ち分を上へ広げる行数（懸垂式の桁の高さまで）

_M_POWER_RAIL = ("power_rail", (0.16, 0.16, 0.17), 0.5, 0.6)       # 鋼の給電レール（暗い灰色）
_M_POWER_INS = ("power_insulator", (0.86, 0.84, 0.76), 0.4, 0.0)   # 磁器の碍子（白に近い象牙色）


def _holdout():
    import bpy
    m = bpy.data.materials.get("power_beam_holdout")
    if m is None:
        m = bpy.data.materials.new("power_beam_holdout")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        ho = nt.nodes.new("ShaderNodeHoldout")
        nt.links.new(ho.outputs[0], out.inputs["Surface"])
    return m


def _near_sign(path):
    """経路の右（sweep の u の正）が手前なら 1、左が手前なら -1、決まらなければ 0"""
    d = Vector((path[-1].x - path[0].x, path[-1].y - path[0].y))
    if d.length < 1e-6:
        return 0
    d.normalize()
    dot = Vector((d.y, -d.x)).dot(_FRONT)
    return 0 if abs(dot) < 1e-3 else (1 if dot > 0 else -1)


def _power_spec(suspended):
    """方式ごとの (桁の半幅, 桁の下面, 桁の上面, レールの横の範囲 (内, 外), レールの高さの範囲 (下, 上))"""
    if suspended:
        u = SUSP_BEAM_W / 2
        z1 = SUSP_BEAM_BOT - POWER_SUSP_DROP
        return u, SUSP_BEAM_BOT, SUSP_BEAM_TOP + MONO_TOP_T, (u - POWER_RAIL_W, u), (z1 - POWER_RAIL_H, z1 + POWER_SUSP_DROP)
    u = MONO_BEAM_W / 2
    return u, MONO_BEAM_TOP - MONO_ELEV_BEAM_D, MONO_BEAM_TOP + MONO_TOP_T, (u, u + POWER_RAIL_W), (POWER_STRADDLE_Z, POWER_STRADDLE_Z + POWER_RAIL_H)


def power_parts(suspended):
    """電化の way-object の部品（TRACK_PROFILES の "track_parts"）: 桁の holdout と、手前・奥の給電レール"""
    _, zb, zt, (ui, uo), (z0, z1) = _power_spec(suspended)

    def beam(path, k):
        u = _power_spec(suspended)[0] * k
        return sweep(path, [(-u, zb), (u, zb), (u, zt), (-u, zt)])

    def rail(near):
        def shape(path, k):
            s = _near_sign(path)
            sides = [s if near else -s] if s else ([] if near else [1, -1])
            geo = [sweep(path, [(g * ui * k, z0), (g * uo * k, z0), (g * uo * k, z1), (g * ui * k, z1)][::g])
                   for g in sides]
            return merge(geo) if geo else None
        return shape
    w = "gauge" if suspended else "bed"   # 跨座式は桁の斜めの幅に合わせる（monorail_parts）。懸垂式は変えない（#375）
    return (
        Part("power_beam_hold", "rail", w, _holdout, beam, tall=True),
        Part("power_rail_back", "rail", w, _M_POWER_RAIL, rail(False), tall=True, thin=True),
        Part("power_rail_front", "rail", w, _M_POWER_RAIL, rail(True), tall=True, thin=True, front=True),
    )


def power_insulator_fills(suspended):
    """碍子（TRACK_PROFILES の "cell_fills"）。桁がタイルを出入りする辺の中点（と桁の端）から少し内の、桁の両脇に 1 つずつ。
    手前の側は手前の絵、奥の側は奥の絵（手前と奥の決まらない向きは両方とも奥）"""
    u, zb, _, (ui, uo), (z0, z1) = _power_spec(suspended)
    L, W, Hh = POWER_INS
    if suspended:  # 桁の下面から下へぶら下げる
        zc, off = zb - Hh / 2, u - W / 2
    else:  # 桁の側面から外へ出す（レールを支える）
        zc, off = (z0 + z1) / 2, u + W / 2

    def maker(near):
        def make(paths):
            geo = []
            for q, o in _supports(paths):
                q, o = Vector((q.x, q.y)), Vector((o.x, o.y))
                t = Vector((-o.y, o.x))
                c0 = q - o * POWER_INS_IN
                for s in (1, -1):
                    dot = (t * s).dot(_FRONT)
                    if (dot > 1e-3) != near:
                        continue
                    c = c0 + t * (s * off)
                    geo.append(box(c.x, c.y, zc, L, W, Hh, rot=math.atan2(o.y, o.x)))
            if not geo:
                return None
            g = merge(geo)
            return lambda path, k: g
        return make
    return tuple((Part(f"power_ins_{'front' if near else 'back'}", "rail", "gauge", _M_POWER_INS, None, tall=True, front=near), maker(near))
                 for near in (False, True))
