"""AMI の配る zip を作る（アドオンのディレクトリで。先に `python -X utf8 build.py` で dist/ を作っておく）。

    python -X utf8 release.py --version beta.1 --paks ami_rail ami_road ami_tram ami_extra
    （第 2 弾の景観を入れるときは ami_scenery、モノレール・運河を入れるときは ami_monorail・ami_canal も並べる。#123・#113・#114）

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
"""
import argparse
import os
import shutil
import sys
import zipfile

import lineup

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
OUT = os.path.join(HERE, "work", "release")
TEMPLATE = os.path.join(HERE, "release")
TEXTS = os.path.join(TEMPLATE, "text")
THUMBNAIL = os.path.join(HERE, "docs", "thumbnail", "thumbnail.png")
KINDS = ("ami_rail", "ami_road", "ami_tram", "ami_monorail", "ami_canal", "ami_extra", "ami_scenery", "ami_rail_old")  # build.py の KINDS と同じ


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", required=True, help="版の名前（zip の名前と readme に入る）")
    ap.add_argument("--paks", nargs="+", required=True, help="入れる dist/ の pak の名前（拡張子なし）")
    ap.add_argument("--extract", action="store_true", help="work/release/ami-<版>/ にも展開する")
    a = ap.parse_args()

    if "ami" in a.paks and any(p in KINDS and p != "ami_rail_old" for p in a.paks):  # 旧描画位置（#26）の pak は ami に入らないので、一緒に入れてよい
        sys.exit("[release] 全部入りの ami と種類別の pak を同時に入れると、同じ物を二重に読む")
    paks = []
    for p in a.paks:
        path = os.path.join(DIST, p + ".pak")
        if not os.path.isfile(path):
            sys.exit(f"[release] {path} が無い（先に build.py）")
        paks.append(path)

    name = f"ami-{a.version}"
    os.makedirs(OUT, exist_ok=True)
    zpath = os.path.join(OUT, name + ".zip")
    with open(os.path.join(TEMPLATE, "readme.txt"), encoding="utf8") as f:
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
        if os.path.isfile(THUMBNAIL):
            z.write(THUMBNAIL, "thumbnail.png")
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


if __name__ == "__main__":
    main()
