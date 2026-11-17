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
    # 型は 1 つずつ順に抜く。まとめて 1 つの形にすると、分岐・十字で帯どうしが重なって自己交差になり、use_self=True（遅い）が要る。
    # 1 つの帯・扇形は自分と重ならないので use_self=False で足り、結果は同じ絵で速い
    for g in geo:
        cutter = mesh_object("cut", *merge([g]), mat)
        cutter.hide_render = True
        # sweep の面の向きは経路の向きで変わるので、外向きにそろえる（Boolean が効かなくなる）
        recalc_normals(cutter)
        boolean(ob, cutter, transfer=transfer, use_self=False)
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
             tile=None, half=None, half_over=None, path_opts=None, tall_pad=TALL_PAD):
    """部品を経路ごとに作り、乗っている基準面の分だけ動かし、slope(x,y)->z で傾け、タイルの外を切り落とす。
    widths は横幅の倍率（Part.width → 倍率。無いものは 1）。ends は経路の始点が行き止まりの端か（where="end" の部品を作る）。
    skin は材質の差し替え（部品の名前 → 材質。雪など）。
    道路: tile（RoadTile）を渡すと、where="tile" の板と "line" の白線を先に作る（板・白線・経路の部品の順）。
    half は斜めのタイルで残す半分を決める経路（切り抜いた後に、角の側の帯だけを残す。half_over は中心線を越えて残す幅）。
    tall_pad は高さのある部品をタイルの辺の外へ残す幅。
    path_opts（無くてよい）は経路の添字 → (widths, div)。その経路だけ横幅の倍率と下げ幅を変える（カーブを斜めの絵で表す T字・十字の
    斜めの部分。diag_curves）。1 回の組み立てで全部の経路を作るので、部品の添字（pi）と分岐の通り道の削り（corridor）は全部の経路で合う"""
    skin = skin or {}
    widths = widths or {}
    path_opts = path_opts or {}
    moves = {k: datum_move(d, slope, div) for k, d in datums.items()}
    # 経路ごとの横幅の倍率と動かし方（path_opts に無い経路はセルの widths・div）
    widths_of = [path_opts[i][0] if i in path_opts else widths for i in range(len(paths))]
    moves_of = [{k: datum_move(d, slope, path_opts[i][1]) for k, d in datums.items()} if i in path_opts else moves
                for i in range(len(paths))]
    obs = []
    for part in parts:
        if tile is not None and part.where in ("tile", "line") and part.group in groups:
            for i, ob in _part_objects(part, paths, widths, skin, tile):
                obs += _place(ob, part, i, paths, widths, moves)
    for i, path in enumerate(paths):
        for part in parts:
            if part.where in ("tile", "line") or part.group not in groups or (part.where == "end" and not ends)                     or (part.ground and not slope):
                continue
            geo = part.shape(path, widths_of[i].get(part.width, 1.0))
            if geo is None:
                continue
            ob = mesh_object(f"{part.name}{i}", *geo, make_material(skin.get(part.name, part.material), part.name))
            obs += _place(ob, part, i, paths, widths_of[i], moves_of[i], widths_of if path_opts else None)
            if path_opts and obs and obs[-1] is ob:
                ob["diag"] = i in path_opts
    for ob in obs:
        if slope:
            apply_slope(ob, slope)
            if ob.get("ground"):
                for v in ob.data.vertices:
                    # 底は地面に、上面は地面より少し上に（厚みが 0 になると切り抜きで形が消える）
                    v.co.z = 0.0 if v.co.z < -10 else max(v.co.z, 0.02)
        if clip:
            # 斜めの部分（path_opts）の壁は、タイルの辺の外へ残さない。経路をタイルの外へ長く延ばしてあり、辺の外に残った壁の切れ端が
            # 直線の壁の上へ 2px はみ出した（T字・十字の直線の側の壁。AMI #16 の指摘）。隣は直線のタイルで、その壁が辺まで来る
            pad = (0.0 if ob.get("diag") else tall_pad) if ob.get("tall") else CLIP_PAD
            clip_to_tile(ob, pad)
            if ob.get("tall"):
                open_ends(ob, pad)
    if half is not None:
        keeper = mesh_object("half", *half_tile(half, DIAG_OVERFILL if half_over is None else half_over),
                             material("road_curb", (0.62, 0.61, 0.59)))
        keeper.hide_render = True
        for ob in obs:
            boolean(ob, keeper, op="INTERSECT")
        bpy.data.objects.remove(keeper, do_unlink=True)
    return obs


def _place(ob, part, i, paths, widths, moves, widths_of=None):
    """作った物に印を付け、分岐で通り道を削り、基準面の分だけ動かす。返すのは [物]（削って消えたら []）。
    widths_of（無くてよい）は経路ごとの横幅の倍率。あれば、ほかの経路の通り道の幅はその経路の倍率で決める"""
    ob["pname"], ob["pi"], ob["cut"] = part.name, i, False
    ob["k"] = widths.get(part.width, 1.0)
    mixed = widths_of is not None
    # 経路ごとに倍率を変えた組み立て（斜めの部分のある T字・十字）では、削られたかをタイルの中の面積で見る。
    # 斜めの部分の経路はタイルの外へ長く延ばしてあり、タイルの外だけで削られた直線の壁まで「削られた」になって、基盤が壁の外へ出た
    measure = _tile_area if mixed else (lambda o: sum(f.area for f in o.data.polygons))
    area = measure(ob) if part.corridor and len(paths) > 1 else 0.0
    if part.corridor and len(paths) > 1:
        # ほかの経路の通り道に入る部分を削る。残るのは、通り道の集まりの外側の縁に立つ壁だけ。
        # 経路どうしが接する所（タイルの辺の近く）では、二つの経路の壁が同じ位置に重なる。先の経路の壁を残し、
        # 後の経路の壁は、先の経路の壁の位置まで含めて削る（重なった切れ端が、奥/手前の版で余分な壁として残った）
        kj = lambda j: (widths_of[j] if widths_of else widths).get(part.width, 1.0)
        narrow = lambda j: part.corridor * kj(j) - 0.02
        wide = lambda j: (part.corridor + (part.thick or WALL_W)) * kj(j) + 0.02
        band = lambda w: [(-w, -1.0), (w, -1.0), (w, 3.0), (-w, 3.0)]
        others = [j for j in range(len(paths)) if j != i]
        if mixed and part.tall:
            # 壁は、ほかの経路のうちタイルの中でこの壁の側にあるものの通り道でだけ削る。斜めの部分の経路はタイルの外へ長く
            # 延ばしてあり、その通り道が反対側の壁の端まで削って、切れ端が 1px の縦線で残った（T字の直線の側の壁。AMI #16 の指摘）
            others = [j for j in others if _on_side(paths[j], paths[i], ob)]
        # 他の経路の通り道は 1 本ずつ順に削る。まとめて 1 つの形にすると、分岐・十字で帯どうしが重なって自己交差になり、
        # use_self=True（遅い）が要る。1 本の帯は自分と重ならないので use_self=False で足り、結果は同じ絵で速い（2026-11-17）
        geo = [[sweep(paths[j], band(wide(j) if j < i else narrow(j)))] for j in others]
        if mixed:
            # 経路の中心線の凸包（タイルの中）も削る。直線と斜めの部分の間（道床の凸包で埋めた所）に、直線の壁の切れ端が残った
            hull = _centre_hull(paths)
            if len(hull) >= 3:
                geo.append([prism(hull, -1.0, 3.0)])
        for g in geo:
            cutter = mesh_object("corridor", *merge(g), make_material(part.material, part.name))
            recalc_normals(cutter)
            boolean(ob, cutter, use_self=False)
            bpy.data.objects.remove(cutter, do_unlink=True)
            if not ob.data.polygons:
                break
        if not ob.data.polygons:
            bpy.data.objects.remove(ob, do_unlink=True)
            return []
        ob["cut"] = measure(ob) < area * 0.98  # 通り道で一部が削られた壁
    # 動かすのは坂を当てて切り抜く前（切り抜きの余白より動く量が大きいので、後だと端が欠ける）
    move = moves[part.datum]
    if move is not None:
        for v in ob.data.vertices:
            v.co += move
    ob["mv"] = tuple(move) if move is not None else (0.0, 0.0, 0.0)  # 基盤の削りを、この物の動きに合わせるため（build_base）
    ob["tall"] = part.tall
    ob["ground"] = part.ground
    ob["centre"] = part.centre
    ob["front"] = part.front
    return [ob]


def _tile_area(ob):
    """物のうち、タイルの中（高さのある部品の切り抜きと同じ範囲）にある部分の面積。写しを切り抜いて測る。"""
    cp = ob.copy()
    cp.data = ob.data.copy()
    bpy.context.scene.collection.objects.link(cp)
    clip_to_tile(cp, TALL_PAD)
    area = sum(f.area for f in cp.data.polygons)
    me = cp.data
    bpy.data.objects.remove(cp, do_unlink=True)
    bpy.data.meshes.remove(me)
    return area


def _on_side(other, path, ob, eps=1e-3):
    """経路 other のタイルの中の部分が、経路 path から見て物 ob（path の壁）と同じ側にあるか。
    ob が path の中心線の上にあるとき（側が決まらない）は真"""
    a, b = path[0], path[-1]
    d = b - a
    side = lambda x, y: d.x * (y - a.y) - d.y * (x - a.x)
    vs = ob.data.vertices
    cx, cy = sum(v.co.x for v in vs) / len(vs), sum(v.co.y for v in vs) / len(vs)
    s = side(cx, cy)
    if abs(s) < eps:
        return True
    return any(side(x, y) * s > eps * abs(s) for x, y in _clip_points([other]))


def _clip_points(paths):
    """経路の中心線をタイルの四角で切った線分の端点（(x, y) の並び）。"""
    lim = TILE / 2
    pts = []
    for path in paths:
        for a, b in zip(path[:-1], path[1:]):
            d = b - a
            t0, t1 = 0.0, 1.0
            ok = True
            for p, q in ((-d.x, a.x + lim), (d.x, lim - a.x), (-d.y, a.y + lim), (d.y, lim - a.y)):
                if abs(p) < 1e-12:
                    if q < 0:
                        ok = False
                    continue
                r = q / p
                if p < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
            if ok and t0 <= t1:
                pts += [(a.x + d.x * t, a.y + d.y * t) for t in (t0, t1)]
    return pts


def _centre_hull(paths):
    """経路の中心線のうちタイルの中の部分の、凸包の頂点（反時計回りの (x, y)）。"""
    lim = TILE / 2
    pts = []
    for path in paths:
        for a, b in zip(path[:-1], path[1:]):
            # 線分をタイルの四角で切る（Liang-Barsky）
            d = b - a
            t0, t1 = 0.0, 1.0
            ok = True
            for p, q in ((-d.x, a.x + lim), (d.x, lim - a.x), (-d.y, a.y + lim), (d.y, lim - a.y)):
                if abs(p) < 1e-12:
                    if q < 0:
                        ok = False
                    continue
                r = q / p
                if p < 0:
                    t0 = max(t0, r)
                else:
                    t1 = min(t1, r)
            if ok and t0 <= t1:
                pts += [(a.x + d.x * t, a.y + d.y * t) for t in (t0, t1)]
    pts = sorted(set((round(x, 6), round(y, 6)) for x, y in pts))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _arc_circle(path):
    """カーブの経路の中心と半径（経路の中ほどの 3 点を通る円）。"""
    a, b, c = (Vector((q.x, q.y)) for q in (path[1], path[len(path) // 2], path[-2]))
    d = 2 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y))
    ux = (a.length_squared * (b.y - c.y) + b.length_squared * (c.y - a.y) + c.length_squared * (a.y - b.y)) / d
    uy = (a.length_squared * (c.x - b.x) + b.length_squared * (a.x - c.x) + c.length_squared * (b.x - a.x)) / d
    centre = Vector((ux, uy))
    return centre, (a - centre).length


def _beyond_prisms(walls, paths, k, wu=None, ww=None, zr=(-2, 2), ref_move=None):
    """残した壁それぞれの「外側」を表す柱の集まり（基盤や端の壁から削る型）。wu・ww は壁の位置と厚み（既定は線路）。
    zr は柱の高さの範囲。坂を当てた後の物を削るときは、坂の高さまで広げる（ROAD_CUT_Z）。
    経路ごとに倍率を変えて組み立てた壁（assemble の path_opts。印 "diag" が付く）は、壁の物の横幅の倍率（k）を使う
    （T字・十字の斜めの部分は倍率が違う。diag_curves）。
    ref_move（無くてよい）は削られる物の動き。そうした壁の動き（mv）と違えば、柱をその差だけずらす（斜めの部分は下げ幅が半分）"""
    ww = ww or WALL_W
    cut = []
    for w in walls:
        mixed = "diag" in w
        uw = ((wu or WALL_U) + ww) * (w["k"] if mixed else k)
        path = [Vector((q.x, q.y)) for q in paths[w["pi"]]]
        s = -1 if w["pname"] == "wallL" else 1
        shift = None
        if ref_move is not None and mixed:
            dv = Vector(w["mv"]) - Vector(ref_move)
            shift = dv if dv.length > 1e-6 else None
        if w["pname"].startswith("endw"):  # 行き止まりの端の壁の奥
            d = (path[1] - path[0]).normalized()
            n, p0 = Vector((d.y, -d.x)), path[0] - d * ww
            if w["pname"] == "endw_edge":  # 端の壁がタイルの端に立つ（end_wall_at_edge）: 奥はタイルの外
                p0 = path[0] - d * _reach_edge(path)
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
            d = (path[-1] - path[0]).normalized()
            n = Vector((d.y, -d.x)) * s
            # T字・十字の斜めの部分（カーブの代わり）の、タイルの角の側の壁は、カーブの内側の壁と同じく、いつも外側を削る。
            # 端が直線の通り道でわずかに削られて cut になるが、外側（タイルの角）にはほかの線路が無い
            corner = mixed and w["diag"] and ((path[0] + path[-1]) / 2).dot(n) > 0.5
            if w["cut"] and not corner:
                continue
            a, b = path[0] - d * 30, path[-1] + d * 30
            pts = [a + n * uw, b + n * uw, b + n * 40, a + n * 40]
        verts, faces = prism([(q.x, q.y) for q in pts], *zr)
        if shift is not None:
            verts = [Vector(v) + shift for v in verts]
        cut.append((verts, faces))
    return cut


def _reach_edge(path):
    """経路の始点から、経路の逆向きにタイルの端までの距離（行き止まりの経路。bed_to_edge_shape と同じ求め方）。"""
    d = (path[1] - path[0]).normalized()
    return (TILE / 2 + Vector((path[0].x, path[0].y)).dot(d.to_2d())) / max(abs(d.x), abs(d.y))


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
    move = datum_move(datum, slope, div)
    cut = _beyond_prisms(walls, paths, k, wu, ww, ref_move=move) + (extra_cut or [])
    if cut:
        cutter = mesh_object("basecut", *merge(cut), material(*mat))
        recalc_normals(cutter)
        boolean(plate, cutter)
        bpy.data.objects.remove(cutter, do_unlink=True)
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
