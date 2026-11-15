"""設定値・シーン・材質・形の部品（箱・掃引・経路）・基準面と部品の型・形を切る/傾ける操作（共通の描画の道具 sheetlib の一部。tools/README.md）。"""
from dataclasses import dataclass
from typing import Callable
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

import sheet_settings
from .layout_colors import layout_rgb


ROOT = os.getcwd()  # アドオンのディレクトリ（入口はそこで動かす）

WORK = os.path.join(ROOT, "work")

SRC = os.path.join(ROOT, "src")


# アドオンが入口で登録するシートの設定（アドオンごとの値。tools/README.md）。キーは対象のシート名ではなく、描き分けの名前。
# 共通の描画が名前で引くもの: TRACK_PROFILES["new"]（トンネルの描画）、ROAD_PROFILES["street"]・["expressway"]（道路の部品の選択）
TRACK_PROFILES = {}

ROAD_PROFILES = {}


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


# 実行のモード（sheet_settings.py。環境変数で決まる）
LAYOUT = sheet_settings.LAYOUT
ONLY = sheet_settings.ONLY


def material(name, rgb, rough=0.8, metal=0.0, emit=0.0, special=None):
    """special に SPECIAL の名前を渡すと、その材質が見えている画素を特殊色にする（render_cell と make_sheet で処理）。
    プレーヤーカラーは光の当たり方で8段階のどれかを選ぶので、rgb は灰色にしておくと明暗がそのまま段階になる。"""
    if LAYOUT:
        return layout_material(name)
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
    centre: bool = True     # 手前/奥を決める重心（near_camera）に数えるか


def layout_material(name):
    """レイアウト検証用モードの材質: name の色で、光の当たり方に関わらず一様に光る（影・明暗で部品の境が消えない）。"""
    mname = "layout_" + name
    if mname in bpy.data.materials:
        return bpy.data.materials[mname]
    m = bpy.data.materials.new(mname)
    m.use_nodes = True
    rgb = layout_rgb(name)
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    return m


def make_material(spec, part=None):
    """部品の材質: material() の引数の組か、材質を返す関数（まだらの材質など）。
    レイアウト検証用モードでは、部品の名前（part。無ければ材質の名前）で色を決める。"""
    if LAYOUT:
        return layout_material(part if part is not None else (spec[0] if not callable(spec) else "unnamed"))
    return spec() if callable(spec) else material(*spec)

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
    # Part.centre が偽の部品（線路の汚れ）は数えない。頂点が多く、重心がずれて手前/奥の判定が変わった（カーブの壁の版が入れ替わった）
    ref = _centre([ob for ob in obs if not ob.get("tall") and ob.get("centre", True)]) if origin is None else origin
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
