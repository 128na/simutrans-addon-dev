"""部品を経路ごとに組み立てる（assemble）。基盤・行き止まりの躯体・斜めの切り口（共通の描画の道具 sheetlib の一部。tools/README.md）。"""
from dataclasses import dataclass
from typing import Callable
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .core import (  # noqa: F401
    CLIP_PAD,
    DIAG_OVERFILL,
    FLAT,
    PATH_EXT,
    TILE,
    apply_slope,
    boolean,
    box,
    clip_to_tile,
    corner_piece,
    dashes,
    datum_move,
    half_tile,
    make_material,
    material,
    merge,
    mesh_object,
    open_ends,
    prism,
    recalc_normals,
    sweep,
)
from .wall_parts import (  # noqa: F401
    BASE_H,
    TALL_PAD,
    WALL_U,
    WALL_W,
)
from .road_parts import (  # noqa: F401
    LINE_W,
)


@dataclass
class RoadTile:
    """道路の 1 タイル分の作り（where="tile"・"line" の部品が受ける）。paths は車道の中心線、lines は (path, u) か (path, u, "dash") の白線。
    corners は歩道の角を丸くするタイルの角、size は板の大きさ（アイコンは道路に沿った帯）、hw・curb_w は車道の半幅と縁石の上面の幅"""
    paths: list
    lines: list = ()
    corners: tuple = ()
    size: tuple = (TILE + 4, TILE + 4)
    hw: float = 0.0
    curb_w: float = 0.0
    turns: list = ()  # 右左折の経路（走行跡と同じ）。路肩の雪は、これにも沿って抜く（高速道路の分岐の口を雪でふさがない）

    def line_paths(self):
        """白線を (経路, 横位置, 幅) に開く。点線は SIS に合わせて太め（約2px の四角）の短い経路に分ける。"""
        out = []
        for path, u, *kind in self.lines:
            if kind and kind[0] == "dash":
                out += [(d, u, LINE_W * 2) for d in dashes(path, dash=0.45)]
            else:
                out.append((path, u, LINE_W))
        return out


def _carve(ob, tile, w, k, transfer, mat, turns=False):
    """板 ob から、車道の型（全部の経路に沿った半幅 w の帯 + 角を丸くする扇形の残り）を抜く。turns は右左折の経路でも抜くか。"""
    prof = [(-w * k, -1.0), (w * k, -1.0), (w * k, 1.0), (-w * k, 1.0)]
    geo = [sweep(p, prof) for p in list(tile.paths) + (list(tile.turns) if turns else [])]
    # 角を丸くする: 歩道の角の四角から扇形を除いた部分も抜く
    geo += [corner_piece(c, TILE / 2 - w) for c in tile.corners]
    cutter = mesh_object("cut", *merge(geo), mat)
    cutter.hide_render = True
    # sweep の面の向きは経路の向きで変わるので、外向きにそろえる（Boolean が効かなくなる）
    recalc_normals(cutter)
    boolean(ob, cutter, transfer=transfer)
    bpy.data.objects.remove(cutter, do_unlink=True)


def _part_objects(part, paths, widths, skin, tile):
    """部品の物を作る（作った順に (番号, 物) を返す）。tile は道路の板・白線の部品が受ける RoadTile。"""
    k = widths.get(part.width, 1.0)
    mat = make_material(skin.get(part.name, part.material), part.name)
    if part.where == "tile":
        ob = mesh_object(part.name, *part.shape(tile, k), mat)
        if part.carve:
            _carve(ob, tile, part.carve(tile, k), k, part.transfer, mat, part.group == "snow")
        return [(0, ob)]
    if part.where == "line":
        return [(i, mesh_object(f"{part.name}{i}", *part.shape(path, u, lw, k), mat))
                for i, (path, u, lw) in enumerate(tile.line_paths())]
    raise ValueError(part.where)


def assemble(parts, paths, datums=FLAT, slope=None, clip=True, widths=None, div=1, groups=("body",), ends=False, skin=None,
             tile=None, half=None, half_over=None):
    """部品を経路ごとに作り、乗っている基準面の分だけ動かし、slope(x,y)->z で傾け、タイルの外を切り落とす。
    widths は横幅の倍率（Part.width → 倍率。無いものは 1）。ends は経路の始点が行き止まりの端か（where="end" の部品を作る）。
    skin は材質の差し替え（部品の名前 → 材質。雪など）。
    道路: tile（RoadTile）を渡すと、where="tile" の板と "line" の白線を先に作る（板・白線・経路の部品の順）。
    half は斜めのタイルで残す半分を決める経路（切り抜いた後に、角の側の帯だけを残す。half_over は中心線を越えて残す幅）"""
    skin = skin or {}
    widths = widths or {}
    moves = {k: datum_move(d, slope, div) for k, d in datums.items()}
    obs = []
    for part in parts:
        if tile is not None and part.where in ("tile", "line") and part.group in groups:
            for i, ob in _part_objects(part, paths, widths, skin, tile):
                obs += _place(ob, part, i, paths, widths, moves)
    for i, path in enumerate(paths):
        for part in parts:
            if part.where in ("tile", "line") or part.group not in groups or (part.where == "end" and not ends)                     or (part.ground and not slope):
                continue
            geo = part.shape(path, widths.get(part.width, 1.0))
            if geo is None:
                continue
            ob = mesh_object(f"{part.name}{i}", *geo, make_material(skin.get(part.name, part.material), part.name))
            obs += _place(ob, part, i, paths, widths, moves)
    for ob in obs:
        if slope:
            apply_slope(ob, slope)
            if ob.get("ground"):
                for v in ob.data.vertices:
                    # 底は地面に、上面は地面より少し上に（厚みが 0 になると切り抜きで形が消える）
                    v.co.z = 0.0 if v.co.z < -10 else max(v.co.z, 0.02)
        if clip:
            clip_to_tile(ob, TALL_PAD if ob.get("tall") else CLIP_PAD)
            if ob.get("tall"):
                open_ends(ob, TALL_PAD)
    if half is not None:
        keeper = mesh_object("half", *half_tile(half, DIAG_OVERFILL if half_over is None else half_over),
                             material("road_curb", (0.62, 0.61, 0.59)))
        keeper.hide_render = True
        for ob in obs:
            boolean(ob, keeper, op="INTERSECT")
        bpy.data.objects.remove(keeper, do_unlink=True)
    return obs


def _place(ob, part, i, paths, widths, moves):
    """作った物に印を付け、分岐で通り道を削り、基準面の分だけ動かす。返すのは [物]（削って消えたら []）。"""
    ob["pname"], ob["pi"], ob["cut"] = part.name, i, False
    area = sum(f.area for f in ob.data.polygons)
    if part.corridor and len(paths) > 1:
        # ほかの経路の通り道に入る部分を削る。残るのは、通り道の集まりの外側の縁に立つ壁だけ。
        # 経路どうしが接する所（タイルの辺の近く）では、二つの経路の壁が同じ位置に重なる。先の経路の壁を残し、
        # 後の経路の壁は、先の経路の壁の位置まで含めて削る（重なった切れ端が、奥/手前の版で余分な壁として残った）
        k = widths.get(part.width, 1.0)
        narrow, wide = part.corridor * k - 0.02, (part.corridor + (part.thick or WALL_W)) * k + 0.02
        band = lambda w: [(-w, -1.0), (w, -1.0), (w, 3.0), (-w, 3.0)]
        cutter = mesh_object("corridor", *merge([sweep(q, band(wide if j < i else narrow))
                                                 for j, q in enumerate(paths) if j != i]),
                             make_material(part.material, part.name))
        recalc_normals(cutter)
        boolean(ob, cutter)
        bpy.data.objects.remove(cutter, do_unlink=True)
        if not ob.data.polygons:
            bpy.data.objects.remove(ob, do_unlink=True)
            return []
        ob["cut"] = sum(f.area for f in ob.data.polygons) < area * 0.98  # 通り道で一部が削られた壁
    # 動かすのは坂を当てて切り抜く前（切り抜きの余白より動く量が大きいので、後だと端が欠ける）
    move = moves[part.datum]
    if move is not None:
        for v in ob.data.vertices:
            v.co += move
    ob["tall"] = part.tall
    ob["ground"] = part.ground
    ob["centre"] = part.centre
    return [ob]


def _arc_circle(path):
    """カーブの経路の中心と半径（経路の中ほどの 3 点を通る円）。"""
    a, b, c = (Vector((q.x, q.y)) for q in (path[1], path[len(path) // 2], path[-2]))
    d = 2 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y))
    ux = (a.length_squared * (b.y - c.y) + b.length_squared * (c.y - a.y) + c.length_squared * (a.y - b.y)) / d
    uy = (a.length_squared * (c.x - b.x) + b.length_squared * (a.x - c.x) + c.length_squared * (b.x - a.x)) / d
    centre = Vector((ux, uy))
    return centre, (a - centre).length


def _beyond_prisms(walls, paths, k, wu=None, ww=None, zr=(-2, 2)):
    """残した壁それぞれの「外側」を表す柱の集まり（基盤や端の壁から削る型）。wu・ww は壁の位置と厚み（既定は線路）。
    zr は柱の高さの範囲。坂を当てた後の物を削るときは、坂の高さまで広げる（ROAD_CUT_Z）"""
    ww = ww or WALL_W
    uw = ((wu or WALL_U) + ww) * k
    cut = []
    for w in walls:
        path = [Vector((q.x, q.y)) for q in paths[w["pi"]]]
        s = -1 if w["pname"] == "wallL" else 1
        if w["pname"] == "endw":  # 行き止まりの端の壁の奥
            d = (path[1] - path[0]).normalized()
            n, p0 = Vector((d.y, -d.x)), path[0] - d * ww
            pts = [p0 + n * 30, p0 - n * 30, p0 - n * 30 - d * 30, p0 + n * 30 - d * 30]
        elif len(path) > 4:  # カーブ
            c, r = _arc_circle(path)
            m = len(path) // 2
            tn = (path[m + 1] - path[m - 1]).normalized()
            inner = (c - path[m]).dot(Vector((tn.y, -tn.x)) * s) > 0
            ring = lambda rad: [c + Vector((math.cos(a), math.sin(a))) * rad for a in
                                (2 * math.pi * i / 64 for i in range(64))]
            if inner:
                cut.append(prism([(q.x, q.y) for q in ring(r - uw)], *zr))
            elif not w["cut"]:
                a, b = ring(r + uw), ring(40.0)
                cut += [prism([(q.x, q.y) for q in (a[i], b[i], b[(i + 1) % 64], a[(i + 1) % 64])], *zr) for i in range(64)]
            continue
        else:  # 直線・斜め
            if w["cut"]:
                continue
            d = (path[-1] - path[0]).normalized()
            n = Vector((d.y, -d.x)) * s
            a, b = path[0] - d * 30, path[-1] + d * 30
            pts = [a + n * uw, b + n * uw, b + n * 40, a + n * 40]
        cut.append(prism([(q.x, q.y) for q in pts], *zr))
    return cut


# 斜めの基盤の、壁の無い側の幅（中心線から）。近い斜め（1 タイルずらした斜め 2 本、間隔は TILE / √2）の真ん中まで
DIAG_OPEN_HALF = TILE / (2 * math.sqrt(2))

DIAG_OPEN_UNDERCUT = 3.0  # 切り口の傾き（高さ 1 あたり中心線へ寄る幅）。基盤の厚み BASE_H で約 1 寄る


def _diag_open_cut(walls, path):
    """斜めの基盤のうち、壁の無い側で、中心線から DIAG_OPEN_HALF より外を削る柱。
    タイルの角まで塗ると、近い斜めの隣の線のレールを隠し、角が隣の線の壁の外へ三角に突き出す（2026-11-14、ゲームで確認）"""
    sides = {-1 if w["pname"] == "wallL" else 1 for w in walls if w["pname"] in ("wallL", "wallR")}
    p0, p1 = Vector((path[0].x, path[0].y)), Vector((path[-1].x, path[-1].y))
    d = (p1 - p0).normalized()
    cut = []
    for s in (-1, 1):
        if s in sides:
            continue
        n = Vector((d.y, -d.x)) * s
        a, b = p0 - d * 30, p1 + d * 30
        # 切り口は下ほど中心線へ寄る斜め（上面の縁は DIAG_OPEN_HALF のまま）。縦に切ると、奥の線の切り口の側面（暗い）が
        # 手前の線の床の上に線で見えた（2026-11-14、ゲームで確認）。下向きの面はカメラから見えない
        lo, hi = DIAG_OPEN_HALF - 2 * DIAG_OPEN_UNDERCUT, DIAG_OPEN_HALF + 2 * DIAG_OPEN_UNDERCUT
        verts = [Vector((q.x, q.y, -2)) for q in (a + n * lo, b + n * lo, b + n * 40, a + n * 40)]
        verts += [Vector((q.x, q.y, 2)) for q in (a + n * hi, b + n * hi, b + n * 40, a + n * 40)]
        faces = [(3, 2, 1, 0), (4, 5, 6, 7)] + [(i, (i + 1) % 4, 4 + (i + 1) % 4, 4 + i) for i in range(4)]
        cut.append((verts, faces))
    return cut


def build_base(walls, paths, k, datum, slope, div, mat, clip=True, extra_cut=None, wu=None, ww=None):
    """基盤（道床の下の板。上面が路盤の面、厚み BASE_H は橋で側面に見える）を作る。
    タイル全面の板から、残した壁の外側だけを削る。壁のない側はタイルの端まで埋まるので、
    - 並べた線路の基盤とつながる（直線・斜め・直角カーブの内側と外側）
    - 分岐・十字で、基盤が壁を突き抜けない（壁の外側は必ず削られる）
    - 壁が 1 枚も無ければタイル全面になる（中線、1 タイルだけの軌道）
    walls は残した壁の物（assemble が pname・pi・cut を付けている）。通り道で一部が削られた直線の壁は、
    削られた先に線路があるので外側を削らない（カーブの内側の壁の外側は、ほかの通り道に重ならないのでいつも削る）"""
    plate = mesh_object("base", *box(0, 0, -BASE_H / 2, TILE + 8, TILE + 8, BASE_H), material(*mat))
    plate["tall"] = False
    cut = _beyond_prisms(walls, paths, k, wu, ww) + (extra_cut or [])
    if cut:
        cutter = mesh_object("basecut", *merge(cut), material(*mat))
        recalc_normals(cutter)
        boolean(plate, cutter)
        bpy.data.objects.remove(cutter, do_unlink=True)
    move = datum_move(datum, slope, div)
    if move is not None:
        for v in plate.data.vertices:
            v.co += move
    if slope:
        apply_slope(plate, slope)
    if clip:
        clip_to_tile(plate)
    return plate


def build_start_body(path, ground, datum, mat, u=None):
    """坂のタイルから始まる橋の端（Start）の躯体: 平らな基盤の下を、坂の地面まで埋める。
    ground(x, y) は基盤の面から見た地面の高さ（0 以下）。"""
    d = (path[-1] - path[0]).normalized()
    half = TILE / 2
    # タイルの辺に頂点を置く（辺の外は地面の高さを辺のまま延ばす）
    pts = [path[0], path[0] + d * PATH_EXT, path[-1] - d * PATH_EXT, path[-1]]
    u = u or WALL_U + WALL_W
    ob = mesh_object("startbody", *sweep(pts, [(-u, -60.0), (u, -60.0), (u, -BASE_H), (-u, -BASE_H)]), material(*mat))
    ob["tall"] = False
    cl = lambda v: max(-half, min(half, v))
    for v in ob.data.vertices:
        if v.co.z < -10:
            v.co.z = min(ground(cl(v.co.x), cl(v.co.y)), -BASE_H - 0.02)
    move = datum_move(datum)
    if move is not None:
        for v in ob.data.vertices:
            v.co += move
    clip_to_tile(ob)
    return ob
