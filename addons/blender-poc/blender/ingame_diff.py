"""ゲーム画面と、シートのセルを同じ位置・順番で貼った「予想図」を比べ、違う画素に印を付ける。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/ingame_diff.py -- 画面.png シート名 タイル一覧.txt 出力.png x,y（jump したタイル）

タイル一覧は ingame/tiles.nut で書き出す（1行に x y z 坂 向き）。画面は等倍（gui.set_zoom(3)）で撮る。
予想図は画面の地面の上にセルを貼ったもの。セルの透明な画素は画面のまま残す。
- 位置合わせ: 中心に近いカーブ・行き止まり・分岐のタイルを画面の中から探し、ほかのタイルは Simutrans と同じ式で並べる
- 曲がり（向きが隣り合う2方向）は、カーブの絵と斜めの絵のうち合うほうを使う（どちらになるかは本体が決める）
出力は 左 画面、中 予想図、右 違う画素（明るさの差の合計が THRESH 以上）を紫にしたもの。違う画素の数も出す。
"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose import IMG, IMG_EXPWY, load  # noqa: E402
from render import CELL, TRANSPARENT  # noqa: E402

THRESH = 40
BITS = {"n": 1, "e": 2, "s": 4, "w": 8}
ORDER = "nsew"
# 坂の番号（pak の1段の坂）→ セル。坂の上る向きは compose.slope_cross と同じ
SLOPE_KEY = {4: "up3", 36: "up12", 12: "up6", 28: "up9"}
CURVES = {"sw", "nw", "ne", "se"}


def key_of(dirs):
    s = "".join(c for c in ORDER if dirs & BITS[c])
    # IMG のキーは ns, ew と曲がり（sw など）と分岐（nse など）
    return {"ne": "ne", "nw": "nw", "se": "se", "sw": "sw", "ew": "ew", "ns": "ns"}.get(s, s)


def candidates(slope, dirs, img):
    if slope:
        return [SLOPE_KEY[slope]] if slope in SLOPE_KEY else []
    k = key_of(dirs)
    if k not in img:
        return []
    if k in CURVES:
        return [k, "d" + k]
    return [k]


def cell(sheet, img, key):
    r, c = img[key]
    return sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL]


def paste(out, cl, x, y):
    m = np.any(cl != TRANSPARENT, axis=-1)
    h, w = out.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + CELL, w), min(y + CELL, h)
    if x0 >= x1 or y0 >= y1:
        return
    sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
    out[y0:y1, x0:x1][sub] = cl[y0 - y:y1 - y, x0 - x:x1 - x][sub]


def locate(game, cl, guess, rng=80):
    """セル cl の不透明な内側（縁を2px 除く）が画面といちばん合う左上の位置。"""
    m = np.any(cl != TRANSPARENT, axis=-1)
    mm = m.copy()
    for s in (1, 2):
        mm &= np.roll(m, s, 0) & np.roll(m, -s, 0) & np.roll(m, s, 1) & np.roll(m, -s, 1)
    ys, xs = np.nonzero(mm)
    cl = cl.astype(int)
    best = None
    for dy in range(-rng, rng + 1):
        for dx in range(-rng, rng + 1):
            X, Y = guess[0] + dx, guess[1] + dy
            gy, gx = ys + Y, xs + X
            ok = (gy >= 0) & (gy < game.shape[0]) & (gx >= 0) & (gx < game.shape[1])
            if ok.mean() < 0.9:
                continue
            d = np.abs(game[gy[ok], gx[ok]] - cl[ys[ok], xs[ok]]).mean()
            if best is None or d < best[0]:
                best = (d, X, Y)
    return best


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    shot, name, tiles_path, out_path = args[:4]
    # 撮る前に gui.jump で画面の中央へ動かしたタイル。位置合わせの見当に使う
    jx, jy = (int(v) for v in args[4].split(","))
    game = load(shot).astype(int)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sheet = load(os.path.join(root, "src", name + ".png"))
    img = IMG_EXPWY if name == "expressway" else IMG
    tiles = []
    for line in open(tiles_path, encoding="utf8"):
        p = line.split()
        if len(p) == 5:
            tiles.append(tuple(int(v) for v in p))
    tiles = [(x, y, z, sl, d, candidates(sl, d, img)) for x, y, z, sl, d in tiles]
    tiles = [t for t in tiles if t[5]]
    # 位置合わせ: 形が一つに決まるタイル（カーブ・行き止まり・分岐）。直線は道に沿ってずらしても合ってしまう
    H, W = game.shape[:2]
    xs = [t[0] for t in tiles]
    ys = [t[1] for t in tiles]
    cx, cy = jx, jy
    distinct = [t for t in tiles if t[5][0] not in ("ns", "ew") and not t[3]] or tiles
    ref = min(distinct, key=lambda t: abs(t[0] - cx) + abs(t[1] - cy))
    # 画面のどこにあるかの見当: 一覧の中心のタイルが画面の中央
    # 等倍の 704x560 の画面では、jump したタイルのセルの左上がおよそ (192, 256) に来る
    gx = 192 + ((ref[0] - cx) - (ref[1] - cy)) * 64
    gy = 256 + ((ref[0] - cx) + (ref[1] - cy)) * 32 - ref[2] * 16
    # 曲がりはカーブと斜めのどちらの絵か分からないので、両方で探して合うほう
    if os.environ.get("INGAME_LOCATE"):
        # 位置を直接与える（線路のように模様がくり返すと、道に沿ってずれた所で合ってしまうことがある）
        X, Y = (int(v) for v in os.environ["INGAME_LOCATE"].split(","))
        d = 0.0
    else:
        d, X, Y = min(locate(game, cell(sheet, img, k), (gx, gy), rng=40) for k in ref[5])
    print(f"[locate] ref {ref[:2]} {ref[5][0]} at {X},{Y} (err {d:.1f})")

    def pos(t):
        return (X + ((t[0] - ref[0]) - (t[1] - ref[1])) * 64,
                Y + ((t[0] - ref[0]) + (t[1] - ref[1])) * 32 - (t[2] - ref[2]) * 16)

    pred = game.copy()
    covered = np.zeros(game.shape[:2], bool)
    for t in sorted(tiles, key=lambda t: (t[0] + t[1], t[2])):
        x, y = pos(t)
        keys = t[5]
        if len(keys) > 1:
            # 曲がり: タイルの範囲で画面に合うほうを選ぶ
            scores = []
            for k in keys:
                trial = pred.copy()
                paste(trial, cell(sheet, img, k), x, y)
                y0, y1 = max(y + 64, 0), min(y + 192, H)
                x0, x1 = max(x + 64, 0), min(x + 192, W)
                scores.append(np.abs(trial[y0:y1, x0:x1] - game[y0:y1, x0:x1]).sum() if y0 < y1 and x0 < x1 else 0)
            keys = [keys[int(np.argmin(scores))]]
        paste(pred, cell(sheet, img, keys[0]).astype(int), x, y)
        cov = np.zeros_like(covered)
        paste_mask = np.any(cell(sheet, img, keys[0]) != TRANSPARENT, axis=-1)
        y0, y1, x0, x1 = max(y, 0), min(y + CELL, H), max(x, 0), min(x + CELL, W)
        if y0 < y1 and x0 < x1:
            covered[y0:y1, x0:x1] |= paste_mask[y0 - y:y1 - y, x0 - x:x1 - x]
        del cov
    diff = np.abs(game - pred).sum(-1) >= THRESH
    # 画面の上下の帯（ツールバー・状態表示）と、その近くは除く（端で切れたタイルは、カーブと斜めの絵の選び分けを誤る）
    diff[:56] = False
    diff[-48:] = False
    diff[:, :16] = False
    diff[:, -16:] = False
    print(f"[diff] {name}: {int(diff.sum())} px")
    # 形の欠け・出っ張り: 上下左右の4画素のうち3つ以上と、自分の覆われ方が違う画素
    c = covered.astype(int)
    nb = np.zeros_like(c)
    nb[1:] += c[:-1]
    nb[:-1] += c[1:]
    nb[:, 1:] += c[:, :-1]
    nb[:, :-1] += c[:, 1:]
    inner = np.zeros_like(covered)
    inner[56:-48, 16:-16] = True
    notch = ~covered & (nb >= 3) & inner
    bump = covered & (nb <= 1) & inner
    ny, nx = np.nonzero(notch)
    by, bx = np.nonzero(bump)
    print(f"[shape] {name}: notch {len(ny)} {list(zip(nx.tolist(), ny.tolist()))[:12]} bump {len(by)} {list(zip(bx.tolist(), by.tolist()))[:12]}")
    vis = np.concatenate([game, pred, np.where(diff[..., None], [255, 0, 255], game)], 1).astype(np.uint8)
    h, w, _ = vis.shape
    o = bpy.data.images.new("o", w, h)
    rgba = np.concatenate([vis, np.full((h, w, 1), 255, np.uint8)], 2)
    o.pixels.foreach_set((np.flipud(rgba).astype(np.float32) / 255).ravel())
    o.filepath_raw = os.path.abspath(out_path)
    o.file_format = "PNG"
    o.save()
    # 違う画素について、その画素を含むタイルのセルと、セルの中の位置・不透明か（INGAME_DIFF_DEBUG=1 のとき）
    if os.environ.get("INGAME_DIFF_DEBUG"):
        ys_, xs_ = np.nonzero(diff)
        for y, x in list(zip(ys_, xs_))[:int(os.environ.get("INGAME_DIFF_DEBUG"))]:
            info = []
            for t in tiles:
                tx, ty = pos(t)
                if tx <= x < tx + CELL and ty <= y < ty + CELL:
                    for k in t[5]:
                        cl = cell(sheet, img, k)
                        if np.any(cl[y - ty, x - tx] != TRANSPARENT):
                            info.append(f"{t[:3]}{k}@{x - tx},{y - ty}")
            print(f"[px] {x},{y} game {tuple(game[y, x])} pred {tuple(pred[y, x])} opaque in: {info}")
    # 指定した画素を、どのタイルの菱形が持ち、どのセルが不透明か（INGAME_PROBE="x,y x,y"）
    for spec in os.environ.get("INGAME_PROBE", "").split():
        x, y = (int(v) for v in spec.split(","))
        info = []
        for t in tiles:
            tx, ty = pos(t)
            if tx <= x < tx + CELL and ty <= y < ty + CELL:
                for k in t[5]:
                    cl = cell(sheet, img, k)
                    info.append(f"{t[:3]}{k}@{x - tx},{y - ty}:{'opaque' if np.any(cl[y - ty, x - tx] != TRANSPARENT) else 'clear'}")
        print(f"[probe] {x},{y} game {tuple(game[y, x])} cells: {info}")
    # 違う画素の場所（タイルごと）
    if diff.any():
        hits = {}
        for t in tiles:
            x, y = pos(t)
            y0, y1 = max(y + 64, 0), min(y + 192, H)
            x0, x1 = max(x + 64, 0), min(x + 192, W)
            if y0 < y1 and x0 < x1:
                n = int(diff[y0:y1, x0:x1].sum())
                if n:
                    hits[t[:2]] = n
        print("[diff] tiles:", sorted(hits.items(), key=lambda kv: -kv[1])[:12])


if __name__ == "__main__":
    main()
