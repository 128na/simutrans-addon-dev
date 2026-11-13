"""特殊色の見え方の再現: シートの1行目のセルを「昼」「会社の色を変えたとき」「夜」で並べた画像を作る。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/special_preview.py -- src/tollbooth.png 4 docs/special_preview.png

色の置き換えは Simutrans 本体 display/simgraph16.cc の calc_base_pal_from_night_shift と同じ式
（夜の段階 4、light_level 0）。ゲーム内の色は RGB555/565 に丸められるので、細かい値は少し違う。
"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import SPECIAL, CELL, TRANSPARENT  # noqa: E402

# special_pal の 5 番目の段（赤橙）。会社の色をこれに変えたときの見え方にする
RED = [(86, 32, 14), (110, 40, 16), (134, 48, 18), (158, 57, 20), (182, 65, 22), (206, 74, 24), (230, 82, 26), (255, 91, 28)]
# display_night_lights（夜の光の色）。並びは SPECIAL の player1/player2 より後ろと同じ
NIGHT_LIGHTS = {
    "window_dark": (0xD3, 0xC3, 0x80), "window_light": (0x80, 0xC3, 0xD3), "light_white": (0xFF, 0xFF, 0xE3),
    "window_lit1": (0xD3, 0xC3, 0x80), "window_lit2": (0xD3, 0xC3, 0x80), "light_purple": (0xE1, 0x00, 0xE1),
}
NIGHT = 4
RG, B = 0.75 ** NIGHT, 0.83 ** NIGHT

args = sys.argv[sys.argv.index("--") + 1:]
src, cols, out = args[0], int(args[1]), args[2]
img = bpy.data.images.load(os.path.abspath(src))
w, h = img.size
px = np.empty(w * h * 4, np.float32)
img.pixels.foreach_get(px)
rgb = (np.flipud(px.reshape(h, w, 4))[:CELL, :cols * CELL, :3] * 255 + 0.5).astype(np.int32)
keys = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]
bg = np.all(rgb == TRANSPARENT, axis=-1)

recolor = rgb.copy()
night = (rgb * np.array([RG, RG, B])).astype(np.int32)
for name, colors in SPECIAL.items():
    for i, c in enumerate(colors):
        sel = keys == c[0] * 65536 + c[1] * 256 + c[2]
        if name == "player1":
            recolor[sel] = RED[i]
            night[sel] = (np.array(c) * np.array([RG, RG, B])).astype(np.int32)
        elif name == "player2":
            night[sel] = (np.array(c) * np.array([RG, RG, B])).astype(np.int32)
        else:
            night[sel] = NIGHT_LIGHTS.get(name, c)  # 光の色は暗くならない
night[bg] = (48, 52, 64)
rows = np.concatenate([rgb, recolor, night], axis=0)
rows = rows.repeat(2, 0).repeat(2, 1)
H, W, _ = rows.shape
o = bpy.data.images.new("o", W, H)
o.pixels.foreach_set((np.flipud(np.concatenate([rows, np.full((H, W, 1), 255)], 2)).astype(np.float32) / 255).ravel())
o.filepath_raw = os.path.abspath(out)
o.file_format = "PNG"
o.save()
print("[preview]", out)
