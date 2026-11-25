"""操車場（building の stop。AMI の ami_rail_yard。#115）のシート。線路の脇の構内通路（低い歩み板と柵、端に階段）を描く。

本体は駅の建物（type=stop）を、線路の上に、線路の向きと隣の駅の建物で選んだ配置（layout）で建てる。dims の 3 つ目が 8 なら
（bauer/hausbauer.cc の build_station_extension_depot。2026-11-22 にゲームで確かめた）:
    ビット 0: 線路の向き。0 = 南北、1 = 東西
    ビット 1（2）: 南・東の側に隣の駅の建物が無い（その端が切れる）
    ビット 2（4）: 北・西の側に隣の駅の建物が無い
    つまり 0・1 = 中ほど、2・3 = 南・東の端、4・5 = 北・西の端、6・7 = 1 タイル
隣の駅の建物は、乗客の駅など、ほかの駅の建物でもよい（その側は通路が続く）。

通路は線路の奥の側（南北の線路なら西、東西の線路なら北）に置き、全部を奥の絵（backimage）にする。車両は奥の絵の後に
描かれるので、通路の上に重なる。線路の側の縁は pak128 の乗客の駅のプラットフォームにそろえる（YARD_U0）。切れた端には階段を付ける。

シートの並び（addons/ami/blender/ami_dat.py の YARD_* と同じ）:
    列 0〜7: layout 0〜7
    行 0: 夏の奥の絵、行 1: 雪の奥の絵（dat の季節 [1]）
    列 8: 行 0 がアイコン、行 1 がカーソル（AMI の blender/icons.py が書く。ここでは空けておく）
絵の位置とオフセットは車庫と同じ（depot.py の BUILDING_DROP・BUILDING_OFFSET）。箱積み駅舎の箱 1 段の中に収める（#140）。
"""
import math
import os

import numpy as np

from sheet_rows import YARD_SNOW_ROW  # 雪の絵の行（夏の奥の絵が行 0）。dat を書く側も同じ定義を読む（#302）

from .cells import GROUND_CY, make_sheet, save_rgba
from .core import CELL, TILE, TRANSPARENT, clear_models, material, merge, mesh_object, set_anchor
from .depot import BUILDING_DROP, _depot_box, _depot_render_layer

YARD_LAYOUTS = 8
YARD_ICON_CELL = (0, YARD_LAYOUTS)  # アイコンのセル（行, 列）
YARD_CURSOR_CELL = (1, YARD_LAYOUTS)

# ---- 寸法（タイル 1 辺 = 10。高さ 1 段は H ≈ 2.04 で、画面の 16px）。線路の中心から奥の側へ測る
# 線路の側の縁は、pak128 の乗客の駅（train_platform_early。SNFOSstations.png の layout 6）のプラットフォームの
# 線路の側の縁にそろえる（約 1.0。まくらぎの端。2026-11-22、ユーザーの指摘「プラットフォームの線路寄りに合わせる」）。
# 道床（在来線）は ±1.9 なので、歩み板は道床の肩の上に載る
YARD_U0, YARD_U1 = 1.0, 2.2        # 歩み板の線路の側・外の側
YARD_DECK_Z = 0.55                 # 歩み板の上面の高さ（約 4px）
YARD_DECK_T = 0.08                 # 歩み板の厚み
YARD_END = TILE / 2 - 0.25         # 切れた端で、階段の下の端を置く位置（タイルの端から少し内）
YARD_STAIR_L = 1.3                 # 階段の長さ（線路に沿う）
YARD_STEPS = 4
YARD_LEG_W = 0.16                  # 脚の太さ（細いと 1px に満たず、輪郭の薄い画素として捨てられる）
YARD_PITCH = 1.25                  # 脚と柵の支柱の間隔
YARD_RAIL_H = 0.85                 # 柵の高さ（歩み板の上面から）
YARD_RAIL_T = 0.15                 # 柵の横の棒・支柱の太さ（約 1px）
YARD_RAIL_U = YARD_U1 - 0.06       # 柵の位置（外の縁）

_M_YARD_DECK = ("yard_deck", (0.46, 0.48, 0.48), 0.6)          # 歩み板（グレーチング）
_M_YARD_DECK_SNOW = ("yard_deck_snow", (0.90, 0.93, 0.97), 0.9)
_M_YARD_FRAME = ("yard_frame", (0.58, 0.58, 0.56), 0.7)        # 脚・桁
_M_YARD_RAIL = ("yard_rail", (0.86, 0.74, 0.22), 0.5)          # 柵（黄色の手すり）


def _yard_mat(spec):
    name, rgb, rough = spec
    return material(name, rgb, rough=rough)


def _yard_span(open_minus, open_plus):
    """歩み板の範囲（線路に沿う y）。つながる側はタイルの端まで、切れた側は階段の上の端まで"""
    y0 = -(YARD_END - YARD_STAIR_L) if open_minus else -TILE / 2
    y1 = (YARD_END - YARD_STAIR_L) if open_plus else TILE / 2
    return y0, y1


def build_yard(snow, open_minus, open_plus):
    """線路を y に沿わせ、奥の側を -x に置いた通路の [物]。open_minus・open_plus は -y・+y の端が切れているか（階段を付ける）"""
    x0, x1 = -YARD_U1, -YARD_U0
    y0, y1 = _yard_span(open_minus, open_plus)
    z1 = YARD_DECK_Z
    deck, frame, rail = [], [], []
    deck.append(_depot_box(x0, x1, y0, y1, z1 - YARD_DECK_T, z1))
    # 階段: 歩み板の端から外へ、YARD_STEPS 段で地面へ下りる
    for sign, is_open, y_end in ((-1, open_minus, y0), (1, open_plus, y1)):
        if not is_open:
            continue
        step = YARD_STAIR_L / YARD_STEPS
        for k in range(YARD_STEPS):
            a = y_end + sign * step * k
            b = a + sign * step
            top = z1 * (YARD_STEPS - k - 1) / YARD_STEPS + z1 / YARD_STEPS * 0.5
            deck.append(_depot_box(x0, x1, min(a, b), max(a, b), 0.0, top))  # 段は地面から積む（浮いた板に見せない）
        # 柵の端の支柱（階段の上）
        rail.append(_depot_box(-YARD_RAIL_U, -YARD_RAIL_U + YARD_RAIL_T, y_end - YARD_RAIL_T / 2, y_end + YARD_RAIL_T / 2, z1, z1 + YARD_RAIL_H))
    # 脚（両側の縁）と柵の支柱: 間隔をタイルにそろえ、隣のタイルと同じ位置に並べる
    n = int(round(TILE / YARD_PITCH))
    for k in range(n):
        y = -TILE / 2 + YARD_PITCH * (k + 0.5)
        if not (y0 + YARD_LEG_W <= y <= y1 - YARD_LEG_W):
            continue
        for x in (x0 + 0.05, x1 - 0.05 - YARD_LEG_W):
            frame.append(_depot_box(x, x + YARD_LEG_W, y - YARD_LEG_W / 2, y + YARD_LEG_W / 2, 0, z1 - YARD_DECK_T))
        rail.append(_depot_box(-YARD_RAIL_U, -YARD_RAIL_U + YARD_RAIL_T, y - YARD_RAIL_T / 2, y + YARD_RAIL_T / 2, z1, z1 + YARD_RAIL_H))
    # 柵の横の棒（上と中ほど）
    for z in (z1 + YARD_RAIL_H, z1 + YARD_RAIL_H / 2):
        rail.append(_depot_box(-YARD_RAIL_U, -YARD_RAIL_U + YARD_RAIL_T, y0, y1, z - YARD_RAIL_T, z))
    out = [mesh_object("yard_deck", *merge(deck), _yard_mat(_M_YARD_DECK_SNOW if snow else _M_YARD_DECK)),
           mesh_object("yard_frame", *merge(frame), _yard_mat(_M_YARD_FRAME)),
           mesh_object("yard_rail", *merge(rail), _yard_mat(_M_YARD_RAIL))]
    return out


def yard_layout(layout):
    """layout → (Z の回転（度）, -y の端が切れているか, +y の端が切れているか)。
    南北（ビット 0 = 0）は回さない（+y = 北、奥の側 -x = 西）。東西は -90 度回す（+y → 東、-x → 北）"""
    ew = layout & 1
    open_se = bool(layout & 2)  # 南・東の端が切れている
    open_nw = bool(layout & 4)  # 北・西の端が切れている
    if not ew:
        return 0, open_se, open_nw      # -y = 南、+y = 北
    return -90, open_nw, open_se        # -y = 西、+y = 東


def yard_sheet(sheet, work):
    """操車場のシート（8 layout × 夏・雪の奥の絵。列 8 はアイコン・カーソル）"""
    set_anchor(GROUND_CY + BUILDING_DROP)
    cells = {}
    base = os.path.basename(sheet)[:-4]
    for si, is_snow in enumerate((False, True)):
        for layout in range(YARD_LAYOUTS):
            clear_models()
            rot, open_minus, open_plus = yard_layout(layout)
            obs = build_yard(is_snow, open_minus, open_plus)
            for ob in obs:
                ob.rotation_euler.z = math.radians(rot)
            name = f"{base}_l{layout}_{'snow' if is_snow else 'summer'}_b"
            cells[(si * YARD_SNOW_ROW, layout)] = _depot_render_layer(name, obs, obs)
    empty = np.zeros((CELL, CELL, 4), np.uint8)
    empty[..., :3] = TRANSPARENT
    empty_path = os.path.join(work, f"{base}_empty.png")
    save_rgba(empty_path, empty)
    for cell in (YARD_ICON_CELL, YARD_CURSOR_CELL):
        cells[cell] = empty_path
    make_sheet(cells, 2, YARD_LAYOUTS + 1, sheet)
