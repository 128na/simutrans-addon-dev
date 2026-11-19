"""シートを Blender の別々のプロセスで同時に描く（Blender は使わず、ふつうの Python で動かす）。

使い方（アドオンのディレクトリで）:
    python -X utf8 ../../tools/blender/render_parallel.py [--jobs 16] [--entry blender/render.py] [--blender D:\\bin\\blender\\blender.exe] 対象1 対象2 ...

対象は --entry の入口（既定 blender/render.py）の対象と同じ名前（track・track_wall_back など）。アドオンのディレクトリで動かす。対象ごとに 1 プロセスで、同時に動かすのは --jobs 個まで（既定は sheet_settings.JOBS）。
シートを分けて同時に描くと速い（全 28 枚を 16 並列で約 5 分。2026-11-17）。
Blender のプロセスは優先度「低」で起動する（--priority。既定は sheet_settings.PRIORITY）。ほかの作業が重くならないようにするため。
ログは work/render_<対象>.log。終わったら、失敗した対象（終了コードが 0 でないか、ログに Traceback がある）を出して 1 で終わる。
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheet_settings  # noqa: E402

HERE = os.getcwd()  # アドオンのディレクトリ

ap = argparse.ArgumentParser()
ap.add_argument("--jobs", type=int, default=sheet_settings.JOBS, help="同時に描くプロセスの数（既定は sheet_settings.JOBS。環境変数 SHEET_JOBS）")
ap.add_argument("--entry", default=os.path.join("blender", "render.py"), help="アドオンの入口（アドオンのディレクトリからの相対）")
ap.add_argument("--blender", default=sheet_settings.BLENDER)
ap.add_argument("--priority", choices=("low", "below_normal", "normal"), default=sheet_settings.PRIORITY,
                help="Blender のプロセスの優先度（既定は sheet_settings.PRIORITY = low。環境変数 SHEET_PRIORITY）")
ap.add_argument("targets", nargs="+")
args = ap.parse_args()


def priority_opts(level):
    """Popen に渡す、プロセスの優先度を下げる引数。Windows は優先度クラス（タスクマネージャーの「低」「通常以下」）、ほかは nice 値"""
    if level == "normal":
        return {}
    if os.name == "nt":
        return {"creationflags": subprocess.IDLE_PRIORITY_CLASS if level == "low" else subprocess.BELOW_NORMAL_PRIORITY_CLASS}
    nice = 19 if level == "low" else 10
    return {"preexec_fn": lambda: os.nice(nice)}


POPEN_PRIORITY = priority_opts(args.priority)

os.makedirs(os.path.join(HERE, "work"), exist_ok=True)
queue, running, failed = list(args.targets), {}, []
start = time.time()
while queue or running:
    while queue and len(running) < args.jobs:
        t = queue.pop(0)
        log = open(os.path.join(HERE, "work", f"render_{t}.log"), "w", encoding="utf8")
        cmd = [args.blender, "-b", "--factory-startup", "--python", args.entry, "--", t]
        running[t] = (subprocess.Popen(cmd, cwd=HERE, stdout=log, stderr=subprocess.STDOUT, **POPEN_PRIORITY), log)
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
