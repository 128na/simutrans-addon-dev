"""アドオンのシートを数値で検査する（dat が参照するセルが対象。アイコン・カーソルは除く）。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python ../../tools/blender/sheet_audit.py -- . [--compare 種類A 種類B] [--skip-holes 正規表現]

    例: blender ... -- . --compare ami_rail_ballast ami_rail_slab --skip-holes "_catenary$"

見るもの:
- 参照先のセルが空・シートの外（手前・奥の絵は空でよい）
- セルの端に絵が届いている（切れている）
- 透過色に近い色（白は除く）
- 囲まれた小さな穴・本体から離れた小さな点
- 直線のセルを 3 枚つないだときのすき間（線の絵のように、もともと穴が多い絵は --skip-holes で外す）
- --compare: 同じ作りのはずの 2 種類（名前の頭だけ違うシート。接尾辞の無い通常の版は除く）で、塗りの範囲が違うセル

出力の最後の行が [audit] OK か NG。穴・点は候補なので、拡大して確かめる。
"""
import argparse
import glob
import os
import re
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheetlib import CELL, TRANSPARENT  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("addon")
ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
ap.add_argument("--skip-holes", default=None)
args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])

KEY = np.array(TRANSPARENT, np.int32)
NEAR_KEY = 24             # 透過色との差（RGB の差の合計）がこれ以下なら「近い」
WHITE_R = 245             # 赤がこれ以上の色は白線などとして透過色に近いと数えない
SMALL_HOLE = 40           # これ以下の穴を報告する（画素）
SMALL_SPECK = 12          # これ以下の離れた点を報告する（画素）
COVER_TOL = 16            # --compare で、セルごとに許す塗りの差（画素。行き止まりの細部の違いを無視する）
STEP = {"ew": (64, 32), "ns": (-64, 32)}  # タイル 1 枚分の画面のずれ（pak128）
N4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
N8 = N4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))
LINE = re.compile(r"^[ \t]*([^#=\s][^=\n]*?)[ \t]*=[ \t]*(.*?)[ \t]*$", re.M)
IMAGE_KEY = re.compile(r"^(?:front|back)?(?:image(?:up)?2?|diagonal|pillar2?|ramp2?|start2?)(?:\[|$)", re.I)
# makeobj の書式: [> ]ファイル名[[[[.行].列],x],y]（descriptor/writer/image_writer.cc）。列を省くと、行の値は左上からの通し番号
IMAGE_REF = re.compile(r"^>?\s*((?:[^/]*/)*[^./]+)\.(\d+)(?:\.(\d+))?\s*(?:,|$)")
STRAIGHT = re.compile(r"^(front|back)?image\[(ew|ns)\](?:\[[01]\])?$", re.I)

root = os.path.abspath(args.addon)
sheets = {}


def sheet(name):
    if name not in sheets:
        img = bpy.data.images.load(os.path.join(root, "src", name + ".png"), check_existing=False)
        img.colorspace_settings.name = "Non-Color"
        w, h = img.size
        px = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        sheets[name] = np.rint(np.flipud(px.reshape(h, w, 4))[..., :3] * 255).astype(np.uint8)
    return sheets[name]


def key_distance(a):
    return np.abs(a.astype(np.int32) - KEY).sum(axis=2)


def opaque(a):
    return key_distance(a) > 0


def groups(mask, near):
    """mask の連結成分ごとに (画素の並び, 配列の端に触れたか) を返す。"""
    h, w = mask.shape
    seen = np.zeros_like(mask)
    out = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        seen[y0, x0] = True
        stack, pts, edge = [(int(y0), int(x0))], [], False
        while stack:
            y, x = stack.pop()
            pts.append((y, x))
            for dy, dx in near:
                a, b = y + dy, x + dx
                if not (0 <= a < h and 0 <= b < w):
                    edge = True
                elif mask[a, b] and not seen[a, b]:
                    seen[a, b] = True
                    stack.append((a, b))
        out.append((pts, edge))
    return out


def crop(mask):
    ys, xs = np.nonzero(mask)
    y0, x0 = max(ys.min() - 1, 0), max(xs.min() - 1, 0)
    return mask[y0:ys.max() + 2, x0:xs.max() + 2], y0, x0


def check_cell(cell, holes):
    op = opaque(cell)
    if not op.any():
        return None
    found_here = []
    edge = int(op[0].sum() + op[-1].sum() + op[:, 0].sum() + op[:, -1].sum())
    if edge:
        found_here.append(f"edge={edge}")
    d = key_distance(cell)
    near = int(((d > 0) & (d <= NEAR_KEY) & (cell[..., 0] < WHITE_R)).sum())
    if near:
        found_here.append(f"near_key={near}")
    box, y0, x0 = crop(op)
    if holes:
        small = [(len(p), p[0][1] + x0, p[0][0] + y0) for p, e in groups(~box, N4) if not e and len(p) <= SMALL_HOLE]
        if small:
            found_here.append(f"holes(px,x,y)={sorted(small, reverse=True)[:4]}")
    parts = sorted(((len(p), p[0][1] + x0, p[0][0] + y0) for p, _ in groups(box, N8)), reverse=True)
    specks = [s for s in parts[1:] if s[0] <= SMALL_SPECK]
    if specks:
        found_here.append(f"specks(px,x,y)={specks[:4]}")
    return found_here


def paste_gaps(cell, way):
    sx, sy = STEP[way]
    h, w = cell.shape[:2]
    can = np.zeros((h + 2 * abs(sy), w + 2 * abs(sx)), bool)
    op = opaque(cell)
    for i in range(3):
        px, py = (0 if sx > 0 else 2 * abs(sx)) + sx * i, sy * i
        can[py:py + h, px:px + w] |= op
    box, _, _ = crop(can)
    return sorted((len(p) for p, e in groups(~box, N4) if not e), reverse=True)[:3]


problems = 0
cells_seen = 0
for dat in sorted(glob.glob(os.path.join(root, "src", "*.dat"))):
    name = os.path.splitext(os.path.basename(dat))[0]
    holes = not (args.skip_holes and re.search(args.skip_holes, name))
    seen = {}
    lines = []
    for key, value in LINE.findall(open(dat, encoding="utf8", errors="replace").read()):
        low = key.lower()
        if not IMAGE_KEY.match(low) or value in ("", "-"):
            continue
        ref = IMAGE_REF.match(value)
        if not ref:
            lines.append(f"{key}: 画像の参照を読めない（{value}）")
            continue
        fn, r, c = ref.groups()
        if not os.path.exists(os.path.join(root, "src", fn + ".png")):
            lines.append(f"{key}: {fn}.png が無い")
            continue
        a, r = sheet(fn), int(r)
        if c is None:
            r, c = r // (a.shape[0] // CELL), r % (a.shape[1] // CELL)  # makeobj と同じ計算
        c = int(c)
        if (r + 1) * CELL > a.shape[0] or (c + 1) * CELL > a.shape[1]:
            lines.append(f"{key}: {fn}.{r}.{c} はシートの外")
            continue
        cell = a[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]
        if (fn, r, c) not in seen:
            seen[(fn, r, c)] = check_cell(cell, holes)
            found_here = seen[(fn, r, c)]
            if found_here:
                lines.append(f"{r}.{c} {key}: " + " ".join(found_here))
        if seen[(fn, r, c)] is None:
            if not low.startswith(("front", "back")):
                lines.append(f"{key}: {r}.{c} は空のセル")
            continue
        m = STRAIGHT.match(key)
        if m and holes:
            gaps = paste_gaps(cell, m.group(2).lower())
            if gaps:
                lines.append(f"{key}: つないだときのすき間 {gaps}")
    cells_seen += len(seen)
    problems += len(lines)
    for line in lines:
        print(f"[audit] {name} {line}")

if args.compare:
    a, b = args.compare
    for path in sorted(glob.glob(os.path.join(root, "src", a + "_*.png"))):
        na = os.path.splitext(os.path.basename(path))[0]
        nb = b + na[len(a):]
        if not os.path.exists(os.path.join(root, "src", nb + ".png")):
            continue
        oa, ob = opaque(sheet(na)), opaque(sheet(nb))
        if oa.shape != ob.shape:
            problems += 1
            print(f"[audit] compare {nb}: シートの大きさが違う {oa.shape[1::-1]} / {ob.shape[1::-1]}")
            continue
        for r in range(oa.shape[0] // CELL):
            for c in range(oa.shape[1] // CELL):
                y, x = r * CELL, c * CELL
                ca, cb = oa[y:y + CELL, x:x + CELL], ob[y:y + CELL, x:x + CELL]
                only_a, only_b = int((ca & ~cb).sum()), int((cb & ~ca).sum())
                if max(only_a, only_b) > COVER_TOL:
                    problems += 1
                    print(f"[audit] compare {nb} {r}.{c}: {a} だけ {only_a}px / {b} だけ {only_b}px")

print(f"[audit] {'OK' if not problems else 'NG'} セル {cells_seen} 候補 {problems}")
