"""Blender から Simutrans 用のタイル画像シートを作る共通の道具（blender-poc と AMI が使う）。

アドオンのディレクトリで、そのアドオンの入口（`blender/render.py`）を Blender で動かす。入口はこのパッケージを import し、
アドオンごとの設定（`TRACK_PROFILES`・`ROAD_PROFILES` への登録、シート名と描く関数の対応）を渡して `run_targets` を呼ぶ。
設定の分け方は tools/README.md を参照。

モジュール（import の向きは下から上へ。逆はしない。track_parts は wall_parts・catenary_parts も import する）:
    core         設定値・シーン・材質・形の部品・基準面と部品の型
    track_parts  線路の部品（道床・まくらぎ・レール・車止め・汚れ）
    wall_parts   壁・基盤・橋・高架の橋脚（線路と道路で共通）
    catenary_parts 架線（柱・梁・吊り金具・トロリ線。線路の壁の way-object の電化の版）
    road_parts   道路の部品（路面・縁石・歩道・白線・車線・汚れ・雪）
    assemble     部品を経路ごとに組み立てる
    cells        セルの描画・特殊色・シート化
    sheetlib     シートの組み立て（線路・道路・トンネル・アイコン）と run_targets

アドオンの入口と判定の道具からは `import sheetlib as R` で、どのモジュールの名前も `R.名前` で引ける（下で全部をここに出す）。
"""
from . import core, wall_parts, catenary_parts, track_parts, road_parts, assemble, cells
from . import sheetlib as _sheets

for _m in (core, track_parts, wall_parts, catenary_parts, road_parts, assemble, cells, _sheets):
    globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
