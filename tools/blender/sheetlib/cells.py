"""セルの描画（持ち分マスク・手前の絵の分離）・特殊色・シート化（共通の描画の道具 sheetlib の一部。tools/README.md）。"""
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
    ALPHA_THRESHOLD,
    CELL,
    PX_PER_UNIT,
    SPECIAL,
    SPECIAL_COLORS,
    TILE,
    THIN_ALPHA,
    TRANSPARENT,
    WORK,
    NEAR_AXIS,
    near_camera,
    path_centre,
)


# ---------------------------------------------------------------- 描画と合成

SPECIAL_NAMES = list(SPECIAL)


def _code(k):
    """マスク描画で k 番目の特殊色を表す赤の値（0-255）。"""
    return (k + 1) * 12


def _srgb_to_linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def _mask_materials():
    """特殊色の材質ごとの発光マスク材質と、それ以外を隠す holdout 材質。"""
    out = {}
    for k, name in enumerate(SPECIAL_NAMES):
        mname = "mask_" + name
        m = bpy.data.materials.get(mname)
        if m is None:
            m = bpy.data.materials.new(mname)
            m.use_nodes = True
            nt = m.node_tree
            nt.nodes.clear()
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Color"].default_value = (_srgb_to_linear(_code(k) / 255), 0, 0, 1)
            em.inputs["Strength"].default_value = 1.0
            o = nt.nodes.new("ShaderNodeOutputMaterial")
            nt.links.new(em.outputs[0], o.inputs["Surface"])
        out[name] = m
    hold = bpy.data.materials.get("mask_holdout")
    if hold is None:
        hold = bpy.data.materials.new("mask_holdout")
        hold.use_nodes = True
        nt = hold.node_tree
        nt.nodes.clear()
        ho = nt.nodes.new("ShaderNodeHoldout")
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(ho.outputs[0], o.inputs["Surface"])
    out[None] = hold
    return out


# 持ち分マスク: タイルの地面が画面で占める画素（平らなら菱形、坂なら傾いた四角形）。
# OTRP はタイルごとに「地面 → その上の道」の順に描くので、奥のタイルが手前のタイルの地面の範囲へ描いた画素は、
# 手前の地面で上書きされる。だから、地面の範囲の画素は必ずそのタイル自身が描き、範囲の外は描かない。
# （以前は「見えている面のワールド座標がタイルの中か」で決めていた。少し高さのある道床の側面などは
# 画面では隣の菱形に入るので、隣の地面に上書きされて草の点が出たり、重ねる幅の調整が必要になったりした）


def exits_of(name):
    """セルの名前（ns, up12, diag_sw, curve_ne, nse など）から、つながる辺（n/s/e/w の文字列）を返す。"""
    if name.startswith("close"):
        return "nsew"
    if name.startswith("up"):
        code = int(name.split("_")[-1]) if "_" in name else int(name[2:])
        return "ns" if code in (12, 3) else "ew"
    if name == "single":
        return ""
    return _junction(name.split("_")[-1])


def _junction(name):
    """分岐の絵の名前（nse1・nsew2 など）を、元の T字・十字の名前に戻す。それ以外はそのまま。"""
    return name[:-1] if name[-1:] in ("1", "2") and name[:-1] in ("nse", "new", "nsw", "sew", "nsew") else name


# T字の手前/奥の向き: まっすぐ通る道に対して決める。南北の道は東が手前、東西の道は南が手前
_JUNCTION_AXIS = {"nse": Vector((1, 0, 0)), "nsw": Vector((1, 0, 0)), "new": Vector((0, -1, 0)), "sew": Vector((0, -1, 0))}


def near_frame(name, paths, origin=None):
    """手前/奥を測る向きと点 (axis, origin)。残す壁を選ぶとき（select_walls）と奥・手前の絵に分けるとき（render_layers）で同じものを使う。
    向きは T字ならまっすぐ通る道に対して、それ以外はカメラの向き（NEAR_AXIS）。
    点は、渡されなければ、経路が複数ならタイルの中心、1 本ならその経路の中心線の中心"""
    if origin is None:
        origin = Vector((0, 0, 0)) if len(paths) > 1 else path_centre(paths)
    return _JUNCTION_AXIS.get(_junction(name), NEAR_AXIS), origin


# ゲームが地面の菱形を塗る位置（セルの中で、タイル中心が何px目か）。dat のオフセット -64,-32 と対応し、
# 線路の描画位置（TRACK_PROFILES の dy）には関係しない。ゲーム画面との比較（blender/ingame_diff.py）で合わせた
GROUND_CY = 127


# 道路を描く位置。SIS・pak128 標準の道路は、菱形を地面より 1px 下にずらした絵で、自分の菱形の上の1行は描かず、
# 奥のタイルの絵が下へ1行はみ出して埋める（平らな地面は先にまとめて描かれ、はみ出しは消えない）。
# 同じ決まりにしないと、標準の道路とのつなぎ目に草の線（手前が標準）や 1px の段（奥が標準）が出る。
# 持ち分も絵と同じだけ下げるので、形が曲がる所と持ち分の境がそろい、自分どうしのつなぎ目は地面の位置で描いたときと同じになる
ROAD_CY = 128


def _ground_mask(slope, side=None, cy=GROUND_CY, spill=0, solid=False, lower=0):
    """タイルの地面（四隅の高さは slope、無ければ平ら）が画面で占める画素。画素の中心が四角形の中なら 255。
    side（top/bottom/left/right）を渡すと、菱形のうち中心を通る横・縦の線のその側だけにする（斜めのタイル）。
    線は隣の菱形の頂点と同じ位置なので、隣の直線・斜めのタイルの縁と同じ行・列で切れる。
    cy は菱形の中心の行（絵を地面より下に描くときは、持ち分も下げる）。坂は本体が地面を物と一緒に後から描き、
    奥のタイルのはみ出しを消すので、地面の位置（GROUND_CY）の菱形も足す。
    spill は、菱形のまま手前の2辺だけを何行広げるか（その下へ半行も足す）。pak128 標準の線路（Rail_100）は
    自分の菱形の上の1行を描かず、奥のタイルのはみ出しで埋めるので、奥に来たときにそこを埋める"""
    m = _ground_mask_at(slope, side, cy)
    if solid and slope:
        # 平らな地面の上に立つ坂（橋の端）: 坂の面から地面までの間も持ち分にする（躯体の側面が見える）
        for k in range(32):
            m |= _ground_mask_at(lambda x, y, k=k: slope(x, y) * k / 32, side, cy)
    if spill:
        m |= _ground_mask_at(slope, side, cy + spill) | _ground_mask_at(slope, side, cy + spill + 0.5)
    if cy != GROUND_CY:
        # 手前の縁を半行広げる（標準の道路は上の縁を半行ずれた並びで空けるので、1画素おきに草が見えた）
        m |= _ground_mask_at(slope, side, cy + 0.5)
        if slope:
            m |= _ground_mask_at(slope, side, GROUND_CY)
    if lower:
        # 下へ広げる（高架: 床の下の橋脚が、床より lower 行下の地面まで見える）
        base = m.copy()
        for k in range(1, lower + 1):
            m[k:] |= base[:-k]
    return m


def _ground_mask_at(slope, side, cy):
    half = TILE / 2
    up = PX_PER_UNIT * math.sin(math.radians(60))  # 高さ 1 → 画面で上へ何px（H で 16px）
    pts = []
    for x, y in ((-half, -half), (half, -half), (half, half), (-half, half)):
        z = slope(x, y) if slope else 0.0
        pts.append((CELL / 2 + (x + y) * 64 / TILE, cy + (x - y) * 32 / TILE - z * up))
    yy, xx = np.mgrid[0:CELL, 0:CELL] + 0.5
    inside = np.ones((CELL, CELL), bool)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        # 並びは 左→下→右→上 の角。内側は辺に対して外積が負の側
        inside &= (x1 - x0) * (yy - y0) - (y1 - y0) * (xx - x0) < 0
    if side is not None:
        inside &= {"top": yy < cy, "bottom": yy > cy,
                   "left": xx < CELL / 2, "right": xx > CELL / 2}[side]
    return inside


def _render_ground(slope, path, side=None, cy=GROUND_CY, spill=0, solid=False, lower=0):
    """持ち分マスク（地面の範囲）を PNG に書く。"""
    m = _ground_mask(slope, side, cy, spill, solid, lower).astype(np.uint8) * 255
    save_rgba(path, np.dstack([m, m, m, np.full_like(m, 255)]))


def render_cell(name, exits=None, slope=None, side=None, cy=GROUND_CY, spill=0, solid=False, lower=0):
    """通常の描画に加えて、
    - exits を渡したタイル（線路・道路）は name_own.png（持ち分マスク = 地面の範囲）を描く。
      画素の中心が地面の菱形の中なら残す。slope は坂の高さ slope(x, y)
    - 特殊色の材質があれば name_mask.png も描く（どの画素にどの特殊色を入れるか）"""
    path = os.path.join(WORK, name + ".png")
    mask_path = os.path.join(WORK, name + "_mask.png")
    own_path = os.path.join(WORK, name + "_own.png")
    scene = bpy.context.scene
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for p in (mask_path, own_path):
        if os.path.exists(p):
            os.remove(p)
    if exits is not None:
        _render_ground(slope, own_path, side, cy, spill, solid, lower)
    meshes = [ob for ob in scene.objects if ob.type == "MESH"]
    if not any(s.material and s.material.get("special") for ob in meshes for s in ob.material_slots):
        return path
    masks = _mask_materials()
    saved = []
    for ob in meshes:
        for s in ob.material_slots:
            saved.append((s, s.material))
            s.material = masks[s.material.get("special") if s.material else None]
    scene.render.filepath = mask_path
    bpy.ops.render.render(write_still=True)
    for s, m in saved:
        s.material = m
    return path


def render_layers(name, obs, split, exits, slope, cy, spill, rise, solid=False, lower=0, side=None, separate=False, tall_layers=True,
                  frame=None):
    """高さのある部品（tall）を別の層として描いて重ねる。返すのは（奥の絵のパス, 手前の絵のパス または None）。
    - 本体: 持ち分（地面の範囲）で切る
    - 高さのある部品: 持ち分を上へ rise 行広げた範囲で切る（奥のタイルの絵の上に出る。建物と同じ）
    - split なら、カメラに近い側の部品は手前の絵（dat の frontimage。車両の上に描かれる）に分ける
    side は本体の持ち分を菱形の半分にする（道路の斜め。_ground_mask）。高さのある部品の持ち分は菱形全体のまま（形のほうで帯に切ってある）。
    separate なら重ねずに（本体の絵のパス, 高さのある部品の奥の絵のパス または None, 手前の絵のパス または None）を返す
    （壁を way-object に分ける版。本体は way の絵、壁は way-object の絵になる。本体の絵は持ち分と特殊色を make_sheet が当てる）。
    tall_layers が偽なら、高さのある部品は描かない（separate の雪の絵。way-object には雪の絵が無い）。
    frame は手前/奥を測る向きと点（near_frame。split なら要る）"""
    tall = [ob for ob in obs if ob.get("tall")]
    body = [ob for ob in obs if not ob.get("tall")]
    for ob in tall:
        ob.hide_render = True
    body_path = render_cell(name, exits, slope=slope, side=side, cy=cy, spill=spill, solid=solid, lower=lower)
    if separate and not tall_layers:
        for ob in obs:
            ob.hide_render = False
        return body_path, None, None
    img = load_rgba8(body_path).copy()
    own = load_rgba8(os.path.join(WORK, name + "_own.png"))[..., 0] >= 128
    img[..., 3] = np.where(own, img[..., 3], 0)
    for ob in body:
        ob.hide_render = True
    m = _ground_mask(slope, None, cy, spill, solid, lower)
    # 上へ広げる: 持ち分の全体（坂の下・高架の下へ広げた分も含む）を 1 行ずつ上へずらして足す。
    # 前は地面の四角形だけをずらしていたので、地面を下げた絵（橋の Start）で、平らな橋の上の手前の壁が切れた
    base = m.copy()
    for k in range(1, rise + 1):
        m[:-k] |= base[k:]
    if separate and slope:
        # 壁を way-object に分ける版の坂: 持ち分を左右へ 1 列広げる。坂の上がった側の端で壁の最後の 1 列が切れ、
        # 隣の平らなタイル（十字など）の壁との間に 1px のすき間が出た（AMI #16 の指摘、2026-11-17）
        wide = m.copy()
        wide[:, 1:] |= m[:, :-1]
        wide[:, :-1] |= m[:, 1:]
        m = wide
    front = near_camera(obs, frame) if split else []
    if split:
        # Part.front の部品（架線の梁・トロリ線）は、位置に関わらず手前の絵にする（車両の上に描く）
        front += [ob for ob in tall if ob.get("front") and ob not in front]

    def layer(objs, suffix):
        for ob in tall:
            ob.hide_render = ob not in objs
        im = load_rgba8(render_cell(name + suffix)).copy()
        # 輪郭の半透明の画素は捨てる（色が暗く出て、壁の上の縁とタイルの境に黒い点線が見えた）
        im[..., 3] = np.where(m & (im[..., 3] >= 250), 255, 0)
        # 細い部品（架線の線）: それだけを描き直し、捨てた画素のうち THIN_ALPHA 以上覆われた所を不透明にして足す
        # （1px ほどの線は、全部の画素が半透明になって消えるため。2026-11-18）
        # 広げる部品（架線の梁）: それだけを描き直し、持ち分を左右へ 1 列広げた範囲で足す。斜めのタイルの梁はタイルの角を通って
        # 隣の斜めのタイルの梁とつながるが、菱形の角の列はどちらのタイルの持ち分にも入らず、2px の隙間が見えた（2026-11-18）
        wide = m.copy()
        wide[:, 1:] |= m[:, :-1]
        wide[:, :-1] |= m[:, 1:]
        for key, mask, alpha in (("thin", m, THIN_ALPHA), ("widen", wide, 250)):
            sel = [ob for ob in objs if ob.get(key)]
            if not sel:
                continue
            for ob in tall:
                ob.hide_render = ob not in sel
            th = load_rgba8(render_cell(name + suffix + "_" + key))
            fill = mask & (im[..., 3] == 0) & (th[..., 3] >= alpha)
            im[fill, :3] = th[fill, :3]
            im[fill, 3] = 255
        return im

    back = layer([ob for ob in tall if ob not in front], "_tallb")
    if separate:
        out = [body_path, None, None]
        for k, (objs, im, suffix) in enumerate(((None, back, "_wback"), (front, None, "_wfront"))):
            if objs is not None and not objs:
                continue
            im = layer(objs, "_tallf") if im is None else im
            if im[..., 3].any():
                out[1 + k] = os.path.join(WORK, name + suffix + ".png")
                save_rgba(out[1 + k], im)
        for ob in obs:
            ob.hide_render = False
        return tuple(out)
    a = back[..., 3:4].astype(np.float32) / 255
    img[..., :3] = (back[..., :3] * a + img[..., :3] * (1 - a)).astype(np.uint8)
    img[..., 3] = np.maximum(img[..., 3], back[..., 3])
    path = os.path.join(WORK, name + "_full.png")
    save_rgba(path, img)
    fpath = None
    if front:
        fpath = os.path.join(WORK, name + "_front.png")
        save_rgba(fpath, layer(front, "_tallf"))
    for ob in obs:
        ob.hide_render = False
    return path, fpath


def apply_special(rgb, render, mask):
    """マスクで覆われた画素（半分以上覆われたものだけ。縁は普通の色のまま）を特殊色にする。"""
    covered = mask[..., 3] >= 128
    codes = np.array([_code(k) for k in range(len(SPECIAL_NAMES))])
    # PNG は乗算済みでないアルファで保存されるので、赤の値がそのまま番号になる
    k_of = np.abs(mask[..., 0].astype(np.int32)[..., None] - codes).argmin(axis=-1)
    lum = render[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114])
    n = 0
    for k, name in enumerate(SPECIAL_NAMES):
        sel = covered & (k_of == k)
        if not sel.any():
            continue
        palette = np.array(SPECIAL[name])
        if len(palette) == 1:
            rgb[sel] = palette[0]
        else:
            # 明るさがいちばん近い段階を選ぶ
            pl = palette.astype(np.float32) @ np.array([0.299, 0.587, 0.114])
            rgb[sel] = palette[np.abs(lum[sel][:, None] - pl).argmin(axis=1)]
        n += int(sel.sum())
    return n


def load_rgba8(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    # Blender の pixels は下の行から。上から並べ直す
    return np.flipud((px.reshape(h, w, 4) * 255 + 0.5).astype(np.uint8))


def finalize(sheet):
    """iss と同じ後処理: 特殊色を1ずらし、ほぼ透明な画素を #E7FFFF にする。"""
    # int32 で計算する（int16 だと R*65536 が桁あふれして、特殊色を見逃したり関係ない色をずらしたりする）
    rgb = sheet[..., :3].astype(np.int32)
    keys = rgb[..., 0] * 65536 + rgb[..., 1] * 256 + rgb[..., 2]
    special = np.isin(keys, [r * 65536 + g * 256 + b for r, g, b in SPECIAL_COLORS])
    rgb[special] = np.minimum(rgb[special] + 1, 255)
    clear = sheet[..., 3] < ALPHA_THRESHOLD
    rgb[clear] = TRANSPARENT
    return rgb.astype(np.uint8), int(special.sum())


def save_rgb(path, rgb):
    h, w, _ = rgb.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=False)
    rgba = np.concatenate([rgb, np.full((h, w, 1), 255, np.uint8)], axis=2)
    img.pixels.foreach_set((np.flipud(rgba).astype(np.float32) / 255).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def make_sheet(cells, rows, cols, out):
    sheet = np.zeros((rows * CELL, cols * CELL, 4), np.uint8)
    masked = []
    for (r, c), path in cells.items():
        sl = (slice(r * CELL, (r + 1) * CELL), slice(c * CELL, (c + 1) * CELL))
        sheet[sl] = load_rgba8(path)
        own_path = path[:-4] + "_own.png"
        if os.path.exists(own_path):
            # 持ち分でない画素は透明にする（隣のタイルが描く）
            own = load_rgba8(own_path)
            sheet[sl][..., 3] = np.where(own[..., 0] >= 128, sheet[sl][..., 3], 0)
        mask_path = path[:-4] + "_mask.png"
        if os.path.exists(mask_path):
            masked.append((sl, load_rgba8(mask_path)))
    # 1) 描画で偶然できた特殊色を1ずらして消す 2) 材質で指定した特殊色を入れる（この順で）
    rgb, n_shift = finalize(sheet)
    n_set = sum(apply_special(rgb[sl], sheet[sl], mask) for sl, mask in masked)
    save_rgb(out, rgb)
    print(f"[sheet] {out} special colors: shifted {n_shift}, set {n_set}")


def save_rgba(path, rgba):
    h, w, _ = rgba.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    img.pixels.foreach_set((np.flipud(rgba).astype(np.float32) / 255).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
