"""AMI の pak を作る（アドオンのディレクトリで `python -X utf8 build.py`）。

src/ の dat から、全部入りのまとめ（dist/ami.pak）と、種類別の pak を makeobj で作る:
    dist/ami_rail.pak   線路（ami_rail_*）
    dist/ami_tram.pak   路面軌道（ami_tram*）
    dist/ami_road.pak   道路（ami_road_*）
    dist/ami_extra.pak  付属（壁・橋脚・歩道: ami_wall_*・ami_pier_*・ami_sidewalk*）
dat が 1 つも無い種類の pak は作らない。makeobj の出力に WARNING か ERROR があれば、出力を見せて 1 で終わる（ACCEPTANCE 1-5）。
作った後、分岐の追加画像（Y字分岐・三方分岐。絵の番号 26〜35）を継ぎ足す: src/ex_donors.dat（blender/ami_dat.py が書く提供用の物）を
work/ex/donors.pak に作り、ex_graft.py で dist/ の各 pak の対象の物（線路・路面軌道の way と架線つきの壁）へ写す。提供用の物は dist/ に入らない。
dat は先に blender/ami_dat.py で書き出す。画像（シート）は blender/render.py で描く。
SHEET_LAYOUT=1 を付けると、work/layout/ のシートと dat から work/layout/dist/ に作る（レイアウト検証用モード。ADR 0005）。
"""
import glob
import os
import subprocess
import sys

import ex_graft

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


EX_DONORS = "ex_donors.dat"  # blender/ami_dat.py の EX_DONORS_DAT
EX_WORK = os.path.join(SRC, "dist", "ex") if LAYOUT else os.path.join(HERE, "work", "ex")


def makeobj(out, dats, dist=DIST):
    cmd = ["makeobj", PAKSET, os.path.join(dist, out)] + [os.path.basename(d) for d in dats]
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
    outs = ["ami.pak"]
    for out, prefixes in KINDS.items():
        part = [d for d in dats if os.path.basename(d).startswith(prefixes)]
        if part:
            makeobj(out, part)
            outs.append(out)
    graft_ex(outs)


def graft_ex(outs):
    """分岐の追加画像を継ぎ足す。pak ごとに、名前で当たる提供用の物が全部写ったことと、継ぎ足した絵の中身（ex_graft.check_ex）を確かめる"""
    donors_dat = os.path.join(SRC, EX_DONORS)
    if not os.path.exists(donors_dat):
        sys.exit(f"[build] {donors_dat} が無い（先に blender/ami_dat.py）")
    os.makedirs(EX_WORK, exist_ok=True)
    makeobj("donors.pak", [donors_dat], dist=EX_WORK)
    _, root = ex_graft.read_pak(os.path.join(EX_WORK, "donors.pak"))
    donors = {n: node for n, node in ex_graft.objects(root).items() if n.endswith(ex_graft.DONOR_SUFFIX)}
    for out in outs:
        path = os.path.join(DIST, out)
        done = ex_graft.graft(path, donors)
        print(f"[build] {out}: 分岐の追加画像を {len(done)} 個に継ぎ足した")
        prefixes = KINDS.get(out, ("",))  # ami.pak は全部
        want = [n for n in donors if n.startswith(prefixes)]
        if len(done) != len(want):
            sys.exit(f"[build] {out}: 継ぎ足す対象 {len(want)} 個のうち {len(done)} 個にしか継ぎ足せなかった")
        problems = ex_graft.check_ex(path)
        if problems:
            sys.exit(f"[build] {out}: 継ぎ足した絵がおかしい\n" + "\n".join(problems))


if __name__ == "__main__":
    main()
