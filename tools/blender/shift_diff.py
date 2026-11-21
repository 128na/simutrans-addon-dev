"""2 枚の画面を、片方をずらして比べ、物（背景と違う画素）の差を数える。高架の絵が地上の絵と同じかを確かめるのに使う
（高架は地上より 2 段上に描かれるので、同じ場所へ飛んで撮った画面では上へずれる。pak128 の等倍では 32px）。

使い方: blender -b --factory-startup --python ../../tools/blender/shift_diff.py -- 出力のフォルダ dx,dy 背景.png a1.png b1.png [a2.png b2.png ...]
    背景は、同じ倍率で何も無い所へ飛んで撮った画面（平らな草や雪は、どこへ飛んでも画面の同じ位置に同じ模様が出る）。
    b を (dx, dy) だけずらして a と比べる（b の (x - dx, y - dy) を a の (x, y) と比べる）。dy が正なら b の絵が a より上にある。
    物の画素は、背景と RGB のどれかが 0.02 を超えて違う画素。差は、片方だけに物がある画素と、両方に物があって色が 0.06 を超えて違う画素。
    ずらす前の a と b の同じ位置に同じ物がある画素（地面に立つ名札など。高架と一緒に動かない物）は、ずらす前とずらした後の両方の位置で数えない。
    組ごとに「[diff] <b の名前> <差の画素の数> fixed=<比べる範囲で外した画素の数>」を出し、差の画素を赤にした a を <出力のフォルダ>/<b の名前> に書く。
    比べる範囲は画面の上のツールバーと下の状態行を除いた x 20〜680・y 80〜440（704x560 の画面）。dx は -20〜20、dy は -80〜80 の内にする（比べる範囲が画面の外に出ないように）
    出力の名前は b のファイル名なので、同じ名前の b を別のフォルダから渡すと上書きになる
"""
import os
import sys

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
out_dir = a[0]
dx, dy = map(int, a[1].split(","))
pairs = a[3:]
X0, X1, Y0, Y1 = 20, 680, 80, 440
os.makedirs(out_dir, exist_ok=True)


def load(p):
    i = bpy.data.images.load(os.path.abspath(p), check_existing=False)
    w, h = i.size
    return np.array(i.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]


def differs(x, y, thr):
    return np.abs(x - y).max(axis=2) > thr


BG = load(a[2])
for k in range(0, len(pairs), 2):
    A, B = load(pairs[k]), load(pairs[k + 1])
    obj_a = differs(A, BG, 0.02)
    obj_b = differs(B, BG, 0.02)
    fixed = obj_a & obj_b & ~differs(A, B, 0.02)
    sl_a = (slice(Y0, Y1), slice(X0, X1))
    sl_b = (slice(Y0 - dy, Y1 - dy), slice(X0 - dx, X1 - dx))
    sa, sb = A[sl_a], B[sl_b]
    oa, ob = obj_a[sl_a], obj_b[sl_b]
    d = (oa ^ ob) | (oa & ob & differs(sa, sb, 0.06))
    ex = fixed[sl_a] | fixed[sl_b]
    d &= ~ex
    name = os.path.basename(pairs[k + 1])
    print("[diff] %s %d fixed=%d" % (name, int(d.sum()), int(ex.sum())))
    img = sa * 0.5
    img[d] = [1, 0, 0]
    h, w = img.shape[:2]
    o = bpy.data.images.new("o", w, h)
    o.pixels[:] = np.concatenate([img, np.ones((h, w, 1), np.float32)], axis=2)[::-1].ravel()
    o.filepath_raw = os.path.abspath(os.path.join(out_dir, name))
    o.file_format = "PNG"
    o.save()
