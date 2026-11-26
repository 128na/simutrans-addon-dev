"""水路の踏切（crossing。線路・道路 × 運河）のシート（AMI。#117）。跳ね橋（2 枚の桁が両岸から跳ね上がる）。

本体は踏切のタイルで、2 本の way（運河と、線路か道路）の絵の上に、踏切の奥の絵（乗り物より前）と手前の絵（乗り物の後）を重ねる
（obj/crossing.cc の calc_image）。奥の絵は線路×道路の踏切（crossing.py）と同じくタイル全面を描き、下の way の絵を隠す:
    運河の直線の絵（運河の way のシートのセルをそのまま写す）→ 橋の床（下ろした桁か、岸の固定の部分）→ 奥の側の跳ね上げた桁
手前の絵は、閉じた絵（船が通る）の手前の側の跳ね上げた桁だけ。開いた絵（線路・道路の乗り物が通る）の手前の絵は空。
本体は waytype[0]（線路・道路）の乗り物が通るときに開き、waytype[1]（運河）の船が来ると閉じる（dataobj/crossing_logic.cc）。

橋の床:
- 道路: 床の板（タイルの幅いっぱい）と、床の縁の下の桁、両側の欄干。路面は、その道路の way のシートの直線のセルを写す
  （線路×道路の踏切と同じ。写したセルの sha256 を控えに書き、アドオンの検査が描き直し忘れを見つける）
- 線路: 鋼の床の板に、まくらぎとレール（線路の 4 種で共通の 1 枚）。レールは線路の way と同じ基準面（datums["rail"]）と
  横の範囲・高さで、隣の線路のタイルのレールとつなぐ
桁は岸（水面の縁 CANAL_BANK の位置）を軸に、タイルの中心へ向かって半分ずつ。開いた絵は 2 枚を下ろし、閉じた絵は RAISE_DEG 起こす。
奥・手前は運河で分ける（東西の運河は南の岸、南北の運河は東の岸が手前。船は閉じた桁の間を通る）。

シートの並び（crossing.py と同じ。dat を書く側は addons/ami/blender/ami_dat.py）:
    列 0: 線路・道路が南北（dat の [ns]）で開いた絵、列 1: 同じ向きで閉じた絵、列 2・3: 東西（[ew]）の開いた絵・閉じた絵
    行 0: 夏の奥の絵、行 1: 夏の手前の絵、行 2・3: 雪の奥・手前（dat の [1]）
"""
import math
import os

import numpy as np
from mathutils import Vector

from . import core as _core
from . import sheetlib as _s
from .canal import CANAL_BANK, CANAL_SNOW_ROWS
from .cells import GROUND_CY, ROAD_CY, make_sheet, save_rgba
from .core import TILE, _SNOW, box, clear_models, clip_to_tile, datum_move, make_material, mesh_object, set_anchor
from .crossing import CROSSING_COLS, CROSSING_SNOW_ROW, ROAD_STAMP_SUFFIX, _layer, _over, _road_cell
from .deck_track import DECK_LOOK, deck_top, deck_track

# ---------------------------------------------------------------- 寸法（タイル 1 辺 = 10）
CANAL_CROSSING_HINGE = TILE / 2 - CANAL_BANK  # 桁の軸の、タイルの中心からの距離（水面の縁）
RAISE_DEG = 78                 # 閉じた絵で桁を起こす角度（水平から）
ROAD_DECK_HALF = TILE / 2 - 0.15  # 道路の床の半幅（運河の笠石の外の縁まで）
RAIL_DECK_HALF = 1.6           # 線路の床の半幅
DECK_T = 0.08                  # 床の板の厚み
# 床の縁の下の桁の深さ（床の板の下から）。桁の下端を運河の水面（CANAL_WATER_Z = −0.45）より上に置く（水面に食い込んで見えないように。
# 2026-11-22、#117 のユーザーの確認）。道路は下端が −0.28。線路は基準面（datums["rail"]）で画面の下へ動くので、さらに浅くする
GIRDER_D = {"road": 0.20, "rail": 0.10}
GIRDER_W = 0.18                # 桁の幅
RAILING_H = 0.8                # 欄干の高さ（床から）
RAILING_W = 0.06               # 欄干の柱・手すりの太さ
RAILING_POST = 1.1             # 欄干の柱の間隔
JOINT_W = 0.08                 # 桁の継ぎ目（軸と、2 枚が出会う中心）の線の幅
_M_DECK = ("canal_crossing_deck", (0.30, 0.31, 0.32), 0.7)       # 床の板（鋼。灰色）
_M_DECK_SNOW = _SNOW
_M_GIRDER = ("canal_crossing_girder", (0.20, 0.33, 0.45), 0.6)   # 桁（青灰の塗装の鋼。道路の橋の桁の青に寄せた）
_M_RAILING = ("canal_crossing_railing", (0.85, 0.86, 0.86), 0.5)  # 欄干（白）
_M_JOINT = ("canal_crossing_joint", (0.04, 0.04, 0.04), 0.8)     # 継ぎ目
_M_ASPHALT = ("canal_crossing_asphalt", (0.035, 0.036, 0.04), 0.9)  # 起こした桁の路面（道路）
# 線路の床の材質（色は deck_track の DECK_LOOK。転車台と共通）
_M_SLEEPER = ("canal_crossing_sleeper", *DECK_LOOK["sleeper"])
_M_SLEEPER_SNOW = ("canal_crossing_sleeper_snow", *DECK_LOOK["sleeper_snow"])
_M_RAIL = ("canal_crossing_rail", *DECK_LOOK["rail_head"])
_M_RAIL_SIDE = ("canal_crossing_rail_side", *DECK_LOOK["rail_side"])

# 線路・道路の向き → (運河のセル（直線）、手前の岸の向き（線路・道路の経路の座標 s の符号）)
# 南北の線路・道路は東西の運河を渡り、手前は南の岸（s < 0）。東西の線路・道路は南北の運河を渡り、手前は東の岸（s > 0）
CANAL_CROSSING_DIRS = {"ns": ((0, 3), -1), "ew": ((0, 2), 1)}


def _to_xyz(way_dir, u, s, z):
    """経路の座標（u: 横、s: 経路に沿う向き、z: 高さ）→ タイルの座標。南北の経路は s = y、東西の経路は s = x"""
    return Vector((u, s, z)) if way_dir == "ns" else Vector((s, -u, z))


class _Part:
    """経路の座標で作る直方体の集まり（跳ね上げる桁は、作った後に軸のまわりに回す）"""

    def __init__(self):
        self.items = []  # (頂点の list（経路の座標）, 面, 材質, 名前)

    def box(self, u0, u1, s0, s1, z0, z1, mat, name):
        v, f = box((u0 + u1) / 2, (s0 + s1) / 2, (z0 + z1) / 2, abs(u1 - u0), abs(s1 - s0), abs(z1 - z0))
        self.items.append(([Vector(p) for p in v], f, mat, name))

    def box_at(self, c, mat, name):
        """中心と寸法 (u, s, z, 横, 沿う向き, 高さ) の直方体（deck_track の部品）"""
        v, f = box(*c)
        self.items.append(([Vector(p) for p in v], f, mat, name))

    def raised(self, hinge, z_h, deg):
        """軸（s = hinge、高さ z_h）のまわりに、タイルの中心の側を deg 起こした写し"""
        c = -1 if hinge > 0 else 1  # 軸からタイルの中心への向き
        t = math.radians(deg)
        out = _Part()
        for verts, f, mat, name in self.items:
            nv = []
            for p in verts:
                d, z = (p.y - hinge) * c, p.z - z_h
                d2, z2 = d * math.cos(t) - z * math.sin(t), d * math.sin(t) + z * math.cos(t)
                nv.append(Vector((p.x, hinge + c * d2, z_h + z2)))
            out.items.append((nv, f, mat, name))
        return out

    def build(self, way_dir, move=None, clip=True):
        obs = []
        for verts, f, mat, name in self.items:
            vs = [_to_xyz(way_dir, p.x, p.y, p.z) + (move if move is not None else Vector()) for p in verts]
            ob = mesh_object(name, vs, f, mat)
            if clip:
                clip_to_tile(ob, pad=0)
            obs.append(ob)
        return obs


def _railings(part, half, s0, s1, z, mat, sides=(-1, 1)):
    """床の縁（横 ±half）の欄干: 柱と手すり"""
    n = max(1, round(abs(s1 - s0) / RAILING_POST))
    for side in sides:
        u = side * (half - RAILING_W)
        part.box(u - RAILING_W / 2, u + RAILING_W / 2, s0, s1, z + RAILING_H - RAILING_W, z + RAILING_H, mat, "canal_crossing_railing_top")
        part.box(u - RAILING_W / 2, u + RAILING_W / 2, s0, s1, z + RAILING_H * 0.5 - RAILING_W / 2, z + RAILING_H * 0.5 + RAILING_W / 2,
                 mat, "canal_crossing_railing_mid")
        for i in range(n + 1):
            s = s0 + (s1 - s0) * i / n
            s = min(max(s, min(s0, s1) + RAILING_W / 2), max(s0, s1) - RAILING_W / 2)
            part.box(u - RAILING_W / 2, u + RAILING_W / 2, s - RAILING_W / 2, s + RAILING_W / 2, z, z + RAILING_H, mat,
                     "canal_crossing_railing_post")


def _leaf(kind, hinge, snow, rail, top):
    """1 枚の桁（軸 s = hinge からタイルの中心 s = 0 まで）を、下ろした形で。経路の座標の _Part を返す。
    下ろした形の床の上面は top（道路は地面の高さ 0、線路はまくらぎの下面）"""
    s0, s1 = sorted((hinge, 0.0))
    p = _Part()
    half = ROAD_DECK_HALF if kind == "road" else RAIL_DECK_HALF
    deck = make_material(_M_DECK_SNOW if snow and kind == "rail" else _M_DECK, "canal_crossing_deck")
    girder = make_material(_M_GIRDER, "canal_crossing_girder")
    p.box(-half, half, s0, s1, top - DECK_T, top, deck, "canal_crossing_deck")
    for side in (-1, 1):
        u = side * (half - GIRDER_W / 2)
        p.box(u - GIRDER_W / 2, u + GIRDER_W / 2, s0, s1, top - DECK_T - GIRDER_D[kind], top - DECK_T, girder, "canal_crossing_girder")
    _railings(p, half, s0, s1, top, make_material(_M_RAILING, "canal_crossing_railing"))
    if kind == "road":
        # 起こした桁で見える路面（下ろした絵では、写した道路のセルが上に乗る）
        p.box(-half + RAILING_W * 2, half - RAILING_W * 2, s0, s1, top - 0.005, top + 0.002,
              make_material(_M_ASPHALT, "canal_crossing_asphalt"), "canal_crossing_road")
    else:
        _rails(p, s0, s1, snow, rail, top)
    return p


def _rails(p, s0, s1, snow, rail, top):
    """まくらぎとレール（deck_track の部品。転車台と共通）。
    レールは、線路の way のレールと同じ横の範囲 rail[0]〜rail[1] と上面の高さ rail[2]"""
    sl = make_material(_M_SLEEPER_SNOW if snow else _M_SLEEPER, "canal_crossing_sleeper")
    head, side = make_material(_M_RAIL, "rail_head"), make_material(_M_RAIL_SIDE, "canal_crossing_rail_side")
    sleepers, rails = deck_track(s0, s1, top, rail)
    for c in sleepers:
        p.box_at(c, sl, "canal_crossing_sleeper")
    for web, rail_head in rails:
        p.box_at(web, side, "canal_crossing_rail_web")
        p.box_at(rail_head, head, "rail_head")


def _bank(kind, snow, rail, top, sign):
    """岸の固定の部分（軸 s = sign·HINGE からタイルの辺の外まで）。線路は床の板・まくらぎ・レール、道路は無し（道路の way の絵が見える）"""
    p = _Part()
    if kind != "rail":
        return p
    s0, s1 = sorted((sign * CANAL_CROSSING_HINGE, sign * (TILE / 2 + 0.6)))
    deck = make_material(_M_DECK_SNOW if snow else _M_DECK, "canal_crossing_deck")
    p.box(-RAIL_DECK_HALF, RAIL_DECK_HALF, s0, s1, top - DECK_T, top, deck, "canal_crossing_deck")
    _rails(p, s0, s1, snow, rail, top)
    return p


def _joints(kind, top):
    """下ろした桁の継ぎ目（2 本の軸と中心）の線"""
    p = _Part()
    half = ROAD_DECK_HALF if kind == "road" else RAIL_DECK_HALF
    mat = make_material(_M_JOINT, "canal_crossing_joint")
    z = top + (0.004 if kind == "road" else 0.0)
    for s in (-CANAL_CROSSING_HINGE, 0.0, CANAL_CROSSING_HINGE):
        p.box(-half + RAILING_W * 2, half - RAILING_W * 2, s - JOINT_W / 2, s + JOINT_W / 2, z - 0.01, z + 0.006, mat,
              "canal_crossing_joint")
    return p


def _mask(obs, all_obs, tag):
    """obs を描いた画素（不透明度 1 以上）の真偽の配列"""
    return _layer(tag, obs, all_obs)[..., 3] > 0


def canal_crossing_sheet(sheet, canal_sheet, kind, datums=None, rail=None, road_sheet=None, snow_rows=CANAL_SNOW_ROWS):
    """水路の踏切のシート。kind は "road"（road_sheet の道路の直線のセルを床の路面に写す）か "rail"（共通の線路の床）。
    canal_sheet は運河の way のシートのファイル名（src/ の中。先に描いておく）で、その直線のセルを奥の絵の下地に写す。
    datums・rail は線路の way の基準面とレール (内側, 外側, 上面)（kind が rail のとき。crossing.py と同じ渡し方）"""
    if kind not in ("road", "rail"):
        raise SystemExit(f"[canal_crossing] kind は road か rail: {kind}")
    if kind == "rail" and (datums is None or rail is None or len(rail) != 3):
        raise SystemExit("[canal_crossing] 線路の床には datums と rail（内側, 外側, 上面）が要る")
    canal_png = os.path.join(_core.SRC, canal_sheet)
    road_png = os.path.join(_core.SRC, road_sheet) if road_sheet else None
    for p in (canal_png, road_png):
        if p is not None and not os.path.exists(p):
            raise SystemExit(f"[canal_crossing] 写すシートが無い（先に描く）: {p}")
    # 道路は道路・運河と同じ位置（ROAD_CY）、線路はレールを隣の線路のタイルとつなぐので線路と同じ位置（GROUND_CY）。どちらも dat は -64,-32
    set_anchor(ROAD_CY if kind == "road" else GROUND_CY)
    move = datum_move(datums["rail"]) if kind == "rail" else None
    top = 0.0 if kind == "road" else deck_top(rail)
    cells, stamp = {}, []
    for snow in (False, True):
        for way_dir, (canal_cell, near) in CANAL_CROSSING_DIRS.items():
            if _core.ONLY and way_dir not in _core.ONLY:
                continue
            r, c = canal_cell
            base = _road_cell(canal_png, r + (snow_rows if snow else 0), c, stamp)
            road = None
            if road_png:
                rr, rc = {"ns": (0, 2), "ew": (0, 3)}[way_dir]
                road = _road_cell(road_png, rr + (snow_rows if snow else 0), rc, stamp)
            for closed in (False, True):
                clear_models()
                tag = f"{sheet}_{'snow_' if snow else ''}{way_dir}_{'closed' if closed else 'open'}"
                leaves = {sgn: _leaf(kind, sgn * CANAL_CROSSING_HINGE, snow, rail, top) for sgn in (-1, 1)}
                if closed:
                    leaves = {sgn: lf.raised(sgn * CANAL_CROSSING_HINGE, top - DECK_T - GIRDER_D[kind], RAISE_DEG)
                              for sgn, lf in leaves.items()}
                far = leaves[-near].build(way_dir, move)
                near_obs = leaves[near].build(way_dir, move)
                banks = [ob for sgn in (-1, 1) for ob in _bank(kind, snow, rail, top, sgn).build(way_dir, move)]
                joints = _joints(kind, top).build(way_dir, move) if not closed else []
                bank_area = []
                if road is not None and closed:
                    # 道路の路面を写す範囲: 岸（軸の外）だけ。運河の絵で隠した道路の way の絵を写し直す
                    pb = _Part()
                    for sgn in (-1, 1):
                        s0, s1 = sorted((sgn * CANAL_CROSSING_HINGE, sgn * (TILE / 2 + 1)))
                        pb.box(-TILE, TILE, s0, s1, -0.02, 0.0, make_material(_M_JOINT, "canal_crossing_joint"), "road_bank")
                    bank_area = pb.build(way_dir)
                all_obs = far + near_obs + banks + joints + bank_area
                railing = lambda obs: [ob for ob in obs if "railing" in ob.name]
                body = lambda obs: [ob for ob in obs if "railing" not in ob.name]
                back = base
                if closed:
                    if road is not None:
                        rd = road.copy()
                        rd[..., 3] = np.where(_mask(bank_area, all_obs, tag + "_bankmask"), rd[..., 3], 0)
                        back = _over(back, rd)
                    back = _over(back, _layer(tag + "_bank", banks, all_obs))
                    back = _over(back, _layer(tag + "_far", far, all_obs))
                    front = _layer(tag + "_front", near_obs, all_obs)
                else:
                    # 下ろした桁: 床の板・桁・まくらぎ・レール → （道路は）写した路面 → 継ぎ目 → 欄干
                    back = _over(back, _layer(tag + "_deck", body(far + near_obs) + banks, all_obs))
                    if road is not None:
                        back = _over(back, road)
                    back = _over(back, _layer(tag + "_joint", joints, all_obs))
                    back = _over(back, _layer(tag + "_railing", railing(far + near_obs), all_obs))
                    front = np.zeros_like(base)
                col = CROSSING_COLS[(way_dir, closed)]
                row = CROSSING_SNOW_ROW if snow else 0
                for dr, img, part in ((0, back, "back"), (1, front, "front")):
                    path = os.path.join(_s.WORK, f"{tag}_{part}_full.png")
                    save_rgba(path, img)
                    cells[(row + dr, col)] = path
    make_sheet(cells, 2 * CROSSING_SNOW_ROW, 4, os.path.join(_s.SRC, sheet + ".png"))
    with open(os.path.join(_s.SRC, sheet + ROAD_STAMP_SUFFIX), "w", encoding="utf8", newline="\n") as f:
        f.write("".join(line + "\n" for line in stamp))

