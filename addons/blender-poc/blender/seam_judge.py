"""他のアドオン（SIS・pak128 標準など）とのつなぎ目を、ゲームの画面から判定する。

使い方（アドオンのディレクトリで。ふつうは ingame/seam_check.sh から呼ぶ）:
    blender -b --factory-startup --python blender/seam_judge.py -- 画面.png タイル一覧.txt 出力.png x,y（jump したタイル）

タイル一覧は1行に「x y z 坂 向き 名前」。名前が bpoc_ で始まるタイルがこのアドオンの道で、それ以外が相手の道。
相手とこのアドオンのタイルが道でつながっている辺（継ぎ目）ごとに、両側の道の帯を測って比べる:
- 縁: 継ぎ目から 4〜20px（曲がりは 3〜10px）離れた所で、道の中心線から、両側の道の向きの平均に直角な向きへ、草でない画素が続く範囲。
  両側の中央値の差から「中心のずれ」（段）と「幅の差」を出す。幅の差は道の作りの違いなので、合否には使わない
- 草: 継ぎ目の辺の線（±1px）の上で、両側の帯の縁より GRASS_MARGIN px 内側にある草の画素の数。継ぎ目に入った草の線や隙間
- 模様: 帯を横切る明るさの断面（レール・白線・縁石）を両側で比べ、いちばん合うずらし量
合否: 草 0、|中心のずれ| <= TOL_CENTER（両側の縁が測れて、幅の差が TOL_WIDTH 以下のときだけ。縁がタイルの角まで届く道・曲がりは片側しか測れないので参考。坂と平地の継ぎ目も、坂の帯が広く測れるので参考）、|模様のずれ| <= TOL_PATTERN（相関が弱いときと、曲がりのタイルの継ぎ目は模様を判定しない）。
曲がりの絵は帯を横切る線が曲がった先の帯にもかかるので、相手より 8px 以上外まで続く縁は比べず、もう片方の縁だけで中心のずれを出す。
出力.png は継ぎ目ごとに拡大して並べた画像（目で確かめる用。中心の紫の点が継ぎ目の点）。
位置はタイルの並びから計算する（jump したタイルのセルの左上が画面の (192, 256)）。SEAM_RANGE=n で、このアドオンのセルが画面といちばん合う位置を ±n px 探す。
"""
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compose import IMG, IMG_EXPWY, load  # noqa: E402
from ingame_diff import TRANSPARENT, candidates, cell  # noqa: E402

TOL_CENTER = float(os.environ.get("SEAM_TOL_CENTER", "1.0"))
TOL_PATTERN = float(os.environ.get("SEAM_TOL_PATTERN", "1.0"))
TOL_WIDTH = float(os.environ.get("SEAM_TOL_WIDTH", "3"))
# 継ぎ目の草を数えるのは、両側の帯の縁から何 px 内側まで（縁の角の 1px の尖りは数えない）
GRASS_MARGIN = 2
MIN_CORR = 0.5
SHEETS = {"bpoc_track": "track", "bpoc_track_old": "track_old", "bpoc_road": "road", "bpoc_expressway": "expressway"}
STEP = {"n": (0, -1), "e": (1, 0), "s": (0, 1), "w": (-1, 0)}
OPP = {"n": "s", "s": "n", "e": "w", "w": "e"}
BITS = {"n": 1, "e": 2, "s": 4, "w": 8}
# 菱形の角（タイル中心からの画面の位置）と、辺の両端の角
CORNER = {"nw": (0, -32), "ne": (64, 0), "se": (0, 32), "sw": (-64, 0)}
EDGE = {"n": ("nw", "ne"), "e": ("ne", "se"), "s": ("se", "sw"), "w": ("sw", "nw")}
# 坂の番号の各桁（3進）が角の高さ: sw=1, se=3, ne=9, nw=27
DIGIT = {"sw": 1, "se": 3, "ne": 9, "nw": 27}
HEIGHT_PX = 16


def is_grass(px):
    """草（地面）の色か。草は緑が赤・青より強く、とくに青が低い。歩道の緑がかった敷石（赤と青がほぼ同じ、緑が青より 16〜24 大きい）は草にしない"""
    r, g, b = int(px[0]), int(px[1]), int(px[2])
    return g - max(r, b) > 12 and g - b > 40


class Tile:
    def __init__(self, x, y, z, slope, dirs, name):
        self.x, self.y, self.z, self.slope, self.name = x, y, z, slope, name
        self.dirs = [d for d in "nesw" if dirs & BITS[d]]

    def corner(self, origin, c):
        h = (self.slope // DIGIT[c]) % 3 if self.slope else 0
        cx, cy = origin
        dx, dy = CORNER[c]
        return np.array([cx + dx, cy + dy - h * HEIGHT_PX], float)

    def edge_mid(self, origin, d):
        a, b = EDGE[d]
        return (self.corner(origin, a) + self.corner(origin, b)) / 2


def locate(game, sheet, img, mine, guess, rng):
    """このアドオンのタイル全部のセルを一緒に当て、画面といちばん合うずらし量。直線だけでも、相手の絵との境で決まる。"""
    best = None
    pieces = []
    for t, (gx, gy) in mine:
        keys = candidates(t.slope, sum(BITS[d] for d in t.dirs), img)
        if not keys:
            continue
        cl = cell(sheet, img, keys[0])
        m = np.any(cl != TRANSPARENT, axis=-1)
        mm = m.copy()
        for s in (1, 2):
            mm &= np.roll(m, s, 0) & np.roll(m, -s, 0) & np.roll(m, s, 1) & np.roll(m, -s, 1)
        ys, xs = np.nonzero(mm)
        pieces.append((ys + gy, xs + gx, cl[ys, xs].astype(int)))
    H, W = game.shape[:2]
    for dy in range(-rng, rng + 1):
        for dx in range(-rng, rng + 1):
            tot, n = 0.0, 0
            for ys, xs, val in pieces:
                gy, gx = ys + dy, xs + dx
                ok = (gy >= 0) & (gy < H) & (gx >= 0) & (gx < W)
                tot += np.abs(game[gy[ok], gx[ok]] - val[ok]).sum()
                n += ok.sum() * 3
            if n and (best is None or tot / n < best[0]):
                best = (tot / n, dx, dy)
    return best


def band(game, p, d, m, us, vmax=40):
    """p から d の向きへ us の距離の各点で、m の向きに草でない画素が続く範囲（上端・下端）と、断面の明るさ。"""
    H, W = game.shape[:2]
    tops, bots, prof = [], [], {}
    for u in us:
        c = p + d * u
        def px(v):
            x, y = int(round(c[0] + m[0] * v)), int(round(c[1] + m[1] * v))
            return game[y, x] if 0 <= x < W and 0 <= y < H else None
        if px(0) is None or is_grass(px(0)):
            continue
        top = 0
        while top > -vmax and px(top - 1) is not None and not is_grass(px(top - 1)):
            top -= 1
        bot = 0
        while bot < vmax and px(bot + 1) is not None and not is_grass(px(bot + 1)):
            bot += 1
        tops.append(top)
        bots.append(bot)
        for v in range(top, bot + 1):
            prof.setdefault(v, []).append(float(px(v)[:3].mean()))
    if not tops:
        return None
    # ばらつき（縁が向きに沿ってどれだけ揺れるか）。向きの候補を選ぶのに使う
    spread = float(np.subtract(*np.percentile(tops, [75, 25])) + np.subtract(*np.percentile(bots, [75, 25])))
    return (float(np.median(tops)), float(np.median(bots)), {v: np.mean(a) for v, a in prof.items() if len(a) >= len(tops) // 2},
            len(tops), spread)


def pattern_shift(pa, pb, lo, hi):
    best = None
    scores = {}
    for s in range(-4, 5):
        va = [pa[v] for v in range(lo, hi + 1) if v in pa and v + s in pb]
        vb = [pb[v + s] for v in range(lo, hi + 1) if v in pa and v + s in pb]
        if len(va) < 5:
            continue
        a, b = np.array(va) - np.mean(va), np.array(vb) - np.mean(vb)
        den = np.sqrt((a * a).sum() * (b * b).sum())
        if den == 0:
            continue
        r = (a * b).sum() / den
        scores[s] = r
        if best is None or r > best[1]:
            best = (s, r)
    # いちばん合うずらし量の前後の相関から、1px 未満まで求める（放物線の頂点）
    if best and best[0] - 1 in scores and best[0] + 1 in scores:
        ym, y0, yp = scores[best[0] - 1], best[1], scores[best[0] + 1]
        den = ym - 2 * y0 + yp
        if den < 0:
            best = (best[0] + 0.5 * (ym - yp) / den, best[1])
    return best


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    shot, tiles_path, out_path = args[:3]
    jx, jy = (int(v) for v in args[3].split(","))
    game = load(shot).astype(int)
    tiles = {}
    for line in open(tiles_path, encoding="utf8"):
        p = line.split()
        if len(p) == 6:
            t = Tile(*(int(v) for v in p[:5]), p[5])
            tiles[(t.x, t.y)] = t
    mine_names = {t.name for t in tiles.values() if t.name.startswith("bpoc_")}
    if len(mine_names) != 1:
        print(f"[seam] このアドオンの道が {sorted(mine_names)}（1種類でない）")
        return
    name = mine_names.pop()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sheet = load(os.path.join(root, "src", SHEETS[name] + ".png"))
    img = IMG_EXPWY if name == "bpoc_expressway" else IMG

    # 見当: jump したタイルのセルの左上が (192, 256)（ingame_diff.py と同じ）
    def cell_pos(t):
        return (192 + ((t.x - jx) - (t.y - jy)) * 64, 256 + ((t.x - jx) + (t.y - jy)) * 32 - t.z * HEIGHT_PX)
    mine = [(t, cell_pos(t)) for t in tiles.values() if t.name == name]
    # 位置はタイルの並びの計算どおり（この見当はゲームの jump と画面の大きさ 704x560 で毎回ちょうど合っていた）。
    # 絵の位置を合わせて探すと、こちらの絵のずれを位置合わせが吸収してしまうので、既定では探さない（SEAM_RANGE で探せる）
    rng = int(os.environ.get("SEAM_RANGE", "0"))
    err, ox, oy = locate(game, sheet, img, mine, None, rng)
    print(f"[locate] {name} 見当からのずれ {ox},{oy}（探した範囲 ±{rng}px、err {err:.1f}）")

    def origin(t):
        x, y = cell_pos(t)
        return (x + ox + 128, y + oy + 128)  # 256px セルのタイル中心（dat のオフセット -64,-32）

    joints = []
    for t in tiles.values():
        for d in t.dirs:
            n = tiles.get((t.x + STEP[d][0], t.y + STEP[d][1]))
            if n is None or OPP[d] not in n.dirs or (t.name == name) == (n.name == name):
                continue
            if t.name == name:  # 相手 → このアドオン の向きにそろえる（同じ継ぎ目を2回数えない）
                continue
            joints.append((t, d, n))
    if not joints:
        print("[seam] 継ぎ目が画面に無い")
        return
    H, W = game.shape[:2]
    # 継ぎ目から何 px 離れた所を測るか。曲がりはすぐ向きが変わるので近くだけ
    def near(t):
        bend = len(t.dirs) == 2 and OPP[t.dirs[0]] != t.dirs[1]
        return range(3, 11) if bend else range(4, 21)
    results, crops = [], []
    for a, d, b in sorted(joints, key=lambda j: (j[0].x, j[0].y)):
        p = a.edge_mid(origin(a), d)
        if not (40 < p[0] < W - 40 and 40 < p[1] < H - 40):
            continue

        def is_bend(t):
            return len(t.dirs) == 2 and OPP[t.dirs[0]] != t.dirs[1]

        def is_diagonal(t):
            """曲がりのタイルが斜めの絵か。出口の先の隣が、階段状に続く曲がり（入口が向かい合い、もう一方の向きが逆）なら斜め"""
            if not is_bend(t):
                return False
            for e in t.dirs:
                other = next(f for f in t.dirs if f != e)
                n = tiles.get((t.x + STEP[e][0], t.y + STEP[e][1]))
                if n is not None and set(n.dirs) == {OPP[e], OPP[other]}:
                    return True
            return False

        def away(t, edge):
            """継ぎ目の辺 edge から、タイル t の道の奥へ向かう単位ベクトル。
            直線・分岐・カーブの絵は反対の辺へ（辺に直角）。斜めの絵はもう一方の辺へ（弦）。行き止まりは中心へ"""
            o = origin(t)
            q0 = t.edge_mid(o, edge)
            if is_diagonal(t):
                q1 = t.edge_mid(o, next(e for e in t.dirs if e != edge))
            elif OPP[edge] in t.dirs or is_bend(t):
                q1 = t.edge_mid(o, OPP[edge])
            else:
                q1 = np.array(o, float)
            return [(q1 - q0) / np.linalg.norm(q1 - q0)]
        best = None
        for da in away(a, d):
            for db in away(b, OPP[d]):
                # 帯を横切る向き: 両側の道の向きの平均に直角（画面で下向き、縦向きの道は右向きを正にする）
                avg = (db - da) / np.linalg.norm(db - da)
                m = np.array([-avg[1], avg[0]])
                if m[1] < -1e-9 or (abs(m[1]) < 1e-9 and m[0] < 0):
                    m = -m
                ba, bb = band(game, p, da, m, near(a)), band(game, p, db, m, near(b))
                if ba is None or bb is None:
                    continue
                # 帯を正しい向きで横切ると幅がいちばん狭く、縁の揺れも小さい
                score = (ba[3] + bb[3], -((ba[1] - ba[0]) + (bb[1] - bb[0]) + ba[4] + bb[4]))
                if best is None or score > best[0]:
                    best = (score, da, db, m, ba, bb)
        if best is None:
            ba = bb = None
        else:
            _, da, db, m, ba, bb = best
        tag = f"{a.name}({a.x},{a.y}) -{d}- {b.name}({b.x},{b.y})"
        if ba is None or bb is None:
            print(f"[seam] {tag}: 道の帯が見つからない（画面の外か、位置合わせの失敗）")
            results.append(False)
            continue
        # 曲がりの絵では、帯を横切る線が曲がった先の帯にもかかり、縁が相手より大きく外まで続く。その縁は測れないので比べない
        bend_a, bend_b = is_bend(a) and not is_diagonal(a), is_bend(b) and not is_diagonal(b)
        # 継ぎ目の辺の両端（タイルの角）の、帯を横切る向きの位置。縁がここまで届く道（歩道付きの道路・全面の道床）は、縁を比べない
        c0, c1 = (a.corner(origin(a), c) for c in EDGE[d])
        dmean = (db - da) / np.linalg.norm(db - da)
        vpos = lambda q: np.linalg.solve(np.column_stack([dmean, m]), q - p)[1]
        vc = sorted([vpos(c0), vpos(c1)])
        known = []
        for i in (0, 1):
            diff = bb[i] - ba[i]
            if abs(diff) > 8 and ((bend_b and abs(bb[i]) > abs(ba[i])) or (bend_a and abs(ba[i]) > abs(bb[i]))):
                continue
            if abs(ba[i]) >= abs(vc[i]) - 2 or abs(bb[i]) >= abs(vc[i]) - 2:
                continue
            known.append(diff)
        width = (bb[1] - bb[0]) - (ba[1] - ba[0]) if len(known) == 2 else None
        center = float(np.mean(known)) if known else None
        # 幅が大きく違う道どうし（作りの違い）は、中心の差を段とは見なさない（参考に出す）
        # 片側の縁だけのとき（曲がり・幅いっぱいの道）は幅の違いと区別できないので、これも参考
        # 坂と平地の継ぎ目は、坂の帯が直角の向きに広く測れる（手本どうしの Rail_100 の平地→坂でも、坂が 6px 広く中心は 0）。
        # 平地の相手と坂のこちらの幅がそろって見えても作りの違いを含むので、これも参考（坂どうしは比べる）
        slope_mix = bool(a.slope) != bool(b.slope)
        judge_center = width is not None and abs(width) <= TOL_WIDTH and not slope_mix
        lo, hi = max(ba[0], bb[0]) + GRASS_MARGIN, min(ba[1], bb[1]) - GRASS_MARGIN
        # 継ぎ目の辺の線（±1px）の上で、両側の帯の内側にある草
        e = (c1 - c0) / np.linalg.norm(c1 - c0)
        grass = set()
        for t_ in np.arange(-80, 80.5, 0.5):
            q = p + e * t_
            # 帯の中の位置は、道の中心線からの m の向きの距離（q - p = α·dir + v·m を解く）。継ぎ目の辺のどちら側でも測れるよう、両側の向きの平均を使う
            v = vpos(q)
            if not (lo <= v <= hi):
                continue
            for k in (-1, 0, 1):
                x, y = int(round(q[0] + m[0] * k)), int(round(q[1] + m[1] * k))
                if 0 <= x < W and 0 <= y < H and is_grass(game[y, x]):
                    grass.add((x, y))
        # 模様は帯の縁から 4px 内側だけで比べる（縁はタイルの角で切られて、絵がずれても動かない）
        ps = pattern_shift(ba[2], bb[2], int(lo) + 2, int(hi) - 2)
        ok = not grass and (not judge_center or abs(center) <= TOL_CENTER)
        pat = "模様 判定なし"
        if ps:
            pat = f"模様のずれ {ps[0]:+.1f}px（相関 {ps[1]:.2f}）"
            if bend_a or bend_b:
                pat += " 参考（曲がり）"
            elif ps[1] >= MIN_CORR and abs(ps[0]) > TOL_PATTERN:
                ok = False
        results.append(ok)
        print(f"[seam] {'OK' if ok else 'NG'} {tag} @({p[0]:.0f},{p[1]:.0f}): 中心のずれ {'比べない' if center is None else f'{center:+.1f}px'}{'（片側の縁だけ）' if len(known) == 1 else ''}"
              f"{'' if judge_center or center is None else '（坂と平地なので参考）' if slope_mix else '（幅が違うので参考）'} "
              f"幅の差 {'-' if width is None else f'{width:+.1f}px'} "
              f"継ぎ目の草 {len(grass)}px {sorted(grass)[:4]} {pat}"
              f"（縁 相手 {ba[0]:+.0f}〜{ba[1]:+.0f} / こちら {bb[0]:+.0f}〜{bb[1]:+.0f}）")
        # 目で確かめる用の拡大（継ぎ目の点に紫の印）
        r, s = 24, 5
        x, y = int(round(p[0])), int(round(p[1]))
        t = np.zeros((2 * r + 1, 2 * r + 1, 3), int)
        y0, y1, x0, x1 = max(y - r, 0), min(y + r + 1, H), max(x - r, 0), min(x + r + 1, W)
        t[y0 - (y - r):y1 - (y - r), x0 - (x - r):x1 - (x - r)] = game[y0:y1, x0:x1]
        for gx, gy in grass:
            if abs(gx - x) <= r and abs(gy - y) <= r:
                t[gy - y + r, gx - x + r] = (255, 255, 0)
        t[r, r] = (255, 0, 255)
        crops.append(np.pad(t.repeat(s, 0).repeat(s, 1), ((0, 0), (0, 4), (0, 0)), constant_values=255))
    print(f"[seam] {name}: 継ぎ目 {len(results)} か所、NG {results.count(False)}")
    if crops:
        v = np.concatenate(crops, 1).astype(np.uint8)
        h, w, _ = v.shape
        o = bpy.data.images.new("o", w, h)
        rgba = np.concatenate([v, np.full((h, w, 1), 255, np.uint8)], 2)
        o.pixels.foreach_set((np.flipud(rgba).astype(np.float32) / 255).ravel())
        o.filepath_raw = os.path.abspath(out_path)
        o.file_format = "PNG"
        o.save()


main()
