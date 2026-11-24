"""画面を出さない OTRP 本体（BACKEND=posix）で pak を読み、読み込みの誤りを出力の文字列で見つける（#236。調査は docs/records/2026-11-24_headless-pak-load.md）。

    python -X utf8 tools/ci/check_pak_load.py --sim <sim> --pakset <simutrans-test-base.zip> <pak>...
    python -X utf8 tools/ci/check_pak_load.py --sim <sim> --pakset <zip> --self-test <壊す元の pak>

- pakset は本体の tests/simutrans-test-base.zip（本体の既定の pak）。一時の作業フォルダに展開し、その addons/pak/ に <pak>... を置いて起動する。
- 起動の前に必ず settings.xml を消す（OTRP は settings.xml の記録で、起動のたびに使用状況を外へ送る）。作業フォルダは毎回新しく作り、終わりに消す。
  送っていないことは出力でも確かめる（`statistics log is not send.` が出ること、`sent query:` が出ないこと）。
- 判定は終了コードでなく出力の文字列。通る条件は 3 つ全部: 読み込みの終わりの合図（DONE）が出る・渡した pak ごとに「読んだ」行（READ）が出る・失敗の行（ERRORS）が 1 つも出ない。
  FATAL が出たら本体は終わらない（Windows）ので、その時点で止める。時間切れ・合図なしの終了・異常終了は失敗（終了コードは、合図なしで終わったときだけ見る）。
- 見つけられないもの: 絵の画素の破損・末尾が数バイト欠けた pak・必須の絵の書き忘れ・空の絵・タイルの大きさの取り違え（記録の「壊した pak の結果」）。
  半分で切れた pak は何も出さずに物が消える（見つけるのは一覧の比較で、この検査には入れていない。#245）。
- --self-test: 判定そのもの（疑似の本体でハング・すぐ終了・異常終了・合図なし・使用状況の送信）と、元の pak から壊した pak（空・ROOT の大きさ・参照切れ・名前の重複）で、
  失敗することと、元の pak で通ることを確かめる。
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
    (re.compile(r"^ERROR:(?!\s*modal_dialogue)"), "ERROR の行（空・壊れたファイルなど）"),
    (re.compile(r"skipping unknown"), "知らないノード（makeobj が絵を読めなかった物・壊れたノード）"),
    (re.compile(r"is overlaid"), "名前の重複（全部入りと種類別を一緒に置いていないか）"),
    (re.compile(r"too old"), "pak の版が本体より新しい"),
    (re.compile(r"Reading addon object data failed"), "アドオンの物を読めなかった"),
    (re.compile(r"cannot resolve"), "参照切れ"),
    (re.compile(r"sent query:"), "使用状況を外へ送った（settings.xml を消せていない）"),
]
# 読み込みが終わった合図（ゲームの起動の最後）。pakset が無い・言語が無いときも出るので、これだけでは通さない（READ も要る）
DONE = re.compile(r"modal_dialogue:\s+called without a display driver")
FATAL = re.compile(r"FATAL ERROR")
# 渡した pak を本体が読んだ行。本体が pak を開こうとした印で、読めた証拠ではない（読めたかは ERRORS と一覧で見る）（-debug 3。実測: obj_reader_t::read_file():<タブ>filename='addons/pak/<名前>'）
READ = "obj_reader_t::read_file():"
# 使用状況を送らない印（settings.xml が無いときに出る）。FATAL で止まったときは出ないので要求しない
NOT_SENT = "statistics log is not send."


def collect(cmd, cwd, env, timeout):
    """cmd を動かして標準出力の行を集める。終わり方（end）は次のどれか:
    done（DONE の行を見た）・fatal（FATAL の行を見た）・eof（合図なしに出力が閉じた。rc は終了コード）・timeout（時間切れ）。
    戻り値は (行, end, rc)"""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding="utf8", errors="replace")
    lines, state = [], {"end": "eof"}

    def reader():
        for line in proc.stdout:
            line = line.rstrip("\n")
            lines.append(line)
            if FATAL.search(line):
                state["end"] = "fatal"
                return
            if DONE.search(line):
                state["end"] = "done"
                return

    t = threading.Thread(target=reader, daemon=True)
    t.start()
    t.join(timeout)
    timed_out = t.is_alive()  # kill の前に決める（kill で出力が閉じると reader が終わる）
    rc = None
    if not timed_out and state["end"] == "eof":
        try:
            rc = proc.wait(5)
        except subprocess.TimeoutExpired:
            rc = None
    proc.kill()
    proc.wait()
    t.join(5)
    return lines, ("timeout" if timed_out else state["end"]), rc


def clean_settings(root):
    for d in (root, os.path.join(root, "config")):
        f = os.path.join(d, "settings.xml")
        if os.path.exists(f):
            os.remove(f)


def run(sim, pakset_zip, paks, timeout):
    """pak を読んで、(出力の行, 終わり方, 終了コード) を返す"""
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
        clean_settings(root)  # 使用状況を送らないために消す（展開した物に入っていなくても毎回確かめる）
        cmd = [os.path.abspath(sim), "-use_workdir", "-singleuser", "-objects", "pak/", "-addons", "-nosound", "-debug", "3"]
        env = dict(os.environ)
        env["PATH"] = os.path.dirname(os.path.abspath(sim)) + os.pathsep + env.get("PATH", "")  # Windows は DLL を sim の隣と PATH から探す
        try:
            return collect(cmd, root, env, timeout)
        finally:
            clean_settings(root)  # 終了後も消す（送信用の記録が書かれている）
    finally:
        shutil.rmtree(work, ignore_errors=True)


def judge(lines, end, rc, paks=()):
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
    elif end == "eof":
        bad.append(f"終わりの合図が無いまま本体が終わった（終了コード {rc}。異常終了か、起動に失敗）")
    if end == "done":
        for p in paks:
            want = "addons/pak/" + os.path.basename(p)
            if not any(READ in l and want in l.replace("\\", "/") for l in lines):
                bad.append(f"渡した pak を読んだ行が無い: {os.path.basename(p)}")
        if not any(NOT_SENT in l for l in lines):
            bad.append(f"使用状況を送らない印（{NOT_SENT}）が出ない（settings.xml が残っていないか）")
    return bad


def report(lines, end, rc, paks, secs):
    bad = judge(lines, end, rc, paks)
    print(f"[pak-load] {len(paks)} pak, {len(lines)} 行, {secs:.1f} 秒, 終わり方 {end}")
    for b in bad[:30]:
        print("  NG " + b)
    if len(bad) > 30:
        print(f"  … ほか {len(bad) - 30} 件")
    return not bad


def check(sim, pakset, paks, timeout):
    t0 = time.time()
    lines, end, rc = run(sim, pakset, paks, timeout)
    return report(lines, end, rc, paks, time.time() - t0)


FAKE_SENT = "Warning: log_sender_t::send_launch_log():\tstatistics log is not send."
FAKE_READ = "Message: obj_reader_t::read_file():\tfilename='addons/pak/x.pak'"
FAKE_DONE = "ERROR: modal_dialogue:\tcalled without a display driver => nothing will be shown!"


def fake_sim(lines, tail="sleep"):
    """疑似の本体のコード（python -c に渡す）。lines を出して、tail が sleep なら眠り続け、exit:N ならその終了コードで終わる"""
    code = "import sys, time\n"
    for l in lines:
        code += f"print({l!r}, flush=True)\n"
    if tail == "sleep":
        code += "time.sleep(60)\n"
    elif tail.startswith("exit:"):
        code += f"sys.exit({int(tail[5:])})\n"
    return code


def judge_self_test(timeout=3):
    """判定の自己確認。疑似の本体で、通るはずの出力と、失敗にするはずの出力を collect と judge に通す"""
    ok = [FAKE_SENT, FAKE_READ, FAKE_DONE]
    cases = [
        ("疑似: 通る出力（印・読んだ行・合図）", fake_sim(ok), True),
        ("疑似: 出力なしのハング", fake_sim([]), False),
        ("疑似: すぐ終わる（出力なし。終了コード 0）", fake_sim([], "exit:0"), False),
        ("疑似: 異常終了（Segmentation fault・終了コード 139）", fake_sim(["Segmentation fault"], "exit:139"), False),
        ("疑似: 1 行出して眠る", fake_sim(["Message: x"]), False),
        ("疑似: 合図はあるが、渡した pak を読んだ行が無い", fake_sim([FAKE_SENT, FAKE_DONE]), False),
        ("疑似: 使用状況を送った（sent query:）", fake_sim([FAKE_SENT, "sent query: http://example", FAKE_READ, FAKE_DONE]), False),
        ("疑似: 送らない印が無い", fake_sim([FAKE_READ, FAKE_DONE]), False),
        ("疑似: 知らない ERROR の行", fake_sim([FAKE_SENT, FAKE_READ, "ERROR: foo", FAKE_DONE]), False),
    ]
    good = True
    for name, code, want in cases:
        print(f"== {name}")
        t0 = time.time()
        lines, end, rc = collect([sys.executable, "-c", code], None, dict(os.environ), timeout)
        got = report(lines, end, rc, ["x.pak"], time.time() - t0)
        if got != want:
            print(f"  期待と違う: {'通った' if got else '失敗した'}（期待は{'通る' if want else '失敗'}）")
            good = False
    return good


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
    ok = judge_self_test()
    work = tempfile.mkdtemp(prefix="pakbreak_")
    try:
        raw = open(src, "rb").read()
        base = os.path.basename(src)
        stem, ext = os.path.splitext(base)
        # (名前, [(ファイル名, 中身)...], 通るはずか)
        cases = [("元の pak（通るはず）", [(base, raw)], True),
                 ("空のファイル", [(base, b"")], False),
                 ("ROOT の大きさ", [(base, break_root_size(raw))], False),
                 ("参照切れ（xref）", [(base, break_xref(raw))], False),
                 ("名前の重複（同じ pak を 2 本）", [(base, raw), (stem + "_copy" + ext, raw)], False)]
        for name, files, want_pass in cases:
            d = os.path.join(work, str(len(os.listdir(work))))
            os.makedirs(d)
            paths = []
            for fn, data in files:
                p = os.path.join(d, fn)
                with open(p, "wb") as f:
                    f.write(data)
                paths.append(p)
            print(f"== {name}")
            got = check(sim, pakset, paths, timeout)
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
