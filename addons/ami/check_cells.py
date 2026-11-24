"""dat が空のセル（全部透明）を指していないかの検査（#241）。check.sh が呼ぶ。Python の標準ライブラリだけで動く（CI に numpy・Blender は無い）。

    python -X utf8 check_cells.py [src のディレクトリ]
    python -X utf8 check_cells.py --self-test

dat の絵のキー（image・imageup・diagonal・frontimage・backimage・openimage など、値が `<シート>.<行>.<列>[,x,y]` の形のもの）が指すセルを、
シートの PNG で読み、全部の画素が透明色（231,255,255）なら失敗にする。セルを描き忘れたり、dat の指すセルがずれたりすると、
その向き・坂の絵が空になって本体で見えなくなる（#217・#227 で、設定が 2 か所に分かれていて片方を直し忘れた取りこぼし）。
icon・cursor は check_icons.py が見るので、ここでは読まない。値が `-`（絵なし。dat が意図して空にしたもの）はセルの参照でないので対象外。
PNG の読み方は check_icons.py と同じ（Blender を使わない）。

ほとんどの物は、描かない向き・坂・層を空のセルに向ける（壁・架線は奥の層か手前の層だけ、路面表示の way は使わない向きなど。意図して空）ので、
「空のセルを指してはならない」とは言えない。そこで、空のセルを指す（層を除いた）絵の種類を物ごとに check_cells.allow.txt に控え、控えに無い物が新しく
空のセルを指したら失敗にする（向きの追加・セルのずれ・描き忘れ）。控えにあるのに空でなくなったものも失敗にする（控えを古いまま残さない）。
意図して空にしたものを足す・絵を描いて空でなくなったものを外すときは、`python -X utf8 check_cells.py --update` で控えを書き直し、差分を読んでコミットする。
"""
import multiprocessing
import os
import re
import sys
import tempfile

from check_icons import CELL, TRANSPARENT, cell_of, fmt, read_dats, read_rows

ALLOW_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_cells.allow.txt")

# セルの参照を値に持たないキー（check_icons.py が別に見るもの）
SKIP_KEYS = ("icon", "cursor")

EMPTY_ROW = bytes(TRANSPARENT) * CELL


PICTURE_KEY = re.compile(r"^[a-z_]*(image|pillar|ramp|start|diagonal)[a-z_0-9]*(\[|$)")  # 絵を指すキー（値は参照か `-`）


def group_key(key):
    """控えの単位のキー。層（back・front）は残す（片方の層だけ空にした直し忘れを拾うため）。季節の添字（末尾の [0]・[1]。添字が 2 つ以上あるキーだけ）は畳む"""
    if key.count("[") >= 2:
        key = re.sub(r"\[[01]\]$", "", key)
    return key


def empty_cells(task):
    """(シートの PNG のパス, 行の数, [(行, 列)]) → {(行, 列): 空か}。シートごとに別のプロセスで呼ぶ"""
    path, nrows, cells = task
    w, h, rows = read_rows(path, nrows)
    out = {}
    for r, c in cells:
        if (c + 1) * CELL > w or (r + 1) * CELL > h:
            out[(r, c)] = None
        else:
            out[(r, c)] = all(bytes(rows[y][c * CELL * 3:(c + 1) * CELL * 3]) == EMPTY_ROW for y in range(r * CELL, (r + 1) * CELL))
    return out


def scan(src, jobs=None):
    """src の dat が指すセルを読み、(エラー, {物: {空の絵の種類}}, 調べたセルの数, 調べた参照の数) を返す。

    空の絵の種類は、同じ物の同じキー（層は別。季節の添字 [0]・[1] は畳む）が、全部空のセルを指しているもの。
    奥の層だけ・手前の層だけを描く物（壁・架線・柱・踏切の手前の絵など）は、描かない層が空のセルを指すので、控えに入る"""
    objs = read_dats(src)
    errors, refs = [], 0
    uses = {}  # セル → [(物, ファイル, キー)]
    for o in objs:
        for k, v in o["keys"].items():
            if k in SKIP_KEYS:
                continue
            cell = cell_of(v)
            if cell:
                refs += 1
                uses.setdefault(cell, []).append((o["name"], o["file"], k))
            elif PICTURE_KEY.match(k) and v != "-" and not v.isdigit():  # pillar_distance などの数値は絵でない
                errors.append(f"{o['name']}（{o['file']}）: {k} の値がセルの参照でも `-` でもない（検査の対象外になる）: {v}")
    if not refs:
        errors.append(f"{src} に、セルを指す絵のキーが 1 つも無い（dat が読めていない）")
    per_sheet = {}
    for sheet, r, c in uses:
        per_sheet.setdefault(sheet, []).append((r, c))
    tasks, sheets = [], []
    for sheet, cells in sorted(per_sheet.items()):
        path = os.path.join(src, sheet + ".png")
        if not os.path.exists(path):
            errors.append(f"シートが無い: {sheet}.png（{who([u for cell, us in uses.items() if cell[0] == sheet for u in us])}）")
            continue
        tasks.append((path, (max(r for r, _ in cells) + 1) * CELL, cells))
        sheets.append(sheet)
    if jobs is None:
        jobs = min(os.cpu_count() or 1, 8)
    if jobs > 1 and len(tasks) > 1:
        with multiprocessing.Pool(jobs) as pool:
            results = pool.map(empty_cells, tasks, chunksize=1)
    else:
        results = [empty_cells(t) for t in tasks]
    empty = {}
    for sheet, res in zip(sheets, results):
        for (r, c), e in res.items():
            cell = (sheet, r, c)
            if e is None:
                errors.append(f"セル {fmt(cell)} がシートの外（{who(uses[cell])}）")
            else:
                empty[cell] = e
    # 物ごと・キー（季節を畳む）ごとに、指すセルが全部空のものを探す
    groups = {}
    for cell, us in uses.items():
        for name, f, k in us:
            groups.setdefault((name, f, group_key(k)), []).append((cell, k))
    empties = {}
    for (name, f, g), items in groups.items():
        if all(empty.get(cell) for cell, _ in items):
            empties.setdefault(name, set()).add(g)
    return errors, empties, len(uses), refs


def read_allow(path):
    allow = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf8"):
            if line.strip() and not line.startswith("#") and ": " in line:
                name, gs = line.rstrip("\n").split(": ", 1)
                allow[name] = set(gs.split())
    return allow


def write_allow(path, empties):
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write("# check_cells.py が許す、空のセルを指す絵の種類（物: 層を除いた絵の種類…）。意図して描かない向き・坂・層。\n"
                "# python -X utf8 check_cells.py --update で書き直し、差分を読んでからコミットする（手で直さない）。\n")
        for name in sorted(empties):
            f.write(f"{name}: {' '.join(sorted(empties[name]))}\n")


def compare(empties, allow):
    errors = []
    for name in sorted(empties):
        new = empties[name] - allow.get(name, set())
        if new:
            errors.append(f"{name}: 空のセル（全部透明）を指す絵が控え（check_cells.allow.txt）に無い（{len(new)} 件）: {head(sorted(new))}。"
                          f"絵を描き忘れたか、dat の指すセルがずれている。意図して空なら --update で控えに足す")
    for name in sorted(allow):
        gone = allow[name] - empties.get(name, set())
        if gone:
            errors.append(f"{name}: 控えにあるが、もう空のセルを指していない（{len(gone)} 件）: {head(sorted(gone))}。--update で控えから外す")
    return errors


def head(items, n=6):
    return " ".join(items[:n]) + (f" ほか {len(items) - n} 件" if len(items) > n else "")


def who(users):
    s = "・".join(f"{n} の {k}（{f}）" for n, f, k in users[:4])
    return s + (f"ほか {len(users) - 4} か所" if len(users) > 4 else "")


# ---------------------------------------------------------------- 自己検査
def write_png(path, w, h, fill_rows):
    """8bit RGB・フィルタ 0 の PNG を書く。fill_rows(y) が 1 行分の bytes（w*3）を返す"""
    import struct
    import zlib

    def chunk(t, b):
        c = struct.pack(">I", len(b)) + t + b
        return c + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + fill_rows(y) for y in range(h))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def self_test():
    """2 セル（0.0 は絵あり、0.1 は空）のシートで、空のセルを指す dat で失敗し、絵のあるセルだけなら通ることを確かめる"""
    with tempfile.TemporaryDirectory() as d:
        full, none = bytes((10, 20, 30)) * CELL, EMPTY_ROW
        write_png(os.path.join(d, "t.png"), CELL * 2, CELL, lambda y: full + none)

        def run(body):
            with open(os.path.join(d, "t.dat"), "w", encoding="utf8") as f:
                f.write(body)
            e, empties, _, _ = scan(d, jobs=1)
            return e + compare(empties, {})

        ok = run("obj=way\nname=t\nimage[ns]=t.0.0,-1,-2\nimage[ew]=-\nicon=> t.0.1\n")
        assert not ok, ok  # icon は読まない・`-` は対象外
        bad = run("obj=way\nname=t\nimage[ns]=t.0.0\ndiagonal[ne]=t.0.1,0,0\n")
        assert len(bad) == 1 and "diagonal[ne]" in bad[0] and "image[ns]" not in bad[0], bad
        one = run("obj=way-object\nname=t\nbackimage[ns]=t.0.1\nfrontimage[ns]=t.0.0\n")  # 片方の層だけ空でも、控えに無ければ落ちる（層ごとに見る）
        assert len(one) == 1 and "backimage[ns]" in one[0] and "frontimage[ns]" not in one[0], one
        e, empties, _, _ = scan(d, jobs=1)
        assert compare(empties, {"t": {"backimage[ns]"}}) == []  # 控えにあれば通る
        assert len(compare(empties, {"t": {"frontimage[ns]"}})) == 2  # 控えの層が違えば、新しいのと古いのの両方で落ちる
        season = run("obj=way\nname=t\nimage[ns][0]=t.0.1\nimage[ns][1]=t.0.0\n")  # 季節は畳む（片方でも絵があれば空でない）
        assert not season, season
        text = run("obj=way\nname=t\nimage[ns]=oops\nimage[ew]=t.0.0\n")  # 参照の形でない値は黙って無視しない
        assert len(text) == 1 and "image[ns]" in text[0], text
        none = run("obj=way\nname=t\n")  # 参照が 0 件
        assert len(none) == 1 and "1 つも無い" in none[0], none
        assert compare({"t": {"image[ns]"}}, {"t": {"image[ns]"}}) == []  # 控えにあれば通る
        assert len(compare({}, {"t": {"image[ns]"}})) == 1  # 空でなくなった控えは古い
        out = run("obj=way\nname=t\nimage[ns]=t.0.2\n")
        assert len(out) == 1 and "外" in out[0], out
        gone = run("obj=way\nname=t\nimage[ns]=u.0.0\n")
        assert len(gone) == 1 and "シートが無い" in gone[0], gone
    print("check_cells.py の自己検査は通った")


def main(src, update=False):
    errors, empties, ncells, nrefs = scan(src)
    if update and not errors:
        write_allow(ALLOW_FILE, empties)
        print(f"控えを書き直した: {ALLOW_FILE}（{len(empties)} 物）")
        return 0
    errors += compare(empties, read_allow(ALLOW_FILE))
    if errors:
        for e in errors[:40]:
            print(e)
        if len(errors) > 40:
            print(f"（ほか {len(errors) - 40} 件は省いた）")
        print(f"{'::error::' if os.environ.get('GITHUB_ACTIONS') else ''}空のセルを指す dat の検査で {len(errors)} 件")
        return 1
    print(f"空のセルを指す dat の検査は通った（{nrefs} 参照・{ncells} セル）")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
        sys.exit(0)
    here = os.path.dirname(os.path.abspath(__file__))
    args = [a for a in sys.argv[1:] if a != "--update"]
    sys.exit(main(args[0] if args else os.path.join(here, "src"), "--update" in sys.argv))
