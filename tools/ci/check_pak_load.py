"""画面を出さない OTRP 本体（BACKEND=posix）で pak を読み、読み込みの誤りを出力の文字列で見つける（#236。調査は docs/records/2026-11-24_headless-pak-load.md）。

    python -X utf8 tools/ci/check_pak_load.py --sim <sim> --pakset <simutrans-test-base.zip> <pak>...
    python -X utf8 tools/ci/check_pak_load.py --sim <sim> --pakset <zip> --self-test <壊す元の pak>
    python -X utf8 tools/ci/check_pak_load.py --sim <sim> --pakset <zip> --makeobj makeobj <pak>...   # 登録された名前の一覧も比べる（#245）

- pakset は本体の tests/simutrans-test-base.zip（本体の既定の pak）。一時の作業フォルダに展開し、その addons/pak/ に <pak>... を置いて起動する。
- 起動の前に必ず settings.xml を消す（OTRP は settings.xml の記録で、起動のたびに使用状況を外へ送る）。作業フォルダは毎回新しく作り、終わりに消す。
  送っていないことは出力でも確かめる（`statistics log is not send.` が出ること、`sent query:` が出ないこと）。
- 判定は終了コードでなく出力の文字列。通る条件は 3 つ全部: 読み込みの終わりの合図（DONE）が出る・渡した pak ごとに「読んだ」行（READ）が出る・失敗の行（ERRORS）が 1 つも出ない。
  FATAL が出たら本体は終わらない（Windows）ので、その時点で止める。時間切れ・合図なしの終了・異常終了は失敗（終了コードは、合図なしで終わったときだけ見る）。
- 見つけられないもの: 絵の画素の破損・末尾が数バイト欠けた pak・必須の絵の書き忘れ・空の絵・タイルの大きさの取り違え（記録の「壊した pak の結果」）。
  半分で切れた pak は何も出さずに物が消える。これは --makeobj を渡したときの「名前の一覧の比較」で見つける（#245。下）。
- --makeobj <makeobj>（#245）: scenario（tools/ci/pak_names_scenario/）で、本体に登録された way・way-object・tunnel・bridge・roadsign・building の名前を出し、
  `makeobj list` の同じ種類の名前と比べる。pak に入っているのに登録されていない名前（足りない）と、pak に無いのに登録された名前（余る。pakset だけで起動した一覧を引いて求める）があれば失敗。
  比べない種類: crossing など（本体に一覧を出す API が無い。件数だけ出す）。
- --self-test: 判定そのもの（疑似の本体でハング・すぐ終了・異常終了・合図なし・使用状況の送信）と、元の pak から壊した pak（空・ROOT の大きさ・参照切れ・名前の重複）で、
  失敗することと、元の pak で通ることを確かめる。--makeobj も渡すと、名前の一覧の比較も確かめる（ROOT の子を 1 つ削った pak・半分で切った pak は、出力に何も出ないが一覧の比較で失敗する）。
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
    (re.compile(r"An error occurred within a script"), "scenario の実行の誤り（API の名前の違いなど）"),
]
# 読み込みが終わった合図（ゲームの起動の最後）。pakset が無い・言語が無いときも出るので、これだけでは通さない（READ も要る）
DONE = re.compile(r"modal_dialogue:\s+called without a display driver")
FATAL = re.compile(r"FATAL ERROR")
# 渡した pak を本体が読んだ行。本体が pak を開こうとした印で、読めた証拠ではない（読めたかは ERRORS と一覧で見る）（-debug 3。実測: obj_reader_t::read_file():<タブ>filename='addons/pak/<名前>'）
READ = "obj_reader_t::read_file():"
# 名前の一覧を出す scenario（tools/ci/pak_names_scenario/）の出力。「PAKNAMES <種類> <名前>」と、終わりの合図
SCENARIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pak_names_scenario")
SCENARIO_NAME = "pakchk"
NAMES = re.compile(r"PAKNAMES (\S+) (.+?)\s*$")
NAMES_DONE = re.compile(r"PAKNAMES done\s*$")
# makeobj list の種類のうち、本体に一覧を出す API があって比べる物
COMPARED = ("way", "way-object", "tunnel", "bridge", "roadsign", "building")
# 使用状況を送らない印（settings.xml が無いときに出る）。FATAL で止まったときは出ないので要求しない
NOT_SENT = "statistics log is not send."


def collect(cmd, cwd, env, timeout, done=DONE):
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
            if done.search(line):
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


def run(sim, pakset_zip, paks, timeout, names=False):
    """pak を読んで、(出力の行, 終わり方, 終了コード) を返す。names なら、名前の一覧を出す scenario も動かす"""
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
        if names:
            # 本体は addons/<pak>/scenario/ を先に探し（addons/pak/ に物があるときだけ）、無ければ pakset の pak/scenario/ を探す。
            # 先に探す側に無いと ERROR の行が出るので、両方に置く
            for base in (add, os.path.join(root, "pak")):
                shutil.copytree(SCENARIO_DIR, os.path.join(base, "scenario", SCENARIO_NAME))
        clean_settings(root)  # 使用状況を送らないために消す（展開した物に入っていなくても毎回確かめる）
        cmd = [os.path.abspath(sim), "-use_workdir", "-singleuser", "-objects", "pak/", "-addons", "-nosound", "-debug", "3"]
        if names:
            cmd += ["-scenario", SCENARIO_NAME]
        env = dict(os.environ)
        env["PATH"] = os.path.dirname(os.path.abspath(sim)) + os.pathsep + env.get("PATH", "")  # Windows は DLL を sim の隣と PATH から探す
        try:
            return collect(cmd, root, env, timeout, NAMES_DONE if names else DONE)
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


def parse_names(lines):
    """scenario の出力から (登録された名前の集合 {(種類, 名前)}, 年表が有効か)"""
    got, timeline = set(), None
    for l in lines:
        m = NAMES.search(l)
        if not m:
            continue
        if m.group(1) == "timeline":
            timeline = m.group(2) == "on"
        elif m.group(1) != "done":
            got.add((m.group(1), m.group(2)))
    return got, timeline


LIST_ROW = re.compile(r"^(\S+)\s+(.+?)\s+\d+\s+\d+\s*$")


def makeobj_names(makeobj, paks):
    """makeobj list の (種類, 名前) の集合と、比べない種類ごとの件数。pak ごとに別々に呼ぶ"""
    names, skipped = set(), {}
    for p in paks:
        try:
            out = subprocess.run([makeobj, "list", p], capture_output=True, text=True, encoding="utf8", errors="replace", timeout=60)
        except (OSError, subprocess.TimeoutExpired) as e:
            sys.exit(f"[pak-load] makeobj を動かせない（--makeobj {makeobj}）: {e}")
        if out.returncode != 0:
            sys.exit(f"[pak-load] makeobj list が失敗: {p}\n{out.stdout}{out.stderr}")
        rows = 0
        for l in out.stdout.splitlines():
            m = LIST_ROW.match(l)
            if not m or m.group(1) == "type":
                continue
            rows += 1
            if m.group(1) in COMPARED:
                names.add((m.group(1), m.group(2)))
            else:
                skipped[m.group(1)] = skipped.get(m.group(1), 0) + 1
        if rows == 0:
            sys.exit(f"[pak-load] makeobj list の出力から物の行を読めない: {p}")
    return names, skipped


_base_cache = {}


def base_names(sim, pakset, timeout):
    """pakset だけで起動したときに登録されている名前（これより多い名前が「余る」物）"""
    key = (os.path.abspath(sim), os.path.abspath(pakset))
    if key not in _base_cache:
        lines, end, rc = run(sim, pakset, [], timeout, names=True)
        if end != "done":
            sys.exit(f"[pak-load] pakset だけの起動で名前の一覧が出ない（終わり方 {end}）")
        _base_cache[key] = parse_names(lines)[0]
    return _base_cache[key]


def compare_names(lines, expected, base):
    """pak の名前（expected。makeobj list）と本体に登録された名前を比べて、失敗の理由の一覧を返す"""
    got, timeline = parse_names(lines)
    bad = []
    if timeline is None:
        bad.append("名前の一覧が出ていない（scenario の出力に timeline の行が無い）")
        return bad
    if timeline:
        bad.append("年表（timeline）が有効（intro_year が先の物が一覧に出ず、比べられない）")
    for t, n in sorted(expected - got):
        bad.append(f"pak にあるが登録されていない: {t} {n}" + ("（アイコンの無い way は一覧に出ない）" if t == "way" else ""))
    for t, n in sorted(got - base - expected):
        bad.append(f"pak に無いのに登録されている: {t} {n}")
    return bad


LAST_BAD = []  # 直前の report の失敗の理由（自己確認が文面を照合する）


def report(lines, end, rc, paks, secs, expected=None, base=None, skipped=None):
    bad = judge(lines, end, rc, paks)
    if expected is not None and end == "done":
        bad += compare_names(lines, expected, base)
    LAST_BAD[:] = bad
    print(f"[pak-load] {len(paks)} pak, {len(lines)} 行, {secs:.1f} 秒, 終わり方 {end}"
          + (f", 名前の一覧: {len(expected)} 個を比べた" if expected is not None else "")
          + (f"（比べない種類: {', '.join(f'{k} {v}' for k, v in sorted(skipped.items()))}）" if skipped else ""))
    for b in bad[:30]:
        print("  NG " + b)
    if len(bad) > 30:
        print(f"  … ほか {len(bad) - 30} 件")
    return not bad


def check(sim, pakset, paks, timeout, makeobj=None, expected_paks=None):
    """expected_paks は makeobj list で名前を求める pak（既定は paks。壊した pak の確かめでは元の pak）"""
    t0 = time.time()
    expected = base = skipped = None
    if makeobj:
        expected, skipped = makeobj_names(makeobj, expected_paks or paks)
        base = base_names(sim, pakset, timeout)
    lines, end, rc = run(sim, pakset, paks, timeout, names=bool(makeobj))
    return report(lines, end, rc, paks, time.time() - t0, expected, base, skipped)


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


def drop_last_object(data):
    """ROOT の直下の最後の物（WAY など。参照されていない物）を 1 つ削り、ROOT の子の数を 1 減らす。本体は何も出さずに、その物だけを登録しない"""
    head = data.index(b"\x1a") + 1
    root = head + 4
    assert data[root:root + 4] == b"ROOT"

    def node_end(o):
        children, size = struct.unpack_from("<HH", data, o + 4)
        h = 8
        if size == 0xFFFF:
            size = struct.unpack_from("<I", data, o + 8)[0]
            h = 12
        p = o + h + size
        for _ in range(children):
            p = node_end(p)
        return p

    n = struct.unpack_from("<H", data, root + 4)[0]
    assert n >= 2, "削る物と残る物が要る"
    p, last = root + 8, None
    for _ in range(n):
        last, p = p, node_end(p)
    assert p == len(data), "ノードの木が pak の終わりまで続かない"
    b = bytearray(data[:last])
    struct.pack_into("<H", b, root + 4, n - 1)
    return bytes(b)


# 自己確認で、失敗の理由に含まれるはずの文字列（別の理由で失敗していても通らないように）
WANT_MSG = {"空のファイル": "unexpected end of file", "ROOT の大きさ": "ROOT must have size 0", "参照切れ（xref）": "cannot resolve",
            "名前の重複（同じ pak を 2 本）": "is overlaid",
            "登録されない物が 1 つ（ROOT の最後の物を削る）": "pak にあるが登録されていない",
            "半分で切れた pak": "pak にあるが登録されていない",
            "余る物が 1 つ（makeobj list の側が 1 つ少ない）": "pak に無いのに登録されている"}


def self_test(sim, pakset, src, timeout, makeobj=None):
    ok = judge_self_test()
    work = tempfile.mkdtemp(prefix="pakbreak_")
    try:
        raw = open(src, "rb").read()
        base = os.path.basename(src)
        stem, ext = os.path.splitext(base)
        # (名前, [(ファイル名, 中身)...], 通るはずか[, 名前の一覧の元にする pak])
        cases = [("元の pak（通るはず）", [(base, raw)], True),
                 ("空のファイル", [(base, b"")], False),
                 ("ROOT の大きさ", [(base, break_root_size(raw))], False),
                 ("参照切れ（xref）", [(base, break_xref(raw))], False),
                 ("名前の重複（同じ pak を 2 本）", [(base, raw), (stem + "_copy" + ext, raw)], False)]
        if makeobj:
            # 読み込みの出力には何も出ない壊れ方。名前の一覧の比較だけが見つける
            cases += [("登録されない物が 1 つ（ROOT の最後の物を削る）", [(base, drop_last_object(raw))], False),
                      ("半分で切れた pak", [(base, raw[:len(raw) // 2])], False)]
            # 逆向き: 本体に登録される名前が makeobj list に無い（余る）。一覧の元を 1 つ少ない pak にして、元の pak を読む
            few = os.path.join(work, "few")
            os.makedirs(few)
            with open(os.path.join(few, base), "wb") as f:
                f.write(drop_last_object(raw))
            cases += [("余る物が 1 つ（makeobj list の側が 1 つ少ない）", [(base, raw)], False, few + os.sep + base)]
        for name, files, want_pass, *expected in cases:
            d = os.path.join(work, str(len(os.listdir(work))))
            os.makedirs(d)
            paths = []
            for fn, data in files:
                p = os.path.join(d, fn)
                with open(p, "wb") as f:
                    f.write(data)
                paths.append(p)
            print(f"== {name}")
            got = check(sim, pakset, paths, timeout, makeobj, expected or [src])
            if got != want_pass:
                print(f"  期待と違う: {'通った' if got else '失敗した'}（期待は{'通る' if want_pass else '失敗'}）")
                ok = False
            elif name in WANT_MSG and not any(WANT_MSG[name] in b for b in LAST_BAD):
                print(f"  失敗の理由が違う（期待は「{WANT_MSG[name]}」を含む）")
                ok = False
        return ok
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim", required=True, help="BACKEND=posix でビルドした本体")
    ap.add_argument("--pakset", required=True, help="本体の tests/simutrans-test-base.zip")
    ap.add_argument("--timeout", type=float, default=90)
    ap.add_argument("--makeobj", help="makeobj（渡すと、登録された名前の一覧を makeobj list と比べる。#245）")
    ap.add_argument("--self-test", action="store_true", help="壊した pak で失敗することを確かめる（pak は 1 本）")
    ap.add_argument("paks", nargs="+")
    a = ap.parse_args()
    for p in a.paks:
        if not os.path.isfile(p):
            sys.exit(f"[pak-load] pak が無い: {p}")
    if a.self_test:
        if len(a.paks) != 1:
            sys.exit("[pak-load] --self-test は pak を 1 本だけ渡す")
        good = self_test(a.sim, a.pakset, a.paks[0], a.timeout, a.makeobj)
    else:
        good = check(a.sim, a.pakset, a.paks, a.timeout, a.makeobj)
    sys.exit(0 if good else 1)


if __name__ == "__main__":
    main()
