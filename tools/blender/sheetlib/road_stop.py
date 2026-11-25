"""道路の停留所（building の stop・waytype=road。AMI の ami_road_bus_stop・ami_road_truck_stop。#277）のシート。
道路の見える側（南北の道路なら東、東西の道路なら南）の脇に、ホーム（バス停）か積み降ろし場（トラックの荷役所）を置く。道路そのものは描かない。

本体の層の決め方は操車場と同じ（bauer/hausbauer.cc の build_station_extension_depot。層が 8 の停留所は、道路・線路の区別なく、
ビット 0 = 道路の向き（0 = 南北、1 = 東西）、ビット 1（2）= 南・東の側に隣の停留所が無い、ビット 2（4）= 北・西の側に隣の停留所が無い）。
そのため向きと端の決め方は yard.py の yard_layout をそのまま使う。

ホームは、道路の車道の縁（ROAD_HW = 3.6。縁石の立ち上がり）の外から、タイルの端の内（4.95）まで。歩道（ami_sidewalk）の帯と重なる。
ホーム・積み降ろし場の床は奥の絵（車両の下）、屋根・標識・木箱は手前の絵（車両の上）に描く。

シートの並び（addons/ami/blender/ami_dat.py の ROAD_STOP_* と同じ）:
    列 0〜7: layout 0〜7
    行 0: 夏の奥の絵、行 1: 夏の手前の絵、行 2・3: 雪の奥・手前（dat の季節 [1]）
    列 8: 行 0 がアイコン、行 1 がカーソル（AMI の blender/icons.py が書く。ここでは空けておく）
絵の位置とオフセットは車庫と同じ（depot.py の BUILDING_DROP・BUILDING_OFFSET）。箱積み駅舎の箱 1 段（高さ 2 段 = 32px）の中に収める。
"""
import math
import os

import numpy as np

from .cells import GROUND_CY, make_sheet, save_rgba
from .core import CELL, TILE, TRANSPARENT, clear_models, material, merge, mesh_object, set_anchor
from .depot import BUILDING_DROP, _depot_box, _depot_render_layer
from .road_parts import ROAD_HW
from .yard import yard_layout

ROAD_STOP_LAYOUTS = 8
ROAD_STOP_SNOW_ROW = 2                          # 雪の絵の行のずらし（夏の奥・手前が行 0・1）
ROAD_STOP_ICON_CELL = (0, ROAD_STOP_LAYOUTS)    # アイコンのセル（行, 列）
ROAD_STOP_CURSOR_CELL = (1, ROAD_STOP_LAYOUTS)

# ---- 寸法（タイル 1 辺 = 10。高さ 1 段は H ≈ 2.04 で、画面の 16px。1 単位 = 約 2.6m の縮尺だが、絵は見た目で決める）
PLATFORM_U0 = ROAD_HW + 0.1        # ホームの道路の側の縁（車道の縁の外）
PLATFORM_U1 = TILE / 2 - 0.05      # 外の縁（タイルの端の内）
END_INSET = TILE / 2 - 0.2         # 切れた端で、ホームの床の端を置く位置（タイルの端から少し内）
RAMP_L = 1.2                       # 切れた端の斜路（段の連なり）の長さ（道路に沿う）
RS_POST_W = 0.2                       # 柱の太さ（細いと 1px に満たず、輪郭の画素として捨てられる）

# 種類ごとの寸法
ROAD_STOP_SHAPES = {
    # バス停: 低いホームに、小さな屋根の待合と標識
    "bus": dict(deck_z=0.35, ramp_steps=2, deck_rgb=(0.66, 0.66, 0.64), edge_rgb=(0.95, 0.80, 0.18)),
    # トラックの荷役所: 高い積み降ろし場に木箱と標識
    "truck": dict(deck_z=1.0, ramp_steps=4, deck_rgb=(0.56, 0.57, 0.58), edge_rgb=(0.95, 0.70, 0.10)),
}
RS_ROOF_Z = 2.7                       # バス停の屋根の下面
RS_ROOF_T = 0.16                      # 屋根の厚み
RS_SIGN_H = 2.6                       # 標識の柱の高さ（床の上面から）
RS_CRATE = (1.2, 1.2, 1.0)            # 木箱（トラックの荷役所）の大きさ（x, y, z）

_M_RS_SNOW = ("rs_snow", (0.90, 0.93, 0.97), 0.9)
_M_RS_FRAME = ("rs_frame", (0.40, 0.42, 0.44), 0.6)       # 柱・梁
_M_RS_ROOF = ("rs_roof", (0.20, 0.42, 0.62), 0.5)         # 屋根（青）
_M_RS_PLATE = ("rs_plate", (0.10, 0.32, 0.72), 0.4)       # 標識の板（青）
_M_RS_PLATE_TRUCK = ("rs_plate_truck", (0.95, 0.70, 0.10), 0.4)  # 荷役所の標識の板（黄）
_M_RS_CRATE = ("rs_crate", (0.55, 0.38, 0.20), 0.8)       # 木箱
_M_RS_GLASS = ("rs_glass", (0.62, 0.78, 0.84), 0.3)       # 待合の背の板


def _rs_mat(spec):
    name, rgb, rough = spec
    return material(name, rgb, rough=rough)


def _rs_span(open_minus, open_plus):
    """床の範囲（道路に沿う y）。つながる側はタイルの端まで、切れた側は斜路の上の端まで"""
    y0 = -(END_INSET - RAMP_L) if open_minus else -TILE / 2
    y1 = (END_INSET - RAMP_L) if open_plus else TILE / 2
    return y0, y1


def _rs_obj(name, boxes, spec):
    return mesh_object(name, *merge(boxes), _rs_mat(spec)) if boxes else None


def build_road_stop(kind, snow, open_minus, open_plus):
    """道路を y に沿わせ、見える側（+x）に床を置いた停留所の (奥の絵の [物], 手前の絵の [物]) を返す。
    open_minus・open_plus は -y・+y の端が切れているか（斜路を付ける）"""
    s = ROAD_STOP_SHAPES[kind]
    z1 = s["deck_z"]
    x0, x1 = PLATFORM_U0, PLATFORM_U1
    y0, y1 = _rs_span(open_minus, open_plus)
    deck = [_depot_box(x0 + 0.3, x1, y0, y1, 0.0, z1)]
    edge = [_depot_box(x0, x0 + 0.3, y0, y1, 0.0, z1)]  # 道路の側の縁の帯（黄）
    # 斜路: 床の端から外へ、段で地面へ下りる
    for sign, is_open, y_end in ((-1, open_minus, y0), (1, open_plus, y1)):
        if not is_open:
            continue
        step = RAMP_L / s["ramp_steps"]
        for k in range(s["ramp_steps"]):
            a = y_end + sign * step * k
            b = a + sign * step
            top = z1 * (s["ramp_steps"] - k - 1) / s["ramp_steps"] + z1 / s["ramp_steps"] * 0.5
            deck.append(_depot_box(x0, x1, min(a, b), max(a, b), 0.0, top))
    deck_obj = mesh_object("rs_deck", *merge(deck), _rs_mat(_M_RS_SNOW if snow else (f"rs_deck_{kind}", s["deck_rgb"], 0.7)))
    back = [deck_obj, _rs_obj("rs_edge", edge, (f"rs_edge_{kind}", s["edge_rgb"], 0.6))]
    front = []
    # 標識: 切れていない側のタイルの端寄りの、柱と板
    px, py = x1 - 0.5, y0 + 1.0 if not open_minus else 0.0
    pole = [_depot_box(px, px + RS_POST_W, py, py + RS_POST_W, z1, z1 + RS_SIGN_H)]
    plate = [_depot_box(px - 0.3, px + RS_POST_W + 0.3, py - 0.04, py + RS_POST_W + 0.04, z1 + RS_SIGN_H - 0.9, z1 + RS_SIGN_H)]
    front += [_rs_obj("rs_pole", pole, _M_RS_FRAME), _rs_obj("rs_plate", plate, _M_RS_PLATE if kind == "bus" else _M_RS_PLATE_TRUCK)]
    if kind == "bus":
        # 待合: 2 本の柱と屋根。背（外の縁）に板
        ya, yb = max(y0 + 0.8, -2.2), min(y1 - 0.8, 2.2)
        if yb - ya > 1.5:
            posts = [_depot_box(x1 - 0.5 - RS_POST_W, x1 - 0.5, y - RS_POST_W / 2, y + RS_POST_W / 2, z1, z1 + RS_ROOF_Z)
                     for y in (ya, yb)]
            roof = [_depot_box(x0 + 0.5, x1 + 0.0, ya - 0.3, yb + 0.3, z1 + RS_ROOF_Z, z1 + RS_ROOF_Z + RS_ROOF_T)]
            back_wall = [_depot_box(x1 - 0.1, x1, ya, yb, z1 + 0.9, z1 + RS_ROOF_Z - 0.2)]  # 背の板（腰から上の透けた板。低い所は抜く）
            bench = [_depot_box(x1 - 1.0, x1 - 0.5, ya + 0.4, yb - 0.4, z1, z1 + 0.5)]
            front += [_rs_obj("rs_posts", posts, _M_RS_FRAME),
                      _rs_obj("rs_roof", roof, _M_RS_SNOW if snow else _M_RS_ROOF),
                      _rs_obj("rs_glass", back_wall, _M_RS_GLASS), _rs_obj("rs_bench", bench, _M_RS_FRAME)]
    else:
        # 木箱を 2 つ、積み降ろし場に置く（端が切れた側は避ける）
        cx = (x0 + 0.3 + x1) / 2
        ys = [y for y in (-2.0, 1.6) if y0 + 0.9 < y < y1 - 0.9]
        crates = [_depot_box(cx - RS_CRATE[0] / 2, cx + RS_CRATE[0] / 2, y - RS_CRATE[1] / 2, y + RS_CRATE[1] / 2, z1, z1 + RS_CRATE[2])
                  for y in ys]
        front.append(_rs_obj("rs_crates", crates, _M_RS_CRATE))
    return back, [o for o in front if o is not None]


def road_stop_sheet(sheet, kind, work):
    """停留所のシート（kind は ROAD_STOP_SHAPES のキー。8 layout × 夏・雪の奥・手前。列 8 はアイコン・カーソル）"""
    set_anchor(GROUND_CY + BUILDING_DROP)
    cells = {}
    base = os.path.basename(sheet)[:-4]
    for si, is_snow in enumerate((False, True)):
        for layout in range(ROAD_STOP_LAYOUTS):
            clear_models()
            rot, open_minus, open_plus = yard_layout(layout)
            back, front = build_road_stop(kind, is_snow, open_minus, open_plus)
            obs = back + front
            for ob in obs:
                ob.rotation_euler.z = math.radians(rot)
            for row, (objs, suffix) in enumerate(((back, "b"), (front, "f"))):
                name = f"{base}_l{layout}_{'snow' if is_snow else 'summer'}_{suffix}"
                cells[(si * ROAD_STOP_SNOW_ROW + row, layout)] = _depot_render_layer(name, obs, objs)
    empty = np.zeros((CELL, CELL, 4), np.uint8)
    empty[..., :3] = TRANSPARENT
    empty_path = os.path.join(work, f"{base}_empty.png")
    save_rgba(empty_path, empty)
    for cell in (ROAD_STOP_ICON_CELL, ROAD_STOP_CURSOR_CELL):
        cells[cell] = empty_path
    make_sheet(cells, 2 * ROAD_STOP_SNOW_ROW, ROAD_STOP_LAYOUTS + 1, sheet)
