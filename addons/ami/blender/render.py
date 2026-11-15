"""AMI のシートの入口。アドオンのディレクトリで Blender から動かす:

    blender -b --factory-startup --python blender/render.py [-- 対象名 ...]

描画の道具は tools/blender/sheetlib/。ここには AMI のシートの設定（描き分け・シート名）だけを置く
（共通とアドオンの設定の分け方は tools/README.md）。dat は blender/ami_dat.py、pak は build.py。

出力:
    src/ami_rail_ballast.png  在来線（バラスト軌道）の通常の版。今は blender-poc の線路と同じ仮の絵
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
R.TRACK_PROFILES.update({
    "rail_ballast": {"sheet": "ami_rail_ballast", "spill": 1, "datums": _DATUMS, "snow": True,
                     "groups": ("body", "weathering"), "label": "160"},
})

# ---------------------------------------------------------------- 対象（シート名 → 描く関数）

SHEETS = {
    "ami_rail_ballast": lambda: R.track_sheet("rail_ballast"),
}

if __name__ == "__main__":
    R.run_targets(SHEETS, list(SHEETS))
