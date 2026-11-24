"""前後の撮影（ingame/before_after.sh の PAKDIR_BEFORE・PAKDIR_AFTER）を横に並べる（#227）。

使い方: python -X utf8 ingame/ba_pairs.py <OUT> [--spots spots.txt] [--scale 6]
OUT/before/<名前>.png と OUT/after/<名前>.png の組ごとに、OUT/pairs/<名前>.png に「前 | 後」を並べて書く。
spots.txt（before_after.sh の SPOTS_FILE と同じ。1 行 1 か所）の行が「名前 x y cx0 cy0 cx1 cy1」なら、その名前は撮った画面の
(cx0,cy0)-(cx1,cy1)（画素。左上が原点）を切り抜き、最近傍で scale 倍にして並べる。切り抜きは差分から自動で探さず、座標で決める
（差分から探すと、片方が外れることがあった。#217）。切り抜きの無い名前は、画面全体を等倍で並べる。
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

LABEL_H = 14
GAP = 8


def read_crops(path):
    crops = {}
    if not path:
        return crops
    for line in open(path, encoding="utf-8"):
        f = line.split()
        if not f or f[0].startswith("#") or len(f) < 7:
            continue
        crops[f[0]] = tuple(int(v) for v in f[3:7])
    return crops


def read_names(path):
    """spots.txt の名前（# の行・空行を除く）"""
    if not path:
        return []
    return [f[0] for f in (ln.split() for ln in open(path, encoding="utf-8")) if f and not f[0].startswith("#")]


def pair(name, before, after, crop, scale):
    ims = []
    for im in (before, after):
        im = im.convert("RGB")
        if crop:
            im = im.crop(crop).resize(((crop[2] - crop[0]) * scale, (crop[3] - crop[1]) * scale), Image.NEAREST)
        ims.append(im)
    w = ims[0].width + ims[1].width + GAP
    h = max(ims[0].height, ims[1].height) + LABEL_H
    out = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(out)
    x = 0
    for label, im in zip(("before", "after"), ims):
        d.text((x + 2, 1), f"{name} {label}", fill=(0, 0, 0))
        out.paste(im, (x, LABEL_H))
        x += im.width + GAP
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--spots")
    ap.add_argument("--scale", type=int, default=6)
    a = ap.parse_args()
    crops = read_crops(a.spots)
    os.makedirs(os.path.join(a.out, "pairs"), exist_ok=True)
    have = {s: {f[:-4] for f in os.listdir(os.path.join(a.out, s)) if f.endswith(".png")} for s in ("before", "after")}
    # --spots に書いた名前は全部数える（撮れなかった物を黙って飛ばさない）
    names = sorted(have["before"] | have["after"] | set(read_names(a.spots)))
    bad = 0
    for n in names:
        gone = [s for s in ("before", "after") if n not in have[s]]
        if gone:
            print(f"[pairs] 警告: {n} の画像が無い（{', '.join(gone)}）", file=sys.stderr)
            bad += 1
            continue
        b, af = (os.path.join(a.out, s, n + ".png") for s in ("before", "after"))
        ib, ia = Image.open(b), Image.open(af)
        crop = crops.get(n)
        if crop and not (0 <= crop[0] < crop[2] <= min(ib.width, ia.width) and 0 <= crop[1] < crop[3] <= min(ib.height, ia.height)):
            print(f"[pairs] 警告: 切り抜きの座標が画像（{ib.width}×{ib.height}）の外: {n} {crop}", file=sys.stderr)
            bad += 1
            continue
        p = os.path.join(a.out, "pairs", n + ".png")
        pair(n, ib, ia, crop, a.scale).save(p)
        print(f"[pairs] {p}")
    return 1 if bad or not names else 0


if __name__ == "__main__":
    sys.exit(main())
