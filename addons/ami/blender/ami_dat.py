"""AMI の dat を書き出す（Blender は使わない。アドオンのディレクトリで `python -X utf8 blender/ami_dat.py`）。

値（速度・費用・維持費・登場年）は VALUES が持つ。README の「値の一覧」と同じにする。
まだ絵を作っていない way は BUILT に入れない（dat も pak も作らない）。シートの行の並びは
    夏の絵 4 行（奥の絵）→ 雪の絵 4 行
で、無壁の線路の並び。カーブは斜めの絵（DIAG_CURVES）を指す。橋の版は、そのステップで足す。
高架の版（ami_rail_ballast_elev_<版>）は基盤の版と同じ並びで system_type=1。橋脚の way（ami_pier_rail）は行 0〜3 だけで、雪の絵も同じセル。

基盤の版の way（ami_rail_ballast_base_<版>）は通常の版と同じ並びで、近い斜めの絵を持たない（本体が分け合うタイルに 2 本の way を置き、
奥の線と手前の線を別の版にできる。docs/reference/way-addon.md の 6 章）。壁の way-object（ami_wall_rail_<版>）のシートは
    奥の絵 4 行（backimage）→ 手前の絵 4 行（frontimage）
で、セルの位置は way と同じ。雪の絵は無い（way-object に雪のキーが無い）。ami_wall_rail_twin は近い斜めの分け合うタイル用で、
back と front のシートの斜めのセルを指す（README の「壁の敷き方」）。

架線つきの壁の way-object（ami_wall_rail_<版>_catenary）は壁と同じ並びで、own_waytype=electrified_track（電化）。
ami_wall_rail_twin_catenary は近い斜めの分け合うタイル用で、斜めの梁を短くした back と front の架線つきのシート
（ami_wall_rail_twin_catenary_<back|front>）の斜めのセルを指す（README の「架線の作り」）。
"""
import os

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
NL = chr(10)
SNOW_ROWS = 4  # 雪の絵は、夏の絵の 4 行下

IMAGES = (  # (キー, 添字, 行, 列)。セル配置は iss・blender-poc の線路と同じ。[0] の夏の絵。雪の絵（[1]）は行を SNOW_ROWS だけ下げる
    ("image", "[ns]", 0, 2), ("image", "[ew]", 0, 3), ("image", "[s]", 0, 5), ("image", "[w]", 0, 6),
    ("image", "[n]", 0, 7), ("image", "[e]", 0, 8), ("image", "[-]", 0, 9), ("imageup", "[12]", 1, 0),
    ("imageup", "[9]", 1, 1), ("imageup", "[3]", 1, 2), ("imageup", "[6]", 1, 3), ("imageup2", "[12]", 1, 5),
    ("imageup2", "[9]", 1, 6), ("imageup2", "[3]", 1, 7), ("imageup2", "[6]", 1, 8), ("diagonal", "[sw]", 2, 0),
    ("diagonal", "[nw]", 2, 1), ("diagonal", "[ne]", 2, 2), ("diagonal", "[se]", 2, 3),
    ("diagonal", "[close1]", 2, 4), ("diagonal", "[close2]", 2, 9), ("image", "[sw]", 2, 5), ("image", "[nw]", 2, 6),
    ("image", "[ne]", 2, 7), ("image", "[se]", 2, 8), ("image", "[nse]", 3, 5), ("image", "[new]", 3, 6),
    ("image", "[nsw]", 3, 7), ("image", "[sew]", 3, 8), ("image", "[nsew]", 3, 9), ("image", "[nse1]", 2, 10),
    ("image", "[new1]", 2, 11), ("image", "[nsw1]", 2, 12), ("image", "[sew1]", 2, 13), ("image", "[nsew1]", 2, 14),
    ("image", "[nse2]", 3, 10), ("image", "[new2]", 3, 11), ("image", "[nsw2]", 3, 12), ("image", "[sew2]", 3, 13),
    ("image", "[nsew2]", 3, 14),
)

# (速度 km/h, 費用, 維持費, 登場年)。費用・維持費は pak128 の way と同じ単位（1/100 cr）。iss の線路（15000・300）を基準にした
VALUES = {
    "ami_tram": dict(waytype="tram_track", speed=60, cost=10000, maintenance=200, intro_year=1900),
    "ami_rail_ballast": dict(waytype="track", speed=160, cost=15000, maintenance=300, intro_year=1900),
    "ami_rail_slab": dict(waytype="track", speed=480, cost=40000, maintenance=800, intro_year=2000),
    "ami_road_local": dict(waytype="road", speed=40, cost=5000, maintenance=100, intro_year=1900),
    "ami_road_general": dict(waytype="road", speed=120, cost=8000, maintenance=200, intro_year=1930),
    "ami_road_expressway": dict(waytype="road", speed=360, cost=20000, maintenance=500, intro_year=1990),
}

# カーブを斜めの絵で表すシート（pak128 標準の線路と同じ。dat の image[sw]・[nw]・[ne]・[se] が diagonal と同じセルを指す。
# シートのカーブのセル（行 2 の列 5〜8）は描かない。render.py の diag_curves と同じにする）
DIAG_CURVES = {"ami_rail_ballast"}
CURVE_TO_DIAG = {"[sw]": (2, 0), "[nw]": (2, 1), "[ne]": (2, 2), "[se]": (2, 3)}

# 絵を作った way（名前 → シート名）。dat と pak を作る
BUILT = {"ami_rail_ballast": "ami_rail_ballast"}
BASE_VARIANTS = ("single", "back", "center", "front")
for _v in BASE_VARIANTS:
    BUILT[f"ami_rail_ballast_base_{_v}"] = f"ami_rail_ballast_base_{_v}"
    VALUES[f"ami_rail_ballast_base_{_v}"] = VALUES["ami_rail_ballast"]
    # 基盤の版はカーブのセル（行 2 の列 5〜8）を斜めの形で描く（render.py の curve_cells）。斜めのセルとは基盤の削り方だけが違う:
    # 斜めのセルは近い斜めの分け合うタイルのために、壁の無い側を 2 本の真ん中で削る。カーブ（斜めが続かない曲がり）は削らない
NO_CLOSE = {f"ami_rail_ballast_base_{_v}" for _v in BASE_VARIANTS}  # 近い斜めの絵を持たない way

# ---------------------------------------------------------------- 高架の 4 版（#18）
# 基盤の版と同じ並び（近い斜めの絵を持たない）で、system_type=1。値は仮: iss と同じく地上の 2 倍の費用・維持費（速さは地上と同じ）
ELEV_COST_K = 2
ELEVATED = set()
for _v in BASE_VARIANTS:
    _n = f"ami_rail_ballast_elev_{_v}"
    BUILT[_n] = _n
    VALUES[_n] = dict(VALUES["ami_rail_ballast"], cost=VALUES["ami_rail_ballast"]["cost"] * ELEV_COST_K,
                      maintenance=VALUES["ami_rail_ballast"]["maintenance"] * ELEV_COST_K)
    NO_CLOSE.add(_n)
    ELEVATED.add(_n)

# ---------------------------------------------------------------- 橋脚の way（#18）
# 高架の真下の地面のタイルに敷く。waytype は仮に narrowgauge_track（pak128 と AMI が使っていない。README の「橋脚の作り」）。
# iss の tram_track は、本体が track（system_type=7）として読むので、線路の網とつながり、線路の way-object（壁・架線）も載る。
# 値は仮（iss の橋脚と同じ費用・維持費）。topspeed は走らせる物ではないので 1
PIER_VALUES = dict(waytype="narrowgauge_track", cost=1000, maintenance=100, intro_year=1900, topspeed=1)
PIERS = {"ami_pier_rail": "ami_pier_rail"}
# 橋脚のシートにあるセル（render の pier_sheet）。分岐の絵（switch 画像）は T字・十字と同じ柱
PIER_SWITCH = {"[nse1]": "[nse]", "[nse2]": "[nse]", "[new1]": "[new]", "[new2]": "[new]", "[nsw1]": "[nsw]", "[nsw2]": "[nsw]",
               "[sew1]": "[sew]", "[sew2]": "[sew]", "[nsew1]": "[nsew]", "[nsew2]": "[nsew]"}

# ---------------------------------------------------------------- 壁の way-object（線路用、壁だけ。架線つきは下の CATENARY）
# 値は仮（README の「今の決まりごと」）。topspeed は架線でない way-object では列車の速さを縛らない（本体は電化した編成にだけ
# max_wayobj_speed を当てる。vehicle/simvehicle.cc）。同じ waytype の way-object は、遅い物を速い物で置き換える（Ctrl なし。
# obj/wayobj.cc の extend_wayobj）ので、twin だけ 1 速くして、back・front を敷き直しても twin が残るようにする
WALL_VALUES = dict(cost=3000, maintenance=60, intro_year=1900, topspeed=1000)
WALL_TWIN_TOPSPEED = WALL_VALUES["topspeed"] + 1
# center は側壁が無く、行き止まりの端の壁だけ（ほかのキーの絵は空。架線つきの版で center も要るので 4 版にそろえる）
WALLS = {f"ami_wall_rail_{_v}": f"ami_wall_rail_{_v}" for _v in BASE_VARIANTS}
WALL_FRONT_ROW = 4  # 壁のシートの手前の絵の行（sheetlib の WALL_FRONT_ROW と同じ）
WAYOBJ_KEYS = {"image": "image", "imageup": "imageup", "imageup2": "imageup2", "diagonal": "diagonal"}  # way のキー → way-object の back/front の後ろ
# 近い斜めの分け合うタイル用: 斜めの向きごとに、タイルの角の側の壁を持つ版のシート（back は nw・sw、front は ne・se。README の「壁の敷き方」）
TWIN_FROM = {"[nw]": "ami_wall_rail_back", "[sw]": "ami_wall_rail_back", "[ne]": "ami_wall_rail_front", "[se]": "ami_wall_rail_front"}

# ---------------------------------------------------------------- 架線つきの壁の way-object（線路用、電化。#17）
# 値は仮（README の「架線の作り」）。架線の way-object の topspeed は、電化した編成の速さを縛る（本体の max_wayobj_speed）ので、
# いちばん速い線路（高速線 480 km/h）より大きくする。壁だけの版（1000・twin 1001）より速くして、壁の上に敷くと架線つきに置き換わる
# （逆に、架線つきの上に壁だけの版を敷いても置き換わらない。外してから敷く）。近い斜めの分け合うタイル用の twin は 1 速くする（壁だけの版と同じ理由。
# 壁だけの twin 1001 も置き換える）。twin の絵は、斜めの梁を短くした back・front の版のシート（render.py の TWIN_FROM）
CATENARY_VALUES = dict(cost=4000, maintenance=100, intro_year=1900, topspeed=1100)
CATENARY_TWIN_TOPSPEED = CATENARY_VALUES["topspeed"] + 1
CATENARY = {f"ami_wall_rail_{_v}_catenary": f"ami_wall_rail_{_v}_catenary" for _v in BASE_VARIANTS}
TWIN_FROM_CATENARY = {k: v.replace("ami_wall_rail_", "ami_wall_rail_twin_catenary_") for k, v in TWIN_FROM.items()}


def dat_text(name, sheet):
    v = VALUES[name]
    out = [
        f"# AMI: {name}（CC BY 4.0）。{v['speed']} km/h。シートは blender/render.py が描く",
        "obj=way",
        f"name={name}",
        "copyright=AMI (CC BY 4.0)",
        f"intro_year={v['intro_year']}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        f"waytype={v['waytype']}",
        f"cost={v['cost']}",
        f"maintenance={v['maintenance']}",
        f"topspeed={v['speed']}",
        f"system_type={1 if name in ELEVATED else 0}",
        f"icon=> {sheet}.0.0",
        f"cursor={sheet}.0.1,-64,-32",
    ]
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if name in NO_CLOSE and idx.startswith("[close"):
                continue
            if key == "image" and sheet in DIAG_CURVES and idx in CURVE_TO_DIAG:
                row, col = CURVE_TO_DIAG[idx]
            out.append(f"{key}{idx}[{season}]={sheet}.{row + season * SNOW_ROWS}.{col},-64,-32")
    return NL.join(out) + NL


def wall_dat_text(name, sheet, twin=False, catenary=False):
    """壁の way-object の dat。セルは way と同じ位置（分岐の絵・近い斜めは持たない。壁は通常の T字・十字と同じ）。
    カーブは way と同じく斜めのセルを指す。twin は近い斜めの分け合うタイル用（斜めとカーブのキーだけ、TWIN_FROM のシートを指す）。
    catenary は架線つき（電化。own_waytype=electrified_track、値は CATENARY_VALUES。twin は TWIN_FROM_CATENARY のシート）"""
    v = CATENARY_VALUES if catenary else WALL_VALUES
    twin_from = TWIN_FROM_CATENARY if catenary else TWIN_FROM
    kind = "架線つき（電化）" if catenary else "壁だけ、架線なし"
    out = [
        f"# AMI: {name}（CC BY 4.0）。線路の壁の way-object（{kind}）。シートは blender/render.py が描く",
        "obj=way-object",
        f"name={name}",
        "copyright=AMI (CC BY 4.0)",
        f"intro_year={v['intro_year']}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        "waytype=track",
        f"own_waytype={'electrified_track' if catenary else 'track'}",
        f"cost={v['cost']}",
        f"maintenance={v['maintenance']}",
        f"topspeed={(CATENARY_TWIN_TOPSPEED if catenary else WALL_TWIN_TOPSPEED) if twin else v['topspeed']}",
        f"icon=> {sheet}.0.0",
        f"cursor={sheet}.0.1,-64,-32",
    ]
    for key, idx, row, col in IMAGES:
        if key not in WAYOBJ_KEYS or idx.startswith("[close") or idx[1:-1].endswith(("1", "2")) and key == "image":
            continue
        if key == "image" and idx in CURVE_TO_DIAG:
            row, col = CURVE_TO_DIAG[idx]
        src = sheet
        if twin:
            if not ((key == "diagonal" or key == "image") and idx in twin_from):
                continue
            src = twin_from[idx]
        for side, dr in (("back", 0), ("front", WALL_FRONT_ROW)):
            out.append(f"{side}{WAYOBJ_KEYS[key]}{idx}={src}.{row + dr}.{col},-64,-32")
    return NL.join(out) + NL


def pier_dat_text(name, sheet):
    """橋脚の way の dat。カーブは斜めのセル、分岐の絵は T字・十字のセル。雪の絵（[1]）は夏と同じセル（柱に雪は描かない）"""
    v = PIER_VALUES
    cell = {(key, idx): (row, col) for key, idx, row, col in IMAGES}
    out = [
        f"# AMI: {name}（CC BY 4.0）。高架の真下の地面に敷く橋脚の way。シートは blender/render.py が描く",
        "obj=way",
        f"name={name}",
        "copyright=AMI (CC BY 4.0)",
        f"intro_year={v['intro_year']}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        f"waytype={v['waytype']}",
        f"cost={v['cost']}",
        f"maintenance={v['maintenance']}",
        f"topspeed={v['topspeed']}",
        "system_type=0",
        f"icon=> {sheet}.0.0",
        f"cursor={sheet}.0.1,-64,-32",
    ]
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if key == "image" and idx in CURVE_TO_DIAG:
                row, col = CURVE_TO_DIAG[idx]
            elif key == "image" and idx in PIER_SWITCH:
                row, col = cell[("image", PIER_SWITCH[idx])]
            out.append(f"{key}{idx}[{season}]={sheet}.{row}.{col},-64,-32")
    return NL.join(out) + NL


def main():
    os.makedirs(SRC, exist_ok=True)
    for name, sheet in BUILT.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(dat_text(name, sheet))
        print(f"[dat] {name}.dat")
    for name, sheet in WALLS.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(wall_dat_text(name, sheet))
        print(f"[dat] {name}.dat")
    with open(os.path.join(SRC, "ami_wall_rail_twin.dat"), "w", encoding="utf8", newline=NL) as f:
        f.write(wall_dat_text("ami_wall_rail_twin", "ami_wall_rail_back", twin=True))
    print("[dat] ami_wall_rail_twin.dat")
    for name, sheet in CATENARY.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(wall_dat_text(name, sheet, catenary=True))
        print(f"[dat] {name}.dat")
    with open(os.path.join(SRC, "ami_wall_rail_twin_catenary.dat"), "w", encoding="utf8", newline=NL) as f:
        f.write(wall_dat_text("ami_wall_rail_twin_catenary", "ami_wall_rail_twin_catenary_back", twin=True, catenary=True))
    print("[dat] ami_wall_rail_twin_catenary.dat")
    for name, sheet in PIERS.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(pier_dat_text(name, sheet))
        print(f"[dat] {name}.dat")


if __name__ == "__main__":
    main()
