"""AMI の検査（check_*.py）が共通で使う物: dat の読み・セルの参照・PNG の読み・offset・セルの digest（#303）。
検査の中身（何を落とすか）は各 check_*.py に置き、ここには「読む」物だけを置く。同じ物を 2 本の検査が別々に持たない。
"""
import glob
import hashlib
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..", "..", "tools", "blender"))
import sheet_settings  # noqa: E402  pak の大きさ（環境変数 SHEET_PAK_SIZE。既定は pak128。256 の検査は SHEET_PAK_SIZE=256 で流す。#261）

SCALE = sheet_settings.SCALE  # pak128 に対する倍率。検査の対象は、128 は src/、256 は src256/（blender/ami_dat.py の SRC と同じ）
SRC = os.path.join(HERE, "src" + sheet_settings.SUFFIX)
CELL = 256 * SCALE  # 1 セルの画素数（pak128 は 256、256 は 512）
TRANSPARENT = (231, 255, 255)
REF = re.compile(r"^>?\s*([A-Za-z0-9_\-]+)\.(\d+)\.(\d+)\s*(?:,|$)")
REF_OFFSET = re.compile(r"^>?\s*[A-Za-z0-9_\-]+\.\d+\.\d+\s*(?:,\s*(-?\d+)\s*,\s*(-?\d+))?\s*(?:,|$)")  # セルの後の offset（無ければ None, None）


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


def drop_missing(src, objs):
    """環境変数 CHECK_SKIP_MISSING=1 のとき、絵のシート（dat のセルの参照が指す PNG）が src に無い物を除く。除いた物の数も返す。
    256 は PNG をコミットせず（dat と生活道路だけ。#261）、描いた分だけ検査したいときに使う（CI。シートが全部そろった手元では付けない）"""
    if not os.environ.get("CHECK_SKIP_MISSING"):
        return objs, 0
    kept = [o for o in objs
            if all(os.path.exists(os.path.join(src, cell[0] + ".png")) for cell in (cell_of(v) for v in o["keys"].values()) if cell)]
    return kept, len(objs) - len(kept)


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


def png_size(path):
    """PNG の幅・高さ（IHDR だけ読む）"""
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"PNG でない: {path}")
    return struct.unpack(">II", head[16:24])


def size_error(path, w, h):
    """シートの大きさ w x h がセルの大きさ CELL の倍数でなければ、その文を返す（別の大きさのシート。128 のシートを 256 で検査した、など。
    セルの切りが全部ずれて、ほかの検査が分かりにくい文で落ちる）。倍数なら None"""
    if w % CELL or h % CELL:
        return f"シート {os.path.basename(path)} の大きさ {w}x{h} が、セルの大きさ {CELL}px の倍数でない（SHEET_PAK_SIZE と合わないシート）"
    return None


def offset_of(value):
    """セルの参照の offset（x, y）。無ければ None"""
    m = REF_OFFSET.match(value)
    return None if not m or m.group(1) is None else (int(m.group(1)), int(m.group(2)))


def cell_digest(rows, row, col):
    """read_rows の行（RGB）から、セル (row, col) の画素を上の行から並べた sha256（blender/icons.py の cell_digest と同じ並び。控えを読む側（check_icons・check_crossing）の共通の 1 か所）"""
    h = hashlib.sha256()
    for y in range(row * CELL, (row + 1) * CELL):
        h.update(bytes(rows[y][col * CELL * 3:(col + 1) * CELL * 3]))
    return h.hexdigest()
