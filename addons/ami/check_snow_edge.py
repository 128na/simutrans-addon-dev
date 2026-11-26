"""道路の地上の基盤の版の雪の絵の、下の端の暗い列の検査（#366）。check.sh が呼ぶ。Pillow と numpy を使う（版は ci.env）。

    python -X utf8 check_snow_edge.py [src のディレクトリ]
    python -X utf8 check_snow_edge.py --self-test
    SHEET_PAK_SIZE=256 python -X utf8 check_snow_edge.py   # 256 のシート（src256/）
    CHECK_SKIP_MISSING=1 ...                                # 比べる通常の版のシートが無い物は飛ばし、基盤の版が 1 枚も無くても通す（256 の CI。PNG は生活道路だけ）

地上の基盤の版（ami_road_<種類>_base_<版>）は、路面の板と路肩の雪の板を壁の外の面で切る。同じ所で切ると、路面の板の切り口
（影の色の縦の面）が雪の下に 1 行出て、雪の気候でタイルの手前の縁に暗い点線になった（#360。sheetlib の road_sheet の snow_recess と
road_parts の ROAD_SNOW_ASPHALT_RECESS で、雪の絵だけ路面の板を内で切って隠した）。切る位置や雪の板の厚みを変えると戻りうるので、ここで見る。

数え方（pak256 のリポジトリの記録 docs/records/2026-11-26_snow-road-seam.md の pakimg.py count と同じ決まり）: 雪の行（シートの後半の行。
sheet_rows の way_snow_rows。道路の基盤の版も通常の版も手前の絵の行を持たないので、行 4〜7）のセルの各列で、一番下の透明でない画素の
RGB の和が 300 未満で、すぐ上の画素が透明でなく和が 500 より大きい列を「暗い列」とする。
通常の版（ami_road_<種類>）の雪の行にも、斜めの半分のセルの角で車道の路面と白線がタイルの縁に来る所が同じ形で数えられる
（一般道路で 128 は 48 列、256 は 14 列。#360 の PR）。そこで、基盤の版の各セルの暗い列が、同じ種類の通常の版の同じセルより多ければ
失敗にする（基盤の版と通常の版は同じセルの並び）。
#360 の直しの前は、生活道路の base_single で 128 は 75 列、256 は 3279 列（通常の版は 0）で、10 枚とも落ちる。
暗い帯を 2 行以上まで数える形も試したが、直しの後の幹線道路・高速道路で、通常の版とセルの絵の違う所（暗い縁の 2〜3 行）が
基盤の版だけで数えられて誤って落ちた。今の切り口は 128・256 とも 1 行なので、1 行の決まりにしている（#366 の PR）。
"""
import glob
import os
import re
import sys

import numpy as np
from PIL import Image

from check_lib import CELL, SRC, TRANSPARENT, size_error

BASE = re.compile(r"^ami_road_([a-z]+)_base_[a-z]+\.png$")
DARK, BRIGHT = 300, 500  # RGB の和（0〜765）の境


def dark_columns(rgb):
    """セルの配列（高さ × 幅 × 3。int）の、下の端の暗い列の数"""
    opaque = ~np.all(rgb == TRANSPARENT, axis=2)
    h = opaque.shape[0]
    # 列ごとの一番下の透明でない画素の行（無い列は -1）
    rev = opaque[::-1]
    has = rev.any(axis=0)
    bottom = np.where(has, h - 1 - rev.argmax(axis=0), -1)
    cols = np.nonzero(bottom >= 1)[0]
    y = bottom[cols]
    s0 = rgb[y, cols].sum(axis=1)
    s1 = rgb[y - 1, cols].sum(axis=1)
    return int(np.count_nonzero(opaque[y - 1, cols] & (s0 < DARK) & (s1 > BRIGHT)))


def snow_dark_columns(path):
    """シートの雪の行（後半の行）のセルごとの暗い列の数（(行, 列): 数。0 は省く）と、シートの大きさ"""
    with Image.open(path) as im:
        a = np.asarray(im.convert("RGB")).astype(np.int32)
    rows, cols = a.shape[0] // CELL, a.shape[1] // CELL
    per = {}
    for r in range(rows // 2, rows):
        for c in range(cols):
            n = dark_columns(a[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL])
            if n:
                per[(r, c)] = n
    return per, (a.shape[1], a.shape[0])


def main(src):
    skip = bool(os.environ.get("CHECK_SKIP_MISSING"))
    errors, lines = [], []
    plain_cache = {}
    bases = sorted(p for p in glob.glob(os.path.join(src, "ami_road_*_base_*.png")) if BASE.match(os.path.basename(p)))
    if not bases and not skip:
        errors.append(f"{src} に道路の地上の基盤の版のシート（ami_road_<種類>_base_<版>.png）が 1 枚も無い")
    for path in bases:
        name = os.path.basename(path)
        plain = os.path.join(src, f"ami_road_{BASE.match(name).group(1)}.png")
        pname = os.path.basename(plain)
        if not os.path.isfile(plain):
            if skip:
                lines.append(f"  飛ばした（通常の版 {pname} のシートが無い）: {name}")
            else:
                errors.append(f"{name}: 比べる通常の版のシート {pname} が無い")
            continue
        if plain not in plain_cache:
            plain_cache[plain] = snow_dark_columns(plain)
        limit, psize = plain_cache[plain]
        per, size = snow_dark_columns(path)
        bad = [e for e in (size_error(path, *size), size_error(plain, *psize)) if e]
        if not bad and size != psize:
            bad.append(f"{name} の大きさ {size[0]}x{size[1]} が、通常の版 {pname} の {psize[0]}x{psize[1]} と違う（セルの並びが同じでない）")
        if bad:
            errors.extend(bad)
            continue
        worse = {k: (n, limit.get(k, 0)) for k, n in per.items() if n > limit.get(k, 0)}
        lines.append(f"  {name}: {sum(per.values())} 列（通常の版 {sum(limit.values())} 列）")
        if worse:
            top = sorted(worse.items(), key=lambda kv: kv[1][1] - kv[1][0])[:6]
            cells = " ".join(f"({r},{c}):{n}>{m}" for (r, c), (n, m) in top)
            errors.append(f"{name}: 雪の行の {len(worse)} セルで、下の端の暗い列が通常の版 {pname} の同じセルより多い"
                          f"（路面の板の切り口が雪の下に出ている。#360。(行,列):基盤の版>通常の版 {cells}）")
    print(f"check_snow_edge: {src}（セル {CELL}px）: 基盤の版 {len(bases)} 枚")
    for line in lines:
        print(line)
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1
    return 0


def self_test():
    """作った小さなセルで、暗い列の決まりと、通常の版との比べを確かめる"""
    t = np.array(TRANSPARENT, dtype=np.int32)
    cell = np.tile(t, (8, 6, 1))
    snow, asphalt, edge = np.array([225, 225, 235]), np.array([56, 58, 61]), np.array([80, 80, 84])
    cell[2:6, 0:6] = snow
    assert dark_columns(cell) == 0, "雪だけの縁は暗い列にならない"
    cell[6, 0:4] = edge  # 雪の下に切り口の暗い 1 行（4 列）
    assert dark_columns(cell) == 4, dark_columns(cell)
    cell[2:7, 4:6] = asphalt  # 路面が縁まで来る列（すぐ上も暗い）は数えない
    assert dark_columns(cell) == 4, dark_columns(cell)
    one = np.tile(t, (3, 2, 1))
    one[2] = edge  # すぐ上が透明な列は数えない
    assert dark_columns(one) == 0
    one[1] = (100, 100, 100)  # 境の値: 和 300 は暗くない、500 は明るくない
    one[2] = (100, 100, 99)
    assert dark_columns(one) == 0
    one[1] = (167, 167, 167)
    assert dark_columns(one) == 2
    one[1] = (167, 167, 166)
    assert dark_columns(one) == 0
    # シートで: 雪の行（後半）だけを、セルごとに通常の版と比べる
    import tempfile
    os.environ.pop("CHECK_SKIP_MISSING", None)
    with tempfile.TemporaryDirectory() as d:
        def sheet(name, dark):  # dark: {(行, 列): 暗い列の数}。2 行 × 2 列のシート
            a = np.tile(np.array(TRANSPARENT, dtype=np.uint8), (CELL * 2, CELL * 2, 1))
            for r in (0, 1):
                a[r * CELL + 10:r * CELL + 20, :] = (225, 225, 235)
            for (r, c), n in dark.items():
                a[r * CELL + 20, c * CELL:c * CELL + n] = (80, 80, 84)
            Image.fromarray(a).save(os.path.join(d, name))
        base = os.path.join(d, "ami_road_local_base_single.png")
        assert main(d) == 1  # 基盤の版が 1 枚も無ければ落ちる
        sheet("ami_road_local.png", {(0, 0): 50, (1, 0): 5})  # 温帯の行の暗い列は数えない
        sheet("ami_road_local_base_single.png", {(0, 0): 99, (1, 0): 5})
        assert snow_dark_columns(base)[0] == {(1, 0): 5}
        assert main(d) == 0  # 通常の版にもある物と同じ数は許す
        sheet("ami_road_local_base_single.png", {(1, 0): 6})
        assert main(d) == 1  # 1 列でも多ければ落ちる
        sheet("ami_road_local_base_single.png", {(1, 0): 1, (1, 1): 3})
        assert main(d) == 1  # 合計が少なくても、ほかのセルで多ければ落ちる
        sheet("ami_road_local_base_single.png", {})
        assert main(d) == 0
        os.remove(os.path.join(d, "ami_road_local.png"))
        assert main(d) == 1  # 比べる通常の版が無ければ落ちる
        os.environ["CHECK_SKIP_MISSING"] = "1"
        try:
            assert main(d) == 0  # CHECK_SKIP_MISSING では飛ばす
        finally:
            del os.environ["CHECK_SKIP_MISSING"]
    print("check_snow_edge: self-test ok")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(self_test())
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else SRC))
