"""AMI の dat を書き出す（Blender は使わない。アドオンのディレクトリで `python -X utf8 blender/ami_dat.py`）。

値（速度・費用・維持費・登場年）は VALUES が持つ。README の「今の決まりごと」と同じにする。
旧描画位置（SIS に合う。#26）の線路は catalog.OLD_TRACKS。名前（ami_rail_<種類>_old…・ami_wall_rail_old_…）と絵のシートが違うだけで、dat の並び・値は新と同じ。
まだ絵を作っていない way は BUILT に入れない（dat も pak も作らない）。シートの行の並びは
    夏の絵 4 行（奥の絵）→ 雪の絵 4 行
で、無壁の線路の並び。カーブは斜めの絵（DIAG_CURVES）を指す。
高架の版（ami_rail_ballast_elev_<版>）は基盤の版と同じ並びで system_type=1。橋脚の way は雪の絵も同じセルで、単柱（ami_pier_rail）は行 0〜3 だけ、
門型（ami_pier_rail_gate）は行 0〜3 が奥の絵、行 4〜7 が手前の絵（PIER_FRONT_ROW）。

基盤の版の way（ami_rail_ballast_base_<版>）は通常の版と同じ並びで、近い斜めの絵を持たない（本体が分け合うタイルに 2 本の way を置き、
奥の線と手前の線を別の版にできる。docs/reference/way-addon.md の 6 章）。壁の way-object（ami_wall_rail_<版>）のシートは
    奥の絵 4 行（backimage）→ 手前の絵 4 行（frontimage）
で、セルの位置は way と同じ。雪の絵は無い（way-object に雪のキーが無い）。ami_wall_rail_twin は近い斜めの分け合うタイル用で、
back と front のシートの斜めのセルを指す（docs/objects/rail.md の「壁の敷き方」）。

架線つきの壁の way-object（ami_wall_rail_<版>_catenary）は壁と同じ並びで、own_waytype=electrified_track（電化）。
ami_wall_rail_twin_catenary は近い斜めの分け合うタイル用で、斜めの梁を短くした back と front の架線つきのシート
（ami_wall_rail_twin_catenary_<back|front>）の斜めのセルを指す（docs/objects/rail.md の「架線の作り」）。

橋（BRIDGES）とトンネル（TUNNELS）は blender-poc の橋・トンネルと同じシートの並びで、手前の絵は無い（壁は way-object）。
makeobj は橋の手前のキーが無いと警告するので、手前のキーは全部、空のセル（BRIDGE_EMPTY_CELL）を指す（docs/objects/rail.md の「橋とトンネルの作り」）。

way・基盤・高架・橋・トンネルの名前は、軌道の種類の表（blender/catalog.py）から展開する。
"""
import os
import sys

import catalog
import src_lock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "blender"))
import marking_kinds  # noqa: E402  路面表示の種類ごとの表（絵のあるセル・雪の絵）。描く側（sheetlib の marking.py）も同じ表を読む（#352）
import sheet_rows  # noqa: E402  行の並び（雪の絵・手前の絵の行のずらし）と offset。シートを描く側（sheetlib）も同じ定義を読む（#302）
import sheet_settings  # noqa: E402  pak の大きさ（SHEET_PAK_SIZE。既定は pak128）

# dat の位置合わせ（セルの左上からタイルの左上までの画素。pak128 は -64,-32）。pak の大きさに比例する（sheetlib の GROUND_CY・ROAD_CY と対応）
OFFSET = f"{-64 * sheet_settings.SCALE},{-32 * sheet_settings.SCALE}"
# pak128 以外の大きさは src<大きさ>/ に書く（pak128 の src/ と混ぜない）。組まない物（catalog.SCALED_EXCLUDED）は書かない（put）
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src" + sheet_settings.SUFFIX)
NL = chr(10)
# 雪の絵の行のずらしは tools/blender/sheet_rows.py の定義を、物ごとに引く（way は way_snow_rows、運河・歩道は CANAL_SNOW_ROWS・SIDEWALK_SNOW_ROWS。今は同じ値）

IMAGES = (  # (キー, 添字, 行, 列)。セル配置は iss・blender-poc の線路と同じ。[0] の夏の絵。雪の絵（[1]）は行を sheet_rows.way_snow_rows だけ下げる
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
# 道路の way（waytype=road）の dat に分岐の絵を書くか。真（既定）で書く。OTRP v64 で KUTA 流の道路の決まりが無くなり、戻した（#46、teamhimeh/simutrans#816、2026-11-23）。外すときは偽にする。
# 外していた間（2026-11-20〜23）の経緯は docs/objects/road.md の「分岐の絵（switch 画像 1・2）」。シートの分岐のセルは描いたまま残す。
# 真にしたら ingame/road_sample.nut の SWITCH_IMAGES も真にする
ROAD_SWITCH_IMAGES = True

# (速度 km/h, 費用, 維持費, 登場年)。費用・維持費は pak128 の way と同じ単位（1/100 cr）。iss の線路（15000・300）を基準にした
VALUES = {
    "ami_tram": dict(waytype="tram_track", speed=60, cost=10000, maintenance=200, intro_year=1900),
    "ami_rail_ballast": dict(waytype="track", speed=160, cost=15000, maintenance=300, intro_year=1900),
    "ami_rail_concrete": dict(waytype="track", speed=240, cost=30000, maintenance=600, intro_year=1960),
    "ami_rail_ladder": dict(waytype="track", speed=360, cost=35000, maintenance=700, intro_year=1990),
    "ami_rail_slab": dict(waytype="track", speed=480, cost=40000, maintenance=800, intro_year=2000),
    "ami_road_local": dict(waytype="road", speed=40, cost=5000, maintenance=100, intro_year=1900),
    "ami_road_general": dict(waytype="road", speed=120, cost=8000, maintenance=200, intro_year=1930),
    "ami_road_trunk": dict(waytype="road", speed=240, cost=14000, maintenance=350, intro_year=1960),  # 値は確定（#257。2026-11-24、ユーザーの判断）
    "ami_road_expressway": dict(waytype="road", speed=360, cost=20000, maintenance=500, intro_year=1990),
    # 跨座式モノレール（#113）。値は #110 の一覧（在来線の高架と同じ費用・維持費。速さは pak128 のモノレールの車両の最高 150）
    "ami_monorail_straddle": dict(waytype="monorail_track", speed=150, cost=30000, maintenance=600, intro_year=1900),
    # 運河（#114）。値は #110 の一覧（速さは pak128 の船の最高 53 km/h が走れる値）
    "ami_canal": dict(waytype="water", speed=60, cost=25000, maintenance=500, intro_year=1900),
    "ami_canal_scenic": dict(waytype="water", speed=60, cost=25000, maintenance=500, intro_year=1900),  # 景観の運河（#161）。実用と同じ値
    # 懸垂式モノレール（#116）。値は #110 の一覧（跨座式と同じ）。地上の 3 版の値（下で版ごとに写す）
    "ami_monorail_suspended": dict(waytype="monorail_track", speed=150, cost=30000, maintenance=600, intro_year=1900),
    # 狭軌（#370）。速さは iss の iss_wng_0030・iss_wng_0060 と同じ。60 の費用・維持費は iss（在来線と同じ 15000・300）、30 は路面軌道と同じ（軽便）
    catalog.NARROW_WOOD: dict(waytype="narrowgauge_track", speed=30, cost=10000, maintenance=200, intro_year=1900),
    catalog.NARROW_BALLAST: dict(waytype="narrowgauge_track", speed=60, cost=15000, maintenance=300, intro_year=1900),
}
# リニア（#371）。値はユーザーの判断 75（案 a）: 速さは iss と同じ 1200 km/h、費用・維持費は高速線（40000・800）の 1.5 倍（iss の 500000・10000 は
# AMI の値から離れすぎるので寄せた）。超電導・常電導・チューブ式で同じ。版・高架は下で写す
MAGLEV_VALUES = dict(waytype="maglev_track", speed=1200, cost=60000, maintenance=1200, intro_year=1900)
for _n in (*catalog.MAGLEV_GUIDEWAYS, *catalog.MAGLEV_BEAMS, *catalog.MAGLEV_TUBES):
    VALUES[_n] = dict(MAGLEV_VALUES)

# 旧描画位置（#26）の線路の値は新と同じ（速さ・費用・維持費・登場年）。名前が違うだけ
for _t in catalog.OLD_TRACKS:
    VALUES[_t.way] = VALUES[_t.way[:-len(catalog.OLD)]]

# カーブを斜めの絵で表すシート（pak128 標準の線路と同じ。dat の image[sw]・[nw]・[ne]・[se] が diagonal と同じセルを指す。
# シートのカーブのセル（行 2 の列 5〜8）は描かない。render.py の diag_curves と同じにする）
DIAG_CURVES = catalog.DIAG_CURVE_WAYS  # 唯一の定義は catalog.py（addon_config.py の DIAG_CURVE_SHEETS と同じ集まり）
CURVE_TO_DIAG = {"[sw]": (2, 0), "[nw]": (2, 1), "[ne]": (2, 2), "[se]": (2, 3)}
# catalog.CORNER_STUB_WAYS の物は、image[sw] などが斜めのセルでなく角のセルを指す（diagonal[...] は斜めのセルのまま。#375）
CURVE_TO_CORNER = {"[sw]": (2, 5), "[nw]": (2, 6), "[ne]": (2, 7), "[se]": (2, 8)}


def curve_cell(name, idx):
    """カーブを斜めの絵で表す物の image[idx]（sw などの曲がり）が指すセル"""
    return (CURVE_TO_CORNER if name in catalog.CORNER_STUB_WAYS else CURVE_TO_DIAG)[idx]

# 手前の絵（frontimage など）を持つ way: シートは 奥の絵 4 行 → 手前の絵 4 行 → 雪の奥の絵 4 行 → 雪の手前の絵 4 行
# （sheetlib の track_sheet の front_row。懸垂式モノレールの柱・梁。#116）。名前の集まり
FRONT_WAYS = catalog.FRONT_WAYS  # 唯一の定義は catalog.py（#242）
FRONT_ROW = sheet_rows.WAY_FRONT_ROW  # render.py の TRACK_PROFILES の front_row と同じ定義
# （手前の絵を持つ way の雪の絵の行のずらし（奥と手前の 8 行の下）は sheet_rows.way_snow_rows(True)）
# 絵を作った way（名前 → シート名）。dat と pak を作る
BUILT = {_n: _n for _n in catalog.BUILT_WAYS}  # 並びの唯一の定義は catalog.py の BUILT_WAYS（#242）
BASE_VARIANTS = catalog.VARIANTS
NO_CLOSE = catalog.NO_CLOSE_WAYS  # 近い斜めの絵を持たない way（唯一の定義は catalog.py）
for _t in catalog.ALL_TRACKS:
    for _v in BASE_VARIANTS:
        # 基盤の版はカーブのセル（行 2 の列 5〜8）を斜めの形で描く（render.py の curve_cells）。斜めのセルとは基盤の削り方だけが違う:
        # 斜めのセルは近い斜めの分け合うタイルのために、壁の無い側を 2 本の真ん中で削る。カーブ（斜めが続かない曲がり）は削らない
        _n = _t.base(_v)
        VALUES[_n] = VALUES[_t.way]
# 路面軌道（#23）。通常の版だけ（並びは catalog.BUILT_WAYS。線路の通常の版と同じで、近い斜め・分岐の絵を持つ）。カーブはカーブのセル（曲線。DIAG_CURVES に入れない）
# 路面軌道の dat に分岐の絵（switch 画像 1・2）を書くか。tram_track は本体で線路と同じ選び方（weg_t::calc_image の track_wt →
# select_switch_image。docs/reference/way-addon.md の 9.2）で、道路の 1・2 のような多車線の交差点の意味は無いので、線路と同じく入れる。
# 道路（ROAD_SWITCH_IMAGES）とはそろえず入れる（2026-11-20、ユーザーの決定。#23）。偽にすると dat から 10 枚を外す（シートのセルは残る）
TRAM_SWITCH_IMAGES = True
# 道路の地上の基盤の版（#22。2026-11-19 にユーザーが確定）: 線路の基盤の版と同じく近い斜めの絵を持たず、カーブはカーブのセル（斜めの形）。
# 値は通常の版と同じ（docs/objects/road.md の「道路の壁・高架・橋脚・橋・トンネルの作り」）
for _r in catalog.ROADS:
    for _v in _r.variants:
        _n = _r.base(_v)
        VALUES[_n] = VALUES[_r.way]

# ---------------------------------------------------------------- 高架の 4 版（#18）
# 基盤の版と同じ並び（近い斜めの絵を持たない）で、system_type=1。値は仮: iss と同じく地上の 2 倍の費用・維持費（速さは地上と同じ）
ELEV_COST_K = 2
ELEVATED = catalog.ELEVATED_WAYS  # 高架（system_type=1）の way（唯一の定義は catalog.py）
for _t in catalog.ALL_TRACKS:
    for _v in BASE_VARIANTS:
        _n = _t.elev(_v)
        VALUES[_n] = dict(VALUES[_t.way], cost=VALUES[_t.way]["cost"] * ELEV_COST_K,
                          maintenance=VALUES[_t.way]["maintenance"] * ELEV_COST_K)
# 道路の高架の 4 版（#22）: 線路の高架と同じく、近い斜めの絵を持たない（分け合うタイルに way が 2 本置かれ、奥の線と手前の線を別の版にできる）。
# カーブはカーブのセル（斜めの形で、壁の無い側をタイルの端まで。render.py の curve_cells）。値の倍率も線路と同じ
for _r in catalog.ROADS:
    for _v in _r.variants:
        _n = _r.elev(_v)
        VALUES[_n] = dict(VALUES[_r.way], cost=VALUES[_r.way]["cost"] * ELEV_COST_K,
                          maintenance=VALUES[_r.way]["maintenance"] * ELEV_COST_K)

# ---------------------------------------------------------------- 跨座式モノレール（#113）
# 物の並びは iss の跨座式に合わせる（2026-11-21、ユーザーの決定）: 地上・高架の 3 版（front・center・back。system_type=1）・トンネル。
# 近い斜めの絵は持たない（iss の dat にキーが無い）。分岐の絵（1・2）は iss と同じく書く（本体は今のところ monorail_track では選ばない。
# boden/wege/weg.cc の calc_image は track_wt と road_wt だけ select_switch_image を呼ぶ）。高架の値の倍率は線路と同じ ELEV_COST_K
for _n in catalog.MONORAIL_ELEVS:
    VALUES[_n] = dict(VALUES[catalog.MONORAIL], cost=VALUES[catalog.MONORAIL]["cost"] * ELEV_COST_K,
                      maintenance=VALUES[catalog.MONORAIL]["maintenance"] * ELEV_COST_K)
# 懸垂式モノレール（#116）: 地上・高架とも柱の側で front・center・back の 3 版（iss の懸垂式と同じ）。柱と梁は way の絵に持たせ、
# 手前の側の柱・梁は手前の絵（FRONT_WAYS）。並びは跨座式と同じ（近い斜め無し・分岐の絵あり）。高架の値の倍率は跨座式と同じ
for _v in catalog.MONORAIL_SUSPENDED_VARIANTS:
    for _elev in (False, True):
        _n = catalog.monorail_suspended(_v, _elev)
        _k = ELEV_COST_K if _elev else 1
        _base = VALUES[catalog.MONORAIL_SUSPENDED]
        VALUES[_n] = dict(_base, cost=_base["cost"] * _k, maintenance=_base["maintenance"] * _k)
# リニアの高架（#371）: 地上の 2 倍（ELEV_COST_K。線路・モノレールと同じ）
for _n in (*catalog.MAGLEV_GUIDEWAY_ELEVS, *catalog.MAGLEV_TUBE_ELEVS,
           *(_e for _w in catalog.MAGLEV_BEAMS for _e in catalog.MAGLEV_BEAM_ELEVS[_w])):
    VALUES[_n] = dict(MAGLEV_VALUES, cost=MAGLEV_VALUES["cost"] * ELEV_COST_K, maintenance=MAGLEV_VALUES["maintenance"] * ELEV_COST_K)

# ---------------------------------------------------------------- 運河（#114）
# 地上の版だけ（iss の運河と同じ。2026-11-22、ユーザーの決定）。近い斜めの絵は持つ（壁の無い way と同じ）。分岐の絵（1・2）は持たない
# （本体は water の way の分岐の絵を選ばない。boden/wege/weg.cc の calc_image は track_wt と road_wt だけ）
NO_DIAG = {catalog.CANAL_SCENIC}  # 斜めの絵（diagonal[...]）を書かない way。景観の運河（#217）は、斜めを L 字のカーブのジグザグにする（iss と同じ）
NO_SWITCH = {catalog.CANAL, catalog.CANAL_SCENIC}  # 分岐の絵（image[nse1] など）を書かない way

# ---------------------------------------------------------------- 橋脚の way（#18）
# 高架の真下の地面のタイルに敷く。waytype は tram_track（iss と同じ。ユーザーの決定、2026-11-18。docs/objects/rail.md の「高架と橋脚の作り」）。
# 本体は track（system_type=7）として読むので、線路の網とつながり、線路の way-object（壁・架線）も載り、道路に重ねられる。
# 値は仮（iss の橋脚と同じ費用・維持費）。topspeed は走らせる物ではないので 1
PIER_VALUES = dict(waytype="tram_track", cost=1000, maintenance=100, intro_year=1900, topspeed=1)
PIERS = {catalog.pier_rail(_g, _o): catalog.pier_rail(_g, _o) for _o in (False, True) for _g in (False, True)}  # 単柱と門型（門型は #18 の追加）。旧描画位置（#26）の橋脚も同じ並び
# 道路用の橋脚（#22）: 線路用と同じ waytype（tram_track。2026-11-19 にユーザーが確定）と値（仮）。シートの並びは単柱の橋脚と同じ（docs/objects/road.md の「道路の壁・高架・橋脚・橋・トンネルの作り」）
PIERS[catalog.PIER_ROAD] = catalog.PIER_ROAD
# 手前の絵（frontimage）を持つ橋脚: 名前 → 手前の絵の行のずらし。シートを描く側の tools/blender/sheetlib/sheetlib.py の
# PIER_GATE_FRONT_ROW（tools/blender/sheet_rows.py）を引く。門型は柱・梁を手前の絵に描く
PIER_FRONT_ROW = {catalog.pier_rail(True, _o): sheet_rows.PIER_GATE_FRONT_ROW for _o in (False, True)}
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
WALLS = {catalog.wall_rail(_v, _o): catalog.wall_rail(_v, _o) for _o in (False, True) for _v in BASE_VARIANTS}  # 新と旧（#26）
WALL_FRONT_ROW = sheet_rows.WALL_FRONT_ROW  # 壁のシートの手前の絵の行（sheetlib も同じ定義）
WAYOBJ_KEYS = {"image": "image", "imageup": "imageup", "imageup2": "imageup2", "diagonal": "diagonal"}  # way のキー → way-object の back/front の後ろ
# 近い斜めの分け合うタイル用: 斜めの向きごとに、タイルの角の側の壁を持つ版のシート（back は nw・sw、front は ne・se。docs/objects/rail.md の「壁の敷き方」）
# 壁だけの twin のアイコン・カーソルのセル（back の版のシートの、どの dat も指さないセル。icons.py が書く。#25）
TWIN_ICON_CELLS = ("0.4", "1.4")
TWIN_FROM = {"[nw]": "ami_wall_rail_back", "[sw]": "ami_wall_rail_back", "[ne]": "ami_wall_rail_front", "[se]": "ami_wall_rail_front"}

# ---------------------------------------------------------------- 道路の壁の way-object（#22）
# waytype=road・own_waytype=road。値は線路の壁と同じ（仮）。版は single・back・center・front（center は線路の center と同じく、側壁が無く
# 行き止まりの端の壁だけ）。シートの並びは線路の壁と同じ。
# 近い斜めの分け合うタイル用の ami_wall_road_twin（名前は 2026-11-19 にユーザーが確定）は、線路の twin と同じ作りで、back・front の斜めのセルを指す
ROAD_WALLS = {f"ami_wall_road_{_v}": f"ami_wall_road_{_v}" for _v in catalog.ROAD_WALL_VARIANTS}
ROAD_WALLS.update({_n: _n for _n in catalog.ROAD_WALL_CURVED})  # カーブの形ごとの single の壁（#260）
ROAD_TWIN_FROM = {k: v.replace("ami_wall_rail_", "ami_wall_road_") for k, v in TWIN_FROM.items()}
# 中央分離帯つきの壁（#118）: 値は #110 で決めた一覧（README の「第 2 弾の物の値」）。速さは壁（1000）・twin（1001）より大きく、壁の上に
# 重ねると分離帯つきに置き換わる。近い斜めの分け合うタイル用の twin_divider は 1 速くする（壁の twin と同じ理由）。
# twin_divider の絵は、西の線（nw・sw）が back の壁、東の線（ne・se）が front_divider（4 車線の手前の線が東になる）
DIVIDER_VALUES = dict(cost=3000, maintenance=60, intro_year=1900, topspeed=1010)
DIVIDER_TWIN_TOPSPEED = DIVIDER_VALUES["topspeed"] + 1
ROAD_DIVIDERS = {_n: _n for _n in catalog.ROAD_DIVIDERS.values()}
ROAD_DIVIDER_TWIN_FROM = {k: (v if v.endswith("_back") else catalog.ROAD_DIVIDERS["front"]) for k, v in ROAD_TWIN_FROM.items()}

# ---------------------------------------------------------------- 架線つきの壁の way-object（線路用、電化。#17）
# 値は仮（docs/objects/rail.md の「架線の作り」）。架線の way-object の topspeed は、電化した編成の速さを縛る（本体の max_wayobj_speed）ので、
# いちばん速い線路（高速線 480 km/h）より大きくする。壁だけの版（1000・twin 1001）より速くして、壁の上に敷くと架線つきに置き換わる
# （逆に、架線つきの上に壁だけの版を敷いても置き換わらない。外してから敷く）。近い斜めの分け合うタイル用の twin は 1 速くする（壁だけの版と同じ理由。
# 壁だけの twin 1001 も置き換える）。twin の絵は、斜めの梁を短くした back・front の版のシート（render.py の TWIN_FROM）
CATENARY_VALUES = dict(cost=4000, maintenance=100, intro_year=1900, topspeed=1100)
CATENARY_TWIN_TOPSPEED = CATENARY_VALUES["topspeed"] + 1
CATENARY = {f"{catalog.wall_rail(_v, _o)}_catenary": f"{catalog.wall_rail(_v, _o)}_catenary" for _o in (False, True) for _v in BASE_VARIANTS}
TWIN_FROM_CATENARY = {k: v.replace("ami_wall_rail_", "ami_wall_rail_twin_catenary_") for k, v in TWIN_FROM.items()}

# ---------------------------------------------------------------- 分岐の追加画像を継ぎ足す物（#57）
# 線路（線路・基盤・高架の版）・路面軌道・道路（通常・基盤・高架の版）の way: 本体（OTRP v64）が Y字分岐・三方分岐で ex 画像を自動で選ぶのは
# track_wt（tram を含む）と road_wt（9.4。v64 は way の種類を問わず同じ決めで選ぶ。道路は #210 でゲームで確かめた）。モノレール・運河は入れない
EX_WAYS = [_n for _n in BUILT if VALUES[_n]["waytype"] in ("track", "tram_track", "road")]
# 架線つきの壁の way-object（twin を除く）: トロリ線を Y字・三方分岐の走行面に合わせた絵を持つ（壁だけの版は絵が T字・十字と同じなので持たない）。
# 本体（obj/wayobj.cc）は、way-object の 26 番の絵があると、隣のタイルの way-object の向きから way と同じ条件で ex 画像を選ぶ。
# 分岐の絵（16 番）が無いとその処理に入らないので、1・2 の 10 枚は T字・十字と同じセルを指す
EX_WAYOBJS = list(CATENARY)


# ---------------------------------------------------------------- 橋とトンネル（#19）
# 橋は欄干を描かず、壁・架線は地上と同じ way-object を重ねる（ADR 0003）。値は仮: 費用・維持費は地上の BRIDGE_COST_K・TUNNEL_COST_K 倍、
# 速さは地上と同じ（docs/objects/rail.md の「橋とトンネルの作り」）。橋の pillar_distance は iss の橋と同じ 1（全部のタイルに橋脚）。
# 橋のシートの並び（render.py の rail_ballast_bridge。blender-poc の橋と同じセル）: 行 0 の列 2・3 が平らな橋（NS・EW）、
# 行 1 が端の坂（列 0〜3 が 1 段、5〜8 が 2 段。並びは way の imageup と同じ 12・9・3・6）、行 2 の列 0・1 が橋脚（南北の橋・東西の橋）、
# 行 3 が坂から始まる端（列 0〜3 が 1 段、5〜8 が 2 段。並びは n・s・e・w）。雪の絵は BRIDGE_SNOW_ROWS 下（橋脚は夏と同じセル）。
# Ramp[N] は北が高い坂の絵、Start[N] は南が高い坂のタイルで使われる（docs/reference/way-addon.md の 5 章）
BRIDGE_COST_K = 4
TUNNEL_COST_K = 4
BRIDGE_SNOW_ROWS = sheet_rows.BRIDGE_SNOW_ROWS
BRIDGE_RAMPS = (("n", 0), ("w", 1), ("s", 2), ("e", 3))  # Ramp の向き → 列（2 段は +5）
BRIDGE_STARTS = (("n", 0), ("s", 1), ("e", 2), ("w", 3))  # Start の向き → 列（2 段は +5）
# makeobj が読む橋の手前の絵のキー（bridge_writer.cc の並び）と、それが指す空のセル（行 0 の列 9。シートの描かない所）
BRIDGE_FRONT_KEYS = (("image", "ns ew".split()), ("start", "nsew"), ("ramp", "nsew"), ("pillar", "sw"),
                     ("image2", "ns ew".split()), ("start2", "nsew"), ("ramp2", "nsew"), ("pillar2", "sw"))
BRIDGE_EMPTY_CELL = "0.9"
BRIDGES = {_t.bridge: (_t.way, _t.bridge) for _t in catalog.ALL_TRACKS}  # 名前 → (地上の way, シート)
BRIDGES.update({_r.bridge: (_r.way, _r.bridge) for _r in catalog.ROADS})  # 道路の橋（#22）。シートの並びは線路の橋と同じ
# トンネルのシートの並び（sheetlib の tunnel_sheet）: 行 0 が奥の絵、行 1 が手前の絵（坑口の躯体）、行 2・3 が雪。列 2〜5 が n・s・e・w。
# image[N] は北が高い坂のタイル。トンネルの中の way は地上の通常の版（way=）
TUNNEL_DIRS = (("n", 2), ("s", 3), ("e", 4), ("w", 5))
TUNNELS = {_t.tunnel: (_t.way, _t.tunnel) for _t in catalog.ALL_TRACKS}  # 名前 → (中の way, シート)
TUNNELS.update({_r.tunnel: (_r.way, _r.tunnel) for _r in catalog.ROADS})  # 道路のトンネル（#22）。シートの並びは線路のトンネルと同じ
TUNNELS[catalog.MONORAIL_TUNNEL] = (catalog.MONORAIL, catalog.MONORAIL_TUNNEL)  # 跨座式モノレールのトンネル（#113）。中の way は地上の版
TUNNELS.update({_n: (_w, _n) for _n, _w in catalog.MAGLEV_TUNNELS.items()})  # リニアのトンネル（#371）。中の way は地上の way（超電導・チューブ式は center の版）
# 狭軌のトンネル（#370）: 60 の版だけ（iss の iss_tn_0060 と同じ。費用・維持費も TUNNEL_COST_K 倍で iss と同じ 60000・1200）
TUNNELS[catalog.NARROW_TUNNEL] = (catalog.NARROW_BALLAST, catalog.NARROW_TUNNEL)


def _head(comment, obj, name, intro_year, before=(), after=()):
    """dat の頭の行（どの dat も共通の並び）: 注記・obj・name・copyright → before → 登場年・退役年 → after。
    before は登場年の前に置くキー（building の type・waytype など）、after は退役年の後のキー（waytype・値・icon・cursor など）。
    before・after に分けるのは、dat のキーの並びを前と変えないため（並びが変わると、比べで差分が出る）"""
    return [
        comment,
        f"obj={obj}",
        f"name={name}",
        "copyright=AMI (CC BY 4.0)",
        *before,
        f"intro_year={intro_year}",
        "intro_month=1",
        "retire_year=2999",
        "retire_month=1",
        *after,
    ]


def _way_values(v, cost_k=1, topspeed=None):
    """waytype・費用・維持費・最高速度の 4 行。cost_k は費用・維持費の倍率。
    最高速度は、v が "topspeed" を持つ表（PIER_VALUES など）ならそれ、VALUES の値（"speed" が最高速度）なら topspeed=v["speed"] を渡す"""
    return [f"waytype={v['waytype']}", f"cost={v['cost'] * cost_k}", f"maintenance={v['maintenance'] * cost_k}",
            f"topspeed={v['topspeed'] if topspeed is None else topspeed}"]


def _head_base(name, kind, obj, base, cost_k):
    """地上の way（base）の値から作る頭の行（橋・トンネル）。最高速度は地上と同じ"""
    v = VALUES[base]
    return _head(f"# AMI: {name}（CC BY 4.0）。{v['speed']} km/h の{kind}。シートは blender/render.py が描く", obj, name, v["intro_year"],
                 after=_way_values(v, cost_k, topspeed=v["speed"]))


def bridge_dat_text(name, base, sheet):
    out = _head_base(name, "橋（欄干なし。壁は way-object を重ねる）", "bridge", base, BRIDGE_COST_K)
    out += ["pillar_distance=1", f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,{OFFSET}"]
    for season in (0, 1):
        dr = season * BRIDGE_SNOW_ROWS
        out += [f"backimage[ns][{season}]={sheet}.{dr}.2,{OFFSET}", f"backimage[ew][{season}]={sheet}.{dr}.3,{OFFSET}"]
        for pre, dc in (("", 0), ("2", 5)):
            out += [f"backramp{pre}[{d}][{season}]={sheet}.{1 + dr}.{c + dc},{OFFSET}" for d, c in BRIDGE_RAMPS]
            out += [f"backstart{pre}[{d}][{season}]={sheet}.{3 + dr}.{c + dc},{OFFSET}" for d, c in BRIDGE_STARTS]
        out += [f"backpillar[s][{season}]={sheet}.2.0,{OFFSET}", f"backpillar[w][{season}]={sheet}.2.1,{OFFSET}"]
        # 手前の絵は無いが、makeobj は front のキーが無いと全部の向きで警告を出す（descriptor/writer/bridge_writer.cc）。空のセルを指す
        for key, dirs in BRIDGE_FRONT_KEYS:
            out += [f"front{key}[{d}][{season}]={sheet}.{BRIDGE_EMPTY_CELL},{OFFSET}" for d in dirs]
    return NL.join(out) + NL


def tunnel_dat_text(name, base, sheet):
    out = _head_base(name, "トンネル", "tunnel", base, TUNNEL_COST_K)
    out += [f"way={base}", f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,{OFFSET}"]
    for season in (0, 1):
        for d, c in TUNNEL_DIRS:
            out += [f"backimage[{d}][{season}]={sheet}.{2 * season}.{c},{OFFSET}",
                    f"frontimage[{d}][{season}]={sheet}.{2 * season + 1}.{c},{OFFSET}"]
    return NL.join(out) + NL


def dat_text(name, sheet, donor=False):
    """way の dat。donor なら分岐の追加画像の提供用の物（名前 + DONOR_SUFFIX。1・2 の 10 枚のキーが EX_CELLS を指す）"""
    v = VALUES[name]
    out = _head(
        f"# AMI: {name}（CC BY 4.0）。{v['speed']} km/h。シートは blender/render.py が描く"
        + ("。分岐の追加画像の提供用（build.py が ex_graft.py で写す。ゲームには入れない）" if donor else ""),
        "way", f"{name}{DONOR_SUFFIX if donor else ''}", v["intro_year"],
        after=[*_way_values(v, topspeed=v["speed"]), f"system_type={1 if name in ELEVATED else 0}",
               f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,{OFFSET}"])
    front = name in FRONT_WAYS
    snow_rows = sheet_rows.CANAL_SNOW_ROWS if name in (catalog.CANAL, catalog.CANAL_SCENIC) else sheet_rows.way_snow_rows(front)
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if name in NO_CLOSE and idx.startswith("[close"):
                continue
            if name in NO_DIAG and key == "diagonal":
                continue
            if key == "image" and idx in SWITCH_IDX and v["waytype"] == "road" and not ROAD_SWITCH_IMAGES:
                continue
            if key == "image" and idx in SWITCH_IDX and name == catalog.TRAM and not TRAM_SWITCH_IMAGES:
                continue
            if key == "image" and idx in SWITCH_IDX and name in NO_SWITCH:
                continue
            if key == "image" and sheet in DIAG_CURVES and idx in CURVE_TO_DIAG:
                row, col = curve_cell(name, idx)
            if donor and key == "image" and idx in EX_CELLS:
                row, col = EX_CELLS[idx]
            out.append(f"{key}{idx}[{season}]={sheet}.{row + season * snow_rows}.{col},{OFFSET}")
            if front:
                out.append(f"front{key}{idx}[{season}]={sheet}.{row + FRONT_ROW + season * snow_rows}.{col},{OFFSET}")
    return NL.join(out) + NL


def wall_dat_text(name, sheet, twin=False, catenary=False, road=False, donor=False, divider=False, old=False):
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
    if old:  # 旧描画位置（#26）の壁: twin が借りるシートも旧の物
        twin_from = {k: s.replace("ami_wall_rail_", "ami_wall_rail_old_") for k, s in twin_from.items()}
    kind = "道路の中央分離帯つきの壁" if divider else "道路の壁" if road else "線路の壁の way-object（架線つき（電化））" if catenary else "線路の壁の way-object（壁だけ、架線なし）"
    wt = "road" if road else "track"
    out = _head(
        f"# AMI: {name}（CC BY 4.0）。{kind}。シートは blender/render.py が描く"
        + ("。分岐の追加画像の提供用（build.py が ex_graft.py で写す。ゲームには入れない）" if donor else ""),
        "way-object", f"{name}{DONOR_SUFFIX if donor else ''}", v["intro_year"],
        after=[f"waytype={wt}", f"own_waytype={'electrified_track' if catenary else wt}",
               f"cost={v['cost']}", f"maintenance={v['maintenance']}",
               f"topspeed={(CATENARY_TWIN_TOPSPEED if catenary else DIVIDER_TWIN_TOPSPEED if divider else WALL_TWIN_TOPSPEED) if twin else v['topspeed']}",
               f"icon=> {sheet}.{icon_cell}", f"cursor={sheet}.{cursor_cell},{OFFSET}"])
    ex = name in EX_WAYOBJS or donor
    cell = {(key, idx): (row, col) for key, idx, row, col in IMAGES}
    for key, idx, row, col in IMAGES:
        if key not in WAYOBJ_KEYS or idx.startswith("[close"):
            continue
        if key == "image" and idx in SWITCH_IDX:
            if not ex:
                continue
            row, col = EX_CELLS[idx] if donor else cell[("image", PIER_SWITCH[idx])]
        if key == "image" and idx in CURVE_TO_DIAG and name not in catalog.ROAD_WALL_CURVED:  # カーブの形ごとの壁（#260）は、カーブのセルが自分の絵
            row, col = CURVE_TO_DIAG[idx]
        src = sheet
        if twin:
            if not ((key == "diagonal" or key == "image") and idx in twin_from):
                continue
            src = twin_from[idx]
        for side, dr in (("back", 0), ("front", WALL_FRONT_ROW)):
            out.append(f"{side}{WAYOBJ_KEYS[key]}{idx}={src}.{row + dr}.{col},{OFFSET}")
    return NL.join(out) + NL


# モノレールの電化の way-object（#116）: waytype=monorail_track・own_waytype=electrified_track。値は線路の架線つきの壁（CATENARY_VALUES）と同じ（仮。
# #110 の一覧に無い）。topspeed は電化した編成の速さを縛る（本体の max_wayobj_speed）ので、モノレール（150 km/h）より大きい
MONORAIL_POWER_VALUES = dict(CATENARY_VALUES)
# リニアのガイド（ami_maglev_guide。#371）: waytype=maglev_track・own_waytype=electrified_track（iss の linear_guide と同じく電化を兼ねる）。
# 値は架線と同じ費用・維持費（ユーザーの判断 75）。topspeed は電化した編成の速さを縛るので、way（1200 km/h）より大きくする
MAGLEV_GUIDE_VALUES = dict(CATENARY_VALUES, topspeed=1300)
# チューブ式のチューブ（ami_maglev_tube_cover。#371）: waytype・own_waytype とも maglev_track（電化しない。手本の marine_express の
# marine_express_tube と同じ）。費用・維持費は手本の費用の比（軌道の約 4 倍。維持費の比は約 4.4 倍）に合わせて、どちらも地上の way の 4 倍。topspeed は way より大きくして縛らない
MAGLEV_TUBE_COVER_VALUES = dict(cost=MAGLEV_VALUES["cost"] * 4, maintenance=MAGLEV_VALUES["maintenance"] * 4, topspeed=1300,
                                intro_year=MAGLEV_VALUES["intro_year"])


def monorail_power_dat_text(name, suspended, waytype="monorail_track", values=None, kind=None, own_waytype="electrified_track"):
    """モノレールの電化の way-object の dat。シートは way-object の並び（奥の絵 0〜3 行・手前の絵 WALL_FRONT_ROW 下）で、
    セルは跨座式の way と同じ位置。カーブは curve_cell（跨座式は角のセル、懸垂式・リニアは斜めのセル）。分岐の絵・近い斜めは持たない。
    リニアのガイドとチューブ（#371）も同じ並びで、waytype・values・kind（注記の物の説明）・own_waytype を渡す"""
    v = values or MONORAIL_POWER_VALUES
    kind = kind or ("懸垂式モノレールの電化（桁の下面の給電レールと碍子）" if suspended else "跨座式モノレールの電化（桁の側面の給電レールと碍子）")
    out = _head(f"# AMI: {name}（CC BY 4.0）。{kind}の way-object。シートは blender/render.py が描く", "way-object", name, v["intro_year"],
                after=[f"waytype={waytype}", f"own_waytype={own_waytype}", f"cost={v['cost']}", f"maintenance={v['maintenance']}",
                       f"topspeed={v['topspeed']}", f"icon=> {name}.0.0", f"cursor={name}.0.1,{OFFSET}"])
    for key, idx, row, col in IMAGES:
        if key not in WAYOBJ_KEYS or idx.startswith("[close") or (key == "image" and idx in SWITCH_IDX):
            continue
        if key == "image" and idx in CURVE_TO_DIAG:
            row, col = curve_cell(name, idx)
        for side, dr in (("back", 0), ("front", WALL_FRONT_ROW)):
            out.append(f"{side}{WAYOBJ_KEYS[key]}{idx}={name}.{row + dr}.{col},{OFFSET}")
    return NL.join(out) + NL


def pier_dat_text(name, sheet):
    """橋脚の way の dat。カーブは斜めのセル、分岐の絵は T字・十字のセル。雪の絵（[1]）は夏と同じセル（柱に雪は描かない）。
    PIER_FRONT_ROW にある橋脚は、同じキーの手前の絵（front<キー>）を、行を下げたセルで足す"""
    v = PIER_VALUES
    cell = {(key, idx): (row, col) for key, idx, row, col in IMAGES}
    out = _head(f"# AMI: {name}（CC BY 4.0）。高架の真下の地面に敷く橋脚の way。シートは blender/render.py が描く", "way", name, v["intro_year"],
                after=[*_way_values(v), "system_type=0", f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,{OFFSET}"])
    front_rows = (0, PIER_FRONT_ROW[name]) if name in PIER_FRONT_ROW else (0,)
    for dr in front_rows:
        for season in (0, 1):
            for key, idx, row, col in IMAGES:
                if key == "image" and idx in CURVE_TO_DIAG:
                    row, col = CURVE_TO_DIAG[idx]
                elif key == "image" and idx in PIER_SWITCH:
                    row, col = cell[("image", PIER_SWITCH[idx])]
                out.append(f"{'front' if dr else ''}{key}{idx}[{season}]={sheet}.{row + dr}.{col},{OFFSET}")
    return NL.join(out) + NL

# 盛土の way（#123。ADR 0008 の景観 6）: 高架の脇の地面に敷く法面の楔。waytype は橋脚と同じ tram_track、速さ 1（ADR 0008）。値は #110 の一覧
EMBANKMENT_VALUES = dict(waytype="tram_track", cost=1000, maintenance=100, intro_year=1900, topspeed=1)
# 雪の絵（[1]）の行のずらし。シートを描く側（tools/blender/sheetlib/sheetlib.py の _EMB_SNOW_ROW）と同じ定義（sheet_rows.py）を引く
EMBANKMENT_SNOW_ROWS = sheet_rows.EMBANKMENT_SNOW_ROWS
# 曲がり（image[sw] など）は行 2 の列 0〜3 の曲がりのセル。斜めの絵（diagonal）は持たない（本体は曲がりの絵を使い、斜めに敷くと角が並ぶ）
EMBANKMENT_CURVES = {"[sw]": (2, 0), "[nw]": (2, 1), "[ne]": (2, 2), "[se]": (2, 3)}


def embankment_dat_text(name, sheet):
    """盛土の way の dat。セルは橋脚のシートと同じ並び（曲がりは EMBANKMENT_CURVES、分岐の絵は T字・十字のセル）。
    雪の絵（[1]）は EMBANKMENT_SNOW_ROWS 下の行"""
    v = EMBANKMENT_VALUES
    cell = {(key, idx): (row, col) for key, idx, row, col in IMAGES}
    out = _head(f"# AMI: {name}（CC BY 4.0）。高架の脇の地面に敷く盛土（法面）の way。シートは blender/render.py が描く", "way", name, v["intro_year"],
                after=[*_way_values(v), "system_type=0", f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,{OFFSET}"])
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if key == "diagonal":
                continue
            if key == "image" and idx in EMBANKMENT_CURVES:
                row, col = EMBANKMENT_CURVES[idx]
            elif key == "image" and idx in PIER_SWITCH:
                row, col = cell[("image", PIER_SWITCH[idx])]
            out.append(f"{key}{idx}[{season}]={sheet}.{row + season * EMBANKMENT_SNOW_ROWS}.{col},{OFFSET}")
    return NL.join(out) + NL

# 盛土の建物の版（#372。ADR 0018）: type=cur の 1 タイルの建物。passengers=0 で乗客の行き先にならず（本体の weight_by_distance は 0 を 0 にする）、
# chance=0 で地図の作成や町の成長で建たない（hausbauer の get_random_desc は 0 を選ばない）。4 向きは layout 0〜3
EMBANKMENT_BUILDING_VALUES = dict(cost=1000, intro_year=1900)


def embankment_building_dat_text(name):
    """盛土の建物の dat。シートは 2 行（夏・雪）× 4 列（layout）で、絵の位置は way と同じ（OFFSET）"""
    v = EMBANKMENT_BUILDING_VALUES
    out = _head(f"# AMI: {name}（CC BY 4.0）。高架の脇の地面に建てる盛土（法面）の建物。シートは blender/render.py が描く", "building", name,
                v["intro_year"], before=["type=cur"],
                after=["dims=1,1,4", "passengers=0", "chance=0", "noconstruction=1", "needs_ground=1",
                       "climates=desert,tropic,mediterran,temperate,tundra,rocky,arctic", f"cost={v['cost']}"])
    for layout in range(4):
        for season in (0, 1):
            out.append(f"backimage[{layout}][0][0][0][0][{season}]={name}.{season}.{layout},{OFFSET}")
    return NL.join(out) + NL


# 説明用の色の way（#372。ADR 0018）: iss の util/describe と同じ値（速さ 1・費用 1・維持費 1）。地上は tram_track、高架は track の system_type=1
DESCRIBE_VALUES = dict(cost=1, maintenance=1, intro_year=1900, topspeed=1)


def describe_dat_text(name, color, elevated):
    """説明用の色の way の dat。地上と高架は同じシート。高架のアイコン・カーソルは (0,4)・(1,4)。雪の絵は夏と同じ。
    近い斜め（close）と分岐の絵は T字・十字のセル（持たない）"""
    v = DESCRIBE_VALUES
    sheet = f"{catalog.PREFIX}describe_{color}"
    cell = {(key, idx): (row, col) for key, idx, row, col in IMAGES}
    icon, cursor = ("0.4", "1.4") if elevated else ("0.0", "0.1")
    waytype = "track" if elevated else "tram_track"
    out = _head(f"# AMI: {name}（CC BY 4.0）。説明用の色の way（{color}。{'高架' if elevated else '地上'}）。シートは blender/render.py が描く",
                "way", name, v["intro_year"],
                after=[f"waytype={waytype}", f"cost={v['cost']}", f"maintenance={v['maintenance']}", f"topspeed={v['topspeed']}",
                       f"system_type={1 if elevated else 0}", f"icon=> {sheet}.{icon}", f"cursor={sheet}.{cursor},{OFFSET}"])
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if idx.startswith("[close"):
                continue
            if key == "image" and idx in PIER_SWITCH:
                row, col = cell[("image", PIER_SWITCH[idx])]
            out.append(f"{key}{idx}[{season}]={sheet}.{row}.{col},{OFFSET}")
    return NL.join(out) + NL


# 多車線と交差点の路面表示の way（#187。ADR 0012）: 道路に重ねて敷く白線と路面の way。waytype は橋脚・盛土と同じ tram_track、速さ 1
# （路面軌道・線路とつながっても速く走れない。車の速さは変わらない）。値は橋脚・盛土と同じ（ADR 0012）
MARKING_VALUES = dict(waytype="tram_track", cost=1000, maintenance=100, intro_year=1900, topspeed=1)
# 種類 → 絵のあるセル・雪の絵を持つか: tools/blender/marking_kinds.py の KINDS（描く側の sheetlib の marking.py も同じ表を読む。#352）。
# ほかの形は空のセル（MARKING_EMPTY_CELL）。雪の絵は MARKING_ROWS 行下
MARKING_EMPTY_CELL = sheet_rows.MARKING_EMPTY_CELL
MARKING_ROWS = sheet_rows.MARKING_ROWS


def marking_dat_text(name, kind):
    """路面表示の way の dat。曲がりは曲がりのセル（斜めの絵は持たない）、分岐の絵は T字・十字のセル（PIER_SWITCH）。
    雪の絵（[1]）は夏と同じセル（車道は除雪した想定で、路面・白線は夏と同じ。路肩の雪は下の道路の絵。ADR 0012）"""
    v = MARKING_VALUES
    cell = {(key, idx): (row, col) for key, idx, row, col in IMAGES}
    out = _head(f"# AMI: {name}（CC BY 4.0）。道路に重ねて敷く路面表示（白線と路面）の way。種類は {kind}。シートは blender/render.py が描く",
                "way", name, v["intro_year"],
                after=[*_way_values(v), "system_type=0", f"icon=> {name}.0.0", f"cursor={name}.0.1,{OFFSET}"])
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if key == "diagonal":
                continue
            if key == "image" and idx in PIER_SWITCH:
                row, col = cell[("image", PIER_SWITCH[idx])]
            if (row, col) not in marking_kinds.KINDS[kind].cells:
                row, col = MARKING_EMPTY_CELL
            elif season and kind in marking_kinds.SNOW_KINDS:
                row += MARKING_ROWS
            out.append(f"{key}{idx}[{season}]={name}.{row}.{col},{OFFSET}")
    return NL.join(out) + NL

# 歩道の way（ami_sidewalk。#24）。waytype は iss の歩道（../refs/iss/src/util/sidewalk/ground.dat）と同じ water（docs/objects/roadside.md の「歩道の作り」）。
# 値は仮（費用・維持費は橋脚と同じ考え方の小さい値。速さ 1 は橋脚と同じ）
SIDEWALK_VALUES = dict(waytype="water", cost=1000, maintenance=20, intro_year=1900, topspeed=1)
# 高架の歩道（ami_sidewalk_elev。#119）: 値は #110 の一覧（docs/objects/roadside.md の「歩道の作り」）。高架は地上の 2 倍
SIDEWALK_ELEV_VALUES = dict(SIDEWALK_VALUES, cost=2000, maintenance=40)
# 歩道の柵（ami_wall_sidewalk_<版>。#119）: water の way-object。値は #110 の一覧（壁と同じ。速さ 1000 は道路の壁と同じで、
# 電柱だけの物（#120、同じ速さ）と重ねると先に置いた方が残る。柵つきの電柱（速さ 1010）を重ねると置き換わる）
SIDEWALK_WALL_VALUES = dict(cost=3000, maintenance=60, intro_year=1900, topspeed=1000)
# 電柱（ami_sidewalk_pole_<版>。#120）: 値は #110 の一覧。柵つきの電柱（ami_wall_sidewalk_<版>_pole）は柵と電柱の和で、速さを柵より大きくし、
# 柵の上に Ctrl を押さずに重ねると柵つきの電柱に置き換わる（way-addon.md の 10 章）。電柱だけの物は柵と同じ速さで、柵とは置き換わらない
SIDEWALK_POLE_VALUES = dict(cost=1000, maintenance=20, intro_year=1900, topspeed=1000)
SIDEWALK_WALL_POLE_VALUES = dict(cost=4000, maintenance=80, intro_year=1900, topspeed=1010)
# 柵の上に柵つきの電柱を重ねると置き換わり、電柱だけでは置き換わらない関係（obj/wayobj.cc の extend_wayobj は速さの小さい方を置き換える）を守る
assert SIDEWALK_WALL_POLE_VALUES["topspeed"] > SIDEWALK_WALL_VALUES["topspeed"] == SIDEWALK_POLE_VALUES["topspeed"], "歩道の柵・電柱の速さの関係が崩れた（#120）"
# 歩道の柵のセル（sheetlib の sidewalk_fence_sheet）: 歩道の way と同じ位置。カーブはシートのカーブのセル（行 2 の列 5〜8）で、斜めのキーは持たない
SIDEWALK_WALL_KEYS = ("image", "imageup", "imageup2")
# 歩道のシートにあるセル（sheetlib の sidewalk_sheet）。斜めの絵・分岐の絵は持たない（本体はカーブの絵を使う）
SIDEWALK_KEYS = ("image", "imageup", "imageup2")


def sidewalk_dat_text(name, sheet):
    """歩道の way の dat。カーブはシートのカーブのセル（行 2 の列 5〜8）。雪の絵（[1]）は SIDEWALK_SNOW_ROWS 下の行。
    高架の歩道（catalog.SIDEWALK_ELEV）は system_type=1 と高架の値"""
    elevated = name == catalog.SIDEWALK_ELEV
    v = SIDEWALK_ELEV_VALUES if elevated else SIDEWALK_VALUES
    out = _head(
        f"# AMI: {name}（CC BY 4.0）。{'高架の歩道の way（道路の高架の隣に敷く）' if elevated else '道路の隣のタイルに敷く歩道の way'}。"
        "シートは blender/render.py が描く",
        "way", name, v["intro_year"],
        after=[*_way_values(v), f"system_type={1 if elevated else 0}", f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,{OFFSET}"])
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if key in SIDEWALK_KEYS and idx not in SWITCH_IDX:
                out.append(f"{key}{idx}[{season}]={sheet}.{row + season * sheet_rows.SIDEWALK_SNOW_ROWS}.{col},{OFFSET}")
    return NL.join(out) + NL


def sidewalk_wall_dat_text(name, sheet, values=None, kind="歩道の柵"):
    """歩道の柵の way-object の dat（waytype=water・own_waytype=water）。奥の絵は行 0〜3、手前の絵は WALL_FRONT_ROW 下の行。
    カーブは歩道の way と同じくカーブのセル（斜めのキーは持たない。本体は斜めの絵の無い way-object にカーブの絵を使う）"""
    v = values or SIDEWALK_WALL_VALUES
    out = _head(f"# AMI: {name}（CC BY 4.0）。{kind}（歩道の way に重ねる way-object）。シートは blender/render.py が描く",
                "way-object", name, v["intro_year"],
                after=["waytype=water", "own_waytype=water", f"cost={v['cost']}", f"maintenance={v['maintenance']}",
                       f"topspeed={v['topspeed']}", f"icon=> {sheet}.0.0", f"cursor={sheet}.0.1,{OFFSET}"])
    for key, idx, row, col in IMAGES:
        if key not in SIDEWALK_WALL_KEYS or idx in SWITCH_IDX or idx.startswith("[close"):
            continue
        for side, dr in (("back", 0), ("front", WALL_FRONT_ROW)):
            out.append(f"{side}{WAYOBJ_KEYS[key]}{idx}={sheet}.{row + dr}.{col},{OFFSET}")
    return NL.join(out) + NL


# ---------------------------------------------------------------- 踏切（線路 × 道路。#111）
# 線路 4 種 × 道路 4 種の 16 個（catalog.CROSSINGS）。本体は踏切を waytype の組と速さだけで選ぶ（dataobj/crossing_logic.cc の get_crossing。
# way の名前は見ない）ので、組ごとに速さの合う踏切を置く。絵は道路の種類ごとのシート（catalog.crossing_sheet）で、線路の 4 種で同じ。
# 値は仮（#110 で決める）: 速さは両方の way の最高速度（踏切で速度を落とさない）、登場年は 2 つの way の遅い方、音なし（iss と同じ sound=-1）。
# シートの並び（sheetlib の crossing.py）: 列 = (道路の向き, 閉じた絵か)、行 0・1 が夏の奥・手前、行 2・3 が雪の奥・手前。
# dat の [ns]・[ew] は waytype[0]（道路）の向き
CROSSING_COLS = {("ns", False): 0, ("ns", True): 1, ("ew", False): 2, ("ew", True): 3}  # crossing.py の CROSSING_COLS と同じ
CROSSING_SNOW_ROW = sheet_rows.CROSSING_SNOW_ROW


def crossing_dat_text(name, track, road):
    t, r = VALUES[track.way], VALUES[road.way]
    sheet = catalog.crossing_sheet(road)
    out = _head(f"# AMI: {name}（CC BY 4.0）。{track.way} × {road.way} の踏切。値は仮（#110）。シートは blender/render.py が描く",
                "crossing", name, max(t["intro_year"], r["intro_year"]),
                after=["sound=-1", "waytype[0]=road", f"speed[0]={r['speed']}", "waytype[1]=track", f"speed[1]={t['speed']}"])
    for season in (0, 1):
        row = season * CROSSING_SNOW_ROW
        for d in ("ns", "ew"):
            for closed, key in ((False, "openimage"), (True, "closedimage")):
                col = CROSSING_COLS[(d, closed)]
                out.append(f"{key}[{d}][{season}]={sheet}.{row}.{col},{OFFSET}")
                out.append(f"front_{key}[{d}][{season}]={sheet}.{row + 1}.{col},{OFFSET}")
    return NL.join(out) + NL



# ---------------------------------------------------------------- 水路の踏切（線路・道路 × 運河。#117）
# 線路 4 種・道路 3 種 × 運河の 7 個（catalog.CANAL_CROSSINGS）。跳ね橋で、船（waytype[1] の water）が来ると閉じる（桁を起こす）。
# 値は #110 の一覧: 運河の側は 60 km/h、線路・道路の側は線路×道路の踏切と同じく way の最高速度（踏切で速度を落とさない）。
# 登場年は 2 つの way の遅い方、音なし。シートの並びは線路×道路の踏切と同じ（sheetlib の canal_crossing.py）


def canal_crossing_dat_text(name, way):
    w, c = VALUES[way.way], VALUES[catalog.CANAL]
    sheet = catalog.canal_crossing_sheet(way)
    out = _head(f"# AMI: {name}（CC BY 4.0）。{way.way} × {catalog.CANAL} の踏切（跳ね橋）。シートは blender/render.py が描く",
                "crossing", name, max(w["intro_year"], c["intro_year"]),
                after=["sound=-1", f"waytype[0]={w['waytype']}", f"speed[0]={w['speed']}", "waytype[1]=water", f"speed[1]={c['speed']}"])
    for season in (0, 1):
        row = season * CROSSING_SNOW_ROW
        for d in ("ns", "ew"):
            for closed, key in ((False, "openimage"), (True, "closedimage")):
                col = CROSSING_COLS[(d, closed)]
                out.append(f"{key}[{d}][{season}]={sheet}.{row}.{col},{OFFSET}")
                out.append(f"front_{key}[{d}][{season}]={sheet}.{row + 1}.{col},{OFFSET}")
    return NL.join(out) + NL

# 車庫（building の depot。#112）。シートの並びは sheetlib の depot.py（列 = layout 0〜3、行 0・1 が夏の奥・手前、行 2・3 が雪の奥・手前、
# 列 4 の行 0・1 がアイコン・カーソル）。layout は道の出る向き（0 = 南・1 = 東・2 = 北・3 = 西。simtool.cc の tool_depot_aux）。
# 費用・維持費は省かず pak128 の既定値を書く（docs/objects/depot.md の「車庫の作り」。省いたり 0 にしたりしない）。dat の値は 1/100 cr
DEPOT_VALUES = {"track": dict(cost=850000, maintenance=1800), "tram_track": dict(cost=850000, maintenance=1800),
                "road": dict(cost=700000, maintenance=1800), "monorail_track": dict(cost=850000, maintenance=1800),
                "water": dict(cost=900000, maintenance=1800),  # 船の車庫（#114）
                "maglev_track": dict(cost=850000, maintenance=1800),  # リニアの車庫（#371。モノレールと同じ）
                "narrowgauge_track": dict(cost=850000, maintenance=1800)}  # 狭軌の車庫（#370）。線路の車庫と同じ
DEPOT_INTRO_YEAR = 1900
DEPOT_LAYOUTS = 4
DEPOT_SNOW_ROW = sheet_rows.DEPOT_SNOW_ROW
DEPOT_ICON_CELL = "0.4"  # sheetlib の depot.DEPOT_ICON_CELL と同じ
DEPOT_CURSOR_CELL = "1.4"  # sheetlib の depot.DEPOT_CURSOR_CELL と同じ
DEPOT_OFFSET = f"{sheet_rows.BUILDING_OFFSET[0]},{sheet_rows.BUILDING_OFFSET[1]}"  # sheetlib の depot.BUILDING_OFFSET（同じ定義）


def depot_dat_text(depot):
    v = DEPOT_VALUES[depot.waytype]
    sheet = depot.name
    out = _head(f"# AMI: {depot.name}（CC BY 4.0）。車庫。シートは blender/render.py が描く（sheetlib の depot.py）",
                "building", depot.name, DEPOT_INTRO_YEAR, before=["type=depot", f"waytype={depot.waytype}"],
                after=[f"cost={v['cost']}", f"maintenance={v['maintenance']}", "noinfo=1", f"dims=1,1,{DEPOT_LAYOUTS}", "needs_ground=1",
                       f"icon=> {sheet}.{DEPOT_ICON_CELL}", f"cursor={sheet}.{DEPOT_CURSOR_CELL},{DEPOT_OFFSET}"])
    for season in (0, 1):
        for layout in range(DEPOT_LAYOUTS):
            row = season * DEPOT_SNOW_ROW
            out.append(f"backimage[{layout}][0][0][0][0][{season}]={sheet}.{row}.{layout},{DEPOT_OFFSET}")
            out.append(f"frontimage[{layout}][0][0][0][0][{season}]={sheet}.{row + 1}.{layout},{DEPOT_OFFSET}")
    return NL.join(out) + NL


# 操車場（building の stop。#115）。シートの並びは sheetlib の yard.py（列 = layout 0〜7、行 0・1 が夏・雪の奥の絵、列 8 の行 0・1 が
# アイコン・カーソル）。layout は線路の向きと、隣の駅の建物の有無（ビット 0 = 東西、2 = 南・東の端、4 = 北・西の端。本体の
# hausbauer.cc の build_station_extension_depot。docs/objects/depot.md の「操車場の作り」）。荷を扱わない（enables_* を書かない）。
# 費用・維持費は省かず書く（#110。pak128 の cost_multiply_station 600 cr・maintenance_building 1800。dat の値は 1/100 cr）
YARD_VALUES = dict(cost=60000, maintenance=1800, level=1)
YARD_INTRO_YEAR = 1900
YARD_LAYOUTS = 8
YARD_SNOW_ROW = sheet_rows.YARD_SNOW_ROW
YARD_ICON_CELL = f"0.{YARD_LAYOUTS}"  # sheetlib の yard.YARD_ICON_CELL と同じ
YARD_CURSOR_CELL = f"1.{YARD_LAYOUTS}"


def yard_dat_text(name):
    v = YARD_VALUES
    out = _head(f"# AMI: {name}（CC BY 4.0）。操車場（荷を扱わない線路の駅の建物）。シートは blender/render.py が描く（sheetlib の yard.py）",
                "building", name, YARD_INTRO_YEAR, before=["type=stop", "waytype=track"],
                after=[f"cost={v['cost']}", f"maintenance={v['maintenance']}", f"level={v['level']}", "noinfo=1", "noconstruction=1",
                       f"dims=1,1,{YARD_LAYOUTS}", "needs_ground=1", f"icon=> {name}.{YARD_ICON_CELL}",
                       f"cursor={name}.{YARD_CURSOR_CELL},{DEPOT_OFFSET}"])
    for season in (0, 1):
        for layout in range(YARD_LAYOUTS):
            out.append(f"backimage[{layout}][0][0][0][0][{season}]={name}.{season * YARD_SNOW_ROW}.{layout},{DEPOT_OFFSET}")
    return NL.join(out) + NL


# 転車台・遷車台（#314）。iss の転車台とトラバーサー（../refs/iss/src/util/rail_misc/table.dat）と同じく道路（road）の way 1 つで、
# つながりの無い 1 タイル（image[-]）が転車台、直線と行き止まりが遷車台。速さ 65535 は iss と同じで、本体が道路を自動で選ぶとき
# （橋・トンネルの上の way・町の道路。bauer/wegbauer.cc の weg_search は求める速さ以下でいちばん速い物を選ぶ）に選ばれないようにする。
# 絵はシートの way の位置（IMAGES）で、カーブ・T 字・十字も持つ（iss は持たず、敷くと見えない way が残る）。坂・斜め・分岐の絵は持たない（docs/objects/depot.md の「転車台・遷車台の作り」）
TURNTABLE_VALUES = dict(waytype="road", cost=1000, maintenance=100, topspeed=65535, intro_year=1900)
TURNTABLE_KEYS = ("[ns]", "[ew]", "[s]", "[w]", "[n]", "[e]", "[-]", "[sw]", "[nw]", "[ne]", "[se]", "[nse]", "[new]", "[nsw]", "[sew]", "[nsew]")


def turntable_dat_text(name):
    v = TURNTABLE_VALUES
    out = _head(f"# AMI: {name}（CC BY 4.0）。転車台・遷車台（道路の way。1 タイルで転車台、直線に敷くと遷車台）。シートは blender/render.py が描く（sheetlib の turntable.py）",
                "way", name, v["intro_year"],
                after=[*_way_values(v), "system_type=0", f"icon=> {name}.0.0", f"cursor={name}.0.1,{OFFSET}"])
    for season in (0, 1):
        for key, idx, row, col in IMAGES:
            if key == "image" and idx in TURNTABLE_KEYS:
                out.append(f"image{idx}[{season}]={name}.{row + season * sheet_rows.WAY_SNOW_ROWS}.{col},{OFFSET}")
    return NL.join(out) + NL


# 道路標識（roadsign。#122）。値は #110 の一覧（費用 500 cr。roadsign の cost は cr 単位で、makeobj が 100 倍する。維持費のキーは無い）。
# 効き目は一方通行（single_way）と最低速度（min_speed）だけ。止まれ・最高速度は飾り（本体に速さの上限のキーが無い。#122 の案 A）
ROADSIGN_COST = 500
ROADSIGN_INTRO_YEAR = 1900
ROADSIGN_EFFECT = {"one_way": "single_way=1", "min_50": "min_speed=50"}
ROADSIGN_OFFSET_LEFT = 14  # 左側通行のときのずらし（本体の既定と同じ値を明示する。obj/roadsign.cc の calc_image）。単位はタイルの幅の 1/64（描くときに tile_raster_scale_x で現在のタイルの幅に直す）なので、pak の大きさによらず同じ値（256 でも 14。倍にすると標識が 1 タイル近く外へずれる。#261 の B で確かめた）
ROADSIGN_ICON_CELL = "0.4"  # sheetlib の roadsign.ROADSIGN_ICON_CELL と同じ
ROADSIGN_CURSOR_CELL = "1.4"  # sheetlib の roadsign.ROADSIGN_CURSOR_CELL と同じ
ROADSIGN_OFFSET = OFFSET  # 道路の way と同じ（sheetlib の ROAD_CY）


def roadsign_dat_text(name, key):
    out = _head(f"# AMI: {name}（CC BY 4.0）。道路標識。シートは blender/render.py が描く（sheetlib の roadsign.py）",
                "roadsign", name, ROADSIGN_INTRO_YEAR, before=["waytype=road"],
                after=[f"cost={ROADSIGN_COST}", f"offset_left={ROADSIGN_OFFSET_LEFT}"])
    if key in ROADSIGN_EFFECT:
        out.append(ROADSIGN_EFFECT[key])
    out += [f"icon=> {name}.{ROADSIGN_ICON_CELL}", f"cursor={name}.{ROADSIGN_CURSOR_CELL},{ROADSIGN_OFFSET}"]
    out += [f"image[{i}]={name}.0.{i},{ROADSIGN_OFFSET}" for i in range(4)]
    return NL.join(out) + NL


ROADSIGN_CROSSWALK_OFFSET_LEFT = 0  # 点対称（180° 回すと重なる）の路面の絵なので、左側通行でずらさない（iss の横断歩道と同じ）


def crosswalk_dat_text(name, one_way):
    """路面の横断歩道の標識（#162）。両方向は image[0]（南北）・[2]（東西）だけ、一方通行は 4 向き（北・南・西・東行き）"""
    out = _head(f"# AMI: {name}（CC BY 4.0）。路面の横断歩道の標識。シートは blender/render.py が描く（sheetlib の roadsign.py。#162）",
                "roadsign", name, ROADSIGN_INTRO_YEAR, before=["waytype=road"],
                after=[f"cost={ROADSIGN_COST}", f"offset_left={ROADSIGN_CROSSWALK_OFFSET_LEFT}", f"single_way={1 if one_way else 0}",
                       "no_foreground=1",  # 路面の標示は車両の下に描く（#187・#189 の路面表示と同じ。向きによって手前になるのを防ぐ）
                       f"icon=> {name}.{ROADSIGN_ICON_CELL}", f"cursor={name}.{ROADSIGN_CURSOR_CELL},{ROADSIGN_OFFSET}"])
    cell = {0: 0, 1: 1, 2: 2, 3: 3} if one_way else {0: 0, 1: None, 2: 1, 3: None}
    out += [f"image[{i}]={name}.0.{c},{ROADSIGN_OFFSET}" if c is not None else f"image[{i}]=-" for i, c in cell.items()]
    return NL.join(out) + NL


def put(name, text):
    """dat を書く。pak128 以外の大きさは、組まない物（catalog.SCALED_EXCLUDED。#301。今は無い）だけ書かない"""
    if sheet_settings.SCALE != 1 and name in catalog.SCALED_EXCLUDED:
        return
    with open(os.path.join(SRC, name + ".dat"), "w", encoding="utf8", newline=NL) as f:
        f.write(text)
    print(f"[dat] {name}.dat" + (f"（pak{sheet_settings.PAK_SIZE}）" if sheet_settings.SCALE != 1 else ""))


def main():
    # --out <フォルダ>: src/ の代わりにそこへ書く（check.sh が src/ を消さずに書き忘れを比べる。#326）。src/ に書くときは、
    # check.sh・build.py と重ならないようにロックを取る（src_lock.py）
    global SRC
    if len(sys.argv) == 3 and sys.argv[1] == "--out":
        SRC = sys.argv[2]
        write_all()
        return
    if len(sys.argv) != 1:
        sys.exit("使い方: ami_dat.py [--out <フォルダ>]")
    with src_lock.hold("ami_dat.py"):
        write_all()


def write_all():
    os.makedirs(SRC, exist_ok=True)
    for name, sheet in BUILT.items():
        put(name, dat_text(name, sheet))
    for name, sheet in WALLS.items():
        put(name, wall_dat_text(name, sheet, old=catalog.is_old(name)))
    for _o in (False, True):  # 新と旧（#26）
        _tw = f"ami_wall_rail_{'old_' if _o else ''}twin"
        put(_tw, wall_dat_text(_tw, catalog.wall_rail("back", _o), twin=True, old=_o))
    for name, sheet in CATENARY.items():
        put(name, wall_dat_text(name, sheet, catenary=True, old=catalog.is_old(name)))
    for name, suspended in catalog.MONORAIL_POWERS.items():
        put(name, monorail_power_dat_text(name, suspended))
    put(catalog.MAGLEV_GUIDE, monorail_power_dat_text(catalog.MAGLEV_GUIDE, False, "maglev_track", MAGLEV_GUIDE_VALUES,
                                                      "超電導リニアのガイド（U 字の側壁とコイル。電化を兼ねる）"))
    put(catalog.MAGLEV_TUBE_COVER, monorail_power_dat_text(catalog.MAGLEV_TUBE_COVER, False, "maglev_track", MAGLEV_TUBE_COVER_VALUES,
                                                           "チューブ式リニアのチューブ（輪の骨組み。電化しない）", "maglev_track"))
    for _o in (False, True):  # 新と旧（#26）
        _tw = f"ami_wall_rail_{'old_' if _o else ''}twin_catenary"
        put(_tw, wall_dat_text(_tw, _tw + "_back", twin=True, catenary=True, old=_o))
    for name, sheet in ROAD_WALLS.items():
        put(name, wall_dat_text(name, sheet, road=True))
    put(catalog.ROAD_WALL_TWIN, wall_dat_text(catalog.ROAD_WALL_TWIN, "ami_wall_road_back", twin=True, road=True))
    for name, sheet in ROAD_DIVIDERS.items():
        put(name, wall_dat_text(name, sheet, road=True, divider=True))
    # twin_divider のアイコン・カーソルは front_divider のシートの、どの dat も指さないセル（TWIN_ICON_CELLS。壁の twin は back のシートの同じセル）
    put(catalog.ROAD_DIVIDER_TWIN, wall_dat_text(catalog.ROAD_DIVIDER_TWIN, catalog.ROAD_DIVIDERS["front"], twin=True, road=True, divider=True))
    for name, sheet in PIERS.items():
        put(name, pier_dat_text(name, sheet))
    for name in catalog.SIDEWALKS:
        put(name, sidewalk_dat_text(name, name))
    for name in catalog.SIDEWALK_WALLS:
        put(name, sidewalk_wall_dat_text(name, name))
    for name, (variant, fence) in catalog.SIDEWALK_POLES.items():
        put(name, sidewalk_wall_dat_text(name, name, SIDEWALK_WALL_POLE_VALUES if fence else SIDEWALK_POLE_VALUES,
                                         f"歩道の柵（{variant}）と電柱" if fence else f"電柱（{variant}。タイルのわきに立てる）"))
    for name in catalog.EMBANKMENTS:
        put(name, embankment_dat_text(name, name))
    for name, kind in catalog.MARKINGS.items():
        put(name, marking_dat_text(name, kind))
    for name in catalog.EMBANKMENT_BUILDINGS:
        put(name, embankment_building_dat_text(name))
    for name, (color, elevated) in catalog.DESCRIBES.items():
        put(name, describe_dat_text(name, color, elevated))
    # 分岐の追加画像の提供用の物（build.py が別の pak に作り、ex_graft.py で写す）。1 つの dat に --- で区切って並べる
    donors = [dat_text(n, BUILT[n], donor=True) for n in EX_WAYS]
    donors += [wall_dat_text(n, CATENARY[n], catenary=True, donor=True) for n in EX_WAYOBJS]
    with open(os.path.join(SRC, EX_DONORS_DAT), "w", encoding="utf8", newline=NL) as f:
        f.write(("---" + NL).join(donors))
    print(f"[dat] {EX_DONORS_DAT}（{len(donors)} 個）")
    for table, text in ((BRIDGES, bridge_dat_text), (TUNNELS, tunnel_dat_text)):
        for name, (base, sheet) in table.items():
            put(name, text(name, base, sheet))
    for name, (track, road) in catalog.CROSSINGS.items():
        put(name, crossing_dat_text(name, track, road))
    for name, way in catalog.CANAL_CROSSINGS.items():
        put(name, canal_crossing_dat_text(name, way))
    for depot in catalog.DEPOTS:
        put(depot.name, depot_dat_text(depot))
    put(catalog.RAIL_YARD, yard_dat_text(catalog.RAIL_YARD))
    put(catalog.RAIL_TURNTABLE, turntable_dat_text(catalog.RAIL_TURNTABLE))
    for name, key in catalog.ROADSIGNS.items():
        put(name, roadsign_dat_text(name, key))
    for name, one_way in catalog.ROADSIGN_CROSSWALKS.items():
        put(name, crosswalk_dat_text(name, one_way))


if __name__ == "__main__":
    main()
