"""シートを Blender の別々のプロセスで同時に描く（Blender は使わず、ふつうの Python で動かす）。

使い方（アドオンのディレクトリで）:
    python -X utf8 blender/render_parallel.py [--jobs 8] [--blender D:\\bin\\blender\\blender.exe] 対象1 対象2 ...

対象は render.py の対象と同じ名前（track・track_wall_back など）。対象ごとに 1 プロセスで、同時に動かすのは --jobs 個まで（既定 8）。
1 プロセスの描画は小さな絵の繰り返しで CPU をほとんど使わないので、シートを分けて同時に描くと速い
（13 枚で 1 プロセスなら 40 分ほど、7 プロセスに分けた残り 7 枚は約 5 分。2026-11-14）。
ログは work/render_<対象>.log。終わったら、失敗した対象（終了コードが 0 でないか、ログに Traceback がある）を出して 1 で終わる。
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("--jobs", type=int, default=8)
ap.add_argument("--blender", default=r"D:\bin\blender\blender.exe")
ap.add_argument("targets", nargs="+")
args = ap.parse_args()

os.makedirs(os.path.join(HERE, "work"), exist_ok=True)
queue, running, failed = list(args.targets), {}, []
start = time.time()
while queue or running:
    while queue and len(running) < args.jobs:
        t = queue.pop(0)
        log = open(os.path.join(HERE, "work", f"render_{t}.log"), "w", encoding="utf8")
        cmd = [args.blender, "-b", "--factory-startup", "--python", "blender/render.py", "--", t]
        running[t] = (subprocess.Popen(cmd, cwd=HERE, stdout=log, stderr=subprocess.STDOUT), log)
    for t, (p, log) in list(running.items()):
        if p.poll() is not None:
            log.close()
            text = open(log.name, encoding="utf8", errors="replace").read()
            ok = p.returncode == 0 and "Traceback" not in text
            if not ok:
                failed.append(t)
            print(f"[render] {t}: {'ok' if ok else 'FAILED'} ({time.time() - start:.0f}s)", flush=True)
            del running[t]
    time.sleep(1)
print(f"[render] done in {time.time() - start:.0f}s" + (f", failed: {' '.join(failed)}" if failed else ""))
sys.exit(1 if failed else 0)
