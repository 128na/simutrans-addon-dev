"""AMI の dat を書き出す（Blender は使わない。アドオンのディレクトリで `python -X utf8 blender/ami_dat.py`）。

値（速度・費用・維持費・登場年）は VALUES が持つ。README の「値の一覧」と同じにする。
まだ絵を作っていない way は BUILT に入れない（dat も pak も作らない）。シートの行の並びは
    夏の絵 4 行（奥の絵）→ 雪の絵 4 行
で、blender-poc の `track_dat.py` が書く無壁の線路と同じ。壁・高架・橋の版（手前の絵の行を持つ）は、それぞれのステップで足す。
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

# 絵を作った way（名前 → シート名）。dat と pak を作る
BUILT = {"ami_rail_ballast": "ami_rail_ballast"}


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
        "system_type=0",
        f"icon=> {sheet}.0.0",
        f"cursor={sheet}.0.1,-64,-32",
    ]
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            out.append(f"{key}{idx}[{season}]={sheet}.{row + season * SNOW_ROWS}.{col},-64,-32")
    return NL.join(out) + NL


def main():
    os.makedirs(SRC, exist_ok=True)
    for name, sheet in BUILT.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(dat_text(name, sheet))
        print(f"[dat] {name}.dat")


if __name__ == "__main__":
    main()
