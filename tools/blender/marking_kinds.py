"""路面表示（marking）の種類ごとの表の唯一の定義（Blender を使わない。#352）。

種類を 1 つ足すと、種類の一覧・絵のあるセル・カーソルのセル・アイコンの絵・アイコンの字・雪の絵を持つかを、
描く側（sheetlib の marking.py）と dat を書く側（AMI の ami_dat.py）・アイコンを書く側（AMI の icons.py）・物の一覧（AMI の catalog.py）が
別々の表に持っていた（6 つ。#349 の記録の案 4）。ここに 1 つだけ置き、どれもここから引く。種類を足すときに触るのは、この表と、
描く関数（marking.py の marking_jobs）と、材質を変える種類ならアドオンの描き分け（AMI の render.py）。描いたセルがこの表の cells と違えば、marking.py の marking_sheet が止める。

置くのは種類ごとの値（種類は描き方で、どのアドオンが使っても同じ）だけ。どの物の名前で配るか（ami_mark_<種類>）はアドオンの側に置く。
セルの位置は sheetlib の way のシートの並び（AMI の ami_dat.py の IMAGES と同じ。iss・blender-poc の線路の並び）。
"""
from collections import namedtuple

# ---------------------------------------------------------------- 形ごとのセル（行, 列）
STRAIGHTS = frozenset({(0, 2), (0, 3)})                                            # 直線（[ns]・[ew]）
SLOPES = frozenset({(1, 0), (1, 1), (1, 2), (1, 3), (1, 5), (1, 6), (1, 7), (1, 8)})  # 坂（1 段・2 段）
DEADENDS = frozenset({(0, 5), (0, 6), (0, 7), (0, 8)})                             # 行き止まり（[s]・[w]・[n]・[e]）
CURVES = frozenset({(2, 5), (2, 6), (2, 7), (2, 8)})                               # 曲がり（[sw]・[nw]・[ne]・[se]）
TEES = frozenset({(3, 5), (3, 6), (3, 7), (3, 8)})                                 # T字（[nse]・[new]・[nsw]・[sew]）
SINGLE = (0, 9)                                                                     # 1 タイル（[-]）
CROSS = (3, 9)                                                                      # 十字（[nsew]）

# 種類の値:
#   group: "street"（一般道路に重ねる白線と路面。#187・#189）、"expwy"（高速道路に重ねる分岐・合流。#188）、"color"（一般道路に重ねる路面の色と黄色の中央線。#313）
#   cells: 絵のあるセル。ほかの形は空のセル（sheet_rows.MARKING_EMPTY_CELL）を指す
#   cursor: カーソル（シートの (0, 1)）に写すセル
#   icon: アイコンの絵にする形（dat の image の添字。AMI は icons.py が image<icon>[0] の絵を使う）
#   label: アイコンの左上の字（AMI は icons.py が書く）
#   snow: 雪の絵（[1]）を夏と別のセル（sheet_rows.MARKING_ROWS 行下）に持つか
Kind = namedtuple("Kind", "group cells cursor icon label snow")

_LANE = STRAIGHTS | SLOPES | DEADENDS
_CENTER2 = DEADENDS | TEES | {SINGLE, CROSS}
_ARM4 = DEADENDS | TEES | CURVES

# 種類 → 値。並びは物の一覧（AMI の catalog.MARKINGS）の並び
KINDS = {
    # 一般道路の多車線と交差点（#187・#189。種類の意味は sheetlib の marking.py の冒頭）
    "lane4": Kind("street", _LANE, (0, 2), "[ns]", "線", False),
    "junction2": Kind("street", _CENTER2, (0, 7), "[n]", "交", False),
    "junction2_t": Kind("street", _CENTER2, (0, 7), "[sew]", "丁", False),
    "junction4_in": Kind("street", _ARM4, (3, 5), "[nse]", "入", True),
    "junction4_out": Kind("street", _ARM4, (3, 7), "[nsw]", "出", True),
    "junction4_c": Kind("street", CURVES, (2, 8), "[se]", "印", False),
    "lane6_a": Kind("street", _LANE, (0, 2), "[ns]", "甲", False),
    "lane6_b": Kind("street", _LANE, (0, 2), "[ns]", "乙", False),
    "lane6_m": Kind("street", _LANE, (0, 2), "[ns]", "央", True),
    "junction6_in": Kind("street", DEADENDS | TEES, (3, 5), "[nse]", "入", True),
    "junction6_out": Kind("street", DEADENDS | TEES, (3, 7), "[nsw]", "出", True),
    "junction6_m": Kind("street", DEADENDS | TEES, (3, 5), "[nse]", "中", True),
    "junction6_c": Kind("street", DEADENDS | {CROSS}, (3, 9), "[nsew]", "心", False),
    # ラウンドアバウト 3×3（#372）: 行き止まり = 腕、T字 = 腕のある辺、曲がり = 輪の角、1 タイル = 中心の島
    "roundabout": Kind("street", DEADENDS | CURVES | TEES | {SINGLE}, (2, 5), "[sw]", "環", False),
    # 高速道路の分岐・合流（#188）: 行き止まり = テーパー、T字 = 平行、曲がり = 分かれ
    "diverge_main": Kind("expwy", _ARM4, (0, 7), "[n]", "分", False),
    "diverge_ramp": Kind("expwy", _ARM4, (0, 7), "[n]", "岐", False),
    "merge_main": Kind("expwy", _ARM4, (0, 7), "[n]", "合", False),
    "merge_ramp": Kind("expwy", _ARM4, (0, 7), "[n]", "流", False),
    # 路面の色と黄色の中央線（#313）: 直線・坂・行き止まり（直線と同じ絵）。色の舗装は十字・1 タイル・T字も
    "paving_red": Kind("color", _LANE | TEES | {SINGLE, CROSS}, (0, 2), "[ns]", "赤", False),
    "paving_blue": Kind("color", _LANE | TEES | {SINGLE, CROSS}, (0, 2), "[ns]", "青", False),
    "paving_green": Kind("color", _LANE | TEES | {SINGLE, CROSS}, (0, 2), "[ns]", "緑", False),
    "paving_red_striped": Kind("color", _LANE, (0, 2), "[ns]", "縞", False),
    "center_yellow": Kind("color", _LANE, (0, 2), "[ns]", "黄", False),
}


def kinds_of(group):
    """その group の種類（KINDS の並び）"""
    return tuple(k for k, v in KINDS.items() if v.group == group)


SNOW_KINDS = frozenset(k for k, v in KINDS.items() if v.snow)

for _k, _v in KINDS.items():
    assert _v.group in ("street", "expwy", "color"), (_k, _v.group)
    assert _v.cursor in _v.cells, (_k, _v.cursor)  # カーソルは絵のあるセルを写す
