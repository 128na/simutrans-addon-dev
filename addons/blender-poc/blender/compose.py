"""つなぎ目の確認: シートのセルを、ゲームと同じ位置・順番でタイルに並べて重ねる（ゲームを起動せずにバリを見る）。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/compose.py -- road work/compose_road.png [倍率] [all|diag|slope|loop]

並べ方は Simutrans と同じ: マップ (i, j)（i が東、j が南）、高さ z のタイルを画面 ((i-j)*64, (i+j)*32 - z*16) に置き、
奥（i+j が小さい）から順に描く。#E7FFFF は透明。背景は草の色にして、透けた画素が緑で見えるようにする。
"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import CELL, SRC, TRANSPARENT  # noqa: E402

GRASS = (70, 130, 40)

# セル位置（行, 列）。dat の割り当てと同じ
IMG = {
    "ns": (0, 2), "ew": (0, 3), "s": (0, 5), "w": (0, 6), "n": (0, 7), "e": (0, 8),
    "up12": (1, 0), "up9": (1, 1), "up3": (1, 2), "up6": (1, 3),
    "up2_12": (1, 5), "up2_9": (1, 6), "up2_3": (1, 7), "up2_6": (1, 8),
    "dsw": (2, 0), "dnw": (2, 1), "dne": (2, 2), "dse": (2, 3),
    "sw": (2, 5), "nw": (2, 6), "ne": (2, 7), "se": (2, 8),
    "nse": (3, 5), "new": (3, 6), "nsw": (3, 7), "sew": (3, 8), "nsew": (3, 9),
}
# 高速道路のカーブは斜めの絵を使う（expressway.dat の image[sw] など）
IMG_EXPWY = dict(IMG, sw=(2, 0), nw=(2, 1), ne=(2, 2), se=(2, 3))


def staircase(i0, j0, n, dj):
    """斜め: 東→北（dj=-1）または東→南（dj=+1）を交互に進む。端は直線。"""
    tiles = [(i0 - 1, j0, 0, "ew")]
    i, j = i0, j0
    for k in range(n):
        if k % 2 == 0:  # 西から来て、北/南へ出る
            tiles.append((i, j, 0, "dnw" if dj < 0 else "dsw"))
            j += dj
        else:  # 南/北から来て、東へ出る
            tiles.append((i, j, 0, "dse" if dj < 0 else "dne"))
            i += 1
    # 抜けた先も直線（n が偶数なら東へ、奇数なら北/南へ出る）
    tiles.append((i, j, 0, "ew" if n % 2 == 0 else "ns"))
    return tiles


def slope_cross(i0, j0):
    """中央を1段上げ、四方の坂を十字に越える（ingame/all_dirs.nut と同じ形）。"""
    t = [(i0, j0, 1, "nsew"),
         (i0, j0 - 1, 0, "up3"), (i0, j0 + 1, 0, "up12"), (i0 - 1, j0, 0, "up6"), (i0 + 1, j0, 0, "up9")]
    for d in (2, 3):
        t += [(i0, j0 - d, 0, "ns"), (i0, j0 + d, 0, "ns"), (i0 - d, j0, 0, "ew"), (i0 + d, j0, 0, "ew")]
    return t


def loop(i0, j0, n=4):
    """四角い輪: カーブ4方向と直線のつなぎ目（ingame/all_dirs.nut の loop と同じ形）。"""
    t = [(i0, j0, 0, "se"), (i0 + n, j0, 0, "sw"), (i0 + n, j0 + n, 0, "nw"), (i0, j0 + n, 0, "ne")]
    for k in range(1, n):
        t += [(i0 + k, j0, 0, "ew"), (i0 + k, j0 + n, 0, "ew"), (i0, j0 + k, 0, "ns"), (i0 + n, j0 + k, 0, "ns")]
    return t


LAYOUTS = {
    "all": staircase(0, 0, 8, -1) + staircase(0, 6, 8, +1) + slope_cross(9, 3) + loop(14, -6),
    "diag": staircase(0, 0, 8, -1) + staircase(0, 6, 8, +1),
    "slope": slope_cross(0, 0),
    "loop": loop(0, 0),
}


def load(path):
    img = bpy.data.images.load(os.path.abspath(path), check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return (np.flipud(px.reshape(h, w, 4))[..., :3] * 255 + 0.5).astype(np.uint8)


def compose(sheet, layout, img=IMG):
    xs = [(i - j) * 64 for i, j, _, _ in layout]
    ys = [(i + j) * 32 - z * 16 for i, j, z, _ in layout]
    x0, y0 = min(xs) - CELL, min(ys) - CELL
    W, H = max(xs) - x0 + CELL, max(ys) - y0 + CELL
    out = np.empty((H, W, 3), np.uint8)
    out[...] = GRASS
    for i, j, z, key in sorted(layout, key=lambda t: (t[0] + t[1], t[2])):
        r, c = img[key]
        cell = sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
        mask = np.any(cell != TRANSPARENT, axis=-1)
        x, y = (i - j) * 64 - x0 - CELL // 2, (i + j) * 32 - z * 16 - y0 - CELL // 2
        region = out[y:y + CELL, x:x + CELL]
        region[mask] = cell[mask]
    # 何も描かれていない外側を切り詰める
    used = np.any(out != GRASS, axis=-1)
    ys_, xs_ = np.nonzero(used)
    return out[ys_.min() - 8:ys_.max() + 9, xs_.min() - 8:xs_.max() + 9]


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:]
    name, out_path = args[0], args[1]
    scale = int(args[2]) if len(args) > 2 else 1
    layout = LAYOUTS[args[3] if len(args) > 3 else "all"]
    img = compose(load(os.path.join(SRC, name + ".png")), layout, IMG_EXPWY if name == "expressway" else IMG)
    img = img.repeat(scale, 0).repeat(scale, 1)
    h, w, _ = img.shape
    o = bpy.data.images.new("o", w, h)
    rgba = np.concatenate([img, np.full((h, w, 1), 255, np.uint8)], 2)
    o.pixels.foreach_set((np.flipud(rgba).astype(np.float32) / 255).ravel())
    o.filepath_raw = os.path.abspath(out_path)
    o.file_format = "PNG"
    o.save()
    print("[compose]", out_path, w, h)
