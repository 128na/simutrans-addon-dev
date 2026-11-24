"""画面を出さない OTRP 本体（BACKEND=posix）で pak を読み、読み込みの誤りを出力の文字列で見つける（#236。調査は docs/records/2026-11-24_headless-pak-load.md）。

    python -X utf8 tools/ci/check_pak_load.py --sim <sim> --pakset <simutrans-test-base.zip> <pak>...
    python -X utf8 tools/ci/check_pak_load.py --sim <sim> --pakset <zip> --self-test <壊す元の pak>

- pakset は本体の tests/simutrans-test-base.zip（本体の既定の pak）。一時の作業フォルダに展開し、その addons/pak/ に <pak>... を置いて起動する。
- 起動の前に必ず settings.xml を消す（OTRP は settings.xml の記録で、起動のたびに使用状況を外へ送る）。作業フォルダは毎回新しく作り、終わりに消す。
- 判定は終了コードでなく出力の文字列（ERRORS）。FATAL が出たら本体は終わらない（Windows）ので、その時点で止める。
- 見つけられないもの: 絵の画素の破損・末尾が数バイト欠けた pak・必須の絵の書き忘れ・空の絵・タイルの大きさの取り違え（記録の「壊した pak の結果」）。
  半分で切れた pak は何も出さずに物が消える（見つけるのは一覧の比較で、この検査には入れていない）。
- --self-test: 元の pak から壊した pak（空・ROOT の大きさ・参照切れ）を作り、それぞれで失敗することと、元の pak で通ることを確かめる。
"""
import argparse
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

# 出たら失敗にする行（記録の表）。どれも -debug 3 の標準出力の行
ERRORS = [
    (re.compile(r"FATAL ERROR"), "致命的な誤り（参照切れ cannot resolve・ROOT の大きさなど）"),
    (re.compile(r"(?<!FATAL )ERROR: obj_reader"), "pak を読めない（空・壊れたファイル）"),
    (re.compile(r"skipping unknown"), "知らないノード（makeobj が絵を読めなかった物・壊れたノード）"),
    (re.compile(r"is overlaid"), "名前の重複（全部入りと種類別を一緒に置いていないか）"),
    (re.compile(r"too old"), "pak の版が本体より新しい"),
    (re.compile(r"Reading addon object data failed"), "アドオンの物を読めなかった"),
    (re.compile(r"cannot resolve"), "参照切れ"),
]
# 読み込みが終わった合図（ゲームの起動の最後。ここまで来て ERRORS が無ければ通る）
DONE = re.compile(r"modal_dialogue: called without a display driver")
FATAL = re.compile(r"FATAL ERROR")


def run(sim, pakset_zip, paks, timeout):
    """pak を読んで、出力の行と終わり方（done・fatal・timeout）を返す"""
    work = tempfile.mkdtemp(prefix="pakload_")
    try:
        with zipfile.ZipFile(pakset_zip) as z:
            z.extractall(work)
        roots = [d for d in os.listdir(work) if os.path.isdir(os.path.join(work, d))]
        root = os.path.join(work, roots[0]) if len(roots) == 1 and not os.path.isdir(os.path.join(work, "pak")) else work
        add = os.path.join(root, "addons", "pak")
        os.makedirs(add, exist_ok=True)
        for p in paks:
            shutil.copy(p, add)
        # 使用状況を送らないために消す（展開した物に入っていなくても毎回確かめる）
        for d in (root, os.path.join(root, "config")):
            f = os.path.join(d, "settings.xml")
            if os.path.exists(f):
                os.remove(f)
        cmd = [os.path.abspath(sim), "-use_workdir", "-singleuser", "-objects", "pak/", "-addons", "-nosound", "-debug", "3"]
        env = dict(os.environ)
        bindir = os.path.dirname(os.path.abspath(sim))
        env["PATH"] = bindir + os.pathsep + env.get("PATH", "")  # Windows は DLL を sim の隣と PATH から探す
        proc = subprocess.Popen(cmd, cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf8", errors="replace")
        lines, state = [], {"end": "timeout"}

        def reader():
            for line in proc.stdout:
                line = line.rstrip("\n")
                lines.append(line)
                if FATAL.search(line):
                    state["end"] = "fatal"
                    break
                if DONE.search(line):
                    state["end"] = "done"
                    break
            else:
                state["end"] = "done" if state["end"] == "timeout" else state["end"]

        t = threading.Thread(target=reader, daemon=True)
        t.start()
        t.join(timeout)
        proc.kill()
        proc.wait()
        # 終了後の settings.xml も消す（送信用の記録が書かれている）
        for d in (root, os.path.join(root, "config")):
            f = os.path.join(d, "settings.xml")
            if os.path.exists(f):
                os.remove(f)
        return lines, ("timeout" if t.is_alive() else state["end"])
    finally:
        shutil.rmtree(work, ignore_errors=True)


def judge(lines, end):
    """失敗の理由の一覧（空なら通った）"""
    bad = []
    seen = set()
    for l in lines:
        for rx, why in ERRORS:
            if rx.search(l) and (why, l) not in seen:
                seen.add((why, l))
                bad.append(f"{why}: {l.strip()}")
    if end == "timeout":
        bad.append("時間切れ（読み込みが終わらない）")
    if not bad and end != "done":
        bad.append(f"読み込みの終わりの合図が無い（終わり方: {end}）")
    return bad


def check(sim, pakset, paks, timeout):
    t0 = time.time()
    lines, end = run(sim, pakset, paks, timeout)
    bad = judge(lines, end)
    print(f"[pak-load] {len(paks)} pak, {len(lines)} 行, {time.time() - t0:.1f} 秒, 終わり方 {end}")
    for b in bad[:30]:
        print("  NG " + b)
    if len(bad) > 30:
        print(f"  … ほか {len(bad) - 30} 件")
    return not bad


# ---- 壊した pak（--self-test） ----
def break_root_size(data):
    """ROOT ノード（ヘッダーの直後。版 4 バイトの後）の大きさ（uint16）を 0 でなくする"""
    head = data.index(b"\x1a") + 1  # ヘッダーは "Simutrans object file ...\n" と 0x1A、版（uint32）
    node = head + 4
    assert data[node:node + 4] == b"ROOT", data[node:node + 8]
    b = bytearray(data)
    struct.pack_into("<H", b, node + 6, 16)  # type(4) children(2) size(2)
    return bytes(b)


def break_xref(data):
    """XREF ノードの参照先の名前の 1 文字を変え、見つからないときに止まる印（fatal）を立てて、解決できない参照にする"""
    i = data.find(b"XREF")
    assert i >= 0, "元の pak に XREF が無い"
    b = bytearray(data)
    # XREF ノード: type(4) children(2) size(2)、中身は 種類(4 バイト 例 WAY と 0 の 4 バイト)・fatal(1)・名前（0 終わり）。
    # fatal が 0 の参照は見つからなくても進むので 1 にする
    size = struct.unpack_from("<H", data, i + 6)[0]
    body = i + 8
    end = body + size - 1  # 0 終わりの 0
    assert data[end] == 0 and end - body > 3
    b[body + 4] = 1
    b[end - 1] = ord("#") if data[end - 1] != ord("#") else ord("$")
    return bytes(b)


def self_test(sim, pakset, src, timeout):
    work = tempfile.mkdtemp(prefix="pakbreak_")
    try:
        ok = True
        raw = open(src, "rb").read()
        base = os.path.basename(src)
        cases = [("元の pak（通るはず）", raw, True),
                 ("空のファイル", b"", False),
                 ("ROOT の大きさ", break_root_size(raw), False),
                 ("参照切れ（xref）", break_xref(raw), False)]
        for name, data, want_pass in cases:
            d = os.path.join(work, str(len(os.listdir(work))))
            os.makedirs(d)
            p = os.path.join(d, base)
            with open(p, "wb") as f:
                f.write(data)
            print(f"== {name}")
            got = check(sim, pakset, [p], timeout)
            if got != want_pass:
                print(f"  期待と違う: {'通った' if got else '失敗した'}（期待は{'通る' if want_pass else '失敗'}）")
                ok = False
        return ok
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim", required=True, help="BACKEND=posix でビルドした本体")
    ap.add_argument("--pakset", required=True, help="本体の tests/simutrans-test-base.zip")
    ap.add_argument("--timeout", type=float, default=90)
    ap.add_argument("--self-test", action="store_true", help="壊した pak で失敗することを確かめる（pak は 1 本）")
    ap.add_argument("paks", nargs="+")
    a = ap.parse_args()
    for p in a.paks:
        if not os.path.isfile(p):
            sys.exit(f"[pak-load] pak が無い: {p}")
    if a.self_test:
        if len(a.paks) != 1:
            sys.exit("[pak-load] --self-test は pak を 1 本だけ渡す")
        good = self_test(a.sim, a.pakset, a.paks[0], a.timeout)
    else:
        good = check(a.sim, a.pakset, a.paks, a.timeout)
    sys.exit(0 if good else 1)


if __name__ == "__main__":
    main()
