"""画面のスクリーンショットから同じ矩形を切り出し、格子に並べて 1 枚にする（間は白 4px）。

使い方: blender -b --factory-startup --python ../../tools/blender/grid.py -- 出力.png x0,y0,x1,y1 列の数 入力1.png 入力2.png ...
    矩形は左上を原点とする画素座標。入力は行ごとに左から並べる（例: addons/ami/ingame/curve_base_study.sh の COMPOSE=1）
"""
import os
import sys

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
out = a[0]
x0, y0, x1, y1 = map(int, a[1].split(","))
nc = int(a[2])
ins = a[3:]
G = 4
tiles = []
for p in ins:
    img = bpy.data.images.load(os.path.abspath(p), check_existing=False)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1]
    tiles.append(px[y0:y1, x0:x1])
th, tw = y1 - y0, x1 - x0
nr = (len(tiles) + nc - 1) // nc
res = np.ones((nr * th + (nr - 1) * G, nc * tw + (nc - 1) * G, 4), dtype=np.float32)
for i, t in enumerate(tiles):
    r, c = divmod(i, nc)
    res[r * (th + G):r * (th + G) + th, c * (tw + G):c * (tw + G) + tw] = t
H, W = res.shape[:2]
o = bpy.data.images.new("o", W, H, alpha=True)
o.pixels[:] = res[::-1].ravel()
o.filepath_raw = os.path.abspath(out)
o.file_format = "PNG"
o.save()
