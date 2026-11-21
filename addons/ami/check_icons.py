"""アイコン・カーソルの参照先の検査（#97）。check.sh が呼ぶ。Python の標準ライブラリだけで動く（CI に numpy・Blender は無い）。

    python -X utf8 check_icons.py [src のディレクトリ]

#25 で、次の 1〜3 の誤りを目で見て見つけた。同じ種類の誤りを機械的に見つける（4 は #141 で足した）。

1. セルの重なり: 各 dat の icon・cursor が指すセルを、ほかの dat のキーや、同じ dat のほかのキーが指していないか。
   blender/icons.py はセルを空けてから書くので、重なると相手の絵が消えるか、2 つの物が同じアイコンになる
   （#25 の前、壁だけの twin が back の版と同じセルを指し、back と同じアイコンが出ていた）
2. 絵の有無: icon のセルの左上 32px がすべて塗られ、cursor のセルに絵があるか（#25 の前、ami_wall_road_center のカーソルが空だった）
3. 背景色: waytype の違う物どうしで、アイコンの背景の色相が近すぎないか。同じメニューに並ぶ物を色で見分けるため
   （#25 の前、路面軌道のアイコンが線路と同じ緑だった）。icons.py の色の表（WAY_BG）は読まず、描かれた画素だけで比べる
   （表ごと元に戻したときにも落ちるように）
4. 別のシートの絵: ほかのシートの絵から作ったアイコン・カーソル（トンネルのアイコンは中の way の絵）が、今の絵のシートから作られているか。
   icons.py が絵のセルの sha256 を <シート>.icon_sources.txt に控え、ここで今のシートと比べる（#141。#89 で線路のシートを描き直した後、
   在来線のトンネルのアイコンが古い線路の絵のままだった）。トンネルには控えが無ければならない

意図して共有・借用するものは、下の SHARE_SUFFIX と BG_BORROW に書く。
"""
import glob
import hashlib
import os
import re
import struct
import sys
import zlib

from ex_graft import DONOR_SUFFIX as SHARE_SUFFIX

CELL = 256
ICON = 32
TRANSPARENT = (231, 255, 255)
REF = re.compile(r"^>?\s*([A-Za-z0-9_\-]+)\.(\d+)\.(\d+)\s*(?:,|$)")

# 意図して共有するもの: 名前が <物><SHARE_SUFFIX> の物は、<物> と同じキーで同じセルを指してよい
# （ex_donors.dat の分岐の追加画像の提供用の物。SHARE_SUFFIX は ex_graft.py の DONOR_SUFFIX。icons.py は ex_donors.dat を書かず、
# 提供用の物のアイコン・カーソルは <物> のセルをそのまま使う）

# 背景色を、dat の waytype でなく別の種類の色で描く物（名前 → 色を借りる waytype）。理由はそれぞれの行に書く
BG_BORROW = {
    "ami_pier_rail": "track",  # 橋脚は tram_track の way だが、線路の下に立てる物なので線路の色（#25）
    "ami_pier_rail_gate": "track",  # 同上
    "ami_pier_road": "road",  # 道路の下に立てる橋脚なので道路の色（#25）
    "ami_sidewalk": "road",  # 歩道は water の way だが、道路の脇に敷く物なので道路の色（#25）
    **{_n: "road" for _n in ("ami_sidewalk_asphalt", "ami_sidewalk_brick", "ami_sidewalk_tile", "ami_sidewalk_elev",
                             "ami_wall_sidewalk_single", "ami_wall_sidewalk_back", "ami_wall_sidewalk_front")},  # 同上（歩道の種類・高架・柵。#119）
    **{_n: "road" for _n in ("ami_sidewalk_pole_back", "ami_sidewalk_pole_front", "ami_wall_sidewalk_back_pole",
                             "ami_wall_sidewalk_front_pole")},  # 同上（電柱と柵つきの電柱。#120）
}
HUE_MIN_DIFF = 20  # waytype の違う物どうしの、背景の色相の差の下限（度）。今の値は線路 149〜150・路面軌道 44・道路 219・高速道路 230・モノレール 285、運河 186。
# 組は dat の waytype なので、道路と高速道路（どちらも road）は比べない
SATURATION_MIN = 60  # 色相を見る画素の、RGB の最大と最小の差の下限（文字の白・影・絵の灰色を除く）


# ---------------------------------------------------------------- dat
def read_dats(src):
    """src の dat を読み、物ごとに {name, obj, waytype, file, keys: {キー: 値}} を返す。1 つのファイルに --- で分けて複数の物が入ってよい"""
    objs = []
    for path in sorted(glob.glob(os.path.join(src, "*.dat"))):
        block = {}
        with open(path, encoding="utf8") as f:
            lines = f.read().splitlines()
        for line in lines + ["---"]:
            line = line.strip()
            if line.startswith("-"):
                if block:
                    objs.append(dict(name=block.get("name", "?"), obj=block.get("obj"), waytype=block.get("waytype"),
                                     file=os.path.basename(path), keys=block))
                block = {}
                continue
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            block[k.strip().lower()] = v.strip()
    return objs


def cell_of(value):
    m = REF.match(value)
    return (m.group(1), int(m.group(2)), int(m.group(3))) if m else None


def fmt(cell):
    return "%s.%d.%d" % cell


# ---------------------------------------------------------------- png（8bit RGB・インターレースなしだけ）
def read_rows(path, nrows):
    """PNG の上から nrows 行を、行ごとの bytearray（RGB）で返す。幅・高さも返す"""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"PNG でない: {path}")
    pos, idat, w, h = 8, [], 0, 0
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if (depth, ctype, interlace) != (8, 2, 0):
                raise SystemExit(f"8bit RGB・インターレースなしの PNG でない（読めない）: {path} depth={depth} color={ctype} interlace={interlace}")
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
    nrows = min(nrows, h)
    stride = w * 3
    raw = zlib.decompressobj().decompress(b"".join(idat), (stride + 1) * nrows)
    prev = bytearray(stride)
    rows = []
    for y in range(nrows):
        off = y * (stride + 1)
        f = raw[off]
        line = bytearray(raw[off + 1:off + 1 + stride])
        if f == 1:  # Sub
            for i in range(3, stride):
                line[i] = (line[i] + line[i - 3]) & 255
        elif f == 2:  # Up
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif f == 3:  # Average
            for i in range(stride):
                line[i] = (line[i] + ((line[i - 3] if i >= 3 else 0) + prev[i]) // 2) & 255
        elif f == 4:  # Paeth
            for i in range(stride):
                a = line[i - 3] if i >= 3 else 0
                b = prev[i]
                c = prev[i - 3] if i >= 3 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        elif f != 0:
            raise SystemExit(f"PNG の行のフィルタが分からない: {path} 行 {y} フィルタ {f}")
        rows.append(line)
        prev = line
    return w, h, rows


def pixel(rows, x, y):
    i = x * 3
    return tuple(rows[y][i:i + 3])


def hue(rgb):
    r, g, b = rgb
    mx, mn = max(rgb), min(rgb)
    if mx - mn < SATURATION_MIN:
        return None
    d = mx - mn
    if mx == r:
        h = ((g - b) / d) % 6
    elif mx == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return h * 60


def background_hue(rows, r, c):
    """アイコン（セルの左上 32px）の背景の色相。背景は左上から右下へのグラデーションなので、上の行と左の列（下の帯より上）の、
    彩りのある画素の色相を 10 度ごとに数え、一番多い所の平均を取る（角に絵や稲妻がかぶる物がある）"""
    x0, y0 = c * CELL, r * CELL
    pts = [(x0 + x, y0) for x in range(ICON)] + [(x0, y0 + y) for y in range(1, ICON - 7)]
    hs = [h for h in (hue(pixel(rows, x, y)) for x, y in pts) if h is not None]
    if not hs:
        return None
    bins = {}
    for h in hs:
        bins.setdefault(int(h // 10), []).append(h)
    best = max(bins.values(), key=len)
    return sum(best) / len(best)


def hue_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


# ---------------------------------------------------------------- 検査
# 道具が無く、アイコン・カーソルを持たない物の種類（踏切は way を交わらせると本体が置く。#111）
NO_TOOL_OBJS = {"crossing"}


STAMP_SUFFIX = ".icon_sources.txt"  # blender/icons.py と同じ


def source_digest(rows, row, col):
    """read_rows の行（RGB）から、セル (row, col) の画素を上の行から並べた sha256（blender/icons.py の cell_digest と同じ並び）"""
    h = hashlib.sha256()
    for y in range(row * CELL, (row + 1) * CELL):
        h.update(bytes(rows[y][col * CELL * 3:(col + 1) * CELL * 3]))
    return h.hexdigest()


def check_sources(src, objs):
    """icons.py が <シート>.icon_sources.txt に控えた、ほかのシートの絵のセルの sha256 を、今のシートと比べる。
    控えが要る物（expected_sources）に控えがあり、控えのセルが今の dat の指すセルか、も見る"""
    errors, cache, stamped = [], {}, {}
    names = {o["name"] for o in objs}
    for path in sorted(glob.glob(os.path.join(src, "*" + STAMP_SUFFIX))):
        stamp = os.path.basename(path)
        for line in open(path, encoding="utf8"):
            if line.startswith("#") or not line.strip():
                continue
            t = line.split()
            if len(t) != 6 or t[1] not in ("icon", "cursor") or not t[3].isdigit() or not t[4].isdigit():
                errors.append(f"{stamp}: 控えの行の形が違う（物 icon|cursor 絵のシート 行 列 sha256）: {line.strip()}")
                continue
            name, kind, sheet, row, col, digest = t[0], t[1], t[2], int(t[3]), int(t[4]), t[5]
            if name not in names:
                errors.append(f"{stamp}: dat に無い物 {name} の行がある。blender/icons.py を流し直す")
                continue
            stamped.setdefault((name, kind), set()).add((sheet, row, col))
            need = (row + 1) * CELL
            if sheet not in cache or len(cache[sheet][2]) < need:
                png = os.path.join(src, sheet + ".png")
                if not os.path.exists(png):
                    errors.append(f"{stamp}: {name} の絵のシート {sheet}.png が無い")
                    continue
                cache[sheet] = read_rows(png, need)
            w, h, rows = cache[sheet]
            if h < need or w < (col + 1) * CELL:
                errors.append(f"{stamp}: {name} の絵のセル {sheet}.{row}.{col} がシート（{w}x{h}）の外")
            elif source_digest(rows, row, col) != digest:
                errors.append(f"{name} の {kind} が、今の {sheet} のセル {row}.{col} から作られていない。"
                              f"絵のシートを描き直したら blender/icons.py を流し直す")
    for (name, kind), cells in expected_sources(objs).items():
        got = stamped.get((name, kind))
        if not got:
            errors.append(f"{name}: {kind} を作ったほかのシートの絵の控え（<シート>{STAMP_SUFFIX}）が無い。blender/icons.py を流し直す")
        elif got != cells:
            errors.append(f"{name}: {kind} の控えのセル {sorted(got)} が、今の dat の指す絵のセル {sorted(cells)} と合わない。"
                          f"blender/icons.py を流し直す")
    return errors


TUNNEL_PICTURE_KEYS = ("image[ns][0]", "frontimage[ns][0]")  # blender/icons.py の picture_keys(way) と同じ
# blender/icons.py の picture_keys(壁・架線) と同じ候補の組（近い斜めの twin は直線を持たないので、斜めの組になる）
WAYOBJ_PICTURE_GROUPS = [[f"back{k}", f"front{k}"] for k in ("image[ns]", "image[s]", "image[n]")] +     [["backdiagonal[nw]", "frontdiagonal[nw]", "backdiagonal[se]", "frontdiagonal[se]"]]


def expected_sources(objs):
    """ほかのシートの絵から作るので控えが要る (物, icon|cursor) → 絵のセルの集合（控えのセルと等しくなければならない）。
    トンネルの icon は中の way の直線のセル。way-object（壁・架線）は、icons.py と同じ候補の組のうち dat にある最初の組で、
    そのセルが icon・cursor と別のシートにあるもの（twin の壁は front の版の斜め）"""
    by_name = {o["name"]: o for o in objs}
    out = {}
    for o in objs:
        keys = o["keys"]
        if o["obj"] in NO_TOOL_OBJS or "icon" not in keys or "cursor" not in keys:
            continue
        if o["obj"] == "tunnel":
            way = by_name.get(keys.get("way"))
            out[(o["name"], "icon")] = {cell_of(way["keys"][k]) for k in TUNNEL_PICTURE_KEYS if way and k in way["keys"]} - {None}
        elif o["obj"] == "way-object":
            group = next((g for g in WAYOBJ_PICTURE_GROUPS if any(k in keys for k in g)), [])
            cells = {cell_of(keys[k]) for k in group if k in keys} - {None}
            for kind in ("icon", "cursor"):
                own = cell_of(keys[kind])
                other = {c for c in cells if own and c[0] != own[0]}
                if other:
                    out[(o["name"], kind)] = other
    return out


def main(src):
    objs = read_dats(src)
    errors = []
    users = {}  # セル → [(名前, キー)]
    for o in objs:
        for k, v in o["keys"].items():
            cell = cell_of(v)
            if cell:
                users.setdefault(cell, []).append((o["name"], k))

    def base_of(name):
        return name[:-len(SHARE_SUFFIX)] if name.endswith(SHARE_SUFFIX) else name

    # 1. セルの重なり（セルごとに 1 件）。共有してよいのは、<物> と <物><SHARE_SUFFIX> の同じキーだけ
    targets = []  # (物, キー, セル)
    reported = set()
    for o in objs:
        if o["obj"] in NO_TOOL_OBJS:
            continue
        for key in ("icon", "cursor"):
            if key not in o["keys"]:
                errors.append(f"{o['name']}（{o['file']}）: {key} が無い")
                continue
            cell = cell_of(o["keys"][key])
            if not cell:
                errors.append(f"{o['name']}（{o['file']}）: {key} の値がセルの参照でない: {o['keys'][key]}")
                continue
            targets.append((o, key, cell))
            if cell in reported or len({(base_of(n), k) for n, k in users[cell]}) == 1:
                continue
            reported.add(cell)
            who = "・".join(f"{n} の {k}" for n, k in users[cell][:5]) + ("ほか" if len(users[cell]) > 5 else "")
            errors.append(f"セル {fmt(cell)} を {len(users[cell])} か所が指している（{who}）。"
                          f"icon・cursor のセルはその物だけが指す（icons.py が書くと、相手の絵が消えるか、同じアイコンになる）")

    # 2. 絵の有無（シートごとに、要る行までだけ読む）
    need = {}
    for _, _, (sheet, r, _) in targets:
        need[sheet] = max(need.get(sheet, 0), (r + 1) * CELL)
    sheets = {}
    for sheet, nrows in need.items():
        path = os.path.join(src, sheet + ".png")
        if not os.path.exists(path):
            errors.append(f"シートが無い: {sheet}.png")
            continue
        sheets[sheet] = read_rows(path, nrows)
    hues = {}  # 名前 → (色相, 色を比べる waytype)
    for o, key, cell in targets:
        sheet, r, c = cell
        if sheet not in sheets:
            continue
        w, h, rows = sheets[sheet]
        if (c + 1) * CELL > w or (r + 1) * CELL > h:
            errors.append(f"{o['name']}: {key} のセル {fmt(cell)} がシート（{w}x{h}）の外")
            continue
        x0, y0 = c * CELL, r * CELL
        if key == "icon":
            empty = sum(1 for y in range(ICON) for x in range(ICON) if pixel(rows, x0 + x, y0 + y) == TRANSPARENT)
            if empty:
                errors.append(f"{o['name']}: icon のセル {fmt(cell)} の左上 {ICON}px に、透明な画素が {empty} ある（アイコンが描かれていない）")
                continue
            hh = background_hue(rows, r, c)
            if hh is None:
                errors.append(f"{o['name']}: icon のセル {fmt(cell)} の背景に色が無い")
                continue
            hues[o["name"]] = (hh, BG_BORROW.get(o["name"], o["waytype"]))
        else:
            if all(pixel(rows, x0 + x, y0 + y) == TRANSPARENT for y in range(CELL) for x in range(CELL)):
                errors.append(f"{o['name']}: cursor のセル {fmt(cell)} が空")

    # 3. 背景色（waytype の違う物どうしで、色相が近すぎないか。組ごとに 1 件にまとめる）
    names = sorted(hues)
    clash = {}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            (ha, wa), (hb, wb) = hues[a], hues[b]
            if wa != wb and hue_diff(ha, hb) < HUE_MIN_DIFF:
                clash.setdefault(tuple(sorted((wa, wb))), []).append((a, ha, b, hb))
    for (wa, wb), pairs in sorted(clash.items()):
        # 例は、借りた色（BG_BORROW）でない物どうしの組を先に出す
        a, ha, b, hb = min(pairs, key=lambda p: (p[0] in BG_BORROW) + (p[2] in BG_BORROW))
        errors.append(f"waytype {wa} と {wb} のアイコンの背景の色相が近い（{len(pairs)} 組。例: {a} {ha:.0f} 度・{b} {hb:.0f} 度。"
                      f"差の下限 {HUE_MIN_DIFF} 度）。意図して借りる色なら check_icons.py の BG_BORROW に書く")

    # 4. ほかのシートの絵から作ったアイコン・カーソルが、今の絵のシートから作られているか（#141）
    errors += check_sources(src, objs)

    n = len(objs)
    if errors:
        for e in errors:
            print(e)
        print(f"{'::error::' if os.environ.get('GITHUB_ACTIONS') else ''}アイコン・カーソルの検査で {len(errors)} 件（{n} 物）")
        return 1
    print(f"アイコン・カーソルの検査は通った（{n} 物・{len(need)} シート）")
    return 0


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "src")))
