"""blender-poc のシートの入口。アドオンのディレクトリで Blender から動かす:

    blender -b --factory-startup --python blender/render.py [-- 対象名 ...]

描画の道具は tools/blender/sheetlib.py。ここには blender-poc のシートの設定（描き分け・シート名・料金所）だけを置く
（共通とアドオンの設定の分け方は tools/README.md）。

出力:
    src/track.png      線路・新描画位置（iss に合わせる）。src/track_old.png は旧描画位置（SIS に合わせる）
    src/road.png       道路（歩道付き。幅は SIS の一般道に合わせる）
    src/expressway.png 高速道路（歩道なし。SIS の高速道路に合わせる）
    src/tollbooth.png  料金所風の建物（屋根がタイルからはみ出す）
    work/              セルごとの生の描画結果（確認用）
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "blender"))
import sheetlib as R  # noqa: E402

# ---------------------------------------------------------------- 道路の描き分け

# 道路の描き分け（R.ROAD_PROFILES）: skin は部品の材質の差し替え（高速道路のアスファルト）、groups は使う部品のまとまり。
# walls は側壁の版（both = single・back・center・front。線路の TRACK_PROFILES と同じ決め方）
R.ROAD_PROFILES.update({
    "street": {"sheet": "road", "prefix": "road_", "groups": ("body", "sidewalk", "marking", "weathering"), "skin": {},
               "label": "50", "style": "road"},
    "expressway": {"sheet": "expressway", "prefix": "expwy_", "groups": ("body", "marking", "weathering"),
                   "skin": dict({"asphalt": R._M_EXPWY_ASPHALT},
                                **{f"wear{i}": R._wear_material("expwy", (0.0027, 0.0027, 0.004), (0.016, 0.016, 0.023), t, 0.0)
                                   for i, (_, t, _) in enumerate(R.WEAR_LAYERS)},
                                **{n: R._slush_material("expwy", (0.0027, 0.0027, 0.004), (0.016, 0.016, 0.023), t, 0.0)
                                   for n, _, t, _, _ in R.SNOW_LAYERS if t is not None}),
                   "expressway": True, "label": "120", "style": "expressway"},
})
for _variant, _walls in (("single", "both"), ("back", "back"), ("center", "center"), ("front", "front")):
    R.ROAD_PROFILES[f"expwy_wall_{_variant}"] = dict(R.ROAD_PROFILES["expressway"], sheet=f"expressway_wall_{_variant}",
                                                   prefix=f"expwy_wall_{_variant}_", walls=_walls, front_row=4,
                                                   groups=R.ROAD_PROFILES["expressway"]["groups"] + ("wall",))
    # 高架（system_type=1）: 側壁の版に、床の下の基盤（build_base）と橋脚を足す。橋脚は床の下から ELEV_STEPS 段下の地面まで（lower 行下まで描く）
    R.ROAD_PROFILES[f"expwy_elev_{_variant}"] = dict(R.ROAD_PROFILES[f"expwy_wall_{_variant}"], sheet=f"expressway_elev_{_variant}",
                                                   prefix=f"expwy_elev_{_variant}_", elevated=True, lower=R.ELEV_LOWER, band="elevated",
                                                   groups=R.ROAD_PROFILES[f"expwy_wall_{_variant}"]["groups"] + ("pier",))
# 橋: 両側の壁（欄干）の版に、青い桁（基盤）・端の坂と橋台の躯体・橋脚の絵を足す。セルの並びは線路の橋と同じ
R.ROAD_PROFILES["expwy_bridge"] = dict(R.ROAD_PROFILES["expwy_wall_single"], sheet="expressway_bridge", prefix="expwy_bridge_",
                                     bridge=True, solid=True, band="bridge", base_mat=R._M_GIRDER, piers=True, starts=True,
                                     groups=R.ROAD_PROFILES["expwy_wall_single"]["groups"] + ("ramp",),
                                     only=("ns", "ew", "up12", "up9", "up3", "up6", "up2_12", "up2_9", "up2_3", "up2_6"))

# ---------------------------------------------------------------- 線路の描き分け

# 線路の描画位置。形状は同じで、画面上の上下位置だけを整数 px ずらす（正: 下へ）
#   new: 新描画位置（レールが低い。今の pak128・iss）
#   old: 旧描画位置（レールが高い。古い pak128・SIS）
# iss と SIS を比べると、どの方位でもレールが画面上で 4〜4.5px 違うだけだった
R.TRACK_PROFILES.update({
    "new": {"sheet": "track", "spill": 1, "datums": {"bed": R.Datum(2, 1), "rail": R.Datum(4, 1)}, "snow": True,
            "groups": ("body", "weathering")},
    "old": {"sheet": "track_old", "spill": 0, "datums": R.FLAT, "snow": True, "groups": ("body", "weathering")},
    # 試作: 新に、車止め・汚れ・雪の絵を足したもの（車止めを試す別のアドオン）
    "trial": {"sheet": "track_trial", "spill": 1, "datums": {"bed": R.Datum(2, 1), "rail": R.Datum(4, 1)},
              "groups": ("body", "structure", "weathering"), "snow": True},
    # 試作: 新に側壁を足したもの。カメラに近い側の壁は手前の絵（frontimage。下の 4 行に同じ並び）
    # 試作: 橋（obj=bridge）。直線と坂（橋の端）だけを描き、床版・側壁（欄干）を足す。橋脚は別のセル
    "bridge": {"sheet": "track_bridge", "spill": 1, "datums": {"bed": R.Datum(2, 1), "rail": R.Datum(4, 1)},
               "groups": ("body", "wall", "base", "ramp", "weathering"), "front_row": 4, "snow": True, "solid": True, "band": "bridge",
               "only": ("ns", "ew", "up12", "up9", "up3", "up6", "up2_12", "up2_9", "up2_3", "up2_6"), "piers": True,
               "starts": True},
    "wall_single": {"sheet": "track_wall_single", "spill": 1, "datums": {"bed": R.Datum(2, 1), "rail": R.Datum(4, 1)},
                    "groups": ("body", "wall", "base", "structure", "weathering"), "front_row": 4, "snow": True, "walls": "both"},
})
# 側壁と基盤のバリエーション: 両側（単線用）・back（奥だけ）・center（壁なし。中線）・front（手前だけ）。
# 基盤は、壁のある側は壁まで、壁のない側はタイルの端まで
for _variant in ("back", "center", "front"):
    R.TRACK_PROFILES[f"wall_{_variant}"] = dict(R.TRACK_PROFILES["wall_single"], sheet=f"track_wall_{_variant}", walls=_variant)
# 高架（dat の system_type=1）: 側壁の 4 つの版に橋脚を足し、持ち分を床の ELEV_STEPS 段（16px × 段数）下まで広げる
for _variant, _walls in (("single", "both"), ("back", "back"), ("center", "center"), ("front", "front")):
    R.TRACK_PROFILES[f"elev_{_variant}"] = dict(R.TRACK_PROFILES["wall_single"], sheet=f"track_elev_{_variant}", walls=_walls,
                                               groups=("body", "wall", "base", "structure", "pier", "weathering"), lower=R.ELEV_LOWER,
                                               band="elevated")
# 試作: ex 画像（Y字・三方分岐）が使えたらどう見えるかを、switch 画像の 1・2 の枠に入れて見る（別のアドオン。雪なし）
R.TRACK_PROFILES["ex_proto"] = dict(R.TRACK_PROFILES["new"], sheet="track_ex_proto", ex_proto=True, snow=False)
R.TRACK_PROFILES["ex_proto2"] = dict(R.TRACK_PROFILES["ex_proto"], sheet="track_ex_proto2", ex_proto="crossover")

# ---------------------------------------------------------------- 料金所

def build_tollbooth(rot_deg):
    """料金所風の建物。屋根は 13x6.5 でタイル(10x10)からはみ出す。"""
    m_conc = R.material("concrete", (0.66, 0.65, 0.62))
    m_white = R.material("booth", (0.86, 0.87, 0.88), rough=0.5)
    # 特殊色: 屋根の帯はプレーヤーカラー、窓は夜に光る窓、屋根の下に照明、ブースの上に赤と緑のランプ
    m_glass = R.material("glass", (0.25, 0.38, 0.48), rough=0.15, special="window_dark")
    m_roof = R.material("roof", (0.80, 0.81, 0.83), rough=0.6)
    m_band = R.material("band", (0.35, 0.35, 0.35), special="player1")
    m_road = R.material("asphalt", (0.28, 0.28, 0.30))
    m_lamp = R.material("lamp", (1.0, 1.0, 0.6), emit=1.0, special="light_yellow")
    m_red = R.material("lamp_red", (1.0, 0.1, 0.1), emit=1.0, special="light_red")
    m_green = R.material("lamp_green", (0.0, 0.8, 0.0), emit=1.0, special="light_green")

    parts = {
        "road": (m_road, [R.box(0, 0, 0.05, 10, 10, 0.1)]),
        "island": (m_conc, [R.box(0, 0, 0.3, 1.4, 8.0, 0.5)]),
        "booth": (m_white, [R.box(0, 0.6, 1.8, 1.1, 2.2, 2.5)]),
        "glass": (m_glass, [R.box(0, 0.6, 2.2, 1.16, 1.6, 1.0)]),
        "pillars": (m_white, [R.box(0, -2.4, 3.0, 0.5, 0.5, 5.0), R.box(0, 3.4, 3.0, 0.5, 0.5, 5.0)]),
        "roof": (m_roof, [R.box(0, 0.5, 5.75, 13.0, 6.5, 0.7)]),
        "band": (m_band, [R.box(0, 0.5, 5.75, 13.06, 6.56, 0.28)]),
        # 安全島の両端に照明灯（柱と光る頭）
        "lamp_posts": (m_white, [R.box(0, y, 1.2, 0.15, 0.15, 1.8) for y in (-3.7, 3.7)]),
        "lamps": (m_lamp, [R.box(0, y, 2.25, 0.4, 0.4, 0.3) for y in (-3.7, 3.7)]),
        # 左の車線は赤（閉鎖）、右の車線は緑（開放）。ブース上の柱の両脇に向ける
        "lamp_red": (m_red, [R.box(-0.6, -2.4, 4.6, 0.2, 0.5, 0.5)]),
        "lamp_green": (m_green, [R.box(0.6, -2.4, 4.6, 0.2, 0.5, 0.5)]),
    }
    obs = [R.mesh_object(name, *R.merge(geo), mat) for name, (mat, geo) in parts.items()]
    for ob in obs:
        ob.rotation_euler.z = math.radians(rot_deg)
    return obs


def tollbooth_sheet():
    R.set_anchor(192)  # dat オフセット -64,-96 と対応（上に160px の余白）
    cells = {}
    for i, rot in enumerate((0, 90, 180, 270)):
        R.clear_models()
        build_tollbooth(rot)
        cells[(0, i)] = R.render_cell(f"tollbooth_r{i}")
    R.clear_models()
    build_tollbooth(0)
    cells[(0, 4)] = R.render_icon("tollbooth_icon", 1.25, shift=(0.0, 0.2))
    cells[(0, 5)] = cells[(0, 0)]  # カーソルは向き0と同じ絵
    R.make_sheet(cells, 1, 6, R.sheet_path("tollbooth.png"))

# ---------------------------------------------------------------- 対象（シート名 → 描く関数）

SHEETS = {
    "track": lambda: R.track_sheet("new"),
    "track_old": lambda: R.track_sheet("old"),
    "track_trial": lambda: R.track_sheet("trial"),
    "track_ex_proto": lambda: R.track_sheet("ex_proto"),
    "track_ex_proto2": lambda: R.track_sheet("ex_proto2"),
    "track_bridge": lambda: R.track_sheet("bridge"),
}
for _variant in ("single", "back", "center", "front"):
    SHEETS[f"track_wall_{_variant}"] = lambda v=_variant: R.track_sheet(f"wall_{v}")
    SHEETS[f"track_elev_{_variant}"] = lambda v=_variant: R.track_sheet(f"elev_{v}")
SHEETS["track_tunnel"] = R.tunnel_sheet
SHEETS["icons"] = R.icon_gallery
SHEETS["road"] = lambda: R.road_sheet()
SHEETS["expressway"] = lambda: R.road_sheet("expressway")
for _variant in ("single", "back", "center", "front"):
    SHEETS[f"expressway_wall_{_variant}"] = lambda v=_variant: R.road_sheet(f"expwy_wall_{v}")
    SHEETS[f"expressway_elev_{_variant}"] = lambda v=_variant: R.road_sheet(f"expwy_elev_{v}")
SHEETS["expressway_bridge"] = lambda: R.road_sheet("expwy_bridge")
SHEETS["expressway_tunnel"] = lambda: R.tunnel_sheet("expressway")
SHEETS["tollbooth"] = tollbooth_sheet

if __name__ == "__main__":
    R.run_targets(SHEETS, ["track", "track_old", "road", "expressway", "tollbooth"])
