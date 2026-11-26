"""道路のカーブのセルと、隣の直線のセルをつないだときの、タイルの辺のすき間の検査（#378）。check.sh が呼ぶ。Pillow と numpy を使う。

    python -X utf8 check_curve_join.py [src のディレクトリ]
    python -X utf8 check_curve_join.py --self-test
    SHEET_PAK_SIZE=256 python -X utf8 check_curve_join.py   # 256 のシート（src256/）
    CHECK_SKIP_MISSING=1 ...                                 # dat の指すシートが無い物は飛ばす（256 の CI。PNG は生活道路だけ）

生活道路の L 字のカーブ（sheetlib の MiterPath）の削る形が角を越えてもう一方の脚の路面を削り、雪の絵で路面の板を内へ寄せる（#360）と、
タイルの辺に沿って 1 画素の帯が透け、256 で角のタイルと隣の直線のタイルの境に地面の色の点線が出た（#378）。
数え方: 道路の dat（ami_road_*.dat）ごとに、温帯と雪（image[..][0]・[1]）のカーブ 4 つ（sw・nw・ne・se）を、つながる 2 方向の隣に
直線（ns・ew）を置いてゲームと同じ並びに重ね、透明で、左右か上下の両隣が塗られた画素を数える。タイルの菱形の頂点の近く
（VERTEX_R × 倍率の画素）は数えない（3 枚の角が寄る所で、直す前から 1〜2 画素ある。路面の外）。1 つのつなぎで MIN_HOLES 画素以上あれば失敗にする。
直す前は、生活道路の base_single の雪で 128 は 6 画素（sw・se が各 3。しきい値の余裕は無い）、256 は 85 画素だった。
セルはどれも dat の位置合わせ（offset）が同じとみなして重ねる（AMI の道路の dat は全部同じ値。違うセルが混ざったら読むように直す）。
"""
import os
import re
import sys

import numpy as np
from PIL import Image

from check_lib import CELL, SCALE, SRC, TRANSPARENT

KEY = re.compile(r"^image\[(ns|ew|sw|nw|ne|se)\]\[([01])\]=([a-z0-9_]+)\.(\d+)\.(\d+),(-?\d+),(-?\d+)", re.M)
CURVES = ("sw", "nw", "ne", "se")
VERTEX_R = 6  # pak128 での画素
MIN_HOLES = 3  # 1 つのつなぎでこれ以上なら失敗（点線。直す前は 128 で 3、256 で 14〜28。高架などに、頂点から少し離れた 1〜2 画素の点が直す前からある）
W = CELL // 2  # タイルの幅（画面。pak128 は 128）


def step(d):
    """隣のタイルの画面のずれ（北 = 右上、東 = 右下、南 = 左下、西 = 左上）"""
    return {"n": (W // 2, -W // 4), "e": (W // 2, W // 4), "s": (-W // 2, W // 4), "w": (-W // 2, -W // 4)}[d]


def holes(layers):
    """layers: [(セルの RGBA の配列, x, y)] を重ねたときの、すき間の画素（頂点の近くを除く）の座標（最初の層のセルの座標）"""
    canvas = np.zeros((CELL * 3, CELL * 3), bool)
    for a, x, y in layers:
        canvas[CELL + y:CELL * 2 + y, CELL + x:CELL * 2 + x] |= a
    t, o = ~canvas, canvas
    h = t[1:-1, 1:-1] & ((o[1:-1, :-2] & o[1:-1, 2:]) | (o[:-2, 1:-1] & o[2:, 1:-1]))
    ys, xs = np.nonzero(h)
    xs, ys = xs + 1 - CELL, ys + 1 - CELL
    c = CELL / 2
    verts = [(c - W / 2, c), (c + W / 2, c), (c, c - W / 4), (c, c + W / 4)]
    r = VERTEX_R * SCALE
    keep = [all((x - vx) ** 2 + (y - vy) ** 2 > r * r for vx, vy in verts) for x, y in zip(xs, ys)]
    return [(int(x), int(y)) for x, y, k in zip(xs, ys, keep) if k]


def main(src):
    skip = bool(os.environ.get("CHECK_SKIP_MISSING"))
    errors, checked = [], 0
    sheets = {}
    for dat in sorted(f for f in os.listdir(src) if f.startswith("ami_road_") and f.endswith(".dat")):
        with open(os.path.join(src, dat), encoding="utf-8", errors="replace") as f:
            text = f.read()
        cells = {}
        for k, season, sheet, r, c, _, _ in KEY.findall(text):
            cells[(k, int(season))] = (sheet, int(r), int(c))
        for season in (0, 1):
            if not all((k, season) in cells for k in CURVES + ("ns", "ew")):
                continue
            missing = [s for s in {v[0] for (k, se), v in cells.items() if se == season}
                       if not os.path.isfile(os.path.join(src, s + ".png"))]
            if missing:
                if not skip:
                    errors.append(f"{dat}: シートが無い {missing}")
                continue
            for s in {v[0] for (k, se), v in cells.items() if se == season}:
                if s not in sheets:
                    with Image.open(os.path.join(src, s + ".png")) as im:
                        a = np.asarray(im.convert("RGBA"))
                    sheets[s] = (a[..., 3] > 0) & ~np.all(a[..., :3] == TRANSPARENT, axis=2)

            def cell(k):
                s, r, c = cells[(k, season)]
                return sheets[s][r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
            checked += 1
            for cv in CURVES:
                layers = [(cell(cv), 0, 0)] + [(cell("ns" if d in "ns" else "ew"), *step(d)) for d in cv]
                hs = holes(layers)
                if len(hs) >= MIN_HOLES:
                    errors.append(f"{dat}: {'雪' if season else '温帯'}のカーブ {cv} と隣の直線の境に、透ける画素が {len(hs)}"
                                  f"（カーブのセルの座標 {hs[:6]}。#378）")
    print(f"check_curve_join: {src}（セル {CELL}px）: 道路の dat の季節 {checked} 組")
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1
    return 0


def self_test():
    """菱形のタイルを塗ったセルで、つないだときにすき間が無いこと、辺に 1 画素の帯を空けると数えること、頂点を数えないことを確かめる"""
    yy, xx = np.mgrid[0:CELL, 0:CELL]
    c = CELL / 2
    tile = np.abs(xx + 0.5 - c) / (W / 2) + np.abs(yy + 0.5 - c) / (W / 4) <= 1.02
    assert not holes([(tile, 0, 0), (tile, *step("s")), (tile, *step("w"))]), holes([(tile, 0, 0), (tile, *step("s"))])
    cut = tile.copy()
    # 西の辺（左の頂点から上の頂点へ）の中ほどの内側 1 画素を空ける
    edge = np.abs(xx + 0.5 - c) / (W / 2) + np.abs(yy + 0.5 - c) / (W / 4)
    band = (edge > 0.97) & (edge <= 1.02) & (xx < c) & (yy < c) & (np.abs(xx - (c - W / 4)) < W / 16)
    cut[band] = False
    assert holes([(cut, 0, 0), (tile, *step("w"))]), "辺の帯を数えない"
    print("check_curve_join: self-test OK")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sys.exit(main(args[0] if args else SRC))
