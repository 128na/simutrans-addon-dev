"""線路の壁・橋脚の面を、#78 の段 2（線路の基盤・高架・橋に入れたコンクリート）にそろえた版を試しに描く（#83）。

壁の way-object（ami_wall_rail_<版>・_catenary・ami_wall_rail_twin_catenary_<back|front>）と橋脚の way（ami_pier_rail・ami_pier_rail_gate）の
シートを、壁（材質の名前 wall）・橋脚（pier・pier_post_<角>・pier_beam_<辺>）の材質を段 2（render.py の TRACK_SURFACE）に替えて描く。
架線の柱・梁などほかの材質と、橋の柱（材質 pier。橋のシートは描かない）・坑口・道路の壁と橋脚は今のまま。

アドオンのディレクトリで:

    python -X utf8 ../../tools/blender/render_parallel.py --entry blender/wallpier_calib.py <対象 ...>   # 描く（対象は TARGETS）
    python -X utf8 blender/wallpier_calib.py      # 描いた後: src/ と build.py を work/wallpier/<段>/build/ に写し、描いた絵を上書きして pak を作る

描いた絵は work/wallpier/<段>/src/。pak は work/wallpier/<段>/build/dist/ami.pak で、dist/ami.pak と同じ名前の物だけを持つ（違いは壁・橋脚の絵だけ）。
壁のシートは基盤の版の対象（ami_rail_ballast_base_<版>）が書くので、その way のシートも work/wallpier/<段>/src/ に描かれる（pak には入れない。
src/ と同じになるかを確かめる）。AMI_WALLPIER=0 で描くと差し替えなし（src/ とバイト単位で同じになるかを確かめる）。
"""
import glob
import os
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
STEP = os.environ.get("AMI_WALLPIER", "2")   # 2: 段 2 にそろえる、0: 差し替えなし
WORK_DIR = os.path.join(ROOT, "work", "wallpier", STEP)
TRACK = "ami_rail_ballast"   # catalog.WALL_TRACK（壁・架線のシートを描く元の軌道）
VARIANTS = ("single", "back", "center", "front")
BASE_TARGETS = [f"{TRACK}_base_{v}" for v in VARIANTS]   # 壁のシート ami_wall_rail_<版> を書く
TARGETS = BASE_TARGETS + [f"ami_wall_rail_{v}_catenary" for v in VARIANTS] + \
    [f"ami_wall_rail_twin_catenary_{v}" for v in ("back", "front")] + ["ami_pier_rail", "ami_pier_rail_gate"]
# pak で差し替えるシート（壁・橋脚だけ。基盤の版の way のシートは差し替えない）
SHEETS_OUT = [f"ami_wall_rail_{v}" for v in VARIANTS] + [f"ami_wall_rail_{v}_catenary" for v in VARIANTS] + \
    [f"ami_wall_rail_twin_catenary_{v}" for v in ("back", "front")] + ["ami_pier_rail", "ami_pier_rail_gate"]
GATE_CORNERS = ("c", "ne", "nw", "se", "sw")             # 門型の柱の角（sheetlib の _gate_parts）
GATE_SIDES = ("n", "s", "e", "w", "ne", "nw", "se", "sw")  # 門型の梁の辺（直線は辺、斜めの片持ちは角）


def _render():
    import render  # noqa: E402  AMI の描き分けを登録する（render.py は __main__ でないので描かない）
    import sheetlib as R  # noqa: E402
    import sheetlib.cells as C  # noqa: E402
    import sheetlib.core as K  # noqa: E402
    import sheetlib.sheetlib as S  # noqa: E402

    on = STEP != "0"
    conc = lambda nm, rgb: (lambda: R.tiled_concrete_material(f"ami_wallpier_concrete_{nm}", rgb, **render.TRACK_SURFACE))
    wall = {R._M_WALL[0]: conc(R._M_WALL[0], R._M_WALL[1])} if on else {}
    pier = {R._M_PIER[0]: conc(R._M_PIER[0], R._M_PIER[1])} if on else {}
    gate = {}
    if on:
        gate.update({f"{R._M_PIER_POST[0]}_{k}": conc(f"{R._M_PIER_POST[0]}_{k}", R._M_PIER_POST[1]) for k in GATE_CORNERS})
        gate.update({f"{R._M_PIER_BEAM[0]}_{k}": conc(f"{R._M_PIER_BEAM[0]}_{k}", R._M_PIER_BEAM[1]) for k in GATE_SIDES})

    S.SRC = os.path.join(WORK_DIR, "src")
    for m in (K, C, S):
        m.WORK = os.path.join(WORK_DIR, "tmp")
    os.makedirs(K.WORK, exist_ok=True)
    os.makedirs(S.SRC, exist_ok=True)

    p = lambda n: n.removeprefix("ami_")
    for v in VARIANTS:  # 基盤の版は今の基盤・躯体の差し替え（TRACK_MAT_SKIN）に壁を足す。架線つきの壁は壁だけ
        prof = R.TRACK_PROFILES[p(f"{TRACK}_base_{v}")]
        prof["mat_skin"] = dict(prof.get("mat_skin") or {}, **wall)
        R.TRACK_PROFILES[p(f"{TRACK}_base_{v}") + "_catenary"]["mat_skin"] = wall or None
    for v in ("back", "front"):
        R.TRACK_PROFILES[p(f"{TRACK}_base_{v}") + "_twin_catenary"]["mat_skin"] = wall or None
    sheets = {t: render.SHEETS[t] for t in TARGETS}
    sheets["ami_pier_rail"] = lambda: R.pier_sheet("ami_pier_rail", render._DATUMS, label=render.PIER_LABEL, mat_skin=pier or None)
    sheets["ami_pier_rail_gate"] = lambda: R.pier_gate_sheet("ami_pier_rail_gate", render._DATUMS, label=render.PIER_GATE_LABEL,
                                                             mat_skin=gate or None)
    R.run_targets(sheets, TARGETS)


def _pack():
    """src/ と build.py・ex_graft.py を work/wallpier/<段>/build/ に写し、壁・橋脚の絵だけを描いた物に替えて build.py を回す。"""
    build = os.path.join(WORK_DIR, "build")
    shutil.rmtree(build, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "src"), os.path.join(build, "src"))
    for f in ("build.py", "ex_graft.py"):
        shutil.copy(os.path.join(ROOT, f), build)
    for n in SHEETS_OUT:
        png = os.path.join(WORK_DIR, "src", n + ".png")
        if not os.path.exists(png):
            sys.exit(f"[wallpier] {png} が無い（先に描く）")
        shutil.copy(png, os.path.join(build, "src", n + ".png"))
    r = subprocess.run([sys.executable, "-X", "utf8", "build.py"], cwd=build)
    if r.returncode != 0:
        sys.exit("[wallpier] build.py が失敗")
    print(f"[wallpier] {os.path.join(build, 'dist', 'ami.pak')}（差し替え {len(SHEETS_OUT)} 枚）")
    for f in sorted(glob.glob(os.path.join(WORK_DIR, "src", f"{TRACK}_base_*.png"))):
        same = open(f, "rb").read() == open(os.path.join(ROOT, "src", os.path.basename(f)), "rb").read()
        print(f"[wallpier] way のシート {os.path.basename(f)}: {'src/ と同じ' if same else 'src/ と違う'}")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        _pack()
    else:
        sys.path.insert(0, _HERE)
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
        _render()
