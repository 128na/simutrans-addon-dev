"""Blender から Simutrans 用のタイル画像シートを作る検証スクリプト。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/render.py

出力:
    src/track.png      線路（道床に厚みあり）。セル配置は iss の線路と同じ
    src/tollbooth.png  料金所風の建物（屋根がタイルからはみ出す）
    work/              セルごとの生の描画結果（確認用）
"""
import math
import os
import sys

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
SPECIAL_COLORS = {
    (107, 107, 107), (155, 155, 155), (179, 179, 179), (201, 201, 201),
    (223, 223, 223), (87, 101, 111), (127, 155, 241), (255, 255, 83),
    (255, 33, 29), (1, 221, 1), (227, 227, 255), (193, 177, 209),
    (77, 77, 77), (255, 1, 127), (1, 1, 255), (36, 75, 103), (57, 94, 124),
    (76, 113, 145), (96, 132, 167), (116, 151, 189), (136, 171, 211),
    (156, 190, 233), (176, 210, 255), (123, 88, 3), (142, 111, 4),
    (161, 134, 5), (180, 157, 7), (198, 180, 8), (217, 203, 10),
    (236, 226, 11), (255, 249, 13),
}


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


def material(name, rgb, rough=0.8, metal=0.0):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
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
        if ob.type == "MESH" and ob.name != "clip":
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


def straight(a, b, ext=0.6):
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    return [a - d * ext, b + d * ext]


def arc(center, start_deg, end_deg, radius=TILE / 2, n=24, ext=0.6):
    c = Vector(center)
    pts = []
    for i in range(n + 1):
        t = math.radians(start_deg + (end_deg - start_deg) * i / n)
        pts.append(c + Vector((math.cos(t), math.sin(t))) * radius)
    d0 = (pts[0] - pts[1]).normalized()
    d1 = (pts[-1] - pts[-2]).normalized()
    return [pts[0] + d0 * ext] + pts + [pts[-1] + d1 * ext]


# pak128 標準に合わせて低くする: 道床の厚み0.12（画面で約1px）、レール上面0.30（約2px）
BALLAST_H = 0.12
BALLAST = [(-1.9, 0.0), (1.9, 0.0), (1.55, BALLAST_H), (-1.55, BALLAST_H)]
SLEEPER_Z, SLEEPER_H, SLEEPER_LEN = 0.15, 0.08, 2.0
# レールの間隔は iss・SIS に合わせて画面上 6px（直線で 1単位 ≈ 6.4px）
RAIL_IN, RAIL_OUT, RAIL_Z0, RAIL_Z1 = 0.417, 0.517, 0.19, 0.30

# 斜めのタイルの横幅の倍率。3D のまま描くと、斜めは横幅が縮まずに映って直線の約1.6倍太く見える。
# 画面上で直線と同じ太さに見える比率 2/√10 にする（pak128 標準も斜めはレール間隔を細く描く）
DIAG_RAIL = 2 / math.sqrt(10)
DIAG_BALLAST = 0.8


def build_track(paths, slope=None, clip=True, rail_scale=1.0, ballast_scale=1.0):
    """paths の線路を作り、タイルの外を切り落とし、slope(x,y)->z で傾ける。
    rail_scale / ballast_scale はレール・まくらぎ／道床の横幅の倍率。"""
    m_ballast = material("ballast", (0.42, 0.40, 0.37))
    m_sleeper = material("sleeper", (0.62, 0.61, 0.58))
    m_rail = material("rail", (0.50, 0.36, 0.30), rough=0.35, metal=0.6)

    ballast = [(u * ballast_scale, v) for u, v in BALLAST]
    a, b = RAIL_IN * rail_scale, RAIL_OUT * rail_scale
    rail_l = [(-b, RAIL_Z0), (-a, RAIL_Z0), (-a, RAIL_Z1), (-b, RAIL_Z1)]
    rail_r = [(a, RAIL_Z0), (b, RAIL_Z0), (b, RAIL_Z1), (a, RAIL_Z1)]

    obs = []
    for i, path in enumerate(paths):
        obs.append(mesh_object(f"ballast{i}", *sweep(path, ballast), m_ballast))
        sleepers = [box(p.x, p.y, SLEEPER_Z, 0.24, SLEEPER_LEN * rail_scale, SLEEPER_H, rot=ang)
                    for p, ang in along(path, 0.62, 0.31)]
        if sleepers:
            obs.append(mesh_object(f"sleeper{i}", *merge(sleepers), m_sleeper))
        obs.append(mesh_object(f"railL{i}", *sweep(path, rail_l), m_rail))
        obs.append(mesh_object(f"railR{i}", *sweep(path, rail_r), m_rail))

    for ob in obs:
        if slope:
            for v in ob.data.vertices:
                v.co.z += slope(v.co.x, v.co.y)
        if clip:
            clip_to_tile(ob)


_clipper = None


def clip_to_tile(ob):
    """タイルの範囲（xy: ±TILE/2）で切り抜く。隣のタイルとの継ぎ目をそろえるため。"""
    global _clipper
    if _clipper is None or _clipper.name not in bpy.data.objects:
        v, f = box(0, 0, 0, TILE, TILE, 60)
        me = bpy.data.meshes.new("clip")
        me.from_pydata([tuple(x) for x in v], [], f)
        _clipper = bpy.data.objects.new("clip", me)
        _clipper.hide_render = True
        bpy.context.scene.collection.objects.link(_clipper)
    mod = ob.modifiers.new("clip", "BOOLEAN")
    mod.operation = "INTERSECT"
    mod.solver = "EXACT"
    mod.object = _clipper
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)


def build_tollbooth(rot_deg):
    """料金所風の建物。屋根は 13x6.5 でタイル(10x10)からはみ出す。"""
    m_conc = material("concrete", (0.66, 0.65, 0.62))
    m_white = material("booth", (0.86, 0.87, 0.88), rough=0.5)
    m_glass = material("glass", (0.25, 0.38, 0.48), rough=0.15)
    m_roof = material("roof", (0.80, 0.81, 0.83), rough=0.6)
    m_band = material("band", (0.12, 0.42, 0.24))
    m_road = material("asphalt", (0.28, 0.28, 0.30))

    parts = {
        "road": (m_road, [box(0, 0, 0.05, 10, 10, 0.1)]),
        "island": (m_conc, [box(0, 0, 0.3, 1.4, 8.0, 0.5)]),
        "booth": (m_white, [box(0, 0.6, 1.8, 1.1, 2.2, 2.5)]),
        "glass": (m_glass, [box(0, 0.6, 2.2, 1.16, 1.6, 1.0)]),
        "pillars": (m_white, [box(0, -2.4, 3.0, 0.5, 0.5, 5.0), box(0, 3.4, 3.0, 0.5, 0.5, 5.0)]),
        "roof": (m_roof, [box(0, 0.5, 5.75, 13.0, 6.5, 0.7)]),
        "band": (m_band, [box(0, 0.5, 5.75, 13.06, 6.56, 0.28)]),
    }
    obs = [mesh_object(name, *merge(geo), mat) for name, (mat, geo) in parts.items()]
    for ob in obs:
        ob.rotation_euler.z = math.radians(rot_deg)
    return obs


# ---------------------------------------------------------------- 描画と合成

def render_cell(name):
    path = os.path.join(WORK, name + ".png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


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
    rgb = sheet[..., :3].astype(np.int16)
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
    for (r, c), path in cells.items():
        sheet[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL] = load_rgba8(path)
    rgb, n_special = finalize(sheet)
    save_rgb(out, rgb)
    print(f"[sheet] {out} special-color pixels shifted: {n_special}")


# ---------------------------------------------------------------- 各アドオン

# 線路の描画位置。形状は同じで、画面上の上下位置だけを整数 px ずらす（正: 下へ）
#   new: 新描画位置（道床が低い。今の pak128・iss）
#   old: 旧描画位置（道床が高い。古い pak128・SIS）
# iss と SIS を比べると、どの方位でもレールが画面上で 4〜4.5px 違うだけだった
TRACK_PROFILES = {
    "new": {"sheet": "track", "dy": 3},
    "old": {"sheet": "track_old", "dy": -1},
}


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
        (0, 5): ("s", [[Vector(O), Vector(S) + Vector((0, -0.6))]], None),
        (0, 6): ("w", [[Vector(O), Vector(W) + Vector((-0.6, 0))]], None),
        (0, 7): ("n", [[Vector(O), Vector(N) + Vector((0, 0.6))]], None),
        (0, 8): ("e", [[Vector(O), Vector(E) + Vector((0.6, 0))]], None),
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
    set_anchor(128 + prof["dy"])  # dat オフセット -64,-32 と対応
    cells = {}
    for pos, (name, paths, slope) in jobs.items():
        clear_models()
        if name.startswith("diag_"):
            build_track(paths, slope, rail_scale=DIAG_RAIL, ballast_scale=DIAG_BALLAST)
        else:
            build_track(paths, slope)
        cells[pos] = render_cell(f"{prof['sheet']}_{name}")

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
    build_track([straight((0, -12), (0, 12))], clip=False)
    cells[(0, 0)] = render_icon("track_icon", 0.5, shift=(-0.14, 0.2), label="100")
    cells[(0, 1)] = cells[(0, 2)]  # カーソルは ns と同じ絵

    make_sheet(cells, 4, 10, os.path.join(SRC, prof["sheet"] + ".png"))


ICON = 32
ICON_SS = 4  # 4倍の大きさで描いて縮小し、輪郭をなめらかにする
LABEL_FONT = "C:/Windows/Fonts/arialbd.ttf"  # 無ければ Blender 標準の字体
ICON_BG = ((0, 196, 96), (0, 112, 56))  # iss のアイコンに合わせた緑（左上→右下）


def add_label(text, x, y, height):
    """カメラの手前に文字を置く。x, y は 0〜1 の画面位置（左上が0）、height も画面比。"""
    sc = bpy.context.scene
    cam = sc.camera
    scale = cam.data.ortho_scale
    rot = cam.rotation_euler.to_matrix()
    right, up, fwd = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0)), rot @ Vector((0, 0, -1))
    shift = Vector((cam.data.shift_x, cam.data.shift_y))
    obs = []
    # 影（右下に1px）→ 白文字の順に重ねる
    px = scale / ICON
    for dx, dy, color, depth in ((px, -px, (0.0, 0.18, 0.08), 9.0), (0, 0, (1, 1, 1), 10.0)):
        cu = bpy.data.curves.new("label", "FONT")
        cu.body = text
        cu.size = height * scale / 0.72  # 大文字の高さが height になるように
        cu.align_y = "TOP"
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


def render_icon(name, zoom, shift=(0.0, 0.0), label=None):
    """今のモデルをアイコンにする。背景を塗り、文字を重ね、セルの左上 32x32 に置く。"""
    sc = bpy.context.scene
    cam = sc.camera.data
    saved = (cam.shift_x, cam.shift_y)
    size = ICON * ICON_SS
    sc.render.resolution_x = sc.render.resolution_y = size
    cam.ortho_scale = TILE * math.sqrt(2) * zoom
    cam.shift_x, cam.shift_y = shift
    labels = add_label(label, 0.07, 0.07, 0.44) if label else []
    big = load_rgba8(render_cell(name)).astype(np.float32) / 255
    for ob in labels:
        bpy.data.objects.remove(ob, do_unlink=True)
    sc.render.resolution_x = sc.render.resolution_y = CELL
    cam.ortho_scale = ORTHO
    cam.shift_x, cam.shift_y = saved

    # 背景のグラデーションに重ねる
    t = (np.add.outer(np.arange(size), np.arange(size)) / (2 * size - 2))[..., None]
    c0, c1 = (np.array(c, np.float32) / 255 for c in ICON_BG)
    bg = c0 * (1 - t) + c1 * t
    a = big[..., 3:4]
    rgb = big[..., :3] * a + bg * (1 - a)
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
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(SRC, exist_ok=True)
    setup_scene()
    print(f"[info] ortho={ORTHO:.4f} px/unit={PX_PER_UNIT:.4f} height_step={H:.4f}")
    targets = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["track", "track_old", "tollbooth"]
    if "track" in targets:
        track_sheet("new")
    if "track_old" in targets:
        track_sheet("old")
    if "tollbooth" in targets:
        tollbooth_sheet()
