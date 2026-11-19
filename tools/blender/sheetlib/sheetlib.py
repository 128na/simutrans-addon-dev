"""シートの組み立て（線路・道路・トンネル・アイコン）と、入口から呼ぶ run_targets（共通の描画の道具 sheetlib の一部。tools/README.md）。"""
from dataclasses import dataclass, replace
from typing import Callable
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from .core import (  # noqa: F401
    CELL,
    LAYOUT,
    DIAG_HALF,
    DIAG_OVERFILL,
    FLAT,
    H,
    NEAR_AXIS,
    ONLY,
    ORTHO,
    PATH_EXT,
    PX_PER_UNIT,
    ROAD_PROFILES,
    SNOW_SKIN,
    SRC,
    TILE,
    TRACK_PROFILES,
    WORK,
    apply_slope,
    arc,
    boolean,
    box,
    clear_models,
    clip_to_tile,
    datum_move,
    material,
    merge,
    mesh_object,
    near_camera,
    recalc_normals,
    set_anchor,
    setup_scene,
    straight,
)
from .track_parts import (  # noqa: F401
    BED_FILLS,
    bed_fill_shape,
    DIAG_BALLAST,
    DIAG_RAIL,
    TRACK_EXTRAS,
    TRACK_PARTS,
    TRACK_SNOW_WEAR_SKIN,
    TRACK_WEAR_SKIN,
)
from .catenary_parts import (  # noqa: F401
    CAT_POLE_TOP,
    is_catenary,
)
from .wall_parts import (  # noqa: F401
    BASE_H,
    ELEV_BODY_D,
    ELEV_BODY_DIAG_INSET,
    ELEV_BODY_INSET,
    ELEV_STEPS,
    PIER_ACROSS_K,
    PIER_FOOT,
    PIER_RISE,
    PIER_SIZE,
    PIER_TOP_OVERLAP,
    PIER_GATE_BEAM_D,
    PIER_GATE_BEAM_EMBED,
    PIER_GATE_POST,
    _M_PIER_BEAM,
    _M_PIER_POST,
    WALL_U,
    _M_ELEV_BODY,
    _M_PIER,
    PIER_L,
    PIER_W,
    TALL_PAD,
    _M_BASE,
    _M_WALL,
)
from .road_parts import (  # noqa: F401
    CURB_W,
    DIAG_EDGE,
    EDGE_LINE,
    EXPWY_WALL_U,
    EXPWY_WALL_W,
    ROAD_CUT_Z,
    ROAD_DIAG,
    ROAD_HW,
    ROAD_PARTS,
    ROAD_SNOW_GROUPS,
    ROAD_SNOW_SKIN,
    STOP_LINE_D,
    STOP_LINE_SPAN,
    EDGE_CORNER_R,
    SWITCH_RUT_ARCS,
    WearPath,
)
from .assemble import (  # noqa: F401
    RoadTile,
    _beyond_prisms,
    _diag_open_cut,
    assemble,
    build_base,
    build_start_body,
)
from .cells import (  # noqa: F401
    GROUND_CY,
    ROAD_CY,
    _ground_mask,
    _junction,
    exits_of,
    load_rgba8,
    make_sheet,
    render_cell,
    render_layers,
    save_rgba,
)


def build_road(paths, lines, slope=None, scale=1.0, clip=True, size=TILE + 4, corners=(), half=None, hw=ROAD_HW,
               sidewalk=True, curb_w=CURB_W, half_over=DIAG_OVERFILL, groups=None, skin=None, datums=FLAT, div=1, ends=False,
               wear_paths=None, prof=None, tall_pad=None):
    """道路を部品（ROAD_PARTS）の組み立てで作る。paths は車道の中心線（複数で分岐・十字）、lines は (path, u)・(path, u, "dash")
    （分岐の口の点線）・(path, u, "cdash")（中央線の破線。区切りはタイルの辺）の白線。
    corners は歩道の角を丸くするタイルの角、half は斜めのタイルで残す半分を決める経路。
    prof は道路の描き分け（ROAD_PROFILES の値の辞書。groups・skin を使う）。無ければ sidewalk で ROAD_PROFILES の "street"（歩道あり）か
    "expressway"（歩道なし）を引く（blender-poc が登録する名前）。sidewalk=False は歩道・縁石を作らず、タイル全面をアスファルトにする
    （groups・skin を渡すとそちらが優先）。
    wear_paths を渡すと、路面の痛み（group "weathering"）を paths ではなくそちらに沿って作る（交差点の右左折、行き止まりの手前で止める跡）。
    tall_pad（無くてよい）は assemble に渡す、高さのある部品（壁）をタイルの辺の外へ残す幅"""
    if prof is None:
        prof = ROAD_PROFILES["street" if sidewalk else "expressway"]
    groups = groups or prof["groups"]
    tile = RoadTile(paths, lines, corners, size if isinstance(size, tuple) else (size, size), hw, curb_w, wear_paths or ())
    # 車線の倍率: 斜め（scale が 1 でない）は直線の 1/√2（タイルの辺で直線の車線と同じ点を通る）
    widths = {"road": scale, "lane": 1.0 if scale == 1.0 else DIAG_EDGE}
    skin = dict(prof["skin"], **(skin or {}))
    main = groups if wear_paths is None else tuple(g for g in groups if g != "weathering")
    obs = assemble(ROAD_PARTS, paths, datums, slope, clip, widths, div, main, ends,
                   skin=skin, tile=tile, half=half, half_over=half_over, **({} if tall_pad is None else {"tall_pad": tall_pad}))
    if wear_paths is not None and "weathering" in groups:
        obs += assemble(ROAD_PARTS, wear_paths, datums, slope, clip, widths, div, ("weathering",), skin=skin, half=half,
                        half_over=half_over)
    return obs


# 高速道路（SIS_E_RG1-1_01S に合わせる）: 白線の位置は一般道と同じで、歩道が無くタイル全面がアスファルト
# 画面で横向きになる斜めに直交する向きの 1 が、画面の縦で何px か（64/√2/10 ≈ 4.5px）
DIAG_PX = 64 / math.sqrt(2) / TILE

# 画面で横向きになる斜めの中央線を、半画素（0.5px）ずらす量
DIAG_CENTER_SHIFT = 0.5 / DIAG_PX

# 斜めの道路の経路をタイルの辺の中点からどれだけ外へ延ばすか（車道・縁石の型と白線）
DIAG_EXT = 8.0

# 高架・橋の道路の基盤を、路面の板（厚み 0.04）の下へ下げる量。上面が路面と同じ高さだと重なって基盤の色が出た（2026-11-14、ゲームで確認）。
# 躯体・桁も同じだけ下げる。道路用の橋脚（pier_sheet の top_drop）も同じ値で上端を合わせる
ROAD_BASE_DROP = 0.05


def road_sheet(style="street"):
    """道路のシート。style は ROAD_PROFILES の名前。プロファイルのキーのうち、無くてよいもの:
    center: 中央線の種類。"solid"（実線。既定）・"dash"（破線。区切りはタイルの辺。tile_dashes）・None（中央線なし）
    switches: 真なら分岐の絵（OTRP の switch 画像。dat の image[nse1]〜image[nsew2]）を行 2・3 の列 10〜14 に描く（シートは 15 列）。
        expressway（歩道なし）の道路だけ。絵の中身は下の switch_lines
    priority_cross: 真なら十字の分岐の絵（nsew1・nsew2。固定の道具・詳細ダイアログでだけ選べる）を、優先道路のある十字にする
        （nsew1 は南北が優先、nsew2 は東西が優先。下の priority_lines）。無ければ、nsew1 は南北の中央線と点線、nsew2 は線なし
    open_cross: 真なら通常の十字（nsew）を、交差点の中に白線を通さない開いた十字にする
        （どちらも優先道路に見せない）。無ければ、東西の中央線と両側の点線（高速道路の十字の作り）
    corner_arcs: 真なら分岐の絵（T字・十字・1・2・優先道路の十字）で、隣り合う腕の路側線を角で円弧（EDGE_CORNER_R）でつなぐ
    switch_ruts: 真なら T字の分岐の絵の 1・2 を、どちらも「1」と同じ T字の白線にし、走行跡（轍）を直進と右左折のカーブ 1 本だけにする
        （カーブは下の SWITCH_RUT_ARCS）。1 と 2 の違いは轍だけ
    drive_left: priority_cross の停止線の通行の側。真（既定）なら左側通行、偽なら右側通行（停止線が進入する車線の反対の半分へ移る）
    以下は壁を way-object に分ける版（AMI の道路の壁・高架・橋。ADR 0003）で使う。線路の track_sheet の同じ名前のキーと同じ意味:
    wall_sheet: 壁を way の絵に焼き込まず、この名前の way-object のシートに分ける（奥の絵 4 行 → 手前の絵 4 行。雪の行は無い）
    write_walls: 偽なら壁を way の絵から分けるが、壁のシートは書かない（高架・橋。壁は地上と同じ way-object を重ねる）
    wall_only: way のシートを書かず、壁のシートだけを書く（雪の絵も描かない）
    elev_body: 基盤の下に躯体を足す（深さ body_d、壁のある側は壁の外の面から body_inset 内で止める、材質 body_mat。
        既定は高架の ELEV_BODY_D・ELEV_BODY_INSET・_M_ELEV_BODY。橋の桁は body_inset=0 と桁の材質）
    curve_cells: カーブのセル（2, 5〜8）も斜めの形で描き、タイルの半分で切らない（壁の無い側をタイルの端まで。地上の基盤の版・高架）
    lower と solid を両方持つ橋は、平らなセルだけ持ち分を下へ広げる（端の坂と坂から始まる端は広げない。track_sheet と同じ）"""
    prof = ROAD_PROFILES[style]
    expwy = prof.get("expressway", False)
    prefix, groups = prof["prefix"], prof["groups"]
    half = TILE / 2
    N, S, E, W, O = (0, half), (0, -half), (half, 0), (-half, 0), (0, 0)
    arc_sw = arc((-half, -half), 0, 90)
    arc_nw = arc((-half, half), -90, 0)
    arc_ne = arc((half, half), 180, 270)
    arc_se = arc((half, -half), 90, 180)
    sn, we = straight(S, N), straight(W, E)
    center_kind = prof.get("center", "solid")
    if center_kind not in ("solid", "dash", None):
        raise SystemExit(f"[road_sheet] {style}: center は solid・dash・None のどれか: {center_kind}")

    def center(p, u=0.0):
        """中央線（無しなら空）。破線は区切りをタイルの辺にそろえる"""
        if center_kind is None:
            return []
        return [(p, u, "cdash")] if center_kind == "dash" else [(p, u)]

    both = lambda p: [(p, -EDGE_LINE)] + center(p) + [(p, EDGE_LINE)]  # 両側の白線と中央線
    # 行き止まり: 車道は奥の歩道の手前（両脇の歩道と同じ幅を残す）まで
    end = lambda d: [-Vector(d).normalized() * ROAD_HW, Vector(d) * 1.12]
    sides = lambda p: [(p, -EDGE_LINE), (p, EDGE_LINE)]
    drive_left = prof.get("drive_left", True)
    # 十字の形で描く分岐の絵の名前 → 形の元の名前（持ち分・壁の選び方・走行跡は十字と同じにする）

    corner_r = EDGE_CORNER_R if prof.get("corner_arcs") else 0.0
    E_ = EDGE_LINE
    reach = half + PATH_EXT  # 腕の白線をタイルの辺の外まで延ばす

    def arm_edge(a, s):
        """腕 a（タイルの中心から見た単位ベクトル）の、s の側（a に直角な単位ベクトル）の路側線。角の円弧の端からタイルの辺の外まで"""
        a, s = Vector(a), Vector(s)
        return ([a * (E_ + corner_r) + s * E_, a * reach + s * E_], 0.0)

    def corner_arc(a, b, n=12):
        """腕 a と腕 b（隣り合う 2 本）のあいだの角の路側線（4 分の 1 の円弧）。corner_r が 0 なら無し"""
        if not corner_r:
            return []
        a, b = Vector(a), Vector(b)
        c = (a + b) * (E_ + corner_r)
        pts = [c - a * corner_r * math.cos(t) - b * corner_r * math.sin(t)
               for t in (math.pi / 2 * i / n for i in range(n + 1))]
        # t=0 で c - a r = b(E+r) + a E（腕 b の、a の側の路側線の端）、t=π/2 で a(E+r) + b E（腕 a の、b の側の路側線の端）
        return [(pts, 0.0)]

    def corner(a, b):
        """角の円弧と、その両側の腕の路側線"""
        return corner_arc(a, b) + [arm_edge(a, b), arm_edge(b, a)]

    def mouth_dash(m, s):
        """道路（軸 m）の s の側の路側線のうち、s の向きの腕の口を渡る点線（口の幅 = その腕の両側の路側線のあいだ）"""
        m, s = Vector(m), Vector(s)
        return ([s * E_ - m * E_, s * E_ + m * E_], 0.0, "dash")

    def arm_center(a, start=None):
        """腕 a の中央線。start（タイルの中心からの距離）からタイルの辺の外まで"""
        a = Vector(a)
        return center([a * (E_ + corner_r if start is None else start), a * reach])

    AX = {"n": (0, 1), "s": (0, -1), "e": (1, 0), "w": (-1, 0)}

    def priority_lines(main):
        """優先道路のある十字の白線。main は優先道路の向き（"ns" か "ew"）。優先道路は中央線を交差点の中も通し、路側線は
        交差点の口を点線で渡す（高速道路の十字の点線と同じ）。従道路は、2 つの口の進入する車線（半分）に停止線を引き、
        中央線を停止線からタイルの辺まで引く。停止線の位置・幅は STOP_LINE_*（road_parts）"""
        p, cross_dirs = (sn, ((1, 0), (-1, 0))) if main == "ns" else (we, ((0, 1), (0, -1)))
        if prof.get("corner_arcs"):
            # 優先道路の路側線は、角の円弧の端までを実線、口を点線にする。従道路の路側線は円弧で優先道路の路側線へつなぐ
            m = Vector((0, 1)) if main == "ns" else Vector((1, 0))
            out = center(p)
            for a in cross_dirs:
                out += [mouth_dash(m, a)] + corner(a, m) + corner(a, -m)
        else:
            out = center(p) + [(p, -EDGE_LINE, "dash"), (p, EDGE_LINE, "dash")]
        for a in cross_dirs:
            a = Vector(a)
            d = -a  # 口から交差点へ進入する向き
            side = Vector((-d.y, d.x))  # 進入する向きの左。左側通行では進入する車線の側
            if not drive_left:
                side = -side
            c = a * STOP_LINE_D
            out.append(([c, c + side * STOP_LINE_SPAN], 0.0, "stop"))
            out += center([c, a * (half + PATH_EXT)])
        return out
    NE_, NW_, SE_, SW_ = (half, half), (-half, half), (half, -half), (-half, -half)
    jobs = {
        # セル位置は線路と同じ（行, 列）。最後の要素は歩道の角を丸くするタイルの角
        (0, 2): ("ns", [sn], both(sn), None),
        (0, 3): ("ew", [we], both(we), None),
        (0, 5): ("s", [end(S)], sides(end(S)), None),
        (0, 6): ("w", [end(W)], sides(end(W)), None),
        (0, 7): ("n", [end(N)], sides(end(N)), None),
        (0, 8): ("e", [end(E)], sides(end(E)), None),
        # 単独のタイル（どこにもつながらない）は SIS と同じく十字と同じ形
        (0, 9): ("single", [sn, we], [], None, (NE_, NW_, SE_, SW_)),
        (1, 0): ("up12", [sn], both(sn), lambda x, y: H * (y + half) / TILE),
        (1, 1): ("up9", [we], both(we), lambda x, y: H * (half - x) / TILE),
        (1, 2): ("up3", [sn], both(sn), lambda x, y: H * (half - y) / TILE),
        (1, 3): ("up6", [we], both(we), lambda x, y: H * (x + half) / TILE),
        (1, 5): ("up2_12", [sn], both(sn), lambda x, y: 2 * H * (y + half) / TILE),
        (1, 6): ("up2_9", [we], both(we), lambda x, y: 2 * H * (half - x) / TILE),
        (1, 7): ("up2_3", [sn], both(sn), lambda x, y: 2 * H * (half - y) / TILE),
        (1, 8): ("up2_6", [we], both(we), lambda x, y: 2 * H * (x + half) / TILE),
        (2, 5): ("curve_sw", [arc_sw], both(arc_sw), None),
        (2, 6): ("curve_nw", [arc_nw], both(arc_nw), None),
        (2, 7): ("curve_ne", [arc_ne], both(arc_ne), None),
        (2, 8): ("curve_se", [arc_se], both(arc_se), None),
        # 分岐: 直線の中央線と、枝の無い側の白線だけを引く
        (3, 5): ("nse", [sn, straight(O, E)], [(sn, 0.0), (sn, -EDGE_LINE)], None, (NE_, SE_)),
        (3, 6): ("new", [we, straight(O, N)], [(we, 0.0), (we, EDGE_LINE)], None, (NE_, NW_)),
        (3, 7): ("nsw", [sn, straight(O, W)], [(sn, 0.0), (sn, EDGE_LINE)], None, (NW_, SW_)),
        (3, 8): ("sew", [we, straight(O, S)], [(we, 0.0), (we, -EDGE_LINE)], None, (SE_, SW_)),
        (3, 9): ("nsew", [sn, we], [], None, (NE_, NW_, SE_, SW_)),
    }
    if expwy:
        # 高速道路: 行き止まりも直線と同じ絵。分岐は枝の側の路側線を点線にする
        # （経路の右が +u。南→北の経路は +u が東、西→東の経路は +u が南）。
        # 十字と単独のタイルは東西の中央線と両側の点線。カーブは dat で斜めの絵を使う（SIS と同じ）ので描かない
        dash = lambda p, u: (p, u, "dash")
        cross = center(we) + [dash(we, -EDGE_LINE), dash(we, EDGE_LINE)]
        # T字: (本線, 枝の無い側の路側線の横位置, 枝の側)。経路の右が +u（南→北は +u が東、西→東は +u が南）
        tees = {"nse": (sn, -EDGE_LINE, EDGE_LINE), "new": (we, EDGE_LINE, -EDGE_LINE),
                "nsw": (sn, EDGE_LINE, -EDGE_LINE), "sew": (we, -EDGE_LINE, EDGE_LINE)}
        tee = lambda n: center(tees[n][0]) + [(tees[n][0], tees[n][1]), dash(tees[n][0], tees[n][2])]
        # 枝の向きと、本線の軸（T字の名前 → (枝, 本線の軸)）
        tee_axes = {"nse": ("e", "n"), "new": ("n", "e"), "nsw": ("w", "n"), "sew": ("s", "e")}

        def tee_lines(n, mouth=True):
            """corner_arcs の T字の白線: 本線の中央線と、枝の無い側の実線（通り抜ける道路の路側線はそのまま）。枝の側は、
            本線の路側線を角の円弧の端まで実線にし、円弧で枝の路側線へつなぐ。mouth なら枝の口を点線で渡す（通常の T字）、
            偽なら渡さない（「1」の渡り口。枝の先はすぐ隣の道路）"""
            b, m = (Vector(AX[k]) for k in tee_axes[n])
            out = center(tees[n][0]) + [(tees[n][0], tees[n][1])] + corner(b, m) + corner(b, -m)
            return out + ([mouth_dash(m, b)] if mouth else [])
        if prof.get("corner_arcs"):
            tee = tee_lines
        if prof.get("open_cross"):
            # 開いた十字（2026-11-19、ユーザーの決定）: 交差点の中に走行車線を横切る白線を引かない（どちらも優先道路に見せない）。
            # 腕の路側線は角まで（corner_arcs なら円弧でつなぐ）、中央線は腕の口まで
            cross = []
            for a, b in (("n", "e"), ("e", "s"), ("s", "w"), ("w", "n")):
                cross += corner(AX[a], AX[b])
            for a in "nesw":
                cross += arm_center(AX[a])
        jobs.update({
            (0, 5): ("s", [sn], both(sn), None),
            (0, 6): ("w", [we], both(we), None),
            (0, 7): ("n", [sn], both(sn), None),
            (0, 8): ("e", [we], both(we), None),
            (0, 9): ("single", [sn, we], cross, None),
            (3, 5): ("nse", [sn], tee("nse"), None),
            (3, 6): ("new", [we], tee("new"), None),
            (3, 7): ("nsw", [sn], tee("nsw"), None),
            (3, 8): ("sew", [we], tee("sew"), None),
            (3, 9): ("nsew", [sn, we], cross, None),
        })
        for pos in ((2, 5), (2, 6), (2, 7), (2, 8)):
            del jobs[pos]
        if prof.get("switches"):
            # 分岐の絵（OTRP の switch 画像）。行 2 の列 10〜14 が「1」（本体の nw=false）、行 3 が「2」（nw=true）。並びは nse・new・nsw・sew・nsew
            # （線路の track_sheet と同じ）。道路の自動選択（本体の weg_t::select_switch_road_image）は、T字の枝の側の隣も T字（sew は十字も）で、
            # 本線の両隣が分岐でないときに「1」を選ぶ。道路を 2 本隣り合わせに並べて渡り口でつないだ形で、枝の先はすぐ隣の道路。
            #   1: 渡り口。枝の側の路側線を描かない（隣の道路とのあいだを開ける）。十字の 1 は南北を優先（南北の中央線を通し、東西の口を点線）
            #   2: 優先の無い交差点（固定の道具で選んだときだけ出る）。交差点の中の中央線と、枝の側の路側線を描かない。十字の 2 は線なし
            #   （switch_ruts・priority_cross で下のとおり置き換える）
            switch_lines = {
                "nse": ([(sn, -EDGE_LINE)] + center(sn), [(sn, -EDGE_LINE)]),  # corner_arcs なら下で置き換える
                "new": ([(we, EDGE_LINE)] + center(we), [(we, EDGE_LINE)]),
                "nsw": ([(sn, EDGE_LINE)] + center(sn), [(sn, EDGE_LINE)]),
                "sew": ([(we, -EDGE_LINE)] + center(we), [(we, -EDGE_LINE)]),
                "nsew": (center(sn) + [dash(sn, -EDGE_LINE), dash(sn, EDGE_LINE)], []),
            }
            if prof.get("corner_arcs"):
                for base_name in ("nse", "new", "nsw", "sew"):
                    switch_lines[base_name] = (tee_lines(base_name, mouth=False), switch_lines[base_name][1])
            if prof.get("switch_ruts"):
                # T字の 1・2 はどちらも「1」の白線（枝の無い側は実線、渡り口の点線なし）。違いは轍（走行跡）だけ（下の wear）
                for base_name in ("nse", "new", "nsw", "sew"):
                    switch_lines[base_name] = (switch_lines[base_name][0], switch_lines[base_name][0])
            if prof.get("priority_cross"):
                # 十字の分岐の絵は優先道路のある十字（2026-11-19、ユーザーの決定）。自動では出ず、固定の道具・詳細ダイアログでだけ選ぶ。
                # 本体の選択肢（feature/switch-image-override の gui/ground_info.cc）は、値 1「十字（左右が直進）」が nsew2、
                # 値 2「十字（上下が直進）」が nsew1。nsew1 は南北、nsew2 は東西を優先する（前からの nsew1 の南北優先に合わせた）
                switch_lines["nsew"] = (priority_lines("ns"), priority_lines("ew"))
            for col, (base_name, (lines1, lines2)) in enumerate(switch_lines.items()):
                paths = [sn, we] if base_name == "nsew" else [sn if "ns" in base_name else we]
                jobs[(2, 10 + col)] = (f"{base_name}1", paths, lines1, None)
                jobs[(3, 10 + col)] = (f"{base_name}2", paths, lines2, None)
    walls = prof.get("walls")
    wall_sheet, write_walls, wall_only = prof.get("wall_sheet"), prof.get("write_walls", True), prof.get("wall_only", False)
    if walls:
        # 側壁の版: 分岐は枝の経路も通す（壁を枝の口で開ける。白線はそのまま）。行き止まりは、閉じた側の辺の手前に端の壁を立てる
        # （経路の始点を壁の内側に置く。端の壁は経路の始点の奥に立つ）
        jobs.update({
            (3, 5): ("nse", [sn, straight(O, E)], jobs[(3, 5)][2], None),
            (3, 6): ("new", [we, straight(O, N)], jobs[(3, 6)][2], None),
            (3, 7): ("nsw", [sn, straight(O, W)], jobs[(3, 7)][2], None),
            (3, 8): ("sew", [we, straight(O, S)], jobs[(3, 8)][2], None),
        })
        if wall_sheet:
            # 壁を way-object に分ける版の分岐の絵も、元の T字・十字と同じ経路（枝つき）で壁・基盤・躯体を作る（白線だけが違う）。
            # 本線だけの経路にすると、枝の口に壁があるものとして床と躯体が削られる。blender-poc の壁の版は分岐の絵を持たない
            tee_paths = {"nse": [sn, straight(O, E)], "new": [we, straight(O, N)], "nsw": [sn, straight(O, W)],
                         "sew": [we, straight(O, S)], "nsew": [sn, we]}
            for pos_, job in list(jobs.items()):
                base_name = job[0].rstrip("12")
                if pos_[1] >= 10 and base_name in tee_paths:
                    jobs[pos_] = (job[0], tee_paths[base_name], *job[2:])
        for pos, name, closed, open_ in (((0, 5), "s", N, S), ((0, 6), "w", E, W), ((0, 7), "n", S, N), ((0, 8), "e", W, E)):
            d = Vector(open_).normalized()
            p_end = [Vector(closed).normalized() * EXPWY_WALL_U, Vector(open_) + d * PATH_EXT]
            # 壁を way-object に分ける版は、白線も端の壁の内側の面（経路の始点）で止める。タイルの辺まで引くと、壁と別に描いた way の絵で
            # 白線の端が壁の下の縁から 1px 出て、明るい点に見えた（AMI の道路の高架の行き止まり、2026-11-19、ゲームで確認）。
            # 壁を焼き込む版は壁の外側を削る型で消えるので変えない
            jobs[pos] = (name, [p_end], both(p_end if wall_sheet else (sn if name in "ns" else we)), None)
    # 斜めの経路はタイルの外まで十分に延ばす。45° の向きでは型の端の角が内側に入り込み、
    # 延長が短い（2.5）とタイルの端の近くで縁石が削り残されて、つなぎ目に切り欠きが出た
    diag = {
        (2, 0): ("diag_sw", straight(S, W, ext=DIAG_EXT)),
        (2, 1): ("diag_nw", straight(N, W, ext=DIAG_EXT)),
        (2, 2): ("diag_ne", straight(N, E, ext=DIAG_EXT)),
        (2, 3): ("diag_se", straight(S, E, ext=DIAG_EXT)),
    }
    # prof["curve_cells"]（無くてよい）: カーブのセル（2, 5〜8）も斜めの形で描く（線路の基盤の版の curve_cells と同じ。dat の image[sw] などが
    # このセルを指す）。斜めのセルはタイルの半分で切るので、並べた車線の直角の曲がりで、内側の線のカーブのタイルとの間に三角のすき間が出た
    # （AMI の道路の高架の複線。2026-11-19、ゲームで確認）
    curve_cells = ({(2, 5): "curve_sw", (2, 6): "curve_nw", (2, 7): "curve_ne", (2, 8): "curve_se"}
                   if prof.get("curve_cells") else {})
    if "only" in prof:
        jobs = {k_: v for k_, v in jobs.items() if v[0] in prof["only"]}
        diag = {}
        curve_cells = {}
    if wall_only:
        # 壁の way-object は分岐の絵を持たない（壁は通常の T字・十字と同じ）
        jobs = {k_: v for k_, v in jobs.items() if k_[1] < 10}
    # 走行跡の経路: 分岐・十字は直進に右左折のカーブを足す。行き止まりは中ほどから開いた側へ（閉じた側の手前で止める。WearPath.fade）
    wear = {"nse": [sn, arc_ne, arc_se], "new": [we, arc_nw, arc_ne], "nsw": [sn, arc_nw, arc_sw], "sew": [we, arc_sw, arc_se],
            "nsew": [sn, we, arc_sw, arc_nw, arc_ne, arc_se]}
    for d_name, open_ in (("s", S), ("w", W), ("n", N), ("e", E)):
        dv = Vector(open_).normalized()
        wear[d_name] = [WearPath([-dv * 1.0, Vector(open_) + dv * PATH_EXT], fade=True)]
    if prof.get("switch_ruts"):
        # T字の分岐の絵の轍: 直進と、枝とつなぐカーブ 1 本（SWITCH_RUT_ARCS の向き）
        arcs = {"sw": arc_sw, "nw": arc_nw, "ne": arc_ne, "se": arc_se}
        for sname, corner_name in SWITCH_RUT_ARCS.items():
            wear[sname] = [sn if sname[:2] == "ns" else we, arcs[corner_name]]
    # 坂のタイルから始まる橋の端（Start・Start2）: 平らな橋の絵の下に、坂の地面までの躯体を足す（線路の橋と同じ）。
    # 本体の slope_t::north は南が高い坂で、そのとき Start[N] が使われる（東西も同じく、名前と反対の側が高い）
    grounds = {}
    if prof.get("starts"):
        high = {"n": lambda x, y: (half - y) / TILE, "s": lambda x, y: (y + half) / TILE,
                "e": lambda x, y: (half - x) / TILE, "w": lambda x, y: (x + half) / TILE}
        for j, d in enumerate("nsew"):
            for col, steps, pre in ((j, 1, "start"), (5 + j, 2, "start2")):
                p_ = sn if d in "ns" else we
                jobs[(3, col)] = (f"{pre}_{d}", [p_], both(p_), None)
                grounds[f"{pre}_{d}"] = (lambda f, n: lambda x, y: n * H * (f(x, y) - 1))(high[d], steps)
    # 道路は SIS・pak128 標準と同じく、地面の菱形より 1px 下に描く（ROAD_CY）。持ち分も同じだけ下げる（下の _ground_mask）
    set_anchor(ROAD_CY)
    cells = {}
    # 行の並びは線路と同じ: 奥の絵 4 行 →（手前の絵 4 行。側壁の版）→ 雪の奥の絵 4 行 →（雪の手前の絵 4 行）。白線は雪に隠れるので描かない
    block = 8 if "front_row" in prof else 4
    variants = [(0, "", {}, groups), (block, "_snow", ROAD_SNOW_SKIN, groups + ROAD_SNOW_GROUPS)]
    wcells = {}
    if wall_only:
        variants = variants[:1]  # way-object には雪の絵が無い
    k = DIAG_EDGE / ROAD_DIAG  # 経路からの距離の倍率（scale=ROAD_DIAG を掛けると直線の 1/√2）

    def shoot(pos, row0, cname, name, paths, slope, obs, side=None):
        """組み立てた 1 タイルを描いてシートのセルに置く。側壁の版は、残す壁を選び、壁を別の層（奥の絵・手前の絵）で描く。"""
        if walls:
            kl = DIAG_EDGE if name.startswith("diag_") else 1.0
            kept = select_walls(obs, name, paths, walls)
            trim_end_walls(kept, paths, kl, None, EXPWY_WALL_U, EXPWY_WALL_W, ROAD_CUT_Z)
            # 路面・白線・走行跡・路肩の雪も、残した壁の外側を削る（基盤と同じ型）。斜めでは壁が経路から約 3.2 にあり、
            # タイルの角（3.54）までの路面が壁の外へはみ出して見えた（2026-11-15、ゲームで確認）
            # 型の柱は坂の高さまで伸ばす（ROAD_CUT_Z）。路面は坂を当てた後なので、-2〜2 では橋の端の坂（高さ H〜2H）の
            # 上の方が削れずに残り、壁の手前に路面が出て躯体にかぶさった（2026-11-15、ゲームで確認）
            beyond = _beyond_prisms(kept, paths, kl, EXPWY_WALL_U, EXPWY_WALL_W, ROAD_CUT_Z)
            if beyond:
                # 抜く形（壁の外側の角柱）は 1 つずつ順に抜く（まとめると自己交差して use_self が要り遅い。assemble._carve と同じ）
                cutters = []
                for piece in beyond:
                    c = mesh_object("roadcut", *merge([piece]), material(*_M_BASE))
                    recalc_normals(c)
                    cutters.append(c)
                for ob in [ob for ob in obs if not ob.get("tall") and not ob.get("pname", "").startswith("pier")]:
                    for cutter in cutters:
                        boolean(ob, cutter, use_self=False)
                    if not ob.data.polygons:
                        obs.remove(ob)
                        bpy.data.objects.remove(ob, do_unlink=True)
                for c in cutters:
                    bpy.data.objects.remove(c, do_unlink=True)
            if slope and prof.get("bridge"):
                # 端の坂の躯体は、assemble が上面を地面より少し上（0.02）に止めるので、坂の下の端で路面（上面 0）より上に出て
                # 路面にはみ出して見えた（2026-11-15、ゲームで確認）。上面を路面の少し下に下げる
                for ob in [ob for ob in obs if ob.get("pname") == "rampbody"]:
                    for v in ob.data.vertices:
                        h = slope(v.co.x, v.co.y)
                        v.co.z = min(v.co.z, h - 0.06) if v.co.z > 0.01 else min(0.0, h - 0.08)
            if prof.get("elevated") or prof.get("bridge"):
                if walls in ("back", "center") and name.startswith("diag_"):
                    # back・center の斜めは橋脚を描かない（線路の高架と同じ。手前の front の線の橋脚で足りる）
                    for ob in [ob for ob in obs if ob.name.startswith("pier")]:
                        obs.remove(ob)
                        bpy.data.objects.remove(ob, do_unlink=True)
                # 基盤: 路面の下の板。残した壁の外側を削り、壁の無い側はタイルの端まで埋める（並べた車線の基盤とつながる）
                base = build_base(kept, paths, kl, FLAT["bed"], slope, 1, prof.get("base_mat", _M_BASE), wu=EXPWY_WALL_U,
                                  ww=EXPWY_WALL_W)
                # 路面の板（厚み 0.04）の下に入れる。上面が路面と同じ高さだと重なって基盤の灰色が出た（2026-11-14、ゲームで確認）
                for v in base.data.vertices:
                    v.co.z -= ROAD_BASE_DROP
                obs.append(base)
                if prof.get("elev_body"):
                    # 躯体（高架）・桁（橋）: 基盤の下の板。基盤と同じ決め方で削り、壁のある側は壁の外の面から body_inset 内で止める
                    body = build_base(kept, paths, kl, FLAT["bed"], slope, 1, prof.get("body_mat", _M_ELEV_BODY),
                                      wu=EXPWY_WALL_U - prof.get("body_inset", ELEV_BODY_INSET), ww=EXPWY_WALL_W, z0=-BASE_H,
                                      depth=prof.get("body_d", ELEV_BODY_D), name="elev_body")
                    for v in body.data.vertices:
                        v.co.z -= ROAD_BASE_DROP
                    obs.append(body)
                if name in grounds:
                    obs.append(build_start_body(paths[0], grounds[name], FLAT["bed"], _M_BASE, u=EXPWY_WALL_U + EXPWY_WALL_W))
                    slope = grounds[name]  # 持ち分を、坂の地面まで下へ広げる
        lower, solid = prof.get("lower", 0), prof.get("solid", False)
        if solid and (slope or name in grounds):
            # 地面に接する橋の端（端の坂・坂から始まる端）では持ち分を下へ広げない（坂の低い側で地面より下の基盤・躯体が描かれる。
            # track_sheet と同じ）。blender-poc の橋は lower を持たないので変わらない
            lower = 0
        if wall_sheet and any(ob.get("tall") for ob in obs):
            # 壁を way-object に分ける版: 本体（壁なし）は way のシート、壁は way-object のシート（夏の絵だけ）へ
            body_path, wback, wfront = render_layers(cname, obs, True, exits_of(name), slope, ROAD_CY, 0, WALL_RISE, solid, lower,
                                                     side=side, separate=True, tall_layers=row0 == 0 and write_walls)
            cells[(pos[0] + row0, pos[1])] = body_path
            if wback:
                wcells[pos] = wback
            if wfront:
                wcells[(pos[0] + WALL_FRONT_ROW, pos[1])] = wfront
        elif any(ob.get("tall") for ob in obs):
            cells[(pos[0] + row0, pos[1])], front = render_layers(cname, obs, True, exits_of(name), slope, ROAD_CY, 0,
                                                                  WALL_RISE, solid, lower, side=side)
            if front:
                cells[(pos[0] + row0 + prof["front_row"], pos[1])] = front
        else:
            cells[(pos[0] + row0, pos[1])] = render_cell(cname, exits_of(name), slope=slope, side=side, cy=ROAD_CY, solid=solid,
                                                         lower=lower)

    for row0, suffix, skin, grp in variants:
        kw = dict(sidewalk=not expwy, groups=grp, skin=skin, prof=prof)
        cn = lambda name: prefix + suffix.lstrip("_") + ("_" if suffix else "") + name
        for pos, (name, paths, lines, slope, *rest) in jobs.items():
            clear_models()
            # 壁を way-object に分ける版の坂: 壁をタイルの外へ長めに残す（track_sheet と同じ。坂の上がった側の端で壁の最後の列が欠ける）
            obs = build_road(paths, lines, slope, corners=rest[0] if rest else (), ends=name in ("s", "w", "n", "e"),
                             wear_paths=wear.get(name, wear.get(_junction(name))),
                             tall_pad=SLOPE_WALL_PAD if wall_sheet and slope else None, **kw)
            shoot(pos, row0, cn(name), name, paths, slope, obs)

        def build_diag(name, path, over=DIAG_OVERFILL, cut_half=True):
            """斜めのタイル 1 枚を組み立てる。cut_half なら Simutrans の斜めの絵と同じく角の側の半分だけを残す（カーブのセルは偽）"""
            # 画面で横向きになる斜め（se・nw）は、中央線がちょうど画素の行の境に乗り、2行に分かれて灰色に見える。
            # 半画素ずらして1行に収める（どちらも南東の側へ。sweep の +u は se で南東、nw で北西）
            c = {"diag_se": DIAG_CENTER_SHIFT, "diag_nw": -DIAG_CENTER_SHIFT}.get(name, 0.0) / ROAD_DIAG
            e = EDGE_LINE * k
            if name in ("diag_se", "diag_nw"):
                # 路側の白線も、経路（画素の行の境）からの距離を「整数 + 0.5」px に丸めて1行に収める（約 0.3px 内へ）。
                # 縦向きの斜め（sw・ne）はそのままで列に収まる。両方を同時に収める EDGE_LINE は無い
                e = (math.floor(EDGE_LINE * DIAG_EDGE * DIAG_PX) + 0.5) / DIAG_PX / ROAD_DIAG
            return build_road([path], [(path, -e)] + center(path, c) + [(path, e)], scale=ROAD_DIAG,
                              half=path if cut_half else None, hw=ROAD_HW * k, curb_w=CURB_W * DIAG_EDGE, half_over=over, **kw)

        for pos, (name, path) in diag.items():
            clear_models()
            obs = build_diag(name, path)
            shoot(pos, row0, cn(name), name, [path], None, obs, side=DIAG_HALF[name])
        for pos, name in curve_cells.items():
            # カーブのセルを斜めの形で描く（prof["curve_cells"]）。斜めのセルとの違いは、タイルの半分で切らないことだけ。
            # 路面・基盤・躯体は、壁の無い側をタイルの端まで延ばす（壁のある側は _beyond_prisms と基盤の決め方で壁の外の面で止まる）
            d_name = name.replace("curve_", "diag_")
            clear_models()
            path = next(p for n, p in diag.values() if n == d_name)
            obs = build_diag(d_name, path, cut_half=False)
            shoot(pos, row0, cn(name), d_name, [path], None, obs)
        if walls:
            # 側壁の版は近い斜めの絵を持たない（線路と同じ。本体が分け合うタイルに 2 本の way を置き、back と front を組み合わせられる）
            continue
        # 近い斜め（diagonal[close1]・[close2]）: 1 タイル空けて並べた斜め 2 本が分け合う十字のタイル。
        # 絵があると分け合うタイルは十字 1 本の way になる（壁の無い線路と同じ）。斜めの 2 片をそのまま 1 枚に描き、持ち分は菱形全体。
        # 片は中心線で切って重ねない（重ねると歩道の面が二重になる）
        for pos, name, pair in (((2, 4), "close1", ("diag_nw", "diag_se")), ((2, 9), "close2", ("diag_ne", "diag_sw"))):
            clear_models()
            for d in pair:
                build_diag(d, next(p for n, p in diag.values() if n == d), over=0.0)
            cells[(pos[0] + row0, pos[1])] = render_cell(cn(name), exits_of(name), cy=ROAD_CY)

    if prof.get("piers"):
        # 橋脚: 橋の下の地面のタイルに立つ柱（高さ 1 段）。道を横切る向きに、両側の壁の下まで長い。(2, 0) が南北の橋、(2, 1) が東西の橋
        # prof["pier_box"]（無くてよい）: (道を横切る向きの長さ, 道に沿う向きの長さ, 材質)。無ければ POC の橋の柱
        set_anchor(128)
        across, along, pmat = prof.get("pier_box", (2 * EXPWY_WALL_U, PIER_W, _M_BASE))
        for col, (sx, sy) in enumerate(((across, along), (along, across))):
            clear_models()
            mesh_object("pier", *box(0, 0, H / 2, sx, sy, H), material(*pmat))
            cells[(2, col)] = render_cell(f"{prof['sheet']}_pier{col}")
        set_anchor(ROAD_CY)

    # アイコン: 道路を大きく斜めに通し、左上に最高速度を書く
    clear_models()
    long = straight((0, -12), (0, 12), ext=0.6)
    build_road([long], both(long), clip=False, size=(TILE, 26), sidewalk=not expwy, groups=groups, prof=prof)
    # 線路のシリーズと同じ型: 背景の色（道路・高速道路）、左上の最高速度、右下の印（側壁の版 S・B・C・F）、下の帯（高架・橋）
    badge = ICON_BADGE[walls] if walls and not prof.get("bridge") else None
    cells[(0, 0)] = render_icon(prefix + "icon", 0.5, shift=(-0.14, 0.2), label=prof["label"], style=prof["style"], badge=badge,
                                band=prof.get("band"))
    # カーソル: 南北の直線の絵（壁は版のとおり）の上に、アイコンと同じ色の札と最高速度
    clear_models()
    obs = build_road([sn], both(sn), sidewalk=not expwy, groups=groups, prof=prof)
    if walls:
        select_walls(obs, "ns", [sn], walls)
    cells[(0, 1)] = render_cursor(prefix + "cursor", prof["label"], prof["style"])
    if not wall_only:
        make_sheet(cells, 2 * block, 15 if prof.get("switches") else 10, os.path.join(SRC, prof["sheet"] + ".png"))
    if wall_sheet and write_walls:
        # 壁の way-object のアイコン（仮の絵。道路と同じ絵に、印と文字を書く）とカーソル（直線の壁）
        clear_models()
        build_road([long], both(long), clip=False, size=(TILE, 26), sidewalk=not expwy, groups=groups, prof=prof)
        wcells[(0, 0)] = render_icon(wall_sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=prof.get("wall_label", "W"),
                                     style=prof["style"], badge=badge)
        ns = wcells.get((0, 2)) or wcells.get((WALL_FRONT_ROW, 2))  # front の版の直線は手前の絵だけ
        if ns:
            wcells[(0, 1)] = ns
        make_sheet(wcells, 2 * WALL_FRONT_ROW, 15 if any(c >= 10 for _, c in wcells) else 10, os.path.join(SRC, wall_sheet + ".png"))


# ---------------------------------------------------------------- 各アドオン

ICON_BADGE = {"both": "S", "back": "B", "center": "C", "front": "F"}  # アイコンの右下の印（single / back / center / front）

WALL_RISE = 11  # 側壁の高さ（画面の px。持ち分を上へ広げる行数）

# 壁を way-object に分ける版（TRACK_PROFILES の wall_sheet）の、壁のシートの行の並び: 奥の絵（dat の backimage）4 行 → 手前の絵（frontimage）4 行。
# セルの位置は way のシートと同じ。way-object には雪の絵が無いので、雪の行は無い
WALL_FRONT_ROW = 4
# その版の坂のセルで、壁をタイルの辺の外へ残す幅（高さのある部品の TALL_PAD の代わり）
SLOPE_WALL_PAD = TALL_PAD * 2

# datums: 基準面ごとの下げ幅（Datum(drop, ground)）。絵の基準位置は両方とも BALLAST_DY（地面の菱形より 1px 上 = 旧の位置）。
# ground: 下げ幅のうち、地面の上での位置のずれにあたる px（datum_move）。新は道床の輪郭が地面の菱形の中心線より 1px 下
# （道床を 2px 下げ、基準位置 BALLAST_DY が 1px 上）。レールも同じ 1px（4px 下げ、うち 3px はレールの高さと基準位置の分）。
# 坂のタイルだけに効く（平地は c = 1 で、下げ幅はそのまま）
# spill: 持ち分を手前の2辺へ何行はみ出させるか（_ground_mask）。新は pak128 標準の Rail_100 と同じく 1 行。
# Rail_100 は自分の菱形の上の1行を描かないので、はみ出さないと、こちらが奥・Rail_100 が手前の継ぎ目に草の線が出た
# 新は走行面（レールとまくらぎ）を 4px、路盤（道床）を 2px 下げる。
# 道床を下げないと、直線でレールが道床の下寄りに見えた（上の余白 約 11px・下 約 6px）。Rail_100 は道床の中心がレールより約 1px 下。
# 道床を 4px 下げると、画面で縦向きの斜め（sw・ne）は辺で直線と同じ点を通る位置が無く、道床の角に段が出た。2px では段は出なかった
BALLAST_DY = -1


def select_walls(obs, name, paths, side, wall_names=None, origin=None):
    """側壁のバリエーション（複線以上を並べて作るとき用）: back はカメラから遠い側の壁だけ、front は近い側の壁だけ、center は無し。
    残さない壁は消して obs から外し、残した壁（高さのある部品）を返す。行き止まりの端の壁は、壁のある版ならいつも残す。
    手前/奥を分ける向き: T字は、まっすぐ通る道（東西か南北）に対して手前か奥かで決める（分岐の向きで壁が変わる）。
    南北の道は東が手前、東西の道は南が手前。それ以外はカメラの向き（NEAR_AXIS）。origin を渡すと、手前/奥をその点から測る。
    架線の部品（catenary_parts）は壁に数えない: 柱は壁と同じ決め方で残すか消し（center は無し）、梁・トロリ線はいつも残す。
    返すのは壁だけ（基盤・端の壁の削りに使う）"""
    axis = {"nse": Vector((1, 0, 0)), "nsw": Vector((1, 0, 0)),
            "new": Vector((0, -1, 0)), "sew": Vector((0, -1, 0))}.get(_junction(name), NEAR_AXIS)
    if origin is None and len(paths) > 1:
        origin = Vector((0, 0, 0))
    near = near_camera(obs, axis, origin=origin)
    keep = {"both": lambda ob: True, "center": lambda ob: False,
            "front": lambda ob: ob in near, "back": lambda ob: ob not in near}[side]
    walls = [ob for ob in obs if ob.get("tall") and not is_catenary(ob)]
    kept = [ob for ob in walls if ob.name.startswith("endw") or keep(ob)]
    poles = [ob for ob in obs if ob.get("tall") and is_catenary(ob) and ob["pname"].startswith("cat_pole")]
    for ob in [ob for ob in walls if ob not in kept] + [ob for ob in poles if not keep(ob)]:
        obs.remove(ob)
        bpy.data.objects.remove(ob, do_unlink=True)
    return kept


def trim_end_walls(kept, paths, k, move, wu=None, ww=None, zr=(-2, 2)):
    """行き止まりの端の壁から、残した側壁の外側を削る（側壁のある側は側壁で止まる）。move は路盤の基準面の動き。zr は _beyond_prisms と同じ"""
    end_walls = [ob for ob in kept if ob.name.startswith("endw")]
    sides = _beyond_prisms([ob for ob in kept if not ob.name.startswith("endw")], paths, k, wu, ww, zr, ref_move=move)
    if not (end_walls and sides):
        return
    cutter = mesh_object("endcut", *merge(sides), material(*_M_WALL))
    recalc_normals(cutter)
    if move is not None:
        for v in cutter.data.vertices:
            v.co += move
    for ob in end_walls:
        boolean(ob, cutter)
    bpy.data.objects.remove(cutter, do_unlink=True)


def trim_catenary(obs, kept, paths, k, move):
    """架線の梁から、残した側壁の外側を削る（壁のある側は壁の外の面で止まり、壁の無い側はタイルの端まで延びて隣の線の梁とつながる）。
    削る型は trim_end_walls と同じ（_beyond_prisms）で、高さを坂（急坂で 2 段）の上の梁まで広げる。
    低いと急坂で梁の上の部分が型からはみ出し、削った形が壊れてタイルいっぱいの塊になった"""
    beams = [ob for ob in obs if is_catenary(ob) and ob["pname"] == "cat_beam"]
    sides = [ob for ob in kept if ob["pname"] in ("wallL", "wallR")]
    if not (beams and sides):
        return
    cut = _beyond_prisms(sides, paths, k, zr=(-2, CAT_POLE_TOP + 2 * H + 4), ref_move=move)
    if not cut:
        return
    cutter = mesh_object("catcut", *merge(cut), material(*_M_WALL))
    recalc_normals(cutter)
    if move is not None:
        for v in cutter.data.vertices:
            v.co += move
    for ob in beams:
        boolean(ob, cutter)
    bpy.data.objects.remove(cutter, do_unlink=True)


def track_skin(groups, snow=False):
    """線路の材質の差し替え: 雪（SNOW_SKIN）と、汚れを使う版のまくらぎのくすみ・雪の上の汚れ。"""
    wear = "weathering" in groups
    if snow:
        return dict(SNOW_SKIN, **(TRACK_SNOW_WEAR_SKIN if wear else {}))
    return dict(TRACK_WEAR_SKIN) if wear else None


def track_profile_skin(prof, groups, snow=False):
    """描き分けの材質: track_skin の結果に、夏の絵は prof["skin"]、雪の絵は prof["snow_skin"]（どちらも無くてよい）を重ねる。"""
    return dict(track_skin(groups, snow) or {}, **prof.get("snow_skin" if snow else "skin", {})) or None


def track_body_parts(prof):
    """線路の本体の部品。prof["track_parts"]（無くてよい）があれば TRACK_PARTS を丸ごと置き換える。アイコンの線路もこの部品で描く。"""
    return tuple(prof.get("track_parts", TRACK_PARTS))


def track_sheet_parts(prof):
    """シートに描く部品: 本体 + prof["parts"]（無くてよい。追加の部品）+ TRACK_EXTRAS。
    prof["replace"]（無くてよい）: 部品の名前 → 差し替える部品（形だけを変える。名前は同じにして、材質の差し替えと汚れの色をそのまま使う）"""
    swap = prof.get("replace", {})
    return tuple(swap.get(p.name, p) for p in track_body_parts(prof) + tuple(prof.get("parts", ())) + TRACK_EXTRAS)


# 斜めの部分の横幅の倍率（Part.width → 倍率）
DIAG_WIDTHS = {"gauge": DIAG_RAIL, "bed": DIAG_BALLAST}


def track_sheet(profile="new"):
    prof = TRACK_PROFILES[profile]
    half = TILE / 2
    N, S, E, W, O = (0, half), (0, -half), (half, 0), (-half, 0), (0, 0)
    up = lambda f: (lambda x, y: f(x, y))
    # 隣り合う2辺をつなぐカーブ（中心はその2辺が交わる角）
    arc_sw = arc((-half, -half), 0, 90)
    arc_nw = arc((-half, half), -90, 0)
    arc_ne = arc((half, half), 180, 270)
    arc_se = arc((half, -half), 90, 180)
    jobs = {
        # セル位置は iss の線路 dat と同じ（行, 列）
        (0, 2): ("ns", [straight(S, N)], None),
        (0, 3): ("ew", [straight(W, E)], None),
        (0, 5): ("s", [[Vector(O), Vector(S) + Vector((0, -PATH_EXT))]], None),
        (0, 6): ("w", [[Vector(O), Vector(W) + Vector((-PATH_EXT, 0))]], None),
        (0, 7): ("n", [[Vector(O), Vector(N) + Vector((0, PATH_EXT))]], None),
        (0, 8): ("e", [[Vector(O), Vector(E) + Vector((PATH_EXT, 0))]], None),
        (0, 9): ("single", [[Vector((0, -1.8)), Vector((0, 1.8))]], None),
        (1, 0): ("up12", [straight(S, N)], up(lambda x, y: H * (y + half) / TILE)),
        (1, 1): ("up9", [straight(W, E)], up(lambda x, y: H * (half - x) / TILE)),
        (1, 2): ("up3", [straight(S, N)], up(lambda x, y: H * (half - y) / TILE)),
        (1, 3): ("up6", [straight(W, E)], up(lambda x, y: H * (x + half) / TILE)),
        (1, 5): ("up2_12", [straight(S, N)], up(lambda x, y: 2 * H * (y + half) / TILE)),
        (1, 6): ("up2_9", [straight(W, E)], up(lambda x, y: 2 * H * (half - x) / TILE)),
        (1, 7): ("up2_3", [straight(S, N)], up(lambda x, y: 2 * H * (half - y) / TILE)),
        (1, 8): ("up2_6", [straight(W, E)], up(lambda x, y: 2 * H * (x + half) / TILE)),
        (2, 0): ("diag_sw", [straight(S, W, ext=2.5)], None),
        (2, 1): ("diag_nw", [straight(N, W, ext=2.5)], None),
        (2, 2): ("diag_ne", [straight(N, E, ext=2.5)], None),
        (2, 3): ("diag_se", [straight(S, E, ext=2.5)], None),
        # 近い斜め（本体の diagonal[close1]・[close2]）: 1 タイル空けて並べた斜め 2 本が 1 つのタイル（十字）に入るときの絵。
        # close1 は北西と南東の角の 2 片、close2 は北東と南西の角の 2 片（本体 way_desc_t::get_close_diagonal_image_id）
        (2, 4): ("close1", [straight(N, W, ext=2.5), straight(S, E, ext=2.5)], None),
        (2, 9): ("close2", [straight(N, E, ext=2.5), straight(S, W, ext=2.5)], None),
        (2, 5): ("curve_sw", [arc_sw], None),
        (2, 6): ("curve_nw", [arc_nw], None),
        (2, 7): ("curve_ne", [arc_ne], None),
        (2, 8): ("curve_se", [arc_se], None),
        # 分岐（T字）: 直線 + 枝の方向へ両側から入るカーブ。どちら側へ分かれても線がつながって見える
        # 十字: 直線2本 + 4方向のカーブ（斜めの線路が集まる交点にも使われる）
        (3, 5): ("nse", [straight(S, N), arc_se, arc_ne], None),
        (3, 6): ("new", [straight(W, E), arc_nw, arc_ne], None),
        (3, 7): ("nsw", [straight(S, N), arc_sw, arc_nw], None),
        (3, 8): ("sew", [straight(W, E), arc_sw, arc_se], None),
        (3, 9): ("nsew", [straight(S, N), straight(W, E), arc_sw, arc_nw, arc_ne, arc_se], None),
    }
    # 分岐の絵（OTRP の switch 画像。dat の image[nse1]〜image[nsew2]）: まくらぎとレールだけを、直線 + 片側のカーブにする。
    # 道床・側壁・基盤は元の T字・十字と同じ（片側のカーブだけで組むと、カーブの内側に丸い壁が立ち、隣とつながらない）。
    # 行 2 の列 10〜14 が「1」（本体の nw=false）、行 3 の列 10〜14 が「2」（nw=true）。並びは nse・new・nsw・sew・nsew。
    # どちらのカーブかは本体の weg_t::select_switch_image から: nse は東の隣が北西のカーブ（北へ分かれる）とき 2 で、
    # このタイルの中では南–東のカーブを通る。十字の 1 は北西–南東が直進（南西・北東のカーブ）、2 は北東–南西が直進
    switch_arcs = {"nse": (arc_ne, arc_se), "new": (arc_ne, arc_nw), "nsw": (arc_sw, arc_nw), "sew": (arc_sw, arc_se),
                   "nsew": ((arc_sw, arc_ne), (arc_nw, arc_se))}
    if prof.get("switches", True):
        for col, (base_name, arcs) in enumerate(switch_arcs.items()):
            lines = [straight(S, N), straight(W, E)] if base_name == "nsew" else [straight(S, N) if "ns" in base_name else straight(W, E)]
            full = next(v[1] for v in jobs.values() if v[0] == base_name)
            for k, a in enumerate(arcs):
                rails = lines + (list(a) if base_name == "nsew" else [a])
                if prof.get("ex_proto") == "crossover":
                    # 試作 2: 渡り線の中央の十字。直線 2 本だけの交差（カーブなし）を十字の 1・2 に入れる。T字は通常のまま
                    if base_name == "nsew":
                        rails = [straight(S, N), straight(W, E)]
                elif prof.get("ex_proto"):
                    # 試作: ex 画像の形を 1・2 の枠で見る。T字の 1 は Y字（両側のカーブだけ、直線なし）、2 は通常のまま。
                    # 十字の 1・2 は三方分岐（東西の直線 + 東へ開く／西へ開く両側のカーブ）
                    if base_name == "nsew":
                        rails = [straight(W, E)] + ([arc_ne, arc_se] if k == 0 else [arc_nw, arc_sw])
                    elif k == 0:
                        rails = list(arcs)
                jobs[(2 + k, 10 + col)] = (f"{base_name}{k + 1}", full, None, rails)
    # prof["end_from_edge"]（無くてよい）: 行き止まりのレールの終点を、閉じた側のタイルの端からタイル 1 辺のこの割合の所にする
    # （無ければタイルの中心。車止め・まくらぎ・汚れの帯は終点＝経路の始点に合わせて動く）
    if "end_from_edge" in prof:
        back = TILE * (0.5 - prof["end_from_edge"])
        for pos, (name, paths, slope, *rest) in list(jobs.items()):
            if name in ("s", "w", "n", "e"):
                p0, p1 = paths[0]
                jobs[pos] = (name, [[p0 - (p1 - p0).normalized() * back, p1]], slope, *rest)
    # dat オフセット -64,-32 と対応。持ち分は地面の菱形のまま（新描画位置は絵が 4px 下だが、持ち分を 4 行下げると、
    # 手前のタイルへはみ出した 2〜4 行目を手前の地面が消し、どのつなぎ目にも草の線が出た）
    # prof["anchor"]・prof["cy"]（無くてよい）: 絵の基準位置と持ち分の菱形の中心。路面軌道（道路の上に重ねる）は道路と同じ ROAD_CY
    cy = prof.get("cy", GROUND_CY)
    anchor = prof.get("anchor", 128 + BALLAST_DY)
    set_anchor(anchor)
    cells = {}
    parts = track_sheet_parts(prof)
    # prof["bed_fills"]（無くてよい）: 分岐のすき間を埋める層。部品の名前 → (上面の半幅, 板の下面の高さ, 板の上面の高さ)。書いた順に埋める。
    # 無ければ道床（BED_FILLS）。指定した名前の部品が無いときは、埋める層が黙って消えないように止める
    bed_fills = prof.get("bed_fills", BED_FILLS)
    missing = [n for n in prof.get("bed_fills", ()) if not any(p.name == n for p in parts)]
    if missing:
        raise SystemExit(f"[track_sheet] {profile}: bed_fills の部品が無い: {' '.join(missing)}")
    # prof["diag_curves"]（無くてよい）: pak128 標準の線路と同じく、カーブを斜めの絵で表す。カーブのセルは描かず（dat が斜めのセルを指す）、
    # T字・十字・分岐の絵のカーブを、同じ 2 辺をつなぐ斜めの直線にする。斜めの部分は斜めのセルと同じ幅・下げ幅で作り、隣の斜めのタイルとつなぐ
    # 壁の版でも使える: 直線と斜めの部分を 1 回の assemble で組み、斜めの部分だけ横幅の倍率と下げ幅を変える（path_opts）ので、
    # 壁の添字（pi）・分岐の通り道の削り（corridor）・基盤の削り（_beyond_prisms）が全部の経路で合う
    diag_of = {}
    if prof.get("diag_curves"):
        diag_paths = {id(arc_sw): ("diag_sw", straight(S, W, ext=2.5)), id(arc_nw): ("diag_nw", straight(N, W, ext=2.5)),
                      id(arc_ne): ("diag_ne", straight(N, E, ext=2.5)), id(arc_se): ("diag_se", straight(S, E, ext=2.5))}
        swap = lambda ps: [diag_paths[id(p)][1] if id(p) in diag_paths else p for p in ps]
        # prof["curve_cells"]（無くてよい）: カーブのセルも斜めの形で描く（基盤の版。dat の image[sw] などがこのセルを指す）。
        # 斜めのセルとの違いは、基盤の壁の無い側を削らないことだけ（_diag_open_cut は近い斜めの分け合うタイル用）。
        # 複線の直角の曲がりでは、内側の線のカーブのタイルの外側半分が、外側の線の直線の基盤とつながる（削ると草の三角が残った）
        fresh = {"curve_sw": (S, W), "curve_nw": (N, W), "curve_ne": (N, E), "curve_se": (S, E)}
        jobs = {k: ((v[0], [straight(*fresh[v[0]], ext=2.5)], v[2]) if v[0].startswith("curve_") else
                    (v[0], swap(v[1]), v[2], *[swap(r) for r in v[3:]]))
                for k, v in jobs.items() if prof.get("curve_cells") or not v[0].startswith("curve_")}
        diag_of = {id(p): n for n, p in diag_paths.values()}
    if "only" in prof:
        jobs = {k: v for k, v in jobs.items() if v[0] in prof["only"]}
    if ONLY:
        jobs = {k: v for k, v in jobs.items() if v[0] in ONLY + ("ns",)}  # ns はカーソルにも使うのでいつも描く
    if "walls" in prof:
        # 側壁・高架の版は近い斜めの絵を持たない。本体は、近い斜めの絵が無い way の近い斜めを「1 タイルに 2 本の way」で作るので、
        # 奥の線を back、手前の線を front の版にでき、2 本の間に壁が立たない（絵があると十字 1 本の way になり、両方が同じ版になる）
        jobs = {k: v for k, v in jobs.items() if not v[0].startswith("close")}
    # 坂のタイルから始まる橋の端（Start・Start2）: 平らな橋の絵の下に、坂の地面までの躯体を足す。
    # 本体の slope_t::north は南が高い坂で、そのとき Start[N] が使われる（東西も同じく、名前と反対の側が高い）
    grounds = {}
    if prof.get("starts"):
        high = {"n": lambda x, y: (half - y) / TILE, "s": lambda x, y: (y + half) / TILE,
                "e": lambda x, y: (half - x) / TILE, "w": lambda x, y: (x + half) / TILE}
        for j, d in enumerate("nsew"):
            for col, steps, pre in ((j, 1, "start"), (5 + j, 2, "start2")):
                jobs[(3, col)] = (f"{pre}_{d}", [straight(S, N) if d in "ns" else straight(W, E)], None)
                grounds[f"{pre}_{d}"] = (lambda f, n: lambda x, y: n * H * (f(x, y) - 1))(high[d], steps)
    groups = prof.get("groups", ("body",))
    # 雪の絵は下の 4 行に同じ並びで置く（dat の image[..][1]）。汚れは、雪の絵では雪の上の汚れ（灰色）に差し替える
    # 行の並び: 奥の絵 4 行 →（手前の絵 4 行）→ 雪の奥の絵 4 行 →（雪の手前の絵 4 行）
    block = 8 if "front_row" in prof else 4
    # prof["wall_sheet"]（無くてよい）: 壁を way の絵に焼き込まず、この名前の way-object のシートに分ける（AMI の基盤の版と壁。ADR 0003）。
    # way のシートには壁を除いた本体（基盤は壁の位置で止まる）を、壁のシートには壁だけを描く
    wall_sheet = prof.get("wall_sheet")
    # prof["write_walls"]（無くてよい。既定は真）: 偽なら、壁を way の絵から分けるが、壁の way-object のシートは書かない
    # （高架の版。壁は地上の版と同じ way-object を重ねるので、高架の対象では描かない。壁の層も描かない）
    write_walls = prof.get("write_walls", True)
    wcells = {}
    # prof["skin"]（無くてよい）は夏の絵だけ、prof["snow_skin"]（無くてよい）は雪の絵だけの材質の差し替え（部品の名前 → 材質）
    variants = [(0, "", track_profile_skin(prof, groups), groups)]
    if prof.get("snow"):
        variants.append((block, "_snow", track_profile_skin(prof, groups, snow=True), groups))
    for row0, suffix, skin, grp in variants:
        for pos, (name, paths, slope, *rails) in jobs.items():
            clear_models()
            # 画面で横向きの斜め（nw・se）は下げ幅を半分にする（datum_move の div）。斜めは横幅も細くする。
            # diag_curves のカーブのセル（curve_cells）は斜めのセルと同じ形
            shape = name.replace("curve_", "diag_") if diag_of and name.startswith("curve_") else name
            div = 2 if shape in ("diag_nw", "diag_se", "close1") else 1
            widths = DIAG_WIDTHS if shape.startswith(("diag_", "close")) else None
            # 架線の柱・梁（catenary_support）は経路が 1 本のセルだけに作る（分岐・十字に経路ごとの門を作らない。トロリ線は全部の経路）
            cell_grp = grp if len(paths) == 1 else tuple(g for g in grp if g != "catenary_support")
            kw = dict(widths=widths, div=div, groups=cell_grp, ends=name in ("s", "w", "n", "e"), skin=skin)
            if prof.get("wall_sheet") and slope:
                # 壁を way-object に分ける版の坂: 壁をタイルの外へ長めに残す。坂では基準面の動きが平地と違い、
                # 上がった側の端の最後の列が欠けて、隣の平らなタイルの壁との間に 1px のすき間が出た（持ち分は render_layers で 1 列広げる）
                kw["tall_pad"] = SLOPE_WALL_PAD

            def build(ps, pths):
                # diag_curves の斜めの部分は、斜めのセルと同じ幅・下げ幅で組む（同じ assemble の中で、経路ごとに変える）
                opts = {i: (DIAG_WIDTHS, 2 if diag_of[id(p)] in ("diag_nw", "diag_se") else 1)
                        for i, p in enumerate(pths) if id(p) in diag_of}
                out = assemble(ps, pths, prof["datums"], slope, **dict(kw, path_opts=opts or None))
                for pname, spec in bed_fills.items() if opts else ():
                    layer = next((p for p in ps if p.name == pname), None)
                    if layer is None:
                        continue
                    # 直線と斜めの層の間にできる三角のすき間を、層の上面の凸包で埋める（pak128 標準の T字・十字と同じ）。
                    # 部品の名前のままにして、材質の差し替えとレイアウト検証用モードの色をそのまま使う
                    k_diag = DIAG_WIDTHS.get(layer.width, 1.0)
                    fill = replace(layer, shape=bed_fill_shape(pths, {i: k_diag for i in diag_of}, spec))
                    out += assemble([fill], pths[:1], prof["datums"], slope, **dict(kw, widths=None))
                return out
            if rails:
                # 分岐の絵: 走行面（rail の基準面の部品）だけを分岐の経路で作る
                obs = (build([p for p in parts if p.datum != "rail"], paths)
                       + build([p for p in parts if p.datum == "rail"], rails[0]))
            else:
                obs = build(parts, paths)
            side = prof.get("walls", "both")
            # 行き止まりの終点をタイルの中心から動かした版（end_from_edge）は、本体の重心が開いた側へ寄り、側壁の手前/奥の判定が
            # ずれた（タイルの端まで延ばした手前の側壁が奥の絵になった）。手前/奥をタイルの中心から測る
            origin = Vector((0, 0, 0)) if "end_from_edge" in prof and name in ("s", "w", "n", "e") else None
            kept = select_walls(obs, name, paths, side, origin=origin)
            if side in ("back", "center") and name.startswith("diag_"):
                # back・center の斜めは橋脚を描かない。手前にいつも front の線があり、その橋脚で足りる。
                # 描くと、画面で横向きの斜めでは柱の上が手前の線の床に重なって暗い点線に見えた
                for ob in [ob for ob in obs if ob.name.startswith("pier")]:
                    obs.remove(ob)
                    bpy.data.objects.remove(ob, do_unlink=True)
            mask_slope = slope
            kb = (widths or {}).get("bed", 1.0)
            trim_end_walls(kept, paths, kb, datum_move(prof["datums"]["bed"], slope, div))
            if "catenary_support" in grp:
                trim_catenary(obs, kept, paths, kb, datum_move(prof["datums"]["bed"], slope, div))
            if "base" in grp:
                bmat = (skin or {}).get("base", _M_BASE)
                # prof["elev_body"]（無くてよい）: 高架の躯体（桁）を基盤の下に足す。基盤と同じ決め方で、壁のある側は壁の外の面から
                # ELEV_BODY_INSET 内で止め（床の縁が見える）、壁の無い側はタイルの端まで（並べた線の躯体とつながる）
                body_kw = dict(z0=-BASE_H, depth=ELEV_BODY_D, name="elev_body", wu=WALL_U - ELEV_BODY_INSET)
                if name == "single":
                    # 1 タイルだけの軌道: 線路も壁も置かず、タイル全面の基盤だけにする（高架のすき間を埋める景観用）
                    for ob in obs:
                        bpy.data.objects.remove(ob, do_unlink=True)
                    obs = [build_base([], paths, kb, prof["datums"]["bed"], slope, div, bmat)]
                    if prof.get("elev_body"):
                        obs.append(build_base([], paths, kb, prof["datums"]["bed"], slope, div, _M_ELEV_BODY, **body_kw))
                else:
                    open_cut = _diag_open_cut(kept, paths[0]) if name.startswith("diag_") else None
                    obs.append(build_base(kept, paths, kb, prof["datums"]["bed"], slope, div, bmat, extra_cut=open_cut))
                    if prof.get("elev_body"):
                        # 斜めの壁の無い側は、基盤と同じ下ほど中心線へ寄る切り口にし、路盤の面の高さで近い斜めの 2 本の真ん中より内を通す。
                        # 縦に切ると、奥の線の躯体の切り口（カメラを向く暗い面）が手前の線の床の上に三角に出た（2026-11-18、ゲームで確認）
                        body_cut = (_diag_open_cut(kept, paths[0], inset=ELEV_BODY_DIAG_INSET)
                                    if name.startswith("diag_") else None)
                        obs.append(build_base(kept, paths, kb, prof["datums"]["bed"], slope, div, _M_ELEV_BODY, extra_cut=body_cut,
                                              **body_kw))
                if name in grounds:
                    obs.append(build_start_body(paths[0], grounds[name], prof["datums"]["bed"], _M_BASE))
                    mask_slope = grounds[name]  # 持ち分を、坂の地面まで下へ広げる
            cname = f"{prof['sheet']}{suffix}_{name}"
            # 持ち分を下へ広げる行数（prof["lower"]。高架の躯体）。地面に接する橋の端（solid の坂・坂から始まる端）では広げない。
            # 坂の低い側では、基盤・躯体が地面より下にあり、広げると地面の下の部分が描かれて、隣の地上の線路の上に帯（基盤の端の面）と、
            # 手前の壁の下に三角が出た（AMI の橋。2026-11-18、ユーザーの確認用の保存データ）。坂の躯体・Start の躯体は solid・grounds で地面まで描く
            lower = 0 if prof.get("solid") and (slope or name in grounds) else prof.get("lower", 0)
            if wall_sheet and any(ob.get("tall") for ob in obs):
                # 壁を way-object に分ける版: 本体（壁なし）は way のシート、壁は way-object のシート（夏の絵だけ）へ
                body, wback, wfront = render_layers(cname, obs, True, exits_of(name), mask_slope, cy, prof["spill"], prof.get("rise", WALL_RISE),
                                                    prof.get("solid", False), lower, separate=True,
                                                    tall_layers=row0 == 0 and write_walls, origin=origin)
                cells[(pos[0] + row0, pos[1])] = body
                if wback:
                    wcells[pos] = wback
                if wfront:
                    wcells[(pos[0] + WALL_FRONT_ROW, pos[1])] = wfront
            elif any(ob.get("tall") for ob in obs):
                cells[(pos[0] + row0, pos[1])], front = render_layers(cname, obs, True, exits_of(name), mask_slope, cy,
                                                                      prof["spill"], WALL_RISE, prof.get("solid", False),
                                                                      lower, origin=origin)
                if front:
                    cells[(pos[0] + row0 + prof["front_row"], pos[1])] = front
            else:
                cells[(pos[0] + row0, pos[1])] = render_cell(cname, exits_of(name), slope=mask_slope, cy=cy, spill=prof["spill"],
                                                             solid=prof.get("solid", False), lower=lower)

    if prof.get("piers"):
        # 橋脚: 橋の下の地面のタイルに立つ柱（高さ 1 段）。線路の向きに直角に長い。(2, 0) が南北の橋、(2, 1) が東西の橋
        # prof["pier_box"]（無くてよい）: (線路を横切る向きの長さ, 線路に沿う向きの長さ, 材質)。無ければ POC の橋の柱（PIER_L × PIER_W、壁の材質）
        set_anchor(128)
        across, along, pmat = prof.get("pier_box", (PIER_L, PIER_W, _M_WALL))
        for col, (sx, sy) in enumerate(((across, along), (along, across))):
            clear_models()
            mesh_object("pier", *box(0, 0, H / 2, sx, sy, H), material(*pmat))
            cells[(2, col)] = render_cell(f"{prof['sheet']}_pier{col}")
        set_anchor(anchor)

    # 確認用: タイル菱形そのもの（基準位置の検証に使う。シートには入れない）
    set_anchor(128)
    clear_models()
    v, f = box(0, 0, -0.001, TILE, TILE, 0.002)
    mesh_object("tile", v, f, material("tile", (0.5, 0.5, 0.5)))
    render_cell("check_tile_flat")
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH" and ob.name == "tile":
            for vert in ob.data.vertices:
                vert.co.z += H * (vert.co.y + TILE / 2) / TILE
    render_cell("check_tile_up12")

    # アイコン: 線路を大きく斜めに通し、左上に最高速度を書く
    clear_models()
    assemble(track_body_parts(prof), [straight((0, -12), (0, 12), ext=0.6)], clip=False)
    if profile == "trial":
        cells[(0, 0)] = render_icon("track_trial_icon", 0.5, shift=(-0.14, 0.2), label="100", style="track", badge="T")
        # カーソル: 直線の絵の上に、最高速度を書く（アイコンと同じ色の札）
        clear_models()
        assemble(parts, [straight(S, N)], prof["datums"], groups=groups, skin=track_skin(groups))
        cells[(0, 1)] = render_cursor("track_trial_cursor", "100", "track")
    elif prof.get("wall_only"):
        pass  # way のシートを書かない版（下）
    elif "walls" in prof or "band" in prof:
        # 側壁のバリエーションは右下の印（S・B・C・F）、橋は下の帯で区別する
        # prof["badge"]（無くてよい）: 右下の印。無ければ版（walls）の印。None で印なし（橋）
        cells[(0, 0)] = render_icon(prof["sheet"] + "_icon", 0.5, shift=(-0.14, 0.2), label=prof.get("label", "100"), style="track",
                                    badge=prof.get("badge", ICON_BADGE.get(prof.get("walls"))), band=prof.get("band"))
        cells[(0, 1)] = cells[(0, 2)]
    else:
        cells[(0, 0)] = render_icon("track_icon", 0.5, shift=(-0.14, 0.2), label=prof.get("label", "100"))
        cells[(0, 1)] = cells[(0, 2)]  # カーソルは ns と同じ絵

    rows = block * (2 if prof.get("snow") else 1)
    # prof["wall_only"]（無くてよい）: way のシートを書かず、壁の way-object のシートだけを書く（架線つきの壁。way は基盤の版と同じ絵なので、
    # 基盤の版の対象が書く。prof["sheet"] は作業ファイル（work/）の名前にだけ使うので、基盤の版と別の名前にする）
    if not prof.get("wall_only"):
        make_sheet(cells, rows, 15 if any(c >= 10 for _, c in cells) else 10, os.path.join(SRC, prof["sheet"] + ".png"))
    if wall_sheet and write_walls:
        # 壁の way-object のアイコン（仮の絵。way と同じ絵に、印と W を書く）とカーソル（直線の奥の壁）
        clear_models()
        assemble(track_body_parts(prof), [straight((0, -12), (0, 12), ext=0.6)], clip=False)
        wcells[(0, 0)] = render_icon(wall_sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=prof.get("wall_label", "W"), style="track",
                                     badge=ICON_BADGE.get(prof.get("walls")))
        ns = wcells.get((0, 2)) or wcells.get((WALL_FRONT_ROW, 2))  # front の版の直線は手前の絵だけ
        ns = ns or wcells.get((0, 5))  # 側壁の無い版（center）は、行き止まりの端の壁の絵をカーソルにする
        if ns:
            wcells[(0, 1)] = ns
        make_sheet(wcells, 2 * WALL_FRONT_ROW, 15 if any(c >= 10 for _, c in wcells) else 10, os.path.join(SRC, wall_sheet + ".png"))


def _pier_jobs():
    """橋脚のシートのセル: (行, 列) → (名前, [(中心, 向き), ...], 坂)。セルの位置は線路の way と同じ（行 0〜3）。
    中心と向きは単柱の橋脚（pier_sheet）の柱の位置。門型（pier_gate_sheet）は名前と坂だけを使う"""
    half = TILE / 2
    N, S, E, W, O = (Vector((0, half)), Vector((0, -half)), Vector((half, 0)), Vector((-half, 0)), Vector((0, 0)))
    NS, EW = N - S, E - W
    mid = lambda a, b: ((a + b) / 2, b - a)  # 斜め: 2 辺の中点を結ぶ経路の中ほどと向き
    up = lambda n, f: (lambda x, y: n * H * f(x, y) / TILE)
    jobs = {  # (行, 列): (名前, [(中心, 向き), ...], 坂)
        (0, 2): ("ns", [(O, NS)], None), (0, 3): ("ew", [(O, EW)], None),
        (0, 5): ("s", [(O, NS)], None), (0, 6): ("w", [(O, EW)], None),
        (0, 7): ("n", [(O, NS)], None), (0, 8): ("e", [(O, EW)], None), (0, 9): ("single", [(O, NS)], None),
        (2, 0): ("diag_sw", [mid(S, W)], None), (2, 1): ("diag_nw", [mid(N, W)], None),
        (2, 2): ("diag_ne", [mid(N, E)], None), (2, 3): ("diag_se", [mid(S, E)], None),
        (2, 4): ("close1", [mid(N, W), mid(S, E)], None), (2, 9): ("close2", [mid(N, E), mid(S, W)], None),
        (3, 5): ("nse", [(O, NS)], None), (3, 6): ("new", [(O, EW)], None), (3, 7): ("nsw", [(O, NS)], None),
        (3, 8): ("sew", [(O, EW)], None), (3, 9): ("nsew", [(O, NS)], None),
    }
    for n, base in ((1, 0), (2, 5)):
        pre = "up" if n == 1 else "up2_"
        jobs[(1, base)] = (f"{pre}12", [(O, NS)], up(n, lambda x, y: y + half))
        jobs[(1, base + 1)] = (f"{pre}9", [(O, EW)], up(n, lambda x, y: half - x))
        jobs[(1, base + 2)] = (f"{pre}3", [(O, NS)], up(n, lambda x, y: half - y))
        jobs[(1, base + 3)] = (f"{pre}6", [(O, EW)], up(n, lambda x, y: x + half))
    if ONLY:
        jobs = {k: v for k, v in jobs.items() if v[0] in ONLY + ("ns",)}
    return jobs


def _pier_top_bottom():
    """橋脚の上端（高架の躯体の下面より PIER_TOP_OVERLAP 上）と下端（地面より PIER_FOOT 下）"""
    return ELEV_STEPS * H - BASE_H - ELEV_BODY_D + PIER_TOP_OVERLAP, -PIER_FOOT


def _pier_place(ob, datums, name, slope):
    """橋脚の形を高架の床と同じ基準面で動かし、坂を当てる（単柱・門型で共通）。
    close1 は nw と se の 2 本で、どちらも画面で横向きの斜め（div 2）。close2 は縦向き（div 1）"""
    div = 2 if name in ("diag_nw", "diag_se", "close1") else 1
    move = datum_move(datums["bed"], slope, div)
    if move is not None:
        for v in ob.data.vertices:
            v.co += move
    if slope:
        apply_slope(ob, slope)


def _pier_cell(cname, slope, cy=GROUND_CY):
    """橋脚のセルを描き、持ち分（地面の菱形を上へ PIER_RISE 行広げた範囲）で切る。輪郭の半透明の画素は捨てる。
    cy は菱形の中心の行（道路用の橋脚は道路と同じ ROAD_CY）"""
    img = load_rgba8(render_cell(cname)).copy()
    m = _ground_mask(slope, None, cy)
    base = m.copy()
    for k in range(1, PIER_RISE + 1):
        m[:-k] |= base[k:]
    img[..., 3] = np.where(m & (img[..., 3] >= 250), 255, 0)
    path = os.path.join(WORK, cname + "_full.png")
    save_rgba(path, img)
    return path


def pier_sheet(sheet, datums, label="P", across=PIER_SIZE * PIER_ACROSS_K, anchor=128 + BALLAST_DY, cy=GROUND_CY, top_drop=0.0,
               diag_k=1.0, style="track"):
    """高架の真下の地面のタイルに敷く、橋脚の way のシート（AMI。ADR 0003）。セルの位置は線路の way と同じ（行 0〜3）。
    柱は経路の中ほど（直線・行き止まり・T字・十字はタイルの中心、斜めは斜めの部分の中ほど）の下に、線路を横切る向きに長く立つ。
    T字・十字は通り抜ける線（T字）・南北の線（十字）の向き。近い斜めの分け合うタイル（close1・close2）は 2 本の柱。
    上端は高架の躯体の下面（地面から ELEV_STEPS 段 − BASE_H − ELEV_BODY_D）より PIER_TOP_OVERLAP 上で、躯体に隠れる。
    高架の床と同じ基準面（datums["bed"]）で動かし、坂は高架と同じく地面の坂を当てる（本体の高架は地面の坂を引き継ぐ）。
    持ち分は地面の菱形を上へ PIER_RISE 行広げた範囲で、輪郭の半透明の画素は捨てる（高さのある部品の層と同じ）。
    anchor・cy は絵の基準位置と持ち分の菱形の中心（既定は線路の way と同じ。道路用の橋脚は道路の ROAD_CY）、
    top_drop は上端を下げる量（道路の高架は基盤を路面の板の下へ ROAD_BASE_DROP 下げてあり、躯体の下面もその分低い）。
    diag_k は斜め（近い斜めを含む）の柱の横切る向きの長さの倍率（道路は斜めの幅が直線の 1/√2）。style はアイコンの背景"""
    top, bottom = _pier_top_bottom()
    top -= top_drop
    set_anchor(anchor)  # 線路の way と同じ（dat のオフセット -64,-32）
    cells = {}
    for pos, (name, piers, slope) in _pier_jobs().items():
        clear_models()
        ac = across * (diag_k if name.startswith(("diag_", "close")) else 1.0)
        for c, d in piers:
            ob = mesh_object("pier", *box(c.x, c.y, (top + bottom) / 2, PIER_SIZE, ac, top - bottom, rot=math.atan2(d.y, d.x)),
                             material(*_M_PIER))
            _pier_place(ob, datums, name, slope)
        cells[pos] = _pier_cell(f"{sheet}_{name}", slope, cy)
    # アイコン（仮の絵。ステップ 13 でまとめて作る）: 直線の柱に、文字と高架の帯。カーソルは南北の直線の柱
    clear_models()
    mesh_object("pier", *box(0, 0, (top + bottom) / 2, PIER_SIZE, across, top - bottom), material(*_M_PIER))
    cells[(0, 0)] = render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style=style, band="elevated")
    cells[(0, 1)] = cells[(0, 2)]
    make_sheet(cells, 4, 10, os.path.join(SRC, sheet + ".png"))


_EDGE = {"n": (0, 1), "s": (0, -1), "e": (1, 0), "w": (-1, 0)}
_OPPOSITE = {"n": "s", "s": "n", "e": "w", "w": "e"}
# 斜めのセル → 経路の外側の角（近い斜めの分け合うタイルは 2 本分）
_DIAG_CORNERS = {"diag_sw": ("sw",), "diag_nw": ("nw",), "diag_ne": ("ne",), "diag_se": ("se",),
                 "close1": ("nw", "se"), "close2": ("ne", "sw")}


def _gate_parts(name):
    """門型の橋脚のセルの柱と梁: ([(柱の角, 中心 x, y)], [(梁の辺, 梁)])。梁は ("box", 中心 x, y, 長さ x, 長さ y) か ("arm", 先端 x, y)。
    直線・坂・T字・十字: 経路が出る手前の辺（南・東）ごとに、その辺に沿う門（辺の両端の角に柱、柱の間に辺に沿う梁）。柱は辺に面を合わせる。
    奥の辺（北・西）の門は奥のタイルの手前の門が兼ねる（継ぎ目ごとに門が 1 つ。両側のタイルが描くと背中合わせの 2 つになる）。
    行き止まりは閉じた側の辺にも門を立てる（床の端を支える）。
    1 タイル（single）は南北の線と同じく北と南の辺。
    斜め: 経路の内側（タイルの中心）に柱を 1 本立て、経路を横切る向きに、外側の角の近く（柱の中心と同じ距離）まで片持ちの梁を出す。
    近い斜めの分け合うタイル（close1・close2）は、中心の柱を 2 本の斜めで分け合い、梁を両側へ出す"""
    q = TILE / 2 - PIER_GATE_POST / 2   # 柱の中心の、タイルの中心からの距離
    if name in _DIAG_CORNERS:
        arms = [(c, ("arm", (1 if "e" in c else -1) * q, (1 if "n" in c else -1) * q)) for c in _DIAG_CORNERS[name]]
        return [("c", 0.0, 0.0)], arms
    exits = "ns" if name == "single" else exits_of(name)
    edges = [e for e in exits if e in "se"]
    if len(exits) == 1:
        edges.append(_OPPOSITE[exits])
    elif name == "single":
        edges = ["n", "s"]
    posts, beams = {}, []
    for e in edges:
        dx, dy = _EDGE[e]
        if dx:   # 東西の辺: 南北に沿う梁
            posts.update({"n" + e: (dx * q, q), "s" + e: (dx * q, -q)})
            beams.append((e, ("box", dx * q, 0.0, PIER_GATE_POST, TILE)))
        else:
            posts.update({e + "e": (q, dy * q), e + "w": (-q, dy * q)})
            beams.append((e, ("box", 0.0, dy * q, TILE, PIER_GATE_POST)))
    return sorted((k, x, y) for k, (x, y) in posts.items()), beams


# 門型の橋脚のシートの手前の絵（frontimage）の行。奥の絵（image）の行 0〜3 の下（壁の way-object の WALL_FRONT_ROW と同じ並び）
# 手前の絵の行のずらし。dat を書く側の addons/ami/blender/ami_dat.py の PIER_FRONT_ROW と同じ値にする
PIER_GATE_FRONT_ROW = 4
# 斜めのタイルで、中心の柱を手前の絵にも描くセル（柱が経路より手前にある。ほかの斜めは同じ奥行きか奥なので奥の絵だけ）
_GATE_CENTER_FRONT = ("diag_nw",)


def pier_gate_sheet(sheet, datums, label="G"):
    """門型の橋脚の way のシート（AMI。#18 の追加）。セルの位置・高さ・基準面・坂・持ち分は単柱の橋脚（pier_sheet）と同じ。
    柱と梁の置き方は _gate_parts。梁と柱の上端は躯体の下面より PIER_GATE_BEAM_EMBED 上（躯体に食い込む）で、梁の深さは PIER_GATE_BEAM_D
    （躯体の下面より下に見えるのは PIER_GATE_BEAM_SHOW）。
    作りは iss の橋脚 5・6（../refs/iss/src/util/pier/ground/pier.dat の iss_wsg_pier5・6）に合わせる: 奥の絵（image）は全部の柱と梁、
    手前の絵（frontimage。乗り物の後に描く）は奥の角（北西）の柱と、経路より奥の中心の柱を除いたもの。手前の絵は行 PIER_GATE_FRONT_ROW〜"""
    _top, bottom = _pier_top_bottom()
    top = ELEV_STEPS * H - BASE_H - ELEV_BODY_D + PIER_GATE_BEAM_EMBED
    btop, bbot = top, top - PIER_GATE_BEAM_D
    set_anchor(128 + BALLAST_DY)

    def build(name):
        """[(形, 手前の絵にも描くか)]"""
        posts, beams = _gate_parts(name)
        # 部品の名前は角・辺ごとに分ける（レイアウト検証用モードで、どの柱・梁がどのタイルのものか見分ける）
        obs = [(mesh_object("pier_post", *box(x, y, (top + bottom) / 2, PIER_GATE_POST, PIER_GATE_POST, top - bottom),
                            material(f"{_M_PIER_POST[0]}_{k}", _M_PIER_POST[1])), k not in ("c", "nw") or name in _GATE_CENTER_FRONT)
               for k, x, y in posts]
        for side, b in beams:
            if b[0] == "box":
                v, f = box(b[1], b[2], (btop + bbot) / 2, b[3], b[4], btop - bbot)
            else:
                # 斜めの片持ちの梁: 中心の柱の中心から先端の点 (x, y) まで、柱の太さの幅（先端は柱の中心と同じ距離）
                x, y = b[1], b[2]
                v, f = box(x / 2, y / 2, (btop + bbot) / 2, math.hypot(x, y), PIER_GATE_POST, btop - bbot, rot=math.atan2(y, x))
            obs.append((mesh_object("pier_beam", v, f, material(f"{_M_PIER_BEAM[0]}_{side}", _M_PIER_BEAM[1])), True))
        return obs

    cells = {}
    for pos, (name, _piers, slope) in _pier_jobs().items():
        clear_models()
        obs = build(name)
        for ob, _front in obs:
            _pier_place(ob, datums, name, slope)
        for front, row in ((False, 0), (True, PIER_GATE_FRONT_ROW)):
            for ob, f in obs:
                ob.hide_render = front and not f
            cells[(pos[0] + row, pos[1])] = _pier_cell(f"{sheet}_{name}{'_front' if front else ''}", slope)
    # アイコン（仮の絵）: 南北の直線の門に、文字と高架の帯。カーソルは南北の直線（手前の絵）
    clear_models()
    build("ns")
    cells[(0, 0)] = render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style="track", band="elevated")
    cells[(0, 1)] = cells[(PIER_GATE_FRONT_ROW, 2)]
    make_sheet(cells, 2 * PIER_GATE_FRONT_ROW, 10, os.path.join(SRC, sheet + ".png"))


ICON = 32

ICON_SS = 4  # 4倍の大きさで描いて縮小し、輪郭をなめらかにする

LABEL_FONT = "C:/Windows/Fonts/arialbd.ttf"  # 無ければ Blender 標準の字体

ICON_BG = ((0, 196, 96), (0, 112, 56))  # iss のアイコンに合わせた緑（左上→右下）

# アイコンのシリーズ: 背景色は waytype で決める（左上→右下）。文字は左上に最高速度、右下に種類の印（badge）、
# 下の帯（band）は地上/高架などの構造の違い。同じ決まりで並べると、ツールバーで種類の違いが色・数字・印で分かる
ICON_STYLES = {
    "track": {"bg": ICON_BG},
    "road": {"bg": ((96, 132, 196), (40, 64, 120))},
    "expressway": {"bg": ((70, 90, 190), (24, 30, 96))},
    "tram": {"bg": ((196, 150, 0), (120, 84, 0))},
}

# 下の帯（地上は帯なし）。（上端, 下端, 色）の並びで、アイコンの高さに対する比。帯は下の 4px ほどにとどめ、右下の印を隠さない
#   高架: 灰色の床と、その下の橋脚 2 本 / 橋: 灰色の床と、その下の水色 / トンネル: 暗い帯
ICON_BANDS = {
    "elevated": [(0.875, 0.9375, 0.0, 1.0, (205, 205, 210)), (0.9375, 1.0, 0.18, 0.30, (205, 205, 210)),
                 (0.9375, 1.0, 0.70, 0.82, (205, 205, 210))],
    "bridge": [(0.875, 0.9375, 0.0, 1.0, (205, 205, 210)), (0.9375, 1.0, 0.0, 1.0, (70, 150, 230))],
    "tunnel": [(0.875, 1.0, 0.0, 1.0, (40, 34, 30))],
}


def add_label(text, x, y, height, color=(1, 1, 1), align="LEFT", res=ICON):
    """カメラの手前に文字を置く。x, y は 0〜1 の画面位置（左上が0）、height も画面比。res は絵の一辺の px（影を 1px ずらす）。"""
    sc = bpy.context.scene
    cam = sc.camera
    scale = cam.data.ortho_scale
    rot = cam.rotation_euler.to_matrix()
    right, up, fwd = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0)), rot @ Vector((0, 0, -1))
    shift = Vector((cam.data.shift_x, cam.data.shift_y))
    obs = []
    # 影（右下に1px）→ 白文字の順に重ねる
    px = scale / res
    for dx, dy, color, depth in ((px, -px, (0.0, 0.18, 0.08), 9.0), (0, 0, color, 10.0)):
        cu = bpy.data.curves.new("label", "FONT")
        cu.body = text
        cu.size = height * scale / 0.72  # 大文字の高さが height になるように
        cu.align_y = "TOP"
        cu.align_x = align
        if os.path.exists(LABEL_FONT):
            cu.font = bpy.data.fonts.load(LABEL_FONT, check_existing=True)
        ob = bpy.data.objects.new("label", cu)
        m = bpy.data.materials.new("label")
        m.use_nodes = True
        nodes = m.node_tree.nodes
        nodes.clear()
        em = nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = (*color, 1)
        outn = nodes.new("ShaderNodeOutputMaterial")
        m.node_tree.links.new(em.outputs[0], outn.inputs[0])
        cu.materials.append(m)
        ob.location = (cam.location + fwd * depth
                       + right * ((x - 0.5 + shift.x) * scale + dx)
                       + up * ((0.5 - y + shift.y) * scale + dy))
        ob.rotation_euler = cam.rotation_euler
        sc.collection.objects.link(ob)
        obs.append(ob)
    return obs


def render_cursor(name, label, style, base=None):
    """今のモデル（1タイル分の絵）をカーソルにする。タイルの上に、アイコンと同じ背景色の札と文字を足す。
    選んでいる物が何かは札の色（waytype）と文字（最高速度など）で分かる。
    base（RGBA の配列）を渡すと、モデルの代わりにその絵に札を足す（文字だけを空の場面で描く。トンネルの重ね絵）。"""
    c0, c1 = ICON_STYLES[style]["bg"]
    if base is not None:
        clear_models()
    labels = add_label(label, 0.5, 0.325, 0.045, align="CENTER", res=CELL)
    rgba = load_rgba8(render_cell(name if base is None else name + "_text")).copy()
    for ob in labels:
        bpy.data.objects.remove(ob, do_unlink=True)
    # 札: 文字の後ろの角丸でない四角（文字は不透明な所だけ上に残す）
    text = rgba[76:100, 96:160].copy()
    if base is not None:
        rgba = base.copy()
    yy = np.linspace(0, 1, 18)[:, None, None]
    plate = (np.array(c0) * (1 - yy) + np.array(c1) * yy).astype(np.uint8) * np.ones((18, 44, 1), np.uint8)
    rgba[79:97, 106:150, :3] = plate
    rgba[79:97, 106:150, 3] = 255
    a = text[..., 3:4].astype(np.float32) / 255
    rgba[76:100, 96:160, :3] = (text[..., :3] * a + rgba[76:100, 96:160, :3] * (1 - a)).astype(np.uint8)
    path = os.path.join(WORK, name + "_cell.png")
    save_rgba(path, rgba)
    return path


def render_icon(name, zoom, shift=(0.0, 0.0), label=None, style=None, badge=None, band=None):
    """今のモデルをアイコンにする。背景を塗り、文字を重ね、セルの左上 32x32 に置く。
    style は ICON_STYLES の名前（背景色）、badge は右下の短い印、band は ICON_BANDS の名前（下の帯）。"""
    sc = bpy.context.scene
    cam = sc.camera.data
    saved = (cam.shift_x, cam.shift_y)
    size = ICON * ICON_SS
    sc.render.resolution_x = sc.render.resolution_y = size
    cam.ortho_scale = TILE * math.sqrt(2) * zoom
    cam.shift_x, cam.shift_y = shift
    labels = add_label(label, 0.07, 0.07, 0.44) if label else []
    if badge:
        labels += add_label(badge, 0.93, 0.52 if band else 0.62, 0.30, color=(1.0, 0.9, 0.2), align="RIGHT")
    big = load_rgba8(render_cell(name)).astype(np.float32) / 255
    for ob in labels:
        bpy.data.objects.remove(ob, do_unlink=True)
    sc.render.resolution_x = sc.render.resolution_y = CELL
    cam.ortho_scale = ORTHO
    cam.shift_x, cam.shift_y = saved

    # 背景のグラデーションに重ねる
    t = (np.add.outer(np.arange(size), np.arange(size)) / (2 * size - 2))[..., None]
    c0, c1 = (np.array(c, np.float32) / 255 for c in (ICON_STYLES[style]["bg"] if style else ICON_BG))
    bg = c0 * (1 - t) + c1 * t
    a = big[..., 3:4]
    rgb = big[..., :3] * a + bg * (1 - a)
    if band:  # 帯は絵の上に重ねる（下に敷くと道の絵に隠れる）
        for y0, y1, x0, x1, color in ICON_BANDS[band]:
            rgb[int(size * y0):int(size * y1), int(size * x0):int(size * x1)] = np.array(color, np.float32) / 255
    small = rgb.reshape(ICON, ICON_SS, ICON, ICON_SS, 3).mean(axis=(1, 3))
    icon = np.concatenate([small, np.ones((ICON, ICON, 1), np.float32)], axis=2)
    cell = np.zeros((CELL, CELL, 4), np.uint8)
    cell[:ICON, :ICON] = (icon * 255 + 0.5).astype(np.uint8)
    path = os.path.join(WORK, name + "_cell.png")
    save_rgba(path, cell)
    return path


def icon_gallery():
    """アイコンのシリーズの見本（work/icon_gallery.png）。同じ線路・道路の絵で、背景色・数字・印・帯だけを変えて並べる。"""
    samples = [("track", "100", None, None), ("track", "160", None, "elevated"), ("track", "80", "T", "tunnel"),
               ("tram", "60", None, None), ("road", "50", None, None), ("road", "50", None, "elevated"),
               ("expressway", "120", None, None), ("expressway", "120", None, "elevated")]
    tiles = []
    for i, (style, label, badge, band) in enumerate(samples):
        clear_models()
        if style in ("track", "tram"):
            assemble(TRACK_PARTS, [straight((0, -12), (0, 12), ext=0.6)], clip=False)
        else:
            build_road([straight((0, -12), (0, 12), ext=0.6)], [], clip=False, size=(TILE, 26), sidewalk=style == "road")
        cell = load_rgba8(render_icon(f"gallery{i}", 0.5, shift=(-0.14, 0.2), label=label, style=style, badge=badge, band=band))
        tiles.append(cell[:ICON, :ICON].repeat(6, 0).repeat(6, 1))
        tiles.append(np.full((ICON * 6, 6, 4), 255, np.uint8))
    save_rgba(os.path.join(WORK, "icon_gallery.png"), np.concatenate(tiles[:-1], 1))


# ---- トンネル（obj=tunnel）: 坂のタイルに置く坑口。奥の絵 = 線路と暗い内側、手前の絵 = 坑口の躯体（車両を隠す）
# 手本（pak128 標準の rail_100_tunnel、iss の tunnel_surface）と同じ作り: 躯体はタイル全体を覆う箱で、屋根は丘の上面（2 段）と同じ高さ。
# 口は低い側の辺にあり、幅も高さもタイルいっぱいに近い（128jp の大きめの車両も通る）
TUNNEL_FACE = 0.0                       # 低い側の辺から坑口の面までの距離

TUNNEL_BORE = (3.4, 2 * H - 0.6)        # 穴の半幅と高さ（屋根の厚み 0.6 を残す）

TUNNEL_HOOD = (TILE / 2, 2 * H)         # 躯体の半幅と高さ

TUNNEL_RISE = 36      # 躯体の高さ（画面の px。持ち分を上へ広げる行数）


def tunnel_sheet(kind="track", profile="new", sheet=None, label="100", road_profile="expressway"):
    """坑口 4 方向（kind: track・expressway）。profile は kind="track" のときの線路の描き分け（TRACK_PROFILES の名前。部品の差し替え replace と夏の材質 skin も使う）、
    road_profile は kind="expressway" のときの道路の描き分け（ROAD_PROFILES の名前か、その値の辞書。groups・skin・label・style を使う）、
    sheet はシート名（無ければ track_tunnel・expressway_tunnel）、label はアイコンの最高速度。pak128 では坑口は 2 段の坂にしか置けない（本体の tunnelbauer）。BackImage[N] は北が高い坂（南から入る）。シートは 行 0: 奥の絵、行 1: 手前の絵、行 2・3: 雪。"""
    half = TILE / 2
    N, S, E, W = (0, half), (0, -half), (half, 0), (-half, 0)
    dirs = {  # 名前: (列, 経路, 高い側の向き, 坂の高さ)
        "n": (2, straight(S, N), Vector((0, 1)), lambda x, y: 2 * H * (y + half) / TILE),
        "s": (3, straight(S, N), Vector((0, -1)), lambda x, y: 2 * H * (half - y) / TILE),
        "e": (4, straight(W, E), Vector((1, 0)), lambda x, y: 2 * H * (x + half) / TILE),
        "w": (5, straight(W, E), Vector((-1, 0)), lambda x, y: 2 * H * (half - x) / TILE),
    }
    expwy = kind == "expressway"
    prof = None if expwy else TRACK_PROFILES[profile]  # 道路の坑口は線路の描き分けを使わない
    road_prof = (ROAD_PROFILES[road_profile] if isinstance(road_profile, str) else road_profile) if expwy else None
    parts = None if expwy else track_sheet_parts(prof)
    # 高速道路: iss の都市高速の坑口（tunnel/road。タイルいっぱいの箱と口の上の名板）が手本。穴は両側の壁の内側まで広げる。
    # 道路は地面の菱形より 1px 下に描く（ROAD_CY）。持ち分も同じだけ下げ、隣の道路と同じく spill は 0
    bore_w = EXPWY_WALL_U - 0.1 if expwy else TUNNEL_BORE[0]
    cy, spill = (ROAD_CY, 0) if expwy else (GROUND_CY, prof["spill"])
    # 道路の作業ファイルの名前と白線: sheet を渡したとき（AMI の道路 3 種）は sheet を名前にし、中央線は道路の描き分けの center
    # （None は無し・"dash" は破線。road_sheet と同じ）。渡さない blender-poc の高速道路は今までどおり（名前は expwy_tunnel、中央線は実線）
    pre = (sheet or "expwy_tunnel") if expwy else (sheet or "tunnel")
    if expwy and sheet:
        ck = road_prof.get("center", "solid")
        road_lines = lambda p: [(p, -EDGE_LINE)] + ([] if ck is None else [(p, 0.0, "cdash") if ck == "dash" else (p, 0.0)]) + [(p, EDGE_LINE)]
    else:
        road_lines = lambda p: [(p, -EDGE_LINE), (p, 0.0), (p, EDGE_LINE)]
    set_anchor(ROAD_CY if expwy else 128 + BALLAST_DY)
    cells = {}
    a0, a1 = -half + TUNNEL_FACE, half  # 坑口の面と、躯体の奥の端（経路に沿った位置）
    for row0, skin in ((0, None), (2, ROAD_SNOW_SKIN if expwy else SNOW_SKIN)):
        for name, (col, path, d, slope) in dirs.items():
            rot = math.atan2(d.y, d.x)
            c = d * ((a0 + a1) / 2)
            # 持ち分: 坂の面だけ。上へは躯体の高さだけ広げる。坂の面より下（高い側の辺の下の面や、そこから覗く穴の中）は
            # 手前の丘のタイルに隠れる所なので描かない（描くと、口が奥を向いた坑口で穴の中が丘の上にはみ出した）
            # 手前の 2 辺は線路と同じだけ広げる（spill。0 だと口の辺で隣の線路との間に 1 画素おきのすき間が出た）
            m = _ground_mask(slope, None, cy, spill)
            base = m.copy()
            for k in range(1, TUNNEL_RISE + 1):
                m[:-k] |= base[k:]

            def shot(suffix):
                img = load_rgba8(render_cell(f"{pre}{'_snow' if skin else ''}_{name}{suffix}")).copy()
                img[..., 3] = np.where(m & (img[..., 3] >= 128), 255, 0)
                path_ = os.path.join(WORK, f"{pre}{'_snow' if skin else ''}_{name}{suffix}_full.png")
                save_rgba(path_, img)
                return path_

            # 奥の絵: 平らな線路（坂に切り込む）と、穴の内側の暗い床と壁
            clear_models()
            m_dark = material("tunnel_dark", (0.015, 0.015, 0.015))
            n = Vector((d.y, -d.x))
            if expwy:
                # 道路は路面の板がタイル全面にあるので床は要らない。雪の絵は路肩だけに雪（道路のシートと同じ）
                grp = road_prof["groups"]
                build_road([path], road_lines(path), sidewalk=False, skin=skin, prof=road_prof,
                           groups=grp + ROAD_SNOW_GROUPS if skin else grp)
            else:
                # 線路の本体と同じく汚れを入れる（雪の絵は雪の上の汚れ）
                grp = prof["groups"]
                tskin = track_profile_skin(prof, grp, snow=bool(skin))  # 夏・雪の材質の差し替えは track_sheet と同じ
                assemble(parts, [path], prof["datums"], groups=grp, skin=tskin)
                # 穴の内側: 床（基盤と同じ材質）と暗い左右の壁だけを置く（線路は床の上に見える。箱で埋めると線路まで隠れた）
                # 床はタイルの幅いっぱい（躯体の下は隠れる。口の辺では、隣の側壁つきの線路の基盤と 1 行重なってすき間を埋める）
                floor = mesh_object("floor", *box(c.x, c.y, 0.005, a1 - a0, TILE, 0.01, rot=rot),
                                    material(*(tskin or {}).get("base", _M_BASE)))
                # 基盤と同じ基準面（bed）に乗せる。動かさないと、隣の線路の基盤より 2px 上で止まり、辺に 1 行のすき間が出た
                mv = datum_move(prof["datums"]["bed"])
                if mv is not None:
                    floor.location += mv
                clip_to_tile(floor)
            inner = []
            for s in (1, -1):
                q = c + n * (s * (bore_w + 0.05))
                # 長さはタイルの辺まで（辺の手前で止めると、隣の側壁の上の縁に 1 画素おきのすき間が出た）
                inner.append(box(q.x, q.y, TUNNEL_BORE[1] / 2, a1 - a0, 0.1, TUNNEL_BORE[1], rot=rot))
            dark = mesh_object("dark", *merge(inner), m_dark)
            clip_to_tile(dark, 0.0)
            cells[(row0, col)] = shot("_back")
            # 手前の絵: 坑口の躯体（面から奥の辺まで）。穴を抜く
            clear_models()
            hood = mesh_object("hood", *box(c.x, c.y, TUNNEL_HOOD[1] / 2, a1 - a0, 2 * TUNNEL_HOOD[0], TUNNEL_HOOD[1], rot=rot),
                               material(*_M_WALL))
            bore = mesh_object("bore", *box(0, 0, TUNNEL_BORE[1] / 2 - 0.5, 30, 2 * bore_w, TUNNEL_BORE[1] + 1.0, rot=rot),
                               material(*_M_WALL))
            boolean(hood, bore)
            bpy.data.objects.remove(bore, do_unlink=True)
            clip_to_tile(hood, 0.0)
            if expwy:
                # 口の上の名板（iss の坑口と同じ橙色の板）。面から少し手前に出す
                q = d * (a0 - 0.06)
                plate = mesh_object("plate", *box(q.x, q.y, TUNNEL_BORE[1] + 0.3, 0.12, 2.2, 0.4, rot=rot),
                                    material("tunnel_plate", (0.85, 0.55, 0.12)))
                clip_to_tile(plate, 0.3)
            cells[(row0 + 1, col)] = shot("_front")
    clear_models()
    long = straight((0, -12), (0, 12), ext=0.6)
    if expwy:
        build_road([long], road_lines(long), clip=False, size=(TILE, 26), sidewalk=False, prof=road_prof)
        cells[(0, 0)] = render_icon(f"{pre}_icon", 0.5, shift=(-0.14, 0.2), label=road_prof["label"], style=road_prof["style"],
                                    band="tunnel")
    else:
        assemble(track_body_parts(prof), [long], clip=False)
        cells[(0, 0)] = render_icon(f"{sheet}_icon" if sheet else "track_tunnel_icon", 0.5, shift=(-0.14, 0.2), label=label, style="track",
                                    band="tunnel")
    # カーソル: 口が手前を向いた坑口（BackImage[N]）の奥の絵に手前の絵（躯体）を重ねた 1 枚
    back, front = load_rgba8(cells[(0, 2)]), load_rgba8(cells[(1, 2)])
    cursor = np.where(front[..., 3:] >= 128, front, back)
    if expwy:
        # 道路のシリーズは、カーソルにアイコンと同じ色の札と最高速度を足す
        cells[(0, 1)] = render_cursor(f"{pre}_cursor", road_prof["label"], road_prof["style"], base=cursor)
    else:
        cells[(0, 1)] = os.path.join(WORK, f"{pre}_cursor.png")
        save_rgba(cells[(0, 1)], cursor)
    make_sheet(cells, 4, 6, os.path.join(SRC, (sheet or ("expressway" if expwy else "track") + "_tunnel") + ".png"))


def run_targets(sheets, default_targets):
    """入口から呼ぶ。sheets は {対象名: 描く関数}、default_targets は対象を渡されなかったときの既定。
    `--` の後の引数を対象名として読み、LAYOUT・ONLY のときは出力先を work/ に替える。知らない対象名は失敗で止める"""
    global SRC
    if LAYOUT:
        import shutil
        dbg = os.path.join(WORK, "layout")
        os.makedirs(dbg, exist_ok=True)
        for f in os.listdir(SRC):
            if f.endswith(".dat"):
                shutil.copy(os.path.join(SRC, f), dbg)
        SRC = dbg
    elif ONLY:
        SRC = os.path.join(WORK, "only")
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(SRC, exist_ok=True)
    setup_scene()
    print(f"[info] ortho={ORTHO:.4f} px/unit={PX_PER_UNIT:.4f} height_step={H:.4f}")
    targets = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(default_targets)
    unknown = [t for t in targets if t not in sheets]
    if unknown:
        # 名前の打ち間違いで何も描かずに正常終了しないように止める（render_parallel.py が失敗として拾う）
        raise SystemExit(f"[render] unknown target: {' '.join(unknown)}")
    for name, draw in sheets.items():  # 登録した順に描く（対象の指定順ではない）
        if name in targets:
            draw()


def sheet_path(name):
    """シートの出力先（src/<name>。LAYOUT・ONLY のときは work/ 以下）。入口が自前のシートを書くときに使う"""
    return os.path.join(SRC, name)
