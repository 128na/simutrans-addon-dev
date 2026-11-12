"""画像（ゲームの画面・合成図）の指定した点の周りを切り出して拡大し、横に並べる。点の画素は紫に印を付ける。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/zoom.py -- 入力.png 出力.png 半径 倍率 x,y [x,y ...]

    例: ingame_diff.py が出した形の候補の座標を、6倍で見る
    blender ... -- work/check/track_dg2.png work/zoom.png 24 6 73,388 566,388

ツールが出した候補（ingame_diff.py の [shape]・[diff]）を目で確かめるときや、つなぎ目の角を見るときに使う。
"""
import os
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
src, out, r, s = args[0], args[1], int(args[2]), int(args[3])
img = bpy.data.images.load(os.path.abspath(src), check_existing=False)
w, h = img.size
p = np.empty(w * h * 4, np.float32)
img.pixels.foreach_get(p)
p = np.flipud(p.reshape(h, w, 4))
parts = []
for spec in args[4:]:
    x, y = (int(v) for v in spec.split(","))
    t = np.zeros((2 * r + 1, 2 * r + 1, 4), np.float32)
    t[..., 3] = 1
    y0, y1, x0, x1 = max(y - r, 0), min(y + r + 1, h), max(x - r, 0), min(x + r + 1, w)
    t[y0 - (y - r):y1 - (y - r), x0 - (x - r):x1 - (x - r)] = p[y0:y1, x0:x1]
    t[r, r, :3] = t[r, r, :3] * 0.3 + np.array([1, 0, 1]) * 0.7
    parts.append(t.repeat(s, 0).repeat(s, 1))
    parts.append(np.ones((t.shape[0] * s, 4, 4), np.float32))
v = np.concatenate(parts[:-1], 1)
H, W, _ = v.shape
o = bpy.data.images.new("o", W, H)
o.pixels.foreach_set(np.flipud(v).ravel())
o.filepath_raw = os.path.abspath(out)
o.file_format = "PNG"
o.save()
print("[zoom]", out, W, H)
