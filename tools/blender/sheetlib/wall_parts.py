"""壁・基盤・橋・高架の橋脚の形と寸法（線路と道路で共通）（共通の描画の道具 sheetlib の一部。tools/README.md）。"""
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
    box,
    sweep,
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
        return box(c.x, c.y, wh / 2, ww, END_WALL_SPAN, wh, rot=math.atan2(d.y, d.x))
    return shape


_end_wall_shape = _end_wall()


def _ramp_body_shape(path, k):
    """橋の端の坂（平地から立ち上がる坂）の躯体: 基盤の下を地面まで埋める。assemble が坂を当てた後、地面より下を切り上げる。"""
    u = (WALL_U + WALL_W) * k
    return sweep(path, [(-u, -RAMP_DEPTH), (u, -RAMP_DEPTH), (u, -BASE_H), (-u, -BASE_H)])

# 橋: 床版（路盤の下の板）と橋脚。床版は路盤に乗る部品、橋脚は橋の下の地面のタイルに描く別の絵
BASE_H = 0.35

PIER_W, PIER_L = 1.6, 3.2
END_WALL_SPAN = 14.0   # 行き止まりの端の壁の幅（タイルの幅より広く作り、後で削る）
RAMP_DEPTH = 60.0      # 橋の端の坂の躯体を地面より下へ延ばす深さ


_M_BASE = ("base", (0.50, 0.50, 0.48))

PIER_SIZE = 1.6
PIER_ACROSS_K = 2.4   # 高架の橋脚の、線路を横切る向きの長さ（PIER_SIZE の倍率）


# 高架の床の高さ（段）。本体は、pak の simuconf に way_height_clearance が無いと height_conversion_factor（pak128 は 2）を使う
# （simmain.cc）。橋脚はこの段数だけ下の地面まで伸ばし、持ち分も同じだけ下へ広げる（lower = 16 行 × 段数）
ELEV_STEPS = 2

ELEV_LOWER = 16 * ELEV_STEPS

# 橋脚を別の way に分けた高架（AMI。ADR 0003）: 床（基盤の板 BASE_H）の下に、躯体（桁）を足す。橋脚は高架の真下の地面のタイルの
# 別の way（pier_sheet）が描き、上端を躯体の下面に合わせる。
#   ELEV_BODY_D: 躯体の深さ（基盤の下面から）。ELEV_BODY_INSET: 壁のある側で、壁の外の面から躯体の側面を内へ下げる幅（床の縁を見せる）。
#   ELEV_BODY_LOWER: 躯体を描くために、高架の way の持ち分を下へ広げる行数（深さの px に余りを足す）
#   ELEV_BODY_DIAG_INSET: 斜めの躯体の壁の無い側の切り口を、路盤の面の高さで近い斜めの 2 本の真ん中（DIAG_OPEN_HALF）から内へ下げる幅。
#   切り口は基盤と同じ傾き（DIAG_OPEN_UNDERCUT）で、下ほど中心線へ寄る（躯体の上面で約 1.35 内）
ELEV_BODY_D = 1.0
ELEV_BODY_INSET = 0.45
ELEV_BODY_DIAG_INSET = 0.3
ELEV_BODY_LOWER = math.ceil((BASE_H + ELEV_BODY_D) * 16 / H) + 2
_M_ELEV_BODY = ("elev_body", (0.56, 0.56, 0.54))

# 高架の橋脚の way（pier_sheet）: 経路の中ほどの下に立つ、線路を横切る向きに長い柱（POC の _pier_box と同じ寸法）。
# 上端は高架の躯体の下面（地面から ELEV_STEPS 段 − BASE_H − ELEV_BODY_D）より PIER_TOP_OVERLAP だけ上（躯体に隠れる）。
# 下端は地面より PIER_FOOT だけ下（持ち分で切る）。PIER_RISE: 持ち分を上へ広げる行数
PIER_TOP_OVERLAP = 0.2
PIER_FOOT = 0.5
PIER_RISE = 16 * ELEV_STEPS + 4
_M_PIER = ("pier", (0.56, 0.56, 0.54))

# 門型の橋脚の way（pier_gate_sheet）: 柱をタイルの角の近くに立て、柱の間を空けて上に梁を渡す。直下に並行する道路と、
# タイルの中ほどを横切る道路のどちらも、柱の内側の面（中心から PIER_GATE_CLEAR）より内を通れる。
#   PIER_GATE_POST: 柱の太さ（正方形の 1 辺）。柱はタイルの辺に面を合わせ（中心は辺から PIER_GATE_POST / 2 内）、隣のタイルの柱と背中合わせになる
#   PIER_GATE_BEAM_EMBED: 梁（と柱）の上端を、高架の躯体の下面より上へ食い込ませる高さ（躯体の深さ ELEV_BODY_D より小さく、躯体に隠れる。
#     床より幅の広い梁の端は、躯体の横で食い込んだ分まで見える）
#   PIER_GATE_BEAM_SHOW: 梁の、躯体の下面より下に見える厚み。高架下の通れる高さは 床の高さ − 基盤 − 躯体 − これ
#   PIER_GATE_BEAM_D: 梁の深さ（上の 2 つの和）
#   PIER_GATE_CLEAR: 柱の内側の面の、タイルの中心からの距離（道路が通れる半幅）
PIER_GATE_POST = 1.0
PIER_GATE_BEAM_EMBED = 0.6
PIER_GATE_BEAM_SHOW = 0.25
PIER_GATE_BEAM_D = PIER_GATE_BEAM_EMBED + PIER_GATE_BEAM_SHOW
PIER_GATE_CLEAR = 5.0 - PIER_GATE_POST   # TILE / 2 − 柱の太さ
_M_PIER_POST = ("pier_post", (0.56, 0.56, 0.54))
_M_PIER_BEAM = ("pier_beam", (0.52, 0.52, 0.50))


def _pier_box(path, across):
    """高架の橋脚: 経路の中ほどの下に立つ、経路を横切る向きに長い柱。床（基盤）の下から、ELEV_STEPS 段下の地面まで。"""
    mid = path[len(path) // 2] if len(path) > 2 else (path[0] + path[-1]) / 2
    d = (path[-1] - path[0]).normalized()
    top, bottom = -BASE_H, -ELEV_STEPS * H
    return box(mid.x, mid.y, (top + bottom) / 2, PIER_SIZE, across, top - bottom, rot=math.atan2(d.y, d.x))


def _pier_shape(path, k):
    return _pier_box(path, PIER_SIZE * PIER_ACROSS_K)  # 線路を横切る向きに長い
