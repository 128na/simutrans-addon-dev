"""AMI の pak を作る（アドオンのディレクトリで `python -X utf8 build.py`）。

src/ の dat から、全部入りのまとめ（dist/ami.pak）と、種類別の pak を makeobj で作る:
    dist/ami_rail.pak   線路（ami_rail_*。車庫 ami_rail_depot を含む。路面軌道・道路の車庫も同じく種類の pak に入る）
    dist/ami_tram.pak   路面軌道（ami_tram*）
    dist/ami_road.pak   道路（ami_road_*。多車線と交差点の路面表示 ami_mark_* も入る）
    dist/ami_monorail.pak モノレール（ami_monorail*。跨座式の way・高架・トンネル、懸垂式の way・高架、電化と車庫 ami_monorail_depot）
    dist/ami_canal.pak    運河（ami_canal*。地上の way と船の車庫 ami_canal_depot）
    dist/ami_extra.pak  付属（壁・橋脚・歩道・歩道の柵・踏切: ami_wall_*（歩道の柵 ami_wall_sidewalk_* と柵つきの電柱を含む）・ami_pier_*・ami_sidewalk*（電柱 ami_sidewalk_pole_* を含む）・ami_crossing_*）
    dist/ami_scenery.pak 景観（盛土・道路標識: ami_embankment_*・ami_sign_*）
    dist/ami_rail_old.pak 旧描画位置（SIS に合う）の線路と、その壁・架線・橋脚（catalog.is_old。#26・ADR 0011）。全部入りの ami.pak と、上の種類別の pak には入らない
dat が 1 つも無い種類の pak は作らない。makeobj の出力に WARNING か ERROR があれば、出力を見せて 1 で終わる（ACCEPTANCE 1-5）。
作った後、分岐の追加画像（Y字分岐・三方分岐。絵の番号 26〜35）を継ぎ足す: src/ex_donors.dat（blender/ami_dat.py が書く提供用の物）を
work/ex/donors.pak に作り、ex_graft.py で dist/ の各 pak の対象の物（線路・路面軌道の way と架線つきの壁）へ写す。提供用の物は dist/ に入らない。
dat は先に blender/ami_dat.py で書き出す。画像（シート）は blender/render.py で描く。
環境変数 SHEET_PAK_SIZE=256 を付けると、256 の pak を src256/ の dat・シートから dist256/ に作る（#266。makeobj の大きさは pak512。
catalog.SCALED_SHEETS の物だけ。分岐の追加画像の継ぎ足しはしない）。pak128 の src/・dist/ には触れない。
BUILD_SKIP_MISSING=1 を付けると、絵のシート（PNG）が無い dat を組まない（256 の PNG は生活道路だけをコミットするので、CI はこれで絵のある物だけを組む。#261）。
--stage-sheeted <フォルダ> は、絵のシートが全部ある dat とそのシートをフォルダにコピーして終わる（check.sh の 256 の dat_linter 用）。
SHEET_LAYOUT=1 を付けると、work/layout/ のシートと dat から work/layout/dist/ に作る（レイアウト検証用モード。ADR 0005）。
"""
import glob
import os
import re
import shutil
import subprocess
import sys

import ex_graft

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "blender"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "blender"))
import catalog  # noqa: E402
import sheet_settings  # noqa: E402  pak の大きさ（SHEET_PAK_SIZE。既定は pak128）
# SHEET_LAYOUT=1 のときは、レイアウト検証用モードのシートと dat（render.py が work/layout/ に書く）から、
# work/layout/dist/ に pak を作る（ゲームで部品の配置と接合を見るため。src/・dist/ は変えない）
LAYOUT = os.environ.get("SHEET_LAYOUT") == "1"
SRC = os.path.join(HERE, "work", "layout") if LAYOUT else os.path.join(HERE, "src" + sheet_settings.SUFFIX)
DIST = os.path.join(SRC, "dist") if LAYOUT else os.path.join(HERE, "dist" + sheet_settings.SUFFIX)
PAKSET = sheet_settings.PAKSET  # セルの一辺（pak128 のゲームは 256px のセルとして切り出す = pak256。iss・blender-poc と同じ。256 の pak は pak512）

KINDS = {
    "ami_rail.pak": ("ami_rail_",),
    "ami_tram.pak": ("ami_tram",),
    "ami_road.pak": ("ami_road_", "ami_mark_"),  # 路面表示（#187）は道路と組で使うので道路に入れる
    "ami_monorail.pak": ("ami_monorail",),  # 跨座式（#113。ADR 0008）・懸垂式（#116）のモノレールと電化。車庫 ami_monorail_depot も入る
    "ami_canal.pak": ("ami_canal",),  # 運河（#114。ADR 0008）。船の車庫 ami_canal_depot も入る
    "ami_extra.pak": ("ami_wall_", "ami_pier_", "ami_sidewalk", "ami_crossing_"),  # 踏切（#111）は線路・道路と組で使うので付属に入れる
    "ami_scenery.pak": ("ami_embankment_", "ami_sign_"),  # 景観（ADR 0008。盛土 #123・道路標識 #122）
    "ami_rail_old.pak": (),  # 旧描画位置の線路・壁・架線・橋脚（#26。ADR 0011）。名前の頭でなく catalog.is_old で決める（belongs）
}
OLD_PAK = "ami_rail_old.pak"


def belongs(pak, name):
    """物 name（dat の名前）が pak に入るか。旧描画位置の物（catalog.is_old）は ami_rail_old.pak だけに入り、全部入りの ami.pak と
    種類別の pak（名前の頭 KINDS）には入らない。pak は拡張子付き（ami.pak は全部入り）"""
    if pak == OLD_PAK:
        return catalog.is_old(name)
    if catalog.is_old(name):
        return False
    return pak == "ami.pak" or name.startswith(KINDS[pak])


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


def sheet_names(dat):
    """dat が指す絵のシートの名前（`<シート>.<行>.<列>` の <シート>）"""
    with open(dat, encoding="utf8") as f:
        return set(re.findall(r"=\s*>?\s*([A-Za-z0-9_\-]+)\.\d+\.\d+", f.read()))


def has_sheets(dat):
    """dat が指す絵のシート（<シート>.png）が、全部 SRC にあるか"""
    return all(os.path.exists(os.path.join(SRC, n + ".png")) for n in sheet_names(dat))


def stage_sheeted(dest):
    """絵のシートが全部ある dat と、そのシートを dest にコピーする（check.sh が 256 の dat_linter を絵のある物だけに掛けるため。#261）"""
    os.makedirs(dest, exist_ok=True)
    n = 0
    for dat in sorted(glob.glob(os.path.join(SRC, "ami_*.dat"))):
        if not has_sheets(dat):
            continue
        for src in [dat] + [os.path.join(SRC, n + ".png") for n in sheet_names(dat)]:
            shutil.copy(src, os.path.join(dest, os.path.basename(src)))
        n += 1
    print(f"[build] シートのある dat {n} 個を {dest} にコピーした")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--stage-sheeted":
        stage_sheeted(sys.argv[2])
        return
    os.makedirs(DIST, exist_ok=True)
    dats = sorted(glob.glob(os.path.join(SRC, "ami_*.dat")))
    if os.environ.get("BUILD_SKIP_MISSING"):
        # 256 の PNG は dat と生活道路だけをコミットする（#261）ので、CI は絵のある物だけを組む。全部のシートを描いた手元では付けない
        n = len(dats)
        dats = [d for d in dats if has_sheets(d)]
        print(f"[build] BUILD_SKIP_MISSING: シートの無い {n - len(dats)} 個の dat は組まない")
    if not dats:
        sys.exit("[build] src/ に ami_*.dat が無い（先に blender/ami_dat.py）")
    stem = lambda d: os.path.splitext(os.path.basename(d))[0]
    makeobj("ami.pak", [d for d in dats if belongs("ami.pak", stem(d))])
    outs = ["ami.pak"]
    for out in KINDS:
        part = [d for d in dats if belongs(out, stem(d))]
        if part:
            makeobj(out, part)
            outs.append(out)
    if sheet_settings.SCALE == 1:  # 分岐の追加画像は線路・路面軌道の物の継ぎ足し。pak128 以外の大きさにはまだ無い（#261）
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
        want = [n for n in donors if belongs(out, n[:-len(ex_graft.DONOR_SUFFIX)])]
        if len(done) != len(want):
            sys.exit(f"[build] {out}: 継ぎ足す対象 {len(want)} 個のうち {len(done)} 個にしか継ぎ足せなかった")
        problems = ex_graft.check_ex(path)
        if problems:
            sys.exit(f"[build] {out}: 継ぎ足した絵がおかしい\n" + "\n".join(problems))


if __name__ == "__main__":
    main()
