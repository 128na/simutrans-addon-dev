"""シート描画のプロファイルを取る（Blender から動かす。絵は変えない）。

使い方（アドオンのディレクトリで。SHEET_ONLY を付けるとシートは work/only/ に出て src は変わらない）:
    SHEET_ONLY=ns,diag_nw,up12 blender -b --factory-startup --python ../../tools/blender/profile_sheet.py -- 対象名

入口（blender/render.py）をそのまま動かし、
- cProfile の上位（累積時間）を work/profile_<対象>.txt に書く
- 描画本体（bpy.ops.render.render）の時間は、結果の中の render の行で分かる
"""
import cProfile
import io
import os
import pstats
import runpy
import sys
import time

target = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "track"
entry = os.path.join("blender", "render.py")

prof = cProfile.Profile()
t0 = time.perf_counter()
prof.enable()
try:
    runpy.run_path(entry, run_name="__main__")
finally:
    prof.disable()
total = time.perf_counter() - t0

os.makedirs("work", exist_ok=True)
s = io.StringIO()
ps = pstats.Stats(prof, stream=s).sort_stats("cumulative")
ps.print_stats(45)
s.write("\n--- tottime 順 ---\n")
pstats.Stats(prof, stream=s).sort_stats("tottime").print_stats(30)
out = os.path.join("work", f"profile_{target}.txt")
open(out, "w", encoding="utf8").write(f"total {total:.1f}s\n" + s.getvalue())
print(f"[profile] total {total:.1f}s -> {out}")
