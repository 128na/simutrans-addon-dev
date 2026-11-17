"""AMI のシートの入口。アドオンのディレクトリで Blender から動かす:

    blender -b --factory-startup --python blender/render.py [-- 対象名 ...]

描画の道具は tools/blender/sheetlib/。ここには AMI のシートの設定（描き分け・シート名）だけを置く
（共通とアドオンの設定の分け方は tools/README.md）。dat は blender/ami_dat.py、pak は build.py。

出力:
    src/ami_rail_ballast.png  在来線（バラスト軌道）の通常の版。形は blender-poc の線路と同じで、夏の道床を砕石のまだらにした
    src/ami_rail_ballast_base_<版>.png  基盤の版（single・back・center・front）の way。基盤は壁の位置で止まる
    src/ami_wall_rail_<版>.png  壁の way-object（4 版。center は行き止まりの端の壁だけ）。上 4 行が奥（back）、下 4 行が手前（front）の絵
    src/ami_wall_rail_<版>_catenary.png  架線つきの壁の way-object（4 版。center は架線と行き止まりの端の壁だけ）。行の並びは壁と同じ
    work/                     セルごとの生の描画結果（確認用）
"""
import dataclasses
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tools", "blender"))
import sheetlib as R  # noqa: E402

# ---------------------------------------------------------------- 線路の描き分け
# 新描画位置（レールが低い。今の pak128・iss）。旧描画位置は、新で全部を作り終えてから別の PR で作る（ADR 0002）。
# datums: 基準面ごとの下げ幅。決め方は blender-poc の README の「描画位置の描き分け」。label はアイコンの最高速度の数字
_DATUMS = {"bed": R.Datum(2, 1), "rail": R.Datum(4, 1)}

# 在来線のバラスト（砕石）: 道床を 2 色のまだらにして、石の粒に見せる（夏の絵だけ。雪の絵は雪の材質のまま）。
# 平均の色は blender-poc の道床の一色 (0.42, 0.40, 0.37) に合わせる。汚れの帯の色はその色から混ぜてあり、
# 坂の測り方（slope_measure.py）はレールを「赤 − 青」の大きい行で探すので、赤みを足さない
BALLAST_STONE_LO = (0.32, 0.305, 0.28)
BALLAST_STONE_HI = (0.52, 0.495, 0.46)
BALLAST_GRAIN = 6.0  # まだらの細かさ（ノイズの Scale。部品の座標 1 単位 ≈ 9px なので、粒は 1〜2px）
_BALLAST_STONE = R.track_noise("ami_ballast_stone", BALLAST_STONE_LO, BALLAST_STONE_HI, BALLAST_GRAIN)

# 形の差し替え（blender-poc の線路から変えたもの。ユーザーの指摘、2026-11-17）:
#   ballast: 行き止まりで、道床をレールの末端より奥（タイルの端）まで敷く
#   oil: レールの間の油の帯を中心をまたぐ 1 本にする（2 本に分けた形は、行き止まりで切り抜きにより消え、まくらぎが白く見えた）
OIL_U = R.RAIL_IN - 0.12           # 油の帯の半幅（blender-poc の oil と同じ）
OIL_Z, OIL_TH = R.BALLAST_H + 0.0015 * 3, 0.001  # 高さは blender-poc の 3 層目と同じ
_REPLACE = {
    "ballast": dataclasses.replace(next(p for p in R.TRACK_PARTS if p.name == "ballast"), shape=R.bed_to_edge_shape),
    "oil": dataclasses.replace(next(p for p in R.TRACK_EXTRAS if p.name == "oil"), shape=R.centre_strip_shape(OIL_U, OIL_Z, OIL_TH)),
}

# 行き止まりのレールの終点（車止めの位置）: 閉じた側のタイルの端から、タイル 1 辺のこの割合の所（ユーザーの指摘、2026-11-17。
# blender-poc はタイルの中心 = 0.5）。道床はタイルの端まで
END_FROM_EDGE = 0.25

R.TRACK_PROFILES.update({
    # diag_curves: カーブを斜めの絵で表す（pak128 標準の線路と同じ。T字・十字・分岐の絵も斜めの直線）。buffer: 行き止まりの車止め
    "rail_ballast": {"sheet": "ami_rail_ballast", "spill": 1, "datums": _DATUMS, "snow": True,
                     "groups": ("body", "weathering", "buffer"), "label": "160", "skin": {"ballast": _BALLAST_STONE},
                     "replace": _REPLACE, "diag_curves": True, "end_from_edge": END_FROM_EDGE},
})

# ---------------------------------------------------------------- 基盤の版と壁の way-object（ADR 0003。#16）
# 基盤の版の way（ami_rail_ballast_base_<版>）は、通常の版の道床の下に基盤を敷き、基盤は壁の位置で止まる（壁の無い側はタイルの端まで）。
# 壁そのものは way の絵に描かず、同じ版の壁の way-object（ami_wall_rail_<版>）のシートに描く（sheetlib の wall_sheet）。
# 版の値は sheetlib の walls（both = single）。center は側壁が無く、壁の way-object は行き止まりの端の壁だけ
# （ユーザーの指摘、2026-11-17。架線つきの版では center も架線の部品を持つので、壁の way-object も同じ 4 版にそろえる）
BASE_VARIANTS = {"single": "both", "back": "back", "center": "center", "front": "front"}

# 行き止まりの壁はタイルの末端まで（ユーザーの指摘、2026-11-17）: 側壁を閉じた側のタイルの端まで延ばし、端の壁をタイルの端に立てる。
# レールの終点と車止めは END_FROM_EDGE のまま（タイルの中）
_EDGE_WALLS = {n: dataclasses.replace(p, shape=R.to_edge_shape(p.shape))
               for p in R.TRACK_EXTRAS for n in ("wallL", "wallR") if p.name == n}
_EDGE_WALLS["endw"] = dataclasses.replace(next(p for p in R.TRACK_EXTRAS if p.name == "endw"), name="endw_edge",
                                          shape=R.end_wall_edge_shape())

for _v, _walls in BASE_VARIANTS.items():
    R.TRACK_PROFILES[f"rail_ballast_base_{_v}"] = dict(
        R.TRACK_PROFILES["rail_ballast"], sheet=f"ami_rail_ballast_base_{_v}", walls=_walls,
        groups=("body", "base", "weathering", "buffer", "wall"),
        replace=dict(_REPLACE, **_EDGE_WALLS), wall_sheet=f"ami_wall_rail_{_v}",
        # カーブのセルを斜めの形で描き、基盤の壁の無い側を削らない（複線の直角の曲がりで、内側の線の外側半分を埋める）
        curve_cells=True)

# ---------------------------------------------------------------- 架線つきの壁の way-object（ADR 0003。#17）
# 壁の way-object に架線（柱・梁・吊り金具・トロリ線。tools/blender/sheetlib/catenary_parts.py）を足した版（ami_wall_rail_<版>_catenary）。
# center は壁が無く、架線（梁・トロリ線）と行き止まりの端の壁だけ。寸法は catenary_parts の CAT_* にまとめた（値は仮。README の「架線の作り」）。
# 壁は基盤の版と同じ形で描き（groups も同じにする。手前/奥の分け方が本体の重心で決まるため）、way のシートは書かない（wall_only。
# way は基盤の版の対象が書く）。sheet は作業ファイルの名前だけに使い、基盤の版と分ける（同時に描いても work/ のセルが混ざらない）
CATENARY_LABEL = "E"  # 架線つきの壁のアイコンの文字（仮。アイコンはステップ 13 でまとめて作る）
for _v in BASE_VARIANTS:
    _base = R.TRACK_PROFILES[f"rail_ballast_base_{_v}"]
    R.TRACK_PROFILES[f"rail_ballast_base_{_v}_catenary"] = dict(
        _base, sheet=f"ami_rail_ballast_base_{_v}_cat", wall_sheet=f"ami_wall_rail_{_v}_catenary",
        groups=_base["groups"] + ("catenary", "catenary_support"), snow=False, wall_only=True, rise=R.CAT_RISE,
        wall_label=CATENARY_LABEL)

# ---------------------------------------------------------------- 対象（シート名 → 描く関数）
# 基盤の版の対象は、way のシートと壁の way-object のシートを 1 つのプロセスで描く

SHEETS = {
    "ami_rail_ballast": lambda: R.track_sheet("rail_ballast"),
}
for _v in BASE_VARIANTS:
    SHEETS[f"ami_rail_ballast_base_{_v}"] = lambda v=_v: R.track_sheet(f"rail_ballast_base_{v}")
for _v in BASE_VARIANTS:
    SHEETS[f"ami_wall_rail_{_v}_catenary"] = lambda v=_v: R.track_sheet(f"rail_ballast_base_{v}_catenary")

if __name__ == "__main__":
    R.run_targets(SHEETS, list(SHEETS))
