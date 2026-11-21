"""踏切（crossing。線路 × 道路）のシート（AMI。#111）。

本体は踏切のタイルで、道路と線路の way の絵の上に、踏切の奥の絵（乗り物より前に描く）と手前の絵（乗り物の後に描く）を重ねる
（obj/crossing.cc の calc_image。踏切は way より後に並ぶ: dataobj/objlist.cc の PRI_CROSSING）。
奥の絵は pak128 の踏切と同じくタイル全面を描き、下の way の絵（道床が路面の上に出る）を隠す:
    道路の直線の絵（道路の way のシートのセルをそのまま写す）→ 線路に沿う踏板（ゴム）と、レールの頭・溝 → 奥の側の遮断機・警報機
手前の絵は、手前の側の遮断機・警報機だけ。
遮断機・警報機は日本式の第 1 種踏切（黄黒の遮断かん、黄黒の柱に X 字の標識と赤い 2 灯）で、道路の左側（左側通行）に線路を挟んで 2 基。
奥・手前は線路で分ける（東西の線路は南の側、南北の線路は東の側が手前。docs/reference/way-addon.md の 2 章の「手前/奥」）。
車は踏切のタイルの外（隣の道路のタイル）で止まるので、タイルの上を通る列車に合わせる。

シートの並び（make_sheet。dat を書く側の addons/ami/blender/ami_dat.py の CROSSING_CELLS と同じ）:
    列 0: 道路が南北（dat の [ns]）で開いた絵、列 1: 同じ向きで閉じた絵、列 2・3: 道路が東西（[ew]）の開いた絵・閉じた絵
    行 0: 夏の奥の絵、行 1: 夏の手前の絵、行 2・3: 雪の奥・手前（dat の [1]）
dat の [ns]・[ew] は waytype[0]（道路）の向き（本体は waytype[1] の線路が南北のとき [ew] の絵を使う。crossing_desc.h の get_background と
boden/grund.cc の crossing_t の作り方）。
"""
import math
import os

import numpy as np
from mathutils import Vector

from . import core as _core
from . import sheetlib as _s
from .cells import GROUND_CY, ROAD_CY, _ground_mask, load_rgba8, make_sheet, render_cell, save_rgba
from .core import (
    CELL,
    PATH_EXT,
    TILE,
    TRANSPARENT,
    box,
    clear_models,
    clip_to_tile,
    datum_move,
    make_material,
    mesh_object,
    set_anchor,
    straight,
    sweep,
)
from .track_parts import RAIL_IN, RAIL_OUT, RAIL_Z1

# ---- 踏板（線路に沿ってタイルの端から端まで。道路の路面の上に重ねる）
PANEL_HALF = 1.25          # 踏板の半幅（経路の中心から。レールの外側 0.52 の外へ約 0.7。iss・pak128 の踏切の板と同じくらい）
FLANGE_W = 0.10            # レールの内側の溝（車輪のフランジの通り道）の幅
_M_PANEL = ("crossing_panel", (0.075, 0.075, 0.08), 0.9)         # ゴムの踏板（黒灰。光が当たって画面では約 0.2 の灰）
_M_FLANGE = ("crossing_flange", (0.01, 0.01, 0.01), 0.9)          # 溝
_M_RAIL_HEAD = ("crossing_rail", (0.92, 0.91, 0.88), 0.4)   # レールの頭（車輪で磨かれた鋼。AMI の線路の RAIL_HEAD_RGB と同じ色）
_M_PANEL_SNOW = ("crossing_panel_snow", (0.80, 0.83, 0.88), 0.9)  # 雪の絵の踏板（踏まれた雪で、道床の雪より少し暗い）

# ---- 遮断機・警報機（寸法はタイル 1 辺 = 10。道路の車道の半幅は 3.6、路側の白線は 3.37）
POST_SIDE = 4.2            # 柱の、道路の中心からの距離（路側の白線の外）
POST_TRACK = 2.4           # 柱の、線路の中心からの距離（線路の道床の半幅 1.9 の外）
POST_W, POST_H = 0.12, 3.0  # 警報機の柱の太さと高さ
POST_STRIPE = 0.3          # 柱の黄黒の縞の長さ
SIGN_Z = 2.75              # X 字の標識の中心の高さ
SIGN_L, SIGN_W, SIGN_T = 1.3, 0.22, 0.04  # X 字の板の長さ・幅・厚み
SIGN_ANGLE = 30            # X 字の板の傾き（水平から、度）
LAMP_Z = 2.15              # 赤い灯の高さ
LAMP_GAP = 0.32            # 2 灯の、柱の中心からの横の距離
LAMP_SIZE = 0.2            # 灯の大きさ
LAMP_PLATE = (0.95, 0.34, 0.04)  # 灯の背板（横・縦・厚み）
GATE_IN = 0.35             # 遮断機の箱の、柱から道路の側への距離
GATE_BOX = (0.3, 0.3, 0.85)  # 遮断機の箱（横・奥行き・高さ）
ARM_W = 0.1                # 遮断かんの太さ
ARM_LEN = POST_SIDE - GATE_IN - 0.3  # 遮断かんの長さ（閉じると道路の中心の手前 0.3 まで、進む側の車線をふさぐ）
ARM_STRIPE = 0.4           # 遮断かんの黄黒の縞の長さ
_M_YELLOW = ("crossing_yellow", (0.95, 0.75, 0.05), 0.6)
_M_BLACK = ("crossing_black", (0.05, 0.05, 0.05), 0.6)
_M_BOX = ("crossing_box", (0.45, 0.45, 0.43), 0.7)
_M_PLATE = ("crossing_plate", (0.04, 0.04, 0.04), 0.7)
_M_LAMP_OFF = ("crossing_lamp_off", (0.30, 0.04, 0.04), 0.4)
_M_LAMP_ON = ("crossing_lamp_on", (1.00, 0.10, 0.05), 0.4, 0.0, 3.0)  # 閉じた絵（点灯）。光らせて暗い面でも赤く見せる
GATE_ALPHA = 128           # 遮断機・警報機の層で残す画素の不透明度（細い部品の輪郭を消しすぎない。架線の THIN_ALPHA と同じ）

# 道路の向き → (線路の経路, [(柱の位置, 道路の側への向き a, 向かってくる車の側への向き f, 手前の絵か)])
# 柱は、道路を進む車の左側（左側通行）で、線路の手前に立つ。南北の道路: 南から来る車は西の側、北から来る車は東の側
_ASSEMBLIES = {
    "ns": (("w", "e"), [((-POST_SIDE, -POST_TRACK), (1, 0), (0, -1), True),
                        ((POST_SIDE, POST_TRACK), (-1, 0), (0, 1), False)]),
    "ew": (("s", "n"), [((-POST_TRACK, POST_SIDE), (0, -1), (-1, 0), False),
                        ((POST_TRACK, -POST_SIDE), (0, 1), (1, 0), True)]),
}
_TILE_EDGE = {"n": (0, TILE / 2), "s": (0, -TILE / 2), "e": (TILE / 2, 0), "w": (-TILE / 2, 0)}
# (道路の向き, 閉じた絵か) → 列
CROSSING_COLS = {("ns", False): 0, ("ns", True): 1, ("ew", False): 2, ("ew", True): 3}
CROSSING_SNOW_ROW = 2      # 雪の絵の行のずらし（夏の奥・手前が行 0・1）


def _strip(path, u0, u1, z, th, mat, name):
    """経路に沿う、横 u0〜u1・上面 z・厚み th の帯"""
    return mesh_object(name, *sweep(path, [(u0, z - th), (u1, z - th), (u1, z), (u0, z)]), mat)


def _deck(track_path, snow, datums, rail):
    """踏板とレールの頭・溝。rail はレールの頭の横の範囲（経路の中心からの内側・外側）と上面の高さ。
    踏板の上面はレールの頭と同じ高さ。線路の way のレールと同じ基準面（datums["rail"]）で動かし、タイルの外を切る"""
    top = rail[2]
    panel = make_material(_M_PANEL_SNOW if snow else _M_PANEL, "crossing_panel")
    obs = [_strip(track_path, -PANEL_HALF, PANEL_HALF, top, top + 0.3, panel, "crossing_panel")]
    for side in (-1, 1):
        head = sorted((side * rail[0], side * rail[1]))
        flange = sorted((side * (rail[0] - FLANGE_W), side * rail[0]))
        obs.append(_strip(track_path, *head, top + 0.002, 0.01, make_material(_M_RAIL_HEAD, "rail_head"), "rail_head"))
        obs.append(_strip(track_path, *flange, top + 0.002, 0.01, make_material(_M_FLANGE, "crossing_flange"),
                          "crossing_flange"))
    move = datum_move(datums["rail"])
    for ob in obs:
        if move is not None:
            for v in ob.data.vertices:
                v.co += move
        clip_to_tile(ob)
    return obs


def _boxes_along(p0, d, length, w, n_from, mats, name, seg):
    """p0 から向き d へ長さ length の角材を、seg ごとに mats を交互に使う箱に分けて作る（黄黒の縞）"""
    d = Vector(d).normalized()
    n = max(1, round(length / seg))
    step = length / n
    rot = math.atan2(d.y, d.x) if abs(d.z) < 0.5 else 0.0
    obs = []
    for i in range(n):
        c = Vector(p0) + d * step * (i + 0.5)
        sx, sy, sz = (step, w, w) if abs(d.z) < 0.5 else (w, w, step)
        obs.append(mesh_object(name, *box(c.x, c.y, c.z, sx, sy, sz, rot=rot), mats[(i + n_from) % 2]))
    return obs


def _assembly(pos, a, f, closed):
    """遮断機と警報機 1 基。pos は柱の位置、a は道路の側（遮断かんの向き）、f は向かってくる車の側（標識・灯の面の向き）"""
    yellow, black = make_material(_M_YELLOW, "crossing_yellow"), make_material(_M_BLACK, "crossing_black")
    stripes = (yellow, black)
    p, a, f = Vector((*pos, 0.0)), Vector((*a, 0.0)), Vector((*f, 0.0))
    obs = _boxes_along(p, (0, 0, 1), POST_H, POST_W, 0, stripes, "crossing_post", POST_STRIPE)
    # X 字の標識: 道路の側の向き a と縦の面（f に直角）に、2 枚の板を ±SIGN_ANGLE 傾けて交差させる
    face = math.atan2(a.y, a.x)
    for sgn in (-1, 1):
        t = math.radians(SIGN_ANGLE) * sgn
        v, fc = box(0, 0, 0, SIGN_L, SIGN_T, SIGN_W)
        rx = [Vector((x.x * math.cos(t), x.y, x.x * math.sin(t) + x.z * math.cos(t))) for x in v]
        verts = [Vector((q.x * math.cos(face) - q.y * math.sin(face), q.x * math.sin(face) + q.y * math.cos(face), q.z))
                 + p + Vector((0, 0, SIGN_Z)) for q in rx]
        obs.append(mesh_object("crossing_sign", verts, fc, yellow))
    # 赤い灯: 黒い背板と、その両面（向かってくる側と反対の側）に 2 灯
    plate = make_material(_M_PLATE, "crossing_plate")
    c = p + Vector((0, 0, LAMP_Z))
    obs.append(mesh_object("crossing_plate", *box(c.x, c.y, c.z, LAMP_PLATE[0], LAMP_PLATE[2], LAMP_PLATE[1], rot=face), plate))
    lamp = make_material(_M_LAMP_ON if closed else _M_LAMP_OFF, "crossing_lamp")
    for side in (-1, 1):
        for face_sgn in (-1, 1):
            q = c + a * side * LAMP_GAP + f * face_sgn * (LAMP_PLATE[2] / 2 + 0.03)
            obs.append(mesh_object("crossing_lamp", *box(q.x, q.y, q.z, LAMP_SIZE, LAMP_SIZE, LAMP_SIZE, rot=face), lamp))
    # 遮断機の箱と遮断かん（閉じると道路の側へ水平、開くと真上）
    g = p + a * GATE_IN
    bx = make_material(_M_BOX, "crossing_box")
    obs.append(mesh_object("crossing_box", *box(g.x, g.y, GATE_BOX[2] / 2, GATE_BOX[0], GATE_BOX[1], GATE_BOX[2], rot=face), bx))
    pivot = g + Vector((0, 0, GATE_BOX[2] - ARM_W / 2))
    if closed:
        obs += _boxes_along(pivot, a, ARM_LEN, ARM_W, 0, stripes, "crossing_arm", ARM_STRIPE)
    else:
        obs += _boxes_along(pivot, (0, 0, 1), ARM_LEN, ARM_W, 0, stripes, "crossing_arm", ARM_STRIPE)
    return obs


def _layer(cname, obs_on, all_obs, mask=None, alpha=0):
    """all_obs のうち obs_on だけを描いた層（RGBA）。mask（無くてよい）の外と、不透明度が alpha 未満の画素は透明にする"""
    for ob in all_obs:
        ob.hide_render = ob not in obs_on
    img = load_rgba8(render_cell(cname)).copy()
    keep = img[..., 3] >= max(alpha, 1)
    if mask is not None:
        keep &= mask
    img[..., 3] = np.where(keep, np.where(alpha, 255, img[..., 3]), 0)
    return img


def _over(dst, src):
    """dst の上に src を重ねる（どちらも RGBA の uint8）"""
    a = src[..., 3:4].astype(np.float32) / 255
    out = dst.astype(np.float32)
    out[..., :3] = src[..., :3] * a + out[..., :3] * (1 - a)
    out[..., 3:4] = np.maximum(out[..., 3:4], src[..., 3:4])
    return (out + 0.5).astype(np.uint8)


def _road_cell(road_png, row, col):
    """道路の way のシート（src/ の完成した RGB のシート）の 1 セルを RGBA で。透過色（#E7FFFF）を透明にする"""
    sheet = load_rgba8(road_png)
    cell = sheet[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL].copy()
    clear = np.all(cell[..., :3] == np.array(TRANSPARENT, np.uint8), axis=-1)
    cell[..., 3] = np.where(clear, 0, 255)
    return cell


def crossing_sheet(sheet, road_sheet, datums, rail=(RAIL_IN, RAIL_OUT, RAIL_Z1), road_cells=None, road_snow_rows=4):
    """踏切のシート。road_sheet は道路の way のシートのファイル名（src/ の中。先に描いておく）で、その直線のセル（road_cells。
    既定は道路の向き → (行, 列) が ns: (0, 2)・ew: (0, 3)。雪は road_snow_rows 行下）を奥の絵の下地に写す。
    datums は線路の way の基準面（レールと踏板を datums["rail"] で動かし、隣の線路のタイルのレールとつなぐ）。
    rail はレールの頭の横の範囲と上面の高さ (内側, 外側, 上面)。踏板の上面もこの高さにする。線路の way のレールの値を渡す
    （既定は sheetlib の track_parts の値。アドオンがレールの寸法を変えたら、その値を渡さないと踏板とレールがずれる）"""
    if len(rail) != 3:
        raise SystemExit(f"[crossing] rail は (内側, 外側, 上面) の 3 つ（#129）: {rail}")
    road_cells = road_cells or {"ns": (0, 2), "ew": (0, 3)}
    road_png = os.path.join(_core.SRC, road_sheet)  # 書き出し先（_s.SRC）は SHEET_ONLY・LAYOUT で替わるが、道路は src/ から読む
    if not os.path.exists(road_png):
        raise SystemExit(f"[crossing] 道路のシートが無い（先に描く）: {road_png}")
    set_anchor(GROUND_CY)  # 線路の way と同じ（dat のオフセット -64,-32）。道路のセルは同じオフセットなので画素をそのまま写す
    deck_mask = _ground_mask(None, cy=ROAD_CY)  # 踏板は道路の路面と同じ持ち分
    cells = {}
    for snow in (False, True):
        for road_dir, (ends, assemblies) in _ASSEMBLIES.items():
            if _core.ONLY and road_dir not in _core.ONLY:
                continue
            track_path = straight(Vector(_TILE_EDGE[ends[0]]), Vector(_TILE_EDGE[ends[1]]), PATH_EXT)
            r, c = road_cells[road_dir]
            base = _road_cell(road_png, r + (road_snow_rows if snow else 0), c)
            for closed in (False, True):
                clear_models()
                deck = _deck(track_path, snow, datums, rail)
                parts = [(_assembly(pos, a, f, closed), front) for pos, a, f, front in assemblies]
                all_obs = deck + [ob for obs, _ in parts for ob in obs]
                tag = f"{sheet}_{'snow_' if snow else ''}{road_dir}_{'closed' if closed else 'open'}"
                back = _over(base, _layer(tag + "_deck", deck, all_obs, deck_mask))
                back = _over(back, _layer(tag + "_back", [ob for obs, fr in parts if not fr for ob in obs], all_obs,
                                          alpha=GATE_ALPHA))
                front = _layer(tag + "_front", [ob for obs, fr in parts if fr for ob in obs], all_obs, alpha=GATE_ALPHA)
                col = CROSSING_COLS[(road_dir, closed)]
                row = CROSSING_SNOW_ROW if snow else 0
                for dr, img, kind in ((0, back, "back"), (1, front, "front")):
                    path = os.path.join(_s.WORK, f"{tag}_{kind}_full.png")
                    save_rgba(path, img)
                    cells[(row + dr, col)] = path
    make_sheet(cells, 2 * CROSSING_SNOW_ROW, 4, os.path.join(_s.SRC, sheet + ".png"))
