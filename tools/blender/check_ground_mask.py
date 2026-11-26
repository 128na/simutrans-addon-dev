"""256 の持ち分マスク（sheetlib.cells._ground_mask）が、pak256 の地面の形と画素で一致するかの検査（#321）。Blender は使わない。

使い方（リポジトリのどこからでも）:
    python -X utf8 tools/blender/check_ground_mask.py

bpy などを差し替えて cells を読み、SHEET_PAK_SIZE=256 で次を確かめる。失敗は終了コード 1。
- 四隅の高さ 0〜2（最低 0）の 65 形すべてで、マスクが地面のマスをセルの (128, 62 + GROUND_PHASE) に置いた形と同じ
- 平らのマスクを格子に並べたとき、隙間も重なりも無い
- side の上下・左右が重ならず、合わせると全体になる（既定の引数のとき）
- 広げたマスク（線路の spill、道路の cy = ROAD_CY、高架の lower、橋の端の solid）が、平らと坂で素のマスク
  （道路は地面の位置の菱形も。#333）を含み、
  平らの spill・道路のマスクを格子に並べて隙間が無い
- 広げたマスクの列に途中の穴が無い（65 形。#333）
- 1 段の台の上の十字と四方の坂の道路（pak256 の scene.py の slope_road）を並べて、台の地面に道路の穴が無い（#333）
地面の形は pak256（128-bit-net/pak256 の 54fc440）の objects/ground/temperate/draw_ground.py の column_span・covered と同じ決まり
（列 x の中心 x + 0.5 で上の辺（左→上→右の角）と下の辺（左→下→右の角）を引き、行 y を 上 <= y < 下 で塗る）を、
ここに書き写して使う（別のリポジトリなので読み込まない。原本が変わったら写し直す）。
"""
import inspect
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
from sheetlib import sheetlib as S  # noqa: E402
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
        # 素のマスクは同じ cy の菱形。道路（ROAD_CY）は、平らでも地面の位置の菱形も含む（坂と平らの境で奥の縁が跳ばない。#333）
        base = cells._column_mask(sl, None, kw.get("cy", cells.GROUND_CY))
        if kw.get("cy", cells.GROUND_CY) != cells.GROUND_CY:
            base = base | cells._column_mask(sl, None, cells.GROUND_CY)
        m = cells._ground_mask(sl, **kw)
        if (base & ~m).any():
            fails.append(f"{name} の形 {s}: 素のマスクを含まない（{int((base & ~m).sum())} 画素）")
for name in ("spill", "road"):
    if (tiled(cells._ground_mask(None, **WIDENED[name])) == 0).any():
        fails.append(f"{name} の平らの並びに隙間がある")

# 平らな道路（ROAD_CY）の奥の辺の上の帯（地面の菱形の中で、道路の位置の菱形より上）: つながる辺（北・西）は空ける（奥のタイルの絵が埋める。
# 塗ると、白線が向きを変える所で奥の線の端を覆った。#354）。つながらない辺は地面の位置まで塗る（坂と平らの境の跳び。#333）。
# 左右の列の仮定を使わず、地図の上の位置で見る: 北・西の隣のタイルの道路の菱形を、画面のずれ（北は右上、西は左上へ半タイル）に置き、
# 手前のタイルの持ち分と重なるか。つながる辺なら重ならない（奥のタイルの絵だけが見える）、つながらない辺なら帯の分だけ重なる
_HALF_W, _HALF_H = 64 * SCALE, 32 * SCALE
_NEIGHBOR = {"n": (_HALF_W, -_HALF_H), "w": (-_HALF_W, -_HALF_H)}  # 奥の隣のセルの、画面での位置のずれ（x, y）


def _shifted(mask, dx, dy):
    out = np.zeros_like(mask)
    h, w = mask.shape
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = mask[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


_road = cells._column_mask(None, None, cells.ROAD_CY)
for exits in ("", "ns", "ew", "nsew", "ne", "sw", "nw", "se"):
    m = cells._ground_mask(None, cy=cells.ROAD_CY, exits=exits)
    for d, (dx, dy) in _NEIGHBOR.items():
        n = int((m & _shifted(_road, dx, dy)).sum())
        if d in exits and n:
            fails.append(f"平らな道路（つながる辺 {exits!r}）: つながる {d} の隣の道路の菱形に {n} 画素かかる")
        if d not in exits and n == 0:
            fails.append(f"平らな道路（つながる辺 {exits!r}）: つながらない {d} の辺の上の帯を塗らない")
# 坂は exits で変わらない（坂は本体が地面を後から描くので、つながる辺の上も地面の位置まで塗る。#333）
for s in [(1, 1, 0, 0), (0, 0, 1, 1), (1, 0, 0, 0), (0, 0, 2, 2)]:
    sl = slope_of(*s)
    if (cells._ground_mask(sl, cy=cells.ROAD_CY, exits="nsew") != cells._ground_mask(sl, cy=cells.ROAD_CY)).any():
        fails.append(f"坂 {s}: exits で持ち分が変わる")
# render_cell が持ち分の絵（_own.png）を書くときに exits を渡すか（bpy は差し替えてあり、描画はしない）
_saved = []
with mock.patch.object(cells, "save_rgba", lambda path, img: _saved.append(img[..., 0] > 0)):
    cells.render_cell("check_exits", "nsew", cy=cells.ROAD_CY)
    cells.render_cell("check_exits", "", cy=cells.ROAD_CY)
if len(_saved) != 2 or not (_saved[0] != _saved[1]).any():
    fails.append("render_cell の持ち分の絵が exits で変わらない（_render_ground に exits が届かない）")
# 線路の版の prof["fill_back_band"]（路面軌道）は、持ち分に exits を空で渡し、つながる辺の上も塗る（#365）。
# track_sheet（中身の _track_sheet）は持ち分（render_cell・render_layers）に track_own_exits の値だけを渡す（exits_of を直に渡す枝が残ると、印が効かない）
if S.track_own_exits({"fill_back_band": True}, "nsew2") != "" or S.track_own_exits({}, "nsew2") != "nsew":
    fails.append("track_own_exits: fill_back_band のときに空、無いときに exits_of と同じ値を返さない")
_track_src = inspect.getsource(S._track_sheet)
if "exits_of(" in _track_src or _track_src.count("own_exits") < 4:
    fails.append("track_sheet が持ち分に track_own_exits を通さない exits を渡す所がある（fill_back_band が効かない）")


def gaps(mask):
    """列ごとに、一番上と一番下の行の間で抜けている画素の数"""
    n = 0
    for col in mask.T:
        rows = np.nonzero(col)[0]
        if len(rows):
            n += int(rows[-1] - rows[0] + 1 - len(rows))
    return n


# 広げたマスクの列が途切れない（#333: 道路の坂は地面の位置と道路の位置の形の和で、間のずらしが抜けると、
# 縦の幅が 2 画素より薄い角の近くの列に 1 行の穴ができ、台の上の十字の奥の角に草の線が出た）
for s in shapes:
    sl = slope_of(*s)
    for name, kw in list(WIDENED.items()) + ([("solid", dict(solid=True))] if sl else []):
        n = gaps(cells._ground_mask(sl, **kw))
        if n:
            fails.append(f"{name} の形 {s}: 列の途中の穴 {n} 画素")


def scene_hole():
    """1 段の台の上の十字と、四方の坂の道路（pak256 の scene.py の slope_road）を並べ、
    台の地面の範囲で、どの道路のマスクにも覆われない画素の数を返す"""
    canvas, ground_ = (np.zeros((CELL * 3, CELL * 3), bool) for _ in range(2))

    def put(target, mask, i, j, base):
        ox, oy = CELL + (i - j) * GCELL // 2, CELL + (i + j) * GCELL // 4 - base * STEP
        target[oy:oy + CELL, ox:ox + CELL] |= mask
    # (i, j) = (東, 南)。台は高さ 1。北の坂は南の 2 角、南の坂は北の 2 角、西の坂は東の 2 角、東の坂は西の 2 角が上がる
    put(canvas, cells._ground_mask(None, cy=cells.ROAD_CY), 0, 0, 1)
    for (i, j), corner in {(0, -1): (1, 1, 0, 0), (0, 1): (0, 0, 1, 1), (-1, 0): (0, 1, 1, 0), (1, 0): (1, 0, 0, 1)}.items():
        put(canvas, cells._ground_mask(slope_of(*corner), cy=cells.ROAD_CY), i, j, 0)
    put(ground_, cells._ground_mask(None), 0, 0, 1)
    return int((ground_ & ~canvas).sum())


n = scene_hole()
if n:
    fails.append(f"台の上の十字と四方の坂の道路: 台の地面で道路に覆われない画素 {n}")

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
print(f"[ground-mask] 256 の持ち分マスク: 地面と一致 {len(shapes)} 形・平らの並びに隙間と重なり無し・side の分け方・広げたマスク（列の穴無し）・"
      f"台の上の十字 OK（GROUND_PHASE {cells.GROUND_PHASE}）")
