"""くどさの物差しを合わせるための、在来線の描き込みの度合いを段階に分けた試作（#56 の C）。

アドオンのディレクトリで、render_parallel.py の入口として動かす:

    python -X utf8 ../../tools/blender/render_parallel.py --entry blender/calib.py ami_rail_ballast_calib0 ...
    python -X utf8 blender/calib.py   # 描いた後: dat を書き、work/calib/ami_calib.pak を作る（Blender を使わない）

通常の版の way（ami_rail_ballast）だけを、段ごとに別の名前で描く。基盤・高架・橋・トンネル・壁は作らない。
出力は work/calib/（src/・dist/ は変えない。build.py が src/ の ami_*.dat を全部 ami.pak に入れるため）。
段 1 は今の版で、描かずに src/ami_rail_ballast.png を ami_rail_ballast_calib1 の名前で入れる（ゲームに入っている ami.pak が
リポジトリの今の版と同じとは限らないため）:
    0  省きすぎ: 汚れ・まくらぎのくすみ・砕石のまだらを除き、道床を一色にする
    2〜4  描き込みすぎ: 砕石のまだらの明暗差と細かさ、汚れの濃さを強め、まくらぎを詰める（段が上がるほど強い）
段は、精細化（#56）を入れる前の render.py の在来線に重ねて作った（2026-11-20）。ラウンド 8 で render.py の在来線の描き分けが変わったので、
今描き直すと物差しを合わせたときの段とは違う絵になる（段 1 も今の src/ になる。まくらぎの形は今の render.py が間隔を束ねて作るので、段 2〜4 のまくらぎの間隔も効かない）。物差しの値は、そのとき撮った work/calib/shots から測る
（docs/reference/way-addon.md の 11 章）
"""
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
CALIB_DIR = os.path.join(ROOT, "work", "calib")
BASE = "ami_rail_ballast"

# 段 → (砕石のまだらの明暗差の倍率, まだらの細かさ, 汚れの色を道床の色から離す倍率, まくらぎの間隔)。
# 今の版（段 1）は (1.0, 6.0, 1.0, 0.62)。段 0 は汚れとまだらを使わない
CALIB_STEPS = {
    2: (1.7, 9.0, 1.4, 0.62),
    3: (2.4, 12.0, 1.8, 0.54),
    4: (3.2, 16.0, 2.2, 0.47),
}
STEP_NAMES = [f"{BASE}_calib{s}" for s in (0, 1, *CALIB_STEPS)]


def _render():
    import render  # noqa: E402  AMI の描き分けを登録する（render.py は __main__ でないので描かない）
    import sheetlib as R  # noqa: E402
    import sheetlib.sheetlib as S  # noqa: E402
    import sheetlib.track_parts as TP  # noqa: E402

    base = R.TRACK_PROFILES[BASE.removeprefix("ami_")]
    sheets = {}

    # 段 0: 汚れを除き（groups から weathering を外す）、道床の材質を差し替えない（一色）
    p0 = dict(base, sheet=f"{BASE}_calib0", groups=tuple(g for g in base["groups"] if g != "weathering"), skin={})
    R.TRACK_PROFILES["calib0"] = p0
    sheets[p0["sheet"]] = lambda: R.track_sheet("calib0")

    mean = R._BALLAST_RGB
    away = lambda c, w: tuple(min(1.0, max(0.0, m + w * (x - m))) for x, m in zip(c, mean))
    for step, (contrast, grain, wear, pitch) in CALIB_STEPS.items():
        tag = f"calib{step}"
        stone = R.track_noise(f"ami_ballast_stone_{tag}", away(render.BALLAST_STONE_LO, contrast),
                              away(render.BALLAST_STONE_HI, contrast), grain)
        replace = dict(base.get("replace", {}))
        for i, (n, (u0, u1), (lo, hi), t, _) in enumerate(R.TRACK_WEAR):
            old = replace.get(n) or next(p for p in R.TRACK_EXTRAS if p.name == n)
            mat = R.track_noise(f"track_{n}_{tag}", away(R._mix(mean, lo, t), wear), away(R._mix(mean, hi, t), wear), 3.0)
            replace[n] = R.Part(n, old.datum, old.width, mat, old.shape, old.group)
        prof = dict(base, sheet=f"{BASE}_{tag}", skin={"ballast": stone}, replace=replace)
        R.TRACK_PROFILES[tag] = prof

        def draw(tag=tag, pitch=pitch):
            TP.SLEEPER_PITCH = pitch  # まくらぎの形は描くときにこの値を読む（1 プロセスで 1 段を描く前提）
            R.track_sheet(tag)
        sheets[prof["sheet"]] = draw

    S.SRC = os.path.join(CALIB_DIR, "src")
    R.run_targets(sheets, list(sheets))


def _pack():
    """描いたシートから dat を書き（ami_rail_ballast.dat の名前を差し替える）、work/calib/ami_calib.pak を作る。"""
    src = os.path.join(CALIB_DIR, "src")
    with open(os.path.join(ROOT, "src", f"{BASE}.dat"), encoding="utf8") as f:
        dat = f.read()
    shutil.copy(os.path.join(ROOT, "src", f"{BASE}.png"), os.path.join(src, f"{BASE}_calib1.png"))
    names = []
    for name in STEP_NAMES:
        if not os.path.exists(os.path.join(src, name + ".png")):
            sys.exit(f"[calib] {name}.png が無い（先に描く）")
        with open(os.path.join(src, name + ".dat"), "w", encoding="utf8", newline="\n") as f:
            f.write(re.sub(rf"\b{BASE}\b", name, dat))
        names.append(name + ".dat")
    out = os.path.join(CALIB_DIR, "ami_calib.pak")
    r = subprocess.run(["makeobj", "pak256", out, *names], cwd=src, capture_output=True, text=True,
                       encoding="utf8", errors="replace")
    text = r.stdout + r.stderr
    if r.returncode != 0 or any("warning" in l.lower() or "error" in l.lower() for l in text.splitlines()):
        print(text)
        sys.exit("[calib] makeobj が失敗か警告あり")
    print(f"[calib] {out}: {len(names)} dat")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        _pack()
    else:
        sys.path.insert(0, _HERE)
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
        _render()
