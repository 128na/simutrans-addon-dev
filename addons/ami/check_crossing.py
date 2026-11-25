"""踏切のシートが今の道路のシートから描かれているかの検査（#130）。check.sh が呼ぶ。Python の標準ライブラリだけで動く。

    python -X utf8 check_crossing.py [src のディレクトリ]

踏切の奥の絵は、道路の way のシートの直線のセルを下地に写して描く（tools/blender/sheetlib/crossing.py の crossing_sheet）。
道路のシートを描き直して踏切を描き直し忘れると、踏切のタイルだけ古い路面になる（check.sh は Blender で描かないので、
絵を比べても気づけない）。crossing_sheet は、写したセルの sha256 を踏切のシートの横の控え（<踏切のシート>.road_cells.txt）に書く。
水路の踏切（#117。tools/blender/sheetlib/canal_crossing.py）も同じ控えに、写した運河（と道路）のセルを書く。
ここでは、控えのセルを今の道路・運河のシートから読み直して sha256 を比べ、違えば「道路のシートの後に踏切を描き直す」と言って 1 で終わる。
"""
import glob
import hashlib
import os
import sys

from check_icons import CELL, SRC, read_rows

STAMP_SUFFIX = ".road_cells.txt"  # tools/blender/sheetlib/crossing.py の ROAD_STAMP_SUFFIX と同じ
# 控えに無ければならないセル（道路・運河の直線の ns・ew と、その雪の行。blender/render.py の crossing_sheet の既定）。
# 一部の向きだけ描いた控え（SHEET_ONLY）を src に持ち込んだときにも気づけるように、全部そろっているかを見る
EXPECTED_CELLS = {(0, 2), (0, 3), (4, 2), (4, 3)}


def expected_sources(name):
    """踏切のシートの名前 → 写したシートの名前の集まり。
    線路×道路: ami_crossing_road_<道路>.png → {ami_road_<道路>.png}
    水路の踏切（#117）: ami_crossing_canal_road_<道路>.png → {ami_canal.png, ami_road_<道路>.png}、ami_crossing_canal_rail.png → {ami_canal.png}"""
    if name.startswith("ami_crossing_canal_"):
        rest = name[len("ami_crossing_canal_"):]
        return {"ami_canal.png"} | ({"ami_" + rest} if rest.startswith("road_") else set())
    return {name.replace("ami_crossing_", "ami_")}


def cell_digest(rows, row, col):
    """read_rows の行（RGB）から、セル (row, col) の画素を上の行から並べた sha256"""
    h = hashlib.sha256()
    for y in range(row * CELL, (row + 1) * CELL):
        h.update(bytes(rows[y][col * CELL * 3:(col + 1) * CELL * 3]))
    return h.hexdigest()


def main(src):
    sheets = sorted(glob.glob(os.path.join(src, "ami_crossing_*.png")))
    if not sheets:
        print("[crossing] 踏切のシートが無い")
        return 1
    errors, checked, cache = [], 0, {}
    for png in sheets:
        stamp = png[:-len(".png")] + STAMP_SUFFIX
        name = os.path.basename(png)
        if not os.path.exists(stamp):
            errors.append(f"{name}: 写した道路のセルの控え（{os.path.basename(stamp)}）が無い。踏切のシートを描き直す")
            continue
        with open(stamp, encoding="utf8") as f:
            lines = [line.split() for line in f.read().splitlines() if line.strip()]
        bad = [" ".join(t) for t in lines if len(t) != 4 or not t[1].isdigit() or not t[2].isdigit()]
        if bad:
            errors.append(f"{name}: 控えの行の形が違う（道路のシート 行 列 sha256）: {bad[0]}")
            continue
        sources = expected_sources(name)
        got = {}
        for src_sheet, r, c, _ in lines:
            got.setdefault(src_sheet, set()).add((int(r), int(c)))
        if got != {s: EXPECTED_CELLS for s in sources} or len(lines) != len(EXPECTED_CELLS) * len(sources):
            errors.append(f"{name}: 控えのセルが {sorted(sources)} の {sorted(EXPECTED_CELLS)} でない"
                          f"（{ {k: sorted(v) for k, v in sorted(got.items())} }）。踏切のシートを全部の向きで描き直す")
            continue
        for road, row, col, digest in lines:
            row, col = int(row), int(col)
            road_png = os.path.join(src, road)
            if not os.path.exists(road_png):
                errors.append(f"{name}: 写した道路のシート {road} が無い")
                continue
            need = (row + 1) * CELL
            if road not in cache or len(cache[road]) < need:
                w, h, cache[road] = read_rows(road_png, need)
                if h < need or w < (col + 1) * CELL:
                    errors.append(f"{name}: {road} が {w}x{h} で、セル {row}.{col} が入らない")
                    del cache[road]
                    continue
            checked += 1
            if cell_digest(cache[road], row, col) != digest:
                errors.append(f"{name}: {road} のセル {row}.{col} が、踏切を描いたときと違う")
    for e in errors:
        print(f"[crossing] {e}")
    if errors:
        print("[crossing] 道路・運河のシートを描き直したら、踏切のシートも描き直す（blender/render.py の ami_crossing_road_<道路>・"
              "ami_crossing_canal_<road_<道路>|rail>）")
        return 1
    print(f"[crossing] 踏切のシート {len(sheets)} 枚、写した道路のセル {checked} 個が、今の道路のシートと同じ")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else SRC))
