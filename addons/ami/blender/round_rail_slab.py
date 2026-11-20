"""精細化のラウンド（#56）の、高速線（スラブ軌道）一式の描き分け。blender/round.py が AMI_FAMILY=rail_slab のときに読む。

ROUND_SETTINGS: ラウンドの鍵（"1"・葉の試しの "1xxx" など）→ 設定。値の決め方は docs/records/ の各ラウンドの記録
（docs/records/2026-11-20_ami-slab-refine-round<n>.md）。
apply(cfg, n, R, render): 描く前に、render.py の設定（R.TRACK_PROFILES など）に cfg を重ねる。土台は今の render.py。
共有の tools/blender/sheetlib の値をモジュールごと書き換えない（ほかの系統の絵が変わる）。要るときは、描き分けの辞書の中で差し替える。

設定の鍵（どれも無くてよい）:
    rail        True: レールを在来線の本番（render.py の RAIL_*。暗いさび色の 1px の側面と、明るい頭の帯）にそろえる
    rail_head   False: rail のうち、明るい頭の帯を載せない（側面の形と色だけそろえる）
    wear_t      汚れの帯ごとの、スラブの色からの寄せ具合の倍率（名前 → 倍率。0 で描かない）。sheetlib の SLAB_WEAR_K の上に掛ける
    fastener    (線路に沿う幅, 横切る幅): 締結装置の大きさ（sheetlib の FASTENER_ALONG・FASTENER_ACROSS は 0.22・0.34）
    fastener_rgb  締結装置の色
    snow_clean  True: 雪の絵で、汚れの帯も雪にする（在来線のラウンド 6 の clean）
    snow_rgb    雪の絵の道床・スラブの雪の色（在来線の本番は 0.945・0.945・1.0）
    snow_parts  True: 雪の絵で、締結装置と突起も雪にする（レールだけが出る）
    bed_rgb     コンクリート道床の色（暗い側, 明るい側。sheetlib の SLAB_BED_LO・HI は 0.30〜0.38）
    bed_u       コンクリート道床の (下面, 上面) の半幅（sheetlib は 1.72・1.68。在来線の道床の下面は 1.9）
    joint       (線路に沿う幅, 色): スラブの継ぎ目に、スラブの幅いっぱいの暗い帯を載せる（継ぎ目を見せる）
    wear_centre (半幅, 寄せ具合の倍率): さびの帯 2 本ずつを描かず、レールの間の油の帯をこの半幅に広げる
    slab_rgb    軌道スラブの色（暗い側, 明るい側。sheetlib の SLAB_LO・HI は 0.60〜0.68）
    drop        描かない部品の名前（例: 突起 slab_stud・欠き込み slab_notch・締結装置 slab_fastener・そのさび sleeper_rust）
    head_rgb    rail で載せる明るい頭の帯の色（在来線は 0.92・0.91・0.88）
"""
import dataclasses

# ラウンド 1（土台は今の render.py。在来線のラウンド 1〜8 の決めごとのうち、スラブ軌道にも当てはまるものから試す）
#   1rail: レールを在来線にそろえる（④ そろい）。1wear: 汚れの帯（明暗の縞）を弱める。1wearoff: 汚れの帯なし。
#   1fast: 締結装置を誇張して、まくらぎの代わりの拍子にする。1snow: 雪の絵を在来線と同じ積もったばかりの雪にする
ROUND_SETTINGS = {
    "1rail": {"rail": True},
    "1wear": {"wear_t": {"rust0": 0.5, "rust1": 0.5, "oil": 0.5}},
    "1wearoff": {"wear_t": {"rust0": 0.0, "rust1": 0.0, "oil": 0.0}},
    "1fast": {"fastener": (0.28, 0.56)},
    "1snow": {"snow_clean": True, "snow_rgb": (0.945, 0.945, 1.0)},
    # 1fast は暗い市松に見えた（在来線のラウンド 4 の黒い梯子と同じ）。1fastlt: 色を明るく、少しだけ大きく
    "1fastlt": {"fastener": (0.26, 0.46), "fastener_rgb": (0.22, 0.22, 0.23)},
    # 1bed: 基盤の版でスラブが床（明るい灰色）に溶ける（在来線のラウンド 5 と同じ）。道床を暗く、在来線の道床の幅に広げて、帯の縁を出す
    "1bed": {"bed_rgb": ((0.20, 0.20, 0.20), (0.27, 0.27, 0.26)), "bed_u": (1.9, 1.85)},
    "1bedc": {"bed_rgb": ((0.20, 0.20, 0.20), (0.27, 0.27, 0.26))},
    "1snow2": {"snow_clean": True, "snow_rgb": (0.945, 0.945, 1.0), "snow_parts": True},
}
# ラウンド 1 の組み合わせの候補: 1rail + 1wear + 1bed + 1snow2（締結装置の誇張は採らない）。1b は汚れの帯なし
_R1 = {"rail": True, "bed_rgb": ((0.20, 0.20, 0.20), (0.27, 0.27, 0.26)), "bed_u": (1.9, 1.85),
       "snow_clean": True, "snow_rgb": (0.945, 0.945, 1.0), "snow_parts": True}
# ラウンド 2（土台は 1）: スラブ軌道らしさの葉。2joint: 継ぎ目を暗い帯で見せる（すき間 0.2 は約 1.4px で読めない）。
#   2jointl: 継ぎ目を道床の色で細く。2wearc: さびの帯をやめ、レールの間をくすませる（ブレーキの粉）。2slab: スラブを明るい新しいコンクリートの色に
# 1rail は孤立点を 30 → 37 に上げた（明るいスラブの上の 1px の明るい頭が、画面の 2:1 の斜めで点線になる）。1railnh: 頭の帯なし
ROUND_SETTINGS.update({
    "1railnh": {"rail": True, "rail_head": False},
    "1c": dict(_R1, rail_head=False, wear_t={"rust0": 0.5, "rust1": 0.5, "oil": 0.5}),
    "1d": dict(_R1, rail_head=False),
    # ラウンド 1 = 1d（記録 docs/records/2026-11-20_ami-slab-refine-round1.md）
    "1": dict(_R1, rail_head=False),
    "1a": dict(_R1, wear_t={"rust0": 0.5, "rust1": 0.5, "oil": 0.5}),
    "1b": dict(_R1, wear_t={"rust0": 0.0, "rust1": 0.0, "oil": 0.0}),
})

SLAB = "ami_rail_slab"


def apply(cfg, n, R, render):
    import sheetlib.slab_parts as SP

    profs = [p for p in R.TRACK_PROFILES.values() if str(p.get("sheet", "")).startswith(SLAB)]
    for prof in profs:
        rep = dict(prof.get("replace", {}))
        parts = list(prof.get("parts", ()))
        skin = dict(prof.get("skin", {}))
        snow = dict(prof.get("snow_skin", {}))
        if cfg.get("rail"):
            rep["railL"] = render._BALLAST_REPLACE["railL"]
            rep["railR"] = render._BALLAST_REPLACE["railR"]
            if cfg.get("rail_head", True):
                head = next(p for p in render._BALLAST_PARTS if p.name == "rail_head")
                if "head_rgb" in cfg:
                    head = dataclasses.replace(head, material=("rail_head_r", cfg["head_rgb"]) + tuple(head.material[2:]))
                parts.append(head)
        if "wear_t" in cfg:
            for i, (name, _, (lo, hi), t, _) in enumerate(R.TRACK_WEAR):
                f = cfg["wear_t"].get(name)
                if f is None:
                    continue
                old = rep[name]
                if f == 0:
                    rep[name] = dataclasses.replace(old, shape=lambda path, k: None)
                    continue
                t = t * SP.SLAB_WEAR_K * f
                mat = R.track_noise(f"slab_{name}_r{n}", R._mix(SP.SLAB_RGB, lo, t), R._mix(SP.SLAB_RGB, hi, t), 3.0)
                rep[name] = dataclasses.replace(old, material=mat)
        if "fastener" in cfg or "fastener_rgb" in cfg:
            along, across = cfg.get("fastener", (SP.FASTENER_ALONG, SP.FASTENER_ACROSS))
            z, sz = (SP.FASTENER_Z0 + SP.FASTENER_Z1) / 2, SP.FASTENER_Z1 - SP.FASTENER_Z0
            old = next(p for p in SP.SLAB_TRACK_PARTS if p.name == "slab_fastener")
            mat = old.material if "fastener_rgb" not in cfg else ("slab_fastener_r", cfg["fastener_rgb"]) + tuple(old.material[2:])
            rep["slab_fastener"] = dataclasses.replace(
                old, material=mat, shape=lambda path, k, a=along, c=across: SP._fastener_boxes(path, k, a, c, z, sz))
            o = SP.FASTENER_RUST_OVER
            rust = rep["sleeper_rust"]
            rep["sleeper_rust"] = dataclasses.replace(rust, shape=lambda path, k, a=along, c=across, zz=SP._wear_z(len(R.TRACK_WEAR)):
                                                      SP._fastener_boxes(path, k, a + 2 * o, c + 2 * o, zz + SP.WEAR_TH / 2, SP.WEAR_TH))
        if "bed_rgb" in cfg:
            skin["slab_bed"] = R.track_noise(f"slab_bed_r{n}", *cfg["bed_rgb"], SP.SLAB_BED_GRAIN)
        if "bed_u" in cfg:
            bu, tu = cfg["bed_u"]
            old = rep.get("slab_bed") or next(p for p in SP.SLAB_TRACK_PARTS if p.name == "slab_bed")
            beyond = render._stop_at_end_wall(render._SLAB_DATUMS["slab_bed"]) if "slab_bed" in rep else 0.5
            rep["slab_bed"] = dataclasses.replace(old, shape=_bed_shape(SP, R, bu, tu, beyond))
            fills = dict(prof.get("bed_fills", {}))
            if "slab_bed" in fills:
                fills["slab_bed"] = (tu,) + tuple(fills["slab_bed"][1:])
                prof["bed_fills"] = fills
        if "snow_rgb" in cfg:
            s = ("ami_snow_slab", cfg["snow_rgb"]) + tuple(R.SNOW_SKIN["ballast"][2:])
            snow.update({k: s for k in ("slab_bed", "slab_fill", "slab", "slab_notch", "base")})
            if cfg.get("snow_clean"):
                snow.update({k: s for k in ("oil", "rust0", "rust1", "sleeper_rust")})
        elif cfg.get("snow_clean"):
            snow.update({k: R.SNOW_SKIN["ballast"] for k in ("oil", "rust0", "rust1", "sleeper_rust")})
        if "joint" in cfg:
            w, rgb = cfg["joint"]
            parts.append(R.Part("slab_joint", "rail", "gauge", ("slab_joint", rgb), _joint_shape(SP, R, w), centre=False))
            snow.setdefault("slab_joint", snow.get("slab", R.SNOW_SKIN["ballast"]))
        if "wear_centre" in cfg:
            u, f = cfg["wear_centre"]
            for name in ("rust0", "rust1"):
                rep[name] = dataclasses.replace(rep[name], shape=lambda path, k: None)
            name, _, (lo, hi), t, _ = next(w for w in R.TRACK_WEAR if w[0] == "oil")
            t = t * SP.SLAB_WEAR_K * f
            i = [w[0] for w in R.TRACK_WEAR].index("oil")
            rep["oil"] = dataclasses.replace(
                rep["oil"], material=R.track_noise(f"slab_oil_c_r{n}", R._mix(SP.SLAB_RGB, lo, t), R._mix(SP.SLAB_RGB, hi, t), 3.0),
                shape=SP._wear_centre_shape(u, SP._wear_z(i)))
        if "slab_rgb" in cfg:
            skin["slab"] = R.track_noise(f"slab_r{n}", *cfg["slab_rgb"], SP.SLAB_GRAIN)
        if cfg.get("snow_parts"):
            s_ = snow.get("slab", R.SNOW_SKIN["ballast"])
            snow.update(slab_stud=s_, slab_fastener=s_)
        for name in cfg.get("drop", ()):
            old = rep.get(name) or next(p for p in SP.SLAB_TRACK_PARTS if p.name == name)
            rep[name] = dataclasses.replace(old, shape=lambda path, k: None)
        prof["replace"], prof["parts"], prof["skin"], prof["snow_skin"] = rep, tuple(parts), skin, snow


def _bed_shape(SP, R, bu, tu, beyond):
    """sheetlib の slab_bed_shape と同じ形で、半幅だけを替えたもの（モジュールの SLAB_BED_U・TOP_U を書き換えない）。"""
    def shape(path, k):
        edge = SP._edge_reach(path)
        if edge is not None:
            reach, d = edge
            pts = [path[0] - d * (reach + (beyond(d) if callable(beyond) else beyond))] + list(path)
        else:
            pts = SP._slice(path, *SP._extent(path, SP.SLAB_BED_PAD))
        return R.sweep(pts, [(-bu * k, 0.0), (bu * k, 0.0), (tu * k, SP.SLAB_BED_H), (-tu * k, SP.SLAB_BED_H)])
    return shape


def _joint_shape(SP, R, w):
    """スラブの継ぎ目（sheetlib の _layout の継ぎ目の位置）に、スラブの幅いっぱい・線路に沿う幅 w の薄い板。汚れの帯の上に載せる。"""
    import math
    z = SP._wear_z(len(R.TRACK_WEAR) + 1)

    def shape(path, k):
        out = []
        for s in SP._layout(path)[0]:
            p, d = SP._point(path, s)
            out.append(R.box(p.x, p.y, z, w, 2 * SP.SLAB_U * k, SP.WEAR_TH, rot=math.atan2(d.y, d.x)))
        return R.merge(out) if out else None
    return shape

_R2 = ROUND_SETTINGS["1"]
ROUND_SETTINGS.update({
    "2joint": dict(_R2, joint=(0.30, (0.12, 0.12, 0.12))),
    "2jointl": dict(_R2, joint=(0.20, (0.24, 0.24, 0.23))),
    "2wearc": dict(_R2, wear_centre=(0.36, 0.8)),
    "2slab": dict(_R2, slab_rgb=((0.68, 0.68, 0.65), (0.76, 0.76, 0.73))),
})
ROUND_SETTINGS["2c"] = dict(_R2, joint=(0.30, (0.12, 0.12, 0.12)), wear_centre=(0.36, 0.8))
# ラウンド 2 = 2joint（記録 docs/records/2026-11-20_ami-slab-refine-round2.md）。2wearc・2c は孤立点が上がり、採らない
ROUND_SETTINGS["2"] = ROUND_SETTINGS["2joint"]

# ラウンド 3（土台は 2）: 継ぎ目の中の突起（暗い帯の中の明るい点）と、手本が描かない締結装置を省く。控えめな色のレールの頭
_R3 = ROUND_SETTINGS["2"]
ROUND_SETTINGS.update({
    "3nostud": dict(_R3, drop=("slab_stud", "slab_notch")),
    "3nofast": dict(_R3, drop=("slab_fastener", "sleeper_rust")),
    "3head": dict(_R3, rail_head=True, head_rgb=(0.80, 0.79, 0.76)),
})
# ラウンド 3 = 3nofast（記録 docs/records/2026-11-20_ami-slab-refine-round3.md）。3nostud・3head は孤立点が上がり、採らない
ROUND_SETTINGS["3"] = ROUND_SETTINGS["3nofast"]
