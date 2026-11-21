"""基盤・高架の面の描き込みの量を、段に分けて見比べる試作（#78）。

在来線の基盤の 4 版・高架の 4 版（ami_rail_ballast_base_<版>・_elev_<版>）だけを、段ごとに別の名前で描く。変えるのは、
基盤の板（材質の名前 base）と高架の躯体（elev_body）の材質だけで、道床・まくらぎ・レール・壁・橋脚は今の絵のまま。
材質は描き分けの mat_skin（track_sheet が core の named_materials で入れる）で名前ごと差し替える。

アドオンのディレクトリで:

    AMI_SURFACE=<段> python -X utf8 ../../tools/blender/render_parallel.py --entry blender/surface_calib.py <対象 ...>   # 描く（対象は TARGETS）
    python -X utf8 blender/surface_calib.py      # 描いた後: dat を書き、rounds/ami_surface_calib.pak を作る（Blender を使わない）

描いた絵は work/surface/<段>/src/。pak には段ごとに、8 版の way を <元の名前>_surf<段> の名前で入れる（壁・橋脚は入れない。
見本は dist/ami.pak の壁・橋脚を重ねる）。段 0 は今の版で、描かずに src/ の絵を _surf0 の名前で入れる。

段 2（継ぎ目なし）をユーザーが選び、render.py の TRACK_MAT_SKIN に入れた（2026-11-21）。この入口は、対象の描き分けの mat_skin を
段の表に置き換えて描く（段 0 は差し替えなしの一色）。pak の段 0 は src/ の絵を写すので、段 2 を入れた後に pak を作り直すと段 0 が段 2 の絵になる。
決める前の段 0 は、コミット済みの rounds/ami_surface_calib.pak にある。

段（どれも灰色のまま。坂の測り方 slope_measure.py がレールを「赤 − 青」、地面を緑で見分けるため色みを足さない）:
    0  今の版: 一色（基盤 0.50、躯体 0.56）
    1  まだら: 色を中心に ±12% のまだら（粒は約 4px）。道路一式のコンクリート（render.py の ROAD_CONCRETE）と同じ振れ幅
    2  1 + 汚れ: 大きなしみ（約 30px）で最大 15% 暗くする
    3  2 を強く: まだら ±20%、しみ 25%
    j  2 + 継ぎ目: タイルの 1/4 と 3/4 の所に、縦横の暗い線（幅約 1px）。床の板の継ぎ目と躯体の縦の目地
模様は、タイルの辺で必ずつながるように、タイルの 1 辺を周期にした 4 次元のノイズ（x・y をそれぞれ円に巻く）で作る。
見比べたとき（コミット済みの rounds/ami_surface_calib.pak）の模様は高さ方向に変わらなかった（縦の面が縦の筋になる）。本番に入れるとき、
橋の端の坂の躯体（大きな縦の面）で縦の縞に見えたので、高さも模様に入れた（sheetlib の tiled_concrete_material）。今この入口で描くと、高さを入れた模様になる。
"""
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
WORK_DIR = os.path.join(ROOT, "work", "surface")
TRACK = "ami_rail_ballast"
VARIANTS = ("single", "back", "center", "front")
TARGETS = [f"{TRACK}_{k}_{v}" for k in ("base", "elev") for v in VARIANTS]

# 段 → (まだらの振れ幅, まだらの粒の細かさ〔部品の座標 1 単位あたり。1 単位 ≈ 9px〕, しみの濃さ, しみの細かさ, 継ぎ目)
STEPS = {
    "1": (0.12, 2.5, 0.0, 0.35, False),
    "2": (0.12, 2.5, 0.15, 0.35, False),
    "3": (0.20, 2.5, 0.25, 0.35, False),
    "j": (0.12, 2.5, 0.15, 0.35, True),
}
JOINT_PERIOD = 5.0   # 継ぎ目の間隔（タイルの 1 辺 10 の半分。タイルの辺には置かず、±2.5 の所）
JOINT_W = 0.10       # 継ぎ目の幅（約 1px）
JOINT_DARK = 0.70    # 継ぎ目の色の倍率
STEP_NAMES = ["0", *STEPS]


def surf_name(name, step):
    return f"{name}_surf{step}"


def _concrete(R, name, rgb, step):
    """段 step のコンクリートの材質を返す関数（named_materials の表に入れる）。作りは sheetlib の tiled_concrete_material"""
    amp, grain, stain, stain_scale, joint = STEPS[step]
    return lambda: R.tiled_concrete_material(f"ami_surf{step}_{name}", rgb, amp, grain, stain, stain_scale,
                                             (JOINT_PERIOD, JOINT_W, JOINT_DARK) if joint else None)


def _render():
    import render  # noqa: E402  AMI の描き分けを登録する（render.py は __main__ でないので描かない）
    import sheetlib as R  # noqa: E402
    import sheetlib.cells as C  # noqa: E402
    import sheetlib.core as K  # noqa: E402
    import sheetlib.sheetlib as S  # noqa: E402

    step = os.environ["AMI_SURFACE"]
    table = {} if step == "0" else {spec[0]: _concrete(R, spec[0], spec[1], step) for spec in (R._M_BASE, R._M_ELEV_BODY)}
    out = os.path.join(WORK_DIR, step)
    S.SRC = os.path.join(out, "src")
    for m in (K, C, S):  # 一時ファイルも段ごとに分ける（同じ対象を別の段で同時に描くため）
        m.WORK = os.path.join(out, "tmp")
    os.makedirs(K.WORK, exist_ok=True)

    for t in TARGETS:  # 描き分けの mat_skin（render.py の TRACK_MAT_SKIN）を段の表に置き換える（track_sheet が描くあいだだけ入れる）
        R.TRACK_PROFILES[t.removeprefix("ami_")]["mat_skin"] = table or None
    R.run_targets({t: render.SHEETS[t] for t in TARGETS}, TARGETS)


def _pack():
    """描いた段のシートから dat を書き、rounds/ami_surface_calib.pak を作る（段 0 は src/ の絵）。"""
    pak_src = os.path.join(WORK_DIR, "pak_src")
    shutil.rmtree(pak_src, ignore_errors=True)
    os.makedirs(pak_src)
    names = []
    for step in STEP_NAMES:
        for t in TARGETS:
            png = os.path.join(ROOT, "src", t + ".png") if step == "0" else os.path.join(WORK_DIR, step, "src", t + ".png")
            if not os.path.exists(png):
                sys.exit(f"[surface] {png} が無い（先に描く）")
            new = surf_name(t, step)
            shutil.copy(png, os.path.join(pak_src, new + ".png"))
            with open(os.path.join(ROOT, "src", t + ".dat"), encoding="utf8") as f:
                dat = f.read()
            with open(os.path.join(pak_src, new + ".dat"), "w", encoding="utf8", newline="\n") as f:
                f.write(re.sub(rf"\b{t}\b", new, dat))
            names.append(new + ".dat")
    os.makedirs(os.path.join(ROOT, "rounds"), exist_ok=True)
    out = os.path.join(ROOT, "rounds", "ami_surface_calib.pak")
    r = subprocess.run(["makeobj", "pak256", out, *names], cwd=pak_src, capture_output=True, text=True,
                       encoding="utf8", errors="replace")
    text = r.stdout + r.stderr
    if r.returncode != 0 or any("warning" in l.lower() or "error" in l.lower() for l in text.splitlines()):
        print(text)
        sys.exit("[surface] makeobj が失敗か警告あり")
    print(f"[surface] {out}: {len(names)} dat")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        _pack()
    else:
        sys.path.insert(0, _HERE)
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
        _render()
