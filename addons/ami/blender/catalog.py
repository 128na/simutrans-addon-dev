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
    今は通常の版の way だけ（高架・橋・トンネルは #22 で足す）"""
    key: str

    @property
    def way(self):
        return PREFIX + self.key


RAIL_BALLAST = Track("rail_ballast")  # 在来線（バラスト軌道）
RAIL_SLAB = Track("rail_slab")  # 高速線（スラブ軌道）
TRACKS = (RAIL_BALLAST, RAIL_SLAB)
WALL_TRACK = RAIL_BALLAST  # 共有の壁・架線のシートを描く元の軌道（ほかの種類の基盤の版は、壁のシートを書かない）

ROAD_LOCAL = Road("road_local")  # 生活道路（40 km/h、中央線なし）
ROAD_GENERAL = Road("road_general")  # 一般道路（120 km/h、中央線は白の実線）
ROAD_EXPRESSWAY = Road("road_expressway")  # 高速道路（360 km/h、中央線は白の破線）
ROADS = (ROAD_LOCAL, ROAD_GENERAL, ROAD_EXPRESSWAY)
