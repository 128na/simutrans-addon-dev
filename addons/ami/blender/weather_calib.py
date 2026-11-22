"""汚し（ウェザリング）の案を、モノレールの高架で見比べる試作（#154）。

跨座式・懸垂式の高架の center 版（ami_monorail_straddle_elev_center・ami_monorail_suspended_elev_center）だけを、案ごとに別の名前で描く。
変えるのは桁（mono_beam・mono_top・susp_beam・susp_top）と柱・腕（mono_pier・susp_pier）の材質だけで、形は今のまま。
材質は sheetlib の tiled_concrete_material の汚しの引数（tint・streak・grime）で作る。第 1 弾の物（高架の躯体・橋脚・壁）は変えない。

アドオンのディレクトリで:

    AMI_WEATHER=<案> python -X utf8 ../../tools/blender/render_parallel.py --entry blender/weather_calib.py <対象 ...>   # 描く（対象は TARGETS）
    python -X utf8 blender/weather_calib.py      # 描いた後: dat を書き、rounds/ami_weather_calib.pak を作る（Blender を使わない）

描いた絵は work/weather/<案>/src/。pak には案ごとに、対象を <元の名前>_w<案> の名前で入れる。案 0 は今の版で、描かずに src/ の絵を写す。
見本は ingame/weathering_lineup.nut に SUFFIX=_w<案> を渡して敷く（案の pak に無い物は今の名前で敷く）。

案（どれも灰色のまま。坂の測り方 slope_measure.py がレールを「赤 − 青」、地面を緑で見分けるので、色みは控えめにする）:
    0  今の版: 桁 0.56〜0.64、柱 0.50〜0.58 の 2 色のまだら（タイルの辺で周期にならない track_noise）
    A  色味: 桁・柱の色を少し暖かい灰（赤 +4%、青 −8%）にし、柱を桁より 1 段暗くする（第 1 弾の打ち放しは中性の灰のまま）
    B  雨だれ: 縦の面に縦に長い暗い筋（最大 30% 暗く。横の細かさ 6、縦はその 0.04 倍）
    C  地際の汚れ: 柱の下ほど暗く（地面で 45% 暗く、地面から 3.5 単位で 0）。桁は今の色
A〜C は、まだらを tiled_concrete_material（タイルの 1 辺を周期にした模様）で作り直す。まだらの振れ幅と粒は今の版に合わせる。
"""
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
WORK_DIR = os.path.join(ROOT, "work", "weather")
TARGETS = ["ami_monorail_straddle_elev_center", "ami_monorail_suspended_elev_center"]

BEAM_RGB = (0.60, 0.60, 0.58)   # 今の桁（0.56〜0.64）の中心
PIER_RGB = (0.54, 0.54, 0.52)   # 今の柱（0.50〜0.58）の中心
AMP = 0.067                      # 今のまだらの振れ幅（±0.04 / 0.60）
GRAIN = 4.0                      # 今のまだらの粒（MONO_GRAIN）
WARM = (1.04, 1.00, 0.92)
GRIME_SPAN = 3.5                 # 地際の汚れの高さ（部品の座標。地面から）

# 案 → (桁の汚しの引数, 柱の汚しの引数)。柱の rgb を替えるときは "rgb" に入れる
STEPS = {
    "A": (dict(tint=WARM), dict(tint=WARM, rgb=tuple(x * 0.92 for x in PIER_RGB))),
    "B": (dict(streak=0.30, streak_scale=6.0, streak_stretch=0.04), dict(streak=0.30, streak_scale=6.0, streak_stretch=0.04)),
    "C": ({}, dict(grime=0.45)),
}
STEP_NAMES = ["0", *STEPS]


def weather_name(name, step):
    return f"{name}_w{step}"


def _render():
    import sheetlib as R  # noqa: E402
    import sheetlib.cells as C  # noqa: E402
    import sheetlib.core as K  # noqa: E402
    import sheetlib.sheetlib as S  # noqa: E402
    from sheetlib.wall_parts import ELEV_STEPS, PIER_FOOT  # noqa: E402

    # sheetlib の __init__ が関数 monorail_parts を同じ名前で出すので、`import sheetlib.monorail_parts as MP` だと関数が返る。モジュールは sys.modules から引く
    MP = sys.modules["sheetlib.monorail_parts"]
    step = os.environ["AMI_WEATHER"]
    beam_kw, pier_kw = STEPS[step]
    ground = -ELEV_STEPS * K.H - PIER_FOOT

    def mat(tag, rgb, kw):
        kw = dict(kw)
        rgb = kw.pop("rgb", rgb)
        if kw.get("grime"):
            kw["grime_z"] = (ground, ground + GRIME_SPAN)
        return lambda: K.tiled_concrete_material(f"ami_w{step}_{tag}", rgb, AMP, GRAIN, rough=0.9, **kw)

    # 部品の関数（monorail_parts・suspended_parts・*_pier_fills）は呼ぶときに材質の定数を読むので、render を読む前に差し替える
    MP._M_MONO_BEAM = MP._M_SUSP_BEAM = mat("beam", BEAM_RGB, beam_kw)
    MP._M_MONO_TOP = MP._M_SUSP_TOP = mat("top", BEAM_RGB, beam_kw)
    MP._M_MONO_PIER = MP._M_SUSP_PIER = mat("pier", PIER_RGB, pier_kw)
    import render  # noqa: E402  AMI の描き分けを登録する（render.py は __main__ でないので描かない）

    out = os.path.join(WORK_DIR, step)
    S.SRC = os.path.join(out, "src")
    for m in (K, C, S):  # 一時ファイルも案ごとに分ける（同じ対象を別の案で同時に描くため）
        m.WORK = os.path.join(out, "tmp")
    os.makedirs(K.WORK, exist_ok=True)
    R.run_targets({t: render.SHEETS[t] for t in TARGETS}, TARGETS)


def _pack():
    """描いた案のシートから dat を書き、rounds/ami_weather_calib.pak を作る（案 0 は src/ の絵）。"""
    pak_src = os.path.join(WORK_DIR, "pak_src")
    shutil.rmtree(pak_src, ignore_errors=True)
    os.makedirs(pak_src)
    names = []
    for step in STEP_NAMES:
        for t in TARGETS:
            png = os.path.join(ROOT, "src", t + ".png") if step == "0" else os.path.join(WORK_DIR, step, "src", t + ".png")
            if not os.path.exists(png):
                sys.exit(f"[weather] {png} が無い（先に描く）")
            new = weather_name(t, step)
            shutil.copy(png, os.path.join(pak_src, new + ".png"))
            with open(os.path.join(ROOT, "src", t + ".dat"), encoding="utf8") as f:
                dat = f.read()
            with open(os.path.join(pak_src, new + ".dat"), "w", encoding="utf8", newline="\n") as f:
                f.write(re.sub(rf"\b{t}\b", new, dat))
            names.append(new + ".dat")
    os.makedirs(os.path.join(ROOT, "rounds"), exist_ok=True)
    out = os.path.join(ROOT, "rounds", "ami_weather_calib.pak")
    r = subprocess.run(["makeobj", "pak256", out, *names], cwd=pak_src, capture_output=True, text=True,
                       encoding="utf8", errors="replace")
    text = r.stdout + r.stderr
    if r.returncode != 0 or any("warning" in l.lower() or "error" in l.lower() for l in text.splitlines()):
        print(text)
        sys.exit("[weather] makeobj が失敗か警告あり")
    print(f"[weather] {out}: {len(names)} dat")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        _pack()
    else:
        sys.path.insert(0, _HERE)
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
        _render()
