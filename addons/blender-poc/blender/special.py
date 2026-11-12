"""特殊色の検査: シート画像に特殊色がどれだけ含まれるかを、種類・セルごとに数える。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/special.py -- src/track.png src/tollbooth.png ...

意図しない特殊色は render.py の後処理で 1 ずらして消している。ここで 0 になっていれば消えている。
意図して入れた特殊色（材質に special を付けたもの）は、入れたセルにだけ出ていればよい。
"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import SPECIAL, SPECIAL_COLORS, CELL  # noqa: E402

# 後処理の「1ずらす」が別の特殊色に当たらないこと
for r, g, b in SPECIAL_COLORS:
    shifted = (min(r + 1, 255), min(g + 1, 255), min(b + 1, 255))
    assert shifted not in SPECIAL_COLORS, f"ずらした先も特殊色: {(r, g, b)} -> {shifted}"
print("== ずらした先が特殊色になる色: なし")

name_of = {c: f"{name}[{i}]" if len(cs) > 1 else name for name, cs in SPECIAL.items() for i, c in enumerate(cs)}

for path in sys.argv[sys.argv.index("--") + 1:]:
    img = bpy.data.images.load(os.path.abspath(path), check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    rgb = (np.flipud(px.reshape(h, w, 4))[..., :3] * 255 + 0.5).astype(np.int32)
    keys = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]
    total = 0
    lines = []
    for c, name in name_of.items():
        ys, xs = np.nonzero(keys == c[0] * 65536 + c[1] * 256 + c[2])
        if len(ys):
            cells = sorted({(y // CELL, x // CELL) for y, x in zip(ys, xs)})
            lines.append(f"    {name:16s} {len(ys):6d}px  セル {', '.join(f'{r}.{c}' for r, c in cells)}")
            total += len(ys)
    print(f"== {path}: 特殊色 {total}px")
    for line in lines:
        print(line)
