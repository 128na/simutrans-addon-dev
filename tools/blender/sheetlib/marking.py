"""交差点の路面表示の way（waytype=tram_track。AMI #156）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

道路の上に重ねて敷く路面軌道の way の絵で、白線だけを描く（路面は描かない。下の道路の絵が見える）。
役割は way のつながる形で決める（iss の util/road_misc/intersection.dat と同じ作り）:
  行き止まり（n・e・s・w）: 交差点へ入る口のタイル。行き止まりの向き（つながる辺）が交差点の側で、その辺の手前に横断歩道、
                            その手前に停止線を描く
  ほかの形（直線・曲がり・T字・十字）: 交差点のタイル（口の表示を敷くと交差点のタイルにも表示が載る）。何も描かない
種類（kind）:
  stop:           2 車線の道路（1 タイルに片側 1 車線ずつ）の口。横断歩道は路側線のあいだ、停止線は入ってくる車線の半分
  stop_wide:      4 車線の道路（1 タイルに同じ向きの 2 車線。AMI #121 の lane の版の 1・2）の入る側。横断歩道と停止線を、
                  中央線の側のタイルの辺から路側線まで（左側通行なので、路側線は進入する向きの左）
  crosswalk_wide: 4 車線の道路の出る側。横断歩道だけを、路側線（進入する向きの右）から中央線の側のタイルの辺まで
路側帯（路側線の外）には、どの種類も横断歩道と停止線を描かない（2026-11-22、ユーザーの指摘。#156）
位置と幅は道路の白線（road_parts の EDGE_LINE・LINE_W・LINE_TOP・STOP_LINE_W）に合わせる。雪の絵は持たない（道路は車道を除雪した想定で、
車道の白線は夏と同じ。dat は雪の絵に夏のセルを使う）。坂・斜めの絵は持たない（交差点は平らな所に作る）
"""
import os

from . import sheetlib as _s
from .cells import ROAD_CY, make_sheet, render_cell
from .core import clear_models, material, mesh_object, set_anchor, TILE
from .road_parts import EDGE_LINE, LINE_TOP, LINE_W, STOP_LINE_W

# ---------------------------------------------------------------- 寸法（部品の 1 単位 ≈ 1 m。道路の車線は 1 本 約 3.4）
MARKING_CROSSWALK_NEAR = 1.5   # 横断歩道の帯の、タイルの中心の側の端（タイルの中心から交差点の向きへ）
MARKING_CROSSWALK_FAR = 4.5    # 横断歩道の帯の、交差点の側の端（タイルの辺 5 の 0.5 手前）
MARKING_STRIPE_W = 0.5         # 横断歩道の縞の幅（縞のあいだも同じ幅。周期 1.0 で、隣のタイルの縞と同じ並びになる）
# 縞の中心（進入する向きの左を正とする横位置）。どれも路側線（±EDGE_LINE）の内に収める。周期 1.0 で、4 車線の入る側と出る側の
# 縞は、2 タイルの境（中央線）をまたいで同じ並びになる
MARKING_STRIPES = {"narrow": [i - 3.0 for i in range(7)],      # 2 車線: 路側線の内に 7 本
                   "wide_in": [i - 4.5 for i in range(8)],     # 4 車線の入る側: 中央線の側の辺（-5）から左の路側線の内まで 8 本
                   "wide_out": [i - 2.5 for i in range(8)]}    # 4 車線の出る側: 右の路側線の内から中央線の側の辺（+5）まで 8 本
MARKING_STOP_U = 0.6           # 停止線の中心（タイルの中心から交差点の向きへ。横断歩道の帯の手前）
MARKING_Z = (0.0, LINE_TOP + 0.004)  # 白線の下面・上面（道路の白線より少しだけ上）
MARKING_DRIVE_LEFT = True      # 停止線の通行の側（日本は左側通行。右側通行の版は作らない。2026-11-22、ユーザーの決定）
MARKING_STOP_END = EDGE_LINE - LINE_W / 2  # 停止線の路側の端: 路側線の内の縁まで（路側帯へ出さない）
# 白の材質: 道路の白線（road_parts の _M_LINE。幅 1px で、ゲームの画面では路面と混ざって灰色がかって見える）と同じ明るさに見えるよう、
# 面で描く表示は色と発光を落とす。値は、ゲームの画面（拡大率 1）で道路の白線の画素の平均と、横断歩道の縞の画素の平均を比べて決めた
MARKING_LINE = ("marking_line", (0.80, 0.80, 0.82), 0.6, 0.0, 0.35)

# 種類 → (横断歩道の並び, 停止線の横の範囲（進入する向きの左を正とする横位置）か None)
MARKING_KINDS = {
    "stop": ("narrow", (0.0, MARKING_STOP_END)),
    "stop_wide": ("wide_in", (-TILE / 2, MARKING_STOP_END)),
    "crosswalk_wide": ("wide_out", None),
}
# セル（行, 列）→ 行き止まりの向き（交差点の側の辺）。位置は線路の way と同じ（ami_dat.py の IMAGES の image[s] など）
MARKING_CELLS = {(0, 5): (0, -1), (0, 6): (-1, 0), (0, 7): (0, 1), (0, 8): (1, 0)}
MARKING_EMPTY_CELL = (0, 9)    # 交差点のタイルの形（直線・曲がり・T字・十字・1 タイル）が使う空のセル


def _quad(name, a, u0, u1, v0, v1, mat):
    """交差点の向き a（単位ベクトル）の座標で、u0〜u1（a の向き）× v0〜v1（a の左）の白い板"""
    ax, ay = a
    sx, sy = -ay, ax
    pts = [(u, v) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
    xy = [(ax * u + sx * v, ay * u + sy * v) for u, v in pts]
    if (xy[1][0] - xy[0][0]) * (xy[2][1] - xy[0][1]) - (xy[1][1] - xy[0][1]) * (xy[2][0] - xy[0][0]) < 0:
        xy = xy[::-1]
    z0, z1 = MARKING_Z
    verts = [(x, y, z0) for x, y in xy] + [(x, y, z1) for x, y in xy]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return mesh_object(name, verts, faces, mat)


def marking_build(kind, a):
    """口のタイル 1 枚の白線。a は交差点の側の向き"""
    stripes, stop = MARKING_KINDS[kind]
    mat = material(*MARKING_LINE)
    w = MARKING_STRIPE_W / 2
    for i, c in enumerate(MARKING_STRIPES[stripes]):
        _quad(f"marking_stripe{i}", a, MARKING_CROSSWALK_NEAR, MARKING_CROSSWALK_FAR, c - w, c + w, mat)
    if stop:
        v0, v1 = stop if MARKING_DRIVE_LEFT else (-stop[1], -stop[0])
        _quad("marking_stop", a, MARKING_STOP_U - STOP_LINE_W / 2, MARKING_STOP_U + STOP_LINE_W / 2, v0, v1, mat)


def marking_sheet(sheet, kind, label="M"):
    """交差点の路面表示の way のシート（1 行）。行き止まりのセル（MARKING_CELLS）に口の白線、アイコン（0,0）は仮の絵
    （AMI は icons.py が描き直す）、カーソル（0,1）は北の口の絵。MARKING_EMPTY_CELL は空"""
    set_anchor(ROAD_CY)  # 道路と同じ（dat のオフセット -64,-32）
    cells = {}
    for (r, c), a in MARKING_CELLS.items():
        clear_models()
        marking_build(kind, a)
        cells[(r, c)] = render_cell(f"{sheet}_{r}_{c}")
    clear_models()
    marking_build(kind, (0, 1))
    cells[(0, 0)] = _s.render_icon(sheet + "_icon", 0.5, shift=(-0.14, 0.2), label=label, style="tram")
    cells[(0, 1)] = cells[(0, 7)]
    make_sheet(cells, 1, 10, os.path.join(_s.SRC, sheet + ".png"))
