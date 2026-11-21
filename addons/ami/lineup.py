"""AMI の物の一覧を src/ の dat から作る（アドオンのディレクトリで `python -X utf8 lineup.py`。#138）。

    python -X utf8 lineup.py                                # 種類別の 4 つの pak の一覧を標準出力へ（txt の表）
    python -X utf8 lineup.py --paks ami_rail ami_road -o work/lineup.txt
    python -X utf8 lineup.py --format html -o work/lineup.html

手で書かず dat から作るので、一覧は dat と必ず一致する。どの dat がどの pak に入るかは build.py の KINDS（名前の頭）。
release.py は zip を作るときに、選んだ pak の分の一覧（txt）を ami_lineup.txt として入れる。
列: 名前・種類・最高速度（km/h）・購入費（cr）・維持費（cr/月）・登場年。dat の cost・maintenance は 1/100 cr なので 100 で割る。
知らない obj があれば止まる（新しい種類を足したら KIND_LABELS を直す）。
"""
import argparse
import glob
import html
import os
import sys
import unicodedata

from build import KINDS

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")

WAYTYPES = {
    "track": "線路",
    "road": "道路",
    "tram_track": "路面軌道",
    "water": "運河",
    "monorail_track": "モノレール",
    "maglev_track": "リニア",
    "narrowgauge_track": "狭軌",
}
# 別の waytype を借りている way（橋脚は路面軌道、歩道は運河。iss と同じ作り）。種類はこの名前で出し、速度の欄は空ける
SPECIAL_WAYS = {"ami_pier_rail": "線路の橋脚", "ami_pier_road": "道路の橋脚", "ami_sidewalk": "歩道"}
OBJ_ORDER = ("way", "bridge", "tunnel", "way-object", "crossing", "building")
COLUMNS = ("名前", "種類", "最高速度", "購入費", "維持費", "登場年")
NOTE = (
    "この一覧はアドオンの定義（dat）から自動で作っています。最高速度は km/h、購入費は cr、維持費は cr/月です。"
    "壁・橋脚・歩道・車庫は速度の欄を空けています。踏切の最高速度は「道路/線路」の順です。"
)


def read_dat(path):
    """dat の物のキーと値（キーは小文字）。AMI の dat は 1 ファイルに 1 つの物。2 つ目の物があれば止まる（一覧から黙って落とさない）"""
    obj = {}
    after_sep = False
    with open(path, encoding="utf8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("---"):
                after_sep = True
                continue
            if after_sep and line.lower().startswith("obj="):
                raise ValueError(f"{os.path.basename(path)}: 1 つの dat に物が 2 つ以上ある（lineup.py は 1 つずつを前提にしている）")
            if after_sep or not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            obj.setdefault(k.strip().lower(), v.strip())
    return obj


def waytype(v):
    return WAYTYPES.get(v, v)


def kind_label(o):
    """遊ぶ人向けの種類の名前"""
    t = o.get("obj")
    wt = waytype(o.get("waytype", ""))
    name = o.get("name", "")
    for prefix, label in SPECIAL_WAYS.items():
        if t == "way" and name.startswith(prefix):
            return label
    if t == "way":
        if o.get("system_type") == "1":
            return wt + "（高架）"
        return wt + ("（基盤）" if "_base_" in o.get("name", "") else "")
    if t == "bridge":
        return f"{wt}の橋"
    if t == "tunnel":
        return f"{wt}のトンネル"
    if t == "way-object":
        own = o.get("own_waytype", "")
        part = "壁" if name.startswith("ami_wall_") else "付属物"
        return f"{wt}の{part}" + ("（架線つき）" if own == "electrified_track" else "")
    if t == "crossing":
        return f"踏切（{waytype(o.get('waytype[0]', ''))}×{waytype(o.get('waytype[1]', ''))}）"
    if t == "building" and o.get("type") == "depot":
        return f"{wt}の車庫"
    raise ValueError(f"{o.get('name')}: 知らない obj（{t} {o.get('type', '')}）。lineup.py の kind_label に足す")


def money(v):
    if v is None:
        return ""
    try:
        n = int(v)
    except ValueError:
        raise ValueError(f"数でない費用: {v}") from None
    return f"{n // 100:,}" if n % 100 == 0 else f"{n / 100:,.2f}"


def speed(o):
    t = o.get("obj")
    if t == "crossing":
        return "/".join(o.get(f"speed[{i}]", "?") for i in (0, 1))
    if t in ("way-object", "building") or o.get("name", "").startswith(tuple(SPECIAL_WAYS)):
        return ""
    return o.get("topspeed", "")


def row(o):
    return (
        o["name"],
        kind_label(o),
        speed(o),
        money(o.get("cost")),
        money(o.get("maintenance")),
        o.get("intro_year", ""),
    )


def pak_rows(pak):
    """pak の名前（拡張子なし）に入る物の行。並びは種類（OBJ_ORDER）、名前の順"""
    if pak == "ami":
        prefixes = ("",)
    elif pak + ".pak" in KINDS:
        prefixes = KINDS[pak + ".pak"]
    else:
        raise ValueError(f"知らない pak: {pak}（build.py の KINDS）")
    objs = []
    for path in sorted(glob.glob(os.path.join(SRC, "ami_*.dat"))):
        if os.path.basename(path).startswith(prefixes):
            o = read_dat(path)
            if "name" not in o:
                raise ValueError(f"{path}: name が無い")
            objs.append(o)
    objs.sort(key=lambda o: (OBJ_ORDER.index(o["obj"]) if o.get("obj") in OBJ_ORDER else len(OBJ_ORDER), o["name"]))
    return [row(o) for o in objs]


def check_kinds():
    """種類別の pak の物を合わせると全部入り（ami）と同じになるか。どの KINDS にも当たらない dat があれば、その名前を返す"""
    every = {r[0] for r in pak_rows("ami")}
    parts = [r[0] for k in KINDS for r in pak_rows(k[:-4])]
    return sorted(every - set(parts)) + sorted({n for n in parts if parts.count(n) > 1})


def width(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, w, right):
    sp = " " * (w - width(s))
    return sp + s if right else s + sp


def render_txt(title, sections):
    """sections: [(pak の名前, 行のリスト)]。全角を 2 桁として列をそろえる"""
    right = (False, False, True, True, True, True)
    allrows = [COLUMNS] + [r for _, rows in sections for r in rows]
    ws = [max(width(r[i]) for r in allrows) for i in range(len(COLUMNS))]
    out = [title, "", NOTE, ""]
    for pak, rows in sections:
        out.append(f"■ {pak}.pak（{len(rows)} 個）")
        out.append("  " + "  ".join(pad(c, ws[i], right[i]) for i, c in enumerate(COLUMNS)).rstrip())
        out.append("  " + "  ".join("-" * w for w in ws))
        for r in rows:
            out.append("  " + "  ".join(pad(c, ws[i], right[i]) for i, c in enumerate(r)).rstrip())
        out.append("")
    return "\n".join(out)


def render_html(title, sections):
    e = html.escape
    out = [
        "<!doctype html>",
        '<html lang="ja"><head><meta charset="utf-8">',
        f"<title>{e(title)}</title>",
        "<style>table{border-collapse:collapse}th,td{border:1px solid #ccc;padding:2px 6px}"
        "td.n{text-align:right}</style>",
        "</head><body>",
        f"<h1>{e(title)}</h1>",
        f"<p>{e(NOTE)}</p>",
    ]
    for pak, rows in sections:
        out.append(f"<h2>{e(pak)}.pak（{len(rows)} 個）</h2>")
        out.append("<table><thead><tr>" + "".join(f"<th>{e(c)}</th>" for c in COLUMNS) + "</tr></thead><tbody>")
        for r in rows:
            cells = "".join(f'<td{" class=n" if i >= 2 else ""}>{e(c)}</td>' for i, c in enumerate(r))
            out.append(f"<tr>{cells}</tr>")
        out.append("</tbody></table>")
    out.append("</body></html>")
    return "\n".join(out)


def lineup(paks, version=None, fmt="txt"):
    title = "AMI（AI Marunage Infrastructure）" + (f"{version} " if version else "") + "物の一覧"
    sections = [(p, pak_rows(p)) for p in paks]
    return (render_html if fmt == "html" else render_txt)(title, sections)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paks", nargs="+", default=[k[:-4] for k in KINDS], help="pak の名前（拡張子なし）。ami は全部入り")
    ap.add_argument("--version", help="見出しに入れる版の名前")
    ap.add_argument("--format", choices=("txt", "html"), default="txt")
    ap.add_argument("-o", "--output", help="書き出すファイル（無ければ標準出力）")
    ap.add_argument("--check", action="store_true", help="全部の dat から作れることと、種類別の pak で全部の物を一度ずつ覆うことを確かめる（check.sh）")
    a = ap.parse_args()
    if a.check:
        try:
            bad = check_kinds()
        except ValueError as err:
            sys.exit(f"[lineup] {err}")
        if bad:
            sys.exit("[lineup] 種類別の pak に入らないか、二重に入る物: " + " ".join(bad))
        print(f"[lineup] {len(pak_rows('ami'))} 個の物が種類別の pak に一度ずつ入る")
        return
    try:
        text = lineup(a.paks, a.version, a.format)
    except ValueError as err:
        sys.exit(f"[lineup] {err}")
    if a.output:
        os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
        with open(a.output, "w", encoding="utf8") as f:
            f.write(text)
        print(f"[lineup] {a.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()
