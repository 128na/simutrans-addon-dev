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
    線       構造の線（レール・まくらぎの縁など）の画素の割合（%）。周り 5x5 の中央値と ISO_MED 以上違い、8 つの向きのどれかで、
             その向きの前後 2 画素ずつ（1 つおきの点線も含む）が自分と ISO_DIFF 未満の明るさの画素（LINE_RUN 画素以上まっすぐ続く）
    線を除く 細かさ・孤立点を、線の画素を除いて測った値。くどさの物差し（docs/reference/way-addon.md の 11 章）はこちらで判定する。
             レールの明暗のような構造の線を数えると、構造を描き足すほど「くどい」に寄った（2026-11-20。記録 2026-11-20_ami-busyness-recalibration.md）
    車両比   等倍の細かさ ÷ 車両の画像（pak128 の機関車など。背景色 #E7FFFF を除く）の細かさの中央値。1 に近いほど、
             way が車両と同じくらい目立つ
環境変数 BUSY_REF に通常の版の名前（画像の名前の <名前>）を渡すと、各版の way の画素のうち、通常の版の way の画素と重なる所
だけで測った値の表を足す（ref_row）。基盤・高架の版の基盤や躯体の面を除いて、軌道の部分を通常の版と比べる（#72）
環境変数 BUSY_PAIR に名前の後ろに付ける文字（例: nowall）を渡すと、<名前> と <名前><BUSY_PAIR> の画像がそろう版について、
<名前> の way の画素のうち <名前><BUSY_PAIR> の way の画素と重なる所だけで測った値の表を足す（壁・橋脚を重ねる前の範囲で比べる。#79）
環境変数 BUSY_BYZOOM を空でない値にすると、撮った拡大率ごとに、線を除いた細かさ・孤立点を出す表を足す（#79。拡大率 3 の行は上の表と同じ値）
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
LINE_DIRS = ((1, 0), (0, 1), (1, 1), (1, -1), (2, 1), (2, -1), (1, 2), (1, -2))  # 線の向き（dy, dx）。画面の 2:1 の斜めを含む
LINE_RUN = 4  # 前後 2 画素ずつ（計 4 画素）のうち、自分と同じくらいの明るさが要る数（4 = 5 画素以上まっすぐ続く）


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


def shift(a, dy, dx, fill):
    """a[y + dy, x + dx] を (y, x) に置いた配列（外は fill）。"""
    out = np.full_like(a, fill)
    h, w = a.shape
    ys, yd = (slice(dy, h), slice(0, h - dy)) if dy >= 0 else (slice(0, h + dy), slice(-dy, h))
    xs, xd = (slice(dx, w), slice(0, w - dx)) if dx >= 0 else (slice(0, w + dx), slice(-dx, w))
    out[yd, xd] = a[ys, xs]
    return out


def line_mask(L, m):
    """構造の線の画素（説明は冒頭の「線」）。"""
    med = np.nanmedian(np.stack([shift(L, dy, dx, np.nan) for dy in range(-2, 3) for dx in range(-2, 3)]), 0)
    on = np.zeros_like(m)
    for dy, dx in LINE_DIRS:
        same = [np.abs(shift(L, s * j * dy, s * j * dx, 9.0) - L) < ISO_DIFF for s in (1, -1) for j in (1, 2)]
        on |= np.sum(same, 0) >= LINE_RUN
    return (np.abs(L - med) >= ISO_MED) & on & m


def isolated_excl(L, m, x):
    """孤立点（isolated と同じ決め方。周りを見る範囲は m のまま）のうち、x の画素を除いた数（way の画素 1000 あたり）。"""
    h, w = L.shape
    c = L[1:-1, 1:-1]
    nb = np.stack([L[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx])
    nm = np.stack([m[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]).all(0)
    inside = m[1:-1, 1:-1] & nm
    iso = inside & (np.abs(nb - c).min(0) >= ISO_DIFF) & (np.abs(np.median(nb, 0) - c) >= ISO_MED) & ~x[1:-1, 1:-1]
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


ZOOM_NUM = (2, 3, 4, 1, 3, 5, 1, 3, 1, 1)  # 本体 display/simgraph16.cc の zoom_num・zoom_den（3 が等倍）
ZOOM_DEN = (1, 2, 3, 1, 4, 8, 2, 8, 4, 8)


def same_area(shape, f):
    """縮めた画面（倍率 f < 1）で、等倍の画面に写っていた範囲。画面の中心（切る前の画像の中心）から f 倍の距離の内側。
    shape は上下を切った後の大きさ"""
    h, w = shape
    full_h = h + CROP_TOP + CROP_BOTTOM
    cy, cx = full_h / 2 - CROP_TOP, w / 2
    ys = np.arange(h)[:, None]
    xs = np.arange(w)[None, :]
    return ((np.abs(xs - cx) <= cx * f) & (ys >= cy - (cy) * f) & (ys <= cy + (h - cy) * f))


def vehicle_fineness(paths):
    vals = []
    for p in paths:
        rgb = load(p)
        bg = (np.abs(rgb - np.array([231, 255, 255], np.float32) / 255).max(-1) < 0.02)
        vals.append(fineness(lum(rgb), erode(~bg)))
    return float(np.median(vals)) if vals else float("nan")


def ref_row(folder, season, name, ref):
    """BUSY_REF の表の 1 行: name の way の画素のうち、ref（通常の版）の way の画素と重なる所だけで測る。ref の範囲は、縦にずらして
    明るさが一致する画素が最も多い位置に置く（高架の版は高架の高さのぶん上にずれる）。線の画素は name の way の画素全体で選ぶ"""
    Lr, mr = way_pixels(folder, season, ref, 3)
    L, m = way_pixels(folder, season, name, 3)
    match = lambda dy: int((shift(mr, -dy, 0, False) & m & (np.abs(shift(Lr, -dy, 0, 9.0) - L) < ISO_DIFF / 3)).sum())
    dy = max(range(-48, 9), key=match)
    reg = shift(mr, -dy, 0, False) & m
    x = line_mask(L, m)
    return (f"| {season} | {name} | {dy} | {int(reg.sum())} | {100.0 * reg.sum() / max(1, m.sum()):.1f} | "
            f"{fineness(L, reg & ~x):.4f} | {isolated_excl(L, reg, x):.2f} |")


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
    head = ("| 気候 | 名前 | way の画素 | 細かさ z3 | 細かさ z4 | 細かさ z6 | つぶれ | 孤立点/千 | 車両比 | 線 % | "
            "細かさ（線を除く） | 孤立点/千（線を除く） |")
    lines += [head, "|" + "---|" * 12]
    order = lambda k: (k[0] != "temperate", k[0], k[1])
    for season, name in sorted(keys, key=order):
        zs = keys[(season, name)]
        L3, m3 = way_pixels(folder, season, name, 3)
        f = {z: fineness(*way_pixels(folder, season, name, z)) for z in sorted(zs)}
        crush = f.get(6, float("nan")) / fineness(*box2(L3, m3))
        x3 = line_mask(L3, m3)
        lines.append(f"| {season} | {name} | {int(m3.sum())} | {f.get(3, float('nan')):.4f} | {f.get(4, float('nan')):.4f} | "
                     f"{f.get(6, float('nan')):.4f} | {crush:.3f} | {isolated(L3, m3):.2f} | {f.get(3, float('nan')) / vf:.3f} | "
                     f"{100.0 * x3.sum() / max(1, m3.sum()):.1f} | {fineness(L3, m3 & ~x3):.4f} | {isolated_excl(L3, m3, x3):.2f} |")
    if os.environ.get("BUSY_BYZOOM"):
        lines += ["", "拡大率ごとの値（線を除く。線と孤立点もその拡大率の画面で選ぶ）。「等倍の範囲」は、縮めた画面（拡大率 4 以上）を、",
                  "等倍の画面に写っていた範囲（画面の中心から同じ距離）に限った値。縮めた画面は広く写るので、等倍では画面の外の物も入る:", "",
                  "| 気候 | 名前 | 拡大率 | way の画素 | 細かさ（線を除く） | 孤立点/千（線を除く） | 線 % | 等倍の範囲の画素 | "
                  "等倍の範囲の細かさ | 等倍の範囲の孤立点/千 |",
                  "|" + "---|" * 10]
        for season, name in sorted(keys, key=order):
            for z in sorted(keys[(season, name)]):
                L, m = way_pixels(folder, season, name, z)
                x = line_mask(L, m)
                row = (f"| {season} | {name} | {z} | {int(m.sum())} | {fineness(L, m & ~x):.4f} | "
                       f"{isolated_excl(L, m, x):.2f} | {100.0 * x.sum() / max(1, m.sum()):.1f} |")
                f = ZOOM_NUM[z] / ZOOM_DEN[z]
                if f < 1:
                    c = same_area(m.shape, f) & m
                    row += f" {int(c.sum())} | {fineness(L, c & ~x):.4f} | {isolated_excl(L, c, x):.2f} |"
                else:
                    row += " — | — | — |"
                lines.append(row)
    ref = os.environ.get("BUSY_REF")
    if ref:
        lines += ["", f"通常の版（{ref}）の範囲に限った値（等倍、線を除く）:", "",
                  "| 気候 | 名前 | ずらし dy | 範囲の画素 | way の画素に占める % | 細かさ（線を除く） | 孤立点/千（線を除く） |",
                  "|" + "---|" * 7]
        for season, name in sorted(keys, key=order):
            if (season, ref) in keys:
                lines.append(ref_row(folder, season, name, ref))
    pair = os.environ.get("BUSY_PAIR")
    if pair:
        lines += ["", f"名前に {pair} を足した画像（重ねる前の同じ版）の範囲に限った値（等倍、線を除く）:", "",
                  "| 気候 | 名前 | ずらし dy | 範囲の画素 | way の画素に占める % | 細かさ（線を除く） | 孤立点/千（線を除く） |",
                  "|" + "---|" * 7]
        for season, name in sorted(keys, key=order):
            if (season, name + pair) in keys:
                lines.append(ref_row(folder, season, name, name + pair))
    text = "\n".join(lines) + "\n"
    with open(out, "w", encoding="utf8", newline="\n") as fo:
        fo.write(text)
    print(text)


if __name__ == "__main__":  # half_measure.py が関数だけを import する
    main()
