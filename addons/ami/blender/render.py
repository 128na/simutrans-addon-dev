"""AMI のシートの入口。アドオンのディレクトリで Blender から動かす:

    blender -b --factory-startup --python blender/render.py [-- 対象名 ...]

描画の道具は tools/blender/sheetlib/。ここには AMI のシートの設定（描き分け・シート名）だけを置く
（共通とアドオンの設定の分け方は tools/README.md）。dat は blender/ami_dat.py、pak は build.py。

出力:
    src/ami_rail_ballast.png  在来線（バラスト軌道）の通常の版。形は blender-poc の線路と同じで、夏の道床を砕石のまだらにした
    src/ami_rail_ballast_base_<版>.png  基盤の版（single・back・center・front）の way。基盤は壁の位置で止まる
    src/ami_wall_rail_<版>.png  壁の way-object（4 版。center は行き止まりの端の壁だけ）。上 4 行が奥（back）、下 4 行が手前（front）の絵
    src/ami_wall_rail_<版>_catenary.png  架線つきの壁の way-object（4 版。center は架線と行き止まりの端の壁だけ）。行の並びは壁と同じ
    src/ami_wall_rail_twin_catenary_<back|front>.png  近い斜めの分け合うタイル用の架線つきの壁の絵（back・front の版で、斜めの梁を短くした）
    src/ami_rail_ballast_elev_<版>.png  高架の版（4 版）の way。基盤の版の絵の下に躯体を足す（橋脚・壁は描かない）
    src/ami_pier_rail.png     高架の真下の地面に敷く橋脚の way
    src/ami_pier_rail_gate.png  門型の橋脚の way（柱をタイルの角の近くに立て、直下に道路を通せる）
    src/ami_rail_ballast_bridge.png  橋（欄干なし。床はタイルの幅いっぱいで、壁は way-object を重ねる）。並びは blender-poc の橋と同じ
    src/ami_rail_ballast_tunnel.png  トンネルの坑口（覆いは blender-poc のトンネル、道床・レールは在来線の通常の版）
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

# 近い斜めの分け合うタイル用の架線つきの壁（ami_wall_rail_twin_catenary）の絵。壁だけの twin と同じく、nw・sw の線は back、ne・se の線は
# front の版の斜めのセルを使う。斜めの梁だけを短くした（CAT_BEAM_REACH_TWIN。分け合うタイルの隣の線の外の壁からはみ出さない）。
# 通常の 4 版の梁は変えない（斜めの線を隣のタイルに並べた複線・3 本並びで、梁をタイルの角でつなぐため）。dat は斜めのキーだけを指す
TWIN_FROM = ("back", "front")
for _v in TWIN_FROM:
    R.TRACK_PROFILES[f"rail_ballast_base_{_v}_twin_catenary"] = dict(
        R.TRACK_PROFILES[f"rail_ballast_base_{_v}_catenary"], sheet=f"ami_rail_ballast_base_{_v}_twcat",
        wall_sheet=f"ami_wall_rail_twin_catenary_{_v}",
        replace=dict(R.TRACK_PROFILES[f"rail_ballast_base_{_v}_catenary"]["replace"], cat_beam=R.beam_part(R.CAT_BEAM_REACH_TWIN)))

# ---------------------------------------------------------------- 高架の 4 版と橋脚の way（ADR 0003。#18）
# 高架の版の way（ami_rail_ballast_elev_<版>、dat は system_type=1）は、基盤の版と同じ絵（道床・基盤。基盤は壁の位置で止まる）の下に、
# 躯体（桁。sheetlib の ELEV_BODY_*）を足したもの。橋脚は描かない。壁・架線は地上と同じ way-object（ami_wall_rail_*）を重ねるので、
# 壁の way-object のシートは書かない（write_walls）。持ち分は躯体の分だけ下へ広げる（lower）。アイコンは高架の帯
for _v in BASE_VARIANTS:
    R.TRACK_PROFILES[f"rail_ballast_elev_{_v}"] = dict(
        R.TRACK_PROFILES[f"rail_ballast_base_{_v}"], sheet=f"ami_rail_ballast_elev_{_v}", write_walls=False, elev_body=True,
        lower=R.ELEV_BODY_LOWER, band="elevated")

# 橋脚の way（ami_pier_rail）: 高架の真下の地面のタイルに敷く。柱の上端は高架の躯体の下面に合わせる（sheetlib の pier_sheet）。
# 基準面は在来線と同じ（高架の床と同じ動かし方）
PIER_LABEL = "P"  # アイコンの文字（仮。アイコンはステップ 13 でまとめて作る）
# 門型の橋脚の way（ami_pier_rail_gate。#18 の追加）: 柱をタイルの角の近くに立て、上に梁を渡す（sheetlib の pier_gate_sheet）
PIER_GATE_LABEL = "G"

# ---------------------------------------------------------------- 橋とトンネル（ADR 0003。#19）
# 橋（ami_rail_ballast_bridge、obj=bridge）: 欄干を描かず、壁・架線は地上と同じ way-object を橋の上に重ねる（橋の 4 版は作らない）。
# 床は 1 つの絵で single・back・center・front のどの壁とも組む。床（基盤）と躯体は壁の位置で止め、高架の single と同じ作りにする
# （壁の外に床の縁が出ない。back・center・front を並べた橋は、床の間にすき間が出る。2026-11-18、ユーザーの決定。README の「橋とトンネルの作り」）。
# 壁は way-object が描くので、ここでは基盤を削るためだけに置き、シートには書かない（write_walls。高架の版と同じ）。
# セルは blender-poc の橋（track_bridge）と同じ並び: 行 0 の列 2・3 が平らな橋、行 1 が端の坂（Ramp・Ramp2）、行 2 が橋脚、行 3 が坂から始まる端
# （Start・Start2）。手前の絵は無い（欄干が無く、車両より手前に描く物が無い）。雪の絵は 4 行下
# BRIDGE_DECK_U: 床・端の坂の躯体・Start の躯体の横幅（経路から）。single の壁の外の面。床（基盤）は walls=both の壁の外の面で削られ、同じ幅になる
BRIDGE_DECK_U = R.WALL_U + R.WALL_W
BRIDGE_PIER = (R.PIER_SIZE * R.PIER_ACROSS_K, R.PIER_SIZE, R._M_PIER)  # 橋脚の柱（横切る向き × 沿う向き）。高架の単柱の橋脚と同じ太さ
BRIDGE_CELLS = ("ns", "ew", "up12", "up9", "up3", "up6", "up2_12", "up2_9", "up2_3", "up2_6")
_RAMP_BODY = next(p for p in R.TRACK_EXTRAS if p.name == "rampbody")
_BRIDGE_BASE = R.TRACK_PROFILES["rail_ballast_elev_single"]
R.TRACK_PROFILES["rail_ballast_bridge"] = dict(
    _BRIDGE_BASE, sheet="ami_rail_ballast_bridge", write_walls=False,
    groups=_BRIDGE_BASE["groups"] + ("ramp",), only=BRIDGE_CELLS, starts=True, piers=True, solid=True,
    pier_box=BRIDGE_PIER, deck_u=BRIDGE_DECK_U, band="bridge", badge=None,
    replace=dict(_BRIDGE_BASE["replace"], rampbody=dataclasses.replace(_RAMP_BODY, shape=R.ramp_body_shape(BRIDGE_DECK_U))))

# トンネル（ami_rail_ballast_tunnel、obj=tunnel）: blender-poc の坑口（sheetlib の tunnel_sheet。躯体はタイル全体の箱、口は低い側の辺）に、
# 在来線の通常の版の道床（砕石のまだら）・まくらぎ・レール・汚れを入れたもの。壁・架線は坑口のタイルにも way-object を重ねる
# （坑口の躯体は way の手前の絵で、way-object の絵より後に描かれるので、躯体の中へ入る壁・架線は躯体に隠れる。README の「橋とトンネルの作り」）
TUNNEL_LABEL = "160"

# ---------------------------------------------------------------- 対象（シート名 → 描く関数）
# 基盤の版の対象は、way のシートと壁の way-object のシートを 1 つのプロセスで描く

SHEETS = {
    "ami_rail_ballast": lambda: R.track_sheet("rail_ballast"),
}
for _v in BASE_VARIANTS:
    SHEETS[f"ami_rail_ballast_base_{_v}"] = lambda v=_v: R.track_sheet(f"rail_ballast_base_{v}")
for _v in BASE_VARIANTS:
    SHEETS[f"ami_wall_rail_{_v}_catenary"] = lambda v=_v: R.track_sheet(f"rail_ballast_base_{v}_catenary")
for _v in TWIN_FROM:
    SHEETS[f"ami_wall_rail_twin_catenary_{_v}"] = lambda v=_v: R.track_sheet(f"rail_ballast_base_{v}_twin_catenary")
for _v in BASE_VARIANTS:
    SHEETS[f"ami_rail_ballast_elev_{_v}"] = lambda v=_v: R.track_sheet(f"rail_ballast_elev_{v}")
SHEETS["ami_pier_rail"] = lambda: R.pier_sheet("ami_pier_rail", _DATUMS, label=PIER_LABEL)
SHEETS["ami_pier_rail_gate"] = lambda: R.pier_gate_sheet("ami_pier_rail_gate", _DATUMS, label=PIER_GATE_LABEL)
SHEETS["ami_rail_ballast_bridge"] = lambda: R.track_sheet("rail_ballast_bridge")
SHEETS["ami_rail_ballast_tunnel"] = lambda: R.tunnel_sheet("track", profile="rail_ballast", sheet="ami_rail_ballast_tunnel",
                                                           label=TUNNEL_LABEL)

if __name__ == "__main__":
    R.run_targets(SHEETS, list(SHEETS))
