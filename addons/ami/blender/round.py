"""精細化のラウンド（#56）の版を作る。名前は元の名前の末尾に _round<n> を付け、今の版と同じゲームに並べて比べる。

アドオンのディレクトリで:

    AMI_ROUND=1 python -X utf8 ../../tools/blender/render_parallel.py --entry blender/round.py <対象 ...>   # 描く（対象は ROUND_TARGETS）
    python -X utf8 blender/round.py 1     # 描いたシートから dat を書き、rounds/ami_round1.pak を作る（Blender を使わない）
    python -X utf8 blender/round.py 0     # ラウンド 0（今の src/ をそのまま）の pak を作る

対象は在来線一式（ROUND_TARGETS）。描いた絵は work/rounds/round<n>/src/ に置き、src/・dist/ は変えない。
描かなかったシート（ラウンド 0 の全部、ラウンドで変えない絵）は src/ のものを使う。
dat は src/ のものを写し、ami_ で始まる名前を全部 _round<n> 付きにする（画像の参照・トンネルの way= も）。
ラウンドごとの描き分けは ROUND_SETTINGS（render.py の設定の上に重ねる）。
ラウンド 8（2026-11-20）で、ラウンド 7 の描き分けを render.py（と共有の sheetlib）に入れた。ROUND_SETTINGS の 1〜7 は、入れる前の
render.py に重ねる値として残してある（記録のため）。今の render.py に重ねると二重にかかるので、そのまま描き直さない。
次のラウンドを回すときは、今の render.py を土台にした設定を新しく足す。今の render.py はまくらぎの形を間隔ごと束ねて作るので、
cfg の sleeper_pitch（TP.SLEEPER_PITCH の書き換え）は効かない。間隔を変えるときは sleeper の部品を作り直す。

系統（family）: 在来線一式のほかの系統は、環境変数 AMI_FAMILY で選ぶ（FAMILIES。既定は rail_ballast）。
系統ごとの描き分けは blender/round_<系統>.py の ROUND_SETTINGS と apply(cfg, n, R, render)（render.py の設定の上に重ねる）。
描いた絵は work/rounds/<系統>/round<n>/src/、pak は rounds/ami_<系統>_round<n>.pak（rail_ballast だけは前からの名前のまま）。

    AMI_FAMILY=road AMI_ROUND=1 python -X utf8 ../../tools/blender/render_parallel.py --entry blender/round.py <対象 ...>
    AMI_FAMILY=road python -X utf8 blender/round.py 1
    AMI_FAMILY=road python -X utf8 blender/round.py --targets   # その系統の描く対象を出す
"""
import fnmatch
import importlib
import glob
import os
import re
import shutil
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
BALLAST = "ami_rail_ballast"

# 在来線一式の dat（src/ の名前）と、描く対象（render.py の SHEETS の名前）
ROUND_DATS = ("ami_rail_ballast", "ami_rail_ballast_base_*", "ami_rail_ballast_elev_*", "ami_rail_ballast_bridge",
              "ami_rail_ballast_tunnel", "ami_wall_rail_*", "ami_pier_rail", "ami_pier_rail_gate")
ROUND_TARGETS = (["ami_rail_ballast"] + [f"ami_rail_ballast_base_{v}" for v in ("single", "back", "center", "front")]
                 + [f"ami_wall_rail_{v}_catenary" for v in ("single", "back", "center", "front")]
                 + [f"ami_wall_rail_twin_catenary_{v}" for v in ("back", "front")]
                 + [f"ami_rail_ballast_elev_{v}" for v in ("single", "back", "center", "front")]
                 + ["ami_pier_rail", "ami_pier_rail_gate", "ami_rail_ballast_bridge", "ami_rail_ballast_tunnel"])

# 系統 → pak に入れる dat（src/ の名前。glob）と描く対象（render.py の SHEETS の名前。glob）。
# pak には、見本が _round<n> の名前で引く物を全部入れる（描かなかったシートは src/ のものを写す）。
# 在来線の壁・架線・橋脚は rail_ballast のラウンドで描いた物で、rail_slab の pak には src/ のまま入れる（スラブ軌道の見本 sample.nut が引くため）。
FAMILIES = {
    "rail_ballast": {"dats": ROUND_DATS, "targets": ROUND_TARGETS, "module": None},
    "rail_slab": {"dats": ("ami_rail_slab", "ami_rail_slab_base_*", "ami_rail_slab_elev_*", "ami_rail_slab_bridge",
                           "ami_rail_slab_tunnel", "ami_wall_rail_*", "ami_pier_rail", "ami_pier_rail_gate"),
                  "targets": ("ami_rail_slab", "ami_rail_slab_*"), "module": "round_rail_slab"},
    "tram": {"dats": ("ami_tram",), "targets": ("ami_tram",), "module": "round_tram"},
    "road": {"dats": ("ami_road_*", "ami_wall_road_*", "ami_pier_road", "ami_sidewalk"),
             "targets": ("ami_road_*", "ami_wall_road_*", "ami_pier_road", "ami_sidewalk"), "module": "round_road"},
}
FAMILY = os.environ.get("AMI_FAMILY", "rail_ballast")
if FAMILY not in FAMILIES:
    sys.exit(f"[round] AMI_FAMILY は {' '.join(FAMILIES)} のどれか: {FAMILY}")


# ラウンド → 描き分け。ballast: 砕石のまだら（明暗差の倍率, 細かさ）。wear: 汚れの色を道床の色から離す倍率。
# sleeper_pitch: まくらぎの間隔。値の決め方は記録 docs/records/ の各ラウンドの記録
ROUND_SETTINGS = {
    "1": {"ballast": (2.4, 12.0), "wear": 1.8, "sleeper_pitch": 0.54},
}
# ラウンド 2 は構造の試し（#56）: 意味の木の葉を 1 つずつ入り切りする。base は 1 のまくらぎの間隔の継ぎ目の欠陥（タイルの端で間があく）を直したもの。
# 葉: head（レールの頭頂面の磨かれた帯）、head_x（それに加えてレールを太く高く誇張）、fasten（締結装置）、joint（継目）
_R2 = dict(ROUND_SETTINGS["1"], sleeper_pitch=10 / 18, sleeper_align=True)
_R3 = dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.41, 0.55, 0.30), rail_rgb=(0.30, 0.19, 0.15), embed=True)
ROUND_SETTINGS.update({
    "2base": _R2,
    "2head": dict(_R2, rail_head=True),
    "2headx": dict(_R2, rail_head=True, rail_size=(0.40, 0.56, 0.36)),
    "2fasten": dict(_R2, fasten=True),
    "2joint": dict(_R2, joint=True),
    # headx2: 頭を手本（iss・pak128）ほどに明るく、側面を暗くして、レールを 2 色の線にする。embed: まくらぎの間を道床の砕石で埋める
    "2headx2": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.39, 0.57, 0.40), rail_rgb=(0.30, 0.19, 0.15)),
    "2embed": dict(_R2, embed=True),
    "2": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.39, 0.57, 0.40), rail_rgb=(0.30, 0.19, 0.15), embed=True),
    # jointx: 2 の上に、継目を誇張して置く（明るい頭を約 1px の暗い遊間で切り、継目板を長くする）
    "2jointx": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.39, 0.57, 0.40), rail_rgb=(0.30, 0.19, 0.15), embed=True,
                    joint=(0.9, 0.16)),
    # ラウンド 3: 2 のレールの暗い側面が 2〜3px で重い（pak128 は 1px）。高さの誇張を減らし、側面を 1px にする。頭は 1px のまま
    #   3a: 高さを元（0.11）に戻す。3b: 少しだけ高く（0.14）。3c: 3a の頭を少し暗く（0.80）。3d: 3a の側面を明るく（元のさび色）
    "3a": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.39, 0.57, 0.30), rail_rgb=(0.30, 0.19, 0.15), embed=True),
    "3b": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.39, 0.57, 0.33), rail_rgb=(0.30, 0.19, 0.15), embed=True),
    "3c": dict(_R2, rail_head=(0.80, 0.79, 0.76), rail_size=(0.39, 0.57, 0.30), rail_rgb=(0.30, 0.19, 0.15), embed=True),
    "3d": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.39, 0.57, 0.30), embed=True),
    # 3e・3f: 3a・3d は幅 0.18 で頭が 2px に広がる所があるので、幅を 0.14 に戻す（3e は側面が元のさび色、3f は暗いさび色）
    "3e": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.41, 0.55, 0.30), embed=True),
    "3f": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.41, 0.55, 0.30), rail_rgb=(0.30, 0.19, 0.15), embed=True),
    "3": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.41, 0.55, 0.30), rail_rgb=(0.30, 0.19, 0.15), embed=True),  # = 3f
    # ラウンド 4: まくらぎと道床。3 ではレールの間のまくらぎの間が 50〜70 とほぼ黒く、まくらぎ（約 160）と梯子の模様になった。
    # 原因は油の帯（oil。ほぼ黒に寄せ、さらにラウンド 1 の wear 1.8 で離した）。油の濃さ・色・有無を試す
    #   4oil35: 寄せ具合 0.70 → 0.35、離す倍率 1.0。4oiloff: 油の帯なし。4dust: 油の代わりに制輪子の粉（さびの色）を 0.5。4wear1: 4oil35 + さびの帯も離す倍率 1.0
    "4oil35": dict(_R3, wear_t={"oil": 0.35}, wear_k={"oil": 1.0}),
    "4oiloff": dict(_R3, drop=("oil",)),
    "4dust": dict(_R3, wear_rgb={"oil": ((0.26, 0.21, 0.16), (0.36, 0.30, 0.23))}, wear_t={"oil": 0.5}, wear_k={"oil": 1.0}),
    # 油を薄くするとまくらぎが砂利に溶ける（まくらぎ 165・砂利 135）。まくらぎを明るい PC（コンクリート）の色にして見せる
    #   4mid: 油を 0.5（中くらいの暗さ）。4light: 4oil35 + まくらぎを明るく。4lightmid: 4mid + まくらぎを明るく
    "4mid": dict(_R3, wear_t={"oil": 0.5}, wear_k={"oil": 1.0}),
    "4light": dict(_R3, wear_t={"oil": 0.35}, wear_k={"oil": 1.0}, sleeper_rgb=((0.66, 0.65, 0.62), (0.78, 0.77, 0.74))),
    "4lightmid": dict(_R3, wear_t={"oil": 0.5}, wear_k={"oil": 1.0}, sleeper_rgb=((0.66, 0.65, 0.62), (0.78, 0.77, 0.74))),
    "4": dict(_R3, wear_t={"oil": 0.5}, wear_k={"oil": 1.0}, sleeper_rgb=((0.66, 0.65, 0.62), (0.78, 0.77, 0.74))),  # = 4lightmid
    # ラウンド 5: 道床と床（高架・基盤の版）。4 でまくらぎが明るくなり、線路の帯が床（明るい灰色）と同じ明るさに溶けた。
    #   5shoulder: 道床の形を実物の「肩とのり面」にする（まくらぎの上面の高さの平らな肩を外へ延ばし、そこから床まで斜面）。
    #   5dark: 砕石を暗く（使い込んだ砕石は濃い灰色）。5deck: 床（基盤）のコンクリートを雨だれでくすんだ色に。
    "5shoulder": dict(_R4 := dict(_R3, wear_t={"oil": 0.5}, wear_k={"oil": 1.0},
                                  sleeper_rgb=((0.66, 0.65, 0.62), (0.78, 0.77, 0.74))), shoulder=1.45),
    "5dark": dict(_R4, ballast_dark=0.82),
    "5deck": dict(_R4, deck_rgb=(0.40, 0.40, 0.38)),
    "5shdark": dict(_R4, shoulder=1.45, ballast_dark=0.82),
    "5": dict(_R4, shoulder=1.45, ballast_dark=0.82),  # = 5shdark
    # ラウンド 6: 雪の絵。今は、道床の雪の上に汚れた雪の帯（灰色）と、まくらぎのかすかな梯子が出て、線路の帯が灰色の板に見える。
    #   6clean: 積もったばかりの雪（汚れの帯もまくらぎも雪の色。レールだけが出る）。6rut: レールの脇だけが汚れる（車輪の通る所）。
    #   6plow: 除雪の後（まくらぎの上面が出て、まくらぎの間は汚れた雪）
    "6clean": dict(_R5 := dict(_R4, shoulder=1.45, ballast_dark=0.82), snow_mode="clean"),
    "6rut": dict(_R5, snow_mode="rut"),
    "6plow": dict(_R5, snow_mode="plow"),
    "6": dict(_R5, snow_mode="clean"),  # = 6clean
    # ラウンド 7: 残りの葉をまとめて試す。
    #   雪の縁: 道床の雪（明るさ約 211）が地面の雪（約 229）より暗く、線路の帯の縁が残る。7snow: 道床の雪を地面の雪の色（0.89, 0.89, 0.94）を
    #     元に明るくする（同じ雪）。7snow2: さらに明るく
    #   斜めのレールの白い線: 7dh: 斜めのセルだけ、頭の明るい帯の幅を半分にする（直線では 1px に満たない帯が、斜めでは 1 列を埋める）
    #   レールの点線（雪の孤立点）: 手前のレールの暗い側面が 1 行に 1px で、点線になる。7rail: レールを内へ 0.01 太くする
    #   高架の端の段（#44 の 7 番）の切り分け: 7nobody: 躯体を描かない
    "7snow": dict(_R6 := dict(_R5, snow_mode="clean"), snow_rgb=(0.97, 0.97, 1.0)),
    "7snow2": dict(_R6, snow_rgb=(1.0, 1.0, 1.0)),
    "7snow3": dict(_R6, snow_rgb=(0.945, 0.945, 1.0)),  # 地面の雪と同じ青み（青 / 赤 = 1.057）
    "7dh": dict(_R6, diag_head=0.5),
    "7rail": dict(_R6, rail_size=(0.40, 0.55, 0.30)),
    "7railb": dict(_R6, rail_size=(0.41, 0.56, 0.30)),
    "7railc": dict(_R6, rail_size=(0.42, 0.55, 0.30)),
    "7raild": dict(_R6, rail_size=(0.41, 0.54, 0.30)),
    "7raile": dict(_R6, rail_size=(0.42, 0.56, 0.30)),
    "7nobody": dict(_R6, no_body=True),
    # 7endtrim: 7nobody でも段が残った（躯体ではなく基盤）。基盤を削る位置を内へ下げると段が消える（0.6 では壁の下に 1px のへこみ、0.3 でそろう）
    "7endtrim": dict(_R6, end_trim=0.6),
    "7endtrim3": dict(_R6, end_trim=0.3),
    # 7rail〜7raile: レールの幅を 0.01 ずつ動かすと、点線が南北と東西の直線の間で移るだけで、合計は 6 より減らない → 採らない
    # ラウンド 7: 6 + 道床の雪を地面の雪の青みで明るく（7snow3。7snow2 の白は地面の雪の横で黄ばんで見えた）+ 行き止まりの端の基盤を 0.3 内で止める（7endtrim3）。斜めの頭（7dh）とレールの幅は採らない
    "7": dict(_R6, snow_rgb=(0.945, 0.945, 1.0), end_trim=0.3),
    "4wear1": dict(_R3, wear_t={"oil": 0.35}, wear_k={"oil": 1.0, "rust0": 1.0, "rust1": 1.0}),
    "2combo": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.39, 0.57, 0.40), rail_rgb=(0.30, 0.19, 0.15), embed=True),
})


def round_dir(n):
    if FAMILY == "rail_ballast":
        return os.path.join(ROOT, "work", "rounds", f"round{n}")
    return os.path.join(ROOT, "work", "rounds", FAMILY, f"round{n}")


def pak_path(n):
    name = f"ami_round{n}.pak" if FAMILY == "rail_ballast" else f"ami_{FAMILY}_round{n}.pak"
    return os.path.join(ROOT, "rounds", name)


def family_targets(names):
    """系統の描く対象（FAMILIES の targets の glob を、render.py の SHEETS の名前 names に当てる。並びは names の順）。"""
    pats = FAMILIES[FAMILY]["targets"]
    return [t for t in names if any(fnmatch.fnmatchcase(t, p) for p in pats)]


def _render_family(n):
    """rail_ballast 以外の系統: blender/round_<系統>.py の apply で render.py の設定に重ねてから描く。"""
    import render  # noqa: E402
    import sheetlib as R  # noqa: E402
    mod = importlib.import_module(FAMILIES[FAMILY]["module"])
    mod.apply(mod.ROUND_SETTINGS[n], n, R, render)
    _run(n, R, render, family_targets(list(render.SHEETS)))


def _run(n, R, render, targets):
    import sheetlib.sheetlib as S  # noqa: E402
    import sheetlib.cells as C  # noqa: E402
    import sheetlib.core as K  # noqa: E402
    S.SRC = os.path.join(round_dir(n), "src")
    # 一時ファイルもラウンドごとに分ける（同じ対象を別のラウンドで同時に描くと、work/ の同じ名前の一時ファイルを取り合う）
    for m in (K, C, S):
        m.WORK = os.path.join(round_dir(n), "tmp")
    os.makedirs(K.WORK, exist_ok=True)
    R.run_targets({k: v for k, v in render.SHEETS.items() if k in targets}, list(targets))


def _render(n):
    import render  # noqa: E402  AMI の描き分けを登録する（__main__ でないので描かない）
    import sheetlib as R  # noqa: E402
    import sheetlib.sheetlib as S  # noqa: E402
    import sheetlib.track_parts as TP  # noqa: E402

    cfg = ROUND_SETTINGS[n]
    mean = R._BALLAST_RGB
    away = lambda c, w: tuple(min(1.0, max(0.0, m + w * (x - m))) for x, m in zip(c, mean))
    contrast, grain = cfg["ballast"]
    dk = cfg.get("ballast_dark", 1.0)  # 砕石の色の倍率（ラウンド 5〜）
    stone = R.track_noise(f"ami_ballast_stone_r{n}", tuple(x * dk for x in away(render.BALLAST_STONE_LO, contrast)),
                          tuple(x * dk for x in away(render.BALLAST_STONE_HI, contrast)), grain)
    wear = {}
    for name, _, (lo, hi), t, _ in R.TRACK_WEAR:
        # 汚れの帯ごとの上書き（ラウンド 4〜）: wear_rgb は色（lo, hi）、wear_t は道床の色からの寄せ具合、wear_k は離す倍率
        lo, hi = cfg.get("wear_rgb", {}).get(name, (lo, hi))
        t = cfg.get("wear_t", {}).get(name, t)
        wk = cfg.get("wear_k", {}).get(name, cfg["wear"])
        wear[name] = R.track_noise(f"track_{name}_r{n}", away(R._mix(mean, lo, t), wk), away(R._mix(mean, hi, t), wk), 3.0)
    # 在来線の道床を使う描き分け（通常・基盤・高架・橋・トンネル・壁と架線の元の基盤）だけを替える。高速線・路面軌道は替えない
    for prof in R.TRACK_PROFILES.values():
        if not str(prof.get("sheet", "")).startswith(BALLAST):
            continue
        prof["skin"] = dict(prof.get("skin", {}), ballast=stone)
        rep = dict(prof.get("replace", {}))
        for name, mat in wear.items():
            old = rep.get(name) or next(p for p in R.TRACK_EXTRAS if p.name == name)
            shape = old.shape
            if cfg.get("embed"):
                shape = _lifted(shape, EMBED_TOP - R.BALLAST_H)  # 埋めた砕石の上に出す（まくらぎの上面よりは下）
            if name in cfg.get("drop", ()):
                shape = lambda path, k: None  # noqa: E731  この汚れの帯を描かない
            rep[name] = R.Part(name, old.datum, old.width, mat, shape, old.group)
        prof["replace"] = rep
        if cfg.get("embed"):
            prof["skin"]["ballast_fill"] = stone
        if "sleeper_rgb" in cfg:  # 夏の絵のまくらぎの色（くすみのまだら。TRACK_WEAR_SKIN の sleeper の差し替え）
            prof["skin"]["sleeper"] = R.track_noise(f"track_sleeper_r{n}", *cfg["sleeper_rgb"], 5.0)
        mode = cfg.get("snow_mode")
        if mode:  # 雪の絵の材質（ラウンド 6〜。prof["snow_skin"] は雪の絵だけに効く）
            snow = R.SNOW_SKIN["ballast"]
            if "snow_rgb" in cfg:  # 道床の雪の色（ラウンド 7〜）
                snow = (snow[0] + f"_r{n}", cfg["snow_rgb"]) + tuple(snow[2:])
            ss = dict(prof.get("snow_skin", {}))
            if "snow_rgb" in cfg:
                ss.update(ballast=snow, ballast_fill=snow, base=snow)
            if mode in ("clean", "rut"):
                ss.update({k: snow for k in ("oil", "rust0", "sleeper_rust", "sleeper")})
                ss["rust1"] = snow if mode == "clean" else R.TRACK_SNOW_WEAR_SKIN["rust1"]
            elif mode == "plow":
                ss.update({k: snow for k in ("rust0",)})
                ss["sleeper"] = R.track_noise(f"track_snow_sleeper_r{n}", *cfg["sleeper_rgb"], 5.0)
                ss["ballast_fill"] = R.TRACK_SNOW_WEAR_SKIN["oil"]
            prof["snow_skin"] = ss
        if cfg.get("no_body") and prof.get("elev_body"):  # 切り分け用: 高架の躯体を描かない
            prof["elev_body"] = False
        if "deck_rgb" in cfg:  # 床（基盤）のコンクリートの色
            prof["skin"]["base"] = ("base", cfg["deck_rgb"])
        if "shoulder" in cfg:
            # 道床の肩とのり面: まくらぎの上面の高さ（EMBED_TOP）の平らな肩を ±shoulder まで延ばし、そこから床（±1.9）まで斜面
            old = next(p for p in R.TRACK_PARTS if p.name == "ballast")
            sh, top = cfg["shoulder"], EMBED_TOP - 0.001
            prof["replace"]["ballast"] = R.Part("ballast", old.datum, old.width, old.material,
                                                lambda path, k, sh=sh, top=top: R.sweep(
                                                    path, [(-1.9 * k, 0.0), (1.9 * k, 0.0), (sh * k, top), (-sh * k, top)]))
    if cfg.get("embed"):
        R.SNOW_SKIN["ballast_fill"] = R.SNOW_SKIN["ballast"]
    TP.SLEEPER_PITCH = cfg["sleeper_pitch"]  # まくらぎの形は描くときにこの値を読む（render_parallel は対象ごとに別のプロセス）
    if cfg.get("sleeper_align"):
        # 直線の経路はタイルの辺の外へ PATH_EXT 延びる。まくらぎを辺から半ピッチの位置にそろえ、タイルの継ぎ目でも同じ間隔にする
        TP.SLEEPER_FIRST = (S.PATH_EXT + TP.SLEEPER_PITCH / 2) % TP.SLEEPER_PITCH
    if "end_trim" in cfg:  # 切り分け用: 行き止まりの端の壁で基盤を削る位置を、タイルの端から内へ end_trim 下げる
        A = sys.modules["sheetlib.assemble"]
        _reach = A._reach_edge
        A._reach_edge = lambda path: _reach(path) - cfg["end_trim"]
    extra = _trial_parts(cfg, R, TP)
    for prof in R.TRACK_PROFILES.values():
        if str(prof.get("sheet", "")).startswith(BALLAST) and extra:
            prof["parts"] = tuple(prof.get("parts", ())) + tuple(p for p in extra if p.name not in ("railL", "railR"))
            prof["replace"] = dict(prof["replace"], **{p.name: p for p in extra if p.name in ("railL", "railR")})
    _run(n, R, render, ROUND_TARGETS)


EMBED_TOP = 0.15 + 0.08 / 2 - 0.012  # まくらぎの上面（track_parts の SLEEPER_Z + SLEEPER_H / 2）の少し下


def _lifted(shape, dz):
    def lifted(path, k):
        geo = shape(path, k)
        if geo is None:
            return None
        verts, faces = geo
        return [v + type(v)((0, 0, dz)) for v in verts], faces
    return lifted


def _trial_parts(cfg, R, TP):
    """構造の試しの部品（ラウンド 2）。名前が railL・railR のものはレールの差し替え、ほかは足す部品。"""
    import math
    from mathutils import Vector
    rin, rout, rz1 = cfg.get("rail_size", (TP.RAIL_IN, TP.RAIL_OUT, TP.RAIL_Z1))
    out = []
    if "rail_size" in cfg:
        def rail(side):
            def shape(path, k):
                a, b = rin * k, rout * k
                prof = [(a, TP.RAIL_Z0), (b, TP.RAIL_Z0), (b, rz1), (a, rz1)]
                return R.sweep(path, [(side * u, v) for u, v in prof][::side])
            return shape
        old = {p.name: p for p in R.TRACK_PARTS}
        mat = old["railL"].material
        if "rail_rgb" in cfg:
            mat = ("rail_side", cfg["rail_rgb"]) + tuple(mat[2:])
        out += [R.Part(n, "rail", "gauge", mat, rail(sd)) for n, sd in (("railL", -1), ("railR", 1))]
    if cfg.get("rail_head"):
        # 車輪で磨かれた頭頂面（明るい鋼の色）。側面は今のさび色のまま
        rgb = cfg["rail_head"] if isinstance(cfg["rail_head"], tuple) else (0.80, 0.79, 0.76)
        head = TP._strip_shape(rin + 0.01, rout - 0.01, rz1 + 0.001, 0.004)
        if "diag_head" in cfg:
            # 斜め（横幅の倍率 k < 1）だけ、帯の幅を diag_head 倍にする（帯の中心はそのまま）
            mid, half = (rin + rout) / 2, (rout - rin - 0.02) / 2 * cfg["diag_head"]
            narrow = TP._strip_shape(mid - half, mid + half, rz1 + 0.001, 0.004)
            head = (lambda path, k, h=head, nw=narrow: nw(path, k) if k < 0.99 else h(path, k))
        out.append(R.Part("rail_head", "rail", "gauge", ("rail_head", rgb, 0.4, 0.0), head))
    if cfg.get("embed"):
        # まくらぎの間の砕石: まくらぎの長さの幅で、上面の少し下まで（上面だけが見える）。材質は道床（ballast）と同じ名前で、まだらも同じになる
        top = EMBED_TOP
        half = TP.SLEEPER_LEN / 2 + 0.05
        out.append(R.Part("ballast_fill", "rail", "gauge", R.TRACK_PARTS[0].material,
                          lambda path, k: R.sweep(path, [(-half * k, TP.BALLAST_H - 0.01), (half * k, TP.BALLAST_H - 0.01), (half * k, top), (-half * k, top)])))
    if cfg.get("fasten"):
        # 締結装置: まくらぎごとにレールの内と外に 1 つずつ（暗い金具）
        z = TP.SLEEPER_Z + TP.SLEEPER_H / 2 + 0.02

        def fasten(path, k):
            boxes = []
            for p, ang in R.along(path, TP.SLEEPER_PITCH, TP.SLEEPER_FIRST):
                n = Vector((-math.sin(ang), math.cos(ang)))
                for u in (rin - 0.06, rout + 0.06):
                    for sg in (1, -1):
                        c = p + n * (sg * u * k)
                        boxes.append(R.box(c.x, c.y, z, 0.16, 0.09 * k, 0.04, rot=ang))
            return R.merge(boxes) if boxes else None
        out.append(R.Part("fasten", "rail", "gauge", ("fasten", (0.10, 0.10, 0.11), 0.6, 0.0), fasten))
    if cfg.get("joint"):
        # 継目: タイルの中ほどで、両方のレールに継目板（レールの両脇の暗い板）と遊間（頭頂面の暗い切れ目）
        def joint(path, k):
            best = None
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                d = b - a
                t = max(0.0, min(1.0, -a.dot(d) / d.length_squared))
                q = a + d * t
                if best is None or q.length < best[0].length:
                    best = (q, math.atan2(d.y, d.x))
            if best is None or best[0].length > 0.5:
                return None
            q, ang = best
            n = Vector((-math.sin(ang), math.cos(ang)))
            plate, gap = cfg["joint"] if isinstance(cfg["joint"], tuple) else (0.6, 0.06)  # 継目板の長さ、遊間（頭の切れ目）の長さ
            boxes = []
            for sg in (1, -1):
                for u in (rin - 0.03, rout + 0.03):
                    c = q + n * (sg * u * k)
                    boxes.append(R.box(c.x, c.y, (TP.RAIL_Z0 + rz1) / 2 - 0.02, plate, 0.05 * k, rz1 - TP.RAIL_Z0 - 0.03, rot=ang))
                c = q + n * (sg * (rin + rout) / 2 * k)
                boxes.append(R.box(c.x, c.y, rz1 + 0.008, gap, (rout - rin + 0.02) * k, 0.006, rot=ang))
            return R.merge(boxes)
        out.append(R.Part("joint", "rail", "gauge", ("joint", (0.12, 0.11, 0.10), 0.6, 0.0), joint))
    return out


def _pack(n):
    suffix = f"_round{n}"
    drawn = os.path.join(round_dir(n), "src")
    out_src = os.path.join(round_dir(n), "pak_src")
    shutil.rmtree(out_src, ignore_errors=True)
    os.makedirs(out_src)
    rename = lambda text: re.sub(r"\b(ami_[a-z0-9_]+?)(?=\.\d|\b)", lambda m: m[1] + suffix, text)
    dats = sorted({p for g in FAMILIES[FAMILY]["dats"] for p in glob.glob(os.path.join(ROOT, "src", g + ".dat"))})
    sheets = set()
    names = []
    for d in dats:
        with open(d, encoding="utf8") as f:
            text = f.read()
        sheets |= set(re.findall(r"=\s*>?\s*(ami_[a-z0-9_]+)\.\d", text))
        base = os.path.basename(d)[:-4] + suffix
        with open(os.path.join(out_src, base + ".dat"), "w", encoding="utf8", newline="\n") as f:
            f.write(rename(text))
        names.append(base + ".dat")
    for s in sorted(sheets):
        src = os.path.join(drawn, s + ".png")
        if str(n) == "0" or not os.path.exists(src):
            src = os.path.join(ROOT, "src", s + ".png")
        shutil.copy(src, os.path.join(out_src, s + suffix + ".png"))
    os.makedirs(os.path.join(ROOT, "rounds"), exist_ok=True)
    out = pak_path(n)
    r = subprocess.run(["makeobj", "pak256", out, *names], cwd=out_src, capture_output=True, text=True,
                       encoding="utf8", errors="replace")
    text = r.stdout + r.stderr
    if r.returncode != 0 or any("warning" in line.lower() or "error" in line.lower() for line in text.splitlines()):
        print(text)
        sys.exit(f"[round] makeobj が失敗か警告あり: {out}")
    print(f"[round] {out}: {len(names)} dat, {len(sheets)} シート")


if __name__ == "__main__":
    try:
        import bpy  # noqa: F401
    except ImportError:
        if sys.argv[1] == "--targets":
            sys.path.insert(0, _HERE)
            names = [os.path.basename(p)[:-4] for p in sorted(glob.glob(os.path.join(ROOT, "src", "*.png")))]
            print(" ".join(ROUND_TARGETS if FAMILY == "rail_ballast" else family_targets(names)))
        else:
            _pack(sys.argv[1])
    else:
        sys.path.insert(0, _HERE)
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
        (_render if FAMILY == "rail_ballast" else _render_family)(os.environ["AMI_ROUND"])
