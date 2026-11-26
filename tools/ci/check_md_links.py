"""addons/ と .claude/ の md の相対リンクとアンカーを検査する（#315）。

docs-lint が見るのは直下と docs/ の md だけで、アンカー（`#見出し`）はどこも見ないので、
残りをここで見る。標準ライブラリだけで動く。

    python -X utf8 tools/ci/check_md_links.py

- 検査するのは addons/ と .claude/ の下の md（.claude/worktrees/ は除く）。
- 相対リンクは、指す先が git の管理下（か、まだ add していない新しいファイル）にあること。
  大文字小文字も合っていること（Windows では通っても GitHub では切れる）。
- md へのアンカーは、指す先の見出しから GitHub と同じ作り方で作った名前か、
  `<a id="…">` / `<a name="…">` にあること。指す先は検査の対象外の md でもよい。
- コードの中（``` の囲みと `…`）のリンクと `#` は見ない。外の URL は見ない。
"""

import argparse
import html
import posixpath
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

SOURCE_DIRS = ("addons/", ".claude/")
# リポジトリの直下からの相対パスで比べる。パスの途中の名前で判定すると、
# worktree の中で流したときに全部を飛ばす（#304）。
SKIP_PREFIXES = (".claude/worktrees/",)

FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
QUOTE = re.compile(r"^(?: {0,3}> ?)+")
ATX = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+(.*?))?[ \t]*$")
SETEXT = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
NOT_PARAGRAPH = re.compile(r"^(?: {0,3}(?:[#>|]|[-*+][ \t]|\d+[.)][ \t])| {4}|\t)")
CODE_SPAN = re.compile(r"(?<![`\\])(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
COMMENT = re.compile(r"<!--.*?-->", re.S)
REF_DEF = re.compile(r"^ {0,3}\[(?!\^)[^\]]+\]:[ \t]*(<[^>\n]*>|\S+)", re.M)
HTML_LINK = re.compile(r"""<(?:a|img|source)\b[^<>]*?\s(?:href|src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
HTML_ANCHOR = re.compile(r"""<[a-zA-Z][^<>]*?\s(?:id|name)\s*=\s*(?:"([^"]*)"|'([^']*)')""")
SCHEME = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]+:|//)")


def prose_lines(text):
    """コードの囲み・HTML のコメント・先頭の front matter を空行にした行の並び。行番号は保つ。"""
    lines = text.lstrip("﻿").split("\n")
    lines = [line.rstrip("\r") for line in lines]
    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i] == "---":
                lines[: i + 1] = [""] * (i + 1)
                break
    fence = None
    for i, line in enumerate(lines):
        m = FENCE.match(QUOTE.sub("", line))
        if fence:
            if m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not m[2].strip():
                fence = None
            lines[i] = ""
        elif m and not (m[1][0] == "`" and "`" in m[2]):
            fence = m[1]
            lines[i] = ""
    body = COMMENT.sub(lambda m: "\n" * m[0].count("\n"), "\n".join(lines))
    return body.split("\n")


def heading_text(raw):
    """見出しの md を、画面に出る文字にする。"""
    codes = []

    def keep(m):
        codes.append(m[2].strip())
        return f"\x00{len(codes) - 1}\x00"

    s = CODE_SPAN.sub(keep, raw)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[((?:[^\[\]]|\[[^\]]*\])*)\](?:\((?:[^()]|\([^()]*\))*\)|\[[^\]]*\])", r"\1", s)
    s = re.sub(r"</?[a-zA-Z][^<>]*>", "", s)
    s = re.sub(r"(?<!\w)(_{1,3})(?=\S)(.+?)(?<=\S)\1(?!\w)", r"\2", s)
    s = html.unescape(s)
    return re.sub("\x00(\\d+)\x00", lambda m: codes[int(m[1])], s).strip()


def slugify(text):
    """GitHub の見出しのアンカー名。文字・結合文字・数字・_・-・空白だけを残し、空白を - にする。"""
    kept = []
    for c in text.lower():
        cat = unicodedata.category(c)
        if c in " -" or cat[0] in "LM" or cat in ("Nd", "Nl", "Pc"):
            kept.append(c)
    return "".join(kept).replace(" ", "-")


def headings(lines):
    previous = ""
    for line in lines:
        line = QUOTE.sub("", line)
        m = ATX.match(line)
        if m:
            yield re.sub(r"(?:^|[ \t])#+$", "", m[1] or "")
            previous = ""
            continue
        if SETEXT.match(line) and previous:
            yield previous
            previous = ""
            continue
        if not line.strip() or NOT_PARAGRAPH.match(line):
            previous = ""
        else:
            previous = f"{previous} {line.strip()}".strip()


def heading_slugs(lines):
    """見出しのアンカー名を上から順に返す。同じ名前の 2 つ目からは -1, -2 が付く。"""
    slugs, used = [], {}
    for raw in headings(lines):
        base = slugify(heading_text(raw))
        slug = base
        while slug in used:
            used[base] += 1
            slug = f"{base}-{used[base]}"
        used[slug] = 0
        slugs.append(slug)
    return slugs


def anchors_of(text):
    lines = prose_lines(text)
    found = set(heading_slugs(lines))
    body = CODE_SPAN.sub("", "\n".join(lines))
    found.update(a or b for a, b in HTML_ANCHOR.findall(body))
    return found


def strip_code_spans(body):
    """`…` を消す。対になる ` は、同じ段落（表と箇条書きは 1 項目）の中だけで探す。"""

    def blank(m):
        return "\n" * m[0].count("\n")

    blocks, block = [], []
    for line in body.split("\n"):
        starts = re.match(r"^\s*(?:$|[|#]|[-*+][ \t]|\d+[.)][ \t])", line)
        if starts and block:
            blocks.append("\n".join(block))
            block = []
        block.append(line)
    if block:
        blocks.append("\n".join(block))
    return "\n".join(CODE_SPAN.sub(blank, b) for b in blocks)


def destination(body, i):
    """`](` の直後から、リンク先を読む。リンクの形でなければ None。"""
    m = re.compile(r"[ \t\n]*").match(body, i)
    i = m.end()
    if body.startswith("<", i):
        end = body.find(">", i)
        if end < 0 or "\n" in body[i:end]:
            return None
        dest, i = body[i + 1 : end], end + 1
    else:
        start, depth = i, 0
        while i < len(body) and body[i] not in " \t\n":
            if body[i] == "\\":
                i += 1
            elif body[i] == "(":
                depth += 1
            elif body[i] == ")":
                if depth == 0:
                    break
                depth -= 1
            i += 1
        dest = body[start:i]
    closing = re.compile(r"""[ \t\n]*(?:(?:"[^"]*"|'[^']*'|\([^()]*\))[ \t\n]*)?\)""")
    return dest if closing.match(body, i) else None


def links(text):
    """(行番号, リンク先) を返す。"""
    body = strip_code_spans("\n".join(prose_lines(text)))
    found = []
    for m in re.finditer(r"\]\(", body):
        dest = destination(body, m.end())
        if dest:
            found.append((m.start(), dest))
    for m in REF_DEF.finditer(body):
        found.append((m.start(1), m[1].strip("<>")))
    for m in HTML_LINK.finditer(body):
        found.append((m.start(), m[1] if m[1] is not None else m[2]))
    return [(body.count("\n", 0, pos) + 1, dest) for pos, dest in sorted(found)]


def repo_files(root):
    """管理下のファイルと、まだ add していない新しいファイル（無視しているものは除く）。"""
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    return {p for p in out.split("\0") if p and (root / p).exists()}


def is_source(path):
    return path.endswith(".md") and path.startswith(SOURCE_DIRS) and not path.startswith(SKIP_PREFIXES)


def check(root, files):
    """(検査した md の数, 見たリンクの数, 誤りの行) を返す。"""
    dirs = {""}
    for f in files:
        parent = posixpath.dirname(f)
        while parent not in dirs:
            dirs.add(parent)
            parent = posixpath.dirname(parent)

    cache = {}

    def anchors(path):
        if path not in cache:
            cache[path] = anchors_of((root / path).read_text(encoding="utf-8"))
        return cache[path]

    sources = sorted(f for f in files if is_source(f))
    count, errors = 0, []
    for source in sources:
        for line, raw in links((root / source).read_text(encoding="utf-8")):
            if SCHEME.match(raw) and not raw.lower().startswith("file:"):
                continue
            count += 1

            def fail(reason, source=source, line=line, raw=raw):
                errors.append(f"{source}:{line}: {reason}: {raw}")

            path, _, fragment = raw.partition("#")
            path, _, query = path.partition("?")
            path, fragment = unquote(path), unquote(fragment)
            if path.startswith(("/", "~")) or re.match(r"^(?:[a-zA-Z]:|file:)", path):
                fail("絶対パスのリンクは使わない")
                continue
            if path:
                target = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
                target = "" if target == "." else target
                if target == ".." or target.startswith("../"):
                    fail("リポジトリの外を指す")
                    continue
                if target not in files and target not in dirs:
                    fail("リンク先が無い")
                    continue
            else:
                target = source
            if not fragment:
                continue
            if target in dirs:
                target = posixpath.join(target, "README.md")
            if not target.endswith(".md"):
                continue
            if "plain=1" in query and re.fullmatch(r"L\d+(-L\d+)?", fragment):
                continue
            if target not in files or fragment not in anchors(target):
                fail("アンカーが無い")
    return len(sources), count, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    root = parser.parse_args().root.resolve()
    sys.stdout.reconfigure(encoding="utf-8")

    sources, count, errors = check(root, repo_files(root))
    for e in errors:
        print(f"ERROR {e}")
    print(f"check_md_links: {sources} md, {count} links, {len(errors)} error(s)")
    if sources == 0:
        print("ERROR 検査する md が 1 つも無い（対象の選び方の誤り）")
        return 1
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
