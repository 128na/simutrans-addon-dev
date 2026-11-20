"""シートを Blender の別々のプロセスで同時に描く（Blender は使わず、ふつうの Python で動かす）。

使い方（アドオンのディレクトリで）:
    python -X utf8 ../../tools/blender/render_parallel.py [--jobs 16] [--entry blender/render.py] [--blender D:\\bin\\blender\\blender.exe] 対象1 対象2 ...

対象は --entry の入口（既定 blender/render.py）の対象と同じ名前（track・track_wall_back など）。アドオンのディレクトリで動かす。対象ごとに 1 プロセスで、同時に動かすのは --jobs 個まで（既定は sheet_settings.JOBS）。
シートを分けて同時に描くと速い（全 28 枚を 16 並列で約 5 分。2026-11-17）。
同時に動く Blender の数は、マシン全体で共有する描画の枠（--slots。既定は sheet_settings.SLOTS = 論理コア数 − 4）でも抑える。
ほかの作業者（別の worktree・セッション）の render_parallel.py と枠を融通し合い、空きが無ければ空くまで待つ（render_slots.py。#74）。
--jobs はこの回だけの上限で、枠はマシン全体の上限。止めたり落ちたりした回の枠は OS が返し、その回の Blender も止まる。
Blender のプロセスは優先度「低」で起動する（--priority。既定は sheet_settings.PRIORITY）。ほかの作業が重くならないようにするため。
ログは work/render_<対象>.log。終わったら、失敗した対象（終了コードが 0 でないか、ログに Traceback がある）を出して 1 で終わる。
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_slots  # noqa: E402
import sheet_settings  # noqa: E402

HERE = os.getcwd()  # アドオンのディレクトリ

ap = argparse.ArgumentParser()
ap.add_argument("--jobs", type=int, default=sheet_settings.JOBS, help="同時に描くプロセスの数（既定は sheet_settings.JOBS。環境変数 SHEET_JOBS）")
ap.add_argument("--entry", default=os.path.join("blender", "render.py"), help="アドオンの入口（アドオンのディレクトリからの相対）")
ap.add_argument("--blender", default=sheet_settings.BLENDER)
ap.add_argument("--priority", choices=("low", "below_normal", "normal"), default=sheet_settings.PRIORITY,
                help="Blender のプロセスの優先度（既定は sheet_settings.PRIORITY = low。環境変数 SHEET_PRIORITY）")
ap.add_argument("--slots", type=int, default=sheet_settings.SLOTS,
                help="マシン全体で共有する描画の枠の合計（既定は sheet_settings.SLOTS = 論理コア数 − 4。環境変数 SHEET_SLOTS）")
ap.add_argument("--slot-dir", default=sheet_settings.SLOT_DIR, help="描画の枠を数える共有の場所（環境変数 SHEET_SLOT_DIR）")
ap.add_argument("targets", nargs="+")
args = ap.parse_args()
if args.jobs < 1 or args.slots < 1:
    ap.error(f"--jobs と --slots は 1 以上: jobs={args.jobs} slots={args.slots}")
if args.priority not in ("low", "below_normal", "normal"):  # choices は既定値（SHEET_PRIORITY）を検査しない
    ap.error(f"SHEET_PRIORITY は low・below_normal・normal のどれか: {args.priority}")


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
pool = render_slots.SlotPool(args.slot_dir, args.slots)
jobbed = render_slots.kill_children_with_parent()
print(f"[render] 枠: 合計 {pool.total}（{pool.directory}）、この回の上限 {args.jobs}"
      + ("" if jobbed or os.name != "nt" else "。Job に入れられなかったので、強制終了したときは Blender が残る"), flush=True)
queue, running, failed = list(args.targets), {}, []
start = time.time()
waiting_shown = None  # 最後に表示した、枠を待っている本数（変わったときだけ表示する）
try:
    while queue or running:
        while queue and len(running) < args.jobs:
            slot = pool.try_acquire()
            if slot is None:
                break
            t = queue.pop(0)
            log = open(os.path.join(HERE, "work", f"render_{t}.log"), "w", encoding="utf8")
            cmd = [args.blender, "-b", "--factory-startup", "--python", args.entry, "--", t]
            try:
                p = subprocess.Popen(cmd, cwd=HERE, stdout=log, stderr=subprocess.STDOUT, **POPEN_PRIORITY)
            except BaseException:
                log.close()
                slot.release()
                raise
            running[t] = (p, log, slot)
        # 枠が足りずに、この回の上限より少なくしか動かせていない本数（ほかの作業者が枠を使っている）
        waiting = min(len(queue), args.jobs - len(running))
        if waiting != waiting_shown and (waiting or waiting_shown):
            print(f"[render] 枠待ち: {waiting} 本（動いている {len(running)} 本、残り {len(queue)} 対象。枠の合計 {pool.total}）"
                  if waiting else "[render] 枠待ちが解けた", flush=True)
            waiting_shown = waiting
        for t, (p, log, slot) in list(running.items()):
            if p.poll() is not None:
                slot.release()
                log.close()
                text = open(log.name, encoding="utf8", errors="replace").read()
                ok = p.returncode == 0 and "Traceback" not in text
                if not ok:
                    failed.append(t)
                print(f"[render] {t}: {'ok' if ok else 'FAILED'} ({time.time() - start:.0f}s)", flush=True)
                del running[t]
        time.sleep(1)
finally:
    # Ctrl+C などで抜けたとき: 動いている Blender を止めて枠を返す（強制終了のときは Job と OS が同じことをする）
    for t, (p, log, slot) in running.items():
        if p.poll() is None:
            p.kill()
            p.wait()
        slot.release()
        log.close()
print(f"[render] done in {time.time() - start:.0f}s" + (f", failed: {' '.join(failed)}" if failed else ""))
sys.exit(1 if failed else 0)
