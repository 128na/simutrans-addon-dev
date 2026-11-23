"""AMI のシートの入口。アドオンのディレクトリで Blender から動かす:

    blender -b --factory-startup --python blender/render.py [-- 対象名 ...]

描画の道具は tools/blender/sheetlib/。ここには AMI のシートの設定（描き分け・シート名）だけを置く
（共通とアドオンの設定の分け方は tools/README.md）。dat は blender/ami_dat.py、pak は build.py。
軌道の種類ごとの名前は blender/catalog.py から展開する。種類を足すときは catalog.TRACKS と、下の TRACK_SETTINGS に足す（旧描画位置の版 catalog.OLD_TRACKS は TRACKS から導かれ、TRACK_SETTINGS も新の設定から導く）。

出力（在来線の名前で書く。高速線 ami_rail_slab も、壁・架線・橋脚を除いて同じ並び）:
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
    src/ami_road_<種類>.png    道路の通常の版（local・general・expressway）。断面は blender-poc の高速道路で、中央線と路面の色が種類ごとに違う
    src/ami_mark_<種類>.png  多車線と交差点の路面表示の way（一般道路に重ねる白線と路面。#187）
    src/ami_wall_road_<版>.png  道路の壁の way-object（single・back・center・front。3 種で共有。center は行き止まりの端の壁だけ）。上 4 行が奥、下 4 行が手前の絵
    src/ami_wall_road_<front|center>_divider.png  中央分離帯つきの壁の way-object（壁の版に、奥の側壁の位置の縁石の帯とガードレールを足した）
    src/ami_road_<種類>_base_<版>.png  道路の地上の基盤の版（4 版。2026-11-19 にユーザーが確定）。壁の外を削り、カーブを斜めの形のセルに描く
    src/ami_road_<種類>_elev_<版>.png  道路の高架の版（4 版）。床（路面と基盤）と躯体だけ（橋脚・壁は描かない）
    src/ami_road_<種類>_bridge.png  道路の橋（欄干なし。床の縁の下に青い桁を見せる）
    src/ami_road_<種類>_tunnel.png  道路のトンネルの坑口（覆いは blender-poc の高速道路のトンネル、路面・白線は道路の種類ごと）
    src/ami_pier_road.png     道路の高架の真下の地面に敷く橋脚の way
    src/ami_tram.png          路面軌道（tram_track）の通常の版。道路の上に重ねて敷く想定で、コンクリートの床・縁の帯・レールの頭・溝だけ（段も壁も無い）
    src/ami_sidewalk.png      歩道の way（道路の隣のタイルに敷く。敷石と、つながらない辺の縁石）
    src/ami_embankment_<front|back>.png  盛土の way（高架の脇の地面に敷く芝の法面の楔。#123）
    src/ami_sign_<名前>.png   道路標識（roadsign）。柱と板の 4 向きの絵（#122）
    src/ami_sidewalk_<舗装>.png  歩道の種類（asphalt・brick・tile。形は ami_sidewalk と同じで敷石の材質だけ違う。#119）
    src/ami_sidewalk_elev.png  高架の歩道（板の下に道路の高架と同じ深さの基盤と躯体。#119）
    src/ami_wall_sidewalk_<版>.png  歩道の柵の way-object（single・back・front。#119）
    work/                    セルごとの生の描画結果（確認用）
"""
import dataclasses
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
sys.path.insert(0, _HERE)  # Blender の --python は、スクリプトのディレクトリを探す先に入れない
import catalog  # noqa: E402
import sheetlib as R  # noqa: E402

_p = catalog.profile  # way・シートの名前 → TRACK_PROFILES の名前

# ---------------------------------------------------------------- 線路の描き分け
# 新描画位置（レールが低い。今の pak128・iss）。旧描画位置（SIS に合う）は、catalog.OLD_TRACKS の名前で、下の TRACK_SETTINGS が新の設定から導く（#26。ADR 0011）。
# datums: 基準面ごとの下げ幅。決め方は blender-poc の README の「描画位置の描き分け」。label はアイコンの最高速度の数字
_DATUMS = {"bed": R.Datum(2, 1), "rail": R.Datum(4, 1)}

# 在来線のバラスト（砕石）: 道床を 2 色のまだらにして、石の粒に見せる（夏の絵だけ）。
# 元の 2 色の平均は blender-poc の道床の一色 (0.42, 0.40, 0.37)。そこから明暗差を BALLAST_CONTRAST 倍に広げ（#56）、BALLAST_DARK・BALLAST_TINT で暗く青みの灰にした（#70）。
# 汚れの帯の色は blender-poc の道床の色から混ぜてある。坂の測り方（slope_measure.py）はレールを「赤 − 青」の大きい行で探すので、赤みを足さない
BALLAST_STONE_LO = (0.32, 0.305, 0.28)
BALLAST_STONE_HI = (0.52, 0.495, 0.46)
BALLAST_GRAIN = 12.0  # まだらの細かさ（ノイズの Scale。部品の座標 1 単位 ≈ 9px なので、粒は約 1px）
# 精細化（#56）で決めた描き分け。値の決め方は docs/records/2026-11-20_ami-refine-round1.md〜round7.md（ラウンド 8 で本番に入れた）
BALLAST_CONTRAST = 2.4  # まだらの明暗差を、平均の色（sheetlib の _BALLAST_RGB）から何倍離すか（ラウンド 1）
# 砕石の暗さと色合い: 弾性まくらぎ直結軌道（明るい中立の灰の道床）と見分けるため、暗く青みの灰にした（#70。2026-11-21、ユーザーの決定。
# 試した 4 案と値は記録 docs/records/2026-11-21_ami-ballast-color.md）。#56 のラウンド 5 は DARK 0.82・色合いなし。
# 色合いは R・G・B ごとの倍率。赤み（R − B を上げる）と緑み（地面と見なされる）は足せない（slope_measure.py）。汚れの帯の色は変えない
BALLAST_DARK = 0.66     # 砕石の色の倍率。使い込んだ砕石は床のコンクリートより暗い
BALLAST_TINT = (0.88, 0.97, 1.14)


def _away(c, w, mean=R._BALLAST_RGB):
    """色 c を平均の色 mean から w 倍離す（0〜1 に収める）。"""
    return tuple(min(1.0, max(0.0, m + w * (x - m))) for x, m in zip(c, mean))


def _stone(c):
    return tuple(min(1.0, x * BALLAST_DARK * t) for x, t in zip(_away(c, BALLAST_CONTRAST), BALLAST_TINT))


_BALLAST_STONE = R.track_noise("ami_ballast_stone", _stone(BALLAST_STONE_LO), _stone(BALLAST_STONE_HI), BALLAST_GRAIN)

# 形の差し替え（blender-poc の線路から変えたもの。ユーザーの指摘、2026-11-17）:
#   ballast: 行き止まりで、道床をレールの末端より奥（タイルの端）まで敷く
#   oil: レールの間の油の帯を中心をまたぐ 1 本にする（2 本に分けた形は、行き止まりで切り抜きにより消え、まくらぎが白く見えた）
OIL_U = R.RAIL_IN - 0.12           # 油の帯の半幅（blender-poc の oil と同じ）
OIL_Z, OIL_TH = R.BALLAST_H + 0.0015 * 3, 0.001  # 高さは blender-poc の 3 層目と同じ
_REPLACE = {
    "ballast": dataclasses.replace(next(p for p in R.TRACK_PARTS if p.name == "ballast"), shape=R.bed_to_edge_shape),
    "oil": dataclasses.replace(next(p for p in R.TRACK_EXTRAS if p.name == "oil"), shape=R.centre_strip_shape(OIL_U, OIL_Z, OIL_TH)),
}

# ---- 在来線の精細化（#56）。在来線（TRACK_SETTINGS の RAIL_BALLAST）と、その部品を使い回す弾性まくらぎ直結軌道（RAIL_CONCRETE。下）に効く。
# ここを変えると両方の絵が変わるので、両方のシートの差分を見る（ADR 0006）
# まくらぎ: 間隔 SLEEPER_PITCH（タイル 1 辺 10 に 16 本。直線のセルの画面で 4px おき）。直線の経路はタイルの辺の外へ PATH_EXT 延びるので、
# まくらぎをタイルの辺の上にそろえ、タイルの継ぎ目でも同じ間隔にする（向きを逆にした経路でも同じ位置）。色は明るい PC（コンクリート）の
# くすみのまだら（ラウンド 4）。1/2 の画面（本体がタイルの原点にそろえた 2×2 で平均する）で粒に見えないよう、18 本（約 3.56px おき。
# 2×2 の格子とずれて、むらのある粒になった）から 16 本にし、位置を辺から半ピッチから辺の上へ動かした（#89、2026-11-21、ユーザーの決定。
# 記録 docs/records/2026-11-21_ami-half-zoom-grain.md）
SLEEPER_PITCH = 10 / 16
SLEEPER_FIRST = R.PATH_EXT % SLEEPER_PITCH
SLEEPER_RGB = ((0.66, 0.65, 0.62), (0.78, 0.77, 0.74))
# レール: 側面を暗いさび色の 1px にし（幅 0.14、高さは元の 0.30）、頭頂面に車輪で磨かれた明るい帯を載せる（ラウンド 2・3）
RAIL_IN, RAIL_OUT, RAIL_Z1 = 0.41, 0.55, 0.30
RAIL_SIDE_RGB = (0.30, 0.19, 0.15)
RAIL_HEAD_RGB = (0.92, 0.91, 0.88)
# まくらぎの間を、まくらぎの上面の少し下まで砕石で埋める（ラウンド 2）。汚れの帯はその上に出す
EMBED_TOP = R.SLEEPER_Z + R.SLEEPER_H / 2 - 0.012
# 汚れの帯（sheetlib の TRACK_WEAR）の色: 道床の色からの寄せ具合（無ければ sheetlib の値）と、道床の色から離す倍率。
# 離す倍率 1.8 はラウンド 1、油（レールの間）の 0.5・1.0 はラウンド 4（黒い梯子に見えた）
WEAR_T = {"oil": 0.5}
WEAR_K = {"rust0": 1.8, "rust1": 1.8, "oil": 1.0}
# 道床の肩: まくらぎの上面の高さの平らな肩を ±BALLAST_SHOULDER まで延ばし、そこから床（±1.9）まで斜面（ラウンド 5）
BALLAST_SHOULDER = 1.45
# 雪の絵: 積もったばかりの雪（汚れの帯もまくらぎも雪。レールだけが出る。ラウンド 6）。道床の雪は地面の雪と同じ青みで明るく（ラウンド 7）
SNOW_BED_RGB = (0.945, 0.945, 1.0)

_snow_bed = ("ami_snow_bed", SNOW_BED_RGB) + tuple(R.SNOW_SKIN["ballast"][2:])
_wear = {}
for _n, _u, (_lo, _hi), _t, _ in R.TRACK_WEAR:
    _t = WEAR_T.get(_n, _t)
    _wear[_n] = R.track_noise(f"ami_track_{_n}", _away(R._mix(R._BALLAST_RGB, _lo, _t), WEAR_K[_n]),
                              _away(R._mix(R._BALLAST_RGB, _hi, _t), WEAR_K[_n]), 3.0)


def _lifted(shape, dz):
    """形 shape を dz だけ上げる（汚れの帯を、まくらぎの間を埋めた砕石の上に出す）。"""
    def lifted(path, k):
        geo = shape(path, k)
        if geo is None:
            return None
        verts, faces = geo
        return [v + type(v)((0, 0, dz)) for v in verts], faces
    return lifted


def _rail_shape(side):
    def shape(path, k):
        a, b = RAIL_IN * k, RAIL_OUT * k
        prof = [(a, R.RAIL_Z0), (b, R.RAIL_Z0), (b, RAIL_Z1), (a, RAIL_Z1)]
        return R.sweep(path, [(side * u, v) for u, v in prof][::side])
    return shape


_FILL_HALF = R.SLEEPER_LEN / 2 + 0.05
_rail_mat = ("rail_side", RAIL_SIDE_RGB) + tuple(next(p for p in R.TRACK_PARTS if p.name == "railL").material[2:])
_old = {p.name: p for p in R.TRACK_PARTS + R.TRACK_EXTRAS}
_BALLAST_SECTION = [(-1.9, 0.0), (1.9, 0.0), (BALLAST_SHOULDER, EMBED_TOP - 0.001), (-BALLAST_SHOULDER, EMBED_TOP - 0.001)]
_BALLAST_REPLACE = dict(
    _REPLACE,
    ballast=dataclasses.replace(_old["ballast"], shape=R.bed_to_edge(_BALLAST_SECTION)),
    sleeper=dataclasses.replace(_old["sleeper"], shape=R.sleeper_shape(SLEEPER_PITCH, SLEEPER_FIRST)),
    sleeper_rust=dataclasses.replace(_old["sleeper_rust"], shape=R._sleeper_patch_shape(
        R.RAIL_IN - 0.16, R.RAIL_OUT + 0.16, SLEEPER_PITCH, SLEEPER_FIRST)),
    railL=R.Part("railL", "rail", "gauge", _rail_mat, _rail_shape(-1)),
    railR=R.Part("railR", "rail", "gauge", _rail_mat, _rail_shape(1)),
    **{_n: R.Part(_n, _old[_n].datum, _old[_n].width, _m, _lifted(_REPLACE.get(_n, _old[_n]).shape, EMBED_TOP - R.BALLAST_H),
                  _old[_n].group) for _n, _m in _wear.items()})
_BALLAST_PARTS = (
    R.Part("rail_head", "rail", "gauge", ("rail_head", RAIL_HEAD_RGB, 0.4, 0.0),
           R._strip_shape(RAIL_IN + 0.01, RAIL_OUT - 0.01, RAIL_Z1 + 0.001, 0.004)),
    R.Part("ballast_fill", "rail", "gauge", _old["ballast"].material,
           lambda path, k: R.sweep(path, [(-_FILL_HALF * k, R.BALLAST_H - 0.01), (_FILL_HALF * k, R.BALLAST_H - 0.01),
                                          (_FILL_HALF * k, EMBED_TOP), (-_FILL_HALF * k, EMBED_TOP)])),
)
_BALLAST_SKIN = {"ballast": _BALLAST_STONE, "ballast_fill": _BALLAST_STONE,
                 "sleeper": R.track_noise("ami_track_sleeper", *SLEEPER_RGB, 5.0)}
_BALLAST_SNOW_SKIN = dict({_n: _snow_bed for _n in ("ballast", "ballast_fill", "base", "oil", "rust0", "rust1", "sleeper_rust", "sleeper")})

# ---- 弾性まくらぎ直結軌道（ami_rail_concrete。#62）。在来線の部品（まくらぎ・レール・汚れ・車止め）と寸法をそのまま使い、
# 道床だけを砕石からコンクリートの平らな面にする（在来線とは道床で見分ける。2026-11-21、ユーザーの決定）。道床の高さ・底の幅は
# 在来線の道床と同じ（壁・架線・基盤と噛み合う）。まくらぎのゴムの靴（防振材）の縁は、画面で 1px 未満（docs/reference/way-addon.md の 12 章）で、
# 0.12 まで広げてもまくらぎの間が暗くなるだけで靴に見えなかったので描かない。中央の排水溝も描かない（くどさ。11 章）
# 道床の上面の半幅。在来線の肩（BALLAST_SHOULDER）と同じで、そこから底（±1.9）まで同じ斜面。外形は在来線と同じになる。
# 1.75（ほぼ垂直の縁）では奥の縁が在来線より 1px 外まで塗られ、坂の寄り・継ぎ目のずれが在来線より 0.5px 大きかった。
# 1.55〜1.65 でもシートの塗りが在来線より外へ出たので、在来線と同じ所で止めた（2026-11-21、ユーザーの決定）
CONC_BED_HALF = BALLAST_SHOULDER
CONC_BED_RGB = ((0.47, 0.47, 0.46), (0.56, 0.56, 0.55))  # 道床のコンクリート（まくらぎより暗い。赤みを足さない: slope_measure.py がレールを「赤 − 青」で探す）
CONC_BED_GRAIN = 25.0  # まだらの細かさ（打ち放しの肌。壁・基盤のコンクリートと同じ Scale）
_CONC_SECTION = [(-1.9, 0.0), (1.9, 0.0), (CONC_BED_HALF, EMBED_TOP - 0.001), (-CONC_BED_HALF, EMBED_TOP - 0.001)]
_CONC_BED = R.track_noise("ami_conc_bed", *CONC_BED_RGB, CONC_BED_GRAIN)
_CONC_REPLACE = dict(_BALLAST_REPLACE, ballast=dataclasses.replace(_old["ballast"], shape=R.bed_to_edge(_CONC_SECTION)))
_CONC_SKIN = dict(_BALLAST_SKIN, ballast=_CONC_BED, ballast_fill=_CONC_BED)

# ---- フローティング・ラダー軌道（ami_rail_ladder。#67）。路盤は弾性まくらぎ直結軌道のコンクリートの道床（形・塗りの範囲は在来線と同じ）。
# 横に並ぶまくらぎの代わりに、レールの下に PC の縦梁を 2 本通し、梁の間を暗い帯（路盤が低く見える所）にし、鋼管の継材を
# タイル 1 辺に 4 本（LADDER_TIE_PITCH。タイルの継ぎ目でそろう）渡す。在来線・直結軌道（まくらぎ 16 本）とは、途切れない 2 本の梁と梁の間の
# 暗い帯で、スラブ（幅の広い板と黒い締結装置）とは梁の細さで見分ける（2026-11-21、ユーザーの決定）。本物の梁の幅・継材の間隔は
# 確かめていない（鉄道総研のページの本文に無い）ので、画面の見え方から決めた（docs/reference/way-addon.md の 12 章: 1 単位 ≈ 7.2px）。
# 本物で 1px 未満の継材は太らせる。T字・十字・分岐の絵の斜めの部分（分岐の側）は、梁ではなく在来線のまくらぎにする（LADDER_DIAG）。
# 雪の絵は在来線・直結軌道と同じく、積もったばかりの雪（梁・継材も雪）で、雪では見分けない（#70 の決定に合わせる）
# 縦梁の、経路の中心からの横の範囲（幅約 3.1px、梁の間は約 4.3px）。梁の間は 1/2 の画面でほぼ 2px になり、2×2 の平均で縁が
# 粒にならない（#89 で内側の縁を 0.23 → 0.30。梁の間が約 1.65px だと、縁が 1 画素ごとに明暗に割れた）
LADDER_BEAM = (0.30, 0.73)
LADDER_TIE_PITCH = 2.5        # 継材の間隔（タイル 1 辺 10 に 4 本）
LADDER_TIE_FIRST = (R.PATH_EXT + LADDER_TIE_PITCH / 2) % LADDER_TIE_PITCH
LADDER_TIE_W = 0.2            # 継材の線路に沿う幅（約 1.4px。本物の鋼管は 1px 未満）
LADDER_TIE_RGB = ((0.50, 0.50, 0.50), (0.58, 0.58, 0.58))  # 継材（鋼管の灰）。暗い帯の上で明るく見える
LADDER_GAP_RGB = ((0.10, 0.10, 0.10), (0.16, 0.16, 0.16))  # 梁の間の暗い帯（赤みを足さない）
_BEAM_Z0, _BEAM_Z1 = R.SLEEPER_Z - R.SLEEPER_H / 2, R.SLEEPER_Z + R.SLEEPER_H / 2  # まくらぎと同じ高さ（上面にレールが載る）
_GAP_Z = OIL_Z + EMBED_TOP - R.BALLAST_H  # 梁の間の帯は、在来線の油の帯と同じ高さ（汚れの帯より上）


def _beam_shape(path, k):
    a, b = LADDER_BEAM[0] * k, LADDER_BEAM[1] * k
    return R.merge([R.sweep(path, [(s * a, _BEAM_Z0), (s * b, _BEAM_Z0), (s * b, _BEAM_Z1), (s * a, _BEAM_Z1)][::s]) for s in (1, -1)])


def _tie_shape(path, k):
    z0 = _GAP_Z + 0.0015  # 暗い帯の上から梁の上面まで
    boxes = [R.box(p.x, p.y, (z0 + _BEAM_Z1) / 2, LADDER_TIE_W, (LADDER_BEAM[0] + 0.05) * 2 * k, _BEAM_Z1 - z0, rot=ang)
             for p, ang in R.along(path, LADDER_TIE_PITCH, LADDER_TIE_FIRST)]
    return R.merge(boxes) if boxes else None


# 部品の名前は在来線のもの（sleeper・sleeper_rust・oil）を使い、雪の差し替え（_BALLAST_SNOW_SKIN）がそのまま効くようにする
_LADDER_REPLACE = dict(
    _CONC_REPLACE,
    sleeper=dataclasses.replace(_old["sleeper"], shape=_beam_shape),
    sleeper_rust=dataclasses.replace(_old["sleeper_rust"], material=R.track_noise("ami_ladder_tie", *LADDER_TIE_RGB, 5.0), shape=_tie_shape),
    oil=dataclasses.replace(_old["oil"], material=R.track_noise("ami_ladder_gap", *LADDER_GAP_RGB, 3.0),
                            shape=R.centre_strip_shape(LADDER_BEAM[0] + 0.02, _GAP_Z, 0.001)),
)
LADDER_DIAG = {n: _BALLAST_REPLACE[n] for n in ("sleeper", "sleeper_rust", "oil")}  # 分岐の側（斜めの部分）は在来線のまくらぎ
_LADDER_SKIN = _CONC_SKIN  # 路盤は直結軌道の道床、梁は PC でまくらぎと同じ色

# 行き止まりのレールの終点（車止めの位置）: 閉じた側のタイルの端から、タイル 1 辺のこの割合の所（ユーザーの指摘、2026-11-17。
# blender-poc はタイルの中心 = 0.5）。道床はタイルの端まで
END_FROM_EDGE = 0.25

# 高速線の基準面: bed・rail は在来線のまま（壁・架線・橋脚と噛み合う）。コンクリート道床（slab_bed）はレールと同じ下げ幅にする
_SLAB_DATUMS = dict(_DATUMS, slab_bed=_DATUMS["rail"])

# 旧描画位置（SIS に合う。#26。ADR 0011）: 基準面を動かさず（絵の位置 = 地面の位置）、持ち分を手前へはみ出させない。blender-poc の旧描画位置
# （TRACK_PROFILES["old"]）と同じ。blender-poc は SIS の新幹線の線路と段なくつながることを確かめてある
_OLD_DATUMS = R.FLAT

# 軌道の種類ごとの描き分け（catalog.Track.key → TRACK_PROFILES のキー）。label はアイコンの最高速度の数字
TRACK_SETTINGS = {
    catalog.RAIL_BALLAST.key: {"label": "160", "skin": _BALLAST_SKIN, "snow_skin": _BALLAST_SNOW_SKIN, "replace": _BALLAST_REPLACE,
                               "parts": _BALLAST_PARTS},
    catalog.RAIL_CONCRETE.key: {"label": "240", "skin": _CONC_SKIN, "snow_skin": _BALLAST_SNOW_SKIN, "replace": _CONC_REPLACE,
                                "parts": _BALLAST_PARTS},
    catalog.RAIL_LADDER.key: {"label": "360", "skin": _LADDER_SKIN, "snow_skin": _BALLAST_SNOW_SKIN, "replace": _LADDER_REPLACE,
                              "parts": _BALLAST_PARTS, "diag_replace": LADDER_DIAG},
    # 高速線（スラブ軌道）: 部品は sheetlib の slab_parts。レール・基準面・カーブや行き止まりの作りは在来線と同じ
    catalog.RAIL_SLAB.key: {"label": "480", "datums": _SLAB_DATUMS, "track_parts": R.SLAB_TRACK_PARTS, "bed_fills": R.SLAB_BED_FILLS,
                            "replace": R.SLAB_WEAR_REPLACE, "snow_skin": R.SLAB_SNOW_SKIN},
}

# 旧描画位置の線路（#26）: 新と同じ部品・材質・寸法で、基準面だけを動かさない（datums・spill を上書きする）
for _t in catalog.OLD_TRACKS:
    TRACK_SETTINGS[_t.key] = dict(TRACK_SETTINGS[_t.key[:-len(catalog.OLD)]], datums=_OLD_DATUMS, spill=0)

# ex_switches: 分岐の追加画像（Y字分岐・三方分岐。sheetlib の track_sheet の ex_switches。#57）のセルを描く。基盤・高架の版と架線つきの壁も
# この設定を引き継ぐ（dat は blender/ami_dat.py の EX_WAYS・EX_WAYOBJS、pak への継ぎ足しは ex_graft.py）
for _t in catalog.ALL_TRACKS:
    # diag_curves: カーブを斜めの絵で表す（pak128 標準の線路と同じ。T字・十字・分岐の絵も斜めの直線）。buffer: 行き止まりの車止め
    R.TRACK_PROFILES[_t.key] = dict({"sheet": _t.way, "spill": 1, "datums": _DATUMS, "snow": True,
                                     "groups": ("body", "weathering", "buffer"), "diag_curves": True,
                                     "end_from_edge": END_FROM_EDGE, "ex_switches": True}, **TRACK_SETTINGS[_t.key])

# ---------------------------------------------------------------- 路面軌道（ami_tram。#23）
# tram（waytype=tram_track）で道路の上に重ねて敷く（ADR 0002）。コンクリートで固めた床・縁の明るい帯・レールの頭・溝・さび（sheetlib の
# tram_parts）。床は道路の路面と同じ高さ（基準面は動かさない FLAT）で、絵の基準位置と持ち分は道路と同じ ROAD_CY（spill 0）。
# pak128 標準の Tram_Track_050_A もレールは地面の菱形の位置（ref_measure で直線のずれ +0。AMI の在来線は +2）で、下げていない。
# カーブは曲線のまま（diag_curves を使わない。2026-11-17 のユーザーの指摘。README の「残っていること」）。行き止まりのレールは在来線と同じく
# 閉じた側の端から END_FROM_EDGE で止め（床はタイルの端まで。2026-11-20 のユーザーの指摘）、車止めは置かない（道路の上に立つので）。雪の絵は道路の車道と同じく除雪された夏の絵（TRAM_SNOW_SKIN）
TRAM_KEY = catalog.profile(catalog.TRAM)
TRAM_DATUMS = R.FLAT  # tram_bed（床と縁の帯）は分岐の絵で作り直さない基準面（スラブ軌道の slab_bed と同じ考え方）
R.TRACK_PROFILES[TRAM_KEY] = {
    "sheet": catalog.TRAM, "label": "60", "spill": 0, "datums": TRAM_DATUMS, "snow": True, "anchor": R.ROAD_CY, "cy": R.ROAD_CY,
    "groups": ("body", "weathering"), "track_parts": R.TRAM_TRACK_PARTS, "replace": R.TRAM_WEAR_REPLACE,
    "snow_skin": R.TRAM_SNOW_SKIN, "end_from_edge": END_FROM_EDGE, "cell_fills": R.TRAM_CELL_FILLS, "ex_switches": True,
}

# ---------------------------------------------------------------- 跨座式モノレール（ami_monorail。#113）
# 物の並びは iss の跨座式（地上・高架の 3 版・トンネル）に合わせる（2026-11-21、ユーザーの決定）。部品は sheetlib の monorail_parts（桁と、高架の柱・腕）。
# 桁は走行面（rail）の基準面に乗せ、分岐の絵は分岐の経路の桁を描く。カーブは斜めの絵（iss と同じく dat の image[sw] などが斜めのセルを指す）、
# 近い斜めの絵は描かない（iss の dat にキーが無い）。基準面は動かさない（FLAT）ので、絵の基準位置は地面の高さ（128）。
# 雪の絵は桁の上面だけを雪にする（iss の跨座式は雪の絵を持たない。AMI のほかの way にそろえて足した）
MONORAIL_KEY = catalog.profile(catalog.MONORAIL)
MONORAIL_LABEL = "150"
R.TRACK_PROFILES[MONORAIL_KEY] = {
    "sheet": catalog.MONORAIL, "label": MONORAIL_LABEL, "spill": 1, "datums": R.FLAT, "snow": True, "anchor": 128,
    "groups": ("body",), "track_parts": R.monorail_parts(), "snow_skin": R.MONO_SNOW_SKIN, "diag_curves": True, "close": False,
}
# 高架の 3 版（ami_monorail_elev_<版>、dat は system_type=1）: 桁を下へ深くし、桁が出入りする辺の角に柱と腕を足す（版で柱の側が違う）。
# 柱は高架の高さ（ELEV_STEPS 段）下の地面まで伸ばし、持ち分も同じだけ下へ広げる。アイコンは下の帯で高架を示す
MONORAIL_ELEV_LOWER = R.ELEV_LOWER + 4
for _v in catalog.MONORAIL_ELEV_VARIANTS:
    R.TRACK_PROFILES[catalog.profile(catalog.monorail_elev(_v))] = dict(
        R.TRACK_PROFILES[MONORAIL_KEY], sheet=catalog.monorail_elev(_v),
        track_parts=R.monorail_parts(R.MONO_BEAM_TOP - R.MONO_ELEV_BEAM_D), cell_fills=R.monorail_pier_fills(_v),
        lower=MONORAIL_ELEV_LOWER, band="elevated", badge=_v[0].upper())

# ---------------------------------------------------------------- 懸垂式モノレール（ami_monorail_suspended。#116）
# 物の並びは iss の懸垂式（地上・高架とも front・center・back）に合わせ、支柱は way の絵に持たせる（2026-11-22、進捗管理の決定・案 A）。
# 部品は sheetlib の monorail_parts の suspended_*（空中の桁と、柱・梁）。どれも高さのある部品で、手前の側の柱・梁は手前の絵（シートの行 4〜7、
# 雪は行 12〜15）、桁と奥の側の柱・梁は奥の絵（行 0〜3、雪は行 8〜11）。並び・斜めのカーブ・近い斜め無しは跨座式と同じ。
# 高架の版は柱を高架の下の地面まで延ばし、持ち分も下へ広げる
for _v in catalog.MONORAIL_SUSPENDED_VARIANTS:
    for _elev in (False, True):
        _n = catalog.monorail_suspended(_v, _elev)
        R.TRACK_PROFILES[catalog.profile(_n)] = dict(
            R.TRACK_PROFILES[MONORAIL_KEY], sheet=_n, track_parts=R.suspended_parts(), snow_skin=R.SUSP_SNOW_SKIN,
            cell_fills=R.suspended_pier_fills(_v, _elev), front_row=4, rise=R.SUSP_RISE, badge=_v[0].upper(),
            **(dict(lower=MONORAIL_ELEV_LOWER, band="elevated") if _elev else {}))
# 電化の way-object（ami_monorail_power・ami_monorail_suspended_power。#116）: way-object のシート（奥の絵 4 行 → 手前の絵 4 行。雪の絵は無い）。
# 給電レールと碍子だけを描き、桁は holdout で置いて奥のレールを隠す（sheetlib の monorail_parts の power_*）。並びは跨座式の way と同じ
for _n, _susp in catalog.MONORAIL_POWERS.items():
    R.TRACK_PROFILES[catalog.profile(_n)] = dict(
        R.TRACK_PROFILES[MONORAIL_KEY], sheet=_n, track_parts=R.power_parts(_susp), cell_fills=R.power_insulator_fills(_susp),
        front_row=4, rise=R.POWER_RISE, snow=False, snow_skin={}, label="E", badge="S" if _susp else None)

# ---------------------------------------------------------------- 基盤の版と壁の way-object（ADR 0003。#16）
# 基盤の版の way（ami_rail_ballast_base_<版>）は、通常の版の道床の下に基盤を敷き、基盤は壁の位置で止まる（壁の無い側はタイルの端まで）。
# 壁そのものは way の絵に描かず、同じ版の壁の way-object（ami_wall_rail_<版>）のシートに描く（sheetlib の wall_sheet）。
# 版の値は sheetlib の walls（both = single）。center は側壁が無く、壁の way-object は行き止まりの端の壁だけ
# （ユーザーの指摘、2026-11-17。架線つきの版では center も架線の部品を持つので、壁の way-object も同じ 4 版にそろえる）
BASE_VARIANTS = {_v: "both" if _v == "single" else _v for _v in catalog.VARIANTS}

# 行き止まりの壁はタイルの末端まで（ユーザーの指摘、2026-11-17）: 側壁を閉じた側のタイルの端まで延ばし、端の壁をタイルの端に立てる。
# レールの終点と車止めは END_FROM_EDGE のまま（タイルの中）
_EDGE_WALLS = {n: dataclasses.replace(p, shape=R.to_edge_shape(p.shape))
               for p in R.TRACK_EXTRAS for n in ("wallL", "wallR") if p.name == n}
_EDGE_WALLS["endw"] = dataclasses.replace(next(p for p in R.TRACK_EXTRAS if p.name == "endw"), name="endw_edge",
                                          shape=R.end_wall_edge_shape())


def _stop_at_end_wall(datum, ref=None):
    """行き止まりの道床を、端の壁の内側の面で止める beyond（sheetlib の bed_to_edge・slab_bed_shape に渡す。d は経路の向き）。
    タイルの外まで延ばすと、基準面の分だけ手前へ動いた道床が、端の壁の外の面の下にのぞいた（#44 の 7 番。2026-11-20）。
    壁（bed）と道床（datum）の動きが違うと（高速線のコンクリート道床は壁の 2 倍下げる）、動いた後の道床の端が、動いた後の壁の内側の面に
    来るよう、動きの差の分だけずらす（カメラの側を向く端では内へ、奥を向く端では外へ）"""
    def beyond(d):
        out = lambda m: m.to_2d().dot(-d.to_2d()) if m is not None else 0.0  # 動きのうち、タイルの外向きの分
        return -R.WALL_W + out(R.datum_move(_DATUMS["bed"] if ref is None else ref)) - out(R.datum_move(datum))
    return beyond


# 壁のある版（基盤・高架・橋）の行き止まりの道床
def _edge_beds(stop, slab_stop):
    """壁のある版の行き止まりの道床（軌道の種類ごと）。stop・slab_stop は _stop_at_end_wall の値（道床・コンクリート道床の基準面ごと）"""
    return {
        catalog.RAIL_BALLAST.key: {"ballast": dataclasses.replace(_old["ballast"], shape=R.bed_to_edge(_BALLAST_SECTION, stop))},
        catalog.RAIL_CONCRETE.key: {"ballast": dataclasses.replace(_old["ballast"], shape=R.bed_to_edge(_CONC_SECTION, stop))},
        catalog.RAIL_LADDER.key: {"ballast": dataclasses.replace(_old["ballast"], shape=R.bed_to_edge(_CONC_SECTION, stop))},
        catalog.RAIL_SLAB.key: {"slab_bed": dataclasses.replace(next(p for p in R.SLAB_TRACK_PARTS if p.name == "slab_bed"),
                                                            shape=R.slab_bed_shape(slab_stop))},
    }


_EDGE_BED = _edge_beds(_stop_at_end_wall(_DATUMS["bed"]), _stop_at_end_wall(_SLAB_DATUMS["slab_bed"]))
# 旧: 道床も壁と同じ基準面（動かさない）なので、基準面の差は 0
_OLD_STOP = _stop_at_end_wall(_OLD_DATUMS["bed"], _OLD_DATUMS["bed"])
_EDGE_BED.update({_k + catalog.OLD: _v for _k, _v in _edge_beds(_OLD_STOP, _OLD_STOP).items()})

for _t in catalog.ALL_TRACKS:
    # 壁の way-object は軌道の種類に属さない共有の物なので、シートは catalog.WALL_TRACK（旧は WALL_TRACK_OLD）の基盤の版だけが書く
    _is_old = _t.key.endswith(catalog.OLD)
    _shared = {} if _t == (catalog.WALL_TRACK_OLD if _is_old else catalog.WALL_TRACK) else {"write_walls": False}
    for _v, _walls in BASE_VARIANTS.items():
        R.TRACK_PROFILES[_p(_t.base(_v))] = dict(
            R.TRACK_PROFILES[_t.key], sheet=_t.base(_v), walls=_walls,
            groups=("body", "base", "weathering", "buffer", "wall"),
            replace=dict(R.TRACK_PROFILES[_t.key].get("replace", {}), **_EDGE_WALLS,
                         **_EDGE_BED.get(_t.key, {})), wall_sheet=catalog.wall_rail(_v, _is_old),
            # カーブのセルを斜めの形で描き、基盤の壁の無い側を削らない（複線の直角の曲がりで、内側の線の外側半分を埋める）
            curve_cells=True,
            # 斜めのタイルの側壁は裏面を描かない。タイルの境で取った壁の切り口から壁の中（暗い）が見え、斜めの階段の下の端の角
            # （斜めの手前の壁と行き止まりの奥の壁の角）に暗い縦線が出た（#63）
            cull_diag_wall_ends=True, **_shared)

# ---------------------------------------------------------------- 架線つきの壁の way-object（ADR 0003。#17）
# 壁の way-object に架線（柱・梁・吊り金具・トロリ線。tools/blender/sheetlib/catenary_parts.py）を足した版（ami_wall_rail_<版>_catenary）。
# center は壁が無く、架線（梁・トロリ線）と行き止まりの端の壁だけ。寸法は catenary_parts の CAT_* にまとめた（値は仮。README の「架線の作り」）。
# 壁は基盤の版と同じ形で描き（groups も同じにする。手前/奥の分け方が本体の重心で決まるため）、way のシートは書かない（wall_only。
# way は基盤の版の対象が書く）。sheet は作業ファイルの名前だけに使い、基盤の版と分ける（同時に描いても work/ のセルが混ざらない）
CATENARY_LABEL = "E"  # 架線つきの壁のアイコンの文字（仮。アイコンはステップ 13 でまとめて作る）
_WT = catalog.WALL_TRACK  # 壁・架線のシートを描く元の軌道
_WALL_TRACKS = ((catalog.WALL_TRACK, False), (catalog.WALL_TRACK_OLD, True))  # 新と旧（#26）
for _w, _wold in _WALL_TRACKS:
    for _v in BASE_VARIANTS:
        _base = R.TRACK_PROFILES[_p(_w.base(_v))]
        R.TRACK_PROFILES[f"{_p(_w.base(_v))}_catenary"] = dict(
            _base, sheet=f"{_w.base(_v)}_cat", wall_sheet=catalog.wall_rail(_v, _wold) + "_catenary",
            groups=_base["groups"] + ("catenary", "catenary_support"), snow=False, wall_only=True, rise=R.CAT_RISE,
            wall_label=CATENARY_LABEL)

# 近い斜めの分け合うタイル用の架線つきの壁（ami_wall_rail_twin_catenary）の絵。壁だけの twin と同じく、nw・sw の線は back、ne・se の線は
# front の版の斜めのセルを使う。斜めの梁だけを短くした（CAT_BEAM_REACH_TWIN。分け合うタイルの隣の線の外の壁からはみ出さない）。
# 通常の 4 版の梁は変えない（斜めの線を隣のタイルに並べた複線・3 本並びで、梁をタイルの角でつなぐため）。dat は斜めのキーだけを指す
TWIN_FROM = ("back", "front")
for _w, _wold in _WALL_TRACKS:
    for _v in TWIN_FROM:
        _cat = R.TRACK_PROFILES[f"{_p(_w.base(_v))}_catenary"]
        R.TRACK_PROFILES[f"{_p(_w.base(_v))}_twin_catenary"] = dict(
            _cat, sheet=f"{_w.base(_v)}_twcat", wall_sheet=f"ami_wall_rail_{'old_' if _wold else ''}twin_catenary_{_v}",
            replace=dict(_cat["replace"], cat_beam=R.beam_part(R.CAT_BEAM_REACH_TWIN)), ex_switches=False)  # dat は斜めのキーだけ

# ---------------------------------------------------------------- 高架の 4 版と橋脚の way（ADR 0003。#18）
# 高架の版の way（ami_rail_ballast_elev_<版>、dat は system_type=1）は、基盤の版と同じ絵（道床・基盤。基盤は壁の位置で止まる）の下に、
# 躯体（桁。sheetlib の ELEV_BODY_*）を足したもの。橋脚は描かない。壁・架線は地上と同じ way-object（ami_wall_rail_*）を重ねるので、
# 壁の way-object のシートは書かない（write_walls）。持ち分は躯体の分だけ下へ広げる（lower）。アイコンは高架の帯
for _t in catalog.ALL_TRACKS:
    for _v in BASE_VARIANTS:
        R.TRACK_PROFILES[_p(_t.elev(_v))] = dict(
            R.TRACK_PROFILES[_p(_t.base(_v))], sheet=_t.elev(_v), write_walls=False, elev_body=True,
            lower=R.ELEV_BODY_LOWER, band="elevated")

# 橋脚の way（ami_pier_rail）: 高架の真下の地面のタイルに敷く。柱の上端は高架の躯体の下面に合わせる（sheetlib の pier_sheet）。
# 基準面は在来線と同じ（高架の床と同じ動かし方）
PIER_LABEL = "P"  # アイコンの文字（仮。アイコンはステップ 13 でまとめて作る）
# 門型の橋脚の way（ami_pier_rail_gate。#18 の追加）: 柱をタイルの角の近くに立て、上に梁を渡す（sheetlib の pier_gate_sheet）
PIER_GATE_LABEL = "G"

# ---------------------------------------------------------------- 橋とトンネル（ADR 0003。#19）
# 橋（ami_rail_ballast_bridge、obj=bridge）: 欄干を描かず、壁・架線は地上と同じ way-object を橋の上に重ねる（橋の 4 版は作らない）。
# 橋は 1 つで、single の壁を重ねる（2026-11-18、ユーザーの決定）。床（基盤）と躯体は高架の single と同じ作りで、壁の外の面で止める
# （壁の外に床の縁が出ない。README の「橋とトンネルの作り」）。端の坂の躯体（rampbody）と坂から始まる端の躯体（build_start_body）も、
# sheetlib の既定で壁の外の面までの幅になる。
# 壁は way-object が描くので、ここでは基盤を削るためだけに置き、シートには書かない（write_walls。高架の版と同じ）。
# セルは blender-poc の橋（track_bridge）と同じ並び: 行 0 の列 2・3 が平らな橋、行 1 が端の坂（Ramp・Ramp2）、行 2 が橋脚、行 3 が坂から始まる端
# （Start・Start2）。手前の絵は無い（欄干が無く、車両より手前に描く物が無い）。雪の絵は 4 行下
BRIDGE_PIER = (R.PIER_SIZE * R.PIER_ACROSS_K, R.PIER_SIZE, R._M_PIER)  # 橋脚の柱（横切る向き × 沿う向き）。高架の単柱の橋脚と同じ太さ
BRIDGE_CELLS = ("ns", "ew", "up12", "up9", "up3", "up6", "up2_12", "up2_9", "up2_3", "up2_6")
for _t in catalog.ALL_TRACKS:
    _bridge_base = R.TRACK_PROFILES[_p(_t.elev("single"))]
    R.TRACK_PROFILES[_p(_t.bridge)] = dict(
        _bridge_base, sheet=_t.bridge, write_walls=False,
        groups=_bridge_base["groups"] + ("ramp",), only=BRIDGE_CELLS, starts=True, piers=True, solid=True,
        pier_box=BRIDGE_PIER, band="bridge", badge=None,
        # 端の坂の躯体の上面を基盤の下へ（低い端の角に躯体がのぞき、雪の絵で灰色の小片になった。#44）
        ramp_body_under_base=True)

# トンネル（ami_rail_ballast_tunnel、obj=tunnel）: blender-poc の坑口（sheetlib の tunnel_sheet。躯体はタイル全体の箱、口は低い側の辺）に、
# 在来線の通常の版の道床（砕石のまだら）・まくらぎ・レール・汚れを入れたもの。壁・架線は坑口のタイルにも way-object を重ねる
# （坑口の躯体は way の手前の絵で、way-object の絵より後に描かれるので、躯体の中へ入る壁・架線は躯体に隠れる。README の「橋とトンネルの作り」）

# ---------------------------------------------------------------- 線路の基盤・高架の面のコンクリート（#78）
# 基盤の板（材質の名前 base）と高架の躯体（elev_body）を、一色から打ち放しのコンクリートにする: 元の色を中心に ±12% のまだら（粒は約 4px。
# 道路一式のコンクリート ROAD_CONCRETE と同じ振れ幅）に、約 30px の大きなしみで最大 15% 暗くする。模様はタイルの 1 辺を周期にしてあり、
# タイルの辺で切れない（sheetlib の tiled_concrete_material）。継ぎ目の線は描かない。段 0〜3 と継ぎ目の案を見比べ、ユーザーが段 2・継ぎ目なしに
# 決めた（2026-11-21。橋もそろえることも同じ日にユーザーが決めた。比べた案は blender/surface_calib.py、記録 docs/records/2026-11-21_ami-surface-detail.md）。
# 線路の基盤・高架の版と橋（床と桁。高架の single と同じ作りで、高架とつながる）に渡す。雪の絵では基盤の上面は雪の材質のまま。
# 線路の壁（材質 wall）・橋脚（pier。門型は柱 pier_post_<角>・梁 pier_beam_<辺>）・橋の柱（pier）・坑口の躯体（wall）も同じ段 2 にする
# （#83。今の絵と並べて見比べ、ユーザーがそろえると決めた。2026-11-21。比べた案は blender/wallpier_calib.py、
# 記録 docs/records/2026-11-21_ami-wall-pier-surface.md）。壁の way-object のシートは基盤の版の対象が書くので、基盤の版の表に wall を入れる
# （way のシートの壁は基盤を削るためだけに置くので、way の絵は変わらない）。道路の壁・橋脚は道路一式のコンクリート（ROAD_MAT_SKIN）のまま
TRACK_SURFACE = dict(amp=0.12, grain=2.5, stain=0.15, stain_scale=0.35)


def _track_concrete(nm, rgb):
    return lambda: R.tiled_concrete_material(f"ami_track_concrete_{nm}", rgb, **TRACK_SURFACE)


TRACK_WALL_SKIN = {R._M_WALL[0]: _track_concrete(*R._M_WALL)}
TRACK_PIER_SKIN = {R._M_PIER[0]: _track_concrete(*R._M_PIER)}
# 門型の橋脚の柱と梁の材質の名前（sheetlib の _gate_parts の角・辺。斜めの片持ちの梁は角の名前）
TRACK_GATE_SKIN = {f"{spec[0]}_{k}": _track_concrete(f"{spec[0]}_{k}", spec[1])
                   for spec, keys in ((R._M_PIER_POST, ("c", "ne", "nw", "se", "sw")),
                                      (R._M_PIER_BEAM, ("n", "s", "e", "w", "ne", "nw", "se", "sw")))
                   for k in keys}
TRACK_MAT_SKIN = {spec[0]: _track_concrete(*spec) for spec in (R._M_BASE, R._M_ELEV_BODY)} | TRACK_WALL_SKIN | TRACK_PIER_SKIN
for _t in catalog.ALL_TRACKS:
    for _v in BASE_VARIANTS:
        for _name in (_t.base(_v), _t.elev(_v)):
            R.TRACK_PROFILES[_p(_name)]["mat_skin"] = TRACK_MAT_SKIN
    R.TRACK_PROFILES[_p(_t.bridge)]["mat_skin"] = TRACK_MAT_SKIN
# 架線つきの壁は基盤の版の描き分けを上で写したもの（mat_skin を持たない）なので、壁の表を渡す
for _w, _ in _WALL_TRACKS:
    for _v in BASE_VARIANTS:
        R.TRACK_PROFILES[f"{_p(_w.base(_v))}_catenary"]["mat_skin"] = TRACK_WALL_SKIN
    for _v in TWIN_FROM:
        R.TRACK_PROFILES[f"{_p(_w.base(_v))}_twin_catenary"]["mat_skin"] = TRACK_WALL_SKIN

# ---------------------------------------------------------------- 道路 3 種の通常の版（#21）
# 断面は blender-poc の高速道路（ROAD_PROFILES["expressway"]）と同じ: 片側 1 車線、タイル全面が路面、歩道なし、路側の白線は実線
# （分岐の口は点線）。描くのは sheetlib の road_sheet（expressway=True が歩道なしの作り）。種類ごとに変えるのは中央線・路面の色・アイコン:
#   center: 中央線。生活道路は無し、一般道路は白の実線、高速道路は白の破線（区切りはタイルの辺。sheetlib の tile_dashes）
#   skin: 路面の色。生活道路・一般道路は blender-poc の街路の灰色（pak128 標準の道路とつなぐ色）、高速道路は blender-poc の
#         高速道路の暗く青みのある色を元にする（走行跡と路肩の雪のぼかしも同じ色から作る。sheetlib の asphalt_skin）。
#         明るさと粒は下の「道路一式の質感」で変えてある
# カーブは 3 種とも斜めの絵（dat の image[sw] などが diagonal と同じセル）。道路の壁（#22）は 3 種で共通の way-object にするので、
# カーブの形を種類でそろえる（README の「道路の作り」）。分岐の絵（switch 画像 1・2）の中身は sheetlib の road_sheet の switch_lines。
# T字の 1・2 は、どちらも枝の無い側を実線でふさいだ T字の形で、違いは轍（走行跡）のカーブの向きだけ（switch_ruts。向きは
# sheetlib の road_parts の SWITCH_RUT_ARCS）。十字の分岐の絵（nsew1・nsew2。固定の道具・詳細ダイアログでだけ選べる）は
# 優先道路のある十字（priority_cross。nsew1 が南北優先、nsew2 が東西優先）。どちらも 2026-11-19、ユーザーの決定
# （README の「道路の作り」）。sheetlib の road_sheet に渡す:
#   DRIVE_LEFT: 優先道路の十字の停止線の通行の側。日本は左側通行。右側通行の版を作るときは偽にしたプロファイルを別に作る
#     （停止線が進入する車線の反対の半分へ移る。今は作らない）（drive_left）
DRIVE_LEFT = True

# 道路一式の質感（精細化のラウンド 1〜3 を本番に入れたもの。#56。値の決め方は docs/records/2026-11-20_ami-road-refine-round1.md〜round3.md、
# 入れ方は 2026-11-20_ami-road-refine-production.md）。どれも AMI の道路一式（道路 3 種とその版・道路の壁・道路用の橋脚・歩道）にだけ渡し、
# sheetlib の既定（blender-poc・在来線・スラブ軌道も使う）は変えない
#   路面: 照り返しを切り（生活道路・一般道路。高速道路はもともと切ってある）、2 色を明るくして（生活道路・一般道路 2.4 倍、高速道路 1.6 倍）
#     平均から 1.4 倍離し、色の段を 0.47〜0.53 に狭めて 1 画素の粒にする。走行跡の寄せ具合は半分（高速道路は 4 分の 1。暗い路面では明るく出る）
ROAD_ASPHALT_LIFT = {"street": 2.4, "expwy": 1.6}
ROAD_ASPHALT_AWAY = 1.4
ROAD_ASPHALT_RAMP = (0.47, 0.53)
ROAD_WEAR_T = {"street": 0.5, "expwy": 0.25}


def _road_asphalt_skin(tag, rgb, spec):
    lifted = tuple(tuple(x * ROAD_ASPHALT_LIFT[tag] for x in c) for c in rgb)
    mean = [(a + b) / 2 for a, b in zip(*lifted)]
    away = lambda c: tuple(max(0.0, m + ROAD_ASPHALT_AWAY * (x - m)) for x, m in zip(c, mean))
    return R.asphalt_skin(f"ami_{tag}", away(lifted[0]), away(lifted[1]), spec=spec, ramp=ROAD_ASPHALT_RAMP,
                          wear_t=ROAD_WEAR_T[tag])


#   コンクリート（壁・基盤・高架の躯体・橋脚。坑口の躯体も壁と同じ材質）: 元の色を中心に ±12% のまだら（Scale 25）にして、打ち放しの肌を出す。
#     どれも形を作る関数の中で material(*組) を呼ぶので、材質の名前で差し替える（sheetlib の road_sheet・tunnel_sheet・pier_sheet の mat_skin）
ROAD_CONCRETE = (0.12, 25.0)
ROAD_MAT_SKIN = {
    spec[0]: (lambda nm=spec[0], rgb=spec[1]: R.noisy_material(
        f"ami_road_concrete_{nm}", tuple(x * (1 - ROAD_CONCRETE[0]) for x in rgb), tuple(x * (1 + ROAD_CONCRETE[0]) for x in rgb),
        scale=ROAD_CONCRETE[1], rough=0.9))
    for spec in (R._M_WALL, R._M_BASE, R._M_ELEV_BODY, R._M_PIER, R._M_PIER_POST, R._M_PIER_BEAM)}
#   雪の歩道・縁石と路肩の雪: 一色の雪（sheetlib の _SNOW）を、地面の雪に合わせて青みの色を中心に ±10% のまだら（Scale 60）と発光 0.15 にする。
#     赤を緑より上にする（青みの明るい粒が透明色 231,255,255 に近づくと sheet_audit の候補になった。docs/reference/way-addon.md の特殊色）
ROAD_SNOW_RGB, ROAD_SNOW_AMP = (0.88, 0.86, 0.97), 0.10
ROAD_SNOW = lambda: R.noisy_material("ami_road_snow", tuple(x * (1 - ROAD_SNOW_AMP) for x in ROAD_SNOW_RGB),
                                     tuple(min(1.0, x * (1 + ROAD_SNOW_AMP)) for x in ROAD_SNOW_RGB), scale=60.0, rough=0.9, emit=0.15)
AMI_ROAD_SNOW_SKIN = {"curb": ROAD_SNOW, "paving": ROAD_SNOW, "snowbank": ROAD_SNOW}
#   歩道の敷石: 灰色の敷石と暗い目地（Brick テクスチャ。敷石が約 6 x 3px）
SIDEWALK_PAVING = lambda: R.brick_material("ami_sidewalk_paving", (0.30, 0.295, 0.28), (0.12, 0.12, 0.115), 0.6)

_ROAD_LOOK = {"mat_skin": ROAD_MAT_SKIN, "snow_skin": AMI_ROAD_SNOW_SKIN}
ROAD_SETTINGS = {
    catalog.ROAD_LOCAL.key: dict(_ROAD_LOOK, label="40", style="road", center=None,
                                 skin=_road_asphalt_skin("street", R.STREET_ASPHALT, 0.0)),
    catalog.ROAD_GENERAL.key: dict(_ROAD_LOOK, label="120", style="road", center="solid",
                                   skin=_road_asphalt_skin("street", R.STREET_ASPHALT, 0.0)),
    catalog.ROAD_EXPRESSWAY.key: dict(_ROAD_LOOK, label="360", style="expressway", center="dash",
                                      skin=_road_asphalt_skin("expwy", R.EXPWY_ASPHALT, 0.0)),
}
for _r in catalog.ROADS:
    R.ROAD_PROFILES[_r.key] = dict({"sheet": _r.way, "prefix": _r.way + "_", "groups": ("body", "marking", "weathering"),
                                    "expressway": True, "switches": True, "switch_ruts": True,
                                    "priority_cross": True, "open_cross": True, "corner_arcs": True,
                                    "drive_left": DRIVE_LEFT}, **ROAD_SETTINGS[_r.key])

# ---------------------------------------------------------------- 道路の壁の way-object・高架の 4 版・橋・トンネル・道路用の橋脚（#22）
# 道路の壁（ami_wall_road_<版>。single・back・center・front。center は側壁が無く、行き止まりの端の壁だけ）: blender-poc の高速道路の壁（sheetlib の road_parts の wallL・wallR・endw。
# iss の都市高速と同じくタイルの端に立つコンクリートの壁）を、way の絵に焼き込まず way-object のシートに分ける（sheetlib の road_sheet の
# wall_sheet）。壁の形は 3 種で同じなので、シートは catalog.WALL_ROAD の道路から 1 回だけ描く（wall_only。way のシートは書かない）。
# 地上は通常の版の way にも重ねられるが、並べた車線の直角の曲がりと近い斜めは、地上の基盤の版（下）と組む
ROAD_WALL_LABEL = "W"  # 道路の壁のアイコンの文字（仮。アイコンはステップ 13 でまとめて作る）
_WR = catalog.WALL_ROAD
for _v in catalog.ROAD_WALL_VARIANTS:
    R.ROAD_PROFILES[f"wall_road_{_v}"] = dict(
        R.ROAD_PROFILES[_WR.key], sheet=f"ami_wall_road_{_v}_way", prefix=f"ami_wall_road_{_v}_", walls=BASE_VARIANTS[_v],
        groups=R.ROAD_PROFILES[_WR.key]["groups"] + ("wall",), wall_sheet=f"ami_wall_road_{_v}", wall_only=True,
        wall_label=ROAD_WALL_LABEL)
# 中央分離帯つきの壁（ami_wall_road_<front|center>_divider。#118）: 壁の way-object と同じ作りに、側壁の位置に立つ縁石の帯とガードレール
# （sheetlib の road_parts の median_*）を足す。分離帯は奥の側の 1 本だけが残る（select_walls）。4 車線の手前のタイルに重ねる
ROAD_DIVIDER_LABEL = "D"  # 描画のアイコンの文字（ゲームのアイコンは icons.py が書き直す）
for _v, _name in catalog.ROAD_DIVIDERS.items():
    R.ROAD_PROFILES[f"wall_road_{_v}_divider"] = dict(
        R.ROAD_PROFILES[f"wall_road_{_v}"], sheet=f"{_name}_way", prefix=f"{_name}_",
        groups=R.ROAD_PROFILES[f"wall_road_{_v}"]["groups"] + ("median",), wall_sheet=_name, wall_label=ROAD_DIVIDER_LABEL)

# 地上の基盤の版（<道路>_base_<版>。2026-11-19 にユーザーが確定）: 通常の版の路面から壁の外を削り、カーブのセルを斜めの形で描いて
# 壁の無い側をタイルの端まで延ばす（curve_cells。並べた車線の直角の曲がりで、内側の線との間に草の三角が出ない）。
# 近い斜めの絵を持たない（本体が分け合うタイルに way を 2 本置き、ami_wall_road_twin を重ねられる。線路の基盤の版と同じ）。
# 壁は way-object（ami_wall_road_<版>）を重ねるので、壁のシートは書かない
for _r in catalog.ROADS:
    for _v, _walls in BASE_VARIANTS.items():
        R.ROAD_PROFILES[_p(_r.base(_v))] = dict(
            R.ROAD_PROFILES[_r.key], sheet=_r.base(_v), prefix=_r.base(_v) + "_", walls=_walls,
            groups=R.ROAD_PROFILES[_r.key]["groups"] + ("wall",), wall_sheet=f"ami_wall_road_{_v}", write_walls=False,
            curve_cells=True)

# 高架の 4 版（<道路>_elev_<版>、dat は system_type=1）: 床（路面と基盤）と躯体だけ。橋脚は描かない（道路用の橋脚の way が描く）。
# 基盤は壁の外の面で止まり、壁の無い側はタイルの端まで（線路の高架と同じ）。躯体は壁のある側で壁の外の面から ELEV_BODY_INSET 内で止める。
# 壁は地上と同じ way-object（ami_wall_road_<版>）を重ねるので、壁のシートは書かない（write_walls）。
# 持ち分は基盤と躯体の分だけ下へ広げる（道路の基盤は路面の板の下へ ROAD_BASE_DROP 下げてあるので、線路の ELEV_BODY_LOWER より深い）
ROAD_ELEV_LOWER = math.ceil((R.BASE_H + R.ELEV_BODY_D + R.ROAD_BASE_DROP) * 16 / R.H) + 2
for _r in catalog.ROADS:
    for _v, _walls in BASE_VARIANTS.items():
        R.ROAD_PROFILES[_p(_r.elev(_v))] = dict(
            R.ROAD_PROFILES[_r.key], sheet=_r.elev(_v), prefix=_r.elev(_v) + "_", walls=_walls,
            groups=R.ROAD_PROFILES[_r.key]["groups"] + ("wall",), wall_sheet=f"ami_wall_road_{_v}", write_walls=False,
            elevated=True, elev_body=True, lower=ROAD_ELEV_LOWER, band="elevated", curve_cells=True)

# 橋（<道路>_bridge）: 欄干を描かず、single の壁の way-object を重ねる（線路の橋と同じ）。床・躯体の高さは高架にそろえる。
# 桁（POC の C6。見せ方は 2026-11-19 にユーザーが確定）: iss の都市高速の橋（../refs/iss/src/bridge/road/bridge.dat の iss_br_0120_bridge1）と同じく、床の縁の下に青い鋼の帯を見せる。
# 基盤（BASE_H）と、その下の桁（ROAD_GIRDER_D）を青くし、壁の外の面まで出す（躯体のように内へ下げない）。
# iss の帯は 256px のセルで 4px（../refs/iss/release/pak128/bridge/road/0120_bridge1.png の NS のセル。2026-11-19 に測った）。
# 床の下を描くため、平らなセルは高架と同じだけ持ち分を下へ広げる（端の坂と坂から始まる端は広げない。sheetlib の road_sheet）
ROAD_GIRDER_D = 0.15  # 桁の深さ（基盤の下面から）。基盤と合わせて約 4px
# 橋脚: 道の全幅（両側の壁の下）まで横切る柱（blender-poc の高速道路の橋・高架と同じ考え方。床がタイルいっぱいなので、中央だけの柱は床に隠れる）
ROAD_PIER_ACROSS = 2 * R.EXPWY_WALL_U
ROAD_BRIDGE_PIER = (ROAD_PIER_ACROSS, R.PIER_SIZE, R._M_PIER)
for _r in catalog.ROADS:
    _single = R.ROAD_PROFILES[_p(_r.elev("single"))]
    R.ROAD_PROFILES[_p(_r.bridge)] = dict(
        _single, sheet=_r.bridge, prefix=_r.bridge + "_", elevated=False, bridge=True, solid=True, starts=True, piers=True,
        groups=_single["groups"] + ("ramp",), only=BRIDGE_CELLS, base_mat=R._M_GIRDER, body_mat=R._M_GIRDER, body_inset=0.0,
        body_d=ROAD_GIRDER_D, pier_box=ROAD_BRIDGE_PIER, band="bridge")

# ---------------------------------------------------------------- 対象（シート名 → 描く関数）
# 基盤の版の対象は、way のシートと壁の way-object のシートを 1 つのプロセスで描く


def _track_target(profile):
    return lambda: R.track_sheet(profile)


def _tunnel_target(track):
    return lambda: R.tunnel_sheet("track", profile=track.key, sheet=track.tunnel, label=R.TRACK_PROFILES[track.key]["label"],
                                  mat_skin=TRACK_WALL_SKIN)


SHEETS = {_t.way: _track_target(_t.key) for _t in catalog.ALL_TRACKS}
SHEETS[catalog.TRAM] = _track_target(TRAM_KEY)
SHEETS[catalog.MONORAIL] = _track_target(MONORAIL_KEY)
for _n in catalog.MONORAIL_ELEVS:
    SHEETS[_n] = _track_target(catalog.profile(_n))
for _n in catalog.MONORAIL_SUSPENDEDS + catalog.MONORAIL_SUSPENDED_ELEVS + tuple(catalog.MONORAIL_POWERS):
    SHEETS[_n] = _track_target(catalog.profile(_n))
SHEETS[catalog.MONORAIL_TUNNEL] = lambda: R.tunnel_sheet("track", profile=MONORAIL_KEY, sheet=catalog.MONORAIL_TUNNEL, label=MONORAIL_LABEL,
                                                          mat_skin=TRACK_WALL_SKIN)
for _t in catalog.ALL_TRACKS:
    for _v in BASE_VARIANTS:
        SHEETS[_t.base(_v)] = _track_target(_p(_t.base(_v)))
for _w, _wold in _WALL_TRACKS:
    for _v in BASE_VARIANTS:
        SHEETS[catalog.wall_rail(_v, _wold) + "_catenary"] = _track_target(f"{_p(_w.base(_v))}_catenary")
    for _v in TWIN_FROM:
        SHEETS[f"ami_wall_rail_{'old_' if _wold else ''}twin_catenary_{_v}"] = _track_target(f"{_p(_w.base(_v))}_twin_catenary")
for _t in catalog.ALL_TRACKS:
    for _v in BASE_VARIANTS:
        SHEETS[_t.elev(_v)] = _track_target(_p(_t.elev(_v)))
# 橋脚（旧描画位置の物は基準面を動かさない。#26）
for _old_pier, _pier_datums in ((False, _DATUMS), (True, _OLD_DATUMS)):
    SHEETS[catalog.pier_rail(False, _old_pier)] = (lambda n, d: lambda: R.pier_sheet(n, d, label=PIER_LABEL, mat_skin=TRACK_PIER_SKIN))(
        catalog.pier_rail(False, _old_pier), _pier_datums)
    SHEETS[catalog.pier_rail(True, _old_pier)] = (lambda n, d: lambda: R.pier_gate_sheet(n, d, label=PIER_GATE_LABEL, mat_skin=TRACK_GATE_SKIN))(
        catalog.pier_rail(True, _old_pier), _pier_datums)
for _t in catalog.ALL_TRACKS:
    SHEETS[_t.bridge] = _track_target(_p(_t.bridge))
    SHEETS[_t.tunnel] = _tunnel_target(_t)
_road_target = lambda key: lambda: R.road_sheet(key)
for _r in catalog.ROADS:
    SHEETS[_r.way] = _road_target(_r.key)
# 多車線と交差点の路面表示の way（#187。ADR 0012）: 一般道路に重ねて敷く白線と路面の way（sheetlib の marking_sheet）。
# 路面は一般道路のアスファルトと同じ材質（MARKING_PAVING。走行跡は描かない）
MARKING_LABEL = "M"  # 描画のアイコンの文字（ゲームのアイコンは icons.py が書き直す）
MARKING_PAVING = ROAD_SETTINGS[catalog.ROAD_GENERAL.key]["skin"]["asphalt"]
# 高速道路の分岐・合流（#188）は、高速道路のアスファルト（MARKING_EXPWY_PAVING）
MARKING_EXPWY_PAVING = ROAD_SETTINGS[catalog.ROAD_EXPRESSWAY.key]["skin"]["asphalt"]
for _name, _kind in catalog.MARKINGS.items():
    _paving = MARKING_EXPWY_PAVING if _name in catalog.MARKINGS_EXPWY else MARKING_PAVING
    SHEETS[_name] = (lambda n, k, pv: lambda: R.marking_sheet(n, k, label=MARKING_LABEL, paving=pv, snow=ROAD_SNOW))(_name, _kind, _paving)
for _v in catalog.ROAD_WALL_VARIANTS:
    SHEETS[f"ami_wall_road_{_v}"] = _road_target(f"wall_road_{_v}")
for _v, _name in catalog.ROAD_DIVIDERS.items():
    SHEETS[_name] = _road_target(f"wall_road_{_v}_divider")
for _r in catalog.ROADS:
    for _v in BASE_VARIANTS:
        SHEETS[_r.base(_v)] = _road_target(_p(_r.base(_v)))
        SHEETS[_r.elev(_v)] = _road_target(_p(_r.elev(_v)))
    SHEETS[_r.bridge] = _road_target(_p(_r.bridge))
    # トンネル: 坑口は blender-poc の高速道路のトンネル（iss の都市高速の坑口が手本）で、路面・白線は道路の種類ごと。
    SHEETS[_r.tunnel] = (lambda r: lambda: R.tunnel_sheet("expressway", sheet=r.tunnel, road_profile=R.ROAD_PROFILES[r.key]))(_r)
# 道路用の橋脚の way（ami_pier_road）: 高架の道路の真下の地面に敷く。柱は道の全幅を横切り（ROAD_PIER_ACROSS。斜めは 1/√2）、
# 上端は道路の高架の躯体の下面に合わせる。絵の位置・持ち分は道路と同じ（ROAD_CY）
SHEETS[catalog.PIER_ROAD] = lambda: R.pier_sheet(catalog.PIER_ROAD, R.FLAT, label=PIER_LABEL, across=ROAD_PIER_ACROSS,
                                                 anchor=R.ROAD_CY, cy=R.ROAD_CY, top_drop=R.ROAD_BASE_DROP, diag_k=R.DIAG_EDGE,
                                                 style="road", mat_skin=ROAD_MAT_SKIN)
# 歩道の way（ami_sidewalk）: 道路の隣のタイルに敷く。絵は自分のつながりだけで決まる（sheetlib の sidewalk_sheet）。
# 絵の位置・持ち分は道路と同じ（ROAD_CY）
SIDEWALK_LABEL = "S"  # アイコンの文字（仮。アイコンはステップ 13 でまとめて作る）
# 運河の way（ami_canal。#114）: 水面・護岸・笠石（sheetlib の canal_sheet）。カーブは斜めの絵
CANAL_LABEL = "60"
SHEETS[catalog.CANAL] = lambda: R.canal_sheet(catalog.CANAL, label=CANAL_LABEL)
SHEETS[catalog.CANAL_SCENIC] = lambda: R.canal_sheet(catalog.CANAL_SCENIC, label=CANAL_LABEL, variant="scenic")  # 景観の運河（#161）。閘門つきの坂
SHEETS[catalog.SIDEWALK] = lambda: R.sidewalk_sheet(catalog.SIDEWALK, label=SIDEWALK_LABEL, paving=SIDEWALK_PAVING, snow=ROAD_SNOW)
# 歩道の種類（ami_sidewalk_<舗装>。#119）: 形は ami_sidewalk と同じで、敷石の材質だけが違う。目地の模様の違い（やはず張りなど）は
# 敷石が約 6 x 3px の画面では見分けられないので、色と材質で分ける（2026-11-21、#119 で作業者が決めた。ユーザーが PR で確かめる）
#   asphalt: アスファルト舗装（道路の路面より明るい灰色のまだら） / brick: 赤れんが色のインターロッキングブロック / tile: ベージュの平板（敷石が大きい）
SIDEWALK_PAVINGS = {
    "asphalt": lambda: R.noisy_material("ami_sidewalk_asphalt", (0.045, 0.046, 0.048), (0.085, 0.086, 0.088), scale=60, rough=0.9,
                                        ramp=(0.47, 0.53)),
    "brick": lambda: R.brick_material("ami_sidewalk_brick", (0.30, 0.10, 0.06), (0.11, 0.08, 0.07), 0.6),
    "tile": lambda: R.brick_material("ami_sidewalk_tile", (0.44, 0.38, 0.28), (0.17, 0.15, 0.12), 0.35),
}
for _pv in catalog.SIDEWALK_PAVINGS:
    SHEETS[catalog.sidewalk(_pv)] = (lambda pv: lambda: R.sidewalk_sheet(catalog.sidewalk(pv), label=SIDEWALK_LABEL,
                                                                        paving=SIDEWALK_PAVINGS[pv], snow=ROAD_SNOW))(_pv)
# 高架の歩道（ami_sidewalk_elev）: 敷石は ami_sidewalk と同じ。板の下に、道路の高架と同じ深さの基盤と躯体（材質も道路の高架と同じ）。
# 柱は描かない（道路用の橋脚 ami_pier_road を真下に敷く。上端は道路の高架の躯体の下面で、深さが同じなので合う）
SHEETS[catalog.SIDEWALK_ELEV] = lambda: R.sidewalk_sheet(catalog.SIDEWALK_ELEV, label=SIDEWALK_LABEL, paving=SIDEWALK_PAVING,
                                                         snow=ROAD_SNOW, elevated=True, mat_skin=ROAD_MAT_SKIN)
# 歩道の柵（ami_wall_sidewalk_<版>。#119）: 歩道の板の縁（つながらない辺）に立てる白い鋼の柵の way-object（sheetlib の sidewalk_fence_sheet）
for _v in catalog.SIDEWALK_WALL_VARIANTS:
    SHEETS[catalog.sidewalk_wall(_v)] = (lambda v: lambda: R.sidewalk_fence_sheet(catalog.sidewalk_wall(v), v))(_v)
# 電柱（ami_sidewalk_pole_<版> と、柵つきの ami_wall_sidewalk_<版>_pole。#120）: 毎タイルの柱と、つながる向きの電線（sheetlib の sidewalk_pole_sheet）
for _n, (_v, _f) in catalog.SIDEWALK_POLES.items():
    SHEETS[_n] = (lambda n, v, f: lambda: R.sidewalk_pole_sheet(n, v, fence=f))(_n, _v, _f)

# 盛土の way（#123）: 高架の脇の地面に敷く法面の楔（sheetlib の embankment_sheet）。法面は芝の土（2026-11-21、ユーザーの決定。#123）。
# 芝は 2 色のまだら（EMBANKMENT_GRASS の暗い色・明るい色・細かさ）、雪の絵は雪のまだら
EMBANKMENT_GRASS = ((0.086, 0.315, 0.03), (0.185, 0.59, 0.07), 30.0)  # ゲームの草地（画面で約 80,147,53）に合わせた
EMBANKMENT_SNOW = ((0.80, 0.84, 0.90), (0.92, 0.95, 0.99), 30.0)
_emb_skin = lambda nm, spec: {R.EMBANKMENT_MAT[0]: lambda: R.noisy_material(nm, spec[0], spec[1], scale=spec[2], rough=0.95)}
for _name, _side in catalog.EMBANKMENTS.items():
    SHEETS[_name] = (lambda n, s: lambda: R.embankment_sheet(n, s, mat_skin=_emb_skin("ami_embankment_grass", EMBANKMENT_GRASS),
                                                             snow_skin=_emb_skin("ami_embankment_snow", EMBANKMENT_SNOW)))(_name, _side)

# 踏切（#111）: 道路の種類ごとに 1 枚（線路の 4 種で共有）。奥の絵の下地に、その道路の直線のセルを写すので、道路のシートの後に描く
# （SHEETS の登録順に描く。別の Blender で並べて描くときは、道路のシートを先に描き終えておく）。
# レールと踏板は線路の way と同じ基準面（_DATUMS の rail。4 種で同じ）。レールの横の範囲と上面の高さ（踏板の上面）も線路と同じ値を渡す（#129）
for _r in catalog.ROADS:
    SHEETS[catalog.crossing_sheet(_r)] = (lambda r: lambda: R.crossing_sheet(catalog.crossing_sheet(r), r.way + ".png", _DATUMS,
                                                                                    rail=(RAIL_IN, RAIL_OUT, RAIL_Z1)))(_r)

# 水路の踏切（#117）: 跳ね橋。道路の種類ごとに 1 枚と、線路の 4 種で共通の 1 枚（sheetlib の canal_crossing.py）。奥の絵の下地に運河の直線のセル
# （道路は道路の直線のセルも）を写すので、運河・道路のシートの後に描く。線路のレールは線路の way と同じ基準面・横の範囲・高さ（線路×道路の踏切と同じ）
for _r in catalog.ROADS:
    SHEETS[catalog.canal_crossing_sheet(_r)] = (lambda r: lambda: R.canal_crossing_sheet(
        catalog.canal_crossing_sheet(r), catalog.CANAL + ".png", "road", road_sheet=r.way + ".png"))(_r)
SHEETS[catalog.CANAL_CROSSING_RAIL_SHEET] = lambda: R.canal_crossing_sheet(
    catalog.CANAL_CROSSING_RAIL_SHEET, catalog.CANAL + ".png", "rail", datums=_DATUMS, rail=(RAIL_IN, RAIL_OUT, RAIL_Z1))

# 車庫（#112）: 種類ごとに 1 枚。形と寸法は sheetlib の depot.py（DEPOT_SHAPES）
for _d in catalog.DEPOTS:
    SHEETS[_d.name] = (lambda d: lambda: R.depot_sheet(R.sheet_path(d.name + ".png"), d.kind, R.WORK))(_d)
# 操車場（#115）: 線路の脇の構内通路。形と寸法は sheetlib の yard.py
SHEETS[catalog.RAIL_YARD] = lambda: R.yard_sheet(R.sheet_path(catalog.RAIL_YARD + ".png"), R.WORK)

# 道路標識（#122）: 標識ごとに 1 枚。柱を描き、板の 2D の絵を押す（sheetlib の roadsign.py）
for _n, _k in catalog.ROADSIGNS.items():
    SHEETS[_n] = (lambda n, k: lambda: R.roadsign_sheet(R.sheet_path(n + ".png"), k, R.WORK))(_n, _k)

# 路面の横断歩道の標識（#162）: 柱も板も無く、縞と停止線だけ（sheetlib の roadsign.py）
for _n, _o in catalog.ROADSIGN_CROSSWALKS.items():
    SHEETS[_n] = (lambda n, o: lambda: R.crosswalk_sign_sheet(R.sheet_path(n + ".png"), o, R.WORK))(_n, _o)

if __name__ == "__main__":
    R.run_targets(SHEETS, list(SHEETS))
    # アイコン・カーソル（#25）: 描いたシートの絵から作り、シートのセルに書く（blender/icons.py）。LAYOUT・ONLY の出力（work/）には書かない
    if not (R.LAYOUT or R.ONLY):
        import icons
        _args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        icons.run_in_new_blender([a for a in _args if a in SHEETS] or list(SHEETS))
