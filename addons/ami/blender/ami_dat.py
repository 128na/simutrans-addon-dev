"""AMI の dat を書き出す（Blender は使わない。アドオンのディレクトリで `python -X utf8 blender/ami_dat.py`）。

値（速度・費用・維持費・登場年）は VALUES が持つ。README の「値の一覧」と同じにする。
まだ絵を作っていない way は BUILT に入れない（dat も pak も作らない）。シートの行の並びは
    夏の絵 4 行（奥の絵）→ 雪の絵 4 行
で、無壁の線路の並び。カーブは斜めの絵（DIAG_CURVES）を指す。
高架の版（ami_rail_ballast_elev_<版>）は基盤の版と同じ並びで system_type=1。橋脚の way は雪の絵も同じセルで、単柱（ami_pier_rail）は行 0〜3 だけ、
門型（ami_pier_rail_gate）は行 0〜3 が奥の絵、行 4〜7 が手前の絵（PIER_FRONT_ROW）。

基盤の版の way（ami_rail_ballast_base_<版>）は通常の版と同じ並びで、近い斜めの絵を持たない（本体が分け合うタイルに 2 本の way を置き、
奥の線と手前の線を別の版にできる。docs/reference/way-addon.md の 6 章）。壁の way-object（ami_wall_rail_<版>）のシートは
    奥の絵 4 行（backimage）→ 手前の絵 4 行（frontimage）
で、セルの位置は way と同じ。雪の絵は無い（way-object に雪のキーが無い）。ami_wall_rail_twin は近い斜めの分け合うタイル用で、
back と front のシートの斜めのセルを指す（README の「壁の敷き方」）。

架線つきの壁の way-object（ami_wall_rail_<版>_catenary）は壁と同じ並びで、own_waytype=electrified_track（電化）。
ami_wall_rail_twin_catenary は近い斜めの分け合うタイル用で、斜めの梁を短くした back と front の架線つきのシート
（ami_wall_rail_twin_catenary_<back|front>）の斜めのセルを指す（README の「架線の作り」）。

橋（BRIDGES）とトンネル（TUNNELS）は blender-poc の橋・トンネルと同じシートの並びで、手前の絵は無い（壁は way-object）。
makeobj は橋の手前のキーが無いと警告するので、手前のキーは全部、空のセル（BRIDGE_EMPTY_CELL）を指す（README の「橋とトンネルの作り」）。

way・基盤・高架・橋・トンネルの名前は、軌道の種類の表（blender/catalog.py）から展開する。
"""
import os

import catalog

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

# 分岐の追加画像（ex 画像。本体の絵の番号 26〜35。docs/reference/way-addon.md の 9.4）: makeobj の dat のキーが無いので、
# 26〜35 番に入れる絵を 1・2 の 10 枚のキー（16〜25 番）に割り当てた提供用の物（名前 + ex_graft.DONOR_SUFFIX）を EX_DONORS_DAT に書き、
# build.py が別の pak に作って、ex_graft.py で対象の物の画像リストの末尾へ写す。添字 → (行, 列)。並びは 26〜30 が「1」、31〜35 が「2」の枠:
#   [nse1]〜[sew1]: Y字分岐（26〜29。根元が東・北・西・南）。シートの行 0 の列 10〜13（sheetlib の ex_switches）
#   [nse2]〜[sew2]: 三方分岐（31〜34。十字のタイルに出る。根元が東・北・西・南）。行 1 の列 10〜13
#   [nsew1]・[nsew2]: 30・35 番。自動では使われないので、通常の十字のセル（その形の標準の絵。#57）
EX_CELLS = {"[nse1]": (0, 10), "[new1]": (0, 11), "[nsw1]": (0, 12), "[sew1]": (0, 13), "[nsew1]": (3, 9),
            "[nse2]": (1, 10), "[new2]": (1, 11), "[nsw2]": (1, 12), "[sew2]": (1, 13), "[nsew2]": (3, 9)}
EX_DONORS_DAT = "ex_donors.dat"  # src/ の中。build.py の pak（ami_*.dat）には入らない
DONOR_SUFFIX = "__ex_donor"  # ex_graft.py の DONOR_SUFFIX と同じにする
# 分岐の絵（switch 画像）の添字。dat の image[<添字>] の 1・2 の 10 枚
SWITCH_IDX = {f"[{_s}{_n}]" for _s in ("nse", "new", "nsw", "sew", "nsew") for _n in (1, 2)}
# 道路の way（waytype=road）の dat に分岐の絵を書くか。偽なら書かない（既定）。本体（OTRP）の道路の 1・2 は、自動では
# 多車線の交差点向けに選ばれ（「2」は十字のタイルだけ）、固定の道具の名前（線路の分岐の意味）と合わない。本体の仕様を整理するまで外す
# （2026-11-20、ユーザーの決定。README の「分岐の絵（switch 画像 1・2）」）。シートの分岐のセルは描いたまま残す。真にすれば戻る。
# 戻すのは https://github.com/128na/simutrans-addon-dev/issues/46（本体の仕様の整理は https://github.com/128na/simutrans/issues/15）。
# 真にしたら ingame/road_sample.nut の SWITCH_IMAGES も真にする
ROAD_SWITCH_IMAGES = False

# (速度 km/h, 費用, 維持費, 登場年)。費用・維持費は pak128 の way と同じ単位（1/100 cr）。iss の線路（15000・300）を基準にした
VALUES = {
    "ami_tram": dict(waytype="tram_track", speed=60, cost=10000, maintenance=200, intro_year=1900),
    "ami_rail_ballast": dict(waytype="track", speed=160, cost=15000, maintenance=300, intro_year=1900),
    "ami_rail_concrete": dict(waytype="track", speed=240, cost=30000, maintenance=600, intro_year=1960),
    "ami_rail_ladder": dict(waytype="track", speed=360, cost=35000, maintenance=700, intro_year=1990),
    "ami_rail_slab": dict(waytype="track", speed=480, cost=40000, maintenance=800, intro_year=2000),
    "ami_road_local": dict(waytype="road", speed=40, cost=5000, maintenance=100, intro_year=1900),
    "ami_road_general": dict(waytype="road", speed=120, cost=8000, maintenance=200, intro_year=1930),
    "ami_road_expressway": dict(waytype="road", speed=360, cost=20000, maintenance=500, intro_year=1990),
    # 跨座式モノレール（#113）。値は #110 の一覧（在来線の高架と同じ費用・維持費。速さは pak128 のモノレールの車両の最高 150）
    "ami_monorail_straddle": dict(waytype="monorail_track", speed=150, cost=30000, maintenance=600, intro_year=1900),
    # 運河（#114）。値は #110 の一覧（速さは pak128 の船の最高 53 km/h が走れる値）
    "ami_canal": dict(waytype="water", speed=60, cost=25000, maintenance=500, intro_year=1900),
}

# カーブを斜めの絵で表すシート（pak128 標準の線路と同じ。dat の image[sw]・[nw]・[ne]・[se] が diagonal と同じセルを指す。
# シートのカーブのセル（行 2 の列 5〜8）は描かない。render.py の diag_curves と同じにする）
DIAG_CURVES = {_t.way for _t in catalog.TRACKS} | {_r.way for _r in catalog.ROADS}  # 道路 3 種もカーブは斜めの絵（README の「道路の作り」）
# 跨座式モノレール（#113）: 地上・高架の版とも、カーブは斜めの絵（手本の iss の跨座式の dat と同じ）
DIAG_CURVES |= {catalog.MONORAIL, *catalog.MONORAIL_ELEVS}
DIAG_CURVES.add(catalog.CANAL)  # 運河（#114）もカーブは斜めの絵
DIAG_CURVES |= {_r.lane(_n) for _r in catalog.LANE_ROADS for _n in catalog.LANES}  # 路面表示の版（#121）も通常の版と同じ
CURVE_TO_DIAG = {"[sw]": (2, 0), "[nw]": (2, 1), "[ne]": (2, 2), "[se]": (2, 3)}

# 絵を作った way（名前 → シート名）。dat と pak を作る
BUILT = {}
BASE_VARIANTS = catalog.VARIANTS
NO_CLOSE = set()  # 近い斜めの絵を持たない way
for _t in catalog.TRACKS:
    BUILT[_t.way] = _t.way
    for _v in BASE_VARIANTS:
        # 基盤の版はカーブのセル（行 2 の列 5〜8）を斜めの形で描く（render.py の curve_cells）。斜めのセルとは基盤の削り方だけが違う:
        # 斜めのセルは近い斜めの分け合うタイルのために、壁の無い側を 2 本の真ん中で削る。カーブ（斜めが続かない曲がり）は削らない
        _n = _t.base(_v)
        BUILT[_n] = _n
        VALUES[_n] = VALUES[_t.way]
        NO_CLOSE.add(_n)
# 路面軌道（#23）。通常の版だけで、並びは線路の通常の版と同じ（近い斜め・分岐の絵を持つ）。カーブはカーブのセル（曲線。DIAG_CURVES に入れない）
BUILT[catalog.TRAM] = catalog.TRAM
# 路面軌道の dat に分岐の絵（switch 画像 1・2）を書くか。tram_track は本体で線路と同じ選び方（weg_t::calc_image の track_wt →
# select_switch_image。docs/reference/way-addon.md の 9.2）で、道路の 1・2 のような多車線の交差点の意味は無いので、線路と同じく入れる。
# 道路（ROAD_SWITCH_IMAGES）とはそろえず入れる（2026-11-20、ユーザーの決定。#23）。偽にすると dat から 10 枚を外す（シートのセルは残る）
TRAM_SWITCH_IMAGES = True
# 道路 3 種の通常の版（#21）。並びは線路の通常の版と同じ（近い斜め・分岐の絵を持つ）。waytype と値は VALUES
for _r in catalog.ROADS:
    BUILT[_r.way] = _r.way
# 道路の路面表示の版（#121）: 並び・値は通常の版と同じ（近い斜め・分岐の絵を持つ）。白線だけが違う
for _r in catalog.LANE_ROADS:
    for _n in catalog.LANES:
        BUILT[_r.lane(_n)] = _r.lane(_n)
        VALUES[_r.lane(_n)] = VALUES[_r.way]
# 道路の地上の基盤の版（#22。2026-11-19 にユーザーが確定）: 線路の基盤の版と同じく近い斜めの絵を持たず、カーブはカーブのセル（斜めの形）。
# 値は通常の版と同じ（README の「道路の壁・高架・橋脚・橋・トンネルの作り」）
for _r in catalog.ROADS:
    for _v in BASE_VARIANTS:
        _n = _r.base(_v)
        BUILT[_n] = _n
        VALUES[_n] = VALUES[_r.way]
        NO_CLOSE.add(_n)

# ---------------------------------------------------------------- 高架の 4 版（#18）
# 基盤の版と同じ並び（近い斜めの絵を持たない）で、system_type=1。値は仮: iss と同じく地上の 2 倍の費用・維持費（速さは地上と同じ）
ELEV_COST_K = 2
ELEVATED = set()
for _t in catalog.TRACKS:
    for _v in BASE_VARIANTS:
        _n = _t.elev(_v)
        BUILT[_n] = _n
        VALUES[_n] = dict(VALUES[_t.way], cost=VALUES[_t.way]["cost"] * ELEV_COST_K,
                          maintenance=VALUES[_t.way]["maintenance"] * ELEV_COST_K)
        NO_CLOSE.add(_n)
        ELEVATED.add(_n)
# 道路の高架の 4 版（#22）: 線路の高架と同じく、近い斜めの絵を持たない（分け合うタイルに way が 2 本置かれ、奥の線と手前の線を別の版にできる）。
# カーブはカーブのセル（斜めの形で、壁の無い側をタイルの端まで。render.py の curve_cells）。値の倍率も線路と同じ
for _r in catalog.ROADS:
    for _v in BASE_VARIANTS:
        _n = _r.elev(_v)
        BUILT[_n] = _n
        VALUES[_n] = dict(VALUES[_r.way], cost=VALUES[_r.way]["cost"] * ELEV_COST_K,
                          maintenance=VALUES[_r.way]["maintenance"] * ELEV_COST_K)
        NO_CLOSE.add(_n)
        ELEVATED.add(_n)

# ---------------------------------------------------------------- 跨座式モノレール（#113）
# 物の並びは iss の跨座式に合わせる（2026-11-21、ユーザーの決定）: 地上・高架の 3 版（front・center・back。system_type=1）・トンネル。
# 近い斜めの絵は持たない（iss の dat にキーが無い）。分岐の絵（1・2）は iss と同じく書く（本体は今のところ monorail_track では選ばない。
# boden/wege/weg.cc の calc_image は track_wt と road_wt だけ select_switch_image を呼ぶ）。高架の値の倍率は線路と同じ ELEV_COST_K
BUILT[catalog.MONORAIL] = catalog.MONORAIL
NO_CLOSE.add(catalog.MONORAIL)
for _n in catalog.MONORAIL_ELEVS:
    BUILT[_n] = _n
    VALUES[_n] = dict(VALUES[catalog.MONORAIL], cost=VALUES[catalog.MONORAIL]["cost"] * ELEV_COST_K,
                      maintenance=VALUES[catalog.MONORAIL]["maintenance"] * ELEV_COST_K)
    NO_CLOSE.add(_n)
    ELEVATED.add(_n)

# ---------------------------------------------------------------- 運河（#114）
# 地上の版だけ（iss の運河と同じ。2026-11-22、ユーザーの決定）。近い斜めの絵は持つ（壁の無い way と同じ）。分岐の絵（1・2）は持たない
# （本体は water の way の分岐の絵を選ばない。boden/wege/weg.cc の calc_image は track_wt と road_wt だけ）
BUILT[catalog.CANAL] = catalog.CANAL
NO_SWITCH = {catalog.CANAL}  # 分岐の絵（image[nse1] など）を書かない way

# ---------------------------------------------------------------- 橋脚の way（#18）
# 高架の真下の地面のタイルに敷く。waytype は tram_track（iss と同じ。ユーザーの決定、2026-11-18。README の「高架と橋脚の作り」）。
# 本体は track（system_type=7）として読むので、線路の網とつながり、線路の way-object（壁・架線）も載り、道路に重ねられる。
# 値は仮（iss の橋脚と同じ費用・維持費）。topspeed は走らせる物ではないので 1
PIER_VALUES = dict(waytype="tram_track", cost=1000, maintenance=100, intro_year=1900, topspeed=1)
PIERS = {"ami_pier_rail": "ami_pier_rail", "ami_pier_rail_gate": "ami_pier_rail_gate"}  # 単柱と門型（門型は #18 の追加）
# 道路用の橋脚（#22）: 線路用と同じ waytype（tram_track。2026-11-19 にユーザーが確定）と値（仮）。シートの並びは単柱の橋脚と同じ（README の「道路の壁・高架・橋脚・橋・トンネルの作り」）
PIERS[catalog.PIER_ROAD] = catalog.PIER_ROAD
# 手前の絵（frontimage）を持つ橋脚: 名前 → 手前の絵の行のずらし。シートを描く側の tools/blender/sheetlib/sheetlib.py の
# PIER_GATE_FRONT_ROW と同じ値にする。門型は柱・梁を手前の絵に描く
PIER_FRONT_ROW = {"ami_pier_rail_gate": 4}
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
# 壁だけの twin のアイコン・カーソルのセル（back の版のシートの、どの dat も指さないセル。icons.py が書く。#25）
TWIN_ICON_CELLS = ("0.4", "1.4")
TWIN_FROM = {"[nw]": "ami_wall_rail_back", "[sw]": "ami_wall_rail_back", "[ne]": "ami_wall_rail_front", "[se]": "ami_wall_rail_front"}

# ---------------------------------------------------------------- 道路の壁の way-object（#22）
# waytype=road・own_waytype=road。値は線路の壁と同じ（仮）。版は single・back・center・front（center は線路の center と同じく、側壁が無く
# 行き止まりの端の壁だけ）。シートの並びは線路の壁と同じ。
# 近い斜めの分け合うタイル用の ami_wall_road_twin（名前は 2026-11-19 にユーザーが確定）は、線路の twin と同じ作りで、back・front の斜めのセルを指す
ROAD_WALLS = {f"ami_wall_road_{_v}": f"ami_wall_road_{_v}" for _v in catalog.ROAD_WALL_VARIANTS}
ROAD_TWIN_FROM = {k: v.replace("ami_wall_rail_", "ami_wall_road_") for k, v in TWIN_FROM.items()}
# 中央分離帯つきの壁（#118）: 値は #110 で決めた一覧（README の「第 2 弾の物の値」）。速さは壁（1000）・twin（1001）より大きく、壁の上に
# 重ねると分離帯つきに置き換わる。近い斜めの分け合うタイル用の twin_divider は 1 速くする（壁の twin と同じ理由）。
# twin_divider の絵は、西の線（nw・sw）が back の壁、東の線（ne・se）が front_divider（4 車線の手前の線が東になる）
DIVIDER_VALUES = dict(cost=3000, maintenance=60, intro_year=1900, topspeed=1010)
DIVIDER_TWIN_TOPSPEED = DIVIDER_VALUES["topspeed"] + 1
ROAD_DIVIDERS = {_n: _n for _n in catalog.ROAD_DIVIDERS.values()}
ROAD_DIVIDER_TWIN_FROM = {k: (v if v.endswith("_back") else catalog.ROAD_DIVIDERS["front"]) for k, v in ROAD_TWIN_FROM.items()}

# ---------------------------------------------------------------- 架線つきの壁の way-object（線路用、電化。#17）
# 値は仮（README の「架線の作り」）。架線の way-object の topspeed は、電化した編成の速さを縛る（本体の max_wayobj_speed）ので、
# いちばん速い線路（高速線 480 km/h）より大きくする。壁だけの版（1000・twin 1001）より速くして、壁の上に敷くと架線つきに置き換わる
# （逆に、架線つきの上に壁だけの版を敷いても置き換わらない。外してから敷く）。近い斜めの分け合うタイル用の twin は 1 速くする（壁だけの版と同じ理由。
# 壁だけの twin 1001 も置き換える）。twin の絵は、斜めの梁を短くした back・front の版のシート（render.py の TWIN_FROM）
CATENARY_VALUES = dict(cost=4000, maintenance=100, intro_year=1900, topspeed=1100)
CATENARY_TWIN_TOPSPEED = CATENARY_VALUES["topspeed"] + 1
CATENARY = {f"ami_wall_rail_{_v}_catenary": f"ami_wall_rail_{_v}_catenary" for _v in BASE_VARIANTS}
TWIN_FROM_CATENARY = {k: v.replace("ami_wall_rail_", "ami_wall_rail_twin_catenary_") for k, v in TWIN_FROM.items()}

# ---------------------------------------------------------------- 分岐の追加画像を継ぎ足す物（#57）
# 線路（線路・基盤・高架の版）と路面軌道の way: 本体が Y字分岐・三方分岐で ex 画像を自動で選ぶのは track_wt（tram を含む）だけ（9.4）。道路は入れない
EX_WAYS = [_n for _n in BUILT if VALUES[_n]["waytype"] in ("track", "tram_track")]
# 架線つきの壁の way-object（twin を除く）: トロリ線を Y字・三方分岐の走行面に合わせた絵を持つ（壁だけの版は絵が T字・十字と同じなので持たない）。
# 本体（obj/wayobj.cc）は、way-object の 26 番の絵があると、隣のタイルの way-object の向きから way と同じ条件で ex 画像を選ぶ。
# 分岐の絵（16 番）が無いとその処理に入らないので、1・2 の 10 枚は T字・十字と同じセルを指す
EX_WAYOBJS = list(CATENARY)


# ---------------------------------------------------------------- 橋とトンネル（#19）
# 橋は欄干を描かず、壁・架線は地上と同じ way-object を重ねる（ADR 0003）。値は仮: 費用・維持費は地上の BRIDGE_COST_K・TUNNEL_COST_K 倍、
# 速さは地上と同じ（README の「橋とトンネルの作り」）。橋の pillar_distance は iss の橋と同じ 1（全部のタイルに橋脚）。
# 橋のシートの並び（render.py の rail_ballast_bridge。blender-poc の橋と同じセル）: 行 0 の列 2・3 が平らな橋（NS・EW）、
# 行 1 が端の坂（列 0〜3 が 1 段、5〜8 が 2 段。並びは way の imageup と同じ 12・9・3・6）、行 2 の列 0・1 が橋脚（南北の橋・東西の橋）、
# 行 3 が坂から始まる端（列 0〜3 が 1 段、5〜8 が 2 段。並びは n・s・e・w）。雪の絵は BRIDGE_SNOW_ROWS 下（橋脚は夏と同じセル）。
# Ramp[N] は北が高い坂の絵、Start[N] は南が高い坂のタイルで使われる（docs/reference/way-addon.md の 5 章）
BRIDGE_COST_K = 4
TUNNEL_COST_K = 4
BRIDGE_SNOW_ROWS = 4
BRIDGE_RAMPS = (("n", 0), ("w", 1), ("s", 2), ("e", 3))  # Ramp の向き → 列（2 段は +5）
BRIDGE_STARTS = (("n", 0), ("s", 1), ("e", 2), ("w", 3))  # Start の向き → 列（2 段は +5）
# makeobj が読む橋の手前の絵のキー（bridge_writer.cc の並び）と、それが指す空のセル（行 0 の列 9。シートの描かない所）
BRIDGE_FRONT_KEYS = (("image", "ns ew".split()), ("start", "nsew"), ("ramp", "nsew"), ("pillar", "sw"),
                     ("image2", "ns ew".split()), ("start2", "nsew"), ("ramp2", "nsew"), ("pillar2", "sw"))
BRIDGE_EMPTY_CELL = "0.9"
BRIDGES = {_t.bridge: (_t.way, _t.bridge) for _t in catalog.TRACKS}  # 名前 → (地上の way, シート)
BRIDGES.update({_r.bridge: (_r.way, _r.bridge) for _r in catalog.ROADS})  # 道路の橋（#22）。シートの並びは線路の橋と同じ
# トンネルのシートの並び（sheetlib の tunnel_sheet）: 行 0 が奥の絵、行 1 が手前の絵（坑口の躯体）、行 2・3 が雪。列 2〜5 が n・s・e・w。
# image[N] は北が高い坂のタイル。トンネルの中の way は地上の通常の版（way=）
TUNNEL_DIRS = (("n", 2), ("s", 3), ("e", 4), ("w", 5))
TUNNELS = {_t.tunnel: (_t.way, _t.tunnel) for _t in catalog.TRACKS}  # 名前 → (中の way, シート)
TUNNELS.update({_r.tunnel: (_r.way, _r.tunnel) for _r in catalog.ROADS})  # 道路のトンネル（#22）。シートの並びは線路のトンネルと同じ
TUNNELS[catalog.MONORAIL_TUNNEL] = (catalog.MONORAIL, catalog.MONORAIL_TUNNEL)  # 跨座式モノレールのトンネル（#113）。中の way は地上の版


def _head(name, kind, obj, base, cost_k, sheet):
    v = VALUES[base]
    return [
        f"# AMI: {name}（CC BY 4.0）。{v['speed']} km/h の{kind}。シートは blender/render.py が描く",
        f"obj={obj}",
        f"name={name}",
        "copyright=AMI (CC BY 4.0)",
        f"intro_year={v['intro_year']}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        f"waytype={v['waytype']}",
        f"cost={v['cost'] * cost_k}",
        f"maintenance={v['maintenance'] * cost_k}",
        f"topspeed={v['speed']}",
    ]


def bridge_dat_text(name, base, sheet):
    out = _head(name, "橋（欄干なし。壁は way-object を重ねる）", "bridge", base, BRIDGE_COST_K, sheet)
    out += ["pillar_distance=1", f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,-64,-32"]
    for season in (0, 1):
        dr = season * BRIDGE_SNOW_ROWS
        out += [f"backimage[ns][{season}]={sheet}.{dr}.2,-64,-32", f"backimage[ew][{season}]={sheet}.{dr}.3,-64,-32"]
        for pre, dc in (("", 0), ("2", 5)):
            out += [f"backramp{pre}[{d}][{season}]={sheet}.{1 + dr}.{c + dc},-64,-32" for d, c in BRIDGE_RAMPS]
            out += [f"backstart{pre}[{d}][{season}]={sheet}.{3 + dr}.{c + dc},-64,-32" for d, c in BRIDGE_STARTS]
        out += [f"backpillar[s][{season}]={sheet}.2.0,-64,-32", f"backpillar[w][{season}]={sheet}.2.1,-64,-32"]
        # 手前の絵は無いが、makeobj は front のキーが無いと全部の向きで警告を出す（descriptor/writer/bridge_writer.cc）。空のセルを指す
        for key, dirs in BRIDGE_FRONT_KEYS:
            out += [f"front{key}[{d}][{season}]={sheet}.{BRIDGE_EMPTY_CELL},-64,-32" for d in dirs]
    return NL.join(out) + NL


def tunnel_dat_text(name, base, sheet):
    out = _head(name, "トンネル", "tunnel", base, TUNNEL_COST_K, sheet)
    out += [f"way={base}", f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,-64,-32"]
    for season in (0, 1):
        for d, c in TUNNEL_DIRS:
            out += [f"backimage[{d}][{season}]={sheet}.{2 * season}.{c},-64,-32",
                    f"frontimage[{d}][{season}]={sheet}.{2 * season + 1}.{c},-64,-32"]
    return NL.join(out) + NL


def dat_text(name, sheet, donor=False):
    """way の dat。donor なら分岐の追加画像の提供用の物（名前 + DONOR_SUFFIX。1・2 の 10 枚のキーが EX_CELLS を指す）"""
    v = VALUES[name]
    out = [
        f"# AMI: {name}（CC BY 4.0）。{v['speed']} km/h。シートは blender/render.py が描く"
        + ("。分岐の追加画像の提供用（build.py が ex_graft.py で写す。ゲームには入れない）" if donor else ""),
        "obj=way",
        f"name={name}{DONOR_SUFFIX if donor else ''}",
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
            if key == "image" and idx in SWITCH_IDX and v["waytype"] == "road" and not ROAD_SWITCH_IMAGES:
                continue
            if key == "image" and idx in SWITCH_IDX and name == catalog.TRAM and not TRAM_SWITCH_IMAGES:
                continue
            if key == "image" and idx in SWITCH_IDX and name in NO_SWITCH:
                continue
            if key == "image" and sheet in DIAG_CURVES and idx in CURVE_TO_DIAG:
                row, col = CURVE_TO_DIAG[idx]
            if donor and key == "image" and idx in EX_CELLS:
                row, col = EX_CELLS[idx]
            out.append(f"{key}{idx}[{season}]={sheet}.{row + season * SNOW_ROWS}.{col},-64,-32")
    return NL.join(out) + NL


def wall_dat_text(name, sheet, twin=False, catenary=False, road=False, donor=False, divider=False):
    """壁の way-object の dat。セルは way と同じ位置（分岐の絵・近い斜めは持たない。壁は通常の T字・十字と同じ）。
    カーブは way と同じく斜めのセルを指す。twin は近い斜めの分け合うタイル用（斜めとカーブのキーだけ、TWIN_FROM のシートを指す）。
    catenary は架線つき（電化。own_waytype=electrified_track、値は CATENARY_VALUES。twin は TWIN_FROM_CATENARY のシート）。
    road は道路の壁（waytype=road・own_waytype=road。twin は ROAD_TWIN_FROM のシート）。divider は道路の中央分離帯つきの壁（road と一緒に
    渡す。値は DIVIDER_VALUES、twin は ROAD_DIVIDER_TWIN_FROM のシート）。
    架線つき（twin を除く）は、分岐の追加画像（EX_WAYOBJS）のために 1・2 の 10 枚のキーも書く: 通常は T字・十字と同じセル（本体が way-object の
    分岐の絵を選ぶ処理に入るが、絵は変わらない）、donor（提供用の物。名前 + DONOR_SUFFIX）は EX_CELLS"""
    v = CATENARY_VALUES if catenary else DIVIDER_VALUES if divider else WALL_VALUES
    # 壁だけの twin は back の版のシートを借りるので、アイコン・カーソルは back の版のセル（0.0・0.1）でなく、使っていないセルに置く（#25）
    icon_cell, cursor_cell = TWIN_ICON_CELLS if twin and not catenary else ("0.0", "0.1")
    twin_from = (TWIN_FROM_CATENARY if catenary else ROAD_DIVIDER_TWIN_FROM if divider else ROAD_TWIN_FROM if road
                 else TWIN_FROM)
    kind = "道路の中央分離帯つきの壁" if divider else "道路の壁" if road else "線路の壁の way-object（架線つき（電化））" if catenary else "線路の壁の way-object（壁だけ、架線なし）"
    wt = "road" if road else "track"
    out = [
        f"# AMI: {name}（CC BY 4.0）。{kind}。シートは blender/render.py が描く"
        + ("。分岐の追加画像の提供用（build.py が ex_graft.py で写す。ゲームには入れない）" if donor else ""),
        "obj=way-object",
        f"name={name}{DONOR_SUFFIX if donor else ''}",
        "copyright=AMI (CC BY 4.0)",
        f"intro_year={v['intro_year']}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        f"waytype={wt}",
        f"own_waytype={'electrified_track' if catenary else wt}",
        f"cost={v['cost']}",
        f"maintenance={v['maintenance']}",
        f"topspeed={(CATENARY_TWIN_TOPSPEED if catenary else DIVIDER_TWIN_TOPSPEED if divider else WALL_TWIN_TOPSPEED) if twin else v['topspeed']}",
        f"icon=> {sheet}.{icon_cell}",
        f"cursor={sheet}.{cursor_cell},-64,-32",
    ]
    ex = name in EX_WAYOBJS or donor
    cell = {(key, idx): (row, col) for key, idx, row, col in IMAGES}
    for key, idx, row, col in IMAGES:
        if key not in WAYOBJ_KEYS or idx.startswith("[close"):
            continue
        if key == "image" and idx in SWITCH_IDX:
            if not ex:
                continue
            row, col = EX_CELLS[idx] if donor else cell[("image", PIER_SWITCH[idx])]
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
    """橋脚の way の dat。カーブは斜めのセル、分岐の絵は T字・十字のセル。雪の絵（[1]）は夏と同じセル（柱に雪は描かない）。
    PIER_FRONT_ROW にある橋脚は、同じキーの手前の絵（front<キー>）を、行を下げたセルで足す"""
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
    front_rows = (0, PIER_FRONT_ROW[name]) if name in PIER_FRONT_ROW else (0,)
    for dr in front_rows:
        for season in (0, 1):
            for key, idx, row, col in IMAGES:
                if key == "image" and idx in CURVE_TO_DIAG:
                    row, col = CURVE_TO_DIAG[idx]
                elif key == "image" and idx in PIER_SWITCH:
                    row, col = cell[("image", PIER_SWITCH[idx])]
                out.append(f"{'front' if dr else ''}{key}{idx}[{season}]={sheet}.{row + dr}.{col},-64,-32")
    return NL.join(out) + NL

# 盛土の way（#123。ADR 0008 の景観 6）: 高架の脇の地面に敷く法面の楔。waytype は橋脚と同じ tram_track、速さ 1（ADR 0008）。値は #110 の一覧
EMBANKMENT_VALUES = dict(waytype="tram_track", cost=1000, maintenance=100, intro_year=1900, topspeed=1)
# 雪の絵（[1]）の行のずらし。シートを描く側の tools/blender/sheetlib/sheetlib.py の _EMB_SNOW_ROW と同じ値にする
EMBANKMENT_SNOW_ROWS = 4
# 曲がり（image[sw] など）は行 2 の列 0〜3 の曲がりのセル。斜めの絵（diagonal）は持たない（本体は曲がりの絵を使い、斜めに敷くと角が並ぶ）
EMBANKMENT_CURVES = {"[sw]": (2, 0), "[nw]": (2, 1), "[ne]": (2, 2), "[se]": (2, 3)}


def embankment_dat_text(name, sheet):
    """盛土の way の dat。セルは橋脚のシートと同じ並び（曲がりは EMBANKMENT_CURVES、分岐の絵は T字・十字のセル）。
    雪の絵（[1]）は EMBANKMENT_SNOW_ROWS 下の行"""
    v = EMBANKMENT_VALUES
    cell = {(key, idx): (row, col) for key, idx, row, col in IMAGES}
    out = [
        f"# AMI: {name}（CC BY 4.0）。高架の脇の地面に敷く盛土（法面）の way。シートは blender/render.py が描く",
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
            if key == "diagonal":
                continue
            if key == "image" and idx in EMBANKMENT_CURVES:
                row, col = EMBANKMENT_CURVES[idx]
            elif key == "image" and idx in PIER_SWITCH:
                row, col = cell[("image", PIER_SWITCH[idx])]
            out.append(f"{key}{idx}[{season}]={sheet}.{row + season * EMBANKMENT_SNOW_ROWS}.{col},-64,-32")
    return NL.join(out) + NL

# 歩道の way（ami_sidewalk。#24）。waytype は iss の歩道（../refs/iss/src/util/sidewalk/ground.dat）と同じ water（README の「歩道の作り」）。
# 値は仮（費用・維持費は橋脚と同じ考え方の小さい値。速さ 1 は橋脚と同じ）
SIDEWALK_VALUES = dict(waytype="water", cost=1000, maintenance=20, intro_year=1900, topspeed=1)
# 高架の歩道（ami_sidewalk_elev。#119）: 値は #110 の一覧（README の「歩道の作り」）。高架は地上の 2 倍
SIDEWALK_ELEV_VALUES = dict(SIDEWALK_VALUES, cost=2000, maintenance=40)
# 歩道の柵（ami_wall_sidewalk_<版>。#119）: water の way-object。値は #110 の一覧（壁と同じ。速さ 1000 は道路の壁と同じで、
# 電柱（#120、同じ速さ）と重ねると先に置いた方が残る）
SIDEWALK_WALL_VALUES = dict(cost=3000, maintenance=60, intro_year=1900, topspeed=1000)
# 歩道の柵のセル（sheetlib の sidewalk_fence_sheet）: 歩道の way と同じ位置。カーブはシートのカーブのセル（行 2 の列 5〜8）で、斜めのキーは持たない
SIDEWALK_WALL_KEYS = ("image", "imageup", "imageup2")
# 歩道のシートにあるセル（sheetlib の sidewalk_sheet）。斜めの絵・分岐の絵は持たない（本体はカーブの絵を使う）
SIDEWALK_KEYS = ("image", "imageup", "imageup2")


def sidewalk_dat_text(name, sheet):
    """歩道の way の dat。カーブはシートのカーブのセル（行 2 の列 5〜8）。雪の絵（[1]）は SNOW_ROWS 下の行。
    高架の歩道（catalog.SIDEWALK_ELEV）は system_type=1 と高架の値"""
    elevated = name == catalog.SIDEWALK_ELEV
    v = SIDEWALK_ELEV_VALUES if elevated else SIDEWALK_VALUES
    out = [
        f"# AMI: {name}（CC BY 4.0）。{'高架の歩道の way（道路の高架の隣に敷く）' if elevated else '道路の隣のタイルに敷く歩道の way'}。"
        "シートは blender/render.py が描く",
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
        f"system_type={1 if elevated else 0}",
        f"icon=> {sheet}.0.0",
        f"cursor={sheet}.0.1,-64,-32",
    ]
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if key in SIDEWALK_KEYS and idx not in SWITCH_IDX:
                out.append(f"{key}{idx}[{season}]={sheet}.{row + season * SNOW_ROWS}.{col},-64,-32")
    return NL.join(out) + NL


def sidewalk_wall_dat_text(name, sheet):
    """歩道の柵の way-object の dat（waytype=water・own_waytype=water）。奥の絵は行 0〜3、手前の絵は WALL_FRONT_ROW 下の行。
    カーブは歩道の way と同じくカーブのセル（斜めのキーは持たない。本体は斜めの絵の無い way-object にカーブの絵を使う）"""
    v = SIDEWALK_WALL_VALUES
    out = [
        f"# AMI: {name}（CC BY 4.0）。歩道の柵（歩道の way に重ねる way-object）。シートは blender/render.py が描く",
        "obj=way-object",
        f"name={name}",
        "copyright=AMI (CC BY 4.0)",
        f"intro_year={v['intro_year']}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        "waytype=water",
        "own_waytype=water",
        f"cost={v['cost']}",
        f"maintenance={v['maintenance']}",
        f"topspeed={v['topspeed']}",
        f"icon=> {sheet}.0.0",
        f"cursor={sheet}.0.1,-64,-32",
    ]
    for key, idx, row, col in IMAGES:
        if key not in SIDEWALK_WALL_KEYS or idx in SWITCH_IDX or idx.startswith("[close"):
            continue
        for side, dr in (("back", 0), ("front", WALL_FRONT_ROW)):
            out.append(f"{side}{WAYOBJ_KEYS[key]}{idx}={sheet}.{row + dr}.{col},-64,-32")
    return NL.join(out) + NL


# ---------------------------------------------------------------- 踏切（線路 × 道路。#111）
# 線路 4 種 × 道路 3 種の 12 個（catalog.CROSSINGS）。本体は踏切を waytype の組と速さだけで選ぶ（dataobj/crossing_logic.cc の get_crossing。
# way の名前は見ない）ので、組ごとに速さの合う踏切を置く。絵は道路の種類ごとのシート（catalog.crossing_sheet）で、線路の 4 種で同じ。
# 値は仮（#110 で決める）: 速さは両方の way の最高速度（踏切で速度を落とさない）、登場年は 2 つの way の遅い方、音なし（iss と同じ sound=-1）。
# シートの並び（sheetlib の crossing.py）: 列 = (道路の向き, 閉じた絵か)、行 0・1 が夏の奥・手前、行 2・3 が雪の奥・手前。
# dat の [ns]・[ew] は waytype[0]（道路）の向き
CROSSING_COLS = {("ns", False): 0, ("ns", True): 1, ("ew", False): 2, ("ew", True): 3}  # crossing.py の CROSSING_COLS と同じ
CROSSING_SNOW_ROW = 2  # crossing.py の CROSSING_SNOW_ROW と同じ


def crossing_dat_text(name, track, road):
    t, r = VALUES[track.way], VALUES[road.way]
    sheet = catalog.crossing_sheet(road)
    out = [
        f"# AMI: {name}（CC BY 4.0）。{track.way} × {road.way} の踏切。値は仮（#110）。シートは blender/render.py が描く",
        "obj=crossing",
        f"name={name}",
        "copyright=AMI (CC BY 4.0)",
        f"intro_year={max(t['intro_year'], r['intro_year'])}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        "sound=-1",
        "waytype[0]=road",
        f"speed[0]={r['speed']}",
        "waytype[1]=track",
        f"speed[1]={t['speed']}",
    ]
    for season in (0, 1):
        row = season * CROSSING_SNOW_ROW
        for d in ("ns", "ew"):
            for closed, key in ((False, "openimage"), (True, "closedimage")):
                col = CROSSING_COLS[(d, closed)]
                out.append(f"{key}[{d}][{season}]={sheet}.{row}.{col},-64,-32")
                out.append(f"front_{key}[{d}][{season}]={sheet}.{row + 1}.{col},-64,-32")
    return NL.join(out) + NL


# 車庫（building の depot。#112）。シートの並びは sheetlib の depot.py（列 = layout 0〜3、行 0・1 が夏の奥・手前、行 2・3 が雪の奥・手前、
# 列 4 の行 0・1 がアイコン・カーソル）。layout は道の出る向き（0 = 南・1 = 東・2 = 北・3 = 西。simtool.cc の tool_depot_aux）。
# 費用・維持費は省かず pak128 の既定値を書く（README の「車庫の作り」。省いたり 0 にしたりしない）。dat の値は 1/100 cr
DEPOT_VALUES = {"track": dict(cost=850000, maintenance=1800), "tram_track": dict(cost=850000, maintenance=1800),
                "road": dict(cost=700000, maintenance=1800), "monorail_track": dict(cost=850000, maintenance=1800),
                "water": dict(cost=900000, maintenance=1800)}  # 船の車庫（#114）
DEPOT_INTRO_YEAR = 1900
DEPOT_LAYOUTS = 4
DEPOT_SNOW_ROW = 2  # sheetlib の depot.DEPOT_SNOW_ROW と同じ
DEPOT_ICON_CELL = "0.4"  # sheetlib の depot.DEPOT_ICON_CELL と同じ
DEPOT_CURSOR_CELL = "1.4"  # sheetlib の depot.DEPOT_CURSOR_CELL と同じ
DEPOT_OFFSET = "-64,-96"  # sheetlib の depot.BUILDING_OFFSET と同じ


def depot_dat_text(depot):
    v = DEPOT_VALUES[depot.waytype]
    sheet = depot.name
    out = [
        f"# AMI: {depot.name}（CC BY 4.0）。車庫。シートは blender/render.py が描く（sheetlib の depot.py）",
        "obj=building",
        f"name={depot.name}",
        "copyright=AMI (CC BY 4.0)",
        "type=depot",
        f"waytype={depot.waytype}",
        f"intro_year={DEPOT_INTRO_YEAR}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        f"cost={v['cost']}",
        f"maintenance={v['maintenance']}",
        "noinfo=1",
        f"dims=1,1,{DEPOT_LAYOUTS}",
        "needs_ground=1",
        f"icon=> {sheet}.{DEPOT_ICON_CELL}",
        f"cursor={sheet}.{DEPOT_CURSOR_CELL}",
    ]
    for season in (0, 1):
        for layout in range(DEPOT_LAYOUTS):
            row = season * DEPOT_SNOW_ROW
            out.append(f"backimage[{layout}][0][0][0][0][{season}]={sheet}.{row}.{layout},{DEPOT_OFFSET}")
            out.append(f"frontimage[{layout}][0][0][0][0][{season}]={sheet}.{row + 1}.{layout},{DEPOT_OFFSET}")
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
    for name, sheet in ROAD_WALLS.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(wall_dat_text(name, sheet, road=True))
        print(f"[dat] {name}.dat")
    with open(os.path.join(SRC, catalog.ROAD_WALL_TWIN + ".dat"), "w", encoding="utf8", newline=NL) as f:
        f.write(wall_dat_text(catalog.ROAD_WALL_TWIN, "ami_wall_road_back", twin=True, road=True))
    print(f"[dat] {catalog.ROAD_WALL_TWIN}.dat")
    for name, sheet in ROAD_DIVIDERS.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(wall_dat_text(name, sheet, road=True, divider=True))
        print(f"[dat] {name}.dat")
    # twin_divider のアイコン・カーソルは front_divider のシートの、どの dat も指さないセル（TWIN_ICON_CELLS。壁の twin は back のシートの同じセル）
    with open(os.path.join(SRC, catalog.ROAD_DIVIDER_TWIN + ".dat"), "w", encoding="utf8", newline=NL) as f:
        f.write(wall_dat_text(catalog.ROAD_DIVIDER_TWIN, catalog.ROAD_DIVIDERS["front"], twin=True, road=True, divider=True))
    print(f"[dat] {catalog.ROAD_DIVIDER_TWIN}.dat")
    for name, sheet in PIERS.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(pier_dat_text(name, sheet))
        print(f"[dat] {name}.dat")
    for name in catalog.SIDEWALKS:
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(sidewalk_dat_text(name, name))
        print(f"[dat] {name}.dat")
    for name in catalog.SIDEWALK_WALLS:
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(sidewalk_wall_dat_text(name, name))
        print(f"[dat] {name}.dat")
    for name in catalog.EMBANKMENTS:
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(embankment_dat_text(name, name))
        print(f"[dat] {name}.dat")
    # 分岐の追加画像の提供用の物（build.py が別の pak に作り、ex_graft.py で写す）。1 つの dat に --- で区切って並べる
    donors = [dat_text(n, BUILT[n], donor=True) for n in EX_WAYS]
    donors += [wall_dat_text(n, CATENARY[n], catenary=True, donor=True) for n in EX_WAYOBJS]
    with open(os.path.join(SRC, EX_DONORS_DAT), "w", encoding="utf8", newline=NL) as f:
        f.write(("---" + NL).join(donors))
    print(f"[dat] {EX_DONORS_DAT}（{len(donors)} 個）")
    for table, text in ((BRIDGES, bridge_dat_text), (TUNNELS, tunnel_dat_text)):
        for name, (base, sheet) in table.items():
            with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
                f.write(text(name, base, sheet))
            print(f"[dat] {name}.dat")
    for name, (track, road) in catalog.CROSSINGS.items():
        with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(crossing_dat_text(name, track, road))
        print(f"[dat] {name}.dat")
    for depot in catalog.DEPOTS:
        with open(os.path.join(SRC, depot.name + ".dat"), "w", encoding="utf8", newline=NL) as f:
            f.write(depot_dat_text(depot))
        print(f"[dat] {depot.name}.dat")


if __name__ == "__main__":
    main()
