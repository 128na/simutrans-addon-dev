"""盛土の建物の版（AMI #372）のシート（共通の描画の道具 sheetlib の一部。tools/README.md）。

盛土の way（sheetlib の embankment_sheet）と同じ楔を、type=cur の 1 タイルの建物の絵にする。形の式（_emb_height・_emb_solid）と
絵の切り方（_pier_cell）は way のものをそのまま使うので、way と並べても同じ見た目になる。建物は隣とつながらないので、側面はどの辺にも作る。
シートは 2 行 × 4 列（行は夏・雪、列は layout 0〜3）。
"""
import os

from . import sheetlib as _s
from .cells import GROUND_CY, make_sheet
from .core import H, clear_models, material, mesh_object, named_materials, set_anchor

# layout 0〜3 の (way の形の名前, 側)。地図を右へ 90 度回すと layout が (l + 3) % 4 になる（本体の gebaeude.cc の rotate_layout）ので、
# 法面の向き（直線）は 南・東・北・西、台の高い角（外の角）は 北西・南西・南東・北東 の順にする
EMBANKMENT_BUILDING_LAYOUTS = {
    "straight": (("ew", "front"), ("ns", "front"), ("ew", "back"), ("ns", "back")),
    # 外の角（高いのがその角だけ）になる側: nw・sw・ne は front、se は back（_emb_height の内の角は front の se と back の nw・ne・sw）
    "corner": (("corner_nw", "front"), ("corner_sw", "front"), ("corner_se", "back"), ("corner_ne", "front")),
}


def embankment_building_sheet(sheet, kind, mat_skin=None, snow_skin=None):
    """盛土の建物のシート。kind は EMBANKMENT_BUILDING_LAYOUTS のキー。mat_skin・snow_skin は embankment_sheet と同じ"""
    top = _s.ELEV_STEPS * H
    set_anchor(GROUND_CY)
    cells = {}
    for row, skin, tag in ((0, mat_skin, ""), (1, snow_skin, "_snow")):
        with named_materials(skin):
            for layout, (name, side) in enumerate(EMBANKMENT_BUILDING_LAYOUTS[kind]):
                clear_models()
                mesh_object("embankment", *_s._emb_solid(_s._emb_height(name, side), top), material(*_s.EMBANKMENT_MAT))
                cells[(row, layout)] = _s._pier_cell(f"{sheet}{tag}_{layout}", None)
    make_sheet(cells, 2, 4, os.path.join(_s.SRC, sheet + ".png"))
