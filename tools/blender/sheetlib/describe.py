"""説明用の色つきの way（AMI #372。手本は iss の util/describe）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

ゲームの中の図解（どこに何を敷くか、つながり）に使う、1 色で塗った帯の way。陰影もまだらも付けず、どの向きの面も同じ色に見えるようにする。
地上（tram_track）と高架（track・system_type=1）は同じシートを使う（iss も同じ画像を指す）。雪の絵は持たない。
形は、直線・行き止まり（端に横棒）・1 タイル・曲がり（中心で折れる）・斜め（辺の中点を結ぶ直線）・T字・十字・坂（1 段・2 段）。
"""
import os

import bpy

from . import marking as _mk
from . import sheetlib as _s
from .cells import GROUND_CY, make_sheet, render_cell
from .core import H, TILE, apply_slope, clear_models, set_anchor

DESCRIBE_W = TILE / 4        # 帯の幅（iss の red.png は、タイルの辺の約 1/4）
DESCRIBE_CAP = TILE / 2      # 行き止まりの横棒の長さ
_HALF = TILE / 2
_DIRS = {"n": (0, 1), "e": (1, 0), "s": (0, -1), "w": (-1, 0)}


def describe_material(rgb8):
    """sRGB 8bit の rgb8 が、光の向きに関係なくそのまま画面に出る材質（黒の下地 + 発光）"""
    name = "ami_describe_{}_{}_{}".format(*rgb8)
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    lin = tuple((c / 255 / 12.92) if c / 255 <= 0.04045 else (((c / 255 + 0.055) / 1.055) ** 2.4) for c in rgb8)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    bsdf.inputs["Emission Color"].default_value = (*lin, 1)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    return m


def _jobs():
    """(行, 列) → (種類, 向き, 坂)。セルの位置は way のシートの並び（dat を書く側の IMAGES）と同じ。
    種類: "arms"（向きの腕を中心からのばす）・"end"（行き止まり）・"single"・"diag"（2 辺の中点を結ぶ）"""
    jobs = {(0, 2): ("arms", "ns", None), (0, 3): ("arms", "ew", None), (0, 5): ("end", "s", None), (0, 6): ("end", "w", None),
            (0, 7): ("end", "n", None), (0, 8): ("end", "e", None), (0, 9): ("single", "", None),
            (2, 0): ("diag", "sw", None), (2, 1): ("diag", "nw", None), (2, 2): ("diag", "ne", None), (2, 3): ("diag", "se", None),
            (2, 5): ("arms", "sw", None), (2, 6): ("arms", "nw", None), (2, 7): ("arms", "ne", None), (2, 8): ("arms", "se", None),
            (3, 5): ("arms", "nse", None), (3, 6): ("arms", "new", None), (3, 7): ("arms", "nsw", None),
            (3, 8): ("arms", "sew", None), (3, 9): ("arms", "nsew", None)}
    slopes = (lambda x, y: y + _HALF, lambda x, y: _HALF - x, lambda x, y: _HALF - y, lambda x, y: x + _HALF)
    for n, base in ((1, 0), (2, 5)):
        for i, (axis, f) in enumerate(zip(("ns", "ew", "ns", "ew"), slopes)):
            jobs[(1, base + i)] = ("arms", axis, (lambda n=n, f=f: lambda x, y: n * H * f(x, y) / TILE)())
    return jobs


def _plan(kind, dirs):
    p = _mk._Plan()
    w = DESCRIBE_W
    if kind == "single":
        p.quad(-w / 2, w / 2, -w / 2, w / 2)
    elif kind == "end":
        dx, dy = _DIRS[dirs]
        p.seg((0.0, 0.0), (dx * _HALF * 1.5, dy * _HALF * 1.5), w)
        p.seg((-dy * DESCRIBE_CAP / 2, dx * DESCRIBE_CAP / 2), (dy * DESCRIBE_CAP / 2, -dx * DESCRIBE_CAP / 2), w / 2)
    elif kind == "diag":
        a, b = ((_DIRS[c][0] * _HALF, _DIRS[c][1] * _HALF) for c in dirs)
        d = (b[0] - a[0], b[1] - a[1])  # タイルの外まで延ばして、切り抜いた端が辺にそろうようにする
        p.seg((a[0] - d[0] / 2, a[1] - d[1] / 2), (b[0] + d[0] / 2, b[1] + d[1] / 2), w)
    else:
        p.quad(-w / 2, w / 2, -w / 2, w / 2)
        for c in dirs:
            dx, dy = _DIRS[c]
            p.seg((0.0, 0.0), (dx * _HALF * 1.5, dy * _HALF * 1.5), w)
    return p


def describe_sheet(sheet, rgb8, label="説"):
    """説明用の色の way のシート（4 行 × 10 列）。rgb8 は帯の色（sRGB 8bit）。アイコン（0,0）は仮の絵（AMI は icons.py が描き直す）、
    カーソル（0,1）は南北の直線。高架の物は、アイコン（0,4）・カーソル（1,4）を使う（2 つの dat が同じセルを指せないため）"""
    set_anchor(GROUND_CY)
    mat = describe_material(rgb8)
    cells = {}
    for rc, (kind, dirs, slope) in _jobs().items():
        clear_models()
        _plan(kind, dirs).emit(None, mat)
        if slope:
            for ob in list(bpy.context.scene.objects):
                if ob.type == "MESH" and ob.name.startswith("marking"):
                    apply_slope(ob, slope)
        cells[rc] = render_cell(f"{sheet}_{rc[0]}_{rc[1]}")
    cells[(0, 1)] = cells[(0, 2)]
    clear_models()
    _plan("arms", "ns").emit(None, mat)
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style="tram")
    cells[(0, 4)], cells[(1, 4)] = cells[(0, 0)], cells[(0, 1)]
    make_sheet(cells, 4, 10, os.path.join(_s.SRC, sheet + ".png"))
