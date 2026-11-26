"""リニア（maglev）の部品（超電導の床・ガイド、常電導の T 字の桁、チューブ式の床とチューブの骨組み。#371）。
TRACK_PROFILES の "track_parts"・"cell_fills"・"snow_skin" に渡す（共通の描画の道具 sheetlib の一部。tools/README.md）。

手本は iss のリニア（refs の iss/src/way/maglev/・way-object/maglev/linear_guide.dat と、配布物の合成済みの絵）と、チューブ式は
marine_express（refs の marine_express_1.1。ユーザーのアドオン、WTFPL）。超電導の寸法は配布物の東西のセルを縦に走査して測り、
常電導の桁とチューブの太さは、AMI のシートを手本と同じ倍率で並べて合わせた（タイルの 1 辺は 10 単位）:
    - 超電導（guideway）: 床と防音壁（壁の高さ 1.9）は way の絵。U 字の側壁（厚さ 0.3、高さ 0.4、壁の中心の間 1.56）は
      ガイドの way-object（電化を兼ねる）。AMI では床を線路の基盤の版の上に置き、防音壁は線路の側壁の位置で高さだけ変える（render.py）
    - 常電導（beam）: T 字の桁（上の幅 1.2、高さ 0.4）。高架の版は桁を下へ深くし、柱と腕は跨座式モノレールと同じ並び（monorail_parts）
    - チューブ式（tube）: 床と中央の溝の way（版と側壁は線路の基盤の版と同じ）と、重ねるチューブの way-object（径 6.4）。
      手本のチューブは透ける輪だが、AMI のシートは 2 値（cells.make_sheet の alpha=False）なので、輪と縦の線の骨組みで描く
"""
import math

from mathutils import Vector

from .core import SCALE, Part, along, merge, sweep, tiled_concrete_material
from .monorail_parts import MONO_SNOW_RGB, _near_sign, mono_concrete
from .track_parts import to_edge_shape

# ---------------------------------------------------------------- 超電導の床（way の track_parts）
MAG_FLOOR_U = 2.15        # 床の半幅（線路の側壁の内側 WALL_U まで）
MAG_FLOOR_T = 0.06        # 床の板の厚み（路盤の面から）
MAG_TROUGH_U = 0.63       # 車両の走る溝の半幅（ガイドの側壁の内側まで）
MAG_WALL_H = 1.9          # 防音壁の高さ（iss の壁の高さ。線路の側壁 WALL_H 1.2 より高い）
MAG_WALL_RISE = 18 * SCALE  # 防音壁の持ち分を上へ広げる行数（壁の高さ 約 15px と余り。線路の WALL_RISE は 11）

MAG_FLOOR_RGB = (0.62, 0.62, 0.60)
MAG_TROUGH_RGB = (0.46, 0.46, 0.45)
_M_MAG_FLOOR = lambda: tiled_concrete_material("mag_floor", MAG_FLOOR_RGB, 0.08, 3.0, rough=0.9)  # noqa: E731
_M_MAG_TROUGH = lambda: tiled_concrete_material("mag_trough", MAG_TROUGH_RGB, 0.08, 3.0, rough=0.9)  # noqa: E731


def _mag_slab(u, z0, z1):
    def shape(path, k):
        return sweep(path, [(-u * k, z0), (u * k, z0), (u * k, z1), (-u * k, z1)])
    return shape


def guideway_parts():
    """超電導の way の床: 防音壁の間の板と、車両の走る溝の暗い帯。路盤の面（bed）の基準面に乗せる（基盤・防音壁と同じ）"""
    return (
        Part("mag_floor", "bed", "bed", _M_MAG_FLOOR, to_edge_shape(_mag_slab(MAG_FLOOR_U, 0.0, MAG_FLOOR_T))),
        Part("mag_trough", "bed", "bed", _M_MAG_TROUGH, to_edge_shape(_mag_slab(MAG_TROUGH_U, MAG_FLOOR_T, MAG_FLOOR_T + 0.004))),
    )


# 雪の絵: 床の板と溝を雪にする（防音壁は線路の壁と同じく夏と同じ）
MAG_SNOW = ("mag_snow", MONO_SNOW_RGB, 0.9)
GUIDEWAY_SNOW_SKIN = {"mag_floor": MAG_SNOW, "mag_trough": ("mag_snow_trough", (0.80, 0.84, 0.90), 0.9)}

# ---------------------------------------------------------------- 超電導のガイド（way-object の track_parts）
GUIDE_IN, GUIDE_OUT = 0.63, 0.93   # 側壁の内側・外側の面（経路から。壁の厚さ 0.3、中心の間 1.56）
GUIDE_H = 0.4                      # 側壁の高さ（床の上面から）
COIL_T = 0.025                     # 側壁の内側の面のコイルの板の厚み
COIL_Z = (0.08, 0.34)              # コイルの板の高さの範囲（床の上面から）
GUIDE_RISE = 11 * SCALE            # 持ち分を上へ広げる行数（側壁の高さ 約 4px と余り。線路の WALL_RISE と同じ）

_M_GUIDE = mono_concrete("mag_guide", (0.66, 0.66, 0.64))
_M_COIL = ("mag_coil", (0.12, 0.13, 0.16), 0.5, 0.4)   # 浮上・案内のコイル（暗い紺の灰）


def _guide_side(near, u0, u1, z0, z1):
    """経路の手前（near）か奥の側の、u0〜u1・z0〜z1 の帯。手前と奥の決まらない向き（経路が画面の縦）は両側とも奥"""
    def shape(path, k):
        s = _near_sign(path)
        sides = [s if near else -s] if s else ([] if near else [1, -1])
        geo = [sweep(path, [(g * u0 * k, z0), (g * u1 * k, z0), (g * u1 * k, z1), (g * u0 * k, z1)][::g]) for g in sides]
        return merge(geo) if geo else None
    return shape


def guide_parts():
    """ガイドの way-object の部品: U 字の側壁と内側のコイル。手前の側は手前の絵（frontimage）、奥の側は奥の絵。
    way-object の絵は way の高さを基準に描かれるので、床の上面（MAG_FLOOR_T）から立てる"""
    z0, z1 = MAG_FLOOR_T, MAG_FLOOR_T + GUIDE_H
    c0, c1 = MAG_FLOOR_T + COIL_Z[0], MAG_FLOOR_T + COIL_Z[1]
    out = []
    for near in (False, True):
        tag = "front" if near else "back"
        out.append(Part(f"mag_guide_{tag}", "bed", "bed", _M_GUIDE, _guide_side(near, GUIDE_IN, GUIDE_OUT, z0, z1), tall=True, front=near))
        out.append(Part(f"mag_coil_{tag}", "bed", "bed", _M_COIL, _guide_side(near, GUIDE_IN - COIL_T, GUIDE_IN, c0, c1),
                        tall=True, front=near, thin=True))
    return tuple(out)


# ---------------------------------------------------------------- 常電導（T 字の桁）
BEAM_TOP = 0.4            # 桁の上面の高さ（way の高さから）
BEAM_FLANGE_U = 0.6       # 上の板の半幅（上の幅 1.2。iss の B1 と同じ倍率で並べて合わせた）
BEAM_FLANGE_T = 0.18      # 上の板の厚み
BEAM_WEB_U = 0.3          # 腹の半幅
BEAM_ELEV_D = 1.6         # 高架の桁の深さ（上面から。跨座式の MONO_ELEV_BEAM_D と同じ）
TOP_T = 0.02              # 上面の板（雪の絵で雪にする面）の厚み
MAG_BEAM_RGB = (0.62, 0.62, 0.60)

_M_MAG_BEAM = mono_concrete("mag_beam", MAG_BEAM_RGB)
_M_MAG_TOP = mono_concrete("mag_beam_top", MAG_BEAM_RGB)


def beam_parts(z0=0.0):
    """常電導の T 字の桁。z0 は腹の下面の高さ（地上は 0、高架は BEAM_TOP − BEAM_ELEV_D）。走行面（rail）の基準面に乗せる"""
    fz = BEAM_TOP - BEAM_FLANGE_T
    return (
        Part("mag_beam_web", "rail", "gauge", _M_MAG_BEAM, _mag_slab(BEAM_WEB_U, z0, fz)),
        Part("mag_beam", "rail", "gauge", _M_MAG_BEAM, _mag_slab(BEAM_FLANGE_U, fz, BEAM_TOP)),
        Part("mag_beam_top", "rail", "gauge", _M_MAG_TOP, _mag_slab(BEAM_FLANGE_U, BEAM_TOP, BEAM_TOP + TOP_T)),
    )


BEAM_SNOW_SKIN = {"mag_beam_top": MAG_SNOW}

# ---------------------------------------------------------------- チューブ式（床と溝の軌道、チューブの way-object）
# 手本は marine_express（ユーザーのアドオン。WTFPL）: 軌道は広い床と中央の溝 1 本で、版（single・back・center・front）は線路と同じ側壁。
# チューブは軌道に重ねる way-object（輪の骨組み）。高架の躯体と側壁は超電導・線路の基盤の版と同じ（render.py）
TUBE_GROOVE_U = 0.22      # 中央の溝の半幅
TUBE_R = 3.2              # チューブの半径（径 6.4。側壁（線路の側壁と同じ位置・高さ 1.2）を包む）
TUBE_ZC = 1.2             # チューブの中心の高さ（床の上面から。輪は床の上面より上だけを描く）
TUBE_RING_T = 0.22        # 輪の太さ（半径の向き）
TUBE_RING_W = 0.24       # 輪の太さ（経路に沿う向き）
TUBE_PITCH = 2.5          # 輪の間隔（タイルの辺から TUBE_PITCH/2 ずらし、タイルの辺に乗せない）
TUBE_STRINGER = 35.0      # 横の縦の線の角度（水平から。度）
TUBE_SEG = 8              # 輪の 1 側（床の上面の端から頂点まで）の分け数
TUBE_RISE = 48 * SCALE    # 持ち分を上へ広げる行数（チューブの頂点 約 35px と余り）

_M_TUBE_GROOVE = _M_MAG_TROUGH
_M_TUBE_FRAME = ("mag_tube_frame", (0.78, 0.80, 0.82), 0.4, 0.6)   # チューブの骨組み（明るい鋼）


def tube_track_parts():
    """チューブ式の way の床: 側壁の間の板と、中央の溝の暗い帯。路盤の面（bed）の基準面に乗せる（超電導の床と同じ）"""
    return (
        Part("mag_floor", "bed", "bed", _M_MAG_FLOOR, to_edge_shape(_mag_slab(MAG_FLOOR_U, 0.0, MAG_FLOOR_T))),
        Part("mag_tgroove", "bed", "bed", _M_TUBE_GROOVE, to_edge_shape(_mag_slab(TUBE_GROOVE_U, MAG_FLOOR_T, MAG_FLOOR_T + 0.004))),
    )


TUBE_SNOW_SKIN = {"mag_floor": MAG_SNOW, "mag_tgroove": ("mag_snow_groove", (0.80, 0.84, 0.90), 0.9)}


def _ring_angles():
    """輪の 1 側の角（水平から。下の端は床の上面の高さ、上の端は頂点 90°）"""
    a0 = math.degrees(math.asin(max(-1.0, -TUBE_ZC / TUBE_R)))
    return [a0 + (90.0 - a0) * i / TUBE_SEG for i in range(TUBE_SEG + 1)]


def _ring_half(p, ang, g, k):
    """経路の点 p（向き ang）の、側 g（1 は sweep の u の正）の半分の輪。断面は TUBE_RING_W × TUBE_RING_T の四角を、円に沿って押し出す"""
    d = Vector((math.cos(ang), math.sin(ang), 0.0))
    n = Vector((d.y, -d.x, 0.0))
    c = Vector((p.x, p.y, MAG_FLOOR_T + TUBE_ZC))
    rings = []
    for a in _ring_angles():
        r = math.radians(a)
        radial = n * (g * math.cos(r) * k) + Vector((0, 0, math.sin(r)))
        radial.normalize()
        pos = c + n * (g * TUBE_R * math.cos(r) * k) + Vector((0, 0, TUBE_R * math.sin(r)))
        w = d * (TUBE_RING_W / 2)
        t = radial * (TUBE_RING_T / 2)
        rings.append([pos - w - t, pos + w - t, pos + w + t, pos - w + t])
    verts = [v for ring in rings for v in ring]
    faces = []
    for i in range(len(rings) - 1):
        for j in range(4):
            j2 = (j + 1) % 4
            faces.append((i * 4 + j, i * 4 + j2, (i + 1) * 4 + j2, (i + 1) * 4 + j))
    faces.append((3, 2, 1, 0))
    last = (len(rings) - 1) * 4
    faces.append((last, last + 1, last + 2, last + 3))
    # 面を外向きにする: 始めの蓋 (3, 2, 1, 0) の向きは −(d × 半径の向き)。それが進む向き（輪に沿う接線）の逆でなければ、全部の面を裏返す
    # （側 g が負だと鏡に映した形になり、裏返る。裏返った形はタイルで切るときに消える）
    tangent = sum(rings[1], Vector()) / 4 - sum(rings[0], Vector()) / 4
    rad0 = (rings[0][3] - rings[0][0]).normalized()
    if d.cross(rad0).dot(tangent) < 0:
        faces = [tuple(reversed(f)) for f in faces]
    return verts, faces


def _sides(path, near):
    """経路の手前（near）か奥の側（sweep の u の符号の一覧）。手前と奥の決まらない向き（経路が画面の縦）は両側とも奥"""
    s = _near_sign(path)
    return [s if near else -s] if s else ([] if near else [1, -1])


def _tube_rings(near):
    """チューブの輪の、手前か奥の側の半分。輪どうしは重ならない（部品の形が自分と交わると、タイルで切るときに消える）"""
    def shape(path, k):
        geo = [_ring_half(p, ang, g, k) for g in _sides(path, near) for p, ang in along(path, TUBE_PITCH, TUBE_PITCH / 2)]
        return merge(geo) if geo else None
    return shape


def _tube_lines(near):
    """チューブの縦の線: 横の線（手前か奥の側）と、頂点の線（奥の側が持つ）。輪とは別の部品にする（交わると切るときに消える）"""
    h = TUBE_RING_T / 2
    r = math.radians(TUBE_STRINGER)

    def shape(path, k):
        geo = []
        for g in _sides(path, near):
            u, z = g * TUBE_R * math.cos(r) * k, MAG_FLOOR_T + TUBE_ZC + TUBE_R * math.sin(r)
            geo.append(sweep(path, [(u - h, z - h), (u + h, z - h), (u + h, z + h), (u - h, z + h)]))
        if not near:
            zt = MAG_FLOOR_T + TUBE_ZC + TUBE_R
            geo.append(sweep(path, [(-h, zt - h), (h, zt - h), (h, zt + h), (-h, zt + h)]))
        return merge(geo) if geo else None
    return shape


def tube_frame_parts():
    """チューブの way-object の部品: 輪と縦の線の骨組み。手前の側の半分は手前の絵（frontimage）、奥の側は奥の絵。床の上面から立てる（ガイドと同じ）"""
    return tuple(Part(f"mag_tube_{kind}_{'front' if near else 'back'}", "bed", "bed", _M_TUBE_FRAME, make(near),
                      tall=True, front=near, thin=True)
                 for near in (False, True) for kind, make in (("ring", _tube_rings), ("line", _tube_lines)))
