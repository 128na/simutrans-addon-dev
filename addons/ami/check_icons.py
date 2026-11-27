"""アイコン・カーソルの参照先の検査（#97）。check.sh が呼ぶ。Python の標準ライブラリだけで動く（CI に numpy・Blender は無い）。

    python -X utf8 check_icons.py [src のディレクトリ]

#25 で、次の 1〜3 の誤りを目で見て見つけた。同じ種類の誤りを機械的に見つける（4 は #141、5 は #287、6 は #330 で足した）。

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

5. カーソルの offset: cursor= の offset（`cell,x,y` の x,y）が、同じ dat のほかの絵のキー（image・backimage など）の offset と同じか（#287）。
   置く前のカーソルはタイルの上に出る絵で、offset が絵と違うとタイルからずれる。ゲームでは撮れないので、ここで守る
   （#282 の前、車庫・操車場・停留所・道路標識の cursor= に offset が無く、ずれていた）。展開後の dat を全部読むので、way 系も同じに見る

6. 仮の絵: icon・cursor のセルが、icons.py が書いた物のままか（#330）。描画（sheetlib の render_icon）はアイコンのセルに仮の絵を描き、
   icons.py が描き直す。icons.py が書いたセルの sha256 を <シート>.icon_cells.txt に控え、ここで今のシートと比べる。
   控えが無いか違えば、icons.py を流さずに描いたシート（#318 で ami_mark_junction4_c が仮の「M」のアイコンのままマージされた）。
   仮の絵は背景色も字の置き方も icons.py の絵に近く（線路・道路・高速道路の背景色は同じ）、画素からは見分けられないので、控えで見る

意図して共有・借用するものは、下の SHARE_SUFFIX と BG_BORROW に書く。意図して offset が違うものは CURSOR_OFFSET_ALLOW に書く。
"""
import glob
import os
import re
import sys

from check_lib import CELL, SRC, TRANSPARENT, cell_digest, cell_of, drop_missing, fmt, offset_of, read_dats, read_rows, size_error
from ex_graft import DONOR_SUFFIX as SHARE_SUFFIX

ICON = 32  # アイコンは大きさによらず 32px（pak256 の menuconf.tab も icon_width = 32）

# cursor= の offset が絵の offset と違ってよい物（名前 → 理由）。今は無い（#287）。足すときは理由を書く
CURSOR_OFFSET_ALLOW = {}

# 意図して共有するもの: 名前が <物><SHARE_SUFFIX> の物は、<物> と同じキーで同じセルを指してよい
# （ex_donors.dat の分岐の追加画像の提供用の物。SHARE_SUFFIX は ex_graft.py の DONOR_SUFFIX。icons.py は ex_donors.dat を書かず、
# 提供用の物のアイコン・カーソルは <物> のセルをそのまま使う）

# 背景色を、dat の waytype でなく別の種類の色で描く物（名前 → 色を借りる waytype）。理由はそれぞれの行に書く
BG_BORROW = {
    "ami_pier_rail": "track",  # 橋脚は tram_track の way だが、線路の下に立てる物なので線路の色（#25）
    "ami_pier_rail_gate": "track",  # 同上
    "ami_pier_rail_old": "track",  # 旧描画位置（#26）の橋脚も同じ
    "ami_pier_rail_old_gate": "track",
    "ami_pier_road": "road",  # 道路の下に立てる橋脚なので道路の色（#25）
    "ami_rail_turntable": "track",  # 転車台は iss と同じく road の way だが、線路につなぐ物なので線路の色（#314）
    "ami_sidewalk": "road",  # 歩道は water の way だが、道路の脇に敷く物なので道路の色（#25）
    **{_n: "road" for _n in ("ami_sidewalk_asphalt", "ami_sidewalk_brick", "ami_sidewalk_tile", "ami_sidewalk_elev",
                             "ami_wall_sidewalk_single", "ami_wall_sidewalk_back", "ami_wall_sidewalk_front")},  # 同上（歩道の種類・高架・柵。#119）
    **{_n: "road" for _n in ("ami_sidewalk_pole_back", "ami_sidewalk_pole_front", "ami_wall_sidewalk_back_pole",
                             "ami_wall_sidewalk_front_pole")},  # 同上（電柱と柵つきの電柱。#120）
}
HUE_MIN_DIFF = 20  # waytype の違う物どうしの、背景の色相の差の下限（度）。今の値は線路 149〜150・路面軌道 44・道路 219・高速道路 230・モノレール 285、運河 186、狭軌 11。
# 組は dat の waytype なので、道路と高速道路（どちらも road）は比べない
SATURATION_MIN = 60  # 色相を見る画素の、RGB の最大と最小の差の下限（文字の白・影・絵の灰色を除く）


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


def check_sources(src, objs, skipped_names=()):
    """icons.py が <シート>.icon_sources.txt に控えた、ほかのシートの絵のセルの sha256 を、今のシートと比べる。
    控えが要る物（expected_sources）に控えがあり、控えのセルが今の dat の指すセルか、も見る。
    skipped_names は、シートが無くて飛ばした物（CHECK_SKIP_MISSING）の名前。その控えの行は見ない"""
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
            if name in skipped_names:
                continue
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
            elif cell_digest(rows, row, col) != digest:
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


CELLS_SUFFIX = ".icon_cells.txt"  # blender/icons.py と同じ


def check_written(src, targets, skipped_names=()):
    """icons.py が <シート>.icon_cells.txt に控えた、書いたアイコン・カーソルのセルの sha256 を、今のシートと比べる（#330）。
    targets は (物, キー, セル) の並び。どの物にも控えの行があり、行のセルが dat の指すセルで、sha256 が今のセルと同じでなければならない。
    控えの無い物・違う物は、icons.py を流さずに描いたシート（render_icon の仮のアイコン・仮のカーソルのまま）か、描き直した後に流し忘れた物。
    提供用の物（<物><SHARE_SUFFIX>。icons.py は書かない）は <物> の行で見る"""
    errors, rows_of, cache = [], {}, {}
    for path in sorted(glob.glob(os.path.join(src, "*" + CELLS_SUFFIX))):
        sheet = os.path.basename(path)[:-len(CELLS_SUFFIX)]
        for line in open(path, encoding="utf8"):
            if line.startswith("#") or not line.strip():
                continue
            t = line.split()
            if len(t) != 5 or t[1] not in ("icon", "cursor") or not t[2].isdigit() or not t[3].isdigit():
                errors.append(f"{sheet}{CELLS_SUFFIX}: 控えの行の形が違う（物 icon|cursor 行 列 sha256）: {line.strip()}")
                continue
            if (t[0], t[1]) in rows_of:  # セルが別のシートへ移った後、前のシートを流し直していない（icons.py の全部の流しで消える）
                errors.append(f"{t[0]} の {t[1]} の行が {rows_of[(t[0], t[1])][0]}{CELLS_SUFFIX} と {sheet}{CELLS_SUFFIX} の両方にある。"
                              f"blender/icons.py（全部）を流し直す")
                continue
            rows_of[(t[0], t[1])] = (sheet, int(t[2]), int(t[3]), t[4])
    want = {}
    for o, key, cell in targets:
        name = o["name"][:-len(SHARE_SUFFIX)] if o["name"].endswith(SHARE_SUFFIX) else o["name"]
        want[(name, key)] = cell
    for (name, key), (sheet, r, c, _) in sorted(rows_of.items()):
        if (name, key) not in want and name not in skipped_names:
            errors.append(f"{sheet}{CELLS_SUFFIX}: dat に無い物 {name} の {key} の行がある。blender/icons.py を流し直す")
    for (name, key), cell in sorted(want.items()):
        got = rows_of.get((name, key))
        if got is None:
            errors.append(f"{name}: {key} を icons.py が書いた控え（<シート>{CELLS_SUFFIX}）が無い。描画の仮の絵のままか、"
                          f"icons.py を流していない（順番は、描く → icons.py → check.sh。render.py は描いた対象のシートの控えしか書かない）。"
                          f"blender -b --factory-startup --python blender/icons.py -- {cell[0]}")
            continue
        sheet, r, c, digest = got
        if (sheet, r, c) != cell:
            errors.append(f"{name}: {key} の控えのセル {fmt((sheet, r, c))} が、今の dat の指すセル {fmt(cell)} と違う。blender/icons.py を流し直す")
            continue
        need = (r + 1) * CELL
        if sheet not in cache or len(cache[sheet][2]) < need:
            png = os.path.join(src, sheet + ".png")
            if not os.path.exists(png):
                continue  # シートが無いことは 2 で数える
            cache[sheet] = read_rows(png, need)
        w, h, rows = cache[sheet]
        if h < need or w < (c + 1) * CELL:
            continue  # シートの外は 2 で数える
        if cell_digest(rows, r, c) != digest:
            errors.append(f"{name}: {key} のセル {fmt(cell)} が、icons.py が書いた物と違う（描き直して描画の仮の絵に戻ったか、"
                          f"手で書き換えた）。blender -b --factory-startup --python blender/icons.py -- {sheet}")
    return errors


def check_cursor_offsets(objs):
    """cursor= の offset が、同じ dat のほかの絵のキー（icon 以外のセルの参照）の offset と同じか（#287）"""
    errors = []
    for o in objs:
        cursor = o["keys"].get("cursor")
        if cursor is None or not cell_of(cursor) or o["name"] in CURSOR_OFFSET_ALLOW:
            continue
        want = offset_of(cursor)
        got = {}
        for k, v in o["keys"].items():
            if k not in ("icon", "cursor") and cell_of(v):
                got.setdefault(offset_of(v), []).append(k)
        for off, keys in sorted(got.items(), key=str):
            if off != want:
                shown = "（無し）" if want is None else f"{want}"
                errors.append(f"{o['name']}（{o['file']}）: cursor の offset {shown} が、絵（{keys[0]} ほか {len(keys)} キー）の offset {off} と違う。"
                              f"置く前のカーソルがタイルからずれる。意図したものなら check_icons.py の CURSOR_OFFSET_ALLOW に理由を書く")
                break
    return errors


def main(src):
    all_objs = read_dats(src)
    objs, skipped = drop_missing(src, all_objs)
    skipped_names = {o["name"] for o in all_objs} - {o["name"] for o in objs}
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
        # 盛土の建物（type=cur。#372）は、道具でなく建物の一覧から選んで建てるので、アイコン・カーソルを持たない
        if o["obj"] in NO_TOOL_OBJS or (o["obj"] == "building" and o["keys"].get("type") == "cur"):
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
        bad = size_error(path, *sheets[sheet][:2])
        if bad:
            errors.append(bad)
            del sheets[sheet]
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
    errors += check_sources(src, objs, skipped_names)

    # 5. cursor= の offset が絵と同じか（#287。シートの有無に関わらないので、飛ばした物も含めた全部を見る）
    errors += check_cursor_offsets(all_objs)

    # 6. アイコン・カーソルのセルが、icons.py が書いた物のままか（#330。描画の仮の絵のままの物を見つける）
    errors += check_written(src, targets, skipped_names)

    n = len(objs)
    if skipped and not n:  # 絵のある物が 1 つも無い（dat の綴りやシートの名前が崩れて、全部飛ばされた）なら、通さない
        errors.append(f"CHECK_SKIP_MISSING で、シートのある物が 1 つも残らなかった（{skipped} 物を飛ばした）")
    if errors:
        for e in errors:
            print(e)
        print(f"{'::error::' if os.environ.get('GITHUB_ACTIONS') else ''}アイコン・カーソルの検査で {len(errors)} 件（{n} 物）")
        return 1
    gone = sorted(skipped_names)
    note = f"。シートの無い {skipped} 物は飛ばした（{' '.join(gone[:4])}{'…' if len(gone) > 4 else ''}）" if skipped else ""
    print(f"アイコン・カーソルの検査は通った（{n} 物・{len(need)} シート{note}）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else SRC))
