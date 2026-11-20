"""精細化のラウンド（#56）の版を作る。名前は元の名前の末尾に _round<n> を付け、今の版と同じゲームに並べて比べる。

アドオンのディレクトリで:

    AMI_ROUND=1 python -X utf8 ../../tools/blender/render_parallel.py --entry blender/round.py <対象 ...>   # 描く（対象は ROUND_TARGETS）
    python -X utf8 blender/round.py 1     # 描いたシートから dat を書き、rounds/ami_round1.pak を作る（Blender を使わない）
    python -X utf8 blender/round.py 0     # ラウンド 0（今の src/ をそのまま）の pak を作る

対象は在来線一式（ROUND_TARGETS）。描いた絵は work/rounds/round<n>/src/ に置き、src/・dist/ は変えない。
描かなかったシート（ラウンド 0 の全部、ラウンドで変えない絵）は src/ のものを使う。
dat は src/ のものを写し、ami_ で始まる名前を全部 _round<n> 付きにする（画像の参照・トンネルの way= も）。
ラウンドごとの描き分けは ROUND_SETTINGS（render.py の設定の上に重ねる）。
"""
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

# ラウンド → 描き分け。ballast: 砕石のまだら（明暗差の倍率, 細かさ）。wear: 汚れの色を道床の色から離す倍率。
# sleeper_pitch: まくらぎの間隔。値の決め方は記録 docs/records/ の各ラウンドの記録
ROUND_SETTINGS = {
    "1": {"ballast": (2.4, 12.0), "wear": 1.8, "sleeper_pitch": 0.54},
}
# ラウンド 2 は構造の試し（#56）: 意味の木の葉を 1 つずつ入り切りする。base は 1 のまくらぎの間隔の継ぎ目の欠陥（タイルの端で間があく）を直したもの。
# 葉: head（レールの頭頂面の磨かれた帯）、head_x（それに加えてレールを太く高く誇張）、fasten（締結装置）、joint（継目）
_R2 = dict(ROUND_SETTINGS["1"], sleeper_pitch=10 / 18, sleeper_align=True)
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
    "2combo": dict(_R2, rail_head=(0.92, 0.91, 0.88), rail_size=(0.39, 0.57, 0.40), rail_rgb=(0.30, 0.19, 0.15), embed=True),
})


def round_dir(n):
    return os.path.join(ROOT, "work", "rounds", f"round{n}")


def _render(n):
    import render  # noqa: E402  AMI の描き分けを登録する（__main__ でないので描かない）
    import sheetlib as R  # noqa: E402
    import sheetlib.sheetlib as S  # noqa: E402
    import sheetlib.track_parts as TP  # noqa: E402

    cfg = ROUND_SETTINGS[n]
    mean = R._BALLAST_RGB
    away = lambda c, w: tuple(min(1.0, max(0.0, m + w * (x - m))) for x, m in zip(c, mean))
    contrast, grain = cfg["ballast"]
    stone = R.track_noise(f"ami_ballast_stone_r{n}", away(render.BALLAST_STONE_LO, contrast),
                          away(render.BALLAST_STONE_HI, contrast), grain)
    wear = {}
    for name, _, (lo, hi), t, _ in R.TRACK_WEAR:
        wear[name] = R.track_noise(f"track_{name}_r{n}", away(R._mix(mean, lo, t), cfg["wear"]),
                                   away(R._mix(mean, hi, t), cfg["wear"]), 3.0)
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
            rep[name] = R.Part(name, old.datum, old.width, mat, shape, old.group, centre=False)
        prof["replace"] = rep
        if cfg.get("embed"):
            prof["skin"]["ballast_fill"] = stone
    if cfg.get("embed"):
        R.SNOW_SKIN["ballast_fill"] = R.SNOW_SKIN["ballast"]
    TP.SLEEPER_PITCH = cfg["sleeper_pitch"]  # まくらぎの形は描くときにこの値を読む（render_parallel は対象ごとに別のプロセス）
    if cfg.get("sleeper_align"):
        # 直線の経路はタイルの辺の外へ PATH_EXT 延びる。まくらぎを辺から半ピッチの位置にそろえ、タイルの継ぎ目でも同じ間隔にする
        TP.SLEEPER_FIRST = (S.PATH_EXT + TP.SLEEPER_PITCH / 2) % TP.SLEEPER_PITCH
    extra = _trial_parts(cfg, R, TP)
    for prof in R.TRACK_PROFILES.values():
        if str(prof.get("sheet", "")).startswith(BALLAST) and extra:
            prof["parts"] = tuple(prof.get("parts", ())) + tuple(p for p in extra if p.name not in ("railL", "railR"))
            prof["replace"] = dict(prof["replace"], **{p.name: p for p in extra if p.name in ("railL", "railR")})
    S.SRC = os.path.join(round_dir(n), "src")
    # 一時ファイルもラウンドごとに分ける（同じ対象を別のラウンドで同時に描くと、work/ の同じ名前の一時ファイルを取り合う）
    import sheetlib.cells as C  # noqa: E402
    import sheetlib.core as K  # noqa: E402
    for m in (K, C, S):
        m.WORK = os.path.join(round_dir(n), "tmp")
    os.makedirs(K.WORK, exist_ok=True)
    R.run_targets({k: v for k, v in render.SHEETS.items() if k in ROUND_TARGETS}, ROUND_TARGETS)


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
        out.append(R.Part("rail_head", "rail", "gauge", ("rail_head", rgb, 0.4, 0.0),
                          TP._strip_shape(rin + 0.01, rout - 0.01, rz1 + 0.001, 0.004)))
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
            boxes = []
            for sg in (1, -1):
                for u in (rin - 0.03, rout + 0.03):
                    c = q + n * (sg * u * k)
                    boxes.append(R.box(c.x, c.y, (TP.RAIL_Z0 + rz1) / 2 - 0.02, 0.6, 0.05 * k, rz1 - TP.RAIL_Z0 - 0.03, rot=ang))
                c = q + n * (sg * (rin + rout) / 2 * k)
                boxes.append(R.box(c.x, c.y, rz1 + 0.004, 0.06, (rout - rin + 0.02) * k, 0.006, rot=ang))
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
    dats = sorted({p for g in ROUND_DATS for p in glob.glob(os.path.join(ROOT, "src", g + ".dat"))})
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
    out = os.path.join(ROOT, "rounds", f"ami_round{n}.pak")
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
        _pack(sys.argv[1])
    else:
        sys.path.insert(0, _HERE)
        sys.path.insert(0, os.path.join(_HERE, "..", "..", "..", "tools", "blender"))
        _render(os.environ["AMI_ROUND"])
