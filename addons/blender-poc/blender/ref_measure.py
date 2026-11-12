"""手本の絵（pak128 標準・iss・SIS などの元画像、またはこのアドオンのシート）で、線路・道路がタイルのどこに描かれているかを測る。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/ref_measure.py -- 画像.png セルの大きさ 向き=行.列 [向き=行.列 ...]

    例: pak128 標準の Rail_100（128px セル）
    blender ... -- ../../../pak128/infrastructure/rail_tracks/rail_100_tracks.png 128 ew=1.6 ns=1.5 sw=4.1 ne=3.6 nw=4.0 se=3.7
    例: このアドオンの線路（256px セル）
    blender ... -- src/track.png 256 ns=0.2 ew=0.3 sw=2.0 nw=2.1 ne=2.2 se=2.3

向き: ew・ns（直線）、sw・ne（画面で縦向きの斜め）、nw・se（画面で横向きの斜め）。
タイルの菱形は pak128 の 128×64px。タイル中心は 128px セルで (64, 96)、256px セル（dat のオフセット -64,-32）で (128, 128)。
出力はすべて「理想の位置（線がタイルの辺の中点を通る位置）からのずれ」を画面の px で表す（正: 直線と横向きの斜めは下、縦向きの斜めは右）。
- 不透明: 透明でない画素全部（道床・車道など）の重心のずれ
- 暗い: 明るさ 70 未満の画素（レールの影・溝など）の重心のずれ
- 断面（直線のみ）: 線に沿った 20 列で、理想の線から上下 k px の行の明るさの平均。レール上面は明るく、側面は暗い。
  二つの絵でレールの行が同じなら、レールは画面で同じ位置にある（重心は道床の幅・陰で 1〜2px 動くので、こちらで比べる）
透明は #E7FFFF か、アルファ 0.5 未満。
"""
import os
import sys

import bpy
import numpy as np

TRANSPARENT = (231, 255, 255)
DARK = 70
# 理想の線: 直線は y - cy = ±(x - cx)/2 、縦向きの斜めは x = cx ∓ 32、横向きの斜めは y = cy ∓ 16
CENTER = {128: (64, 96), 256: (128, 128)}
KINDS = ("ew", "ns", "sw", "ne", "nw", "se")


def load(path):
    img = bpy.data.images.load(os.path.abspath(path), check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    return np.flipud(px.reshape(h, w, 4))


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    sheet = load(args[0])
    C = int(args[1])
    cx, cy = CENTER[C]
    yy, xx = np.mgrid[0:C, 0:C] + 0.5
    rgb = (sheet[..., :3] * 255 + 0.5).astype(int)
    for spec in args[2:]:
        kind, rc = spec.split("=")
        assert kind in KINDS, kind
        r, c = (int(v) for v in rc.split("."))
        cl = rgb[r * C:(r + 1) * C, c * C:(c + 1) * C]
        alpha = sheet[r * C:(r + 1) * C, c * C:(c + 1) * C, 3]
        opaque = np.any(cl != TRANSPARENT, axis=-1) & (alpha >= 0.5)
        dark = opaque & (cl.mean(-1) < DARK)
        if kind == "ew":
            off = yy - cy - (xx - cx) / 2
        elif kind == "ns":
            off = yy - cy + (xx - cx) / 2
        elif kind in ("sw", "ne"):
            off = xx - (cx - 32 if kind == "sw" else cx + 32)
        else:
            off = yy - (cy - 16 if kind == "nw" else cy + 16)
        line = f"[{kind} {r}.{c}]"
        for name, m in (("不透明", opaque), ("暗い", dark)):
            line += f"  {name} {off[m].mean():+.2f}（{off[m].min():+.1f}〜{off[m].max():+.1f}, {int(m.sum())}px）" if m.any() else f"  {name} なし"
        print(line)
        if kind in ("ew", "ns"):
            sgn = 1 if kind == "ew" else -1
            prof = []
            for k in range(-12, 13):
                vals = []
                for x in range(int(cx) - 20, int(cx) + 20, 2):
                    y = int(np.floor(cy + sgn * (x + 0.5 - cx) / 2 + k))
                    if opaque[y, x]:
                        vals.append(cl[y, x].mean())
                prof.append(f"{k:+d}:{np.mean(vals):.0f}" if vals else f"{k:+d}:-")
            print("   断面 " + " ".join(prof))


main()
