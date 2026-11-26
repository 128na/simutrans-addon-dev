"""路面軌道の版が、256 でつながる奥の辺の上の帯も塗る印（fill_back_band）を持つかを見る（#365）。

路面軌道は道路と同じタイルに重なる。土の上の軌道と道路の上の軌道の境・軌道の車庫の前では、道路がその辺でつながらず、
道路が帯を塗って道路の端の暗い縁を描く。軌道も帯を空けると、それをレールで覆う物が無く、レールを横切る暗い線になった。
印の効き方（track_sheet が持ち分に exits を空で渡すこと）は tools/blender/check_ground_mask.py が見る。

bpy などを差し替えて blender/render.py を読む（Blender なし）。失敗は終了コード 1。
    python -X utf8 check_tram_band.py
"""
import os
import sys
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "blender"))
sys.path.insert(0, os.path.join(HERE, "blender"))
for _m in ("bpy", "bmesh", "mathutils", "bpy_extras", "bpy_extras.object_utils"):
    sys.modules[_m] = mock.MagicMock()

import render  # noqa: E402
import sheetlib as R  # noqa: E402

prof = R.TRACK_PROFILES[render.TRAM_KEY]
if not prof.get("fill_back_band"):
    sys.exit("[tram-band] 路面軌道の版に fill_back_band が無い（256 で軌道の境・車庫の前のレールに暗い線が出る。#365）")
if R.track_own_exits(prof, "ns") != "":
    sys.exit("[tram-band] 路面軌道の版の持ち分に渡す exits が空でない（#365）")
print("[tram-band] 路面軌道の版は、つながる奥の辺の上の帯も塗る")
