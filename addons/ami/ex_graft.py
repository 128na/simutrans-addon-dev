"""pak の way・way-object に、分岐の追加画像（ex 画像。絵の番号 26〜35）を継ぎ足す（AMI 専用。配布・サポートはしない）。

makeobj の dat のキーは image[nsew2]（25 番）までで、26〜35 番を書けない（docs/reference/way-addon.md の 9.1）。そこで、
26〜35 番に入れたい絵を 16〜25 番（image[nse1]〜image[nsew2]）に割り当てた「提供用」の物を makeobj で別の pak に作り、
その 10 枚の画像ノードを、対象の物の画像リストの末尾へ写す。写す順がそのまま 26〜35 番になる。

    python -X utf8 ex_graft.py --donor work/ex/donor.pak dist/ami.pak dist/ami_rail.pak   # 対象の pak を書き換える
    python -X utf8 ex_graft.py --list dist/ami_rail.pak                                    # 物ごとの画像リストの枚数を出す

- 提供用の物の名前は、対象の名前 + DONOR_SUFFIX。対象の pak に同じ名前の物（way か way-object）があるものだけを書き換える
- 写す画像リストは、ちょうど 26 枚のもの（way は分岐の絵を持つ向きの絵のリスト、way-object は手前と奥の向きの絵のリスト）。
  提供用と対象で、その数と並び（子ノードの順）が合わなければ止まる。すでに 26 枚を超えているリストがあっても止まる（二重に継ぎ足さない）
- 直すのはリストごとに 2 か所: ノードの見出しの子の数と、データの先頭の count（どちらも uint16）。親のノードには長さの欄が無いので、ほかは変えない。
  way ノードのデータ（版によって長さが違う）は読まない
- 標準ライブラリだけで動く（CI の Linux でも同じ）
"""
import argparse
import os
import struct
import sys

DONOR_SUFFIX = "__ex_donor"
SWITCH_COUNT = 26      # 分岐の絵（switch 画像）まで持つリストの枚数
EX_COUNT = 10          # 継ぎ足す枚数（26〜35 番）
LARGE = 0xFFFF         # ノードの大きさがこの値なら、続く uint32 が本当の大きさ
TYPES = (b"WAY\0", b"WYOB")  # 書き換える物の種類（way・way-object）
IMG_LIST = b"IMG1"
TEXT = b"TEXT"


class Node:
    __slots__ = ("type", "data", "children")

    def __init__(self, typ, data, children):
        self.type, self.data, self.children = typ, data, children


def _read_node(buf, pos):
    typ = buf[pos:pos + 4]
    n_child, size = struct.unpack_from("<HH", buf, pos + 4)
    pos += 8
    if size == LARGE:
        (size,) = struct.unpack_from("<I", buf, pos)
        pos += 4
    data = buf[pos:pos + size]
    pos += size
    children = []
    for _ in range(n_child):
        child, pos = _read_node(buf, pos)
        children.append(child)
    return Node(typ, data, children), pos


def _write_node(node, out):
    size = len(node.data)
    if size >= LARGE:
        out += node.type + struct.pack("<HHI", len(node.children), LARGE, size)
    else:
        out += node.type + struct.pack("<HH", len(node.children), size)
    out += node.data
    for child in node.children:
        _write_node(child, out)


def read_pak(path):
    """(見出しのバイト列, ルートのノード) を返す。見出しは 0x1A までの文字と、続く版の uint32"""
    with open(path, "rb") as f:
        buf = f.read()
    end = buf.index(b"\x1a") + 1 + 4
    root, pos = _read_node(buf, end)
    if pos != len(buf):
        sys.exit(f"[ex_graft] {path}: ルートのノードの後ろに {len(buf) - pos} バイト余りがある（読めない形）")
    return buf[:end], root


def write_pak(path, head, root):
    out = bytearray(head)
    _write_node(root, out)
    with open(path, "wb") as f:
        f.write(out)


def name_of(node):
    text = next((c for c in node.children if c.type == TEXT), None)
    return text.data.split(b"\0", 1)[0].decode("utf8", "replace") if text else ""


def _count(lst):
    return struct.unpack_from("<H", lst.data, 0)[0]


def switch_lists(node):
    """分岐の絵まで持つ画像リスト（子の数も count も 26 より多いか 26 のもの）を、子ノードの順に返す"""
    return [c for c in node.children if c.type == IMG_LIST and max(len(c.children), _count(c)) >= SWITCH_COUNT]


def objects(root):
    return {name_of(n): n for n in root.children if n.type in TYPES}


def graft(target_path, donors):
    head, root = read_pak(target_path)
    done = []
    for name, node in objects(root).items():
        donor = donors.get(name + DONOR_SUFFIX)
        if donor is None:
            continue
        if donor.type != node.type:
            sys.exit(f"[ex_graft] {name}: 提供用の物の種類が違う（{donor.type!r} と {node.type!r}）")
        src, dst = switch_lists(donor), switch_lists(node)
        if not dst or len(src) != len(dst):
            sys.exit(f"[ex_graft] {name}: 26 枚のリストの数が合わない（提供用 {len(src)}、対象 {len(dst)}）")
        for i, (s, d) in enumerate(zip(src, dst)):
            for lst, who in ((s, "提供用"), (d, "対象")):
                if len(lst.children) != SWITCH_COUNT or _count(lst) != SWITCH_COUNT:
                    sys.exit(f"[ex_graft] {name}: {who}の {i} 番目のリストが {len(lst.children)} 枚（count {_count(lst)}）。"
                             f"ちょうど {SWITCH_COUNT} 枚でない（継ぎ足し済みか、分岐の絵が無い）")
            d.children.extend(s.children[16:16 + EX_COUNT])
            d.data = struct.pack("<H", len(d.children)) + d.data[2:]
        done.append(f"{name}（{len(dst)} リスト）")
    write_pak(target_path, head, root)
    return done


def list_pak(path):
    _, root = read_pak(path)
    for name, node in objects(root).items():
        counts = [len(c.children) for c in node.children if c.type == IMG_LIST]
        print(f"{node.type.decode('ascii', 'replace').strip(chr(0))} {name}: {counts}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--donor", help="提供用の物（名前 + " + DONOR_SUFFIX + "）を入れた pak")
    ap.add_argument("--list", action="store_true", help="書き換えず、物ごとの画像リストの枚数を出す")
    ap.add_argument("paks", nargs="+", help="対象の pak（その場で書き換える）")
    a = ap.parse_args()
    if a.list:
        for p in a.paks:
            list_pak(p)
        return
    if not a.donor:
        ap.error("--donor が要る")
    _, droot = read_pak(a.donor)
    donors = {n: node for n, node in objects(droot).items() if n.endswith(DONOR_SUFFIX)}
    if not donors:
        sys.exit(f"[ex_graft] {a.donor}: 提供用の物（名前が {DONOR_SUFFIX} で終わる物）が無い")
    for p in a.paks:
        done = graft(p, donors)
        print(f"[ex_graft] {os.path.basename(p)}: {len(done)} 個に継ぎ足した")


if __name__ == "__main__":
    main()
