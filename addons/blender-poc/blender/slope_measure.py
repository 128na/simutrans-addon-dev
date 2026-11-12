"""ゲームの画面で、直線の線路タイル（平地・坂・急坂）ごとに、道床の縁とレールの位置を測る。坂でレールが道床の片側に寄っていないかを手本と比べる。

使い方（アドオンのディレクトリで。ふつうは ingame/steep_check.sh から呼ぶ）:
    blender -b --factory-startup --python blender/slope_measure.py -- 画面.png タイル一覧.txt x,y（jump したタイル） [出力.png]

タイル一覧は1行に「x y z 坂 向き 名前」（seam_judge.py と同じ）。向きが ns・ew の2方向だけのタイルを測る。
測り方:
- 位置は、地面（坂ならその面）の中心線から画面の縦に何 px 離れているか。正が下。画素の中心で測り、1px ごとの箱（中心が整数）にまとめる
- 線路に沿っては、タイルの中心から、線路を横切るマップの軸の向き（画面で横 2 : 縦 1）に見て ±14px の範囲を使う
- 道床の縁: 中心から外へ、地面の色（緑が赤・青より強い）でない画素が半分以上ある箱が続く範囲
- レール: 帯の中ほどで、このアドオンは「赤 − 青」が大きい箱、手本（Rail_100）は明るい箱の、上の山と下の山の位置（重み付き平均）
- まくらぎの濃淡: レールの間の画素の明るさの、85% の値 − 15% の値。まくらぎが道床に埋もれると小さくなる
- 寄り = レールの中心 − 道床の中心（画面の縦 px）。絵を画面で一様に下げていれば、坂でも平地と同じ値になる。
  余白（縁からレールまで）は坂の向きで帯の高さが変わるので伸び縮みする。比べるのは寄り
合否（このアドオンの坂のタイルごと。手本のタイルは値だけ出す）: 寄りが同じ画面の平地の同じ向きのタイルと SLOPE_TOL（0.5）px 以内で、まくらぎの濃淡が平地の SLOPE_MIN_SLEEPER（0.3）倍以上。
手本の急坂は測らない（Rail_100 は急坂の絵を持たない）。SLOPE_DUMP=1 で、箱ごとの色（断面）も出す。
位置はタイルの並びから計算し、このアドオンの平らなタイルのセルが画面といちばん合う縦のずれを探す（坂のある所へ jump すると、
画面の縦の位置が地形で変わる）。手本だけの画面は、同じ地形・同じ jump のこのアドオンの画面のずれを SLOPE_OFFSET=dx,dy で与える。
出力.png を与えると、測ったタイルの中心を拡大して並べる（紫の点が地面の中心）。
"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose import IMG, load  # noqa: E402
from ingame_diff import TRANSPARENT, candidates, cell  # noqa: E402
from seam_judge import BITS, HEIGHT_PX, SHEETS, Tile  # noqa: E402

SMAX = 30   # 断面を取る範囲（画面の縦 ±px）
TOP, BOTTOM = 45, 25  # 画面の上の道具の列と、下の帯の高さ
UMAX = 14   # 線路に沿って測る範囲（タイルの中心から、画面の横 ±px）
DUMP = os.environ.get("SLOPE_DUMP")
TOL = float(os.environ.get("SLOPE_TOL", "0.5"))  # 寄りが平地の同じ向きのタイルと何 px（画面の縦）違ったら不合格か
MIN_SLEEPER = float(os.environ.get("SLOPE_MIN_SLEEPER", "0.3"))  # まくらぎの濃淡が平地の何倍より小さいと不合格か


def is_ground(px):
    """地面（草）の色か。日なた・陰・坂の明るさの違いがあっても、緑が赤・青より強い"""
    return (px[..., 1] - np.maximum(px[..., 0], px[..., 2])) > 12


def locate(game, tiles, jx, jy):
    """このアドオンの平らなタイルのセルを見当の位置に置き、画面といちばん合うずれ（横 ±2、縦 ±130）。"""
    pieces = []
    for t in tiles:
        if not t.name.startswith("bpoc_") or t.slope:
            continue
        keys = candidates(0, sum(BITS[d] for d in t.dirs), IMG)
        if len(keys) != 1:
            continue
        sheet = SHEET_CACHE.setdefault(t.name, load(os.path.join(ROOT, "src", SHEETS[t.name] + ".png")))
        cl = cell(sheet, IMG, keys[0])
        m = np.any(cl != TRANSPARENT, axis=-1)
        ys, xs = np.nonzero(m)
        gx = 192 + ((t.x - jx) - (t.y - jy)) * 64
        gy = 256 + ((t.x - jx) + (t.y - jy)) * 32 - t.z * HEIGHT_PX
        pieces.append((ys + gy, xs + gx, cl[ys, xs].astype(int)))
    if not pieces:
        return None
    H, W = game.shape[:2]
    best = None
    for dy in range(-130, 131):
        for dx in range(-2, 3):
            tot, n = 0.0, 0
            for ys, xs, val in pieces:
                gy, gx = ys + dy, xs + dx
                ok = (gy >= TOP) & (gy < H - BOTTOM) & (gx >= 0) & (gx < W)
                tot += np.abs(game[gy[ok], gx[ok]] - val[ok]).sum()
                n += int(ok.sum()) * 3
            if n > 3000 and (best is None or tot / n < best[0]):
                best = (tot / n, dx, dy)
    return best


def measure(game, t, origin):
    """タイル t の断面。画素の中心ごとに (u, s) を出し、s を 1 ごとの箱（中心が整数）にまとめる。"""
    H, W = game.shape[:2]
    a, b = (t.edge_mid(origin, d) for d in t.dirs)
    if a[0] > b[0]:
        a, b = b, a
    c = (a + b) / 2
    slope = (b[1] - a[1]) / (b[0] - a[0])  # 中心線の画面の傾き
    mx = 1.0 if "n" in t.dirs else -1.0    # 横切る軸の向き（下向きを正）: ns の線路は右下、ew の線路は左下
    conv = 0.5 - mx * slope                # s を 1 進むと、中心線から画面の縦に何 px 離れるか
    x0, x1 = max(int(c[0]) - UMAX - SMAX, 0), min(int(c[0]) + UMAX + SMAX, W)
    y0, y1 = max(int(c[1]) - 2 * SMAX, TOP), min(int(c[1]) + 2 * SMAX, H - BOTTOM)
    if x0 >= x1 or y0 >= y1:
        return None
    yy, xx = np.mgrid[y0:y1, x0:x1]
    # 画素の中心 = c + u·(1, slope) + s·(mx, 0.5)
    dx, dy = xx + 0.5 - c[0], yy + 0.5 - c[1]
    v = dy - slope * dx  # 中心線からの画面の縦の距離
    u = dx - mx * v / conv
    k = np.floor(v + 0.5).astype(int)
    sel = (np.abs(u) <= UMAX) & (np.abs(k) <= SMAX)
    px = game[y0:y1, x0:x1]
    way = ~is_ground(px)
    # 箱の画素が、線路に沿った範囲の 3/4 以上そろっていない箱（画面の端で切れた所）は使わない
    full = max((sel & (k == i)).sum() for i in range(-SMAX, SMAX + 1))
    frac = {i: way[sel & (k == i)].mean() for i in range(-SMAX, SMAX + 1) if (sel & (k == i)).sum() >= full * 0.75}
    if frac.get(0, 0) < 0.5:
        return None
    top = 0
    while top - 1 in frac and frac[top - 1] >= 0.5:
        top -= 1
    bot = 0
    while bot + 1 in frac and frac[bot + 1] >= 0.5:
        bot += 1
    prof = {i: px[sel & (k == i)].mean(0) for i in range(top, bot + 1)}
    if DUMP:
        print(f"   断面 {t.name}({t.x},{t.y}) " + " ".join(f"{i:+d}:{int(v[0])},{int(v[1])},{int(v[2])}" for i, v in sorted(prof.items())))
    kind = "red" if t.name.startswith("bpoc_") else "bright"
    rl = rails(prof, top, bot, kind)
    sleeper = None
    if rl:
        # まくらぎ: レールの間の画素の明るさの濃淡（線路に沿って、まくらぎと道床が交互に並ぶ）
        mid = sel & (v > rl[0] + 1.0) & (v < rl[1] - 1.0)
        if mid.sum() >= 8:
            v = px[mid].mean(-1)
            sleeper = float(np.percentile(v, 85) - np.percentile(v, 15))
    return {"top": top - 0.5, "bot": bot + 0.5, "rails": rl, "sleeper": sleeper, "conv": conv, "center": c}


def steep(t):
    """2段の坂か（坂の番号を3進で見て、2 の桁がある）"""
    n = t.slope
    while n:
        if n % 3 == 2:
            return True
        n //= 3
    return False


def rails(prof, top, bot, kind):
    """レールの上の山と下の山の位置。kind: "red" は赤みの強い箱（このアドオンのレールの色）、
    "bright" は明るい箱のすぐ下が暗い所（Rail_100 のレールは、明るい上面の下に暗い側面がある）"""
    # レールは帯の中ほど（幅の 6 割）にある。外側の道床の明るい縁・暗い側面を拾わない
    mid, hw = (top + bot) / 2, (bot - top) * 0.3 + 1
    ss = [s for s in sorted(prof) if mid - hw <= s <= mid + hw and (kind == "red" or s + 1 in prof)]
    if len(ss) < 4:
        return None
    if kind == "red":
        val = np.array([prof[s][0] - prof[s][2] for s in ss])
        val = val - np.median(val)
    else:
        val = np.array([prof[s].mean() - prof[s + 1].mean() for s in ss])
    i1 = int(np.argmax(val))
    far = [i for i in range(len(ss)) if abs(ss[i] - ss[i1]) >= 3]
    if not far or val[i1] <= 0:
        return None
    i2 = max(far, key=lambda i: val[i])
    if val[i2] < val[i1] * 0.25:
        return None
    out = []
    for i in sorted((i1, i2)):
        near = [j for j in range(len(ss)) if abs(j - i) <= 1 and val[j] >= val[i] * 0.5]
        out.append(float(sum(val[j] * ss[j] for j in near) / sum(val[j] for j in near)))
    return out


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    shot, tiles_path = args[:2]
    jx, jy = (int(v) for v in args[2].split(","))
    game = load(shot).astype(int)
    tiles = []
    for line in open(tiles_path, encoding="utf8"):
        p = line.split()
        if len(p) == 6:
            tiles.append(Tile(*(int(v) for v in p[:5]), p[5]))
    if os.environ.get("SLOPE_OFFSET"):
        ox, oy = (int(v) for v in os.environ["SLOPE_OFFSET"].split(","))
        print(f"[locate] 与えられたずれ {ox},{oy}")
    else:
        best = locate(game, tiles, jx, jy)
        if best is None:
            print("[slope] このアドオンの平らなタイルが無い。SLOPE_OFFSET=dx,dy で位置を与える")
            return
        err, ox, oy = best
        print(f"[locate] 見当からのずれ {ox},{oy}（err {err:.1f}）")
    rows = []
    for t in sorted(tiles, key=lambda t: (t.name, -abs(t.slope), t.x, t.y)):
        if sorted(t.dirs) not in (["n", "s"], ["e", "w"]):
            continue
        origin = (192 + ox + 128 + ((t.x - jx) - (t.y - jy)) * 64,
                  256 + oy + 128 + ((t.x - jx) + (t.y - jy)) * 32 - t.z * HEIGHT_PX)
        rows.append((t, measure(game, t, origin)))
    # 平地の同じ向きのタイルの値（坂と比べる基準）
    flat = {}
    for t, r in rows:
        if r and r["rails"] and not t.slope:
            flat.setdefault((t.name, "".join(t.dirs)), r)
    results, marks = [], []
    for t, r in rows:
        tag = f"{t.name}({t.x},{t.y}) 坂{t.slope} {''.join(t.dirs)}"
        if steep(t) and not t.name.startswith("bpoc_"):
            print(f"[slope] {tag}: 手本の急坂は測らない（Rail_100 には急坂の絵が無く、1段の坂の絵が出る）")
            continue
        if r is None:
            print(f"[slope] {tag}: 測れない（画面の外か、位置合わせの失敗）")
            continue
        marks.append(r["center"])
        cb = (r["top"] + r["bot"]) / 2
        line = f"[slope] {tag}: 道床 {r['top']:+.1f}〜{r['bot']:+.1f}（中心 {cb:+.2f}）"
        if not r["rails"]:
            print(line + " レールが見つからない")
            if t.slope and t.name.startswith("bpoc_"):
                results.append(False)
            continue
        cr = sum(r["rails"]) / 2
        off = cr - cb
        line += f" レール {r['rails'][0]:+.1f}・{r['rails'][1]:+.1f}（中心 {cr:+.2f}） 寄り {off:+.2f}px"
        line += f" 上の余白 {r['rails'][0] - r['top']:.1f}px 下の余白 {r['bot'] - r['rails'][1]:.1f}px"
        if r["sleeper"] is not None:
            line += f" まくらぎの濃淡 {r['sleeper']:.0f}"
        f = flat.get((t.name, "".join(t.dirs)))
        if t.slope and f:
            foff = sum(f["rails"]) / 2 - (f["top"] + f["bot"]) / 2
            ok = abs(off - foff) <= TOL
            line += f" 平地との差 {off - foff:+.2f}px"
            if f["sleeper"] and r["sleeper"] is not None:
                ok = ok and r["sleeper"] >= f["sleeper"] * MIN_SLEEPER
                line += f"・濃淡 {r['sleeper'] / f['sleeper']:.2f}倍"
            if t.name.startswith("bpoc_"):
                line += " OK" if ok else " NG"
                results.append(ok)
        print(line)
    if results:
        print(f"[slope] 坂 {len(results)} タイル中 合格 {sum(results)}・不合格 {len(results) - sum(results)}")
    if len(args) > 3 and marks:
        R, S = 40, 5
        parts = []
        for c in marks:
            x, y = int(c[0]), int(c[1])
            tl = np.zeros((2 * R + 1, 2 * R + 1, 3), np.float32)
            y0, y1, x0, x1 = max(y - R, 0), min(y + R + 1, game.shape[0]), max(x - R, 0), min(x + R + 1, game.shape[1])
            tl[y0 - (y - R):y1 - (y - R), x0 - (x - R):x1 - (x - R)] = game[y0:y1, x0:x1] / 255.0
            tl[R, R] = (1, 0, 1)
            parts.append(tl.repeat(S, 0).repeat(S, 1))
            parts.append(np.ones((tl.shape[0] * S, 4, 3), np.float32))
        v = np.concatenate(parts[:-1], 1)
        v = np.dstack([v, np.ones(v.shape[:2], np.float32)])
        o = bpy.data.images.new("o", v.shape[1], v.shape[0])
        o.pixels.foreach_set(np.flipud(v).ravel())
        o.filepath_raw = os.path.abspath(args[3])
        o.file_format = "PNG"
        o.save()


SHEET_CACHE = {}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    main()
