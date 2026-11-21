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


RAIL_BALLAST = Track("rail_ballast")  # 在来線（バラスト軌道）
RAIL_SLAB = Track("rail_slab")  # 高速線（スラブ軌道）
RAIL_CONCRETE = Track("rail_concrete")  # 弾性まくらぎ直結軌道（240 km/h。#62）
RAIL_LADDER = Track("rail_ladder")  # フローティング・ラダー軌道（360 km/h。#67）
TRACKS = (RAIL_BALLAST, RAIL_CONCRETE, RAIL_LADDER, RAIL_SLAB)
WALL_TRACK = RAIL_BALLAST  # 共有の壁・架線のシートを描く元の軌道（ほかの種類の基盤の版は、壁のシートを書かない）

# 路面軌道（60 km/h、tram で道路に重ねる。ADR 0002）。通常の版だけ（壁・基盤・高架・橋・トンネルを作らない）ので、TRACKS に入れない
# （TRACKS の種類は基盤・高架・橋・トンネルの名前を導き、カーブを斜めの絵にする。路面軌道のカーブは曲線のまま。README の「残っていること」）
TRAM = "ami_tram"

ROAD_LOCAL = Road("road_local")  # 生活道路（40 km/h、中央線なし）
ROAD_GENERAL = Road("road_general")  # 一般道路（120 km/h、中央線は白の実線）
ROAD_EXPRESSWAY = Road("road_expressway")  # 高速道路（360 km/h、中央線は白の破線）
ROADS = (ROAD_LOCAL, ROAD_GENERAL, ROAD_EXPRESSWAY)
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


DEPOTS = (Depot("rail", "track"), Depot("tram", "tram_track"), Depot("road", "road"))
