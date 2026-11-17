"""AMI のシートの入口。アドオンのディレクトリで Blender から動かす:

    blender -b --factory-startup --python blender/render.py [-- 対象名 ...]

描画の道具は tools/blender/sheetlib/。ここには AMI のシートの設定（描き分け・シート名）だけを置く
（共通とアドオンの設定の分け方は tools/README.md）。dat は blender/ami_dat.py、pak は build.py。

出力:
    src/ami_rail_ballast.png  在来線（バラスト軌道）の通常の版。形は blender-poc の線路と同じで、夏の道床を砕石のまだらにした
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

# ---------------------------------------------------------------- 対象（シート名 → 描く関数）

SHEETS = {
    "ami_rail_ballast": lambda: R.track_sheet("rail_ballast"),
}

if __name__ == "__main__":
    R.run_targets(SHEETS, list(SHEETS))
