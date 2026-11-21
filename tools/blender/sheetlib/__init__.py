"""Blender から Simutrans 用のタイル画像シートを作る共通の道具（blender-poc と AMI が使う）。

アドオンのディレクトリで、そのアドオンの入口（`blender/render.py`）を Blender で動かす。入口はこのパッケージを import し、
アドオンごとの設定（`TRACK_PROFILES`・`ROAD_PROFILES` への登録、シート名と描く関数の対応）を渡して `run_targets` を呼ぶ。
設定の分け方は tools/README.md を参照。

モジュール（import の向きは下から上へ。逆はしない。track_parts は wall_parts・catenary_parts も import する）:
    core         設定値・シーン・材質・形の部品・基準面と部品の型
    track_parts  線路の部品（道床・まくらぎ・レール・車止め・汚れ）
    slab_parts   スラブ軌道の部品（コンクリート道床・てん充層・スラブ・突起・締結装置。track_parts を import する）
    tram_parts   路面軌道の部品（コンクリートの床・縁の帯・レールの頭・溝・さび。track_parts を import する）
    wall_parts   壁・基盤・橋・高架の橋脚（線路と道路で共通）
    catenary_parts 架線（柱・梁・吊り金具・トロリ線。線路の壁の way-object の電化の版）
    road_parts   道路の部品（路面・縁石・歩道・白線・車線・汚れ・雪）
    assemble     部品を経路ごとに組み立てる
    cells        セルの描画・特殊色・シート化
    sheetlib     シートの組み立て（線路・道路・トンネル・アイコン）と run_targets
    sidewalk     歩道の way（地上・高架）と歩道の柵の way-object のシート（sheetlib の render_icon を使う）
    crossing     踏切（線路 × 道路）のシート（道路の way のシートのセルを下地に写す）
    depot        車庫（building の depot）など 1 タイルの建物のシート（4 方向 × 奥・手前 × 夏・雪）
    roadsign     道路標識（roadsign）のシート（柱を描き、板の 2D の絵を押す）

アドオンの入口と判定の道具からは `import sheetlib as R` で、どのモジュールの名前も `R.名前` で引ける（下で全部をここに出す）。
"""
from . import core, wall_parts, catenary_parts, track_parts, slab_parts, tram_parts, road_parts, assemble, cells
from . import sheetlib as _sheets
from . import sidewalk
from . import crossing
from . import depot
from . import roadsign

for _m in (core, track_parts, slab_parts, tram_parts, wall_parts, catenary_parts, road_parts, assemble, cells, _sheets, sidewalk, crossing, depot, roadsign):
    globals().update({_k: _v for _k, _v in vars(_m).items() if not _k.startswith("__")})
