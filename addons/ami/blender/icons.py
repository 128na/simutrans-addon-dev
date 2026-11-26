"""AMI のアイコン・カーソル（#25）。描いたシートの絵から作り、シートのアイコンとカーソルのセルに書き込む。

    blender -b --factory-startup --python blender/icons.py [-- シート名 ...]

アドオンのディレクトリで動かす。シート名を渡さなければ全部。render.py は描いたシートについて、最後にこれを別の Blender で動かす
（文字を描く場面を、シートの場面と分けるため）。決まり（2026-11-21、ユーザーの決定。#25 の案 A・版の字は漢字）:

- アイコン（32px）: 背景色 = 種類（線路・路面軌道・道路・高速道路・モノレール。WAY_BG）、左上 = 最高速度、右下の黒い札 = 版の漢字
  （単・後・中・前・双。VERSION_MARK）、下の帯 = 構造（高架・橋・トンネル。橋脚は高架の帯）。
  絵は、その物の直線のセルを北と南の隣のタイルの位置にもつないで、半分の大きさにしたもの（歩道はタイル 1 枚を 1/4 に）。
  等倍で真ん中を切ると、壁の single は片側しか入らず、橋脚は灰色の塊になって見分けにくかった。
  壁は版の札だけ（中央分離帯つきは左上に「分」、電柱と柵つきの電柱は左上に「柱」）、架線は左上に稲妻、橋脚は左上に「脚」「門」、歩道は左上に「歩」、車庫は左上に「庫」（絵は道が南へ出る向きの建物を 1/4 に）、
  盛土は左上に「盛」と版の札（背景は路面軌道の色。tram_track の way）、路面表示は左上に catalog.MARK_LABELS の字（背景は路面軌道の色。#187）、
  道路標識は道路の色に標識の板を 2 倍にした絵だけ（#122）
- カーソル（256px のセル）: その物の直線の絵（トンネルは坑口）に、アイコンと同じ背景色の札で「速度 + 版」（例 160後）
- 絵と札の中身は dat から読む（名前・obj・waytype・topspeed と、image[ns] などのキーが指すセル）。dat の icon・cursor が指すセルに書く
- シート名を渡すと、そのシートに書くアイコン・カーソルと、そのシートの絵から作るアイコン・カーソル（トンネルは中の way の絵、
  twin の壁は front の版の斜め）を書き直す（#141）。render.py は --own を付けて呼び、描いたシートにだけ書く（並べて描くとき、
  ほかのプロセスが描いている途中のシートを上書きしないように）。ほかのシートにある分は、描き終えてから流す命令を出す
- ほかのシートの絵から作った物は、絵のセルの sha256 を、書いたシートの横の <シート>.icon_sources.txt に控える。check_icons.py が比べる
- 書いたアイコン・カーソルのセルの sha256 を、書いたシートの横の <シート>.icon_cells.txt に控える。check_icons.py が比べ、
  icons.py を流していないシート（描画の仮のアイコンのまま）に気づく（#330）
"""
import glob
import hashlib
import os
import re
import subprocess
import sys

import bpy
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
sys.path.insert(0, _HERE)  # Blender の --python は、スクリプトのディレクトリを探す先に入れない
import catalog  # noqa: E402
import sheetlib as R  # noqa: E402

SCALE = R.SCALE  # pak の大きさ（pak128 を 1 とする倍率。sheet_settings.PAK_SIZE）。アイコン（ICON px）は大きさによらず 32px のまま
SRC = os.path.join(_HERE, "..", "src" + R.sheet_settings.SUFFIX)
CELL = R.CELL
ICON = 32
SS = 4  # 4 倍で組んで縮める（文字の輪郭をなめらかにする）
I = ICON * SS
FONT_EN = "C:/Windows/Fonts/arialbd.ttf"
FONT_JA = "C:/Windows/Fonts/YuGothB.ttc"
SKIP_DATS = ("ex_donors.dat",)

# 背景色（左上 → 右下のグラデーション）。種類で決める
WAY_BG = {"rail": ((0, 196, 96), (0, 112, 56)), "tram": ((214, 160, 0), (140, 92, 0)),
          "road": ((96, 132, 196), (40, 64, 120)), "expwy": ((70, 90, 190), (24, 30, 96)),
          "monorail": ((168, 72, 200), (96, 32, 120)),  # モノレール（#113）は紫（色相 285。ほかの waytype と 20 度以上離す。check_icons.py）
          "canal": ((0, 170, 190), (0, 96, 112))}  # 運河（#114）は青緑（色相 186）
VERSION_MARK = {"single": "単", "back": "後", "center": "中", "front": "前", "twin": "双"}
DECK = (215, 215, 220)  # 帯の床・柱の色
BOLT = [(13, 1), (4, 15), (9, 15), (6, 26), (17, 10), (12, 10), (16, 1)]  # 稲妻（32px の座標）
TRANSPARENT = np.array(R.TRANSPARENT)
# カーソルの札の位置（セルの中の上端。横は真ん中）と大きさ（等倍の px）
PLATE_TOP = 78 * SCALE
PLATE_H = 14
PLATE_CHAR_W = 8
YARD_LABEL = "操"  # 操車場のアイコンの左上の字と、カーソルの札（#115）
DEPOT_LABEL = "庫"  # 車庫のアイコンの左上の字と、カーソルの札（#112）
TURNTABLE_LABEL = "転"  # 転車台・遷車台のアイコンの左上の字と、カーソルの札（#314）
NS_STEP = (64 * SCALE, -32 * SCALE)  # 南北の直線で、北の隣のタイルの画面のずれ（pak128 のタイルは幅 128・高さ 64）


# ---------------------------------------------------------------- dat を読む
def read_dat(path):
    d = {}
    for line in open(path, encoding="utf8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        d[k.strip().lower()] = v.strip()
    return d


def ref(v):
    """"sheet.r.c,x,y" や "> sheet.r.c" → (シート, 行, 列)"""
    v = v.lstrip("> ").split(",")[0]
    sheet, r, c = v.rsplit(".", 2)
    return sheet, int(r), int(c)


# 路面表示（#187）の、絵にするセル（北へ向かう腕・北南の直線・北が閉じた T字の中心）。左上の字は catalog.MARK_LABELS
MARK_PICTURE = {"ami_mark_lane4": "image[ns][0]", "ami_mark_junction2": "image[n][0]", "ami_mark_junction2_t": "image[sew][0]",
                "ami_mark_junction4_in": "image[nse][0]", "ami_mark_junction4_out": "image[nsw][0]", "ami_mark_junction4_c": "image[se][0]",
                "ami_mark_lane6_a": "image[ns][0]", "ami_mark_lane6_b": "image[ns][0]", "ami_mark_lane6_m": "image[ns][0]", "ami_mark_junction6_in": "image[nse][0]", "ami_mark_junction6_out": "image[nsw][0]",
                "ami_mark_junction6_m": "image[nse][0]", "ami_mark_junction6_c": "image[nsew][0]",
                **{f"ami_mark_{_k}": "image[n][0]" for _k in ("diverge_main", "diverge_ramp", "merge_main", "merge_ramp")},
                **{f"ami_mark_{_k}": "image[ns][0]" for _k in ("paving_red", "paving_blue", "paving_green", "paving_red_striped", "center_yellow")}}


def describe(d):
    """dat から、アイコンの決まりに使う中身を取る"""
    name, obj = d["name"], d["obj"]
    m = re.search(r"_(single|back|center|front|twin)(_arc|_ell)?(_catenary|_divider|_pole)?$", name)
    info = dict(name=name, version=m.group(1) if m else None, speed=None, struct=None, label=None,
                old=catalog.is_old(name))  # old: 旧描画位置（SIS に合う。#26）の物。アイコンの左下に「旧」
    if name.startswith(("ami_tram", "ami_embankment", "ami_mark_")):  # 盛土・路面表示は tram_track の way（路面軌道の道具の一覧に出る）
        info["way"] = "tram"
    elif name.startswith("ami_road_expressway"):
        info["way"] = "expwy"
    elif name.startswith("ami_monorail"):  # 跨座式モノレールの way・高架・トンネルと車庫（#113）
        info["way"] = "monorail"
    elif name.startswith("ami_canal"):  # 運河と船の車庫（#114）
        info["way"] = "canal"
    elif "road" in name or "sidewalk" in name or obj == "roadsign":  # 歩道（ami_sidewalk*）と歩道の柵（ami_wall_sidewalk_*）は道路の色（#25・#119）。道路標識も（#122）
        info["way"] = "road"
    else:
        info["way"] = "rail"
    if obj == "way-object":
        info["kind"] = "catenary" if d.get("own_waytype") == "electrified_track" else "wall"
        if name.endswith("_divider"):
            info["label"] = "分"  # 中央分離帯つきの壁（#118）: 左上に「分」
        elif "_pole" in name:
            info["label"] = "柱"  # 電柱（ami_sidewalk_pole_<版>）と柵つきの電柱（#120）: 左上に「柱」、右下に版
        elif name.startswith("ami_monorail_suspended"):
            info["label"] = "懸"  # 懸垂式モノレールの電化（#116）: 跨座式用（電気の印だけ）と見分けるため左上に「懸」
    elif name.startswith("ami_pier"):
        info.update(kind="pier", label="門" if name.endswith("_gate") else "脚", struct="elev")
    elif name.startswith("ami_sidewalk"):  # 歩道の種類と高架の歩道（#119）も同じ決まり。高架は下の帯
        info.update(kind="sidewalk", label="歩", struct="elev" if name.endswith("_elev") else None)
    elif name == catalog.RAIL_TURNTABLE:  # 転車台・遷車台（#314）。道路の way だが線路の色。速度は出さず、左上に「転」
        info.update(kind="turntable", label=TURNTABLE_LABEL, way="rail")
    elif obj == "building" and d.get("type") == "stop":  # 操車場（#115）。速度は無く、左上に「操」
        info.update(kind="yard", label=YARD_LABEL)
    elif obj == "building":  # 車庫（#112）。速度は無く、左上に「庫」
        info.update(kind="depot", label=DEPOT_LABEL)
    elif obj == "roadsign":  # 道路標識（#122）: 字も札も無く、標識の板を 2 倍にした絵だけ（板の模様で見分ける）
        info["kind"] = "sign"
    elif name.startswith("ami_embankment"):  # 盛土（#123）: 左上に「盛」、右下に版（前・後）
        info.update(kind="embankment", label="盛")
    elif name.startswith("ami_mark_"):  # 路面表示（#187）: 左上に catalog.MARK_LABELS の字。速度は出さない
        info.update(kind="marking", label=catalog.MARK_LABELS[name])
    else:
        info["kind"] = {"bridge": "bridge", "tunnel": "tunnel"}.get(obj, "way")
        info["speed"] = d["topspeed"]
        info["struct"] = {"bridge": "bridge", "tunnel": "tunnel"}.get(obj, "elev" if "_elev_" in name else None)
        if name.startswith("ami_monorail_suspended"):
            info["label"] = "懸"  # 懸垂式モノレール（#116）: 跨座式と見分けるため左上に「懸」、右下に版（柱の側）
    return info


def picture_keys(d, kind, for_cursor):
    """絵にするセルのキーの候補（順に試し、絵のある最初の組を使う）。way-object は奥と手前を重ねる"""
    if kind == "tunnel":
        if for_cursor:
            return [["backimage[n][0]", "frontimage[n][0]"]]
        return None  # アイコンは中の way の絵（下の icon_layers）
    if kind == "bridge":
        return [["backimage[ns][0]"]]
    if kind == "yard":  # 1 タイルの南北の線路（layout 6。両端に階段）の奥の絵
        return [["backimage[6][0][0][0][0][0]"]]
    if kind == "turntable":  # つながりの無い 1 タイル（転車台）の絵（#314）
        return [["image[-][0]"]]
    if kind == "depot":  # 道が南へ出る向き（layout 0）の奥と手前の絵
        return [["backimage[0][0][0][0][0][0]", "frontimage[0][0][0][0][0][0]"]]
    if kind == "marking":  # 路面表示（#187）: MARK_PICTURE のセル
        return [[MARK_PICTURE[d["name"]]]]
    if kind == "sign":  # 北行きの絵（画面の右の角。表が見える）。一方通行は板を反対の向きに向けた絵なので、表が見える image[1]（#200）
        return [["image[1]" if d["name"].endswith("_one_way") else "image[0]"]]
    if kind in ("wall", "catenary"):
        # 近い斜めの分け合うタイル用（twin）は直線を持たないので、平行な 2 つの斜め（nw・se）を重ねる
        return [[f"back{k}", f"front{k}"] for k in ("image[ns]", "image[s]", "image[n]")] + \
            [["backdiagonal[nw]", "frontdiagonal[nw]", "backdiagonal[se]", "frontdiagonal[se]"]]
    return [["image[ns][0]", "frontimage[ns][0]"]]


# ---------------------------------------------------------------- 画像
_sheets = {}


def load_sheet(sheet):
    if sheet not in _sheets:
        _sheets[sheet] = R.load_rgba8(os.path.join(SRC, sheet + ".png")).copy()
    return _sheets[sheet]


def cell_rgba(sheet, r, c):
    """シートのセルを RGBA（0〜1）で。透明色は透明に"""
    x = load_sheet(sheet)[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL].astype(np.float32) / 255
    clear = np.all(np.abs(x[..., :3] * 255 - TRANSPARENT) < 1.5, axis=2)
    x[clear, 3] = 0
    x[~clear, 3] = 1
    return x


def layers(d, keys, extend=False):
    """keys の組を順に試し、絵のある最初の組を重ねて返す。extend なら、南北の直線（[ns]）を北と南の隣のタイルの位置にも重ねて、
    タイルの縁で切れない長い直線にする（アイコンの絵。大きさは 2 倍のセル）"""
    for group in keys:
        out = np.zeros((CELL, CELL, 4), np.float32)
        for k in group:
            if k in d:
                over(out, cell_rgba(*ref(d[k])))
        if not out[..., 3].any():
            continue
        if not extend:
            return out
        big = np.zeros((2 * CELL, 2 * CELL, 4), np.float32)
        reps = range(-2, 3) if any("[ns]" in k for k in group) else (0,)
        for i in reps:  # 北の隣のタイルは、画面で右上へ（タイルの幅の半分, 高さの半分）
            over(big, out, CELL // 2 + i * NS_STEP[0], CELL // 2 + i * NS_STEP[1])
        return big
    return np.zeros((2 * CELL if extend else CELL, 2 * CELL if extend else CELL, 4), np.float32)


def over(dst, src, x=0, y=0):
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    al = s[..., 3:4]
    dd = dst[y0:y1, x0:x1]
    dd[..., :3] = s[..., :3] * al + dd[..., :3] * (1 - al)
    dd[..., 3:4] = al + dd[..., 3:4] * (1 - al)


def down(c, k):
    h, w = c.shape[0] // k, c.shape[1] // k
    x = c[:h * k, :w * k].reshape(h, k, w, k, 4)
    al = x[..., 3:4].mean(axis=(1, 3))
    rgb = (x[..., :3] * x[..., 3:4]).mean(axis=(1, 3)) / np.maximum(al, 1e-6)
    return np.concatenate([rgb, al], 2)


def center_crop(c, size):
    """絵のある範囲の真ん中を中心に、size 四方を切る"""
    ys, xs = np.nonzero(c[..., 3] > 0.05)
    out = np.zeros((size, size, 4), np.float32)
    if len(ys) == 0:
        return out
    cy, cx = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2
    over(out, c, size // 2 - cx, size // 2 - cy)
    return out


def grad(c0, c1, h, w):
    t = (np.add.outer(np.arange(h), np.arange(w)) / max(h + w - 2, 1))[..., None]
    c0, c1 = np.array(c0, np.float32) / 255, np.array(c1, np.float32) / 255
    return np.concatenate([c0 * (1 - t) + c1 * t, np.ones((h, w, 1), np.float32)], 2)


def rect(dst, x0, y0, x1, y1, color, alpha=1.0):
    dst[y0:y1, x0:x1, :3] = np.array(color, np.float32) / 255 * alpha + dst[y0:y1, x0:x1, :3] * (1 - alpha)
    dst[y0:y1, x0:x1, 3] = 1


def poly(dst, pts, color, scale, dx=0, dy=0):
    """多角形を塗る（pts は scale 倍した座標になる）"""
    h, w = dst.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    px, py = (xx + 0.5) / scale - dx, (yy + 0.5) / scale - dy
    inside = np.zeros((h, w), bool)
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        cond = (y0 > py) != (y1 > py)
        xc = x0 + (py - y0) * (x1 - x0) / ((y1 - y0) if y1 != y0 else 1e-9)
        inside ^= cond & (px < xc)
    dst[inside, :3] = np.array(color, np.float32) / 255
    dst[inside, 3] = 1


# ---------------------------------------------------------------- 文字（この Blender の場面で、文字だけを平らに描く）
_text_setup = {}


def text(w, h, items):
    """items: (文字, x, y, 大文字の高さ, 色, 揃え, 影)。座標は px（左上が原点）。漢字を含む文字は FONT_JA で描く"""
    sc = bpy.context.scene
    if not _text_setup:
        sc.render.engine = "BLENDER_WORKBENCH"
        sc.display.shading.light = "FLAT"
        sc.display.shading.color_type = "OBJECT"
        sc.display.render_aa = "8"
        sc.render.film_transparent = True
        sc.view_settings.view_transform = "Standard"
        for ob in list(sc.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        cam.data.type = "ORTHO"
        sc.collection.objects.link(cam)
        sc.camera = cam
        _text_setup["fonts"] = {p: bpy.data.fonts.load(p, check_existing=True) for p in (FONT_EN, FONT_JA)}
    for ob in list(sc.objects):
        if ob.type == "FONT":
            bpy.data.objects.remove(ob, do_unlink=True)
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.camera.data.ortho_scale = max(w, h)
    sc.camera.location = (w / 2, -h / 2, 50)
    for body, x, y, hh, color, align, shadow in items:
        ja = any(ord(ch) > 127 for ch in body)
        for (dx, dy), col, z in ([((SS, -SS), (0.0, 0.12, 0.06), 1)] if shadow else []) + [((0, 0), color, 2)]:
            cu = bpy.data.curves.new("t", "FONT")
            cu.body = body
            cu.font = _text_setup["fonts"][FONT_JA if ja else FONT_EN]
            cu.size = hh / (0.88 if ja else 0.72)  # 大文字（漢字は字の高さ）が hh になるように
            cu.align_x = align
            cu.align_y = "TOP"
            ob = bpy.data.objects.new("t", cu)
            ob.color = (*col, 1)
            ob.location = (x + dx, -y + dy, z)
            sc.collection.objects.link(ob)
    # 一時ファイルはプロセスごとの名前にする。render_parallel.py は対象ごとにアイコンの後処理（この icons.py）を同時に動かすので、
    # 共通の名前だと文字の絵を取り合い、別の対象の札が入ったり欠けたりした（#244）
    p = os.path.join(R.WORK, f"_icon_text_{os.getpid()}.png")
    sc.render.filepath = p
    try:
        bpy.ops.render.render(write_still=True)
        return R.load_rgba8(p).astype(np.float32) / 255
    finally:
        try:
            os.remove(p)
        except OSError:
            pass


# ---------------------------------------------------------------- アイコンとカーソル
def band(ic, struct):
    """下の帯（高さ 6px）。高架: 床と柱 2 本、橋: 床と水、トンネル: 暗い帯と口"""
    y0 = I - 6 * SS
    if struct == "elev":
        rect(ic, 0, y0, I, y0 + 2 * SS, DECK)
        rect(ic, 0, y0 + 2 * SS, I, I, (30, 30, 30), 0.35)
        for x in (5, 23):
            rect(ic, x * SS, y0 + 2 * SS, (x + 4) * SS, I, DECK)
    elif struct == "bridge":
        rect(ic, 0, y0, I, y0 + 2 * SS, DECK)
        rect(ic, 0, y0 + 2 * SS, I, I, (60, 140, 230))
    elif struct == "tunnel":
        rect(ic, 0, y0, I, I, (60, 52, 46))
        rect(ic, 12 * SS, y0 + 2 * SS, 20 * SS, I, (10, 10, 10))


OLD_MARK = "旧"  # 旧描画位置の物のアイコンの印（左下）


def make_icon(info, pic):
    """32px のアイコン（RGBA 0〜1）"""
    ic = grad(*WAY_BG[info["way"]], I, I)
    over(ic, pic.repeat(SS, 0).repeat(SS, 1))
    has_band = info["struct"] is not None
    if has_band:
        band(ic, info["struct"])
    items = []
    if info["speed"]:
        items.append((info["speed"], 2 * SS, 2 * SS, 11 * SS, (1, 1, 1), "LEFT", True))
    if info["label"]:
        items.append((info["label"], 2 * SS, 2 * SS, 11 * SS, (1, 1, 1), "LEFT", True))
    if info["old"]:
        items.append((OLD_MARK, 2 * SS, I - (20 * SS if has_band else 13 * SS), 11 * SS, (1, 1, 1), "LEFT", True))
    if info["kind"] == "catenary":
        poly(ic, BOLT, (0, 40, 20), SS, 1, 1)
        poly(ic, BOLT, (255, 225, 30), SS)
    if items:
        over(ic, text(I, I, items))
    if info["version"]:
        s = 13 * SS
        x1, y1 = I - SS, I - (7 * SS if has_band else SS)
        rect(ic, x1 - s, y1 - s, x1, y1, (20, 20, 20), 0.85)
        over(ic, text(s, s, [(VERSION_MARK[info["version"]], s / 2, 2 * SS, 10 * SS, (1, 1, 1), "CENTER", False)]), x1 - s, y1 - s)
    return down(ic, SS)


def plate_label(info):
    mark = VERSION_MARK.get(info["version"], "")
    return (info["speed"] or info["label"] or "") + mark


def make_cursor(info, pic):
    """256px のカーソル（RGBA 0〜1）。絵の上に札を足す"""
    cur = pic.copy()
    label = plate_label(info)
    bolt = info["kind"] == "catenary"
    if not label and not bolt:
        return cur
    ss = SS * SCALE  # 札は絵（SCALE 倍）に合わせて大きくする（組む大きさ。縮めるのは SS 倍だけ）
    w = (len(label) * PLATE_CHAR_W + 8 + (10 if bolt else 0)) * ss
    h = PLATE_H * ss
    pl = grad(*WAY_BG[info["way"]], h, w)
    if bolt:
        poly(pl, [(x * 0.45 + 2, y * 0.45 + 1) for x, y in BOLT], (255, 225, 30), ss)
    if label:
        x = (w + (10 * ss if bolt else 0)) / 2
        pl_text = text(w, h, [(label, x, 3 * ss, 8 * ss, (1, 1, 1), "CENTER", True)])
        over(pl, pl_text)
    pl = down(pl, SS)  # SS 倍で組んだものを縮める。札の大きさは SCALE 倍のまま
    over(cur, pl, CELL // 2 - pl.shape[1] // 2, PLATE_TOP)
    return cur


def icon_source(d, info, dats):
    """アイコンの絵にする dat とキーの候補。トンネルは中の way の絵"""
    if info["kind"] == "tunnel":
        d = dats[d["way"]]
        return d, picture_keys(d, "way", False)
    return d, picture_keys(d, info["kind"], False)


def used_cells(d, keys):
    """layers が使う組（絵のある最初の組）のセル"""
    for group in keys:
        cells = [ref(d[k]) for k in group if k in d]
        if any(cell_rgba(*c)[..., 3].any() for c in cells):
            return cells
    return []


def cell_digest(sheet, r, c):
    """セルの RGB の sha256（行を上から。check_lib.py の cell_digest と同じ並び）"""
    x = load_sheet(sheet)[r * CELL:(r + 1) * CELL, c * CELL:(c + 1) * CELL, :3]
    return hashlib.sha256(np.ascontiguousarray(x, dtype=np.uint8).tobytes()).hexdigest()


def icon_picture(d, info, dats):
    d, keys = icon_source(d, info, dats)
    if info["kind"] == "sign" and "crosswalk" in info["name"]:  # 路面の横断歩道（#162）: 柱も板も無いので、縞の全体を 1/3 に縮める
        return crosswalk_picture(layers(d, keys))
    if info["kind"] == "sign":  # 標識の上の側（板と柱の上）を ICON/2 四方で切り、画素のまま 2 倍にする（板の字がつぶれないように）
        return sign_picture(layers(d, keys))
    if info["kind"] in ("sidewalk", "depot", "yard", "turntable"):  # 敷石・車庫・転車台はタイル 1 枚なので、つなげず、タイル 1 枚を 1/4 にして菱形を見せる
        return down(center_crop(layers(d, keys), 4 * ICON * SCALE), 4 * SCALE)
    return down(center_crop(layers(d, keys, extend=True), 2 * ICON * SCALE), 2 * SCALE)


def crosswalk_picture(c):
    """縞と停止線の全体（外接の四角）を、ICON の中央に 1/3 に縮めて置く"""
    ys, xs = np.nonzero(c[..., 3] > 0.05)
    out = np.zeros((3 * ICON * SCALE, 3 * ICON * SCALE, 4), np.float32)
    if len(ys):
        over(out, c, 3 * ICON * SCALE // 2 - (xs.min() + xs.max()) // 2, 3 * ICON * SCALE // 2 - (ys.min() + ys.max()) // 2)
    return down(out, 3 * SCALE)


def sign_picture(c):
    ys, xs = np.nonzero(c[..., 3] > 0.05)
    out = np.zeros((ICON // 2, ICON // 2, 4), np.float32)
    if len(ys):
        over(out, c, ICON // 4 - (xs.min() + xs.max()) // 2, 2 - ys.min())
    return out.repeat(2, 0).repeat(2, 1)


def put(sheet, r, c, rgba):
    """RGBA（0〜1）を、シートのセルの左上から書く。特殊色を 1 ずらし、透明な所は透明色にする（sheetlib の finalize）"""
    arr = (np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8)
    rgb, _ = R.finalize(arr)
    full = load_sheet(sheet)
    h, w = rgb.shape[:2]
    y0, x0 = r * CELL, c * CELL
    full[y0:y0 + CELL, x0:x0 + CELL, :3] = TRANSPARENT  # セルを空けてから書く
    full[y0:y0 + h, x0:x0 + w, :3] = rgb
    full[y0:y0 + CELL, x0:x0 + CELL, 3] = 255


def key_sheets(d, keys):
    """キーの候補が指すセルのシート（画素は読まない）"""
    return {ref(d[k])[0] for group in keys or () for k in group if k in d}


def main(targets=None, own_only=False):
    dats = {}
    for p in sorted(glob.glob(os.path.join(SRC, "*.dat"))):
        if os.path.basename(p) in SKIP_DATS:
            continue
        d = read_dat(p)
        dats[d["name"]] = d
    touched, skipped = set(), set()
    written = {}  # シート → {(物, icon|cursor): (行, 列)}。書いたセルの控え（write_cells）に使う
    targets = set(targets or ())
    for name, d in dats.items():
        if "icon" not in d:
            continue  # 踏切（obj=crossing。#111）は道具が無く、アイコン・カーソルを持たない
        isheet, ir, ic_ = ref(d["icon"])
        csheet, cr, cc = ref(d["cursor"])
        info = describe(d)
        pd, pkeys = icon_source(d, info, dats)
        ckeys = picture_keys(d, info["kind"], True)
        if targets and not {isheet, csheet} & targets:
            # ほかのシートの絵から作るアイコン（トンネルは中の way の絵。#141）は、絵のシートを渡したときにも作り直す。
            # own_only（render.py から呼ぶとき）は、ほかのプロセスが描いている途中のシートに書かないよう、書かずに知らせる
            if not (key_sheets(pd, pkeys) | key_sheets(d, ckeys)) & targets:
                continue
            if own_only:
                skipped.add(name)
                continue
        icells = used_cells(pd, pkeys)
        ccells = used_cells(d, ckeys)
        stamp = {isheet: [], csheet: []}
        stamp[isheet] += [(name, "icon", *c, cell_digest(*c)) for c in icells if c[0] != isheet]
        stamp[csheet] += [(name, "cursor", *c, cell_digest(*c)) for c in ccells if c[0] != csheet]
        for sheet, rows in stamp.items():
            stamps = load_stamps(sheet)
            stamps[:] = [t for t in stamps if t[0] != name] + rows
        icon = make_icon(info, icon_picture(d, info, dats))
        cell = np.zeros((CELL, CELL, 4), np.float32)
        cell[:ICON, :ICON] = icon
        cur = make_cursor(info, layers(d, picture_keys(d, info["kind"], True)))
        # 絵を読み終えてから書く（同じシートのセルを読む物がある）
        put(isheet, ir, ic_, cell)
        put(csheet, cr, cc, cur)
        written.setdefault(isheet, {})[(name, "icon")] = (ir, ic_)
        written.setdefault(csheet, {})[(name, "cursor")] = (cr, cc)
        touched |= {isheet, csheet}
        print(f"[icon] {name}: {isheet}.{ir}.{ic_} / {csheet}.{cr}.{cc} {plate_label(info)}")
    for sheet in sorted(touched):
        R.save_rgb(os.path.join(SRC, sheet + ".png"), _sheets[sheet][..., :3])
        print(f"[icon] wrote {sheet}.png")
        write_stamps(sheet, dats)
        write_cells(sheet, dats, written.get(sheet, {}), {k for w in written.values() for k in w})
    if not targets:  # 全部を書いたときは、アイコンを書かなくなったシートの控えを消す
        for suffix in (STAMP_SUFFIX, CELLS_SUFFIX):
            for path in glob.glob(os.path.join(SRC, "*" + suffix)):
                if os.path.basename(path)[:-len(suffix)] not in touched:
                    os.remove(path)
                    print(f"[icon] removed {os.path.basename(path)}")
    if skipped:
        print("[icon] 描いたシートの絵から作るアイコン・カーソルが、ほかのシートにある（書いていない）。描き終えたら作り直す: "
              "blender -b --factory-startup --python blender/icons.py -- " + " ".join(sorted(targets)))


# ---------------------------------------------------------------- ほかのシートの絵の控え（#141）
# ほかのシートのセルから作ったアイコン・カーソル（トンネルのアイコンは中の way のシートの絵）について、そのセルの sha256 を、
# アイコン・カーソルを書いたシートの横の控え（<シート>.icon_sources.txt）に書く。check_icons.py が今のシートと比べ、
# 絵のシートを描き直してアイコンを作り直し忘れたことに気づく（check.sh は Blender を使わないので、絵を作って比べられない）。
# 控えをシートごとに分けるのは、render_parallel.py で並べて描くとき、シートとその控えを同じプロセスが続けて書くようにするため
STAMP_SUFFIX = ".icon_sources.txt"  # check_icons.py と同じ
STAMP_HEADER = "# 物 icon|cursor 絵のシート 行 列 sha256（blender/icons.py が書き、check_icons.py が今のシートと比べる。#141）"
_stamps = {}


def load_stamps(sheet):
    """シートの控えの行 [(物, icon|cursor, 絵のシート, 行, 列, sha256)]"""
    if sheet not in _stamps:
        path = os.path.join(SRC, sheet + STAMP_SUFFIX)
        rows = []
        if os.path.exists(path):
            for line in open(path, encoding="utf8"):
                t = line.split()
                if len(t) == 6 and not line.startswith("#") and t[3].isdigit() and t[4].isdigit():  # 壊れた行は捨てて書き直す
                    rows.append((t[0], t[1], t[2], int(t[3]), int(t[4]), t[5]))
        _stamps[sheet] = rows
    return _stamps[sheet]


def write_stamps(sheet, dats):
    """控えを書く（dat に無い物の行は落とす）。行が無ければ控えを消す"""
    path = os.path.join(SRC, sheet + STAMP_SUFFIX)
    rows = sorted(t for t in load_stamps(sheet) if t[0] in dats)
    if not rows:
        if os.path.exists(path):
            os.remove(path)
        return
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(STAMP_HEADER + "\n")
        for t in rows:
            f.write("%s %s %s %d %d %s\n" % t)


# ---------------------------------------------------------------- 書いたセルの控え（#330）
# icons.py が書いたアイコン・カーソルのセルの sha256 を、そのシートの横の控え（<シート>.icon_cells.txt）に書く。
# check_icons.py が今のシートと比べ、icons.py を流さずに描いたシート（render_icon の仮のアイコン・仮のカーソルのまま）に気づく
# （#318 で、ami_mark_junction4_c が仮の「M」のアイコンのままマージされた）。控えをシートごとに分けるのは、上の控えと同じ理由
CELLS_SUFFIX = ".icon_cells.txt"  # check_icons.py と同じ
CELLS_HEADER = "# 物 icon|cursor 行 列 sha256（blender/icons.py が書いたセル。check_icons.py が今のシートと比べる。#330）"


def write_cells(sheet, dats, rows_now, written_any):
    """書いたセルの控えを書く。前の控えのうち、今回どこかのシートに書いた物（written_any。セルが別のシートへ移った物を含む）と
    dat に無い物の行は落とす（own_only で書かなかった物の行は残す）。sha256 は put の後のシート（保存する画素）から取る"""
    path = os.path.join(SRC, sheet + CELLS_SUFFIX)
    rows = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf8"):
            t = line.split()
            if len(t) == 5 and not line.startswith("#") and t[2].isdigit() and t[3].isdigit():
                rows[(t[0], t[1])] = (int(t[2]), int(t[3]), t[4])
    rows = {k: v for k, v in rows.items() if k not in written_any}
    for (name, kind), (r, c) in rows_now.items():
        rows[(name, kind)] = (r, c, cell_digest(sheet, r, c))
    rows = {k: v for k, v in rows.items() if k[0] in dats}
    if not rows:
        if os.path.exists(path):
            os.remove(path)
        return
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(CELLS_HEADER + "\n")
        for (name, kind), (r, c, digest) in sorted(rows.items()):
            f.write(f"{name} {kind} {r} {c} {digest}\n")


def run_in_new_blender(targets):
    """render.py から呼ぶ。文字の場面をシートの場面と分けるため、別の Blender で動かす"""
    cmd = [bpy.app.binary_path, "-b", "--factory-startup", "--python", os.path.abspath(__file__), "--", "--own"] + list(targets)
    r = subprocess.run(cmd, cwd=os.path.join(_HERE, ".."), capture_output=True, text=True, encoding="utf8", errors="replace")
    for line in r.stdout.splitlines():
        if line.startswith("[icon]") or "Error" in line or "Traceback" in line:
            print(line)
    if r.returncode != 0 or "Traceback" in r.stdout + r.stderr:
        print(r.stderr[-3000:])
        raise SystemExit("[icon] アイコン・カーソルの書き込みに失敗")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    main({a for a in args if a != "--own"} or None, own_only="--own" in args)
