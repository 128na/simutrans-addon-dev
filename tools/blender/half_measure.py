"""1/2 の画面の粒を、ゲームを使わずにシートから測る（AMI #89）。

本体は 1/2 の画面の絵を、タイルの原点（偶数の座標）にそろえた 2×2 の単純平均で作る（`display/simgraph16.cc` の `rezoom_img`）。
シートのセルの原点はタイルの原点と偶奇が同じ（AMI は 256px のセルで dat の位置合わせ -64,-32、pak128 は 128px のセルで 0,0）なので、
セルの原点から 2×2 で平均すれば、ゲームの 1/2 の絵になる。区切りを 1px ずらすと値が大きく変わる（孤立点が 2〜125）ので、ずらさない。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python ../../tools/blender/half_measure.py -- セルの大きさ 前.png 後.png

2 枚のシートの空でないセルごとに、等倍と 1/2 の値を並べる（測り方は busy_measure.py と同じ。孤立点は way の画素 1000 あたり）:
    等倍  細かさ / 孤立点（どちらも線を除く。くどさの物差し docs/reference/way-addon.md の 11 章）
    1/2   孤立点（線を除く）と、孤立点（線を含む）
1/2 の孤立点が 15 以上増えたか、等倍の細かさが 0.01 以上動いたセルに「<<」を付ける。最後に、1/2 の画素の数で重みを付けた合計を出す。
規則正しい模様（間隔をそろえたまくらぎ）は、1/2 で「1 つおきの点線」になり、線として除かれる。粒が減ったのか線に移っただけかは、
線を含む値も見て決める。ゲームの画面での確かめは ingame/calib_capture.sh と busy_measure.py の BUSY_BYZOOM で行う。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from busy_measure import erode, fineness, isolated, isolated_excl, line_mask, load, lum  # noqa: E402

KEY = np.array([231, 255, 255], np.float32) / 255  # 透明色


def measure(rgb):
    valid = np.abs(rgb - KEY).max(-1) > 0.02
    if valid.sum() < 200:
        return None
    L = lum(rgb)
    m = erode(valid)
    x = line_mask(L, m)
    h, w = rgb.shape[:2]
    v4 = valid.reshape(h // 2, 2, w // 2, 2)
    c4 = rgb.reshape(h // 2, 2, w // 2, 2, 3)
    cnt = v4.sum((1, 3))
    half = (c4 * v4[..., None]).sum((1, 3)) / np.maximum(cnt, 1)[..., None]  # 本体と同じく、透明でない画素だけを平均する
    Lh = lum(half)
    mh = erode(cnt == 4)
    xh = line_mask(Lh, mh)
    return fineness(L, m & ~x), isolated_excl(L, m, x), isolated_excl(Lh, mh, xh), isolated(Lh, mh), int(mh.sum())


def main():
    a = sys.argv[sys.argv.index("--") + 1:]
    cp = int(a[0])
    A, Bs = load(a[1]), load(a[2])
    rows, cols = A.shape[0] // cp, A.shape[1] // cp
    tot = [[0.0, 0.0, 0], [0.0, 0.0, 0]]
    print("| セル | 等倍 前 | 等倍 後 | 1/2 線を除く 前 → 後 | 1/2 線を含む 前 → 後 | |")
    print("|---|---|---|---|---|---|")
    for r in range(rows):
        for c in range(cols):
            cell = (slice(r * cp, (r + 1) * cp), slice(c * cp, (c + 1) * cp))
            ra, rb = measure(A[cell]), measure(Bs[cell])
            if ra is None or rb is None:
                continue
            flag = "<<" if rb[2] > ra[2] + 15 or abs(rb[0] - ra[0]) > 0.01 else ""
            print(f"| {r}.{c} | {ra[0]:.4f}/{ra[1]:.1f} | {rb[0]:.4f}/{rb[1]:.1f} | {ra[2]:.1f} → {rb[2]:.1f} | "
                  f"{ra[3]:.1f} → {rb[3]:.1f} | {flag} |")
            for t, v in zip(tot, (ra, rb)):
                t[0] += v[2] * v[4]
                t[1] += v[3] * v[4]
                t[2] += v[4]
    print(f"\n合計（1/2 の画素で重み付け）: 線を除く {tot[0][0] / tot[0][2]:.1f} → {tot[1][0] / tot[1][2]:.1f}、"
          f"線を含む {tot[0][1] / tot[0][2]:.1f} → {tot[1][1] / tot[1][2]:.1f}")


if __name__ == "__main__":
    main()
