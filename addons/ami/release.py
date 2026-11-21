"""AMI の配る zip を作る（アドオンのディレクトリで。先に `python -X utf8 build.py` で dist/ を作っておく）。

    python -X utf8 release.py --version beta.1 --paks ami_rail ami_road ami_tram ami_extra

zip（work/release/ami-<版>.zip）の中身:
    pak128/<pak>.pak   --paks で選んだ dist/ の pak（名前は拡張子なし）。ゲームの addons/ に展開すると addons/pak128/ に入る
    ami_readme.txt     release/readme.txt の {version} を版の名前に置き換えたもの（遊ぶ人向けの説明・ベータの注意・既知の課題）
    ami_license.txt    release/license.txt（CC BY 4.0 と帰属）
    thumbnail.png      docs/thumbnail.png があれば入れる（#96）
pak の名前が dist/ に無いとき、--paks に ami（全部入り）と種類別を混ぜたとき（同じ物を二重に読む）は止まる。
展開した中身を ingame/beta_check.sh の PAKS に渡すと、配る形のままゲームで確かめられる（--extract で work/release/ami-<版>/ にも展開する）。
"""
import argparse
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
OUT = os.path.join(HERE, "work", "release")
TEMPLATE = os.path.join(HERE, "release")
THUMBNAIL = os.path.join(HERE, "docs", "thumbnail.png")
KINDS = ("ami_rail", "ami_road", "ami_tram", "ami_extra")  # build.py の KINDS と同じ


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", required=True, help="版の名前（zip の名前と readme に入る）")
    ap.add_argument("--paks", nargs="+", required=True, help="入れる dist/ の pak の名前（拡張子なし）")
    ap.add_argument("--extract", action="store_true", help="work/release/ami-<版>/ にも展開する")
    a = ap.parse_args()

    if "ami" in a.paks and any(p in KINDS for p in a.paks):
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
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for path in paks:
            z.write(path, "pak128/" + os.path.basename(path))
        # Windows のメモ帳でも読めるよう、改行は CRLF・UTF-8（BOM つき）にする
        z.writestr("ami_readme.txt", "﻿" + readme.replace("\r\n", "\n").replace("\n", "\r\n"))
        with open(os.path.join(TEMPLATE, "license.txt"), encoding="utf8") as f:
            z.writestr("ami_license.txt", "﻿" + f.read().replace("\r\n", "\n").replace("\n", "\r\n"))
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
