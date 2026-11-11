"""描画位置の検証: Blender の出力と iss の既存画像で、セル内の描画範囲を比べる。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/check.py -- <iss の線路画像>
"""
import os
import sys

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
CELL = 256


def load(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return np.flipud((px.reshape(h, w, 4) * 255 + 0.5).astype(np.uint8))


def bbox(cell):
    """不透明な画素（アルファ25以上、#E7FFFF 以外）の範囲 (x0, y0, x1, y1)。"""
    mask = cell[..., 3] >= 25
    mask &= ~((cell[..., 0] == 231) & (cell[..., 1] == 255) & (cell[..., 2] == 255))
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def cell_of(sheet, r, c):
    return sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]


iss_path = sys.argv[sys.argv.index("--") + 1]
iss = load(iss_path)

print("== 基準: タイル菱形（期待値 x64-191, y96-159 / 坂は上端が16px上）")
for name in ("check_tile_flat", "check_tile_up12"):
    print(f"  {name:16s} {bbox(load(os.path.join(WORK, name + '.png')))}")

def centroid(cell):
    mask = cell[..., 3] >= 25
    mask &= ~((cell[..., 0] == 231) & (cell[..., 1] == 255) & (cell[..., 2] == 255))
    ys, xs = np.nonzero(mask)
    return float(xs.mean()), float(ys.mean())


def tilt(cell):
    """描画の傾き。正: 右下がり（＼）、負: 右上がり（／）。"""
    mask = cell[..., 3] >= 25
    mask &= ~((cell[..., 0] == 231) & (cell[..., 1] == 255) & (cell[..., 2] == 255))
    ys, xs = np.nonzero(mask)
    return float(np.corrcoef(xs, ys)[0, 1])


# 重心のずれが大きいセルは、向きやセル割り当ての取り違えを疑う
LIMIT = 12
print(f"== iss と比較（描画範囲 x0,y0,x1,y1 と重心のずれ。{LIMIT}px 超は NG）")
pairs = {
    (0, 2): "ns", (0, 3): "ew", (0, 5): "s", (0, 6): "w", (0, 7): "n", (0, 8): "e",
    (0, 9): "single",
    (1, 0): "up12", (1, 1): "up9", (1, 2): "up3", (1, 3): "up6",
    (1, 5): "up2_12", (1, 6): "up2_9", (1, 7): "up2_3", (1, 8): "up2_6",
    (2, 0): "diag_sw", (2, 1): "diag_nw", (2, 2): "diag_ne", (2, 3): "diag_se",
    (2, 5): "curve_sw", (2, 6): "curve_nw", (2, 7): "curve_ne", (2, 8): "curve_se",
    (3, 5): "nse", (3, 6): "new", (3, 7): "nsw", (3, 8): "sew", (3, 9): "nsew",
}
ng = 0
for (r, c), name in pairs.items():
    mine = load(os.path.join(WORK, f"track_{name}.png"))
    ref = cell_of(iss, r, c)
    (mx, my), (rx, ry) = centroid(mine), centroid(ref)
    d = ((mx - rx) ** 2 + (my - ry) ** 2) ** 0.5
    tm, tr = tilt(mine), tilt(ref)
    # 傾きがはっきりしているセルは、向きが iss と同じかも見る
    same_tilt = not (abs(tm) > 0.3 and abs(tr) > 0.3 and tm * tr < 0)
    flag = "OK" if d <= LIMIT and same_tilt else "NG"
    ng += flag == "NG"
    print(f"  [{r}.{c}] {name:9s} {flag} ずれ{d:5.1f}px 傾き{tm:+.2f}/{tr:+.2f}  blender={bbox(mine)}  iss={bbox(ref)}")
print(f"== NG {ng} 件")
