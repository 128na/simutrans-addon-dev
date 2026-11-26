"""AMI の配る zip を作る（アドオンのディレクトリで。先に `python -X utf8 build.py` で dist/ を作っておく）。

    python -X utf8 release.py --version beta.1 --paks ami_rail ami_road ami_tram ami_extra
    （第 2 弾の景観を入れるときは ami_scenery、モノレール・運河・狭軌を入れるときは ami_monorail・ami_canal・ami_narrow も並べる。#123・#113・#114・#370）

zip（work/release/ami-<版>.zip）の中身:
    pak128/<pak>.pak   --paks で選んだ dist/ の pak（名前は拡張子なし）。ゲームの addons/ に展開すると addons/pak128/ に入る
    ami_readme.txt     release/readme.txt の {version} を版の名前に置き換えたもの（遊ぶ人向けの簡潔な説明・導入方法・注意点。#137）
    ami_license.txt    release/license.txt（CC BY 4.0 と帰属）
    ami_lineup.txt     --paks で選んだ pak に入る物の一覧。src/ の dat から lineup.py が作る（#138）
    thumbnail.png      docs/thumbnail/thumbnail.png があれば入れる（#96）
    pak128/text/ja_ami.tab  release/text/ja_ami.tab（日本語の名前。今は道路標識の 6 種。#122）。ゲームの addons/pak128/text/ に入り、
                       本体はファイル名の先頭 2 文字で言語を決める（dataobj/translator.cc）。読んでいない pak の物の訳は使われないだけ
pak の名前が dist/ に無いとき、--paks に ami（全部入り）と種類別を混ぜたとき（同じ物を二重に読む）は止まる。
展開した中身を ingame/beta_check.sh の PAKS に渡すと、配る形のままゲームで確かめられる（--extract で work/release/ami-<版>/ にも展開する）。

環境変数 SHEET_PAK_SIZE=256 を付けると、dist256/（build.py が作る 256 の pak）から、pak だけを入れた zip（work/release/ami-256-<版>.zip）を作る（#266）。
pak は zip の直下に置く（pak256 の fetch_ami.py は zip の中の .pak を全部取る）。readme・許諾・一覧・訳・サムネイルは入れない
（許諾は pak256 が addons/ami/release/license.txt の写しを持つ）。--readme・--no-thumbnail は無視する。pak128 の zip とは名前が違うので混ざらない。

readme の元に固定の版名（beta.3・ami-beta.3.zip・alpha.1 など）が書いてあると止まる（#345）。版ごとの変更は Release の説明に書き、
readme には {version} だけを書く（#341）。python -X utf8 release.py --check で release/readme*.txt を全部確かめる（check.sh。--self-test は検出の確かめ）。
"""
import argparse
import glob
import os
import re
import shutil
import sys
import tempfile
import zipfile

import lineup

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools", "blender"))
import sheet_settings  # noqa: E402  pak の大きさ（SHEET_PAK_SIZE。既定は pak128）

DIST = os.path.join(HERE, "dist" + sheet_settings.SUFFIX)
OUT = os.path.join(HERE, "work", "release")
TEMPLATE = os.path.join(HERE, "release")
TEXTS = os.path.join(TEMPLATE, "text")
THUMBNAIL = os.path.join(HERE, "docs", "thumbnail", "thumbnail.png")
KINDS = ("ami_rail", "ami_road", "ami_tram", "ami_monorail", "ami_canal", "ami_narrow", "ami_extra", "ami_scenery", "ami_rail_old")  # build.py の KINDS と同じ
# 固定の版名（版は beta.<n>・タグは ami-beta.<n>。256 の試しは alpha.<n>。README の「配る形」）。前が英数字なら版名ではない
FIXED_VERSION = re.compile(r"(?<![A-Za-z0-9])(?:alpha|beta)\.\d+", re.IGNORECASE)


def fixed_versions(text):
    """readme の元の中の固定の版名を (行番号, 行) で返す。{version} の置き換えの記号は版名に当たらない"""
    return [(n, line.strip()) for n, line in enumerate(text.splitlines(), 1) if FIXED_VERSION.search(line)]


def check_readme(path):
    """readme の元に固定の版名があれば、場所を出して止まる（#345）"""
    with open(path, encoding="utf8") as f:
        hits = fixed_versions(f.read())
    if hits:
        where = "\n".join(f"  {path}:{n}: {line}" for n, line in hits)
        sys.exit(f"[release] readme に固定の版名がある（版ごとの変更は Release の説明に書き、readme は {{version}} だけにする。#341）:\n{where}")


def self_test():
    """固定の版名を見つけるか、置き換えの記号や版名でない語を見逃すか、配る zip を組む経路で止まるかを確かめる"""
    bad = ["ami-beta.3 からの変更", "ami-beta.3.zip を消してから", "beta.3-old の zip", "（beta.12）", "alpha.1", "Beta.3 からの変更"]
    good = ["AMI（AI Marunage Infrastructure）{version}", "ami-{version}.zip", "beta 版", "alphabeta.3", "pak128.japan", "v1.2"]
    errors = [s for s in bad if not fixed_versions(s)] + [s for s in good if fixed_versions(s)]
    # 組む経路: 版名入りの readme なら、pak を探す前に止まる（無い pak の名前を渡しても readme の件で止まる）。
    # 256 の zip は readme を入れないので、この確かめは pak128 のときだけ
    if sheet_settings.SCALE != 1:
        sys.exit("[release] --self-test は SHEET_PAK_SIZE を付けずに流す")
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "readme.txt")
        with open(path, "w", encoding="utf8") as f:
            f.write("AMI {version}\n## ami-beta.3 からの変更\n")
        try:
            main(["--version", "selftest", "--paks", "no_such_pak", "--readme", path])
            errors.append("版名入りの readme で main が止まらない")
        except SystemExit as e:
            if "固定の版名" not in str(e.code):
                errors.append(f"版名入りの readme で main が別の理由で止まった: {e.code}")
    if errors:
        sys.exit("[release] self-test 失敗: " + " / ".join(errors))
    print(f"[release] self-test ok（見つける {len(bad)}・見逃す {len(good)}・組む経路で止まる）")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", help="版の名前（zip の名前と readme に入る）")
    ap.add_argument("--paks", nargs="+", help="入れる dist/ の pak の名前（拡張子なし）")
    ap.add_argument("--readme", default=os.path.join(TEMPLATE, "readme.txt"), help="readme の元（既定 release/readme.txt。旧描画位置の zip は release/readme_old.txt）")
    ap.add_argument("--no-thumbnail", action="store_true", help="thumbnail.png を入れない")
    ap.add_argument("--extract", action="store_true", help="work/release/ami-<版>/ にも展開する")
    ap.add_argument("--check", action="store_true", help="release/readme*.txt に固定の版名が無いかだけを確かめる（check.sh）")
    ap.add_argument("--self-test", action="store_true", help="固定の版名の検出を確かめる")
    a = ap.parse_args(argv)

    if a.self_test:
        self_test()
        return
    if a.check:
        readmes = sorted(glob.glob(os.path.join(TEMPLATE, "readme*.txt")))
        if not readmes:
            sys.exit(f"[release] {TEMPLATE} に readme*.txt が無い")
        for path in readmes:
            check_readme(path)
        print(f"[release] readme に固定の版名なし（{len(readmes)} 個）")
        return
    if not a.version or not a.paks:
        ap.error("--version と --paks が要る")

    scaled = sheet_settings.SCALE != 1  # pak128 以外の大きさ: pak だけの zip（#266）
    if not scaled:
        check_readme(a.readme)  # pak を作り直す前に気づけるよう、pak を探すより先に見る
    if "ami" in a.paks and any(p in KINDS and p != "ami_rail_old" for p in a.paks):  # 旧描画位置（#26）の pak は ami に入らないので、一緒に入れてよい
        sys.exit("[release] 全部入りの ami と種類別の pak を同時に入れると、同じ物を二重に読む")
    paks = []
    for p in a.paks:
        path = os.path.join(DIST, p + ".pak")
        if not os.path.isfile(path):
            sys.exit(f"[release] {path} が無い（先に build.py）")
        paks.append(path)

    name =f"ami-{sheet_settings.PAK_SIZE}-{a.version}" if scaled else f"ami-{a.version}"
    os.makedirs(OUT, exist_ok=True)
    zpath = os.path.join(OUT, name + ".zip")
    if scaled:
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for path in paks:
                z.write(path, os.path.basename(path))
    else:
        write_full_zip(zpath, a, paks)
    with zipfile.ZipFile(zpath) as z:
        for i in z.infolist():
            print(f"[release] {i.filename}  {i.file_size:,} B")
    print(f"[release] {zpath}  {os.path.getsize(zpath):,} B")

    if a.extract:
        dst = os.path.join(OUT, name)
        shutil.rmtree(dst, ignore_errors=True)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(dst)
        print(f"[release] 展開した: {dst}")


def write_full_zip(zpath, a, paks):
    """pak128 の配る zip（pak・readme・許諾・一覧・訳・サムネイル）を書く"""
    with open(a.readme, encoding="utf8") as f:
        readme = f.read().replace("{version}", a.version)
    try:
        listing = lineup.lineup(a.paks, a.version)
    except ValueError as err:
        sys.exit(f"[release] 一覧を作れない: {err}")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for path in paks:
            z.write(path, "pak128/" + os.path.basename(path))
        # Windows のメモ帳でも読めるよう、改行は CRLF・UTF-8（BOM つき）にする
        z.writestr("ami_readme.txt", "﻿" + readme.replace("\r\n", "\n").replace("\n", "\r\n"))
        with open(os.path.join(TEMPLATE, "license.txt"), encoding="utf8") as f:
            z.writestr("ami_license.txt", "﻿" + f.read().replace("\r\n", "\n").replace("\n", "\r\n"))
        z.writestr("ami_lineup.txt", "﻿" + listing.replace("\r\n", "\n").replace("\n", "\r\n"))
        for t in sorted(os.listdir(TEXTS)) if os.path.isdir(TEXTS) else ():  # 訳は手を加えずそのまま（先頭の § を残す）
            z.write(os.path.join(TEXTS, t), "pak128/text/" + t)
        if os.path.isfile(THUMBNAIL) and not a.no_thumbnail:
            z.write(THUMBNAIL, "thumbnail.png")


if __name__ == "__main__":
    main()
