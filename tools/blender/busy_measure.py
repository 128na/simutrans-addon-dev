"""くどさの数値: 同じ場所を way を敷く前（bare）と後（way）で撮った画面から、way の画素だけを選んで測る（AMI の #56 の C）。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python ../../tools/blender/busy_measure.py -- 画像のフォルダ 出力.md [車両の画像 ...]

画像の名前は <気候>_<名前>_z<拡大率>_<bare|way>.png（ingame/calib_capture.sh が撮る）。拡大率 3 が等倍。
way の画素: bare と way の色の差が MASK_DIFF 以上の画素から、縁の 1px を削ったもの（草との境の明暗差を数えない）。
測るもの（どれも明るさ 0〜1 で、way の画素の中だけ）:
    細かさ   隣り合う画素（両方が way）の明るさの差の平均。等倍と、縮めた拡大率で出す
    つぶれ   ゲームが 1/2 に縮めた画面の細かさ ÷ 等倍の画面を 2x2 の平均で縮めた絵の細かさ。1 より大きいほど、縮めたときに
             模様が平均されずに残る（ちらつき・ざらつき）
    孤立点   周り 8 画素のどれとも ISO_DIFF 以上違い、周りの中央値と ISO_MED 以上違う画素の数（way の画素 1000 あたり）
    車両比   等倍の細かさ ÷ 車両の画像（pak128 の機関車など。背景色 #E7FFFF を除く）の細かさの中央値。1 に近いほど、
             way が車両と同じくらい目立つ
"""
import os
import re
import sys

import bpy
import numpy as np

MASK_DIFF = 0.06
ISO_DIFF = 0.06
ISO_MED = 0.10
CROP_TOP, CROP_BOTTOM = 60, 40  # 上のツールバーと下の状態行


def load(p):
    i = bpy.data.images.load(os.path.abspath(p))
    w, h = i.size
    x = np.empty(w * h * 4, np.float32)
    i.pixels.foreach_get(x)
    bpy.data.images.remove(i)
    return np.flipud(x.reshape(h, w, 4))[..., :3]


def lum(rgb):
    return rgb @ np.array([0.299, 0.587, 0.114], np.float32)


def erode(m):
    e = m.copy()
    e[1:, :] &= m[:-1, :]
    e[:-1, :] &= m[1:, :]
    e[:, 1:] &= m[:, :-1]
    e[:, :-1] &= m[:, 1:]
    e[0, :] = e[-1, :] = e[:, 0] = e[:, -1] = False
    return e


def fineness(L, m):
    dx = np.abs(np.diff(L, axis=1))[m[:, 1:] & m[:, :-1]]
    dy = np.abs(np.diff(L, axis=0))[m[1:, :] & m[:-1, :]]
    d = np.concatenate([dx, dy])
    return float(d.mean()) if d.size else float("nan")


def isolated(L, m):
    h, w = L.shape
    c = L[1:-1, 1:-1]
    nb = np.stack([L[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx])
    nm = np.stack([m[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]).all(0)
    inside = m[1:-1, 1:-1] & nm
    iso = inside & (np.abs(nb - c).min(0) >= ISO_DIFF) & (np.abs(np.median(nb, 0) - c) >= ISO_MED)
    n = int(inside.sum())
    return 1000.0 * iso.sum() / n if n else float("nan")


def box2(L, m):
    h, w = (L.shape[0] // 2) * 2, (L.shape[1] // 2) * 2
    L2 = L[:h, :w].reshape(h // 2, 2, w // 2, 2).mean((1, 3))
    m2 = m[:h, :w].reshape(h // 2, 2, w // 2, 2).all((1, 3))
    return L2, m2


def way_pixels(folder, season, name, z):
    b = load(os.path.join(folder, f"{season}_{name}_z{z}_bare.png"))
    w = load(os.path.join(folder, f"{season}_{name}_z{z}_way.png"))
    b, w = b[CROP_TOP:-CROP_BOTTOM], w[CROP_TOP:-CROP_BOTTOM]
    m = erode(np.abs(w - b).sum(-1) >= MASK_DIFF)
    return lum(w), m


def vehicle_fineness(paths):
    vals = []
    for p in paths:
        rgb = load(p)
        bg = (np.abs(rgb - np.array([231, 255, 255], np.float32) / 255).max(-1) < 0.02)
        vals.append(fineness(lum(rgb), erode(~bg)))
    return float(np.median(vals)) if vals else float("nan")


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    folder, out, vehicles = a[0], a[1], a[2:]
    pat = re.compile(r"^(\w+?)_(\w+)_z(\d+)_way\.png$")
    keys = {}
    for f in sorted(os.listdir(folder)):
        mt = pat.match(f)
        if mt:
            keys.setdefault((mt[1], mt[2]), set()).add(int(mt[3]))
    vf = vehicle_fineness(vehicles)
    lines = [f"車両の細かさ（中央値、{len(vehicles)} 枚）: {vf:.4f}", ""]
    head = "| 気候 | 名前 | way の画素 | 細かさ z3 | 細かさ z4 | 細かさ z6 | つぶれ | 孤立点/千 | 車両比 |"
    lines += [head, "|" + "---|" * 9]
    order = lambda k: (k[0] != "temperate", k[0], k[1])
    for season, name in sorted(keys, key=order):
        zs = keys[(season, name)]
        L3, m3 = way_pixels(folder, season, name, 3)
        f = {z: fineness(*way_pixels(folder, season, name, z)) for z in sorted(zs)}
        crush = f.get(6, float("nan")) / fineness(*box2(L3, m3))
        lines.append(f"| {season} | {name} | {int(m3.sum())} | {f.get(3, float('nan')):.4f} | {f.get(4, float('nan')):.4f} | "
                     f"{f.get(6, float('nan')):.4f} | {crush:.3f} | {isolated(L3, m3):.2f} | {f.get(3, float('nan')) / vf:.3f} |")
    text = "\n".join(lines) + "\n"
    with open(out, "w", encoding="utf8", newline="\n") as fo:
        fo.write(text)
    print(text)


main()
