"""盛土（#123）の絵の形と割り当ての検査（#148）。check.sh が呼ぶ。Python の標準ライブラリだけで動く（CI に numpy・Blender は無い）。

    python -X utf8 check_embankment.py [src のディレクトリ]

盛土の dat（名前が ami_embankment_<front|back>）の絵のキーごとに、そのキーが指すセルの絵の塗った範囲が、キーから決まる形を
画面に写した範囲と合うかを見る。dat のキーとセルの割り当てが崩れても、形の作り（sheetlib の embankment_sheet）が崩れても落ちる。

- 期待する形は、ここで README の「盛土の作り」から書き直したもの（sheetlib を読まない。読むと、作りが崩れたときに一緒に崩れる）
  - 楔: 高い辺は高架と同じ 2 段（32px）。front は北・西が高い（法面が南・東を向く）、back は逆
  - 直線・行き止まり・坂は直線の楔、曲がりは台の角（外の角・内の角を斜めの稜線で折る）、T字・十字・1 タイルは上が平らな箱
  - つながる辺には側面が無く、地面より上の辺には側面がある（T字・十字の箱は、開いた辺から底が見える）
- キーと形: image[ns] は南北の直線、[n] などは行き止まり、[-] は 1 タイル、[sw] などは曲がり、[nse] などと分岐の絵
  （[nse1]・[nse2]）は T字・十字、imageup[12] などは坂（imageup2 は 2 段の坂）。雪の絵（[1]）も同じ形
- 比べ方: 形を細かい点に分けて 128px の座標に写し（地面の菱形は (64,64)(128,96)(64,128)(0,96)、1 段は 16px）、塗る画素の集まりを作る。
  絵の塗った画素のうち、期待の範囲から TOL px より離れた画素と、期待の範囲を TOL px 削った内側で塗られていない画素を数える
  （輪郭の 1〜2px の差は、つなぎ目で隣へ延ばす分（EMB_OVERLAP）・持ち分の切り方・輪郭の半透明の画素を捨てる分）

見分けられないもの: 直線と行き止まり（行き止まりの端の三角の面は、直線の楔の輪郭の内側に描かれる）、T字・十字のうち
開いた辺の違いが輪郭に出ないもの（例: 南北東と北東西。開いた辺から見える底が、側面と同じ範囲を塗る）。どちらも面の色でしか違わない
"""
import os
import sys

from check_icons import CELL, TRANSPARENT, cell_of, fmt, read_dats, read_rows

TOL = 2          # 輪郭の許し（px）
MAX_BAD = 6      # 許しの外に出た画素の数の上限（輪郭の端の数画素）
STEPS = 160      # タイル 1 辺を割る数（1 つの点が約 0.4px）
OVERLAP = 0.025  # つながる辺で隣のタイルへ延ばす長さ（タイル 1 辺 = 1。sheetlib の EMB_OVERLAP 0.25 / TILE 10）
LEVEL = 16       # 1 段の高さ（px）
HIGH = 2         # 楔の高い辺の段数（高架と同じ）

F = {"n": lambda x, y: y + 0.5, "s": lambda x, y: 0.5 - y, "e": lambda x, y: x + 0.5, "w": lambda x, y: 0.5 - x}
OPP = {"n": "s", "s": "n", "e": "w", "w": "e"}
SLOPE = {"12": "n", "9": "w", "3": "s", "6": "e"}  # 坂の番号 → 高い辺（way-addon.md の 5 章）


def shape_of(key):
    """dat のキー（小文字）→ (形の名前, つながる辺, 坂の高い辺, 坂の段数)。盛土の絵のキーでなければ None"""
    if key.startswith("imageup"):
        n = 2 if key.startswith("imageup2") else 1
        code = key[key.index("[") + 1:key.index("]")]
        hi = SLOPE[code]
        return (f"up{'' if n == 1 else '2_'}{code}", "ns" if hi in "ns" else "ew", hi, n)
    if not key.startswith("image["):
        return None
    idx = key[len("image["):key.index("]")].rstrip("12")
    if idx == "-":
        return ("single", "", None, 0)
    if idx in ("sw", "nw", "ne", "se"):
        return (f"corner_{idx}", idx, None, 0)
    return (idx, idx, None, 0)


def height(name, side):
    """形の高さの割合（0 = 地面、1 = 2 段）の関数。x は東、y は北で、タイルは -0.5〜0.5"""
    hi_ns, hi_ew = ("w", "n") if side == "front" else ("e", "s")
    if name in ("ns", "n", "s") or name.startswith("up") and name[-2:] in ("12", "_3") or name == "up3":
        return F[hi_ns]
    if name in ("ew", "e", "w") or name.startswith("up"):
        return F[hi_ew]
    if name.startswith("corner_"):
        c = name[-2:]
        inner = c == "se" if side == "front" else c != "se"   # 内の角: front は南東、back は北西・北東・南西
        if inner:   # 低い角 c の向かいの 2 辺が高い
            a, b = F[OPP[c[0]]], F[OPP[c[1]]]
            return lambda x, y: min(1.0, a(x, y) + b(x, y))
        a, b = F[c[0]], F[c[1]]
        return lambda x, y: max(0.0, a(x, y) + b(x, y) - 1.0)
    return lambda x, y: 1.0


def expected(name, side, exits, slope_hi, slope_n):
    """期待する塗る画素の集まり（128px の座標）"""
    h = height(name, side)
    g = F[slope_hi] if slope_hi else (lambda x, y: 0.0)
    pts = set()

    def put(sx, sy0, sy1):
        x = int(sx)
        for y in range(int(min(sy0, sy1)), int(max(sy0, sy1)) + 1):
            pts.add((x, y))

    lo = {s: -0.5 - (OVERLAP if s in exits else 0.0) for s in "sw"}
    hi = {s: 0.5 + (OVERLAP if s in exits else 0.0) for s in "ne"}
    n = STEPS
    for i in range(n + 1):
        for j in range(n + 1):
            ex, ey = -0.5 + i / n, -0.5 + j / n   # 辺の元の点（高さはここで決める）
            x = lo["w"] if i == 0 else hi["e"] if i == n else ex
            y = lo["s"] if j == 0 else hi["n"] if j == n else ey
            sx = 64 + 64 * (x + y)
            base = 96 - 32 * (y - x) - LEVEL * slope_n * g(ex, ey)
            top = base - LEVEL * HIGH * min(1.0, max(0.0, h(ex, ey)))
            put(sx, top, top)    # 上の面
            put(sx, base, base)  # 底
            edge = [s for s, on in (("w", i == 0), ("e", i == n), ("s", j == 0), ("n", j == n)) if on]
            if top < base and any(s not in exits for s in edge):
                put(sx, top, base)  # 側面（地面より上の、つながらない辺）
    return pts


def near(pts, r):
    """pts から r px 以内の画素"""
    out = set()
    for x, y in pts:
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                out.add((x + dx, y + dy))
    return out


def inner(pts, r):
    """pts の中で、まわり r px がすべて pts の画素"""
    return {(x, y) for x, y in pts if all((x + dx, y + dy) in pts for dx in range(-r, r + 1) for dy in range(-r, r + 1))}


def painted(rows, r, c, dx, dy):
    out = set()
    for y in range(r * CELL, (r + 1) * CELL):
        line = rows[y]
        for x in range(c * CELL, (c + 1) * CELL):
            if tuple(line[x * 3:x * 3 + 3]) != TRANSPARENT:
                out.add((x - c * CELL + dx, y - r * CELL + dy))
    return out


def main(src):
    errors, sheets, cache = [], {}, {}
    checked = 0
    objs = [o for o in read_dats(src) if o["name"].startswith("ami_embankment_")]
    if not objs:
        sys.exit("[check_embankment] 盛土の dat が無い")
    for o in objs:
        side = o["name"].rsplit("_", 1)[1]
        keys = o["keys"]
        for key, value in keys.items():
            spec = shape_of(key)
            if spec is None:
                continue
            cell = cell_of(value)
            if cell is None:
                errors.append(f"{o['name']}: {key} がセルを指していない（{value}）")
                continue
            sheet, r, c = cell
            if sheet not in sheets:
                path = os.path.join(src, sheet + ".png")
                _, h, _ = read_rows(path, 1)
                sheets[sheet] = read_rows(path, h)[2]
            parts = value.split(",")
            dx, dy = (int(parts[1]), int(parts[2])) if len(parts) >= 3 else (0, 0)
            got = painted(sheets[sheet], r, c, dx, dy)
            ck = (spec, side)
            if ck not in cache:
                exp = expected(spec[0], side, *spec[1:])
                cache[ck] = (near(exp, TOL), inner(exp, TOL))
            loose, core = cache[ck]
            outside = len(got - loose)
            missing = len(core - got)
            checked += 1
            if outside > MAX_BAD or missing > MAX_BAD:
                errors.append(f"{o['name']}: {key} のセル {fmt(cell)} が形 {spec[0]}（{side}）と合わない"
                              f"（期待の外に塗った画素 {outside}、期待の内側で塗られていない画素 {missing}）")
        # 雪の絵は夏の絵の EMBANKMENT_SNOW_ROWS（4）行下
        for key, value in keys.items():
            if shape_of(key) and key.endswith("[0]"):
                snow = keys.get(key[:-3] + "[1]")
                a, b = cell_of(value), cell_of(snow or "")
                if b is None or a is None or (b[0], b[1] - 4, b[2]) != a:
                    errors.append(f"{o['name']}: {key[:-3]}[1] が夏の絵 {fmt(a) if a else value} の 4 行下を指していない（{snow}）")
    for e in errors:
        print(e)
    if errors:
        sys.exit(f"[check_embankment] {len(errors)} 件")
    print(f"[check_embankment] 盛土の絵 {checked} 枚の形と割り当てが合う")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
