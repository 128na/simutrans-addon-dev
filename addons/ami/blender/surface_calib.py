"""基盤・高架の面の描き込みの量を、段に分けて見比べる試作（#78）。

在来線の基盤の 4 版・高架の 4 版（ami_rail_ballast_base_<版>・_elev_<版>）だけを、段ごとに別の名前で描く。変えるのは、
基盤の板（材質の名前 base）と高架の躯体（elev_body）の材質だけで、道床・まくらぎ・レール・壁・橋脚は今の絵のまま。
材質は core の named_materials で名前ごと差し替える（src/・dist/・共有の sheetlib は変えない）。

アドオンのディレクトリで:

    AMI_SURFACE=<段> python -X utf8 ../../tools/blender/render_parallel.py --entry blender/surface_calib.py <対象 ...>   # 描く（対象は TARGETS）
    python -X utf8 blender/surface_calib.py      # 描いた後: dat を書き、rounds/ami_surface_calib.pak を作る（Blender を使わない）

描いた絵は work/surface/<段>/src/。pak には段ごとに、8 版の way を <元の名前>_surf<段> の名前で入れる（壁・橋脚は入れない。
見本は dist/ami.pak の壁・橋脚を重ねる）。段 0 は今の版で、描かずに src/ の絵を _surf0 の名前で入れる。

段（どれも灰色のまま。坂の測り方 slope_measure.py がレールを「赤 − 青」、地面を緑で見分けるため色みを足さない）:
    0  今の版: 一色（基盤 0.50、躯体 0.56）
    1  まだら: 色を中心に ±12% のまだら（粒は約 4px）。道路一式のコンクリート（render.py の ROAD_CONCRETE）と同じ振れ幅
    2  1 + 汚れ: 大きなしみ（約 30px）で最大 15% 暗くする
    3  2 を強く: まだら ±20%、しみ 25%
    j  2 + 継ぎ目: タイルの 1/4 と 3/4 の所に、縦横の暗い線（幅約 1px）。床の板の継ぎ目と躯体の縦の目地
模様は、タイルの辺で必ずつながるように、タイルの 1 辺を周期にした 4 次元のノイズ（x・y をそれぞれ円に巻く）で作る。
画面で縦の面（基盤・躯体の側面）は、高さ方向に模様が変わらない（縦の筋になる）。
"""
import math
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
    """段 step のコンクリートの材質を返す関数（named_materials の表に入れる）。"""
    amp, grain, stain, stain_scale, joint = STEPS[step]
    tile = R.TILE

    def make():
        import bpy
        mname = f"ami_surf{step}_{name}"
        if mname in bpy.data.materials:
            return bpy.data.materials[mname]
        m = bpy.data.materials.new(mname)
        m.use_nodes = True
        nt = m.node_tree
        N, L = nt.nodes, nt.links
        bsdf = N["Principled BSDF"]
        bsdf.inputs["Roughness"].default_value = 0.8  # 今の材質（core の material() の既定）と同じ。変えるのは色だけ
        tc = N.new("ShaderNodeTexCoord")
        sep = N.new("ShaderNodeSeparateXYZ")
        L.new(tc.outputs["Object"], sep.inputs["Vector"])

        def math_node(op, a, b=None):
            n = N.new("ShaderNodeMath")
            n.operation = op
            for i, v in enumerate((a, b)):
                if v is None:
                    continue
                if isinstance(v, (int, float)):
                    n.inputs[i].default_value = v
                else:
                    L.new(v, n.inputs[i])
            return n.outputs[0]

        # x・y をタイルの 1 辺を周期に円へ巻く（半径 tile/2π で、ノイズの尺度は部品の座標と同じ）
        rad = tile / (2 * math.pi)
        ang = lambda s: math_node("MULTIPLY", s, 2 * math.pi / tile)
        ax, ay = ang(sep.outputs["X"]), ang(sep.outputs["Y"])
        cx, sx = math_node("MULTIPLY", math_node("COSINE", ax), rad), math_node("MULTIPLY", math_node("SINE", ax), rad)
        cy, sy = math_node("MULTIPLY", math_node("COSINE", ay), rad), math_node("MULTIPLY", math_node("SINE", ay), rad)
        comb = N.new("ShaderNodeCombineXYZ")
        L.new(cx, comb.inputs["X"])
        L.new(sx, comb.inputs["Y"])
        L.new(cy, comb.inputs["Z"])

        def noise(scale, detail):
            n = N.new("ShaderNodeTexNoise")
            n.noise_dimensions = "4D"
            n.inputs["Scale"].default_value = scale
            n.inputs["Detail"].default_value = detail
            L.new(comb.outputs["Vector"], n.inputs["Vector"])
            L.new(sy, n.inputs["W"])
            return n.outputs["Fac"]

        ramp = N.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[0].color = (*(x * (1 - amp) for x in rgb), 1)
        ramp.color_ramp.elements[1].position = 0.65
        ramp.color_ramp.elements[1].color = (*(x * (1 + amp) for x in rgb), 1)
        L.new(noise(grain, 2.0), ramp.inputs["Fac"])
        col = ramp.outputs["Color"]
        # 倍率（しみ・継ぎ目）を掛け合わせる
        k = None
        if stain:
            # しみ: ノイズの値が 0.5 より上の所ほど暗く（0.5 で 1、0.65 で 1 − stain）
            t = math_node("MULTIPLY", math_node("MAXIMUM", math_node("SUBTRACT", noise(stain_scale, 1.0), 0.5), 0.0), 1 / 0.15)
            k = math_node("SUBTRACT", 1.0, math_node("MULTIPLY", math_node("MINIMUM", t, 1.0), stain))
        if joint:
            def line(s):  # s を JOINT_PERIOD で割った余りが ±JOINT_W/2 に入れば 1（±2.5 の所）
                f = math_node("FRACT", math_node("DIVIDE", math_node("ADD", s, JOINT_PERIOD / 2), JOINT_PERIOD))
                d = math_node("MINIMUM", f, math_node("SUBTRACT", 1.0, f))
                return math_node("LESS_THAN", d, JOINT_W / 2 / JOINT_PERIOD)
            on = math_node("MAXIMUM", line(sep.outputs["X"]), line(sep.outputs["Y"]))
            jk = math_node("SUBTRACT", 1.0, math_node("MULTIPLY", on, 1 - JOINT_DARK))
            k = jk if k is None else math_node("MULTIPLY", k, jk)
        if k is not None:
            mix = N.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            kc = N.new("ShaderNodeCombineColor")
            for ch in ("Red", "Green", "Blue"):
                L.new(k, kc.inputs[ch])
            L.new(col, mix.inputs["A"])
            L.new(kc.outputs["Color"], mix.inputs["B"])
            col = mix.outputs["Result"]
        L.new(col, bsdf.inputs["Base Color"])
        return m
    return make


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

    def wrap(draw):
        def run():
            with R.named_materials(table):
                draw()
        return run
    R.run_targets({t: wrap(render.SHEETS[t]) for t in TARGETS}, TARGETS)


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
