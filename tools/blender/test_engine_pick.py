"""EEVEE の識別子の選び方（sheetlib.core.pick_eevee）の確認。Blender の中で動かす:
    blender -b --factory-startup --python tools/blender/test_engine_pick.py
版による分岐（_NEXT だけ・BLENDER_EEVEE だけ・両方・どちらも無い）は識別子の一覧を差し替えて確かめ、
いまの Blender では setup_scene が実際に描画エンジンを設定できることも確かめる。失敗は終了コード 1。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from sheetlib import core  # noqa: E402

CASES = [
    ({"BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH", "CYCLES"}, "BLENDER_EEVEE_NEXT"),   # 4.2〜4.5
    ({"BLENDER_EEVEE", "BLENDER_WORKBENCH", "CYCLES"}, "BLENDER_EEVEE"),              # 4.1 以前・5.x
    ({"BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"}, "BLENDER_EEVEE_NEXT"),        # 両方あれば _NEXT
]
fails = []
for ids, want in CASES:
    got = core.pick_eevee(ids)
    if got != want:
        fails.append(f"{sorted(ids)}: {got} != {want}")
try:
    core.pick_eevee({"CYCLES", "BLENDER_WORKBENCH"})
    fails.append("EEVEE が無いのに止まらなかった")
except RuntimeError:
    pass

scene = core.setup_scene()
if scene.render.engine not in core.EEVEE_IDS:
    fails.append(f"setup_scene の engine が想定外: {scene.render.engine}")

print(f"[test] blender {bpy.app.version_string} engine={scene.render.engine}")
if fails:
    print("[test] FAIL:", *fails, sep="\n  ")
    sys.exit(1)
print("[test] ok")
