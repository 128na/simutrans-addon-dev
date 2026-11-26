"""精細化のラウンド（#56）の版を作る。名前は元の名前の末尾に _round<n> を付け、今の版と同じゲームに並べて比べる。

アドオンのディレクトリで:

    python -X utf8 blender/round.py 0     # ラウンド 0（今の src/ をそのまま）の pak を作る（Blender を使わない）
    python -X utf8 blender/round.py <n>   # 描いた絵（work/rounds/round<n>/src/）があれば、それから rounds/ami_round<n>.pak を作り直す

対象は在来線一式（ROUND_TARGETS）。描いた絵は work/rounds/round<n>/src/ に置き、src/・dist/ は変えない。
描かなかったシート（ラウンド 0 の全部、ラウンドで変えない絵）は src/ のものを使う。
dat は src/ のものを写し、ami_ で始まる名前を全部 _round<n> 付きにする（画像の参照・トンネルの way= も）。
ラウンド 8（2026-11-20）で、在来線のラウンド 7 の描き分けを render.py（と共有の sheetlib）に入れた。ラウンド 1〜7 の鍵と、それを描く
関数（_render・_trial_parts）は、入れる前の render.py に重ねる作りで、今の render.py に重ねると二重にかかるので、#351 で外した。
試した葉と決めた値は docs/records/2026-11-20_ami-refine-round<n>.md、外す前の設定と関数は a15b576 のこのファイルにある。
在来線の次のラウンドを回すときは、ほかの系統と同じく今の render.py を土台にした round_<系統>.py（ROUND_SETTINGS と apply）を足し、
FAMILIES の rail_ballast の module に名前を書く（鍵の検査と描く入口は module で分かれるので、ほかは変えなくてよい。今の render.py はまくらぎの形を間隔ごと束ねて作るので、まくらぎの間隔を変えるときは sleeper の部品を作り直す）。

系統（family）: 在来線一式のほかの系統は、環境変数 AMI_FAMILY で選ぶ（FAMILIES。既定は rail_ballast）。
系統ごとの描き分けは blender/round_<系統>.py の ROUND_SETTINGS と apply(cfg, n, R, render)（render.py の設定の上に重ねる）。
module が None の系統（今は rail_ballast）は描き分けの鍵を持たず、描かずに pak を作る（ラウンド 0 など）ことだけができる。
描いた絵は work/rounds/<系統>/round<n>/src/、pak は rounds/ami_<系統>_round<n>.pak（rail_ballast だけは前からの名前のまま）。

    AMI_FAMILY=road4 AMI_ROUND=1sh python -X utf8 ../../tools/blender/render_parallel.py --entry blender/round.py <対象 ...>
    AMI_FAMILY=road4 python -X utf8 blender/round.py 1sh
    AMI_FAMILY=road4 python -X utf8 blender/round.py --targets   # その系統の描く対象を出す
"""
import fnmatch
import importlib
import glob
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)

# 在来線一式の dat（src/ の名前）と、描く対象（render.py の SHEETS の名前）
ROUND_DATS = ("ami_rail_ballast", "ami_rail_ballast_base_*", "ami_rail_ballast_elev_*", "ami_rail_ballast_bridge",
              "ami_rail_ballast_tunnel", "ami_wall_rail_*", "ami_pier_rail", "ami_pier_rail_gate")
ROUND_TARGETS = (["ami_rail_ballast"] + [f"ami_rail_ballast_base_{v}" for v in ("single", "back", "center", "front")]
                 + [f"ami_wall_rail_{v}_catenary" for v in ("single", "back", "center", "front")]
                 + [f"ami_wall_rail_twin_catenary_{v}" for v in ("back", "front")]
                 + [f"ami_rail_ballast_elev_{v}" for v in ("single", "back", "center", "front")]
                 + ["ami_pier_rail", "ami_pier_rail_gate", "ami_rail_ballast_bridge", "ami_rail_ballast_tunnel"])

# 旧描画位置（SIS に合う。#26）の物は、ラウンドの対象にしない（glob の ami_wall_rail_*・ami_rail_slab_* などに合ってしまうため）。catalog.is_old と同じ
_OLD_NAME = re.compile(r"ami_(rail_[a-z]+_old(_|$)|wall_rail_old_|pier_rail_old)")


def _is_old(name):
    return _OLD_NAME.match(name) is not None


# 系統 → pak に入れる dat（src/ の名前。glob）と描く対象（render.py の SHEETS の名前。glob）。
# pak には、見本が _round<n> の名前で引く物を全部入れる（描かなかったシートは src/ のものを写す）。
# 在来線の壁・架線・橋脚は rail_ballast のラウンドで描いた物で、rail_slab の pak には src/ のまま入れる（スラブ軌道の見本 sample.nut が引くため）。
FAMILIES = {
    "rail_ballast": {"dats": ROUND_DATS, "targets": ROUND_TARGETS, "module": None},
    "rail_slab": {"dats": ("ami_rail_slab", "ami_rail_slab_base_*", "ami_rail_slab_elev_*", "ami_rail_slab_bridge",
                           "ami_rail_slab_tunnel", "ami_wall_rail_*", "ami_pier_rail", "ami_pier_rail_gate"),
                  "targets": ("ami_rail_slab", "ami_rail_slab_*"), "module": "round_rail_slab"},
    "tram": {"dats": ("ami_tram",), "targets": ("ami_tram",), "module": "round_tram"},
    "road": {"dats": ("ami_road_*", "ami_wall_road_*", "ami_pier_road", "ami_sidewalk"),
             "targets": ("ami_road_*", "ami_wall_road_*", "ami_pier_road", "ami_sidewalk"), "module": "round_road"},
    # 第 4 弾の物（#256）: 幹線道路・円弧と L 字の道路・Y 字と三方分岐。道路一式（road と同じ対象）に、今の本番を土台にした汚しを重ねる
    "road4": {"dats": ("ami_road_*", "ami_wall_road_*", "ami_pier_road", "ami_sidewalk"),
              "targets": ("ami_road_*", "ami_wall_road_*", "ami_pier_road", "ami_sidewalk"), "module": "round_road4"},
    # 第 3 弾の物（#197）: 路面表示（ami_mark_*）と運河・景観の運河。運河の踏切のシートは運河のセルが下地なので、系統に入れない
    "wave3": {"dats": ("ami_mark_*", "ami_canal", "ami_canal_scenic"), "targets": ("ami_mark_*", "ami_canal", "ami_canal_scenic"),
              "module": "round_wave3"},
    # 第 5 弾の物（#331）: 路面の色・黄色の中央線・交差点の中心の印（ami_mark_* の見本が _round<n> で引くので、路面表示は全部 pak に入れる）と
    # 転車台・遷車台。描くのは試す物だけ（ほかの路面表示は src/ のまま）
    "wave5": {"dats": ("ami_mark_*", "ami_rail_turntable"),
              "targets": ("ami_mark_paving_*", "ami_mark_center_yellow", "ami_rail_turntable"), "module": "round_wave5"},
}
FAMILY = os.environ.get("AMI_FAMILY", "rail_ballast")
if FAMILY not in FAMILIES:
    sys.exit(f"[round] AMI_FAMILY は {' '.join(FAMILIES)} のどれか: {FAMILY}")


# module が None の系統の描き分けの鍵（rail_ballast のラウンド 1〜7 は本番に入れたので #351 で外した。上の説明）
ROUND_SETTINGS = {}


def round_dir(n):
    if FAMILY == "rail_ballast":
        return os.path.join(ROOT, "work", "rounds", f"round{n}")
    return os.path.join(ROOT, "work", "rounds", FAMILY, f"round{n}")


def pak_path(n):
    name = f"ami_round{n}.pak" if FAMILY == "rail_ballast" else f"ami_{FAMILY}_round{n}.pak"
    return os.path.join(ROOT, "rounds", name)


def family_targets(names):
    """系統の描く対象（FAMILIES の targets の glob を、render.py の SHEETS の名前 names に当てる。並びは names の順）。"""
    pats = FAMILIES[FAMILY]["targets"]
    return [t for t in names if not _is_old(t) and any(fnmatch.fnmatchcase(t, p) for p in pats)]


def _render_family(n):
    """rail_ballast 以外の系統: blender/round_<系統>.py の apply で render.py の設定に重ねてから描く。"""
    import render  # noqa: E402
    import sheetlib as R  # noqa: E402
    mod = importlib.import_module(FAMILIES[FAMILY]["module"])
    mod.apply(mod.ROUND_SETTINGS[n], n, R, render)
    _run(n, R, render, family_targets(list(render.SHEETS)))


def _run(n, R, render, targets):
    import sheetlib.sheetlib as S  # noqa: E402
    import sheetlib.cells as C  # noqa: E402
    import sheetlib.core as K  # noqa: E402
    S.SRC = os.path.join(round_dir(n), "src")
    # 一時ファイルもラウンドごとに分ける（同じ対象を別のラウンドで同時に描くと、work/ の同じ名前の一時ファイルを取り合う）
    for m in (K, C, S):
        m.WORK = os.path.join(round_dir(n), "tmp")
    os.makedirs(K.WORK, exist_ok=True)
    R.run_targets({k: v for k, v in render.SHEETS.items() if k in targets}, list(targets))


def _graft_ex(out, out_src, suffix, bases):
    """ラウンドの pak に、分岐の追加画像（ex 画像。絵の番号 26〜35）を継ぎ足す（build.py の graft_ex と同じ。#256）。
    src/ex_donors.dat の提供用の物のうち、この pak に入れた物（bases。suffix 抜きの名前）のものだけを、名前に suffix を付けて作る"""
    sys.path.insert(0, ROOT)
    import ex_graft  # noqa: E402
    with open(os.path.join(ROOT, "src", "ex_donors.dat"), encoding="utf8") as f:
        blocks = re.split(r"(?m)^(?=obj=)", f.read())
    keep = []
    for b in blocks:
        m = re.search(r"(?m)^name=(\S+?)__ex_donor\s*$", b)
        if b.startswith("obj=") and m and m[1] in bases:
            keep.append(re.sub(r"\b(ami_[a-z0-9_]+?)(?=\.\d|\b)", lambda mm: mm[1] + suffix, b)
                        .replace("__ex_donor" + suffix, suffix + "__ex_donor"))
    if not keep:
        return 0
    name = "donors_ex.dat"
    with open(os.path.join(out_src, name), "w", encoding="utf8", newline="\n") as f:
        f.write("".join(keep))
    pak = os.path.join(out_src, "donors_ex.pak")
    r = subprocess.run(["makeobj", "pak256", pak, name], cwd=out_src, capture_output=True, text=True, encoding="utf8", errors="replace")
    if r.returncode != 0 or any("warning" in x.lower() or "error" in x.lower() for x in (r.stdout + r.stderr).splitlines()):
        print(r.stdout + r.stderr)
        sys.exit("[round] 提供用の pak が失敗か警告あり")
    _, root = ex_graft.read_pak(pak)
    donors = {n: node for n, node in ex_graft.objects(root).items() if n.endswith(ex_graft.DONOR_SUFFIX)}
    done = ex_graft.graft(out, donors)
    if len(done) != len(donors):
        sys.exit(f"[round] 継ぎ足す対象 {len(donors)} 個のうち {len(done)} 個にしか継ぎ足せなかった")
    return len(done)


def _pack(n):
    suffix = f"_round{n}"
    drawn = os.path.join(round_dir(n), "src")
    out_src = os.path.join(round_dir(n), "pak_src")
    shutil.rmtree(out_src, ignore_errors=True)
    os.makedirs(out_src)
    rename = lambda text: re.sub(r"\b(ami_[a-z0-9_]+?)(?=\.\d|\b)", lambda m: m[1] + suffix, text)
    dats = sorted({p for g in FAMILIES[FAMILY]["dats"] for p in glob.glob(os.path.join(ROOT, "src", g + ".dat"))
                   if not _is_old(os.path.basename(p)[:-4])})
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
        if str(n) == "0" or not os.path.exists(src):
            src = os.path.join(ROOT, "src", s + ".png")
        shutil.copy(src, os.path.join(out_src, s + suffix + ".png"))
    os.makedirs(os.path.join(ROOT, "rounds"), exist_ok=True)
    out = pak_path(n)
    r = subprocess.run(["makeobj", "pak256", out, *names], cwd=out_src, capture_output=True, text=True,
                       encoding="utf8", errors="replace")
    text = r.stdout + r.stderr
    if r.returncode != 0 or any("warning" in line.lower() or "error" in line.lower() for line in text.splitlines()):
        print(text)
        sys.exit(f"[round] makeobj が失敗か警告あり: {out}")
    bases = {nm[:-len(suffix + ".dat")] for nm in names}
    n_ex = _graft_ex(out, out_src, suffix, bases)
    print(f"[round] {out}: {len(names)} dat, {len(sheets)} シート, 分岐の追加画像 {n_ex} 個")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        import argparse
        ap = argparse.ArgumentParser(
            prog="round.py", allow_abbrev=False, description="精細化のラウンドの pak を作る（Blender を使わない）。系統は環境変数 AMI_FAMILY（既定 rail_ballast）。")
        ap.add_argument("rounds", nargs="*", metavar="鍵", help="ラウンドの鍵（ROUND_SETTINGS の鍵。例: 0・1sh）。並べると順に pak を作る")
        ap.add_argument("--targets", action="store_true", help="その系統の描く対象を出す（pak は作らない）")
        args = ap.parse_args()
        if args.targets:
            if args.rounds:
                ap.error("--targets には鍵を渡さない")
            sys.path.insert(0, _HERE)
            names = [os.path.basename(p)[:-4] for p in sorted(glob.glob(os.path.join(ROOT, "src", "*.png")))]
            print(" ".join(ROUND_TARGETS if FAMILY == "rail_ballast" else family_targets(names)))
        else:
            if not args.rounds:
                ap.error("鍵を 1 つ以上渡す")
            bad = [k for k in args.rounds if not re.fullmatch(r"[0-9A-Za-z]+", k)]
            if bad:
                ap.error("鍵の形でない引数: " + " ".join(bad))
            # 綴り違い（abc など）で空の名前の pak を作らない: 系統の ROUND_SETTINGS の鍵、ラウンド 0、描いた絵のあるラウンドだけ受ける
            sys.path.insert(0, _HERE)
            mod = FAMILIES[FAMILY]["module"]
            known = set(ROUND_SETTINGS if mod is None else importlib.import_module(mod).ROUND_SETTINGS)
            unknown = [k for k in args.rounds if k != "0" and k not in known and not os.path.isdir(os.path.join(round_dir(k), "src"))]
            if unknown:
                ap.error(f"系統 {FAMILY} に無いラウンドの鍵: " + " ".join(unknown))
            for key in args.rounds:
                _pack(key)
    else:
        sys.path.insert(0, _HERE)
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
        if FAMILIES[FAMILY]["module"] is None:
            sys.exit(f"[round] {FAMILY} の描き分けの鍵は無い（#351 で外した。冒頭の説明）")
        _render_family(os.environ["AMI_ROUND"])
