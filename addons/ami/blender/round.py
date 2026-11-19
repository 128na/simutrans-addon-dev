"""精細化のラウンド（#56）の版を作る。名前は元の名前の末尾に _round<n> を付け、今の版と同じゲームに並べて比べる。

アドオンのディレクトリで:

    AMI_ROUND=1 python -X utf8 ../../tools/blender/render_parallel.py --entry blender/round.py <対象 ...>   # 描く（対象は ROUND_TARGETS）
    python -X utf8 blender/round.py 1     # 描いたシートから dat を書き、rounds/ami_round1.pak を作る（Blender を使わない）
    python -X utf8 blender/round.py 0     # ラウンド 0（今の src/ をそのまま）の pak を作る

対象は在来線一式（ROUND_TARGETS）。描いた絵は work/rounds/round<n>/src/ に置き、src/・dist/ は変えない。
描かなかったシート（ラウンド 0 の全部、ラウンドで変えない絵）は src/ のものを使う。
dat は src/ のものを写し、ami_ で始まる名前を全部 _round<n> 付きにする（画像の参照・トンネルの way= も）。
ラウンドごとの描き分けは ROUND_SETTINGS（render.py の設定の上に重ねる）。
"""
import glob
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
BALLAST = "ami_rail_ballast"

# 在来線一式の dat（src/ の名前）と、描く対象（render.py の SHEETS の名前）
ROUND_DATS = ("ami_rail_ballast", "ami_rail_ballast_base_*", "ami_rail_ballast_elev_*", "ami_rail_ballast_bridge",
              "ami_rail_ballast_tunnel", "ami_wall_rail_*", "ami_pier_rail", "ami_pier_rail_gate")
ROUND_TARGETS = (["ami_rail_ballast"] + [f"ami_rail_ballast_base_{v}" for v in ("single", "back", "center", "front")]
                 + [f"ami_wall_rail_{v}_catenary" for v in ("single", "back", "center", "front")]
                 + [f"ami_wall_rail_twin_catenary_{v}" for v in ("back", "front")]
                 + [f"ami_rail_ballast_elev_{v}" for v in ("single", "back", "center", "front")]
                 + ["ami_pier_rail", "ami_pier_rail_gate", "ami_rail_ballast_bridge", "ami_rail_ballast_tunnel"])

# ラウンド → 描き分け。ballast: 砕石のまだら（明暗差の倍率, 細かさ）。wear: 汚れの色を道床の色から離す倍率。
# sleeper_pitch: まくらぎの間隔。値の決め方は記録 docs/records/ の各ラウンドの記録
ROUND_SETTINGS = {
    1: {"ballast": (2.4, 12.0), "wear": 1.8, "sleeper_pitch": 0.54},
}


def round_dir(n):
    return os.path.join(ROOT, "work", "rounds", f"round{n}")


def _render(n):
    import render  # noqa: E402  AMI の描き分けを登録する（__main__ でないので描かない）
    import sheetlib as R  # noqa: E402
    import sheetlib.sheetlib as S  # noqa: E402
    import sheetlib.track_parts as TP  # noqa: E402

    cfg = ROUND_SETTINGS[n]
    mean = R._BALLAST_RGB
    away = lambda c, w: tuple(min(1.0, max(0.0, m + w * (x - m))) for x, m in zip(c, mean))
    contrast, grain = cfg["ballast"]
    stone = R.track_noise(f"ami_ballast_stone_r{n}", away(render.BALLAST_STONE_LO, contrast),
                          away(render.BALLAST_STONE_HI, contrast), grain)
    wear = {}
    for name, _, (lo, hi), t, _ in R.TRACK_WEAR:
        wear[name] = R.track_noise(f"track_{name}_r{n}", away(R._mix(mean, lo, t), cfg["wear"]),
                                   away(R._mix(mean, hi, t), cfg["wear"]), 3.0)
    # 在来線の道床を使う描き分け（通常・基盤・高架・橋・トンネル・壁と架線の元の基盤）だけを替える。高速線・路面軌道は替えない
    for prof in R.TRACK_PROFILES.values():
        if not str(prof.get("sheet", "")).startswith(BALLAST):
            continue
        prof["skin"] = dict(prof.get("skin", {}), ballast=stone)
        rep = dict(prof.get("replace", {}))
        for name, mat in wear.items():
            old = rep.get(name) or next(p for p in R.TRACK_EXTRAS if p.name == name)
            rep[name] = R.Part(name, old.datum, old.width, mat, old.shape, old.group, centre=False)
        prof["replace"] = rep
    TP.SLEEPER_PITCH = cfg["sleeper_pitch"]  # まくらぎの形は描くときにこの値を読む（render_parallel は対象ごとに別のプロセス）
    S.SRC = os.path.join(round_dir(n), "src")
    R.run_targets({k: v for k, v in render.SHEETS.items() if k in ROUND_TARGETS}, ROUND_TARGETS)


def _pack(n):
    suffix = f"_round{n}"
    drawn = os.path.join(round_dir(n), "src")
    out_src = os.path.join(round_dir(n), "pak_src")
    shutil.rmtree(out_src, ignore_errors=True)
    os.makedirs(out_src)
    rename = lambda text: re.sub(r"\b(ami_[a-z0-9_]+?)(?=\.\d|\b)", lambda m: m[1] + suffix, text)
    dats = sorted({p for g in ROUND_DATS for p in glob.glob(os.path.join(ROOT, "src", g + ".dat"))})
    sheets = set()
    names = []
    for d in dats:
        with open(d, encoding="utf8") as f:
            text = f.read()
        sheets |= set(re.findall(r"=\s*>?\s*(ami_[a-z0-9_]+)\.\d", text))
        base = os.path.basename(d)[:-4] + suffix
        with open(os.path.join(out_src, base + ".dat"), "w", encoding="utf8", newline="\n") as f:
            f.write(rename(text))
        names.append(base + ".dat")
    for s in sorted(sheets):
        src = os.path.join(drawn, s + ".png")
        if n == 0 or not os.path.exists(src):
            src = os.path.join(ROOT, "src", s + ".png")
        shutil.copy(src, os.path.join(out_src, s + suffix + ".png"))
    os.makedirs(os.path.join(ROOT, "rounds"), exist_ok=True)
    out = os.path.join(ROOT, "rounds", f"ami_round{n}.pak")
    r = subprocess.run(["makeobj", "pak256", out, *names], cwd=out_src, capture_output=True, text=True,
                       encoding="utf8", errors="replace")
    text = r.stdout + r.stderr
    if r.returncode != 0 or any("warning" in line.lower() or "error" in line.lower() for line in text.splitlines()):
        print(text)
        sys.exit(f"[round] makeobj が失敗か警告あり: {out}")
    print(f"[round] {out}: {len(names)} dat, {len(sheets)} シート")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        _pack(int(sys.argv[1]))
    else:
        sys.path.insert(0, _HERE)
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
        _render(int(os.environ["AMI_ROUND"]))
