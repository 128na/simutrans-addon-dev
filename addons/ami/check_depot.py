"""車庫（building）の絵の大きさの検査（#112）。check.sh が呼ぶ。Python の標準ライブラリだけで動く（CI に numpy・Blender は無い）。

    python -X utf8 check_depot.py [src のディレクトリ]

車庫は、箱積み駅舎の箱 1 段（1 タイル × 高さ 2 段 = 32px。#140）に収める（2026-11-21、ユーザーの決定）。dat の obj=building の物について:

1. 奥の絵・手前の絵（backimage・frontimage）の塗った画素が、箱の六角形の中にあるか。六角形は pak128 の 128px のセルの座標で
   (64,32)(128,64)(128,96)(64,128)(0,96)(0,64)（地面の菱形 y64〜127 と、その 32px 上の菱形を結んだ形）。画素の中心で判定する。
   セルの座標に dat のオフセットを足すと 128px の座標（256px のセルを切る AMI の決まり。build.py の PAKSET）。
   256（SHEET_PAK_SIZE=256。src256/）は座標が全部 2 倍（箱 1 段 = 64px。#261）。
   外へ出ると、隣や上に積んだ箱と重なる
2. 奥の絵の上端が y32（256 は y64）より下か。本体は奥の絵の不透明な上端から建物の高さ（段）を出し、その上に高架を引けるかを決める
   （OTRP の building_desc.cc の get_drawn_height: 段 = (64 - 上端) / 16 の切り捨て。wegbauer.cc は車庫も見る）。
   y32 なら 2 段で、箱の 2 段目（高架の運河、+2 段）を上に積める
"""
import os
import sys

from check_lib import CELL, SCALE, SRC, TRANSPARENT, cell_of, fmt, offset_of, read_dats, read_rows, size_error

# 箱 1 段の六角形（pak128 のセルの座標を SCALE 倍した座標。時計回り）。256 は 2 倍（#261）
HEX = [(x * SCALE, y * SCALE) for x, y in [(64, 32), (128, 64), (128, 96), (64, 128), (0, 96), (0, 64)]]
BOX_TOP = 32 * SCALE  # 奥の絵の上端の下限（同じ座標）


def inside(x, y):
    """セルの座標 (x, y)（pak の大きさに合わせた画素。128 は 128px の座標）の点が六角形の中か（辺の上を含む）"""
    for (x0, y0), (x1, y1) in zip(HEX, HEX[1:] + HEX[:1]):
        if (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0) < -1e-6:
            return False
    return True


def main(src):
    errors = []
    sheets = {}
    checked = 0
    for o in read_dats(src):
        if o["obj"] != "building":
            continue
        for key, value in o["keys"].items():
            if not (key.startswith("backimage[") or key.startswith("frontimage[")):
                continue
            cell = cell_of(value)
            if cell is None:
                continue
            sheet, r, c = cell
            if sheet not in sheets:
                path = os.path.join(src, sheet + ".png")
                w, h, _ = read_rows(path, 1)
                bad = size_error(path, w, h)
                if bad:
                    sys.exit(f"[check_depot] {bad}")
                sheets[sheet] = read_rows(path, h)[2]
            rows = sheets[sheet]
            dx, dy = offset_of(value) or (0, 0)  # offset が無ければ (0, 0)
            out, top = 0, None
            for y in range(r * CELL, (r + 1) * CELL):
                line = rows[y]
                for x in range(c * CELL, (c + 1) * CELL):
                    i = x * 3
                    if tuple(line[i:i + 3]) == TRANSPARENT:
                        continue
                    px, py = x - c * CELL + dx + 0.5, y - r * CELL + dy + 0.5
                    if top is None:
                        top = y - r * CELL + dy
                    if not inside(px, py):
                        out += 1
            checked += 1
            if out:
                errors.append(f"{o['name']}: {key} のセル {fmt(cell)} に、箱の六角形の外の画素が {out} ある")
            if key.startswith("backimage[") and top is not None and top < BOX_TOP:
                errors.append(f"{o['name']}: {key} のセル {fmt(cell)} の上端が y{top}（y{BOX_TOP} より上。建物の高さが 2 段を超える）")
    for e in errors:
        print(e)
    if errors:
        sys.exit(f"[check_depot] {len(errors)} 件")
    print(f"[check_depot] 建物の絵 {checked} 枚が箱 1 段（{32 * SCALE}px）に収まる")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else SRC)
