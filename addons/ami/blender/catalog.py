"""AMI の軌道の種類の表（Blender を使わない）。blender/render.py・ami_dat.py・addon_config.py が、ここから名前を展開する。

軌道の種類を足すときは TRACKS に 1 件足し、render.py の TRACK_SETTINGS に描き分けを足す（値は ami_dat.py の VALUES）。
共有の壁・架線・橋脚（ami_wall_rail_*・ami_pier_rail*）は軌道の種類に属さないので、ここには持たない。
道路の種類は ROADS に足し、render.py の ROAD_SETTINGS に描き分けを足す（線路の Track と同じ考え方）。
"""
from dataclasses import dataclass

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
    README の「道路の壁・高架・橋脚・橋・トンネルの作り」）"""
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

    def lane(self, n):
        """路面表示の版（#121）の名前（ami_road_<種類>_lane<n>）"""
        return f"{self.way}_lane{n}"


RAIL_BALLAST = Track("rail_ballast")  # 在来線（バラスト軌道）
RAIL_SLAB = Track("rail_slab")  # 高速線（スラブ軌道）
RAIL_CONCRETE = Track("rail_concrete")  # 弾性まくらぎ直結軌道（240 km/h。#62）
RAIL_LADDER = Track("rail_ladder")  # フローティング・ラダー軌道（360 km/h。#67）
TRACKS = (RAIL_BALLAST, RAIL_CONCRETE, RAIL_LADDER, RAIL_SLAB)
WALL_TRACK = RAIL_BALLAST  # 共有の壁・架線のシートを描く元の軌道（ほかの種類の基盤の版は、壁のシートを書かない）

# 路面軌道（60 km/h、tram で道路に重ねる。ADR 0002）。通常の版だけ（壁・基盤・高架・橋・トンネルを作らない）ので、TRACKS に入れない
# （TRACKS の種類は基盤・高架・橋・トンネルの名前を導き、カーブを斜めの絵にする。路面軌道のカーブは曲線のまま。README の「残っていること」）
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

# 運河（60 km/h、water。#114。名前は ADR 0008）。物の並びは iss の運河（地上だけ。高架・橋・トンネルは無い）に合わせる
# （2026-11-22、ユーザーの決定）。歩道（ami_sidewalk）と同じ waytype なので、突き当てるとつながる（README の「運河の作り」）
CANAL = "ami_canal"

ROAD_LOCAL = Road("road_local")  # 生活道路（40 km/h、中央線なし）
ROAD_GENERAL = Road("road_general")  # 一般道路（120 km/h、中央線は白の実線）
ROAD_EXPRESSWAY = Road("road_expressway")  # 高速道路（360 km/h、中央線は白の破線）
ROADS = (ROAD_LOCAL, ROAD_GENERAL, ROAD_EXPRESSWAY)
# 路面表示の版（ami_road_<種類>_lane<n>。#121。2026-11-21、ユーザーの決定）: 地上の通常の版の白線を、並べて敷いた多車線の線に替えた way。
# n → (奥の境, 真ん中, 手前の境) の線。edge は今の路側線、center は中央線（実線）、lane は車線の境（破線）。境の線はタイルの辺で、隣と半分ずつ描く。
# 生活道路は中央線が無く、多車線にしないので作らない
LANE_ROADS = (ROAD_GENERAL, ROAD_EXPRESSWAY)
LANES = {
    1: ("edge", "lane", "center"),  # 4 車線の奥
    2: ("center", "lane", "edge"),  # 4 車線の手前
    3: ("edge", "lane", "lane"),    # 6・8 車線の奥
    4: ("lane", "center", "lane"),  # 6 車線の真ん中
    5: ("lane", "lane", "edge"),    # 6・8 車線の手前
    6: ("lane", "lane", "center"),  # 8 車線の内側の奥
    7: ("center", "lane", "lane"),  # 8 車線の内側の手前
}
WALL_ROAD = ROAD_GENERAL  # 道路の壁のシートを描く元の道路（壁の形は 3 種で同じ。断面とカーブの作りが同じため）
ROAD_WALL_VARIANTS = ("single", "back", "center", "front")  # 道路の壁の way-object の版（README の名前の表。center は行き止まりの端の壁だけ）
# 近い斜めの分け合うタイル用の道路の壁（名前は 2026-11-19 にユーザーが確定。README の「道路の壁・高架・橋脚・橋・トンネルの作り」）
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
# 交差点の路面表示の way（#156。ADR 0011）: 道路に重ねて敷く tram_track の way。名前 → 種類（sheetlib の marking の MARKING_KINDS）。
# stop は 2 車線の道路の口、taper は 2 車線の導流帯、stop_wide は 4 車線の入る側（導流帯と口）、crosswalk_wide は 4 車線の出る側
# （横断歩道だけ）、branch は 4 車線の口の向きを決める枝（絵は無い）
MARKINGS = {f"{PREFIX}mark_{_k}": _k for _k in ("stop", "taper", "stop_wide", "crosswalk_wide", "branch")}
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


CROSSINGS = {crossing(_t, _r): (_t, _r) for _t in TRACKS for _r in ROADS}  # 踏切の名前 → (線路, 道路)。12 個


class Depot:
    """車庫（building の depot。#112）。名前は ami_<種類>_depot（ADR 0008）で、build.py の名前の頭の振り分けでその waytype の pak に入る。
    kind は sheetlib の depot.DEPOT_SHAPES のキー（寸法）、waytype は dat の waytype"""

    def __init__(self, kind, waytype):
        self.kind, self.waytype = kind, waytype
        self.name = f"{PREFIX}{kind}_depot"


DEPOTS = (Depot("rail", "track"), Depot("tram", "tram_track"), Depot("road", "road"), Depot("monorail", "monorail_track"),
          Depot("canal", "water"))

# 操車場（building の stop。#115。ADR 0008 の ami_rail_yard）: 荷を扱わない線路の駅の建物。線路の脇の構内通路（2026-11-22、ユーザーの決定）。
# 名前の頭 ami_rail_ で、build.py が線路の pak（ami_rail.pak）に入れる
RAIL_YARD = f"{PREFIX}rail_yard"


# 道路標識（roadsign。#122）。名前は ami_sign_<名前>（ADR 0008）で、build.py の振り分けで ami_scenery.pak に入る。
# 値は 6 種（2026-11-21、ユーザーの決定。#122 の案 A）。キーは sheetlib の roadsign.ROADSIGN_PLATES のキー（板の絵）
ROADSIGN_KEYS = ("one_way", "stop", "speed_40", "speed_60", "speed_80", "min_50")
ROADSIGNS = {f"{PREFIX}sign_{_k}": _k for _k in ROADSIGN_KEYS}
