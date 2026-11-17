"""AMI の pak を作る（アドオンのディレクトリで `python -X utf8 build.py`）。

src/ の dat から、全部入りのまとめ（dist/ami.pak）と、種類別の pak を makeobj で作る:
    dist/ami_rail.pak   線路（ami_rail_*）
    dist/ami_tram.pak   路面軌道（ami_tram*）
    dist/ami_road.pak   道路（ami_road_*）
    dist/ami_extra.pak  付属（壁・橋脚・歩道: ami_wall_*・ami_pier_*・ami_sidewalk*）
dat が 1 つも無い種類の pak は作らない。makeobj の出力に WARNING か ERROR があれば、出力を見せて 1 で終わる（ACCEPTANCE 1-5）。
dat は先に blender/ami_dat.py で書き出す。画像（シート）は blender/render.py で描く。
SHEET_LAYOUT=1 を付けると、work/layout/ のシートと dat から work/layout/dist/ に作る（レイアウト検証用モード。ADR 0005）。
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# SHEET_LAYOUT=1 のときは、レイアウト検証用モードのシートと dat（render.py が work/layout/ に書く）から、
# work/layout/dist/ に pak を作る（ゲームで部品の配置と接合を見るため。src/・dist/ は変えない）
LAYOUT = os.environ.get("SHEET_LAYOUT") == "1"
SRC = os.path.join(HERE, "work", "layout") if LAYOUT else os.path.join(HERE, "src")
DIST = os.path.join(SRC, "dist") if LAYOUT else os.path.join(HERE, "dist")
PAKSET = "pak256"  # 256px のセルとして切り出す（ゲームは pak128）。iss・blender-poc と同じ

KINDS = {
    "ami_rail.pak": ("ami_rail_",),
    "ami_tram.pak": ("ami_tram",),
    "ami_road.pak": ("ami_road_",),
    "ami_extra.pak": ("ami_wall_", "ami_pier_", "ami_sidewalk"),
}


def makeobj(out, dats):
    cmd = ["makeobj", PAKSET, os.path.join(DIST, out)] + [os.path.basename(d) for d in dats]
    r = subprocess.run(cmd, cwd=SRC, capture_output=True, text=True, encoding="utf8", errors="replace")
    text = r.stdout + r.stderr
    bad = [l for l in text.splitlines() if "warning" in l.lower() or "error" in l.lower()]
    if r.returncode != 0 or bad:
        print(text)
        sys.exit(f"[build] {out}: makeobj が失敗か警告あり")
    print(f"[build] {out}: {len(dats)} dat")


def main():
    os.makedirs(DIST, exist_ok=True)
    dats = sorted(glob.glob(os.path.join(SRC, "ami_*.dat")))
    if not dats:
        sys.exit("[build] src/ に ami_*.dat が無い（先に blender/ami_dat.py）")
    makeobj("ami.pak", dats)
    for out, prefixes in KINDS.items():
        part = [d for d in dats if os.path.basename(d).startswith(prefixes)]
        if part:
            makeobj(out, part)


if __name__ == "__main__":
    main()
