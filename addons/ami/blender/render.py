"""AMI のシートの入口。アドオンのディレクトリで Blender から動かす:

    blender -b --factory-startup --python blender/render.py [-- 対象名 ...]

描画の道具は tools/blender/sheetlib/。ここには AMI のシートの設定（描き分け・シート名）だけを置く
（共通とアドオンの設定の分け方は tools/README.md）。dat は blender/ami_dat.py、pak は build.py。

出力:
    src/ami_rail_ballast.png  在来線（バラスト軌道）の通常の版。形は blender-poc の線路と同じで、夏の道床を砕石のまだらにした
    work/                     セルごとの生の描画結果（確認用）
"""
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

R.TRACK_PROFILES.update({
    "rail_ballast": {"sheet": "ami_rail_ballast", "spill": 1, "datums": _DATUMS, "snow": True,
                     "groups": ("body", "weathering"), "label": "160", "skin": {"ballast": _BALLAST_STONE}},
})

# ---------------------------------------------------------------- 対象（シート名 → 描く関数）

SHEETS = {
    "ami_rail_ballast": lambda: R.track_sheet("rail_ballast"),
}

if __name__ == "__main__":
    R.run_targets(SHEETS, list(SHEETS))
