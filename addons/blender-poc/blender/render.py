"""Blender から Simutrans 用のタイル画像シートを作る検証スクリプト。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/render.py

出力:
    src/track.png      線路・新描画位置（iss に合わせる）。src/track_old.png は旧描画位置（SIS に合わせる）
    src/road.png       道路（歩道付き。幅は SIS の一般道に合わせる）
    src/expressway.png 高速道路（歩道なし。SIS の高速道路に合わせる）
    src/tollbooth.png  料金所風の建物（屋根がタイルからはみ出す）
    work/              セルごとの生の描画結果（確認用）
"""
from dataclasses import dataclass
from typing import Callable
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
SRC = os.path.join(ROOT, "src")

CELL = 256                      # 1セルの画素数（iss と同じ）
TILE = 10.0                     # Blender上のタイル1辺
# タイル菱形が 128x64px になる正投影の幅（256px = タイル対角線2本分）
ORTHO = 2 * TILE * math.sqrt(2)
PX_PER_UNIT = CELL / ORTHO
# 高さ1段 = 16px（pak128）。Z方向は sin60° 倍で画面に映る
H = 16 / (PX_PER_UNIT * math.sin(math.radians(60)))

TRANSPARENT = (231, 255, 255)   # #E7FFFF
ALPHA_THRESHOLD = 25            # iss と同じ: これ未満は透過色にする
# 特殊色（Simutrans 本体 descriptor/image.cc の rgbtab と同じ順）。makeobj は RGB が完全に一致した画素だけを特殊色にする
def _hex(*v):
    return [((x >> 16) & 255, (x >> 8) & 255, x & 255) for x in v]


SPECIAL = {
    # プレーヤーカラー（会社の色に置き換わる）。8段階の明るさ
    "player1": _hex(0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF),
    "player2": _hex(0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D),
    # 夜に光る色
    "window_dark": _hex(0x57656F),    # 暗い窓。夜は黄色っぽく光る
    "window_light": _hex(0x7F9BF1),   # 明るい窓。夜は青っぽく光る
    "light_yellow": _hex(0xFFFF53),
    "light_red": _hex(0xFF211D),
    "light_green": _hex(0x01DD01),
    "grey1": _hex(0x6B6B6B),          # 夜も暗くならない灰色（メニュー用）
    "grey2": _hex(0x9B9B9B),
    "grey3": _hex(0xB3B3B3),
    "grey4": _hex(0xC9C9C9),
    "grey5": _hex(0xDFDFDF),
    "light_white": _hex(0xE3E3FF),    # 昼はほぼ白、夜は黄色っぽく光る
    "window_lit1": _hex(0xC1B1D1),    # 窓。夜は黄色く光る
    "window_lit2": _hex(0x4D4D4D),    # 窓。夜は黄色く光る
    "light_purple": _hex(0xFF017F),
    "light_blue": _hex(0x0101FF),
}
SPECIAL_COLORS = {c for colors in SPECIAL.values() for c in colors}
assert len(SPECIAL_COLORS) == 31


# ---------------------------------------------------------------- シーン設定

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    r = scene.render
    r.engine = "BLENDER_EEVEE_NEXT"
    r.resolution_x = r.resolution_y = CELL
    r.resolution_percentage = 100
    r.film_transparent = True
    r.filter_size = 1.0
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    scene.eevee.taa_render_samples = 16
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"

    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.47, 0.5, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.55
    scene.world = world

    # sis と同じ向き: 正投影・X60°・Z45°。原点がセル中央に映るように置く
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ORTHO
    cam = bpy.data.objects.new("cam", cam_data)
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    forward = cam.rotation_euler.to_matrix() @ Vector((0, 0, -1))
    cam.location = -forward * 60
    cam_data.clip_end = 200
    scene.collection.objects.link(cam)
    scene.camera = cam

    # 光は画面の左上（南西）から。左手前の面が明るく、右手前の面が暗くなる
    sun_data = bpy.data.lights.new("sun", "SUN")
    sun_data.energy = 2.2
    sun_data.angle = math.radians(2)
    sun = bpy.data.objects.new("sun", sun_data)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-45))
    scene.collection.objects.link(sun)
    return scene


def set_anchor(tile_center_y):
    """タイル中心をセルの何px目に映すか（dat のオフセットと対応）。"""
    bpy.context.scene.camera.data.shift_y = (tile_center_y - CELL / 2) / CELL


def noisy_material(name, rgb_a, rgb_b, scale=40.0, rough=0.8, emit=0.0, spec=None):
    """2色をノイズで混ぜた材質（石畳・アスファルトのまだら模様）。emit は明るさの底上げ。"""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 2.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*rgb_a, 1)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (*rgb_b, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    if spec is not None:
        bsdf.inputs["Specular IOR Level"].default_value = spec  # 照り返し（空の色の映り込み）の強さ
    if emit:
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emit
    return m


# 確認用の色: 環境変数 BPOC_DEBUG_COLORS=1 で、灰色ばかりの部品を見分けやすい色に替える。シートは work/debug/ に書く（src は変えない）
DEBUG_COLORS = {"ballast": (0.85, 0.75, 0.10), "sleeper": (0.95, 0.95, 0.95), "rail": (0.02, 0.02, 0.02),
                "wall": (0.90, 0.05, 0.05), "base": (0.05, 0.25, 0.90), "rust": (0.9, 0.3, 0.0),
                "rail_top": (0.0, 0.9, 0.9), "stop_post": (0.5, 0.0, 0.5), "base_open": (0.05, 0.75, 0.25)}
DEBUG = os.environ.get("BPOC_DEBUG_COLORS") == "1"


def material(name, rgb, rough=0.8, metal=0.0, emit=0.0, special=None):
    if DEBUG and name in DEBUG_COLORS:
        rgb, metal = DEBUG_COLORS[name], 0.0
    """special に SPECIAL の名前を渡すと、その材質が見えている画素を特殊色にする（render_cell と make_sheet で処理）。
    プレーヤーカラーは光の当たり方で8段階のどれかを選ぶので、rgb は灰色にしておくと明暗がそのまま段階になる。"""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    if special:
        assert special in SPECIAL, special
        m["special"] = special
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
        bsdf.inputs["Emission Strength"].default_value = emit
    return m


def mesh_object(name, verts, faces, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def clear_models():
    for ob in list(bpy.context.scene.objects):
        if ob.type == "MESH" and not ob.name.startswith("clip"):
            bpy.data.objects.remove(ob, do_unlink=True)


# ---------------------------------------------------------------- 形状

def box(cx, cy, cz, sx, sy, sz, rot=0.0):
    """中心・寸法・Z回転で直方体の頂点と面を返す。"""
    c, s = math.cos(rot), math.sin(rot)
    verts = []
    for dz in (-0.5, 0.5):
        for dx, dy in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
            x, y = dx * sx, dy * sy
            verts.append(Vector((cx + x * c - y * s, cy + x * s + y * c, cz + dz * sz)))
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return verts, faces


def merge(parts):
    verts, faces = [], []
    for v, f in parts:
        base = len(verts)
        verts += v
        faces += [tuple(i + base for i in face) for face in f]
    return verts, faces


def sweep(path, profile):
    """平面上の折れ線 path に沿って断面 profile(u=横, v=高さ) を押し出す。"""
    rings = []
    for i, p in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, len(path) - 1)]
        t = (b - a).normalized()
        n = Vector((t.y, -t.x, 0))
        rings.append([Vector((p.x, p.y, 0)) + n * u + Vector((0, 0, v)) for u, v in profile])
    k = len(profile)
    verts = [v for ring in rings for v in ring]
    faces = []
    for i in range(len(rings) - 1):
        for j in range(k):
            j2 = (j + 1) % k
            faces.append((i * k + j, i * k + j2, (i + 1) * k + j2, (i + 1) * k + j))
    faces.append(tuple(reversed(range(k))))
    last = (len(rings) - 1) * k
    faces.append(tuple(last + j for j in range(k)))
    return verts, faces


def along(path, step, offset):
    """path 上に step 間隔で (位置, 向き角) を並べる。"""
    out = []
    seg_lens = [(path[i + 1] - path[i]).length for i in range(len(path) - 1)]
    s = offset
    total = sum(seg_lens)
    while s < total:
        acc = 0.0
        for i, L in enumerate(seg_lens):
            if acc + L >= s:
                t = (s - acc) / L
                p = path[i].lerp(path[i + 1], t)
                d = path[i + 1] - path[i]
                out.append((p, math.atan2(d.y, d.x)))
                break
            acc += L
        s += step
    return out


# 経路をタイルの辺からどれだけ外へ延ばすか。形を切り抜く幅（CLIP_PAD）より十分長くする。
# 同じ長さだと、車道を抜く型の端が切り抜きの縁と重なる。カーブでは型の端がわずかに斜めなので、
# 縁石が細いくさびの形で残り、直線とのつなぎ目に灰色の点線が出た
PATH_EXT = 1.5


def straight(a, b, ext=PATH_EXT):
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    return [a - d * ext, b + d * ext]


def arc(center, start_deg, end_deg, radius=TILE / 2, n=24, ext=PATH_EXT):
    c = Vector(center)
    pts = []
    for i in range(n + 1):
        t = math.radians(start_deg + (end_deg - start_deg) * i / n)
        pts.append(c + Vector((math.cos(t), math.sin(t))) * radius)
    # 端は円の接線の向きに延ばす（多角形の最後の辺の向きだと、辺に対して少し斜めになる）
    sgn = 1 if end_deg > start_deg else -1
    tan = lambda deg: Vector((-math.sin(math.radians(deg)), math.cos(math.radians(deg)))) * sgn
    return [pts[0] - tan(start_deg) * ext] + pts + [pts[-1] + tan(end_deg) * ext]


# pak128 標準に合わせて低くする: 道床の厚み0.12（画面で約1px）、レール上面0.30（約2px）
BALLAST_H = 0.12
BALLAST = [(-1.9, 0.0), (1.9, 0.0), (1.55, BALLAST_H), (-1.55, BALLAST_H)]
SLEEPER_Z, SLEEPER_H, SLEEPER_LEN = 0.15, 0.08, 2.0
# レールの間隔は iss・SIS に合わせて画面上 6px（直線で 1単位 ≈ 6.4px）
RAIL_IN, RAIL_OUT, RAIL_Z0, RAIL_Z1 = 0.417, 0.517, 0.19, 0.30

# 斜めのタイルの横幅の倍率。3D のまま描くと、斜めは横幅が縮まずに映って直線の約1.6倍太く見える。
# 画面上で直線と同じ太さに見える比率 2/√10 にする（pak128 標準も斜めはレール間隔を細く描く）
DIAG_RAIL = 2 / math.sqrt(10)
# 道床は、直線とのつなぎ目（タイルの辺）で直線と同じ幅になる 1/√2（斜めは辺を 45° で横切る）。
# 以前の 0.8 は辺で直線より約 1.8px 広く、つなぎ目の角に段と草の尖りが出た
DIAG_BALLAST = 1 / math.sqrt(2)


# ---- 組み立て: 道は「部品」の集まりで、部品はどれかの「基準面」に乗る。
# 描画位置のずれ（下げ幅）は部品ではなく基準面が持つ。同じ基準面の部品は必ず一緒に動くので、
# 部品を足しても（車止め・側壁・さび・雪など）、乗る基準面を選べば位置は決まる。
#   bed:  路盤の面。道床・側壁・橋脚など、地面に置く物
#   rail: 走行面。まくらぎ・レール・車止めなど、軌道に付く物


@dataclass(frozen=True)
class Datum:
    """基準面の描画位置。drop は平地の画面で何 px 下に描くか。
    ground は、そのうち「地面の上での位置のずれ」にあたる px（残りは、形の高さや基準位置を打ち消す分）。"""
    drop: int = 0
    ground: int = 0


@dataclass(frozen=True)
class Part:
    """部品。shape(path, k) は経路に沿った形（頂点, 面）を返す（無ければ None）。k は横幅の倍率。
    datum: 乗る基準面。width: 横幅の倍率をどれに合わせるか（widths のキー）。
    group: 部品のまとまり（body: 本体。今後 structure: 立体パーツ、weathering: 汚れ、snow: 雪 など。assemble の groups で選ぶ）"""
    name: str
    datum: str
    width: str
    material: tuple
    shape: Callable
    group: str = "body"
    where: str = "path"  # path: 経路に沿う。end: 経路の始点（行き止まりの端）に置く。assemble(ends=True) のときだけ作る
    tall: bool = False   # 高さのある部品。タイルちょうどに切り、持ち分を上へ広げた層として別に描く（render_layers）
    ground: bool = False  # 坂のタイルだけで作り、坂を当てた後に地面（z=0）より下を切り上げる（坂の下を埋める躯体）
    corridor: float = 0.0  # 分岐・十字で、ほかの経路の通り道（中心からこの幅）に入る部分を削る（側壁が線路を横切らないように）
    # 道路の部品（where="tile"・"line"）。tile はタイルに 1 枚の板で、shape(tile, k) を受ける。line は白線 1 本ごとで、shape(path, u, lw, k)
    carve: Callable = None  # tile の板から、全部の経路に沿って車道を抜く。carve(tile, k) は抜く半幅（k を掛ける前）
    transfer: bool = False  # 抜いた切り口に型の材質を移す（縁石の立ち上がり）
    thick: float = 0.0      # 側壁の厚み（corridor で後の経路の壁を削る幅に足す。0 は線路の WALL_W）


def make_material(spec):
    """部品の材質: material() の引数の組か、材質を返す関数（まだらの材質など）。"""
    return spec() if callable(spec) else material(*spec)


def _bed_shape(path, k):
    return sweep(path, [(u * k, v) for u, v in BALLAST])


def _sleeper_shape(path, k):
    boxes = [box(p.x, p.y, SLEEPER_Z, 0.24, SLEEPER_LEN * k, SLEEPER_H, rot=ang) for p, ang in along(path, 0.62, 0.31)]
    return merge(boxes) if boxes else None


def _rail_shape(side):
    def shape(path, k):
        a, b = RAIL_IN * k, RAIL_OUT * k
        if side < 0:
            return sweep(path, [(-b, RAIL_Z0), (-a, RAIL_Z0), (-a, RAIL_Z1), (-b, RAIL_Z1)])
        return sweep(path, [(a, RAIL_Z0), (b, RAIL_Z0), (b, RAIL_Z1), (a, RAIL_Z1)])
    return shape


_M_RAIL = ("rail", (0.50, 0.36, 0.30), 0.35, 0.6)
# 線路の部品（作る順 = 重なりの下から）
TRACK_PARTS = (
    Part("ballast", "bed", "bed", ("ballast", (0.42, 0.40, 0.37)), _bed_shape),
    Part("sleeper", "rail", "gauge", ("sleeper", (0.62, 0.61, 0.58)), _sleeper_shape),
    Part("railL", "rail", "gauge", _M_RAIL, _rail_shape(-1)),
    Part("railR", "rail", "gauge", _M_RAIL, _rail_shape(1)),
)


def _stop_shape(sy, sz, z, sx=0.2, back=0.0):
    """車止めの箱。行き止まりの端（経路の始点）から線路の側へ 0.7 入った所に、線路を横切る向きで置く。"""
    def shape(path, k):
        d = (path[1] - path[0]).normalized()
        c = path[0] + d * (0.7 - back)
        return box(c.x, c.y, z, sx, sy * k, sz, rot=math.atan2(d.y, d.x))
    return shape


def _strip_shape(u0, u1, z, th=0.004):
    """経路に沿った薄い帯（中心から u0〜u1、左右対称に2本）。面の上の色の違い（さび・わだち・光る頭）に使う。"""
    def shape(path, k):
        return merge([sweep(path, [(s * u0 * k, z), (s * u1 * k, z), (s * u1 * k, z + th), (s * u0 * k, z + th)][::s])
                      for s in (1, -1)])
    return shape


_M_STEEL = ("rail_top", (0.78, 0.79, 0.80), 0.25, 0.9)
# 立体パーツ・汚れ（TRACK_PROFILES の groups で選ぶ。本体のシートには入れていない）
TRACK_EXTRAS = (
    # 車止め: 柱2本 + 横木（赤）+ 中央の白い印
    Part("stop_postL", "rail", "gauge", ("stop_post", (0.20, 0.20, 0.22)),
         lambda path, k: _stop_shape(0.16, 0.75, RAIL_Z0 + 0.375, back=0.12)([path[0] + _side(path, 0.47 * k), path[1] + _side(path, 0.47 * k)], 1),
         "structure", "end"),
    Part("stop_postR", "rail", "gauge", ("stop_post", (0.20, 0.20, 0.22)),
         lambda path, k: _stop_shape(0.16, 0.75, RAIL_Z0 + 0.375, back=0.12)([path[0] - _side(path, 0.47 * k), path[1] - _side(path, 0.47 * k)], 1),
         "structure", "end"),
    Part("stop_beam", "rail", "gauge", ("stop_beam", (0.75, 0.10, 0.08)), _stop_shape(1.7, 0.36, RAIL_Z0 + 0.68), "structure", "end"),
    Part("stop_mark", "rail", "gauge", ("stop_mark", (0.92, 0.92, 0.90)), _stop_shape(0.5, 0.38, RAIL_Z0 + 0.68, sx=0.22), "structure", "end"),
    # さび色: レールの両脇の道床に鉄粉が散る。レールの頭は車輪で磨かれて光る
    Part("rust", "rail", "gauge", ("rust", (0.47, 0.31, 0.21)), _strip_shape(RAIL_IN - 0.24, RAIL_OUT + 0.24, BALLAST_H), "weathering"),
    Part("rail_top", "rail", "gauge", _M_STEEL, _strip_shape(RAIL_IN - 0.03, RAIL_OUT + 0.03, RAIL_Z1, 0.02), "weathering"),
)
# 側壁: 路盤の両脇に立つ壁（高さ 1.2 ≈ 画面で 9px）。道床と同じ基準面に乗り、横位置は道床の幅に合わせて動く
# 高さのある部品の切り抜きの余白（約 1.5px）。0 だと、切り口の面（暗い）がタイルの境に縦線で見えた
TALL_PAD = 0.15
WALL_U, WALL_W, WALL_H = 2.15, 0.22, 1.2
_M_WALL = ("wall", (0.60, 0.60, 0.58))


def _wall_shape(s, wu=None, ww=None, wh=None):
    """側壁（s=-1 が左、1 が右）。wu・ww・wh は経路から壁の内側までの距離・厚み・高さ（既定は線路の WALL_U・WALL_W・WALL_H）。"""
    wu, ww, wh = wu or WALL_U, ww or WALL_W, wh or WALL_H

    def shape(path, k):
        # 斜めも直線と同じ作り: 経路から一定の距離（斜めは道床と同じ倍率 k）。タイルの辺で直線の壁と同じ点を通る
        u0, u1 = s * wu * k, s * (wu + ww) * k
        return sweep(path, [(u0, 0.0), (u1, 0.0), (u1, wh), (u0, wh)][::s])
    return shape


def _end_wall(ww=None, wh=None):
    """行き止まりの端の壁: 経路の始点の奥（厚み ww）で左右の側壁をつなぐ（コの字になる）。"""
    ww, wh = ww or WALL_W, wh or WALL_H

    def shape(path, k):
        d = (path[1] - path[0]).normalized()
        c = path[0] - d * (ww / 2)
        # タイルの幅いっぱいに作る。側壁のある側は、その外側を後で削る（trim_end_walls）。側壁のない側はタイルの端まで延びて、
        # 並べた線路の端の壁とつながる（back・center・front を並べた行き止まりが、1 つのコの字になる）
        return box(c.x, c.y, wh / 2, ww, 14.0, wh, rot=math.atan2(d.y, d.x))
    return shape


_end_wall_shape = _end_wall()


def _ramp_body_shape(path, k):
    """橋の端の坂（平地から立ち上がる坂）の躯体: 基盤の下を地面まで埋める。assemble が坂を当てた後、地面より下を切り上げる。"""
    u = (WALL_U + WALL_W) * k
    return sweep(path, [(-u, -60.0), (u, -60.0), (u, -BASE_H), (-u, -BASE_H)])


TRACK_EXTRAS += tuple(Part(name, "bed", "bed", _M_WALL, _wall_shape(s), "wall", tall=True, corridor=WALL_U)
                      for name, s in (("wallL", -1), ("wallR", 1)))
# 橋: 床版（路盤の下の板）と橋脚。床版は路盤に乗る部品、橋脚は橋の下の地面のタイルに描く別の絵
BASE_H = 0.35
PIER_W, PIER_L = 1.6, 3.2


_M_BASE = ("base", (0.50, 0.50, 0.48))
PIER_SIZE = 1.6


def _pier_shape(path, k):
    """高架の橋脚: 経路の中ほどの下に立つ柱。床（基盤）の下から、1 段下の地面まで。"""
    mid = path[len(path) // 2] if len(path) > 2 else (path[0] + path[-1]) / 2
    d = (path[-1] - path[0]).normalized()
    return box(mid.x, mid.y, -(H + BASE_H) / 2, PIER_SIZE, PIER_SIZE * 2.4, H - BASE_H, rot=math.atan2(d.y, d.x))  # 線路を横切る向きに長い


TRACK_EXTRAS += (Part("pier", "bed", "bed", ("base", (0.50, 0.50, 0.48)), _pier_shape, "pier"),)
TRACK_EXTRAS += (Part("endw", "bed", "bed", _M_WALL, _end_wall_shape, "wall", "end", tall=True),
                 Part("rampbody", "bed", "bed", _M_BASE, _ramp_body_shape, "ramp", ground=True))
# 雪の絵（dat の image[..][1]）で差し替える材質。道床とまくらぎに雪が積もり、レールは見える
_SNOW = ("snow", (0.90, 0.93, 0.97), 0.9)
SNOW_SKIN = {"ballast": _SNOW, "sleeper": ("snow_sleeper", (0.80, 0.84, 0.90), 0.9), "base": _SNOW}
FLAT = {"bed": Datum(), "rail": Datum()}


def _side(path, u):
    """経路の始点で、進む向きに直角な向きへ u。"""
    d = (path[1] - path[0]).normalized()
    return Vector((d.y, -d.x)) * u


def datum_move(datum, slope=None, div=1):
    """基準面を画面で drop px 下に描くための、形の動かし方（坂を当てる前に足すベクトル）。動かし方はここだけで決める。
    画面で n px 下 = 地面の上で手前（カメラ側）へ動かしてから坂の高さを当てる（面に沿って動かす）。
    どの基準面も同じやり方で動かすので、坂でもレール・まくらぎは道床の上に乗ったまま（高さを変えずに動かすと埋もれる）。
    坂では手前へ動くと高さも変わり、同じ量を動かしても画面の下げ幅が平地の c 倍になる（c: 手前上がりの坂は 1 より小さい）。
    下げ幅 n のうち
      ground（地面の上での位置のずれ）: 平地と同じ量を動かす。画面の下げ幅は c 倍になるが、
        マップの上で同じ位置なので、タイルの辺で平らな隣の絵と同じ点を通る
      残り（形の高さ・基準位置を打ち消す分。高さは坂でも画面の縦に同じだけ見える）: 画面でちょうどその px になるよう c で割り戻す
    全部を割り戻すと、どの坂でもレールは道床の中ほどに来るが、帯全体が辺で 0.5px（急坂）ずれ、急坂と十字の継ぎ目で道床の縁に 1px の段が出た。
    div は下げ幅を割る数。画面で横向きの斜め（nw・se）は 2: 絵を下げることはマップ上で南東へずらすことと同じで、
    直線は辺を横切る点が辺に沿ってずれる。横向きの斜めは半分だけずらすと、両端で直線と同じ点を通る
    （縦向きの斜めはずらしても線が動かない）"""
    d = datum.drop // div
    if not d:
        return None
    cam = bpy.context.scene.camera
    rot = cam.rotation_euler.to_matrix()  # matrix_world は作った直後だと更新されていない
    up, fwd = rot @ Vector((0, 1, 0)), rot @ Vector((0, 0, -1))
    toward = -Vector((fwd.x, fwd.y, 0)).normalized()
    g = (slope(toward.x, toward.y) - slope(0, 0)) if slope else 0.0  # 手前へ 1 動いたときの高さの変化
    c = (toward.dot(up) + g * up.z) / toward.dot(up)
    px = toward * (cam.data.ortho_scale / CELL) / -toward.dot(up)  # 平地で画面の 1px 下にあたる動き
    ground = datum.ground if slope else 0
    return px * ((d - ground) / c + ground)


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
    mat = make_material(skin.get(part.name, part.material))
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
            ob = mesh_object(f"{part.name}{i}", *geo, make_material(skin.get(part.name, part.material)))
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
                             make_material(part.material))
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
    return [ob]


def _arc_circle(path):
    """カーブの経路の中心と半径（経路の中ほどの 3 点を通る円）。"""
    a, b, c = (Vector((q.x, q.y)) for q in (path[1], path[len(path) // 2], path[-2]))
    d = 2 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y))
    ux = (a.length_squared * (b.y - c.y) + b.length_squared * (c.y - a.y) + c.length_squared * (a.y - b.y)) / d
    uy = (a.length_squared * (c.x - b.x) + b.length_squared * (a.x - c.x) + c.length_squared * (b.x - a.x)) / d
    centre = Vector((ux, uy))
    return centre, (a - centre).length


def _beyond_prisms(walls, paths, k, wu=None, ww=None):
    """残した壁それぞれの「外側」を表す柱の集まり（基盤や端の壁から削る型）。wu・ww は壁の位置と厚み（既定は線路）。"""
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
                cut.append(prism([(q.x, q.y) for q in ring(r - uw)], -2, 2))
            elif not w["cut"]:
                a, b = ring(r + uw), ring(40.0)
                cut += [prism([(q.x, q.y) for q in (a[i], b[i], b[(i + 1) % 64], a[(i + 1) % 64])], -2, 2) for i in range(64)]
            continue
        else:  # 直線・斜め
            if w["cut"]:
                continue
            d = (path[-1] - path[0]).normalized()
            n = Vector((d.y, -d.x)) * s
            a, b = path[0] - d * 30, path[-1] + d * 30
            pts = [a + n * uw, b + n * uw, b + n * 40, a + n * 40]
        cut.append(prism([(q.x, q.y) for q in pts], -2, 2))
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


def open_ends(ob, pad):
    """タイルの境で切った切り口の面を取る。切り口の面は壁の側面より暗く映り、隣のタイルの壁との境に縦線で見えた。
    行き止まりの端（タイルの中にある端）の面は残る。"""
    lim = TILE / 2 + pad
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    dead = [f for f in bm.faces if any(all(abs(v.co[a] - s * lim) < 1e-4 for v in f.verts) for a in (0, 1) for s in (1, -1))]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def _centre(objs):
    vs = [v.co for ob in objs for v in ob.data.vertices]
    return sum(vs, Vector()) / max(1, len(vs))


# 手前/奥を決める向き。カメラは南東にあるので南東が手前。北東と南西は奥行きが同じなので、iss と同じく東寄りを手前にする
NEAR_AXIS = Vector((1.0, -0.5, 0.0)).normalized()


def near_camera(obs, axis=NEAR_AXIS, kind="tall", origin=None):
    """部品（kind="tall": 高さのある部品、それ以外は名前の頭）のうち、手前の側にあるもの（重心が、本体の重心より axis の向きにある）。
    origin を渡すと、本体の重心の代わりにその点から測る"""
    ref = _centre([ob for ob in obs if not ob.get("tall")]) if origin is None else origin
    pick = (lambda ob: ob.get("tall")) if kind == "tall" else (lambda ob: ob.name.startswith(kind))
    return [ob for ob in obs if pick(ob) and (_centre([ob]) - ref).dot(axis) > 0.3]


def apply_slope(ob, slope):
    """坂の高さ slope(x, y) を形に当てる。タイルの外（隣と重ねて描く部分）は、辺の高さのまま平らに延ばす。
    傾きの式をそのまま外へ延ばすと、重ねた部分が隣の平らな面より下（上）にずれて、
    付け根で白線・縁石・道床に段差が出る。辺の上で折れるように、先に辺の位置で面を切っておく。"""
    half = TILE / 2
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for co, no in (((half, 0, 0), (1, 0, 0)), ((-half, 0, 0), (1, 0, 0)),
                   ((0, half, 0), (0, 1, 0)), ((0, -half, 0), (0, 1, 0))):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no)
    clamp = lambda t: max(-half, min(half, t))
    for v in bm.verts:
        v.co.z += slope(clamp(v.co.x), clamp(v.co.y))
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


_clippers = {}


# 形はタイルより少し大きく切り抜いておく（タイルの端の画素も、隣とつながった形で描くため）。
# どの画素を残すかは render_cell の「持ち分マスク」で決める
CLIP_PAD = 0.6


def clip_to_tile(ob, pad=CLIP_PAD):
    """タイルの範囲（xy: ±TILE/2）より pad だけ大きく切り抜く。高さのある部品（側壁など）は pad=0 でタイルちょうどに切る
    （持ち分を上へ広げるので、はみ出した分が奥のタイルの絵の上に出てしまう）。"""
    _clipper = _clippers.get(pad)
    if _clipper is None or _clipper.name not in bpy.data.objects:
        v, f = box(0, 0, 0, TILE + 2 * pad, TILE + 2 * pad, 60)
        me = bpy.data.meshes.new("clip")
        me.from_pydata([tuple(x) for x in v], [], f)
        _clipper = _clippers[pad] = bpy.data.objects.new("clip", me)
        _clipper.hide_render = True
        bpy.context.scene.collection.objects.link(_clipper)
    mod = ob.modifiers.new("clip", "BOOLEAN")
    mod.operation = "INTERSECT"
    mod.solver = "EXACT"
    mod.object = _clipper
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


# ---------------------------------------------------------------- 道路
# SIS の一般道（SIS_L_RG1-1_01S、歩道付き 50km/h）の断面に合わせる。横位置はタイル半幅 5 に対する値:
#   中央線 0 / 車道 ±3.2 / 路側の白線 ±3.3〜3.45 / 縁石 ±3.6〜3.85 / 歩道 〜タイルの端
ROAD_HW = 3.6          # 車道の半幅（縁石の立ち上がりまで）
CURB_W = 0.25          # 縁石の上面の幅
SIDEWALK_H = 0.25      # 歩道の高さ（縁石の立ち上がり 約2px）
LINE_W = 0.15          # 白線の幅（約1px）
EDGE_LINE = 3.37       # 路側の白線の中心
ROAD_DIAG = 2 / math.sqrt(10)  # 斜めの横幅の倍率（SIS も線路と同じく縮めている）
# 斜めのタイルの車道・縁石・白線は、直線とのつなぎ目（タイルの辺）で直線と同じ点を通るようにする。
# 斜めは辺を 45° で横切るので、経路からの距離は直線の 1/√2。SIS の斜め（車道 2.7、白線は直線の 0.632〜0.68 倍）は
# これより少し外・内にずれていて、つなぎ目で白線が1px 切れ、縁石が1〜2px 段になっていた
DIAG_EDGE = 1 / math.sqrt(2)


def boolean(ob, cutter, op="DIFFERENCE", transfer=False):
    mod = ob.modifiers.new("bool", "BOOLEAN")
    mod.operation = op
    mod.solver = "EXACT"
    mod.object = cutter
    mod.use_self = True  # 型が重なり合う（分岐・十字）ときも抜けるように
    if transfer:
        mod.material_mode = "TRANSFER"
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


def prism(pts, z0=-1.0, z1=1.0):
    """平面の多角形 pts を z0〜z1 に押し出した柱の頂点と面。"""
    n = len(pts)
    verts = [Vector((x, y, z0)) for x, y in pts] + [Vector((x, y, z1)) for x, y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    return verts, faces


def corner_piece(corner, r, n=12):
    """タイルの角 corner の歩道を、四角から半径 r の扇形にするために抜く部分（四角 - 扇形）。"""
    cx, cy = corner
    sx, sy = math.copysign(1, cx), math.copysign(1, cy)
    pts = [(cx - sx * r, cy), (cx - sx * r, cy - sy * r), (cx, cy - sy * r)]
    a0 = math.atan2(-sy, 0)
    a1 = math.atan2(0, -sx)
    if a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    if a0 - a1 > math.pi:
        a1 += 2 * math.pi
    for i in range(1, n):
        t = a0 + (a1 - a0) * i / n
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return prism(pts)


# 斜めのタイルで残す範囲: 中心を通る線と、残す角の頂点を通る線（どちらも経路に平行）の間の帯。
# 隣の斜めのタイルは、この帯の続きを描く。角の線で切るのは、その先（隣の草地のタイル）にある歩道が、
# 高さがあるので画面では上へずれて、この菱形の角に入り込むため。
# 帯の縁は、画面では菱形の頂点を通る横（se・nw）か縦（sw・ne）の線になる。この線で正確に切るのは
# 持ち分マスク（_ground_mask の side）の側で行い、形のほうは帯より DIAG_OVERFILL だけ広く残しておく。
# 形の側で切ると、道路の絵は地面より1px 下に描き、歩道の上面は高さの分だけ上へずれるので、縁が頂点の行から
# 1〜2px ずれる。縁の内側に寄せる（以前の DIAG_CUT_INSET）と、今度は直線の舗装の角（頂点の行まである）と段になった
DIAG_OVERFILL = 0.6

# 斜めのタイルで残す画面の半分（帯の範囲）。nw は上、se は下、sw は左、ne は右
DIAG_HALF = {"diag_nw": "top", "diag_se": "bottom", "diag_sw": "left", "diag_ne": "right"}


def half_tile(path, over=DIAG_OVERFILL):
    """斜めのタイルで残す範囲（経路が切り取る角の側の帯）を、少し広げた箱。Simutrans は残りを隣のタイルに描く。
    over は中心線を越えて広げる幅（近い斜めは 2 片を 1 枚に描くので 0 にして、片どうしを重ねない）"""
    mid = (path[0] + path[-1]) / 2
    u = Vector((mid.x, mid.y)).normalized()
    ang = math.atan2(u.y, u.x)
    far = TILE / 2 * math.sqrt(2)  # 中心から角の頂点を通る線まで
    lo, hi = -over, far + DIAG_OVERFILL
    c = (lo + hi) / 2
    return box(u.x * c, u.y * c, 0, hi - lo, 60, 80, rot=ang)


def recalc_normals(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


def dashes(path, dash=0.6, period=1.6):
    """2点の経路 path を点線の短い経路に分ける。"""
    a, b = path[0], path[-1]
    d = (b - a).normalized()
    out, t, L = [], period / 2, (b - a).length
    while t < L:
        out.append([a + d * t, a + d * min(t + dash, L)])
        t += period
    return out


# 道路の材質（まだらの材質は関数で渡す。make_material）
_M_ROAD_ASPHALT = lambda: noisy_material("road_asphalt", (0.013, 0.0135, 0.015), (0.028, 0.029, 0.031), scale=60, rough=0.9)
# 高速道路は SIS に合わせて暗く青みのあるアスファルト（平均 20,20,27）。照り返しを切らないと空の色が映って明るくなる
_M_EXPWY_ASPHALT = lambda: noisy_material("expwy_asphalt", (0.0027, 0.0027, 0.004), (0.016, 0.016, 0.023), scale=60,
                                          rough=0.9, spec=0.0)
_M_CURB = ("road_curb", (0.62, 0.61, 0.59))
_M_PAVING = lambda: noisy_material("road_paving", (0.025, 0.035, 0.02), (0.26, 0.31, 0.22), scale=35)
_M_LINE = ("road_line", (0.95, 0.95, 0.95), 0.6, 0.0, 0.6)


def _line_shape(path, u, lw, k):
    w = lw / 2
    u *= k
    return sweep(path, [(u - w, 0.0), (u + w, 0.0), (u + w, 0.012), (u - w, 0.012)])


# 路面の痛み（group "weathering"。線路のさび色に当たる）: 形ではなく材質の違い。路面の上の薄い板で、横位置は車線（倍率 "lane"。
# 斜めは直線の 1/√2 で、タイルの辺で直線と同じ点を通る）に合わせる。車線は中央線から路側の白線まで（中心 ±1.6）
#   wear0〜2: 車輪の通る所が磨かれて明るい帯。小型車から大型車まで輪距が違うので幅を広く取り、広く薄い帯（wear0）の上に
#   狭く濃い帯（wear2）を重ねて縁をぼかす / oil: 車線の中ほどに落ちた油の暗い帯
#   補修跡（patch）は、1 タイルごとに同じ所に並ぶと目立つのでやめた（2026-11-15、ゲームで確認）
WEAR_LAYERS = (  # (帯の並び, 路面の色からの寄せ具合, 行き止まりで始点を開ける距離)
    (((0.55, 1.40), (1.80, 2.65)), 0.30, 0.0),
    (((0.70, 1.25), (1.95, 2.50)), 0.55, 0.7),
    (((0.85, 1.10), (2.10, 2.35)), 0.80, 1.4),
)
OIL_U = (1.45, 1.75)
_WEAR_LO, _WEAR_HI = (0.030, 0.031, 0.033), (0.060, 0.061, 0.064)
_M_OIL = lambda: noisy_material("road_oil", (0.004, 0.004, 0.005), (0.012, 0.012, 0.013), scale=90, rough=0.7)


def _wear_material(tag, lo, hi, t, spec=None):
    """走行跡の材質: 路面の 2 色（lo・hi）を、磨かれた色へ t だけ寄せる。"""
    mix = lambda a, b: tuple(x + (y - x) * t for x, y in zip(a, b))
    return lambda: noisy_material(f"road_wear_{tag}_{round(t * 100)}", mix(lo, _WEAR_LO), mix(hi, _WEAR_HI), scale=90,
                                  rough=0.9, spec=spec)


class WearPath(list):
    """走行跡だけに使う経路。fade=True は行き止まりへ向かう経路で、始点（閉じた側）から濃い帯ほど手前で止める。"""
    fade = False


def _trim_start(path, dist):
    """折れ線の始点を dist だけ先へ詰める。"""
    out = list(path)
    while dist > 0 and len(out) > 1:
        seg = (out[1] - out[0]).length
        if seg > dist:
            out[0] = out[0].lerp(out[1], dist / seg)
            break
        dist -= seg
        out.pop(0)
    return out


def _lane_strips(spans, z=0.0, th=0.004, fade=0.0):
    """経路に沿った薄い帯（中心から u0〜u1 を左右に 1 本ずつ。spans は (u0, u1) の並び）。白線（厚み 0.012）より下に置く。
    fade は WearPath(fade=True) のときに始点から詰める距離"""
    def shape(path, k):
        if getattr(path, "fade", False):
            path = _trim_start(path, fade)
        return merge([sweep(path, [(s * u0 * k, z), (s * u1 * k, z), (s * u1 * k, z + th), (s * u0 * k, z + th)][::s])
                      for u0, u1 in spans for s in (1, -1)])
    return shape


# 道路の部品（作る順 = 重なりの下から）。どれも路面の基準面（bed）に乗り、横幅の倍率は "road"（斜めは ROAD_DIAG）。
#   asphalt: タイル全面の路面 / curb: 歩道の高さの板から車道を抜く（切り口が縁石の立ち上がり）/ paving: 歩道の石畳（縁石の上面の幅だけ広く抜く）
#   line: 白線（RoadTile.lines の 1 本ごと）
# 歩道は全面の板から車道を抜いて作るので、分岐の口やカーブの外側も自然に埋まる。高速道路は group "sidewalk" を使わない
ROAD_PARTS = (
    Part("asphalt", "bed", "road", _M_ROAD_ASPHALT, lambda t, k: box(0, 0, -0.02, *t.size, 0.04), where="tile"),
    Part("curb", "bed", "road", _M_CURB, lambda t, k: box(0, 0, SIDEWALK_H / 2, *t.size, SIDEWALK_H), "sidewalk", "tile",
         carve=lambda t, k: t.hw, transfer=True),
    Part("paving", "bed", "road", _M_PAVING, lambda t, k: box(0, 0, SIDEWALK_H + 0.01, *t.size, 0.02), "sidewalk", "tile",
         carve=lambda t, k: t.hw + t.curb_w / k),
    Part("line", "bed", "road", _M_LINE, _line_shape, "marking", "line"),
    Part("oil", "bed", "lane", _M_OIL, _lane_strips([OIL_U], fade=WEAR_LAYERS[1][2]), "weathering"),
) + tuple(Part(f"wear{i}", "bed", "lane", _wear_material("street", (0.013, 0.0135, 0.015), (0.028, 0.029, 0.031), t),
               _lane_strips(spans, 0.0015 * i, fade=f), "weathering") for i, (spans, t, f) in enumerate(WEAR_LAYERS))
# 雪の絵の路肩の雪（group "snow"）: 線路より除雪されている想定で、車道（路側の白線の少し外まで）を抜いた残りだけに積もる
# 境目は車線の境（路側の白線）のあたりでぼかす: 白線の内側まで薄いまだらの雪（シャーベット）を 3 段重ね、白線の外から積もった雪。
# 薄い段は白線（上面 0.012）より下に置き、白線はまだらの上に見せる。くっきりした境は目立った（2026-11-15、ゲームで確認）
SNOW_LAYERS = (  # (部品の名前, 雪を抜く半幅, 路面の色から雪へ寄せる具合（None は積もった雪）, 下面, 厚み)
    ("slush0", EDGE_LINE - 0.90, 0.20, 0.0075, 0.001),
    ("slush1", EDGE_LINE - 0.50, 0.40, 0.0085, 0.001),
    ("slush2", EDGE_LINE - 0.20, 0.55, 0.0095, 0.001),
    # 積もった雪は白線から 1〜2px 離し、間を灰色のまだらにする。白線のすぐ外から白い雪にすると、カメラに近い側の白線が
    # 雪と見分けられなかった（2026-11-15）。厚みも白線（0.012）より薄くする
    ("snowbank", EDGE_LINE + 0.35, None, 0.0, 0.0115),
)
_SNOW_LO, _SNOW_HI = (0.70, 0.73, 0.78), (0.90, 0.93, 0.97)


def _slush_material(tag, lo, hi, t, spec=None):
    """まだらの雪: 路面の 2 色を雪の色へ t だけ寄せ、粗いまだらにする（ぼかしの段）。"""
    mix = lambda a, b: tuple(x + (y - x) * t for x, y in zip(a, b))
    return lambda: noisy_material(f"road_slush_{tag}_{round(t * 100)}", mix(lo, _SNOW_LO), mix(hi, _SNOW_HI), scale=45,
                                  rough=0.9, spec=spec)


ROAD_PARTS += tuple(
    Part(n, "bed", "road", _SNOW if t is None else _slush_material("street", (0.013, 0.0135, 0.015), (0.028, 0.029, 0.031), t),
         (lambda z0, th: lambda t_, k: box(0, 0, z0 + th / 2, *t_.size, th))(z0, th), "snow", "tile",
         carve=(lambda w: lambda t_, k: t_.hw * w / ROAD_HW)(w))
    for n, w, t, z0, th in SNOW_LAYERS)
# 高速道路の側壁（iss の都市高速 wrg_0120 と同じく、タイルの端に立つコンクリートの壁）。路面の基準面に乗り、横位置は車線と同じ倍率
# （斜めは直線の 1/√2 で、タイルの辺で直線の壁と同じ点を通る）。外側の面はタイルの端の少し内側（4.95）
EXPWY_WALL_U, EXPWY_WALL_W, EXPWY_WALL_H = 4.55, 0.40, 1.1
ROAD_PARTS += tuple(Part(n, "bed", "lane", _M_WALL, _wall_shape(sg, EXPWY_WALL_U, EXPWY_WALL_W, EXPWY_WALL_H), "wall", tall=True,
                         corridor=EXPWY_WALL_U, thick=EXPWY_WALL_W) for n, sg in (("wallL", -1), ("wallR", 1)))
ROAD_PARTS += (Part("endw", "bed", "lane", _M_WALL, _end_wall(EXPWY_WALL_W, EXPWY_WALL_H), "wall", "end", tall=True),)
EXPWY_PIER_ACROSS = 2 * EXPWY_WALL_U  # 高架の橋脚の、道を横切る向きの長さ。床がタイルいっぱいなので、両側の壁の下まで届かせて床の縁から見せる（中央だけの柱は床に隠れた）


def _expwy_pier_shape(path, k):
    """高架の高速道路の橋脚: 経路の中ほどの下に立つ、道を横切る向きに長い柱（線路の _pier_shape と同じ置き方）。"""
    mid = path[len(path) // 2] if len(path) > 2 else (path[0] + path[-1]) / 2
    d = (path[-1] - path[0]).normalized()
    return box(mid.x, mid.y, -(H + BASE_H) / 2, PIER_SIZE, EXPWY_PIER_ACROSS * k, H - BASE_H, rot=math.atan2(d.y, d.x))


ROAD_PARTS += (Part("pier", "bed", "lane", _M_BASE, _expwy_pier_shape, "pier"),)
# 橋の端の坂（平地から立ち上がる坂）の躯体: 線路の rampbody と同じく、基盤の下を地面まで埋める（壁の外側まで）
ROAD_PARTS += (Part("rampbody", "bed", "lane", _M_BASE,
                    lambda path, k: sweep(path, [(-(EXPWY_WALL_U + EXPWY_WALL_W) * k, -60.0), ((EXPWY_WALL_U + EXPWY_WALL_W) * k, -60.0),
                                                 ((EXPWY_WALL_U + EXPWY_WALL_W) * k, -BASE_H), (-(EXPWY_WALL_U + EXPWY_WALL_W) * k, -BASE_H)]),
                    "ramp", ground=True),)
# 橋の桁: iss の都市高速の橋（bridge/road の 0120_bridge1）と同じく、床の縁を青い鋼の帯に見せる（基盤の側面）
_M_GIRDER = ("girder", (0.22, 0.40, 0.62))
# 道路の描き分け（ROAD_PROFILES）: skin は部品の材質の差し替え（高速道路のアスファルト）、groups は使う部品のまとまり。
# walls は側壁の版（both = single・back・center・front。線路の TRACK_PROFILES と同じ決め方）
ROAD_PROFILES = {
    "street": {"sheet": "road", "prefix": "road_", "groups": ("body", "sidewalk", "marking", "weathering"), "skin": {},
               "label": "50", "style": "road"},
    "expressway": {"sheet": "expressway", "prefix": "expwy_", "groups": ("body", "marking", "weathering"),
                   "skin": dict({"asphalt": _M_EXPWY_ASPHALT},
                                **{f"wear{i}": _wear_material("expwy", (0.0027, 0.0027, 0.004), (0.016, 0.016, 0.023), t, 0.0)
                                   for i, (_, t, _) in enumerate(WEAR_LAYERS)},
                                **{n: _slush_material("expwy", (0.0027, 0.0027, 0.004), (0.016, 0.016, 0.023), t, 0.0)
                                   for n, _, t, _, _ in SNOW_LAYERS if t is not None}),
                   "expressway": True, "label": "120", "style": "expressway"},
}
for _variant, _walls in (("single", "both"), ("back", "back"), ("center", "center"), ("front", "front")):
    ROAD_PROFILES[f"expwy_wall_{_variant}"] = dict(ROAD_PROFILES["expressway"], sheet=f"expressway_wall_{_variant}",
                                                   prefix=f"expwy_wall_{_variant}_", walls=_walls, front_row=4,
                                                   groups=ROAD_PROFILES["expressway"]["groups"] + ("wall",))
    # 高架（system_type=1）: 側壁の版に、床の下の基盤（build_base）と橋脚を足す。橋脚は床の下から 1 段下の地面まで（lower 行下まで描く）
    ROAD_PROFILES[f"expwy_elev_{_variant}"] = dict(ROAD_PROFILES[f"expwy_wall_{_variant}"], sheet=f"expressway_elev_{_variant}",
                                                   prefix=f"expwy_elev_{_variant}_", elevated=True, lower=16, band="elevated",
                                                   groups=ROAD_PROFILES[f"expwy_wall_{_variant}"]["groups"] + ("pier",))
# 橋: 両側の壁（欄干）の版に、青い桁（基盤）・端の坂と橋台の躯体・橋脚の絵を足す。セルの並びは線路の橋と同じ
ROAD_PROFILES["expwy_bridge"] = dict(ROAD_PROFILES["expwy_wall_single"], sheet="expressway_bridge", prefix="expwy_bridge_",
                                     bridge=True, solid=True, band="bridge", base_mat=_M_GIRDER, piers=True, starts=True,
                                     groups=ROAD_PROFILES["expwy_wall_single"]["groups"] + ("ramp",),
                                     only=("ns", "ew", "up12", "up9", "up3", "up6", "up2_12", "up2_9", "up2_3", "up2_6"))
# 雪の絵（dat の image[..][1]）: 道路は線路より除雪されている想定で、車道は夏と同じ（路面・白線・走行跡）。
# 雪は路肩（group "snow" の snowbank）と、歩道・縁石だけ（2026-11-15、ゲームで確認して決めた）
ROAD_SNOW_SKIN = {"curb": _SNOW, "paving": _SNOW}
ROAD_SNOW_GROUPS = ("snow",)


def build_road(paths, lines, slope=None, scale=1.0, clip=True, size=TILE + 4, corners=(), half=None, hw=ROAD_HW,
               sidewalk=True, curb_w=CURB_W, half_over=DIAG_OVERFILL, groups=None, skin=None, datums=FLAT, div=1, ends=False,
               wear_paths=None):
    """道路を部品（ROAD_PARTS）の組み立てで作る。paths は車道の中心線（複数で分岐・十字）、lines は (path, u) か (path, u, "dash") の白線。
    corners は歩道の角を丸くするタイルの角、half は斜めのタイルで残す半分を決める経路。
    sidewalk=False（高速道路）は歩道・縁石を作らず、タイル全面をアスファルトにする（groups・skin を渡すとそちらが優先）。
    wear_paths を渡すと、路面の痛み（group "weathering"）を paths ではなくそちらに沿って作る（交差点の右左折、行き止まりの手前で止める跡）"""
    prof = ROAD_PROFILES["street" if sidewalk else "expressway"]
    groups = groups or prof["groups"]
    tile = RoadTile(paths, lines, corners, size if isinstance(size, tuple) else (size, size), hw, curb_w, wear_paths or ())
    # 車線の倍率: 斜め（scale が 1 でない）は直線の 1/√2（タイルの辺で直線の車線と同じ点を通る）
    widths = {"road": scale, "lane": 1.0 if scale == 1.0 else DIAG_EDGE}
    skin = dict(prof["skin"], **(skin or {}))
    main = groups if wear_paths is None else tuple(g for g in groups if g != "weathering")
    obs = assemble(ROAD_PARTS, paths, datums, slope, clip, widths, div, main, ends,
                   skin=skin, tile=tile, half=half, half_over=half_over)
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


def road_sheet(style="street"):
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
    both = lambda p: [(p, -EDGE_LINE), (p, 0.0), (p, EDGE_LINE)]  # 両側の白線と中央線
    # 行き止まり: 車道は奥の歩道の手前（両脇の歩道と同じ幅を残す）まで
    end = lambda d: [-Vector(d).normalized() * ROAD_HW, Vector(d) * 1.12]
    sides = lambda p: [(p, -EDGE_LINE), (p, EDGE_LINE)]
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
        cross = [(we, 0.0), dash(we, -EDGE_LINE), dash(we, EDGE_LINE)]
        jobs.update({
            (0, 5): ("s", [sn], both(sn), None),
            (0, 6): ("w", [we], both(we), None),
            (0, 7): ("n", [sn], both(sn), None),
            (0, 8): ("e", [we], both(we), None),
            (0, 9): ("single", [sn, we], cross, None),
            (3, 5): ("nse", [sn], [(sn, 0.0), (sn, -EDGE_LINE), dash(sn, EDGE_LINE)], None),
            (3, 6): ("new", [we], [(we, 0.0), (we, EDGE_LINE), dash(we, -EDGE_LINE)], None),
            (3, 7): ("nsw", [sn], [(sn, 0.0), (sn, EDGE_LINE), dash(sn, -EDGE_LINE)], None),
            (3, 8): ("sew", [we], [(we, 0.0), (we, -EDGE_LINE), dash(we, EDGE_LINE)], None),
            (3, 9): ("nsew", [sn, we], cross, None),
        })
        for pos in ((2, 5), (2, 6), (2, 7), (2, 8)):
            del jobs[pos]
    walls = prof.get("walls")
    if walls:
        # 側壁の版: 分岐は枝の経路も通す（壁を枝の口で開ける。白線はそのまま）。行き止まりは、閉じた側の辺の手前に端の壁を立てる
        # （経路の始点を壁の内側に置く。端の壁は経路の始点の奥に立つ）
        jobs.update({
            (3, 5): ("nse", [sn, straight(O, E)], jobs[(3, 5)][2], None),
            (3, 6): ("new", [we, straight(O, N)], jobs[(3, 6)][2], None),
            (3, 7): ("nsw", [sn, straight(O, W)], jobs[(3, 7)][2], None),
            (3, 8): ("sew", [we, straight(O, S)], jobs[(3, 8)][2], None),
        })
        for pos, name, closed, open_ in (((0, 5), "s", N, S), ((0, 6), "w", E, W), ((0, 7), "n", S, N), ((0, 8), "e", W, E)):
            d = Vector(open_).normalized()
            jobs[pos] = (name, [[Vector(closed).normalized() * EXPWY_WALL_U, Vector(open_) + d * PATH_EXT]],
                         both(sn if name in "ns" else we), None)
    # 斜めの経路はタイルの外まで十分に延ばす。45° の向きでは型の端の角が内側に入り込み、
    # 延長が短い（2.5）とタイルの端の近くで縁石が削り残されて、つなぎ目に切り欠きが出た
    diag = {
        (2, 0): ("diag_sw", straight(S, W, ext=DIAG_EXT)),
        (2, 1): ("diag_nw", straight(N, W, ext=DIAG_EXT)),
        (2, 2): ("diag_ne", straight(N, E, ext=DIAG_EXT)),
        (2, 3): ("diag_se", straight(S, E, ext=DIAG_EXT)),
    }
    if "only" in prof:
        jobs = {k_: v for k_, v in jobs.items() if v[0] in prof["only"]}
        diag = {}
    # 走行跡の経路: 分岐・十字は直進に右左折のカーブを足す。行き止まりは中ほどから開いた側へ（閉じた側の手前で止める。WearPath.fade）
    wear = {"nse": [sn, arc_ne, arc_se], "new": [we, arc_nw, arc_ne], "nsw": [sn, arc_nw, arc_sw], "sew": [we, arc_sw, arc_se],
            "nsew": [sn, we, arc_sw, arc_nw, arc_ne, arc_se]}
    for d_name, open_ in (("s", S), ("w", W), ("n", N), ("e", E)):
        dv = Vector(open_).normalized()
        wp = WearPath([-dv * 1.0, Vector(open_) + dv * PATH_EXT])
        wp.fade = True
        wear[d_name] = [wp]
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
    k = DIAG_EDGE / ROAD_DIAG  # 経路からの距離の倍率（scale=ROAD_DIAG を掛けると直線の 1/√2）

    def shoot(pos, row0, cname, name, paths, slope, obs, side=None):
        """組み立てた 1 タイルを描いてシートのセルに置く。側壁の版は、残す壁を選び、壁を別の層（奥の絵・手前の絵）で描く。"""
        if walls:
            kl = DIAG_EDGE if name.startswith("diag_") else 1.0
            kept = select_walls(obs, name, paths, walls)
            trim_end_walls(kept, paths, kl, None, EXPWY_WALL_U, EXPWY_WALL_W)
            # 路面・白線・走行跡・路肩の雪も、残した壁の外側を削る（基盤と同じ型）。斜めでは壁が経路から約 3.2 にあり、
            # タイルの角（3.54）までの路面が壁の外へはみ出して見えた（2026-11-15、ゲームで確認）
            beyond = _beyond_prisms(kept, paths, kl, EXPWY_WALL_U, EXPWY_WALL_W)
            if beyond:
                cutter = mesh_object("roadcut", *merge(beyond), material(*_M_BASE))
                recalc_normals(cutter)
                for ob in [ob for ob in obs if not ob.get("tall") and not ob.get("pname", "").startswith("pier")]:
                    boolean(ob, cutter)
                    if not ob.data.polygons:
                        obs.remove(ob)
                        bpy.data.objects.remove(ob, do_unlink=True)
                bpy.data.objects.remove(cutter, do_unlink=True)
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
                    v.co.z -= 0.05
                obs.append(base)
                if name in grounds:
                    obs.append(build_start_body(paths[0], grounds[name], FLAT["bed"], _M_BASE, u=EXPWY_WALL_U + EXPWY_WALL_W))
                    slope = grounds[name]  # 持ち分を、坂の地面まで下へ広げる
        lower, solid = prof.get("lower", 0), prof.get("solid", False)
        if any(ob.get("tall") for ob in obs):
            cells[(pos[0] + row0, pos[1])], front = render_layers(cname, obs, True, exits_of(name), slope, ROAD_CY, 0,
                                                                  WALL_RISE, solid, lower, side=side)
            if front:
                cells[(pos[0] + row0 + prof["front_row"], pos[1])] = front
        else:
            cells[(pos[0] + row0, pos[1])] = render_cell(cname, exits_of(name), slope=slope, side=side, cy=ROAD_CY, solid=solid,
                                                         lower=lower)

    for row0, suffix, skin, grp in variants:
        kw = dict(sidewalk=not expwy, groups=grp, skin=skin)
        cn = lambda name: prefix + suffix.lstrip("_") + ("_" if suffix else "") + name
        for pos, (name, paths, lines, slope, *rest) in jobs.items():
            clear_models()
            obs = build_road(paths, lines, slope, corners=rest[0] if rest else (), ends=name in ("s", "w", "n", "e"),
                             wear_paths=wear.get(name), **kw)
            shoot(pos, row0, cn(name), name, paths, slope, obs)

        def build_diag(name, path, over=DIAG_OVERFILL):
            # 画面で横向きになる斜め（se・nw）は、中央線がちょうど画素の行の境に乗り、2行に分かれて灰色に見える。
            # 半画素ずらして1行に収める（どちらも南東の側へ。sweep の +u は se で南東、nw で北西）
            c = {"diag_se": DIAG_CENTER_SHIFT, "diag_nw": -DIAG_CENTER_SHIFT}.get(name, 0.0) / ROAD_DIAG
            e = EDGE_LINE * k
            if name in ("diag_se", "diag_nw"):
                # 路側の白線も、経路（画素の行の境）からの距離を「整数 + 0.5」px に丸めて1行に収める（約 0.3px 内へ）。
                # 縦向きの斜め（sw・ne）はそのままで列に収まる。両方を同時に収める EDGE_LINE は無い
                e = (math.floor(EDGE_LINE * DIAG_EDGE * DIAG_PX) + 0.5) / DIAG_PX / ROAD_DIAG
            return build_road([path], [(path, -e), (path, c), (path, e)], scale=ROAD_DIAG,
                              half=path, hw=ROAD_HW * k, curb_w=CURB_W * DIAG_EDGE, half_over=over, **kw)

        for pos, (name, path) in diag.items():
            clear_models()
            obs = build_diag(name, path)
            shoot(pos, row0, cn(name), name, [path], None, obs, side=DIAG_HALF[name])
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
        set_anchor(128)
        for col, (sx, sy) in enumerate(((2 * EXPWY_WALL_U, PIER_W), (PIER_W, 2 * EXPWY_WALL_U))):
            clear_models()
            mesh_object("pier", *box(0, 0, H / 2, sx, sy, H), material(*_M_BASE))
            cells[(2, col)] = render_cell(f"{prof['sheet']}_pier{col}")
        set_anchor(ROAD_CY)

    # アイコン: 道路を大きく斜めに通し、左上に最高速度を書く
    clear_models()
    long = straight((0, -12), (0, 12), ext=0.6)
    build_road([long], both(long), clip=False, size=(TILE, 26), sidewalk=not expwy, groups=groups)
    # 線路のシリーズと同じ型: 背景の色（道路・高速道路）、左上の最高速度、右下の印（側壁の版 S・B・C・F）、下の帯（高架・橋）
    badge = ICON_BADGE[walls] if walls and not prof.get("bridge") else None
    cells[(0, 0)] = render_icon(prefix + "icon", 0.5, shift=(-0.14, 0.2), label=prof["label"], style=prof["style"], badge=badge,
                                band=prof.get("band"))
    # カーソル: 南北の直線の絵（壁は版のとおり）の上に、アイコンと同じ色の札と最高速度
    clear_models()
    obs = build_road([sn], both(sn), sidewalk=not expwy, groups=groups)
    if walls:
        select_walls(obs, "ns", [sn], walls)
    cells[(0, 1)] = render_cursor(prefix + "cursor", prof["label"], prof["style"])
    make_sheet(cells, 2 * block, 10, os.path.join(SRC, prof["sheet"] + ".png"))


def build_tollbooth(rot_deg):
    """料金所風の建物。屋根は 13x6.5 でタイル(10x10)からはみ出す。"""
    m_conc = material("concrete", (0.66, 0.65, 0.62))
    m_white = material("booth", (0.86, 0.87, 0.88), rough=0.5)
    # 特殊色: 屋根の帯はプレーヤーカラー、窓は夜に光る窓、屋根の下に照明、ブースの上に赤と緑のランプ
    m_glass = material("glass", (0.25, 0.38, 0.48), rough=0.15, special="window_dark")
    m_roof = material("roof", (0.80, 0.81, 0.83), rough=0.6)
    m_band = material("band", (0.35, 0.35, 0.35), special="player1")
    m_road = material("asphalt", (0.28, 0.28, 0.30))
    m_lamp = material("lamp", (1.0, 1.0, 0.6), emit=1.0, special="light_yellow")
    m_red = material("lamp_red", (1.0, 0.1, 0.1), emit=1.0, special="light_red")
    m_green = material("lamp_green", (0.0, 0.8, 0.0), emit=1.0, special="light_green")

    parts = {
        "road": (m_road, [box(0, 0, 0.05, 10, 10, 0.1)]),
        "island": (m_conc, [box(0, 0, 0.3, 1.4, 8.0, 0.5)]),
        "booth": (m_white, [box(0, 0.6, 1.8, 1.1, 2.2, 2.5)]),
        "glass": (m_glass, [box(0, 0.6, 2.2, 1.16, 1.6, 1.0)]),
        "pillars": (m_white, [box(0, -2.4, 3.0, 0.5, 0.5, 5.0), box(0, 3.4, 3.0, 0.5, 0.5, 5.0)]),
        "roof": (m_roof, [box(0, 0.5, 5.75, 13.0, 6.5, 0.7)]),
        "band": (m_band, [box(0, 0.5, 5.75, 13.06, 6.56, 0.28)]),
        # 安全島の両端に照明灯（柱と光る頭）
        "lamp_posts": (m_white, [box(0, y, 1.2, 0.15, 0.15, 1.8) for y in (-3.7, 3.7)]),
        "lamps": (m_lamp, [box(0, y, 2.25, 0.4, 0.4, 0.3) for y in (-3.7, 3.7)]),
        # 左の車線は赤（閉鎖）、右の車線は緑（開放）。ブース上の柱の両脇に向ける
        "lamp_red": (m_red, [box(-0.6, -2.4, 4.6, 0.2, 0.5, 0.5)]),
        "lamp_green": (m_green, [box(0.6, -2.4, 4.6, 0.2, 0.5, 0.5)]),
    }
    obs = [mesh_object(name, *merge(geo), mat) for name, (mat, geo) in parts.items()]
    for ob in obs:
        ob.rotation_euler.z = math.radians(rot_deg)
    return obs


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


def render_layers(name, obs, split, exits, slope, cy, spill, rise, solid=False, lower=0, side=None):
    """高さのある部品（tall）を別の層として描いて重ねる。返すのは（奥の絵のパス, 手前の絵のパス または None）。
    - 本体: 持ち分（地面の範囲）で切る
    - 高さのある部品: 持ち分を上へ rise 行広げた範囲で切る（奥のタイルの絵の上に出る。建物と同じ）
    - split なら、カメラに近い側の部品は手前の絵（dat の frontimage。車両の上に描かれる）に分ける
    side は本体の持ち分を菱形の半分にする（道路の斜め。_ground_mask）。高さのある部品の持ち分は菱形全体のまま（形のほうで帯に切ってある）"""
    tall = [ob for ob in obs if ob.get("tall")]
    body = [ob for ob in obs if not ob.get("tall")]
    for ob in tall:
        ob.hide_render = True
    img = load_rgba8(render_cell(name, exits, slope=slope, side=side, cy=cy, spill=spill, solid=solid, lower=lower)).copy()
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
    front = near_camera(obs) if split else []

    def layer(objs, suffix):
        for ob in tall:
            ob.hide_render = ob not in objs
        im = load_rgba8(render_cell(name + suffix)).copy()
        # 輪郭の半透明の画素は捨てる（色が暗く出て、壁の上の縁とタイルの境に黒い点線が見えた）
        im[..., 3] = np.where(m & (im[..., 3] >= 250), 255, 0)
        return im

    back = layer([ob for ob in tall if ob not in front], "_tallb")
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


# ---------------------------------------------------------------- 各アドオン

# 線路の描画位置。形状は同じで、画面上の上下位置だけを整数 px ずらす（正: 下へ）
#   new: 新描画位置（レールが低い。今の pak128・iss）
#   old: 旧描画位置（レールが高い。古い pak128・SIS）
# iss と SIS を比べると、どの方位でもレールが画面上で 4〜4.5px 違うだけだった
TRACK_PROFILES = {
    "new": {"sheet": "track", "spill": 1, "datums": {"bed": Datum(2, 1), "rail": Datum(4, 1)}, "snow": True},
    "old": {"sheet": "track_old", "spill": 0, "datums": FLAT, "snow": True},
    # 試作: 新に、車止め・さび色・雪の絵を足したもの（本体のシートの検証を崩さないよう、別のアドオンにする）
    "trial": {"sheet": "track_trial", "spill": 1, "datums": {"bed": Datum(2, 1), "rail": Datum(4, 1)},
              "groups": ("body", "structure", "weathering"), "snow": True},
    # 試作: 新に側壁を足したもの。カメラに近い側の壁は手前の絵（frontimage。下の 4 行に同じ並び）
    # 試作: 橋（obj=bridge）。直線と坂（橋の端）だけを描き、床版・側壁（欄干）を足す。橋脚は別のセル
    "bridge": {"sheet": "track_bridge", "spill": 1, "datums": {"bed": Datum(2, 1), "rail": Datum(4, 1)},
               "groups": ("body", "wall", "base", "ramp"), "front_row": 4, "snow": True, "solid": True, "band": "bridge",
               "only": ("ns", "ew", "up12", "up9", "up3", "up6", "up2_12", "up2_9", "up2_3", "up2_6"), "piers": True,
               "starts": True},
    "wall_single": {"sheet": "track_wall_single", "spill": 1, "datums": {"bed": Datum(2, 1), "rail": Datum(4, 1)},
                    "groups": ("body", "wall", "base", "structure"), "front_row": 4, "snow": True, "walls": "both"},
}
# 側壁と基盤のバリエーション: 両側（単線用）・back（奥だけ）・center（壁なし。中線）・front（手前だけ）。
# 基盤は、壁のある側は壁まで、壁のない側はタイルの端まで
for _variant in ("back", "center", "front"):
    TRACK_PROFILES[f"wall_{_variant}"] = dict(TRACK_PROFILES["wall_single"], sheet=f"track_wall_{_variant}", walls=_variant)
# 高架（dat の system_type=1）: 側壁の 4 つの版に橋脚を足し、持ち分を床の 1 段（16px）下まで広げる
for _variant, _walls in (("single", "both"), ("back", "back"), ("center", "center"), ("front", "front")):
    TRACK_PROFILES[f"elev_{_variant}"] = dict(TRACK_PROFILES["wall_single"], sheet=f"track_elev_{_variant}", walls=_walls,
                                               groups=("body", "wall", "base", "structure", "pier"), lower=16,
                                               band="elevated")
# 試作: ex 画像（Y字・三方分岐）が使えたらどう見えるかを、switch 画像の 1・2 の枠に入れて見る（別のアドオン。雪なし）
TRACK_PROFILES["ex_proto"] = dict(TRACK_PROFILES["new"], sheet="track_ex_proto", ex_proto=True, snow=False)
TRACK_PROFILES["ex_proto2"] = dict(TRACK_PROFILES["ex_proto"], sheet="track_ex_proto2", ex_proto="crossover")
ICON_BADGE = {"both": "S", "back": "B", "center": "C", "front": "F"}  # アイコンの右下の印（single / back / center / front）
WALL_RISE = 11  # 側壁の高さ（画面の px。持ち分を上へ広げる行数）
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


def select_walls(obs, name, paths, side, wall_names=None):
    """側壁のバリエーション（複線以上を並べて作るとき用）: back はカメラから遠い側の壁だけ、front は近い側の壁だけ、center は無し。
    残さない壁は消して obs から外し、残した壁（高さのある部品）を返す。行き止まりの端の壁は、壁のある版ならいつも残す。
    手前/奥を分ける向き: T字は、まっすぐ通る道（東西か南北）に対して手前か奥かで決める（分岐の向きで壁が変わる）。
    南北の道は東が手前、東西の道は南が手前。それ以外はカメラの向き（NEAR_AXIS）"""
    axis = {"nse": Vector((1, 0, 0)), "nsw": Vector((1, 0, 0)),
            "new": Vector((0, -1, 0)), "sew": Vector((0, -1, 0))}.get(_junction(name), NEAR_AXIS)
    origin = Vector((0, 0, 0)) if len(paths) > 1 else None
    near = near_camera(obs, axis, origin=origin)
    keep = {"both": lambda ob: True, "center": lambda ob: False,
            "front": lambda ob: ob in near, "back": lambda ob: ob not in near}[side]
    walls = [ob for ob in obs if ob.get("tall")]
    kept = [ob for ob in walls if ob.name.startswith("endw") or keep(ob)]
    for ob in [ob for ob in walls if ob not in kept]:
        obs.remove(ob)
        bpy.data.objects.remove(ob, do_unlink=True)
    return kept


def trim_end_walls(kept, paths, k, move, wu=None, ww=None):
    """行き止まりの端の壁から、残した側壁の外側を削る（側壁のある側は側壁で止まる）。move は路盤の基準面の動き。"""
    end_walls = [ob for ob in kept if ob.name.startswith("endw")]
    sides = _beyond_prisms([ob for ob in kept if not ob.name.startswith("endw")], paths, k, wu, ww)
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
    # dat オフセット -64,-32 と対応。持ち分は地面の菱形のまま（新描画位置は絵が 4px 下だが、持ち分を 4 行下げると、
    # 手前のタイルへはみ出した 2〜4 行目を手前の地面が消し、どのつなぎ目にも草の線が出た）
    cy = GROUND_CY
    set_anchor(128 + BALLAST_DY)
    cells = {}
    parts = TRACK_PARTS + TRACK_EXTRAS
    if "only" in prof:
        jobs = {k: v for k, v in jobs.items() if v[0] in prof["only"]}
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
    # 雪の絵は下の 4 行に同じ並びで置く（dat の image[..][1]）。汚れは雪に隠れるので入れない
    # 行の並び: 奥の絵 4 行 →（手前の絵 4 行）→ 雪の奥の絵 4 行 →（雪の手前の絵 4 行）
    block = 8 if "front_row" in prof else 4
    variants = [(0, "", None, groups)]
    if prof.get("snow"):
        variants.append((block, "_snow", SNOW_SKIN, tuple(g for g in groups if g != "weathering")))
    for row0, suffix, skin, grp in variants:
        for pos, (name, paths, slope, *rails) in jobs.items():
            clear_models()
            # 画面で横向きの斜め（nw・se）は下げ幅を半分にする（datum_move の div）。斜めは横幅も細くする
            div = 2 if name in ("diag_nw", "diag_se", "close1") else 1
            widths = {"gauge": DIAG_RAIL, "bed": DIAG_BALLAST} if name.startswith(("diag_", "close")) else None
            kw = dict(widths=widths, div=div, groups=grp, ends=name in ("s", "w", "n", "e"), skin=skin)
            if rails:
                # 分岐の絵: 走行面（rail の基準面の部品）だけを分岐の経路で作る
                obs = (assemble([p for p in parts if p.datum != "rail"], paths, prof["datums"], slope, **kw)
                       + assemble([p for p in parts if p.datum == "rail"], rails[0], prof["datums"], slope, **kw))
            else:
                obs = assemble(parts, paths, prof["datums"], slope, **kw)
            side = prof.get("walls", "both")
            kept = select_walls(obs, name, paths, side)
            if side in ("back", "center") and name.startswith("diag_"):
                # back・center の斜めは橋脚を描かない。手前にいつも front の線があり、その橋脚で足りる。
                # 描くと、画面で横向きの斜めでは柱の上が手前の線の床に重なって暗い点線に見えた
                for ob in [ob for ob in obs if ob.name.startswith("pier")]:
                    obs.remove(ob)
                    bpy.data.objects.remove(ob, do_unlink=True)
            mask_slope = slope
            kb = (widths or {}).get("bed", 1.0)
            trim_end_walls(kept, paths, kb, datum_move(prof["datums"]["bed"], slope, div))
            if "base" in grp:
                bmat = (skin or {}).get("base", _M_BASE)
                if name == "single":
                    # 1 タイルだけの軌道: 線路も壁も置かず、タイル全面の基盤だけにする（高架のすき間を埋める景観用）
                    for ob in obs:
                        bpy.data.objects.remove(ob, do_unlink=True)
                    obs = [build_base([], paths, kb, prof["datums"]["bed"], slope, div, bmat)]
                else:
                    open_cut = _diag_open_cut(kept, paths[0]) if name.startswith("diag_") else None
                    obs.append(build_base(kept, paths, kb, prof["datums"]["bed"], slope, div, bmat, extra_cut=open_cut))
                if name in grounds:
                    obs.append(build_start_body(paths[0], grounds[name], prof["datums"]["bed"], _M_BASE))
                    mask_slope = grounds[name]  # 持ち分を、坂の地面まで下へ広げる
            cname = f"{prof['sheet']}{suffix}_{name}"
            if any(ob.get("tall") for ob in obs):
                cells[(pos[0] + row0, pos[1])], front = render_layers(cname, obs, True, exits_of(name), mask_slope, cy,
                                                                      prof["spill"], WALL_RISE, prof.get("solid", False),
                                                                      prof.get("lower", 0))
                if front:
                    cells[(pos[0] + row0 + prof["front_row"], pos[1])] = front
            else:
                cells[(pos[0] + row0, pos[1])] = render_cell(cname, exits_of(name), slope=mask_slope, cy=cy, spill=prof["spill"],
                                                             solid=prof.get("solid", False), lower=prof.get("lower", 0))

    if prof.get("piers"):
        # 橋脚: 橋の下の地面のタイルに立つ柱（高さ 1 段）。線路の向きに直角に長い。(2, 0) が南北の橋、(2, 1) が東西の橋
        set_anchor(128)
        for col, (sx, sy) in enumerate(((PIER_L, PIER_W), (PIER_W, PIER_L))):
            clear_models()
            mesh_object("pier", *box(0, 0, H / 2, sx, sy, H), material(*_M_WALL))
            cells[(2, col)] = render_cell(f"{prof['sheet']}_pier{col}")
        set_anchor(128 + BALLAST_DY)

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
    assemble(TRACK_PARTS, [straight((0, -12), (0, 12), ext=0.6)], clip=False)
    if profile == "trial":
        cells[(0, 0)] = render_icon("track_trial_icon", 0.5, shift=(-0.14, 0.2), label="100", style="track", badge="T")
        # カーソル: 直線の絵の上に、最高速度を書く（アイコンと同じ色の札）
        clear_models()
        assemble(parts, [straight(S, N)], prof["datums"], groups=groups)
        cells[(0, 1)] = render_cursor("track_trial_cursor", "100", "track")
    elif "walls" in prof or "band" in prof:
        # 側壁のバリエーションは右下の印（S・B・C・F）、橋は下の帯で区別する
        cells[(0, 0)] = render_icon(prof["sheet"] + "_icon", 0.5, shift=(-0.14, 0.2), label="100", style="track",
                                    badge=ICON_BADGE.get(prof.get("walls")), band=prof.get("band"))
        cells[(0, 1)] = cells[(0, 2)]
    else:
        cells[(0, 0)] = render_icon("track_icon", 0.5, shift=(-0.14, 0.2), label="100")
        cells[(0, 1)] = cells[(0, 2)]  # カーソルは ns と同じ絵

    rows = block * (2 if prof.get("snow") else 1)
    make_sheet(cells, rows, 15 if any(c >= 10 for _, c in cells) else 10, os.path.join(SRC, prof["sheet"] + ".png"))


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


def save_rgba(path, rgba):
    h, w, _ = rgba.shape
    img = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    img.pixels.foreach_set((np.flipud(rgba).astype(np.float32) / 255).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


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


def tunnel_sheet(kind="track"):
    """坑口 4 方向（kind: track・expressway）。pak128 では坑口は 2 段の坂にしか置けない（本体の tunnelbauer）。BackImage[N] は北が高い坂（南から入る）。シートは 行 0: 奥の絵、行 1: 手前の絵、行 2・3: 雪。"""
    half = TILE / 2
    N, S, E, W = (0, half), (0, -half), (half, 0), (-half, 0)
    dirs = {  # 名前: (列, 経路, 高い側の向き, 坂の高さ)
        "n": (2, straight(S, N), Vector((0, 1)), lambda x, y: 2 * H * (y + half) / TILE),
        "s": (3, straight(S, N), Vector((0, -1)), lambda x, y: 2 * H * (half - y) / TILE),
        "e": (4, straight(W, E), Vector((1, 0)), lambda x, y: 2 * H * (x + half) / TILE),
        "w": (5, straight(W, E), Vector((-1, 0)), lambda x, y: 2 * H * (half - x) / TILE),
    }
    prof = TRACK_PROFILES["new"]
    expwy = kind == "expressway"
    # 高速道路: iss の都市高速の坑口（tunnel/road。タイルいっぱいの箱と口の上の名板）が手本。穴は両側の壁の内側まで広げる。
    # 道路は地面の菱形より 1px 下に描く（ROAD_CY）。持ち分も同じだけ下げ、隣の道路と同じく spill は 0
    bore_w = EXPWY_WALL_U - 0.1 if expwy else TUNNEL_BORE[0]
    cy, spill = (ROAD_CY, 0) if expwy else (GROUND_CY, prof["spill"])
    pre = "expwy_tunnel" if expwy else "tunnel"
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
                grp = ROAD_PROFILES["expressway"]["groups"]
                build_road([path], [(path, -EDGE_LINE), (path, 0.0), (path, EDGE_LINE)], sidewalk=False, skin=skin,
                           groups=grp + ROAD_SNOW_GROUPS if skin else grp)
            else:
                assemble(TRACK_PARTS, [path], prof["datums"], skin=skin)
                # 穴の内側: 床（基盤と同じ材質）と暗い左右の壁だけを置く（線路は床の上に見える。箱で埋めると線路まで隠れた）
                # 床はタイルの幅いっぱい（躯体の下は隠れる。口の辺では、隣の側壁つきの線路の基盤と 1 行重なってすき間を埋める）
                floor = mesh_object("floor", *box(c.x, c.y, 0.005, a1 - a0, TILE, 0.01, rot=rot),
                                    material(*(skin or {}).get("base", _M_BASE)))
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
        build_road([long], [(long, -EDGE_LINE), (long, 0.0), (long, EDGE_LINE)], clip=False, size=(TILE, 26), sidewalk=False)
        cells[(0, 0)] = render_icon("expwy_tunnel_icon", 0.5, shift=(-0.14, 0.2), label="120", style="expressway", band="tunnel")
    else:
        assemble(TRACK_PARTS, [long], clip=False)
        cells[(0, 0)] = render_icon("track_tunnel_icon", 0.5, shift=(-0.14, 0.2), label="100", style="track", band="tunnel")
    # カーソル: 口が手前を向いた坑口（BackImage[N]）の奥の絵に手前の絵（躯体）を重ねた 1 枚
    back, front = load_rgba8(cells[(0, 2)]), load_rgba8(cells[(1, 2)])
    cursor = np.where(front[..., 3:] >= 128, front, back)
    if expwy:
        # 道路のシリーズは、カーソルにアイコンと同じ色の札と最高速度を足す
        cells[(0, 1)] = render_cursor(f"{pre}_cursor", "120", "expressway", base=cursor)
    else:
        cells[(0, 1)] = os.path.join(WORK, f"{pre}_cursor.png")
        save_rgba(cells[(0, 1)], cursor)
    make_sheet(cells, 4, 6, os.path.join(SRC, ("expressway" if expwy else "track") + "_tunnel.png"))


def tollbooth_sheet():
    set_anchor(192)  # dat オフセット -64,-96 と対応（上に160px の余白）
    cells = {}
    for i, rot in enumerate((0, 90, 180, 270)):
        clear_models()
        build_tollbooth(rot)
        cells[(0, i)] = render_cell(f"tollbooth_r{i}")
    clear_models()
    build_tollbooth(0)
    cells[(0, 4)] = render_icon("tollbooth_icon", 1.25, shift=(0.0, 0.2))
    cells[(0, 5)] = cells[(0, 0)]  # カーソルは向き0と同じ絵
    make_sheet(cells, 1, 6, os.path.join(SRC, "tollbooth.png"))


if __name__ == "__main__":
    if DEBUG:
        import shutil
        dbg = os.path.join(WORK, "debug")
        os.makedirs(dbg, exist_ok=True)
        for f in os.listdir(SRC):
            if f.endswith(".dat"):
                shutil.copy(os.path.join(SRC, f), dbg)
        SRC = dbg
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(SRC, exist_ok=True)
    setup_scene()
    print(f"[info] ortho={ORTHO:.4f} px/unit={PX_PER_UNIT:.4f} height_step={H:.4f}")
    targets = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["track", "track_old", "road", "expressway", "tollbooth"]
    known = {"track", "track_old", "track_trial", "track_ex_proto", "track_ex_proto2", "track_bridge", "track_tunnel",
             "icons", "road", "expressway", "tollbooth"}
    known |= {f"track_{w}_{v}" for w in ("wall", "elev") for v in ("single", "back", "center", "front")}
    known |= {f"expressway_{w}_{v}" for w in ("wall", "elev") for v in ("single", "back", "center", "front")}
    known |= {"expressway_bridge", "expressway_tunnel"}
    unknown = [t for t in targets if t not in known]
    if unknown:
        # 名前の打ち間違いで何も描かずに正常終了しないように止める（render_parallel.py が失敗として拾う）
        raise SystemExit(f"[render] unknown target: {' '.join(unknown)}")
    if "track" in targets:
        track_sheet("new")
    if "track_old" in targets:
        track_sheet("old")
    if "track_trial" in targets:
        track_sheet("trial")
    if "track_ex_proto" in targets:
        track_sheet("ex_proto")
    if "track_ex_proto2" in targets:
        track_sheet("ex_proto2")
    if "track_bridge" in targets:
        track_sheet("bridge")
    for _variant in ("single", "back", "center", "front"):
        if f"track_wall_{_variant}" in targets:
            track_sheet(f"wall_{_variant}")
        if f"track_elev_{_variant}" in targets:
            track_sheet(f"elev_{_variant}")
    if "track_tunnel" in targets:
        tunnel_sheet()
    if "icons" in targets:
        icon_gallery()
    if "road" in targets:
        road_sheet()
    if "expressway" in targets:
        road_sheet("expressway")
    for _variant in ("single", "back", "center", "front"):
        if f"expressway_wall_{_variant}" in targets:
            road_sheet(f"expwy_wall_{_variant}")
        if f"expressway_elev_{_variant}" in targets:
            road_sheet(f"expwy_elev_{_variant}")
    if "expressway_bridge" in targets:
        road_sheet("expwy_bridge")
    if "expressway_tunnel" in targets:
        tunnel_sheet("expressway")
    if "tollbooth" in targets:
        tollbooth_sheet()
