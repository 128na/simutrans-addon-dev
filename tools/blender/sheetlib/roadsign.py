"""道路標識（roadsign）のシート（AMI。#122）。

本体は標識の絵を 4 枚（北・南・西・東の向きの車に向けた標識。dat の image[0]〜[3]）持ち、標識の向きに合う絵をタイルに重ねる
（obj/roadsign.cc の calc_image）。両方向の標識は 2 枚を、奥（乗り物より前に描く）と手前（後に描く）に分けて描く。
絵の位置は pak128 の標識（refs の pak128/infrastructure/road_signs/p128_sign_road_misc.png）と同じく、
その向きの車から見て右の側の、タイルの角の近く（右側通行の絵。左側通行の設定では本体が offset_left だけずらし、奥と手前の描き分けも入れ替える）:
    image[0] 北行き: 北東の角（画面の右の角）。標識の表が南を向き、画面に表が見える
    image[1] 南行き: 南西の角（画面の左の角）。表が北を向き、画面には裏が見える
    image[2] 西行き: 北西の角（画面の上の角）。表が東を向き、画面に表が見える
    image[3] 東行き: 南東の角（画面の下の角）。表が西を向き、画面には裏が見える
柱は Blender で描き（光と影を線路・道路とそろえる）、板は画面の点に 2D の絵を押す。板は pak128 と同じく画面に正対した円・三角・四角で、
数字・矢印は 1px 単位の絵にする（板は画面で 11px ほどで、Blender の面に貼った模様では数字がつぶれる）。
セルの中のタイルは pak128 の大きさ（幅 128px）で描かれるので、板の絵は画面の画素のまま押す。

シートの並び（make_sheet。dat を書く側の addons/ami/blender/ami_dat.py の ROADSIGN_* と同じ）:
    行 0 の列 0〜3: image[0]〜[3]。列 4: 行 0 がアイコン、行 1 がカーソル（AMI の blender/icons.py が書く。ここでは空けておく）
絵の位置は道路と同じ（ROAD_CY。dat のオフセット -64,-32）。雪の絵は無い（roadsign は季節の絵を持たない）。
"""
import os

import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

import bpy

from .cells import ROAD_CY, load_rgba8, make_sheet, render_cell, save_rgba
from .core import CELL, H, TILE, TRANSPARENT, box, clear_models, material, mesh_object, set_anchor

ROADSIGN_ICON_CELL = (0, 4)       # アイコンのセル（行, 列）
ROADSIGN_CURSOR_CELL = (1, 4)     # カーソルのセル
ROADSIGN_ALPHA_KEEP = 128         # この不透明度より薄い輪郭の画素は捨てる（壁と同じ。細い柱が消えない値）
# 柱の位置: 向きごとのタイルの角（Blender の x が東、y が北）。pak128 の標識の柱は、タイルの中心から角までの約 0.87 の所に立つ
ROADSIGN_CORNERS = ((1, 1), (-1, -1), (-1, 1), (1, -1))  # image[0]〜[3]: 北東・南西・北西・南東
ROADSIGN_INSET = 0.87 * TILE / 2
ROADSIGN_FACE_SHOWN = (True, False, True, False)        # 画面に表が見えるか（上の表）
ROADSIGN_PLATE_PX = 25            # 板の中心の高さ（128px の画面で、柱の足元から。pak128 の標識の板の中心は約 26px）
ROADSIGN_POLE_W = 0.2             # 柱の太さ（画面で約 2px。pak128 の標識の柱は 1〜2px）
_M_ROADSIGN_POLE = ("roadsign_pole", (0.62, 0.63, 0.64), 0.5)  # 亜鉛めっきの鋼の柱

# 板の色（RGB 0〜255。特殊色と透明色（231,255,255）から離す）
_RED = (200, 34, 40)
_BLUE = (22, 72, 172)
_WHITE = (238, 238, 236)
_BACK = (128, 130, 134)           # 板の裏（鋼板の灰）
_BACK_EDGE = (82, 84, 88)

# 3x5 の数字（行を上から。1 が字の画素）
_DIGITS = {
    "0": ("111", "101", "101", "101", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "8": ("111", "101", "111", "101", "111"),
}


def _canvas(w, h):
    return np.zeros((h, w, 4), np.uint8)


def _paint(img, mask, rgb):
    img[mask, :3] = rgb
    img[mask, 3] = 255


def _disc(d, r):
    yy, xx = np.mgrid[0:d, 0:d]
    c = (d - 1) / 2
    return np.hypot(xx - c, yy - c) <= r


def _digits(img, text, x0, y0, rgb):
    x = x0
    for ch in text:
        for r, row in enumerate(_DIGITS[ch]):
            for c, bit in enumerate(row):
                if bit == "1":
                    img[y0 + r, x + c, :3] = rgb
                    img[y0 + r, x + c, 3] = 255
        x += 4


def plate_speed(text):
    """最高速度（日本の規制標識 323）: 白い円に赤い輪、青い数字。11px"""
    img = _canvas(11, 11)
    _paint(img, _disc(11, 5.4), _RED)
    _paint(img, _disc(11, 4.4), _WHITE)  # 赤い輪は 1px（数字が輪に掛からないように）
    _digits(img, text, 2, 3, _BLUE)
    return img


def plate_min_speed(text):
    """最低速度（323 の 2）: 青い円に白い数字と下線。11px"""
    img = _canvas(11, 11)
    _paint(img, _disc(11, 5.4), _BLUE)
    _digits(img, text, 2, 2, _WHITE)
    img[8, 3:8, :3] = _WHITE
    return img


def plate_stop():
    """一時停止（330）: 赤い逆三角に白い縁、中に白い字の帯（「止まれ」は画面で読めないので帯で表す）。幅 13・高さ 11"""
    w, h = 13, 11
    img = _canvas(w, h)
    yy, xx = np.mgrid[0:h, 0:w]
    c = (w - 1) / 2
    half = lambda y: (w / 2) * (1 - (y + 0.5) / h)
    tri = np.abs(xx - c) <= half(yy) + 0.3
    _paint(img, tri, _WHITE)
    inner = (np.abs(xx - c) <= half(yy) - 1.3) & (yy >= 1)
    _paint(img, inner, _RED)
    img[3, 4:9, :3] = _WHITE
    return img


def plate_one_way():
    """一方通行（326 の B。縦の板）: 青い四角に白い上向きの矢印。幅 7・高さ 11"""
    w, h = 7, 11
    img = _canvas(w, h)
    img[..., :3] = _BLUE
    img[..., 3] = 255
    for y, (x0, x1) in {1: (3, 3), 2: (2, 4), 3: (1, 5)}.items():
        img[y, x0:x1 + 1, :3] = _WHITE
    img[4:10, 3, :3] = _WHITE
    return img


def plate_back(face):
    """板の裏: 表と同じ形の灰色の板に、暗い縁"""
    img = np.zeros_like(face)
    shape = face[..., 3] > 0
    _paint(img, shape, _BACK)
    edge = shape & ~(np.roll(shape, 1, 0) & np.roll(shape, -1, 0) & np.roll(shape, 1, 1) & np.roll(shape, -1, 1))
    _paint(img, edge, _BACK_EDGE)
    return img


ROADSIGN_PLATES = {
    "one_way": plate_one_way,
    "stop": plate_stop,
    "speed_40": lambda: plate_speed("40"),
    "speed_60": lambda: plate_speed("60"),
    "speed_80": lambda: plate_speed("80"),
    "min_50": lambda: plate_min_speed("50"),
}


def _stamp(cell, plate, cx, cy):
    """板の絵を、セルの (cx, cy)（板の中心）に押す"""
    h, w = plate.shape[:2]
    x0 = int(round(cx)) - w // 2
    y0 = int(round(cy)) - h // 2
    on = plate[..., 3] > 0
    cell[y0:y0 + h, x0:x0 + w][on] = plate[on]


def _cell_xy(p):
    """世界の点 → セルの画素（左上が 0）"""
    scene = bpy.context.scene
    v = world_to_camera_view(scene, scene.camera, Vector(p))
    return v.x * CELL, (1 - v.y) * CELL


def roadsign_sheet(sheet, plate, work):
    """標識のシート。plate は ROADSIGN_PLATES のキー。work は描いたセルを置くディレクトリ"""
    set_anchor(ROAD_CY)
    face = ROADSIGN_PLATES[plate]()
    back = plate_back(face)
    base = os.path.basename(sheet)[:-4]
    z = ROADSIGN_PLATE_PX * H / 16
    cells = {}
    for i, (sx, sy) in enumerate(ROADSIGN_CORNERS):
        clear_models()
        x, y = sx * ROADSIGN_INSET, sy * ROADSIGN_INSET
        mesh_object(f"{base}_pole", *box(x, y, z / 2, ROADSIGN_POLE_W, ROADSIGN_POLE_W, z), material(*_M_ROADSIGN_POLE))
        path = render_cell(f"{base}_{i}")
        im = load_rgba8(path).copy()
        im[..., 3] = np.where(im[..., 3] >= ROADSIGN_ALPHA_KEEP, 255, 0)
        cx, cy = _cell_xy((x, y, z))
        _stamp(im, face if ROADSIGN_FACE_SHOWN[i] else back, cx, cy)
        save_rgba(path, im)
        cells[(0, i)] = path
    # アイコン・カーソルのセルは空けておく（透明。AMI では blender/icons.py が書く）
    empty = np.zeros((CELL, CELL, 4), np.uint8)
    empty[..., :3] = TRANSPARENT
    empty_path = os.path.join(work, f"{base}_empty.png")
    save_rgba(empty_path, empty)
    for cell in (ROADSIGN_ICON_CELL, ROADSIGN_CURSOR_CELL):
        cells[cell] = empty_path
    make_sheet(cells, 2, 5, sheet)
