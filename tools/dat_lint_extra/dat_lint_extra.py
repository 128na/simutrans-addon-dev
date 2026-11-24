"""dat_linter（CI の本線）が見ない、dat の静かな誤りを見つける補助の検査（#224）。

    python tools/dat_lint_extra/dat_lint_extra.py <dat か、dat のあるフォルダ>...
    python tools/dat_lint_extra/dat_lint_extra.py --self-test     # 検査自身が誤りを見つけるか（check.sh が先に回す）

見るもの（コードの名前は simutrans-blender-kit の linter に合わせた）:
  dropped-indent  先頭が空白の行。本体は捨てるので、そのキーは効かない
  value-comment   文字の値の後ろの `# 注記`。値の一部になり、読み込みで失敗する（数値と絵の参照は許されるので見ない）
  bad-int         数値のキーに数字でない値。atoi が 0 や途中までを返し、makeobj は何も言わない
  unknown-key     その obj が読まないキー（綴りの誤り）。makeobj は黙って捨てる
  unknown-obj     知らない obj の種類。makeobj は黙って飛ばし、物が pak に入らない
  way-key         obj=way の絵のキーの綴り（ribi・坂の数。image[zz] や imageup[n] は捨てられる）
  way-slope       obj=way の坂の絵が 4 つそろっていない（欠けた坂は絵が出ない）

dat_linter が見るもの（duplicate-key・waytype・画像の範囲など）は重ねない。差の表は
docs/records/2026-11-24_dat-linter-vs-kit-lint.md。エラーがあれば終了コード 1。

出典: simutrans-blender-kit（Dkijas/simutrans-blender-kit、MIT）の core/schema.py と tools/lint_dat.py の
考え方と、キー表 dat_schema.json（本体 124.5.1 の descriptor/writer から機械的に作られたもの）を借りている。
コードは書き直したが、キーの展開（expand_key）と %s の正規表現は schema.py に由来する。
MIT の著作権表示と許諾の文は LICENSE.simutrans-blender-kit。way の坂の綴りは借りていない
（kit は imageup[n|w|e|s]、この fork の way_writer.cc は imageup[3|6|9|12]）。
"""

import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "dat_schema.json"), encoding="utf-8") as _f:
    _SCHEMA = json.load(_f)
COMMON_KEYS = _SCHEMA["common_keys"]
OBJ_TYPES = _SCHEMA["obj_types"]
TOP_LEVEL = sorted(k for k, v in OBJ_TYPES.items() if v["top_level"])

# printf の変換を正規表現にする。%s は空文字にもなる（way_writer.cc の "%simageup%s[...]"）
_CONV = {"d": r"\d+", "i": r"\d+", "u": r"\d+", "x": r"[0-9a-f]+", "s": r"[^\[\]]*"}


def _pattern_re(fmt):
    out = []
    for part in re.split(r"(%[a-z])", fmt):
        if len(part) == 2 and part[0] == "%":
            out.append(_CONV[part[1]])
        else:
            out.append(re.escape(part))
    return re.compile("^" + "".join(out) + "$")


_PATTERNS = {n: [_pattern_re(f) for f in t["patterns"]] for n, t in OBJ_TYPES.items()}
_GROUP = re.compile(r"\[([^\]]*)\]")
_INT_READERS = ("get_int", "get_int64", "get_int_clamped")
_TEXT_READERS = ("get", "get_string")
# 値が絵の参照の text キー（icon・cursor と、名前に image・diagonal を含むキー）。後ろの注記は本体が許す（image_writer.cc）
_IMAGE_REF_KEYS = ("icon", "cursor")
# get_int は strtol(値, NULL, 0)（tabfile.cc）: 0x… は 16 進、先頭 0 は 8 進（08 は 0 になる）。get_int64 は atof
_INT = re.compile(r"[+-]?(0[xX][0-9a-fA-F]+|0|[1-9]\d*)\Z")
_FLOAT = re.compile(r"[+-]?\d+(\.\d+)?\Z")

# way_writer.cc の ribi_codes と坂（この fork）
WAY_RIBI = {"-", "n", "e", "ne", "s", "ns", "se", "nse", "w", "nw", "ew", "new", "sw", "nsw",
            "sew", "nsew", "nse1", "new1", "nsw1", "sew1", "nsew1",
            "nse2", "new2", "nsw2", "sew2", "nsew2"}
WAY_DIAGONAL = {"ne", "se", "nw", "sw", "close1", "close2"}   # close* は近い斜め（本家 makeobj 125）
WAY_SLOPES = ("3", "6", "9", "12")
_WAY_KEY = re.compile(r"^(front|back)?(image|diagonal|imageup2?)\[([^\]]*)\](?:\[(\d+)\])?$")


def _values_of(content):
    if content[:1].isdigit():
        out = []
        for token in content.split(","):
            if "-" in token[1:]:
                a, b = token.split("-", 1)
                try:
                    out.extend(str(v) for v in range(int(a), int(b) + 1))
                except ValueError:
                    return [content]
            else:
                out.append(token)
        return out
    return content.split(",")


def expand_key(key):
    """image[n,e,s,w][0-1] のような、複数のキーを表す書き方を展開する（tabfile の parameter expansion）。"""
    parts = _GROUP.split(key)
    out = [parts[0]]
    for i in range(1, len(parts), 2):
        content, tail = parts[i], parts[i + 1]
        is_param = "," in content or "-" in content[1:]
        values = _values_of(content) if is_param else [content]
        out = [p + "[" + v + "]" + tail for p in out for v in values]
        if len(out) > 4096:
            return [key]
    return out


def known_key(obj_type, key):
    if key in COMMON_KEYS:
        return True
    t = OBJ_TYPES[obj_type]
    return key in t["keys"] or any(p.match(key) for p in _PATTERNS[obj_type])


def reader_of(obj_type, key):
    info = COMMON_KEYS.get(key) or OBJ_TYPES[obj_type]["keys"].get(key)
    return info["reader"] if info else None


def _way_key_findings(n, key, slopes):
    """obj=way の絵のキー 1 つ。-> [(行, コード, 文)]。slopes は坂のそろい具合の記録。"""
    m = _WAY_KEY.match(key)
    if not m:
        return []
    front, kind, name, season = m.groups()
    if front == "back":
        return [(n, "way-key", "%s: way_writer.cc の接頭辞は front だけ（back は読まない）" % key)]
    if kind == "image":
        ok = name in WAY_RIBI
        allowed = "ribi の綴り（n・ns・nse・nsew など。分岐の絵は nse1 など）"
    elif kind == "diagonal":
        ok = name in WAY_DIAGONAL
        allowed = "ne・se・nw・sw・close1・close2"
    else:
        ok = name in WAY_SLOPES
        allowed = "3・6・9・12"
        if ok:
            slopes.setdefault((front or "", kind, season or ""), set()).add(name)
    if ok:
        return []
    return [(n, "way-key", "%s の [%s] は way_writer.cc が読まない綴り。読むのは %s" % (key, name, allowed))]


def lint(text):
    """-> [(行, コード, メッセージ)]"""
    out = []
    obj_type = None
    slopes = {}
    start = 0

    def close_way():
        for (front, kind, season), got in sorted(slopes.items()):
            if got != set(WAY_SLOPES):
                out.append((start, "way-slope", "%s%s の坂が %s だけ（季節 %s）。3・6・9・12 の 4 つをそろえる（欠けた坂は絵が出ない。imageup2 は空を詰めるので別の坂の絵が出る）"
                            % (front, kind, "・".join(sorted(got, key=int)), season or "なし")))
        slopes.clear()

    for n, raw in enumerate(text.splitlines(), 1):
        if raw.startswith("#") or not raw.strip():
            continue
        if raw.lstrip().startswith("-") and not raw.startswith(" "):
            close_way()
            obj_type = None
            continue
        if raw[0] in " \t" and "=" in raw:
            out.append((n, "dropped-indent", "行頭が空白。本体はこの行を捨てるので、キーが効かない（tabfile.cc read_line）"))
            continue
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = re.sub(r"\s+(?=[^\[]*\])", "", key.strip().lower())
        if key == "obj":
            close_way()
            obj_type = value.strip()   # 本体は大文字小文字を区別する（strcmp）。そのまま比べる
            start = n
            if obj_type not in OBJ_TYPES or not OBJ_TYPES[obj_type]["top_level"]:
                out.append((n, "unknown-obj", "obj=%s は本体が知らない種類。makeobj は黙って飛ばし、pak に入らない。知っているのは %s"
                            % (obj_type, ", ".join(TOP_LEVEL))))
                obj_type = None
            continue
        if obj_type is None:
            continue
        keys = expand_key(key)
        reader = reader_of(obj_type, keys[0])
        if reader in _INT_READERS:
            val = value.split("#")[0].strip()
            ok = _FLOAT.match(val) if reader == "get_int64" else _INT.match(val)
            if val and not ok:
                out.append((n, "bad-int", "%s=%s は本体の読み方（strtol / atof）で数として読めないか、意図と違う値（08 は 8 進で 0）になる。makeobj は何も言わない"
                            % (key, val)))
        elif (reader in _TEXT_READERS and "#" in value and key not in _IMAGE_REF_KEYS
              and "image" not in key and "diagonal" not in key):
            out.append((n, "value-comment", "%s の値の後ろに # がある。dat に行末の注記は無く、値の一部になる（%r）。注記は別の行に書く"
                        % (key, value.strip())))
        for k in keys:
            if not known_key(obj_type, k):
                out.append((n, "unknown-key", "obj=%s は %r を読まない。makeobj は黙って捨てる" % (obj_type, k)))
                break
        if obj_type == "way":
            for k in keys:
                out.extend(_way_key_findings(n, k, slopes))
    close_way()
    return sorted(out)


def dat_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for dirpath, dirs, files in os.walk(p):
                dirs.sort()
                for f in sorted(files):
                    if f.lower().endswith(".dat"):
                        yield os.path.join(dirpath, f)
        else:
            yield p


_SELF_TEST = [   # (入れる行, 出るべきコード)。way の最小形に誤りを 1 つ入れる
    ("topspeed=fast", "bad-int"), ("intro_month=08", "bad-int"), ("copyright=a # b", "value-comment"),
    ("image[zz][0]=a.0.0", "way-key"), ("imageup[n][0]=a.0.0", "way-key"), ("bogus=1", "unknown-key"),
    (" cost=1", "dropped-indent"), ("imageup[3][0]=a.0.0", "way-slope"),
]
_SELF_OK = ["topspeed=0x10", "cost=1.5", "icon=> a.0.0 # note", "image[new2][0]=a.0.0 # note", "diagonal[close1][0]=a.0.0"]


def self_test():
    base = "obj=way\nname=t\nwaytype=road\n"
    bad = 0
    for line, code in _SELF_TEST:
        got = {c for _n, c, _m in lint(base + line + "\n")}
        if code not in got:
            print("self-test: %r で %s が出ない（出た: %s）" % (line, code, sorted(got)))
            bad += 1
    for line in _SELF_OK:
        got = lint(base + line + "\n")
        if got:
            print("self-test: %r が誤検出された: %s" % (line, got))
            bad += 1
    if "unknown-obj" not in {c for _n, c, _m in lint("obj=Way\nname=t\n")}:
        print("self-test: obj=Way で unknown-obj が出ない")
        bad += 1
    return bad


def main(argv):
    if argv == ["--self-test"]:
        bad = self_test()
        print("self-test: %s" % ("失敗 %d" % bad if bad else "ok"))
        return 1 if bad else 0
    if not argv:
        print(__doc__)
        return 2
    files = list(dat_files(argv))
    bad = 0
    for path in files:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            for line, code, msg in lint(f.read()):
                print("%s:%d: error [%s]: %s" % (path, line, code, msg))
                bad += 1
    print("%d file(s), %d error(s)" % (len(files), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
