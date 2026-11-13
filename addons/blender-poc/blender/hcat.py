"""画面のスクリーンショットを横に並べて 1 枚にする（上のツールバーと下の状態行は切る）。

使い方: blender -b --factory-startup --python blender/hcat.py -- 出力.png 入力1.png 入力2.png ...
"""
import os
import sys

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]


def load(p):
    i = bpy.data.images.load(os.path.abspath(p))
    w, h = i.size
    x = np.empty(w * h * 4, np.float32)
    i.pixels.foreach_get(x)
    return np.flipud(x.reshape(h, w, 4))[60:520]


v = np.concatenate([load(p) for p in a[1:]], 1)
H, W, _ = v.shape
o = bpy.data.images.new("o", W, H)
o.pixels.foreach_set(np.flipud(v).ravel())
o.filepath_raw = os.path.abspath(a[0])
o.file_format = "PNG"
o.save()
