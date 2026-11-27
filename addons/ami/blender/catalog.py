"""AMI の軌道の種類の表（Blender を使わない）。blender/render.py・ami_dat.py・addon_config.py が、ここから名前を展開する。

軌道の種類を足すときは TRACKS に 1 件足し、render.py の TRACK_SETTINGS に描き分けを足す（値は ami_dat.py の VALUES）。
共有の壁・架線・橋脚（ami_wall_rail_*・ami_pier_rail*）は軌道の種類に属さないので、ここには持たない。
道路の種類は ROADS に足し、render.py の ROAD_SETTINGS に描き分けを足す（線路の Track と同じ考え方）。
"""
import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "blender"))
import marking_kinds  # noqa: E402  路面表示の種類ごとの表（Blender を使わない。#352）

PREFIX = "ami_"
VARIANTS = ("single", "back", "center", "front")  # 基盤・高架の版（並びは iss・SIS と同じ）


@dataclass(frozen=True)
class Track:
    """軌道の種類 1 つ。key は way の名前から PREFIX を除いたもの（render.py の TRACK_PROFILES の名前の元）。"""
    key: str

    @property
    def way(self):
        return PREFIX + self.key

    def base(self, variant):
        return f"{self.way}_base_{variant}"

    def elev(self, variant):
        return f"{self.way}_elev_{variant}"

    @property
    def bridge(self):
        return f"{self.way}_bridge"

    @property
    def tunnel(self):
        return f"{self.way}_tunnel"


def profile(name):
    """way・シートの名前 → TRACK_PROFILES の名前（PREFIX を除く）。"""
    return name[len(PREFIX):]


@dataclass(frozen=True)
class Road:
    """道路の種類 1 つ。key は way の名前から PREFIX を除いたもの（render.py の ROAD_PROFILES の名前の元）。
    通常の版の way・地上の基盤の版と高架の 4 版・橋・トンネル（#21・#22）。基盤の版は 2026-11-19 にユーザーが確定（
    docs/objects/road.md の「道路の壁・高架・橋脚・橋・トンネルの作り」）"""
    key: str
    variants: tuple = VARIANTS  # 基盤・高架を作る版（一般道路・生活道路は single だけ。#260）

    @property
    def way(self):
        return PREFIX + self.key

    def base(self, variant):
        return f"{self.way}_base_{variant}"

    def elev(self, variant):
        return f"{self.way}_elev_{variant}"

    @property
    def bridge(self):
        return f"{self.way}_bridge"

    @property
    def tunnel(self):
        return f"{self.way}_tunnel"


RAIL_BALLAST = Track("rail_ballast")  # 在来線（バラスト軌道）
RAIL_SLAB = Track("rail_slab")  # 高速線（スラブ軌道）
RAIL_CONCRETE = Track("rail_concrete")  # 弾性まくらぎ直結軌道（240 km/h。#62）
RAIL_LADDER = Track("rail_ladder")  # フローティング・ラダー軌道（360 km/h。#67）
TRACKS = (RAIL_BALLAST, RAIL_CONCRETE, RAIL_LADDER, RAIL_SLAB)
WALL_TRACK = RAIL_BALLAST  # 共有の壁・架線のシートを描く元の軌道（ほかの種類の基盤の版は、壁のシートを書かない）

# 旧描画位置（SIS に合う。#26。ADR 0011）の線路: 新と同じ 4 種を、基準面を動かさない描き方で作る。名前は way・基盤・高架・橋・トンネルとも
# 新の名前の種類の後に _old を入れる（ami_rail_ballast_old・ami_rail_ballast_old_base_<版>）。旧用の壁・架線・橋脚も同じ（wall_rail・pier_rail）。
# 踏切（CROSSINGS）・水路の踏切は新の線路だけ（旧の線路には作らない）ので、TRACKS には旧を入れない
OLD = "_old"
OLD_TRACKS = tuple(Track(_t.key + OLD) for _t in TRACKS)
ALL_TRACKS = TRACKS + OLD_TRACKS
WALL_TRACK_OLD = Track(WALL_TRACK.key + OLD)  # 旧用の壁・架線のシートを描く元の軌道


def is_old(name):
    """名前（way・way-object・シート）が旧描画位置の物か。ami_rail_<種類>_old…・ami_wall_rail_old_…・ami_pier_rail_old…"""
    return re.match(r"(rail_[a-z]+_old(_|$)|wall_rail_old_|pier_rail_old)", name[len(PREFIX):]) is not None


def wall_rail(variant, old=False):
    """線路の壁の way-object の名前（ami_wall_rail_<版>。旧は ami_wall_rail_old_<版>）"""
    return f"{PREFIX}wall_rail_{'old_' if old else ''}{variant}"


def pier_rail(gate=False, old=False):
    """線路用の橋脚の way の名前（ami_pier_rail・ami_pier_rail_gate。旧は ami_pier_rail_old・ami_pier_rail_old_gate）"""
    return f"{PREFIX}pier_rail{'_old' if old else ''}{'_gate' if gate else ''}"

# 路面軌道（60 km/h、tram で道路に重ねる。ADR 0002）。通常の版だけ（壁・基盤・高架・橋・トンネルを作らない）ので、TRACKS に入れない
# （TRACKS の種類は基盤・高架・橋・トンネルの名前を導き、カーブを斜めの絵にする。路面軌道のカーブは曲線のまま。docs/objects/rail.md の「路面軌道の作り」）
TRAM = "ami_tram"

# 跨座式モノレール（150 km/h、monorail_track。#113。名前は ADR 0008）。物の並びは iss の跨座式（地上・高架の front・center・back・トンネル）に合わせる
# （2026-11-21、ユーザーの決定）。線路と違い基盤・橋を作らないので、TRACKS に入れない（TRACKS の種類は基盤・高架・橋の名前を導く）
MONORAIL = "ami_monorail_straddle"
MONORAIL_ELEV_VARIANTS = ("front", "center", "back")  # 高架の版（iss と同じ 3 版。柱を立てる側。single は作らない）


def monorail_elev(variant):
    """跨座式モノレールの高架の版の名前（ami_monorail_elev_<版>）"""
    return f"{MONORAIL}_elev_{variant}"


MONORAIL_ELEVS = tuple(monorail_elev(_v) for _v in MONORAIL_ELEV_VARIANTS)
MONORAIL_TUNNEL = f"{MONORAIL}_tunnel"

# 懸垂式モノレール（150 km/h、monorail_track。#116。名前は ADR 0008）。物の並びは iss の懸垂式に合わせる（2026-11-22、進捗管理の決定。
# 支柱は way の絵に持たせる案 A）: 地上・高架とも柱の側で front・center・back の 3 版。トンネルは作らない（docs/objects/monorail.md の「懸垂式モノレールの作り」）
MONORAIL_SUSPENDED = "ami_monorail_suspended"
MONORAIL_SUSPENDED_VARIANTS = MONORAIL_ELEV_VARIANTS


def monorail_suspended(variant, elevated=False):
    """懸垂式モノレールの名前（地上は ami_monorail_suspended_<版>、高架は ami_monorail_suspended_elev_<版>）"""
    return f"{MONORAIL_SUSPENDED}_{'elev_' if elevated else ''}{variant}"


MONORAIL_SUSPENDEDS = tuple(monorail_suspended(_v) for _v in MONORAIL_SUSPENDED_VARIANTS)
MONORAIL_SUSPENDED_ELEVS = tuple(monorail_suspended(_v, True) for _v in MONORAIL_SUSPENDED_VARIANTS)
# モノレールの電化の way-object（own_waytype=electrified_track。#116）: 電車のモノレールの車両を走らせる。方式ごとに 2 つ
# （2026-11-22、進捗管理の決定）。名前 → 懸垂式用か（絵の作りは sheetlib の monorail_parts の power_*）
MONORAIL_POWERS = {f"{PREFIX}monorail_power": False, f"{PREFIX}monorail_suspended_power": True}
# 直角の曲がりの角を、軸向きに少し進んでから斜めに曲がる形にする物（#375。跨座式の地上・高架と、その桁に付く電化）。
# 角の絵はシートの行 2 の列 5〜8（dat の image[sw]・[nw]・[ne]・[se]）、斜めの走りの diagonal[...] は列 0〜3。render.py の "corner_stub"
CORNER_STUB_WAYS = (MONORAIL, *MONORAIL_ELEVS, *(_n for _n, _susp in MONORAIL_POWERS.items() if not _susp))

# リニア（1200 km/h、maglev_track。#371。範囲は ADR 0017）。iss のリニア 3 種を、形で名前を付けて作る（2026-11-26、ユーザーの判断 75・案 a）。
# 橋・留置線は作らない。トンネルの中の way は地上の way（超電導は center の版）。docs/objects/maglev.md の「リニアの作り」
#   超電導 ami_maglev_guideway_<版>（地上 4 版。防音壁は way の絵）・ami_maglev_guideway_elev_<版>（高架 4 版）・
#     ami_maglev_guide（U 字の側壁の way-object。電化を兼ねる）・ami_maglev_guideway_tunnel
#   常電導 ami_maglev_beam（地上）・ami_maglev_beam_elev_<front|center|back>・ami_maglev_beam_tunnel
#   チューブ式 ami_maglev_tube_<版>（地上 4 版）・ami_maglev_tube_elev_<版>（高架 4 版）・ami_maglev_tube_cover（チューブの way-object。
#     電化しない）・ami_maglev_tube_tunnel。作りは marine_express（ユーザーのアドオン）に合わせた（2026-11-27、ユーザーの指示）
MAGLEV_GUIDEWAY = f"{PREFIX}maglev_guideway"
MAGLEV_GUIDEWAYS = tuple(f"{MAGLEV_GUIDEWAY}_{_v}" for _v in VARIANTS)
MAGLEV_GUIDEWAY_ELEVS = tuple(f"{MAGLEV_GUIDEWAY}_elev_{_v}" for _v in VARIANTS)
MAGLEV_GUIDEWAY_TUNNEL = f"{MAGLEV_GUIDEWAY}_tunnel"
MAGLEV_GUIDEWAY_TUNNEL_WAY = f"{MAGLEV_GUIDEWAY}_center"  # トンネルの中の way（側壁の無い版）
MAGLEV_GUIDE = f"{PREFIX}maglev_guide"
MAGLEV_BEAM = f"{PREFIX}maglev_beam"
MAGLEV_TUBE = f"{PREFIX}maglev_tube"
MAGLEV_TUBES = tuple(f"{MAGLEV_TUBE}_{_v}" for _v in VARIANTS)
MAGLEV_TUBE_ELEVS = tuple(f"{MAGLEV_TUBE}_elev_{_v}" for _v in VARIANTS)
MAGLEV_TUBE_TUNNEL_WAY = f"{MAGLEV_TUBE}_center"  # トンネルの中の way（側壁の無い版）
MAGLEV_TUBE_COVER = f"{MAGLEV_TUBE}_cover"
MAGLEV_BEAMS = (MAGLEV_BEAM,)  # 跨座式モノレールと同じ並び（地上 1・高架 3 版・トンネル）
MAGLEV_ELEV_VARIANTS = MONORAIL_ELEV_VARIANTS


def maglev_elev(way, variant):
    """常電導の高架の版の名前（<地上の名前>_elev_<版>）"""
    return f"{way}_elev_{variant}"


MAGLEV_BEAM_ELEVS = {_w: tuple(maglev_elev(_w, _v) for _v in MAGLEV_ELEV_VARIANTS) for _w in MAGLEV_BEAMS}
MAGLEV_TUNNELS = {MAGLEV_GUIDEWAY_TUNNEL: MAGLEV_GUIDEWAY_TUNNEL_WAY, f"{MAGLEV_BEAM}_tunnel": MAGLEV_BEAM,
                  f"{MAGLEV_TUBE}_tunnel": MAGLEV_TUBE_TUNNEL_WAY}  # トンネルの名前 → 中の way

# 運河（60 km/h、water。#114。名前は ADR 0008）。物の並びは iss の運河（地上だけ。高架・橋・トンネルは無い）に合わせる
# （2026-11-22、ユーザーの決定）。歩道（ami_sidewalk）と同じ waytype なので、突き当てるとつながる（docs/objects/canal.md の「運河の作り」）
CANAL = "ami_canal"
CANAL_SCENIC = "ami_canal_scenic"  # 景観の運河（#161）。実用の運河と同じ値（速さ 60 で #117 の跳ね橋を共用）。水面が 13px 下（iss と同じ）

# 狭軌（narrowgauge_track。#370）: iss の狭軌（../refs/iss/src/way/rail/narrow.dat の iss_wng_0030・iss_wng_0060）と同じく地上の版だけで、
# 速さ 30（木のまくらぎ・土の道床）と 60（PC まくらぎ・砕石）の 2 種。部品は在来線の物を使い回し、軌間だけを内へ寄せる（render.py の
# 「狭軌」）。waytype が線路と違い、線路の壁・架線（waytype=track の way-object）も踏切も載らないので、TRACKS に入れない（TRACKS の種類は
# 基盤・高架・橋・旧描画位置の版・踏切の名前を導く）。トンネルは 60 だけ（iss の iss_tn_0060 と同じ）。名前の頭 ami_narrow_ で build.py が ami_narrow.pak に入れる
NARROW_WOOD = "ami_narrow_wood"  # 30 km/h（軽便）
NARROW_BALLAST = "ami_narrow_ballast"  # 60 km/h
NARROWS = (NARROW_WOOD, NARROW_BALLAST)
NARROW_TUNNEL = f"{NARROW_BALLAST}_tunnel"

ROAD_LOCAL = Road("road_local", ("single",))  # 生活道路（40 km/h、中央線なし）
ROAD_GENERAL = Road("road_general", ("single",))  # 一般道路（120 km/h、中央線は白の実線）
ROAD_TRUNK = Road("road_trunk")  # 幹線道路（#257。最高速度 240 km/h（確定）、中央線は白の破線（直線 4・斜め 3 で高速道路より細かい）。4 車線は道路を 2 本並べる。カーブは高速道路と同じ斜めの直線）
ROAD_EXPRESSWAY = Road("road_expressway")  # 高速道路（360 km/h、中央線は白の広い破線。線 8m・すき間 12m の割り方。#257）
ROADS = (ROAD_LOCAL, ROAD_GENERAL, ROAD_TRUNK, ROAD_EXPRESSWAY)
# 道路のカーブの形（#259。#209 の 2 本目）: 種類 → "arc"（円弧。路面軌道と同じ）か "ell"（L 字。直角）。ここに無い種類（高速道路・幹線道路）は斜めの絵。
# 速さで描き分ける（一般は円弧、生活道路は L 字）。カーブの絵は way のシートの行 2 の列 5〜8 に描き、dat の image[sw] などがそれを指す。
# 基盤・高架の single と壁（ROAD_WALL_CURVED）も同じ形にそろえた（3 本目の #260）
ROAD_CURVE_SHAPES = {ROAD_LOCAL.key: "ell", ROAD_GENERAL.key: "arc"}
# 多車線と交差点の路面表示の way（#187。ADR 0012）: 道路に重ねて敷く tram_track の way。名前 → 種類（tools/blender/marking_kinds.py の KINDS。
# 種類の一覧・セル・アイコンの字はそこに 1 か所だけ置く。#352）。
# 一般道路（ROAD_GENERAL）に重ね、白線と路面を描く（下の道路の線と、帯・交差点の中の雪を覆う）。
# lane4 は 4 車線の直線（2 列とも）、junction2 は 2 車線の腕と中心（4 車線 × 2 車線の中心も）、
# junction2_t は 2 車線の T字路の中心、junction4_in・junction4_out は 4 車線の腕の入る側・出る側と中心（出る側の中心はスクランブル）。
# junction4_c は 4 車線どうしのふつうの中心の 4 枚（junction4_in の曲がりに、4 枚が接する角の中心の印を足した物。#313）。
# 6 車線（#189。外のタイルの直線は lane4、中心の角は junction4_in の曲がりを使う）: lane6_m は真ん中のタイルの直線、junction6_in・junction6_out は
# 腕の入る側・出る側の外の列、junction6_m は腕の真ん中の列（右折車線）、junction6_c は中心 3×3 の角を除く 5 枚（路面で覆うだけ）
MARKINGS = {f"{PREFIX}mark_{_k}": _k for _k in marking_kinds.KINDS}
# 高速道路の分岐・合流（#188）: 高速道路（ROAD_EXPRESSWAY）に重ねる。本線の列（_main）とランプの列（_ramp）。路面は高速道路のアスファルト
MARKINGS_EXPWY = {f"{PREFIX}mark_{_k}": _k for _k in marking_kinds.kinds_of("expwy")}
# 路面の色と黄色の中央線（#313。iss の util/road_misc の pav_*・line）: 一般道路に重ねる。色の舗装 3 色・赤の縞・黄色の中央線
MARKINGS_COLOR = {f"{PREFIX}mark_{_k}": _k for _k in marking_kinds.kinds_of("color")}
# 路面表示のアイコンの左上の字（icons.py が書く。#187）: marking_kinds.KINDS の label
MARK_LABELS = {_n: marking_kinds.KINDS[_k].label for _n, _k in MARKINGS.items()}
WALL_ROAD = ROAD_GENERAL  # 道路の壁のシートを描く元の道路（壁の形は 3 種で同じ。断面とカーブの作りが同じため）
# カーブの形ごとの壁（#260）: 一般道路（円弧）・生活道路（L 字）の基盤・高架は single だけなので、カーブのセルが円弧・L 字の single の壁を別に持つ。
# 名前 → 形（ROAD_CURVE_SHAPES の値）。直線・T字・十字・坂・端の壁は ami_wall_road_single と同じ絵で、カーブのセル（行 2 の列 5〜8）だけが違う。
# 幹線道路・高速道路と、橋・トンネルは ami_wall_road_single（カーブは斜め）を使う
ROAD_WALL_CURVED = {f"ami_wall_road_single_{_s}": _s for _s in ("arc", "ell")}
ROAD_WALL_VARIANTS = ("single", "back", "center", "front")  # 道路の壁の way-object の版（README の名前の表。center は行き止まりの端の壁だけ）
# 近い斜めの分け合うタイル用の道路の壁（名前は 2026-11-19 にユーザーが確定。docs/objects/road.md の「道路の壁・高架・橋脚・橋・トンネルの作り」）
ROAD_WALL_TWIN = "ami_wall_road_twin"
# 中央分離帯つきの壁（#118。ADR 0008）: 4 車線（道路を 2 タイル並べる）の手前のタイルに重ね、奥の側壁の位置に縁石の帯とガードレールを立てる。
# front_divider は手前の側壁つき、center_divider は側壁なし（行き止まりの端の壁は持つ）。奥のタイルは今の ami_wall_road_back のまま
ROAD_DIVIDERS = {_v: f"ami_wall_road_{_v}_divider" for _v in ("front", "center")}
ROAD_DIVIDER_TWIN = "ami_wall_road_twin_divider"  # 近い斜めの分け合うタイル用（西の線は back の壁、東の線は front_divider の絵）
PIER_ROAD = "ami_pier_road"  # 道路用の橋脚の way
SIDEWALK = "ami_sidewalk"  # 歩道の way（道路の隣のタイルに敷く、別の waytype の way。ADR 0003）
# 盛土の way（#123。ADR 0008 の景観 6）: 高架の脇の地面に敷く法面の楔。front は法面が手前（南・東）、back は奥（北・西）を向く
EMBANKMENT_SIDES = ("front", "back")
EMBANKMENTS = {f"{PREFIX}embankment_{_s}": _s for _s in EMBANKMENT_SIDES}
# 盛土の建物の版（#372。ADR 0018）: type=cur の 1 タイルの建物。名前 → 種類（straight = 4 辺のどれかを向く法面、corner = 台の外の角）。
# 4 向きずつ（layout 0〜3）に分けるのは、建物の layout が 8 だと地図の回転で向きが崩れるため
EMBANKMENT_BUILDINGS = {f"{PREFIX}embankment_building": "straight", f"{PREFIX}embankment_building_corner": "corner"}
# 説明用の色の way（#372。ADR 0018。手本 iss の util/describe）: 色 → sRGB 8bit（iss の画像の色）。地上は ami_describe_<色>（tram_track）、
# 高架は ami_describe_<色>_elev（track・system_type=1）で、同じシート ami_describe_<色> を使う。色はつながる向きで描き分けられないので物を分ける
DESCRIBE_COLORS = {"red": (195, 13, 35), "blue": (29, 32, 136), "green": (0, 105, 52), "yellow": (248, 182, 45)}
DESCRIBES = {f"{PREFIX}describe_{_c}{_s}": (_c, _s == "_elev") for _c in DESCRIBE_COLORS for _s in ("", "_elev")}
# 歩道の種類（#119。ADR 0008 の ami_sidewalk_<舗装>）: 舗装の名前。ami_sidewalk（灰色の敷石）は名前を変えずに残す
SIDEWALK_PAVINGS = ("asphalt", "brick", "tile")
SIDEWALK_ELEV = "ami_sidewalk_elev"  # 高架の歩道（system_type=1。敷石は ami_sidewalk と同じ）
SIDEWALK_WALL_VARIANTS = ("single", "back", "front")  # 歩道の柵（way-object）の版。center は柵が無くなるので作らない


def sidewalk(paving):
    """歩道の種類の名前（ami_sidewalk_<舗装>）"""
    return f"{SIDEWALK}_{paving}"


def sidewalk_wall(variant):
    """歩道の柵の way-object の名前（ami_wall_sidewalk_<版>。build.py の ami_wall_ で付属の pak に入る）"""
    return f"{PREFIX}wall_sidewalk_{variant}"


# 歩道の way の全部（地上の種類と高架）。dat・シート・アイコンの決まりは同じ
SIDEWALKS = (SIDEWALK,) + tuple(sidewalk(_p) for _p in SIDEWALK_PAVINGS) + (SIDEWALK_ELEV,)
SIDEWALK_WALLS = tuple(sidewalk_wall(_v) for _v in SIDEWALK_WALL_VARIANTS)
# 電柱（#120。ADR 0008 の ami_sidewalk_pole）: 歩道の way-object。柱はタイルのわき（back は北西、front は南東）に立てる。
# 柵の無い ami_sidewalk_pole_<版> と、柵の版に電柱を足した ami_wall_sidewalk_<版>_pole（1 タイルに water の way-object は 1 つだけなので、
# まとめた物にする）。タイルの中心に立てる版（ami_sidewalk_pole・ami_wall_sidewalk_single_pole）は作らない（歩道の中央に電柱は立たない。
# 2026-11-22、ユーザーの指定で進捗管理が決めた）。名前 → (柱を寄せる版, 柵があるか)
SIDEWALK_POLE_VARIANTS = ("back", "front")
SIDEWALK_POLES = {
    **{f"{SIDEWALK}_pole_{_v}": (_v, False) for _v in SIDEWALK_POLE_VARIANTS},
    **{f"{sidewalk_wall(_v)}_pole": (_v, True) for _v in SIDEWALK_POLE_VARIANTS},
}


def crossing(track, road):
    """線路 × 道路の踏切の名前（#111。ami_crossing_<線路>_<道路>。例 ami_crossing_rail_ballast_road_general）"""
    return f"{PREFIX}crossing_{track.key}_{road.key}"


def crossing_sheet(road):
    """踏切のシートの名前。絵は道路の種類ごとに 1 枚で、線路の 4 種で同じ（踏切の中は道床が見えない。2026-11-21、#111 で進捗管理が決定）"""
    return f"{PREFIX}crossing_{road.key}"


CROSSINGS = {crossing(_t, _r): (_t, _r) for _t in TRACKS for _r in ROADS}  # 踏切の名前 → (線路, 道路)。16 個


# 水路の踏切（#117。ADR 0008 の軌道 6）: 線路 4 種・道路 3 種 × 運河の 7 個。跳ね橋（2026-11-22、ユーザーの決定。#117 のコメント）。
# 名前は ami_crossing_<線路|道路>_canal（例 ami_crossing_rail_ballast_canal）。絵は道路の種類ごとに 1 枚と、線路の 4 種で共通の 1 枚
CANAL_CROSSING_RAIL_SHEET = f"{PREFIX}crossing_canal_rail"


def canal_crossing(way):
    """水路の踏切の名前（way は Track か Road）"""
    return f"{PREFIX}crossing_{way.key}_canal"


def canal_crossing_sheet(way):
    """水路の踏切のシートの名前（道路は種類ごと、線路は 4 種で共通）"""
    return f"{PREFIX}crossing_canal_{way.key}" if isinstance(way, Road) else CANAL_CROSSING_RAIL_SHEET


CANAL_ROADS = tuple(_r for _r in ROADS if _r is not ROAD_TRUNK)  # 水路の踏切を作る道路（幹線道路の版は #257 の範囲外）
CANAL_CROSSINGS = {canal_crossing(_w): _w for _w in TRACKS + CANAL_ROADS}  # 水路の踏切の名前 → 線路か道路。7 個


class Depot:
    """車庫（building の depot。#112）。名前は ami_<種類>_depot（ADR 0008）で、build.py の名前の頭の振り分けでその waytype の pak に入る。
    kind は sheetlib の depot.DEPOT_SHAPES のキー（寸法）、waytype は dat の waytype"""

    def __init__(self, kind, waytype):
        self.kind, self.waytype = kind, waytype
        self.name = f"{PREFIX}{kind}_depot"


DEPOTS = (Depot("rail", "track"), Depot("tram", "tram_track"), Depot("road", "road"), Depot("monorail", "monorail_track"),
          Depot("canal", "water"), Depot("maglev", "maglev_track"),  # リニア（#371）
          Depot("narrow", "narrowgauge_track"))  # 狭軌（#370）

# 操車場（building の stop。#115。ADR 0008 の ami_rail_yard）: 荷を扱わない線路の駅の建物。線路の脇の構内通路（2026-11-22、ユーザーの決定）。
# 名前の頭 ami_rail_ で、build.py が線路の pak（ami_rail.pak）に入れる
RAIL_YARD = f"{PREFIX}rail_yard"

# 転車台・遷車台（#314）: iss の転車台とトラバーサー（../refs/iss/src/util/rail_misc/table.dat）と同じく、道路（waytype=road）の way 1 つ。
# 1 タイルで転車台、直線に敷くと遷車台。線路の 4 種で共通（桁・台車の上の線路は線路の基準面にそろえる）。名前の頭 ami_rail_ で線路の pak に入る
RAIL_TURNTABLE = f"{PREFIX}rail_turntable"


# 道路標識（roadsign。#122）。名前は ami_sign_<名前>（ADR 0008）で、build.py の振り分けで ami_scenery.pak に入る。
# 値は 6 種（2026-11-21、ユーザーの決定。#122 の案 A）。キーは sheetlib の roadsign.ROADSIGN_PLATES のキー（板の絵）
ROADSIGN_KEYS = ("one_way", "stop", "speed_40", "speed_60", "speed_80", "min_50")
ROADSIGNS = {f"{PREFIX}sign_{_k}": _k for _k in ROADSIGN_KEYS}
# 路面の横断歩道（#162）: 柱の無い路面の標示。両方向と一方通行（single_way は物ごとの設定で、1 マスに標識は 1 つしか置けないので分ける）
ROADSIGN_CROSSWALKS = {f"{PREFIX}sign_crosswalk": False, f"{PREFIX}sign_crosswalk_one_way": True}  # 名前 → 一方通行か
# カーブを斜めの絵で表すシート（pak128 標準の線路と同じ。dat の image[sw]・[nw]・[ne]・[se] が diagonal と同じセルを指す）。
# 唯一の定義。dat を書く ami_dat.py（DIAG_CURVES）と、判定・比較の道具が読む addon_config.py（DIAG_CURVE_SHEETS）がここから引く（#227。別々に書いて片方を直し忘れた）
# 基盤の版・高架の版（線路・道路）はカーブを斜めの形の別のセル（基盤の壁の無い側を削らない）に描くので、ここには入れない。render.py の diag_curves と同じにする
DIAG_CURVE_WAYS = {_t.way for _t in ALL_TRACKS} | {_r.way for _r in ROADS if _r.key not in ROAD_CURVE_SHAPES}  # 高速道路・幹線道路もカーブは斜めの絵（一般道路は円弧、生活道路は L 字。#259。docs/objects/road.md の「道路の作り」）
DIAG_CURVE_WAYS |= {MONORAIL, *MONORAIL_ELEVS}  # 跨座式モノレールは高架の版もカーブを斜めの絵（#113。手本の iss の跨座式の dat と同じ）
DIAG_CURVE_WAYS.add(CANAL)  # 運河もカーブは斜めの絵（#114）
DIAG_CURVE_WAYS |= {*MONORAIL_SUSPENDEDS, *MONORAIL_SUSPENDED_ELEVS}  # 懸垂式（#116）も跨座式と同じ
# リニアの常電導（#371）も跨座式と同じ（iss の dat と同じ）。超電導・チューブ式は線路の基盤の版と同じくカーブのセルを斜めの形で描く
DIAG_CURVE_WAYS |= {_n for _w in MAGLEV_BEAMS for _n in (_w, *MAGLEV_BEAM_ELEVS[_w])}
DIAG_CURVE_WAYS |= set(NARROWS)  # 狭軌（#370）も線路と同じく斜めの絵（iss の narrow.dat も image[sw] などが斜めと別のセルだが、AMI の線路にそろえる）


# ---------------------------------------------------------------- way の絵の並びの性質（#242）
# 唯一の定義。dat を書く ami_dat.py と、判定・比較の道具が読む addon_config.py がここから引く（別々に書いて片方を直し忘れた。#227・#242）。
# 絵を作った way（dat と pak を作る。名前 = シート名）の並び。まだ絵を作っていない way は入れない
BUILT_WAYS = []
NO_CLOSE_WAYS = set()  # 近い斜めの絵を持たない way
ELEVATED_WAYS = set()  # 高架（system_type=1）の way
FRONT_WAYS = set()  # 手前の絵（frontimage）を持つ way。シートは 奥の絵 4 行 → 手前の絵 4 行 → 雪の奥 4 行 → 雪の手前 4 行（懸垂式の柱・梁）
for _t in ALL_TRACKS:
    BUILT_WAYS.append(_t.way)
    BUILT_WAYS += [_t.base(_v) for _v in VARIANTS]  # 基盤の版（カーブは斜めの形の別のセル。近い斜め無し）
    NO_CLOSE_WAYS.update(_t.base(_v) for _v in VARIANTS)
BUILT_WAYS.append(TRAM)  # 路面軌道（通常の版だけ）
for _r in ROADS:
    BUILT_WAYS.append(_r.way)
for _r in ROADS:
    BUILT_WAYS += [_r.base(_v) for _v in _r.variants]  # 道路の地上の基盤の版（線路と同じ並び）
    NO_CLOSE_WAYS.update(_r.base(_v) for _v in _r.variants)
for _t in ALL_TRACKS:
    BUILT_WAYS += [_t.elev(_v) for _v in VARIANTS]  # 高架の 4 版
    NO_CLOSE_WAYS.update(_t.elev(_v) for _v in VARIANTS)
    ELEVATED_WAYS.update(_t.elev(_v) for _v in VARIANTS)
for _r in ROADS:
    BUILT_WAYS += [_r.elev(_v) for _v in _r.variants]
    NO_CLOSE_WAYS.update(_r.elev(_v) for _v in _r.variants)
    ELEVATED_WAYS.update(_r.elev(_v) for _v in _r.variants)
BUILT_WAYS += [MONORAIL, *MONORAIL_ELEVS]  # 跨座式（近い斜め無し。高架は system_type=1）
NO_CLOSE_WAYS.update((MONORAIL, *MONORAIL_ELEVS))
ELEVATED_WAYS.update(MONORAIL_ELEVS)
for _v in MONORAIL_SUSPENDED_VARIANTS:  # 懸垂式（#116）: 並びは跨座式と同じで、柱・梁は手前の絵
    for _elev in (False, True):
        _n = monorail_suspended(_v, _elev)
        BUILT_WAYS.append(_n)
        NO_CLOSE_WAYS.add(_n)
        FRONT_WAYS.add(_n)
        if _elev:
            ELEVATED_WAYS.add(_n)
BUILT_WAYS += [CANAL, CANAL_SCENIC]  # 運河（近い斜めの絵は持つ）
# リニア（#371）: どれも近い斜めの絵を持たない。超電導は防音壁を way の絵に焼き込み、手前の側の壁を手前の絵に描く。
# チューブ式も超電導と同じく側壁を way の絵に焼き込む（チューブは way-object）
for _n in MAGLEV_GUIDEWAYS + MAGLEV_GUIDEWAY_ELEVS + MAGLEV_TUBES + MAGLEV_TUBE_ELEVS:
    BUILT_WAYS.append(_n)
    NO_CLOSE_WAYS.add(_n)
    FRONT_WAYS.add(_n)
ELEVATED_WAYS.update(MAGLEV_GUIDEWAY_ELEVS + MAGLEV_TUBE_ELEVS)
for _w in MAGLEV_BEAMS:
    BUILT_WAYS += [_w, *MAGLEV_BEAM_ELEVS[_w]]
    NO_CLOSE_WAYS.update((_w, *MAGLEV_BEAM_ELEVS[_w]))
    ELEVATED_WAYS.update(MAGLEV_BEAM_ELEVS[_w])
BUILT_WAYS += list(NARROWS)  # 狭軌（#370。線路の通常の版と同じく近い斜めの絵を持つ）
BUILT_WAYS = tuple(BUILT_WAYS)
NO_CLOSE_WAYS = frozenset(NO_CLOSE_WAYS)  # 書き換えられないようにする（ami_dat.py などが別名で持つ）
ELEVATED_WAYS = frozenset(ELEVATED_WAYS)
FRONT_WAYS = frozenset(FRONT_WAYS)

# pak128 以外の大きさ（sheet_settings.PAK_SIZE が 128 でない。#261・#266）の、描き・組む物（#301 で、組む物の表から組まない物の表に裏返した）。
# 既定は、pak128 の絵（src/<名前>.png）か dat（src/<名前>.dat）がある物は全部 256 でも描き・組む。物を足したときに、ここへ書き足さなくてよい。
# 256 の絵が合わない物（画素で書いた値を大きさに合わせていない物など）だけを SCALED_EXCLUDED に「名前: 理由」で書く（今は無い）。
# 分岐の追加画像の提供用の dat（ex_donors）は物ではなく、ami_dat.py が別に書く。物を入れるときは、その物を指す dat（ex_donors・twin の壁・踏切）が 256 に残らないかも確かめる
SCALED_EXCLUDED = {}


def _src_names(ext):
    """pak128 の src/ にある、拡張子 ext のファイルの名前（拡張子なし）。src/ は blender/ の隣"""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "src")
    return sorted(os.path.splitext(_f)[0] for _f in os.listdir(src) if _f.endswith(ext) and _f.startswith(PREFIX))


# render.py の描く対象（SHEETS のキー）でない絵: 壁の単独の名前（基盤の版を描くと一緒に書かれる）
SCALED_WALL_SINGLES = tuple(wall_rail(_v, _old) for _old in (False, True) for _v in VARIANTS)
# 256 で描く対象 = pak128 の絵のある物 − 壁の単独の名前 − 組まない物。render.py が対象を渡されないときに描く物で、pak256 の build_ami256.py も読む。
# 並びは名前順。render.py は、これが自分の SHEETS のキーであることを描く前に確かめる
SCALED_TARGETS = tuple(_n for _n in _src_names(".png") if _n not in SCALED_WALL_SINGLES and _n not in SCALED_EXCLUDED)
# 踏切のシート（道路の種類ごとと、線路で共通の水路のもの）。dat を持たず、踏切の dat が指す。pak256 の build_ami256.py が 2 回目に描く物として読む
SCALED_CROSSING_SHEETS = (tuple(crossing_sheet(_r) for _r in ROADS) + tuple(canal_crossing_sheet(_w) for _w in CANAL_ROADS)
                          + (CANAL_CROSSING_RAIL_SHEET,))
