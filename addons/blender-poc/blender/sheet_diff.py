"""2 枚のシート（前と後）をセルごとに比べる: 透過（#E7FFFF）の範囲が変わった画素数と、色が変わった画素数。

使い方（アドオンのディレクトリで）:
    git show HEAD:addons/blender-poc/src/track.png > work/before_track.png
    blender -b --factory-startup --python blender/sheet_diff.py -- work/before_track.png src/track.png

透過の範囲が変わったセルだけを出し、最後に合計を出す。環境変数 ALL=1 で、色だけが変わったセルも出す。
汚れのように色だけを意図して変えたときは、透過の範囲の差が 0 であることを見る（輪郭が変わっていない）。
"""
import os, sys
import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]


def load(p):
    i = bpy.data.images.load(os.path.abspath(p), check_existing=False)
    w, h = i.size
    x = np.empty(w * h * 4, np.float32)
    i.pixels.foreach_get(x)
    return np.round(np.flipud(x.reshape(h, w, 4))[..., :3] * 255).astype(int)


b, n = load(a[0]), load(a[1])
if b.shape != n.shape:
    print("[diff] size differs", b.shape, n.shape)
    sys.exit(1)
key = lambda x: (x[..., 0] == 231) & (x[..., 1] == 255) & (x[..., 2] == 255)
kb, kn = key(b), key(n)
col = (np.abs(b - n).max(-1) > 0) & ~kb & ~kn
rows, cols = b.shape[0] // 256, b.shape[1] // 256
tot_a = tot_c = 0
for r in range(rows):
    for c in range(cols):
        s = np.s_[r * 256:(r + 1) * 256, c * 256:(c + 1) * 256]
        da, dc = int((kb[s] != kn[s]).sum()), int(col[s].sum())
        tot_a += da
        tot_c += dc
        if da or (os.environ.get("ALL") and dc):
            print(f"[diff] cell {r},{c}: alpha {da} px, colour {dc} px")
print(f"[diff] {os.path.basename(a[1])}: alpha differs {tot_a} px, colour differs {tot_c} px")
