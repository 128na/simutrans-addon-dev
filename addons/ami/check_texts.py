"""名前の訳（release/text/ja_ami.tab・en_ami.tab）と dat の name= を突き合わせる（#396）。

    python -X utf8 check_texts.py              # 検査
    python -X utf8 check_texts.py --self-test  # 壊した訳を見つけられるかの確かめ

見るもの:
    - src/・src256/ の dat の name=（分岐の追加画像の提供用 ex_donors の物を除く）の全部が ja にある
    - en のキーが ja と同じで、並びも同じ。dat に無いキー・重複が無い
    - 訳のファイルの形（本体の dataobj/translator.cc の読み方）: 先頭は § （C2 A7）で始まる # の行。後は名前と訳の行が交互。
      空行は 1 つあるとそれ以降の組が 1 行ずれるので置かない。名前と同じ訳は本体が捨てる。% は書式の指定とみなされて、
      名前に無ければその組が捨てられる
    - en の訳は ASCII だけ（日本語が混ざらない）で「(AMI」を含み、ja の訳は「（AMI」を含む
配る zip には release.py が release/text/ の全部を入れる。
"""
import argparse
import glob
import os
import re
import sys

from ex_graft import DONOR_SUFFIX

HERE = os.path.dirname(os.path.abspath(__file__))
TEXTS = os.path.join(HERE, "release", "text")
SRC_DIRS = ("src", "src256")
MARKS = {"ja": "（AMI", "en": "(AMI"}


def dat_names():
    names = set()
    for d in SRC_DIRS:
        for path in glob.glob(os.path.join(HERE, d, "*.dat")):
            with open(path, encoding="utf8") as f:
                for line in f:
                    m = re.match(r"(?i)name=(.*)$", line.strip())
                    if m and not m[1].endswith(DONOR_SUFFIX):
                        names.add(m[1])
    return names


def parse(lang, data):
    """訳のファイルの中身（バイト列）を [(名前, 訳)] と誤りの一覧にする"""
    errors = []
    if not data.startswith("§#".encode()):
        errors.append(f"{lang}: 先頭が「§#」（C2 A7 23）でない")
    lines = data.decode("utf8").replace("\r\n", "\n").split("\n")
    if lines[-1] == "":
        lines.pop()
    body = lines[1:]
    for n, line in enumerate(body, 2):
        if not line.strip() or line != line.strip() or line.startswith("#"):
            errors.append(f"{lang}:{n}: 空行・前後の空白・2 行目より後の # の行は置かない: {line!r}")
    if len(body) % 2:
        errors.append(f"{lang}: 名前と訳の行の数が合わない（{len(body)} 行）")
    pairs = list(zip(body[::2], body[1::2]))
    seen = set()
    for key, value in pairs:
        if key in seen:
            errors.append(f"{lang}: 名前が重複: {key}")
        seen.add(key)
        if value == key or MARKS[lang] not in value:
            errors.append(f"{lang}: 訳に「{MARKS[lang]}」が無いか、名前のまま: {key} → {value}")
        if "%" in value:
            errors.append(f"{lang}: 訳に % がある: {key} → {value}")
        if lang == "en" and not value.isascii():
            errors.append(f"{lang}: 英語の訳に ASCII でない字がある: {key} → {value}")
    return pairs, errors


def check(names, files):
    """names: dat の名前の集合。files: {言語: 中身のバイト列}。誤りの一覧を返す"""
    errors = []
    keys = {}
    for lang, data in files.items():
        pairs, errs = parse(lang, data)
        errors += errs
        keys[lang] = [k for k, _ in pairs]
    for lang, ks in keys.items():
        errors += [f"{lang}: dat にある名前の訳が無い: {n}" for n in sorted(names - set(ks))]
        errors += [f"{lang}: dat に無い名前の訳がある: {n}" for n in sorted(set(ks) - names)]
    if keys["ja"] != keys["en"]:
        errors.append("ja と en の名前の並びが違う")
    return errors


def read_files():
    files = {}
    for lang in MARKS:
        with open(os.path.join(TEXTS, f"{lang}_ami.tab"), "rb") as f:
            files[lang] = f.read()
    return files


def self_test():
    def tab(lang, *pairs):
        mark = "（AMI）" if lang == "ja" else " (AMI)"
        return ("§# x\n" + "".join(f"{k}\n{v}{mark}\n" for k, v in pairs)).encode()

    names = {"a", "b"}
    good = {"ja": tab("ja", ("a", "あ"), ("b", "い")), "en": tab("en", ("a", "A"), ("b", "B"))}
    bad = {
        "訳の抜け": {**good, "ja": tab("ja", ("a", "あ"))},
        "dat に無い名前": {**good, "en": tab("en", ("a", "A"), ("b", "B"), ("c", "C"))},
        "並びの違い": {**good, "en": tab("en", ("b", "B"), ("a", "A"))},
        "重複": {**good, "en": tab("en", ("a", "A"), ("a", "A"), ("b", "B"))},
        "空行": {**good, "en": good["en"].replace(b"A (AMI)\n", b"A (AMI)\n\n")},
        "印が無い": {**good, "en": good["en"].replace("§".encode(), b"")},
        "日本語が混ざる": {**good, "en": tab("en", ("a", "あ"), ("b", "B"))},
        "%": {**good, "en": tab("en", ("a", "50%"), ("b", "B"))},
    }
    errors = [f"正しい訳で誤り: {e}" for e in check(names, good)]
    errors += [f"見逃した: {label}" for label, files in bad.items() if not check(names, files)]
    if errors:
        sys.exit("[check_texts] self-test 失敗: " + " / ".join(errors))
    print(f"[check_texts] self-test ok（見つける {len(bad)}）")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    if ap.parse_args().self_test:
        self_test()
        return
    names = dat_names()
    if not names:
        sys.exit("[check_texts] dat の名前が 1 つも読めない")
    errors = check(names, read_files())
    if errors:
        sys.exit("[check_texts] 失敗:\n  " + "\n  ".join(errors))
    print(f"[check_texts] ok（dat の名前 {len(names)}、ja・en の訳がそろっている）")


if __name__ == "__main__":
    main()
