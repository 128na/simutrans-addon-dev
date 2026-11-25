"""dat が空のセル（全部透明）を指していないかの検査（#241）。check.sh が呼ぶ。Python の標準ライブラリだけでも動く（Pillow があれば速い。CI に numpy・Blender は無い）。

    python -X utf8 check_cells.py [src のディレクトリ]
    python -X utf8 check_cells.py --self-test
    SHEET_PAK_SIZE=256 python -X utf8 check_cells.py   # 256 のシート（src256/）。控えは dat のある物だけ見る（#261）

dat の絵のキー（image・imageup・diagonal・frontimage・backimage・openimage など、値が `<シート>.<行>.<列>[,x,y]` の形のもの）が指すセルを、
シートの PNG で読み、全部の画素が透明色（231,255,255）なら失敗にする。セルを描き忘れたり、dat の指すセルがずれたりすると、
その向き・坂の絵が空になって本体で見えなくなる（#217・#227 で、設定が 2 か所に分かれていて片方を直し忘れた取りこぼし）。
icon・cursor は check_icons.py が見るので、ここでは読まない。値が `-`（絵なし。dat が意図して空にしたもの）はセルの参照でないので対象外。
PNG は Pillow があればそれで読み（CI は pip install Pillow。約 1.4 ギガ画素を数秒で読める）、無ければ check_icons.py の read_rows（純 Python。数分かかる）で読む。結果は同じ（`CHECK_CELLS_PURE=1` で純 Python に固定できる。Blender は使わない）。

ほとんどの物は、描かない向き・坂・層を空のセルに向ける（壁・架線は奥の層か手前の層だけ、路面表示の way は使わない向きなど。意図して空）ので、
「空のセルを指してはならない」とは言えない。そこで、空のセルを指す絵のキー（層・季節は別々に）を物ごとに check_cells.allow.txt に控え、控えに無い物が新しく
空のセルを指したら失敗にする（向きの追加・セルのずれ・描き忘れ）。控えにあるのに空でなくなったものも失敗にする（控えを古いまま残さない）。
意図して空にしたものを足す・絵を描いて空でなくなったものを外すときは、`python -X utf8 check_cells.py --update` で控えを書き直し、差分を読んでコミットする。
"""
import multiprocessing
import os
import re
import sys
import tempfile

from check_icons import CELL, SCALE, SRC, TRANSPARENT, cell_of, drop_missing, fmt, png_size, read_dats, read_rows, size_error

ALLOW_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_cells.allow.txt")

# セルの参照を値に持たないキー（check_icons.py が別に見るもの）
SKIP_KEYS = ("icon", "cursor")

EMPTY_ROW = bytes(TRANSPARENT) * CELL


PICTURE_KEY = re.compile(r"^[a-z_]*(image|pillar|ramp|start|diagonal)[a-z_0-9]*(\[|$)")  # 絵を指すキー（値は参照か `-`）


try:
    from PIL import Image  # あれば C の読みで速い（CI は pip install Pillow）。無ければ純 Python の read_rows
except ImportError:
    Image = None


def empty_cells_pure(path, nrows, cells):
    """純 Python（check_icons.read_rows）の読み。Pillow が無いとき、と Pillow の読みとの突き合わせに使う"""
    w, h, rows = read_rows(path, nrows)
    out = {}
    for r, c in cells:
        if (c + 1) * CELL > w or (r + 1) * CELL > h:
            out[(r, c)] = None
        else:
            out[(r, c)] = all(bytes(rows[y][c * CELL * 3:(c + 1) * CELL * 3]) == EMPTY_ROW for y in range(r * CELL, (r + 1) * CELL))
    return out


def empty_cells_pil(path, cells):
    """Pillow の読み。セルの全画素が透明色かを、切り出したセルの各チャンネルの最小・最大で見る"""
    with open(path, "rb") as f:
        depth = f.read(25)[24:25]  # IHDR のビット深度（Pillow は 16bit を 8bit に落として黙って通すので、純 Python の読みと揃えて自分で弾く）
    with Image.open(path) as im:
        if im.mode != "RGB" or im.info.get("interlace") or depth != b"\x08":
            raise SystemExit(f"8bit RGB・インターレースなしの PNG でない（読めない）: {path} mode={im.mode} depth={depth[0] if depth else None}")
        w, h = im.size
        out = {}
        for r, c in cells:
            if (c + 1) * CELL > w or (r + 1) * CELL > h:
                out[(r, c)] = None
            else:
                out[(r, c)] = im.crop((c * CELL, r * CELL, (c + 1) * CELL, (r + 1) * CELL)).getextrema() == tuple((t, t) for t in TRANSPARENT)
        return out


def empty_cells(task):
    """(シートの PNG のパス, 行の数, [(行, 列)]) → {(行, 列): 空か}。シートごとに別のプロセスで呼ぶ"""
    path, nrows, cells = task
    if Image is None or os.environ.get("CHECK_CELLS_PURE"):
        return empty_cells_pure(path, nrows, cells)
    return empty_cells_pil(path, cells)


def scan(src, jobs=None):
    """src の dat が指すセルを読み、(エラー, {物: {空の絵の種類}}, 調べたセルの数, 調べた参照の数) を返す。

    空の絵の種類は、同じ物の 1 つのキー（層・季節ごとに別）が、空のセルを指しているもの。
    奥の層だけ・手前の層だけを描く物（壁・架線・柱・踏切の手前の絵など）は、描かない層が空のセルを指すので、控えに入る"""
    objs, _ = drop_missing(src, read_dats(src))  # CHECK_SKIP_MISSING=1 のときだけ、シートの無い物を除く
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
        errors.append(f"{src} に、セルを指す絵のキーが 1 つも無い（src の dat が読めていない）")
    per_sheet = {}
    for sheet, r, c in uses:
        per_sheet.setdefault(sheet, []).append((r, c))
    tasks, sheets = [], []
    for sheet, cells in sorted(per_sheet.items()):
        path = os.path.join(src, sheet + ".png")
        if not os.path.exists(path):
            errors.append(f"シートが無い: {sheet}.png（{who([u for cell, us in uses.items() if cell[0] == sheet for u in us])}）")
            continue
        w, h = png_size(path)
        bad = size_error(path, w, h)
        if bad:
            errors.append(bad)
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
    # 物ごと・キー（層・季節ごと）に、指すセルが全部空のものを探す
    groups = {}
    for cell, us in uses.items():
        for name, f, k in us:
            groups.setdefault((name, f, k), []).append((cell, k))
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
        f.write("# check_cells.py が許す、空のセルを指す絵の種類（物: 層・季節ごとの絵のキー…）。意図して描かない向き・坂・層。\n"
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
        if Image is not None:  # Pillow の読みと純 Python の読みが同じ（0.0 は絵あり・0.1 は空・0.2 はシートの外）
            cs = [(0, 0), (0, 1), (0, 2)]
            assert empty_cells_pil(os.path.join(d, "t.png"), cs) == empty_cells_pure(os.path.join(d, "t.png"), CELL, cs) == {(0, 0): False, (0, 1): True, (0, 2): None}
        e, empties, _, _ = scan(d, jobs=1)
        assert compare(empties, {"t": {"backimage[ns]"}}) == []  # 控えにあれば通る
        assert len(compare(empties, {"t": {"frontimage[ns]"}})) == 2  # 控えの層が違えば、新しいのと古いのの両方で落ちる
        season = run("obj=way\nname=t\nimage[ns][0]=t.0.0\nimage[ns][1]=t.0.1\n")  # 季節も別々に見る（冬だけ空でも落ちる）
        assert len(season) == 1 and "image[ns][1]" in season[0] and "image[ns][0]" not in season[0], season
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
        # シートの大きさがセルの倍数でないとき（別の大きさのシート）は、セルを読まずに落とす
        write_png(os.path.join(d, "odd.png"), CELL + 1, CELL, lambda y: bytes(3 * (CELL + 1)))
        odd = run("obj=way\nname=t\nimage[ns]=odd.0.0\n")
        assert len(odd) == 1 and "倍数でない" in odd[0], odd
        # CHECK_SKIP_MISSING=1: シートの無い物（u）だけを飛ばし、シートのある物（t）は見る。付けなければ飛ばさない
        two = "obj=way\nname=t\nimage[ns]=t.0.0\n---\nobj=way\nname=v\nimage[ns]=u.0.0\n"
        assert len(run(two)) == 1 and "シートが無い" in run(two)[0]
        os.environ["CHECK_SKIP_MISSING"] = "1"
        try:
            assert run(two) == [], run(two)
            e, empties, _, refs = scan(d, jobs=1)
            assert refs == 1 and not e, (refs, e)  # v の参照は数えない
        finally:
            del os.environ["CHECK_SKIP_MISSING"]
    print("check_cells.py の自己検査は通った")


def main(src, update=False):
    errors, empties, ncells, nrefs = scan(src)
    if update and SCALE != 1:
        print("控えは pak128 の src/ から書き直す（SHEET_PAK_SIZE を付けずに流す）")
        return 1
    if update and not errors:
        write_allow(ALLOW_FILE, empties)
        print(f"控えを書き直した: {ALLOW_FILE}（{len(empties)} 物）")
        return 0
    allow = read_allow(ALLOW_FILE)
    if SCALE != 1:
        # pak128 以外は、描ける物（catalog.SCALED_SHEETS）だけの dat があるので、dat に無い物の控えは見ない（意図して空の絵の種類は大きさによらず同じ）
        names = {o["name"] for o in drop_missing(src, read_dats(src))[0]}
        allow = {n: g for n, g in allow.items() if n in names}
    errors += compare(empties, allow)
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
    args = [a for a in sys.argv[1:] if a != "--update"]
    sys.exit(main(args[0] if args else SRC, "--update" in sys.argv))
