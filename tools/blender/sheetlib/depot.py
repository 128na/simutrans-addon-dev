"""車庫（building の depot）のシート（AMI。#112）。操車場など、ほかの 1 タイルの建物も building_sheet で描く（ADR 0008）。

本体は車庫を、道が 1 方向だけに出る平らな行き止まりのタイルに建てる。layout は道の出る向きで、0 = 南・1 = 東・2 = 北・3 = 西
（simtool.cc の tool_build_depot_t::tool_depot_aux）。building の絵のキーは [layout][y][x][高さ][動き][季節]
（descriptor/writer/building_writer.cc）。手前の絵（frontimage）は乗り物の後に描かれ、高さは 1 段だけ。
建物の下の way の絵はそのまま描かれるので、床は描かない（入口から、下の way と、建物の中の壁が見える）。

形は入口を南（Blender の -y）に置いて作り、layout ごとに Z 軸のまわりに 90 度ずつ回す（南 → 東 → 北 → 西）。
回した後に画面の手前に来る 2 面（南・東）の壁と屋根を手前の絵、奥の 2 面（北・西）の壁を奥の絵にする。
入口が手前（layout 0・1）なら、乗り物は手前の壁の開口から見え、屋根と壁に隠れる。入口が奥（layout 2・3）なら、手前は閉じた壁になる。

シートの並び（make_sheet。dat を書く側の addons/ami/blender/ami_dat.py の DEPOT_* と同じ）:
    列 0〜3: layout 0〜3
    行 0: 夏の奥の絵、行 1: 夏の手前の絵、行 2・3: 雪の奥・手前（dat の季節 [1]）
    列 4: 行 0 がアイコン、行 1 がカーソル（AMI の blender/icons.py が、描いた絵から作って書く。ここでは空けておく）
絵の位置: タイルの中心をセルの (128, GROUND_CY + BUILDING_DROP) に置き、dat のオフセットは -64,-96（BUILDING_OFFSET）。
pak128 のタイルの中心は (64, 95)（線路・踏切の絵と同じ。cells の GROUND_CY = 127 にオフセット -32）なので、上へ 191px の余白がある。
"""
import math
import os

import numpy as np
from mathutils import Vector

from .cells import GROUND_CY, load_rgba8, make_sheet, render_cell, save_rgba
from .core import CELL, H, TILE, TRANSPARENT, clear_models, material, merge, mesh_object, set_anchor

BUILDING_DROP = 64                  # 建物の絵のタイルの中心を、線路の絵（GROUND_CY）より何 px 下に置くか（上に余白を作る）
BUILDING_OFFSET = (-64, -96)        # dat のオフセット。GROUND_CY + BUILDING_DROP - 96 = 95 が、線路の絵（GROUND_CY - 32）と同じ行
DEPOT_SNOW_ROW = 2                  # 雪の絵の行のずらし（夏の奥・手前が行 0・1）
DEPOT_ICON_CELL = (0, 4)            # アイコンのセル（行, 列）
DEPOT_CURSOR_CELL = (1, 4)          # カーソルのセル
DEPOT_FRONT_SIDES = ("s", "e")            # 画面の手前に来る面（南・東）。この向きの壁は手前の絵にする
_DEPOT_SIDES = ("s", "e", "n", "w")
ALPHA_KEEP = 250                    # この不透明度より薄い輪郭の画素は捨てる（render_layers の _layer と同じ。縁に暗い点が出るため）

# ---- 寸法（タイル 1 辺 = 10。高さ 1 段は H ≈ 2.04 で、画面の 16px）
# 箱積み駅舎の箱 1 段（1 タイル × 高さ 2 段 = 32px。#140）に収める（2026-11-21、ユーザーの決定）:
# 外へ出る部品も含めてタイルの中、笠木の上面は 2 段（BOX_H）ちょうど
BOX_H = 2 * H              # 箱の高さ（32px）
WALL_T = 0.3               # 壁の厚み
OUTSET = 0.1               # 壁の外の面をタイルの端から内へ下げる量（帯・柱形・枠を、この中で外へ出す）
ROOF_T = 0.2               # 屋根の床版の厚み
PARAPET_H = 0.18           # 屋上の立ち上がり（屋根の面から笠木の上面まで）
COPING_T = 0.12            # 笠木の高さ（壁の上端の明るい縁）
BAND_H = 0.35              # 笠木の下の帯（プレーヤーカラー）の高さ
BAND_OUT = 0.03            # 帯を壁の面から出す量
FRAME_W = 0.2              # 入口の枠の幅
FRAME_OUT = 0.06           # 枠を壁の面から出す量
SHUTTER_H = 0.22           # 入口の上の、巻き上げたシャッターの帯の高さ（壁の面に張る）
SHUTTER_OUT = 0.02
WINDOW_H = 0.45            # 側壁の窓の高さ
WINDOW_GAP = 0.3           # 窓の上端から帯の下端まで
WINDOW_W = 1.0             # 窓 1 つの幅
WINDOW_STEP = 1.8          # 窓の間隔
WINDOW_OUT = 0.02          # 窓を壁の面から出す量
PILASTER_W = 0.3           # 壁の柱形（縦の帯）の幅
PILASTER_OUT = 0.06        # 柱形を壁の面から出す量
PLINTH_H = 0.35            # 足元の腰壁（タイルの端まで出す）の高さ
PLINTH_DROP = 0.13         # 腰壁を地面より下へ延ばす量（約 1px。2px にすると箱の六角形の外へ出る）。下の way の絵（道路は地面より 1px 下に描く。cells の ROAD_CY）が、
#                            建物の手前の下の縁から見えないようにする（行き止まりの道路の絵はタイル全体を塗る。#112 で見つけた）
DOOR_PX = 26               # 入口の高さ（px）。pak128 の車両の車体はいちばん高いもので 25px（#112 の記録）

_M_DEPOT_WALL = ("depot_wall", (0.74, 0.74, 0.72), 0.8)       # 外壁（明るい灰のパネル）
_M_DEPOT_PILASTER = ("depot_pilaster", (0.62, 0.62, 0.60), 0.8)
_M_DEPOT_COPING = ("depot_coping", (0.82, 0.82, 0.80), 0.7)   # 笠木
_M_DEPOT_INNER = ("depot_inner", (0.30, 0.30, 0.30), 0.9)      # 建物の中の面（入口から見える。屋根の影で暗い）
_M_DEPOT_ROOF = ("depot_roof", (0.40, 0.42, 0.44), 0.7)        # 屋上（防水の面）
_M_DEPOT_ROOF_SNOW = ("depot_roof_snow", (0.90, 0.93, 0.97), 0.9)
_M_DEPOT_FRAME = ("depot_frame", (0.50, 0.50, 0.48), 0.6)      # 入口の枠
_M_DEPOT_SHUTTER = ("depot_shutter", (0.42, 0.44, 0.46), 0.5)  # 巻き上げたシャッター
_M_DEPOT_BAND = ("depot_band", (0.35, 0.35, 0.35), 0.6)        # 帯（プレーヤーカラー。灰色の明暗が色の段になる）
_M_DEPOT_WINDOW = ("depot_window", (0.30, 0.36, 0.42), 0.2)    # 窓（夜に光る暗い窓）
_M_DEPOT_PLINTH = ("depot_plinth", (0.55, 0.55, 0.53), 0.9)    # 足元の腰壁


class DepotShape:
    """車庫の寸法。建物はタイル全体（外の面はタイルの端から OUTSET 内）で、高さは BOX_H。入口は -y の面。
    door_w は入口の幅。windows は側壁に窓を並べるか"""

    def __init__(self, door_w, windows=True):
        self.half_x = self.half_y = TILE / 2 - OUTSET
        self.wall_h = BOX_H
        self.door_w = door_w
        self.door_h = DOOR_PX * H / 16
        self.windows = windows


def _depot_mat(spec, special=None):
    name, rgb, rough = spec
    return material(name, rgb, rough=rough, special=special)


def _depot_box(x0, x1, y0, y1, z0, z1):
    """軸に平行な箱（範囲で渡す）"""
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return [Vector(p) for p in v], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _depot_wall_parts(s, side, entry):
    """1 面の壁の部品（{(材質, 特殊色): [形]}）。side は入口を南に置いたときの面。entry なら入口を開ける。
    壁は南北の面が東西の端まで通り、東西の面はその間に入る（角で重ならない）"""
    hx, hy, t = s.half_x, s.half_y, WALL_T
    top = s.wall_h
    band0 = top - COPING_T - BAND_H
    parts = {}

    def add(spec, geo, special=None):
        parts.setdefault((spec, special), []).append(geo)

    if side in ("s", "n"):
        y0, y1 = (-hy, -hy + t) if side == "s" else (hy - t, hy)
        out = -1 if side == "s" else 1  # 外の向き（y）
        yo = y0 if side == "s" else y1  # 外の面

        def face_box(xa, xb, z0, z1, d):
            a, b = sorted((yo, yo + out * d))
            return _depot_box(xa, xb, a, b, z0, z1)

        if entry:
            dw = s.door_w / 2
            add(_M_DEPOT_WALL, _depot_box(-hx, -dw, y0, y1, 0, top - COPING_T))
            add(_M_DEPOT_WALL, _depot_box(dw, hx, y0, y1, 0, top - COPING_T))
            add(_M_DEPOT_WALL, _depot_box(-dw, dw, y0, y1, s.door_h, top - COPING_T))
            for x in (-dw - FRAME_W, dw):
                add(_M_DEPOT_FRAME, face_box(x, x + FRAME_W, 0, s.door_h + FRAME_W, FRAME_OUT))
            add(_M_DEPOT_FRAME, face_box(-dw - FRAME_W, dw + FRAME_W, s.door_h, s.door_h + FRAME_W, FRAME_OUT))
            sh0 = s.door_h + FRAME_W
            if sh0 + SHUTTER_H <= band0:
                add(_M_DEPOT_SHUTTER, face_box(-dw, dw, sh0, sh0 + SHUTTER_H, SHUTTER_OUT))
        else:
            add(_M_DEPOT_WALL, _depot_box(-hx, hx, y0, y1, 0, top - COPING_T))
        add(_M_DEPOT_BAND, face_box(-hx, hx, band0, top - COPING_T, BAND_OUT), "player1")
        for x in (-hx, hx - PILASTER_W):  # 四隅の柱形
            add(_M_DEPOT_PILASTER, face_box(x, x + PILASTER_W, 0, band0, PILASTER_OUT))
        add(_M_DEPOT_COPING, _depot_box(-hx, hx, y0, y1, top - COPING_T, top))
    else:
        x0, x1 = (hx - t, hx) if side == "e" else (-hx, -hx + t)
        out = 1 if side == "e" else -1
        xo = x1 if side == "e" else x0
        yi0, yi1 = -hy + t, hy - t  # 南北の壁の間

        def face_box(ya, yb, z0, z1, d):
            a, b = sorted((xo, xo + out * d))
            return _depot_box(a, b, ya, yb, z0, z1)

        add(_M_DEPOT_WALL, _depot_box(x0, x1, yi0, yi1, 0, top - COPING_T))
        add(_M_DEPOT_BAND, face_box(yi0, yi1, band0, top - COPING_T, BAND_OUT), "player1")
        n = max(1, round(2 * hy / 3.2))
        for k in range(1, n):  # 柱形を等間隔に（四隅は南北の面が持つ）
            y = -hy + (2 * hy - PILASTER_W) * k / n
            add(_M_DEPOT_PILASTER, face_box(y, y + PILASTER_W, 0, band0, PILASTER_OUT))
        if s.windows:
            wtop = band0 - WINDOW_GAP
            count = int((2 * hy - 1.0) // WINDOW_STEP)
            start = -WINDOW_STEP * (count - 1) / 2
            for k in range(count):
                y = start + k * WINDOW_STEP
                add(_M_DEPOT_WINDOW, face_box(y - WINDOW_W / 2, y + WINDOW_W / 2, wtop - WINDOW_H, wtop, WINDOW_OUT), "window_dark")
        add(_M_DEPOT_COPING, _depot_box(x0, x1, yi0, yi1, top - COPING_T, top))
    return parts


def _depot_inner(s):
    """建物の中の面（壁の内側に薄い板を張る。入口から見える所を暗くする）。面ごとに分ける"""
    hx, hy, t, e = s.half_x, s.half_y, WALL_T, 0.01
    return {"s": _depot_box(-hx + t, hx - t, -hy + t, -hy + t + e, 0, s.wall_h),
            "n": _depot_box(-hx + t, hx - t, hy - t - e, hy - t, 0, s.wall_h),
            "e": _depot_box(hx - t - e, hx - t, -hy + t, hy - t, 0, s.wall_h),
            "w": _depot_box(-hx + t, -hx + t + e, -hy + t, hy - t, 0, s.wall_h)}


def _depot_plinth(s, side, entry):
    """足元の腰壁。外の面はタイルの端（壁の面より OUTSET 外）で、地面より PLINTH_DROP 下から立ち上げる。入口の幅は開ける"""
    e, t = TILE / 2, OUTSET + WALL_T
    z0, z1 = -PLINTH_DROP, PLINTH_H
    if side in ("s", "n"):
        y0, y1 = (-e, -e + t) if side == "s" else (e - t, e)
        if entry:
            dw = s.door_w / 2 + FRAME_W
            return [_depot_box(-e, -dw, y0, y1, z0, z1), _depot_box(dw, e, y0, y1, z0, z1)]
        return [_depot_box(-e, e, y0, y1, z0, z1)]
    x0, x1 = (e - t, e) if side == "e" else (-e, -e + t)
    return [_depot_box(x0, x1, -e + t, e - t, z0, z1)]


def build_depot(s, snow):
    """入口を南に置いた車庫を作り、[(物, 面)] を返す。面は壁の面（s・e・n・w）か、屋根は "roof"、中の面は "inner_<面>" """
    out = []
    plinth = _depot_mat(_M_DEPOT_PLINTH)
    for side in _DEPOT_SIDES:
        out.append((mesh_object(f"depot_{side}_plinth", *merge(_depot_plinth(s, side, side == "s")), plinth), side))
    for side in _DEPOT_SIDES:
        for (spec, special), geos in _depot_wall_parts(s, side, entry=side == "s").items():
            out.append((mesh_object(f"depot_{side}_{spec[0]}", *merge(geos), _depot_mat(spec, special)), side))
    inner = _depot_mat(_M_DEPOT_INNER)
    for side, geo in _depot_inner(s).items():
        if side == "s":
            # 入口の面の内側は、開口を残して張る
            dw = s.door_w / 2
            hx, hy, t, e = s.half_x, s.half_y, WALL_T, 0.01
            geo = merge([_depot_box(-hx + t, -dw, -hy + t, -hy + t + e, 0, s.wall_h),
                         _depot_box(dw, hx - t, -hy + t, -hy + t + e, 0, s.wall_h),
                         _depot_box(-dw, dw, -hy + t, -hy + t + e, s.door_h, s.wall_h)])
            # 開口の側面（壁の厚み）は入口の壁と一緒に描く（入口が手前なら手前の絵）
            jambs = merge([_depot_box(-dw - e, -dw, -hy, -hy + t, 0, s.door_h), _depot_box(dw, dw + e, -hy, -hy + t, 0, s.door_h),
                           _depot_box(-dw, dw, -hy, -hy + t, s.door_h - e, s.door_h)])
            out.append((mesh_object("depot_jamb", *jambs, inner), "s"))
        out.append((mesh_object(f"depot_inner_{side}", *geo, inner), "inner_" + side))
    # 平らな屋根: 壁の内側に床版を張り、上面は笠木の上面より PARAPET_H 下（屋上の立ち上がりが縁に見える）
    roof = _depot_mat(_M_DEPOT_ROOF_SNOW if snow else _M_DEPOT_ROOF)
    hx, hy, t = s.half_x, s.half_y, WALL_T
    z1 = s.wall_h - PARAPET_H
    out.append((mesh_object("depot_roof", *_depot_box(-hx + t, hx - t, -hy + t, hy - t, z1 - ROOF_T, z1), roof), "roof"))
    return out


def _depot_world_side(side, layout):
    return _DEPOT_SIDES[(_DEPOT_SIDES.index(side) + layout) % 4]


def _depot_layer(tag, layout):
    """どの絵に入れるか（"front"・"back"・None = 描かない）。屋根は手前、壁は回した後の面が南・東なら手前で、北・西なら奥。
    中の面は、奥の壁の内側（入口から見える）だけを奥の絵に入れる。手前の壁の内側はカメラに背を向けているので描かない
    （描くと、薄い板の表の面が建物の床の範囲を覆い、入口から下の way が見えなくなった）"""
    if tag == "roof":
        return "front"
    if tag.startswith("inner_"):
        return None if _depot_world_side(tag[6:], layout) in DEPOT_FRONT_SIDES else "back"
    return "front" if _depot_world_side(tag, layout) in DEPOT_FRONT_SIDES else "back"


def _depot_render_layer(name, obs, show):
    """show の物だけをカメラに映して描く（ほかの物は影だけ落とす。奥の壁の内側は屋根の影で暗くなる）。輪郭の薄い画素は捨てて、描いた絵に書き戻す
    （特殊色のマスク name_mask.png は render_cell が同じ映り方で描き、make_sheet が絵のパスから引く）"""
    for ob in obs:
        ob.visible_camera = ob in show
    path = render_cell(name)
    im = load_rgba8(path).copy()
    im[..., 3] = np.where(im[..., 3] >= ALPHA_KEEP, 255, 0)
    save_rgba(path, im)
    for ob in obs:
        ob.visible_camera = True
    return path


def building_sheet(sheet, build, work, layouts=4, snow=True):
    """1 タイルの建物のシート。build(snow) は入口を南に置いた [(物, 面)] を返す。layout ごとに回して奥と手前を描く。
    work は描いたセルを置くディレクトリ。シートは sheet（パス）に書く"""
    set_anchor(GROUND_CY + BUILDING_DROP)
    cells = {}
    seasons = (False, True) if snow else (False,)
    for si, is_snow in enumerate(seasons):
        for layout in range(layouts):
            clear_models()
            pairs = build(is_snow)
            obs = [ob for ob, _ in pairs]
            for ob in obs:
                ob.rotation_euler.z = math.radians(90 * layout)
            back = [ob for ob, tag in pairs if _depot_layer(tag, layout) == "back"]
            front = [ob for ob, tag in pairs if _depot_layer(tag, layout) == "front"]
            base = os.path.basename(sheet)[:-4]
            for row, (objs, suffix) in enumerate(((back, "b"), (front, "f"))):
                name = f"{base}_l{layout}_{'snow' if is_snow else 'summer'}_{suffix}"
                cells[(si * DEPOT_SNOW_ROW + row, layout)] = _depot_render_layer(name, obs, objs)
    # アイコン・カーソルのセルは空けておく（透明。AMI では blender/icons.py が書く）
    empty = np.zeros((CELL, CELL, 4), np.uint8)
    empty[..., :3] = TRANSPARENT
    empty_path = os.path.join(work, f"{os.path.basename(sheet)[:-4]}_empty.png")
    save_rgba(empty_path, empty)
    for cell in (DEPOT_ICON_CELL, DEPOT_CURSOR_CELL):
        cells[cell] = empty_path
    make_sheet(cells, 2 * len(seasons), layouts + 1, sheet)


# 車庫の種類ごとの入口の幅。箱の大きさと入口の高さは 3 種で同じ。道路はバス・トラックが入る幅の広い入口
DEPOT_SHAPES = {
    "rail": DepotShape(door_w=3.4),
    "tram": DepotShape(door_w=3.2),
    "road": DepotShape(door_w=4.6),
    "monorail": DepotShape(door_w=3.4),  # 跨座式モノレール（#113）。入口は線路と同じ（車体の幅は線路の車両と同じくらい）
    "canal": DepotShape(door_w=7.0),  # 船（#114）。pak128 の船は幅がタイルの大半あるので、入口を運河の水面に近い幅にする
}


def depot_sheet(sheet, kind, work):
    """車庫のシート（kind は DEPOT_SHAPES のキー）"""
    s = DEPOT_SHAPES[kind]
    building_sheet(sheet, lambda snow: build_depot(s, snow), work)
