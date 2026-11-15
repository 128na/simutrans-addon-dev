"""道路の部品（路面・縁石・歩道・白線・車線・汚れ・雪・高速道路の壁と橋脚）（共通の描画の道具 sheetlib の一部。tools/README.md）。"""
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
    H,
    Part,
    _SNOW,
    box,
    merge,
    noisy_material,
    sweep,
)
from .track_parts import (  # noqa: F401
    _SNOW_HI,
    _SNOW_LO,
)
from .wall_parts import (  # noqa: F401
    RAMP_DEPTH,
    BASE_H,
    _M_BASE,
    _M_WALL,
    _end_wall,
    _pier_box,
    _wall_shape,
)


# ---------------------------------------------------------------- 道路
# SIS の一般道（SIS_L_RG1-1_01S、歩道付き 50km/h）の断面に合わせる。横位置はタイル半幅 5 に対する値:
#   中央線 0 / 車道 ±3.2 / 路側の白線 ±3.3〜3.45 / 縁石 ±3.6〜3.85 / 歩道 〜タイルの端
ROAD_HW = 3.6          # 車道の半幅（縁石の立ち上がりまで）

CURB_W = 0.25          # 縁石の上面の幅

SIDEWALK_H = 0.25      # 歩道の高さ（縁石の立ち上がり 約2px）

LINE_W = 0.15          # 白線の幅（約1px）

LINE_TOP = 0.012       # 白線の上面の高さ（汚れ・雪の層は、これより下に置く）

EDGE_LINE = 3.37       # 路側の白線の中心

ROAD_DIAG = 2 / math.sqrt(10)  # 斜めの横幅の倍率（SIS も線路と同じく縮めている）

# 斜めのタイルの車道・縁石・白線は、直線とのつなぎ目（タイルの辺）で直線と同じ点を通るようにする。
# 斜めは辺を 45° で横切るので、経路からの距離は直線の 1/√2。SIS の斜め（車道 2.7、白線は直線の 0.632〜0.68 倍）は
# これより少し外・内にずれていて、つなぎ目で白線が1px 切れ、縁石が1〜2px 段になっていた
DIAG_EDGE = 1 / math.sqrt(2)


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
    return sweep(path, [(u - w, 0.0), (u + w, 0.0), (u + w, LINE_TOP), (u - w, LINE_TOP)])


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


def _mix_material(kind, tag, lo, hi, to, t, scale, spec=None):
    """路面の 2 色（lo・hi）を、目標の 2 色 to へ t だけ寄せたまだらの材質（走行跡・まだらの雪）。"""
    mix = lambda a, b: tuple(x + (y - x) * t for x, y in zip(a, b))
    return lambda: noisy_material(f"road_{kind}_{tag}_{round(t * 100)}", mix(lo, to[0]), mix(hi, to[1]), scale=scale,
                                  rough=0.9, spec=spec)


def _wear_material(tag, lo, hi, t, spec=None):
    """走行跡の材質: 路面の 2 色を、磨かれた色へ t だけ寄せる。"""
    return _mix_material("wear", tag, lo, hi, (_WEAR_LO, _WEAR_HI), t, 90, spec)


class WearPath(list):
    """走行跡だけに使う経路。fade=True は行き止まりへ向かう経路で、始点（閉じた側）から濃い帯ほど手前で止める。"""

    def __init__(self, points, fade=False):
        super().__init__(points)
        self.fade = fade


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


def _slush_material(tag, lo, hi, t, spec=None):
    """まだらの雪: 路面の 2 色を雪の色へ t だけ寄せ、粗いまだらにする（ぼかしの段）。"""
    return _mix_material("slush", tag, lo, hi, (_SNOW_LO, _SNOW_HI), t, 45, spec)


ROAD_PARTS += tuple(
    Part(n, "bed", "road", _SNOW if t is None else _slush_material("street", (0.013, 0.0135, 0.015), (0.028, 0.029, 0.031), t),
         (lambda z0, th: lambda t_, k: box(0, 0, z0 + th / 2, *t_.size, th))(z0, th), "snow", "tile",
         carve=(lambda w: lambda t_, k: t_.hw * w / ROAD_HW)(w))
    for n, w, t, z0, th in SNOW_LAYERS)

# 高速道路の側壁（iss の都市高速 wrg_0120 と同じく、タイルの端に立つコンクリートの壁）。路面の基準面に乗り、横位置は車線と同じ倍率
# （斜めは直線の 1/√2 で、タイルの辺で直線の壁と同じ点を通る）。外側の面はタイルの端の少し内側（4.95）
EXPWY_WALL_U, EXPWY_WALL_W, EXPWY_WALL_H = 4.55, 0.40, 1.1

ROAD_CUT_Z = (-10.0, 4 * H)  # 坂を当てた後の道路の部品から削る型の高さ（急坂 2H より十分高く）

ROAD_PARTS += tuple(Part(n, "bed", "lane", _M_WALL, _wall_shape(sg, EXPWY_WALL_U, EXPWY_WALL_W, EXPWY_WALL_H), "wall", tall=True,
                         corridor=EXPWY_WALL_U, thick=EXPWY_WALL_W) for n, sg in (("wallL", -1), ("wallR", 1)))

ROAD_PARTS += (Part("endw", "bed", "lane", _M_WALL, _end_wall(EXPWY_WALL_W, EXPWY_WALL_H), "wall", "end", tall=True),)

EXPWY_PIER_ACROSS = 2 * EXPWY_WALL_U  # 高架の橋脚の、道を横切る向きの長さ。床がタイルいっぱいなので、両側の壁の下まで届かせて床の縁から見せる（中央だけの柱は床に隠れた）


def _expwy_pier_shape(path, k):
    """高架の高速道路の橋脚: 経路の中ほどの下に立つ、道を横切る向きに長い柱（線路の _pier_shape と同じ置き方）。"""
    return _pier_box(path, EXPWY_PIER_ACROSS * k)


ROAD_PARTS += (Part("pier", "bed", "lane", _M_BASE, _expwy_pier_shape, "pier"),)

# 橋の端の坂（平地から立ち上がる坂）の躯体: 線路の rampbody と同じく、基盤の下を地面まで埋める（壁の外側まで）
ROAD_PARTS += (Part("rampbody", "bed", "lane", _M_BASE,
                    lambda path, k: sweep(path, [(-(EXPWY_WALL_U + EXPWY_WALL_W) * k, -RAMP_DEPTH), ((EXPWY_WALL_U + EXPWY_WALL_W) * k, -RAMP_DEPTH),
                                                 ((EXPWY_WALL_U + EXPWY_WALL_W) * k, -BASE_H), (-(EXPWY_WALL_U + EXPWY_WALL_W) * k, -BASE_H)]),
                    "ramp", ground=True),)

# 橋の桁: iss の都市高速の橋（bridge/road の 0120_bridge1）と同じく、床の縁を青い鋼の帯に見せる（基盤の側面）
_M_GIRDER = ("girder", (0.22, 0.40, 0.62))

# 雪の絵（dat の image[..][1]）: 道路は線路より除雪されている想定で、車道は夏と同じ（路面・白線・走行跡）。
# 雪は路肩（group "snow" の snowbank）と、歩道・縁石だけ（2026-11-15、ゲームで確認して決めた）
ROAD_SNOW_SKIN = {"curb": _SNOW, "paving": _SNOW}

ROAD_SNOW_GROUPS = ("snow",)
