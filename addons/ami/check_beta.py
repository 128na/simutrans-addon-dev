"""配る pak の読み込みの確認（ingame/beta_check.nut）が、dat の物の種類に追いついているかを、ゲームなしで見る（#408）。

    python -X utf8 check_beta.py              # 検査
    python -X utf8 check_beta.py --self-test  # 抜けた表を見つけられるかの確かめ

見るもの（敷く物は beta_check.sh と同じく src/*.dat。分岐の追加画像の提供用 ex_donors.dat は除く）:
    - 1 つの dat は 1 つの物（beta_check.sh の awk は 1 ファイルに 1 物しか読まない）
    - obj（building は type）に、beta_check.nut の敷き方の分岐がある
    - way・way-object の waytype が WT に、way-object・車庫・操車場の waytype が CARRIER に、車庫の waytype が DEPOT_OBJ にある
    - beta_check.nut の運び手の名前（"ami_…"）が dat にある。CARRIER の運び手は、キーの waytype の way
    - way-object ごとに beta_check.nut が選ぶ運び手（CARRIER、名前に _old があれば _old を付けた物、OVERRIDE の差し替え）が、その waytype の way
    - 電化の名前（_catenary・_power・_guide）の way-object は own_waytype=electrified_track（beta_check.nut は電化を own_waytype で判定する）
実際に敷けるかは beta_check.sh をゲームで流して見る。
"""
import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NUT = os.path.join(HERE, "ingame", "beta_check.nut")
SKIP = "ex_donors.dat"
KEYS = ("obj", "name", "waytype", "type", "own_waytype")
ELECTRIC_NAME = re.compile(r"_(catenary|power|guide)")  # way-object だけに当てる
NEEDS = {  # 敷き方（obj、building は obj と type） → waytype が要る表
    "way": ("WT",),
    "way-object": ("WT", "CARRIER"),
    "building depot": ("CARRIER", "DEPOT_OBJ"),
    "building stop": ("CARRIER",),
}


def dat_items():
    """[(ファイル名, [物ごとの {キー: 値}])]"""
    result = []
    for path in sorted(glob.glob(os.path.join(HERE, "src", "*.dat"))):
        if os.path.basename(path) == SKIP:
            continue
        objs = []
        with open(path, encoding="utf8") as f:
            for line in f:
                key, sep, value = line.strip().partition("=")
                key = key.lower()
                if not sep or key not in KEYS:
                    continue
                if key == "obj":
                    objs.append({})
                if objs:
                    objs[-1][key] = value
        result.append((os.path.basename(path), objs))
    return result


def parse_nut(text):
    """beta_check.nut の (表の名前 → {キー: 値}、OVERRIDE は [(waytype, 語, 運び手)], 敷き方の集合, 運び手の名前の集合)"""
    code = "\n".join(line.split("//")[0] for line in text.splitlines())
    tables = {}
    for name in ("CARRIER", "DEPOT_OBJ", "WT"):
        m = re.search(rf"^local {name} = \{{(.*?)\}};", code, re.M)
        tables[name] = dict(re.findall(r'(\w+)\s*=\s*"?(\w+)', m[1])) if m else {}
    m = re.search(r"^local OVERRIDE = \[(.*)\];", code, re.M)
    tables["OVERRIDE"] = re.findall(r'\["(\w+)", "(\w+)", "(\w+)"\]', m[1]) if m else []
    kinds = set()
    for m in re.finditer(r'obj == "([\w-]+)"(?: && it\[4\] == "(\w+)")?', code):
        kinds.add(f"{m[1]} {m[2]}" if m[2] else m[1])
    carriers = {n for n in re.findall(r'"(ami_\w+)"', code) if not n.endswith("_")}
    return tables, kinds, carriers


def check(items, nut):
    tables, kinds, carriers = parse_nut(nut)
    errors = [f"beta_check.nut の表 {n} が読めない" for n, keys in tables.items() if not keys]
    names = set()
    for fname, objs in items:
        if len(objs) != 1:
            errors.append(f"{fname}: 物が {len(objs)} 個ある（beta_check.sh は 1 ファイルに 1 物だけを敷く）")
        for o in objs:
            name = o.get("name", fname)
            names.add(name)
            kind = f"building {o.get('type', '')}" if o["obj"] == "building" else o["obj"]
            if kind not in kinds:
                errors.append(f"{name}: beta_check.nut に {kind} の敷き方が無い")
                continue
            errors += [f"{name}: beta_check.nut の {t} に waytype={o.get('waytype')} が無い"
                       for t in NEEDS.get(kind, ()) if o.get("waytype") not in tables[t]]
    errors += [f"beta_check.nut の運び手が dat に無い: {n}" for n in sorted(carriers - names)]
    ways = {(o.get("name"), o.get("waytype")) for _, objs in items for o in objs if o["obj"] == "way"}
    errors += [f"beta_check.nut の CARRIER の {wt} の運び手が、その waytype の way でない: {n}"
               for wt, n in tables["CARRIER"].items() if (n, wt) not in ways]
    for _, objs in items:
        for o in objs:
            if o["obj"] != "way-object":
                continue
            name, wt = o.get("name", ""), o.get("waytype")
            if ELECTRIC_NAME.search(name) and o.get("own_waytype") != "electrified_track":
                errors.append(f"{name}: 電化の名前だが own_waytype={o.get('own_waytype')}（electrified_track でない）")
            if wt not in tables["CARRIER"]:
                continue  # 上で出している
            # beta_check.nut の check_wayobj と同じ順で運び手を選ぶ
            carrier = tables["CARRIER"][wt] + ("_old" if "_old" in name else "")
            for owt, word, other in tables["OVERRIDE"]:
                if wt == owt and word in name:
                    carrier = other
            if (carrier, wt) not in ways:
                errors.append(f"{name}: beta_check.nut の運び手 {carrier} が waytype={wt} の way でない")
    return errors


def self_test():
    nut = ('local CARRIER = {track = "ami_a"};\nlocal DEPOT_OBJ = {track = mo_depot_rail};\nlocal WT = {track = wt_rail};\n'
           'if (obj == "way") r = 1;\nelse if (obj == "way-object") r = 2;\n'
           'else if (obj == "building" && it[4] == "depot") r = 3;\nelse if (obj == "building" && it[4] == "stop") r = 4;\n'
           'local OVERRIDE = [["track", "sub", "ami_a"]];\n')

    def items(*objs):
        return [(f"{o['name']}.dat", [o]) for o in objs]

    way = {"obj": "way", "name": "ami_a", "waytype": "track"}
    depot = {"obj": "building", "name": "d", "type": "depot", "waytype": "track"}
    wayobj = {"obj": "way-object", "name": "o", "waytype": "track"}
    stop = {"obj": "building", "name": "s", "type": "stop", "waytype": "track"}
    bad = {
        "知らない waytype の way": (items(way, {**way, "name": "m", "waytype": "maglev_track"}), nut),
        "運び手の無い way-object": (items(way, {**wayobj, "waytype": "maglev_track"}), nut),
        "運び手の無い操車場": (items(way, {**stop, "waytype": "maglev_track"}), nut),
        "DEPOT_OBJ だけの抜け": (items(way, depot), nut.replace("DEPOT_OBJ = {track", "DEPOT_OBJ = {road")),
        "運び手の waytype が表のキーと違う": (items({**way, "waytype": "road"}), nut.replace("WT = {track", "WT = {road = wt_road, track")),
        "運び手の無い車庫": (items(way, {**depot, "waytype": "maglev_track"}), nut),
        "知らない type の建物": (items(way, {**depot, "type": "cur"}), nut),
        "知らない obj": (items(way, {"obj": "tunnel", "name": "t", "waytype": "track"}), nut),
        "運び手の名前が dat に無い": (items({**way, "name": "ami_b"}), nut),
        "1 ファイルに 2 物": ([("two.dat", [way, {**way, "name": "ami_c"}])], nut),
        "表が読めない": (items(way), nut.replace("local WT = ", "local WT2 = ")),
        "OVERRIDE が読めない": (items(way), nut.replace("local OVERRIDE = ", "local OVERRIDE2 = ")),
    }
    # 別の理由の誤りで通らないように、出る誤りの文も見る
    road = {**way, "name": "ami_r", "waytype": "road"}
    old = {**way, "name": "ami_a_old"}
    catenary = {**wayobj, "name": "o_catenary", "own_waytype": "electrified_track"}
    expected = {
        "差し替えの運び手の waytype が違う": ("運び手 ami_r が", items(way, road, {**wayobj, "name": "o_sub"}),
                                    nut.replace('"sub", "ami_a"', '"sub", "ami_r"').replace("WT = {track", "WT = {road = wt_road, track")),
        "_old の運び手が無い": ("運び手 ami_a_old が", items(way, {**wayobj, "name": "o_old"}), nut),
        "電化の名前で own_waytype が違う": ("電化の名前", items(way, {**catenary, "own_waytype": "track"}), nut),
    }
    good = items(way, old, wayobj, catenary, {**wayobj, "name": "o_sub"}, {**wayobj, "name": "o_old"}, depot, stop)
    errors = [f"正しい物で誤り: {e}" for e in check(good, nut)]
    errors += [f"見逃した: {label}" for label, args in bad.items() if not check(*args)]
    errors += [f"見逃した: {label}" for label, (text, *args) in expected.items() if not any(text in e for e in check(*args))]
    if errors:
        sys.exit("[check_beta] self-test 失敗: " + " / ".join(errors))
    print(f"[check_beta] self-test ok（見つける {len(bad) + len(expected)}）")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--nut", default=NUT, help="比べる beta_check.nut（直す前の版で落ちるかを確かめるとき）")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    items = dat_items()
    if not items:
        sys.exit("[check_beta] dat が 1 つも読めない")
    with open(args.nut, encoding="utf8") as f:
        errors = check(items, f.read())
    if errors:
        sys.exit("[check_beta] 失敗:\n  " + "\n  ".join(errors))
    print(f"[check_beta] ok（dat の物 {len(items)}、beta_check.nut の敷き方と表がそろっている）")


if __name__ == "__main__":
    main()
