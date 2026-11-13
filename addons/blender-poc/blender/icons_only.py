"""線路のシートのアイコン（左上の 32x32）だけを描き直して差し替える。絵のセルは描き直さない。

使い方（アドオンのディレクトリで）:
    blender -b --factory-startup --python blender/icons_only.py

アイコンの決まり（render.py の ICON_STYLES・ICON_BANDS・ICON_BADGE）だけを変えたときに使う。
対象は、側壁（track_wall_*）・高架（track_elev_*）・橋（track_bridge）のシート。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R  # noqa: E402

os.makedirs(R.WORK, exist_ok=True)
R.setup_scene()
R.set_anchor(128 + R.BALLAST_DY)
for key, prof in R.TRACK_PROFILES.items():
    if "walls" not in prof and "band" not in prof:
        continue
    path = os.path.join(R.SRC, prof["sheet"] + ".png")
    if not os.path.exists(path):
        continue
    R.clear_models()
    R.assemble(R.TRACK_PARTS, [R.straight((0, -12), (0, 12), ext=0.6)], clip=False)
    cell = R.load_rgba8(R.render_icon(prof["sheet"] + "_icon", 0.5, shift=(-0.14, 0.2), label="100", style="track",
                                      badge=R.ICON_BADGE.get(prof.get("walls")), band=prof.get("band")))
    sheet = R.load_rgba8(path)[..., :3].copy()
    sheet[:R.ICON, :R.ICON] = cell[:R.ICON, :R.ICON, :3]
    R.save_rgb(path, sheet)
    print("[icon]", path)
