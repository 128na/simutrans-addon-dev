"""256 の持ち分マスク（sheetlib.cells._ground_mask）が、pak256 の地面の形と画素で一致するかの検査（#321）。Blender は使わない。

使い方（リポジトリのどこからでも）:
    python -X utf8 tools/blender/check_ground_mask.py

bpy などを差し替えて cells を読み、SHEET_PAK_SIZE=256 で次を確かめる。失敗は終了コード 1。
- 四隅の高さ 0〜2（最低 0）の 65 形すべてで、マスクが地面のマスをセルの (128, 62 + GROUND_PHASE) に置いた形と同じ
- 平らのマスクを格子に並べたとき、隙間も重なりも無い
- side の上下・左右が重ならず、合わせると全体になる（既定の引数のとき）
- 広げたマスク（線路の spill、道路の cy = ROAD_CY、高架の lower、橋の端の solid）が、平らと坂で素のマスクを含み、
  平らの spill・道路のマスクを格子に並べて隙間が無い
地面の形は pak256（128-bit-net/pak256 の 54fc440）の objects/ground/temperate/draw_ground.py の column_span・covered と同じ決まり
（列 x の中心 x + 0.5 で上の辺（左→上→右の角）と下の辺（左→下→右の角）を引き、行 y を 上 <= y < 下 で塗る）を、
ここに書き写して使う（別のリポジトリなので読み込まない。原本が変わったら写し直す）。
"""
import itertools
import os
import sys
from unittest import mock

os.environ["SHEET_PAK_SIZE"] = "256"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _m in ("bpy", "bmesh", "mathutils", "bpy_extras", "bpy_extras.object_utils"):
    sys.modules[_m] = mock.MagicMock()

import numpy as np  # noqa: E402
from sheetlib import cells  # noqa: E402
from sheetlib.core import CELL, H, SCALE, TILE  # noqa: E402

GCELL = 128 * SCALE  # 地面のマス（pak256 は 256）
STEP = 16 * SCALE    # 高さ 1 段の画素


def ground(sw, se, ne, nw):
    """pak256 の地面の形（draw_ground.column_span と covered）。角の高さは段"""
    sy, ey, ny, wy = 0.75 * GCELL - STEP * sw, GCELL - STEP * se, 0.75 * GCELL - STEP * ne, 0.5 * GCELL - STEP * nw
    half = GCELL / 2
    xc = np.arange(GCELL) + 0.5
    t = np.where(xc < half, sy + (wy - sy) * xc / half, wy + (ny - wy) * (xc - half) / half)
    b = np.where(xc < half, sy + (ey - sy) * xc / half, ey + (ny - ey) * (xc - half) / half)
    yy = np.arange(GCELL)[:, None]
    return (t[None, :] <= yy) & (yy < b[None, :])


def slope_of(sw, se, ne, nw):
    """角の高さ（段）→ cells の slope(x, y)（世界の単位。x は東、y は北）。マスクに効くのは四隅の高さだけ"""
    if (sw, se, ne, nw) == (0, 0, 0, 0):
        return None
    h = TILE / 2

    def f(x, y):
        u, v = (x + h) / TILE, (y + h) / TILE
        return H * (sw * (1 - u) * (1 - v) + se * u * (1 - v) + ne * u * v + nw * (1 - u) * v)
    return f


fails = []
# 地面のマスを置く位置。縦はゲームで決めた（#321。cells.GROUND_PHASE の注）。値を変えるときは、坂の継ぎ目をゲームで撮り直してからここも直す
dx, dy = CELL // 2 - GCELL // 2, 61
if getattr(cells, "GROUND_CY", None) != 254:
    fails.append(f"GROUND_CY が 254 でない: {getattr(cells, 'GROUND_CY', None)}")
shapes = [s for s in itertools.product(range(3), repeat=4) if min(s) == 0]
for s in shapes:
    want = np.zeros((CELL, CELL), bool)
    want[dy:dy + GCELL, dx:dx + GCELL] = ground(*s)
    got = cells._ground_mask(slope_of(*s))
    if (got ^ want).any():
        fails.append(f"形 {s}（sw, se, ne, nw）: 欠け {int((want & ~got).sum())}・余り {int((got & ~want).sum())}")

def tiled(mask):
    """平らのマスクを格子に並べ、真ん中の範囲で各画素を何枚が覆うかを返す"""
    canvas = np.zeros((CELL * 3, CELL * 3), int)
    for i, j in itertools.product(range(-3, 4), repeat=2):
        ox, oy = CELL + (i - j) * GCELL // 2, CELL + (i + j) * GCELL // 4
        if 0 <= ox <= 2 * CELL and 0 <= oy <= 2 * CELL:
            canvas[oy:oy + CELL, ox:ox + CELL] += mask
    return canvas[CELL + CELL // 4:2 * CELL - CELL // 4, CELL + CELL // 4:2 * CELL - CELL // 4]


core = tiled(cells._ground_mask(None))
if (core != 1).any():
    fails.append(f"平らの並び: 重なり {int((core > 1).sum())}・隙間 {int((core == 0).sum())}")

# 広げたマスク（呼び出しの引数の組。値は画素で、AMI の線路の spill は 2・高架の lower は 32 前後）
WIDENED = {"spill": dict(spill=2), "road": dict(cy=cells.ROAD_CY), "lower": dict(cy=cells.ROAD_CY, lower=32)}
for s in [(0, 0, 0, 0), (1, 1, 0, 0), (0, 0, 2, 2), (1, 0, 0, 0)]:
    sl = slope_of(*s)
    for name, kw in list(WIDENED.items()) + ([("solid", dict(solid=True))] if sl else []):
        # 素のマスクは同じ cy の菱形だけ（道路は地面より下の ROAD_CY に描くので、地面の位置の菱形は含まない）
        base = cells._column_mask(sl, None, kw.get("cy", cells.GROUND_CY))
        m = cells._ground_mask(sl, **kw)
        if (base & ~m).any():
            fails.append(f"{name} の形 {s}: 素のマスクを含まない（{int((base & ~m).sum())} 画素）")
for name in ("spill", "road"):
    if (tiled(cells._ground_mask(None, **WIDENED[name])) == 0).any():
        fails.append(f"{name} の平らの並びに隙間がある")

for s in [(0, 0, 0, 0), (1, 1, 0, 0), (0, 1, 1, 0), (1, 0, 0, 0), (2, 2, 0, 0)]:
    sl = slope_of(*s)
    full = cells._ground_mask(sl)
    for a, b in (("top", "bottom"), ("left", "right")):
        ma, mb = cells._ground_mask(sl, a), cells._ground_mask(sl, b)
        if (ma & mb).any() or ((ma | mb) != full).any():
            fails.append(f"side {a}/{b} の形 {s}: 重なり {int((ma & mb).sum())}・全体との差 {int(((ma | mb) ^ full).sum())}")

if fails:
    print("\n".join(fails))
    sys.exit(1)
print(f"[ground-mask] 256 の持ち分マスク: 地面と一致 {len(shapes)} 形・平らの並びに隙間と重なり無し・side の分け方・広げたマスク OK（GROUND_PHASE {cells.GROUND_PHASE}）")
