"""精細化のラウンド（#56 の流れ。#331）の、第 5 弾の物（路面の色・黄色の中央線・交差点の中心の印、転車台・遷車台）の描き分け。
blender/round.py が AMI_FAMILY=wave5 のときに読む。

土台は今の本番（render.py の MARKING_COLOR_ARGS と sheetlib の turntable.py）。ここは本番の値を書き換えず、このプロセスの中でだけ
材質の差し替え（skin）と部品の足し・寸法の差し替えをする。
ラウンド 3 は本番に入れた（#331）。入れた葉（wear・lift・tt_skin・coping_w・apron_ring・hut_window）は、本番の上に重ねると
二重にかかり、wear は本番の marking.py の口（_color_bands・_put_xy の引数）が変わったので差し替えが合わずに落ちる。
"1"〜"3" と、これらの葉の試しは描き直さない（記録のために残す）。入れていない葉（1ap・1pt）も tt_skin を使い、本番の skin と重なるので、描き直すのは 0null で作りを確かめるときだけにする。

意味の木と試しの判断は docs/records/2026-11-26_ami-wave5-refine-round1.md。

ROUND_SETTINGS: ラウンドの鍵（"1"・葉の試しの "1xxx"）→ 設定。設定のキー（どれも無くてよい）:
    wear: 色の舗装の帯の走行跡 (帯の並び, 色の褪せの寄せ具合)。帯の並びは中央線の中心からの (v0, v1) の組で、左右の帯に 1 本ずつ重ねる。
        褪せた所は、帯の色を路面の走行跡の灰色へ寄せたまだら（下の道路の走行跡 WEAR_LAYERS と同じ所を通す）
    lift: 色の舗装の色に掛ける倍率（赤・青・緑と赤の縞）
    tt_skin: 転車台・遷車台の材質の差し替え。材質の名前（turntable.py の _M_* の先頭）→ ("concrete", rgb, amp, grain, stain, grime)
        （sheetlib の tiled_concrete_material。タイルの辺でつながる）
    coping_w: 転車台・遷車台の縁の黄色の帯の幅（本番 0.18）
"""

_SURF = (0.12, 2.5, 0.15)  # render.py の TRACK_SURFACE（線路の基盤・壁の段 2）と同じ振れ幅・粒・しみ

ROUND_SETTINGS = {
    "0null": {},  # 作りの確かめ: 何も変えない（今の src/ とバイト単位で同じになるか）
    # 色の舗装は、下の一般道路の走行跡・油の帯を一色の帯で覆い、新品のように均一
    #   1wp: 走行跡（WEAR_LAYERS の 2 段目 0.70〜1.25・1.95〜2.50）を帯の上にも通し、帯の色を灰色へ 0.5 寄せる
    #   1wp2: 1 段目の広い幅（0.55〜1.40・1.80〜2.65）を、0.35 寄せる
    "1wp": {"wear": (((0.70, 1.25), (1.95, 2.50)), 0.5)},
    "1wp2": {"wear": (((0.55, 1.40), (1.80, 2.65)), 0.35)},
    # 色の舗装の色は、アスファルトに近い暗さに色みだけを付けた（#313）。iss（明るく鮮やか）と並べると沈んで見える
    "1lift": {"lift": 1.6},
    # 転車台のまわりのコンクリートとピットの壁は一色。線路の基盤・壁と同じ打ち放しの肌（段 2）にし、壁は床際を暗くする
    "1ap": {"tt_skin": {"turntable_apron": ("concrete", (0.60, 0.60, 0.58)) + _SURF + (0.0,),
                        "turntable_wall": ("concrete", (0.56, 0.56, 0.54)) + _SURF + (0.35,)}},
    # ピットの床は一色。砂利と泥の粗いまだら（粒は約 1px）に、大きなしみ
    "1fl": {"tt_skin": {"turntable_floor": ("concrete", (0.42, 0.41, 0.39), 0.25, 10.0, 0.25, 0.0)}},
    # 縁の黄色の帯は約 1.3px で、まわりのコンクリートに埋もれる（12 章の 1〜2px の部品）。誇張して約 2.6px にする
    "1cp": {"coping_w": 0.36},
    # 桁・台車の塗装は一色。塗装の汚れのまだら（粒は約 2px）としみ
    "1pt": {"tt_skin": {"turntable_bridge": ("concrete", (0.30, 0.36, 0.30), 0.15, 5.0, 0.25, 0.0),
                        "turntable_carriage": ("concrete", (0.70, 0.30, 0.12), 0.15, 5.0, 0.25, 0.0)}},
}


ROUND_SETTINGS.update({
    # 転車台のまわりのコンクリートは、タイルいっぱいの明るい四角で、草の中に浮いて見える（iss は土の地面）。
    #   2ring: まわりを、ピットの縁から 0.9 の輪に縮め、角は地面を見せる。2ringd: 2ring に、色を下げて（0.50）打ち放しの肌（段 2）
    "2ring": {"apron_ring": 0.9},
    "2ringd": {"apron_ring": 0.9, "tt_skin": {"turntable_apron": ("concrete", (0.50, 0.50, 0.48)) + _SURF + (0.0,)}},
    # 運転室は窓の無い箱（約 7px）。窓の暗い帯（高さ 0.25 ≈ 2px）を 4 面に回す
    "2win": {"hut_window": (0.25, 0.55, (0.10, 0.12, 0.15))},
})


def _merge(*keys):
    out = {}
    for k in keys:
        for name, v in ROUND_SETTINGS[k].items():
            out[name] = dict(out.get(name, {}), **v) if isinstance(v, dict) else v
    return out


# ラウンド 1 で採った葉: 1wp・1lift・1fl・1cp（1wp2 は帯全体が灰色にくすむ、1ap・1pt は等倍で見分けられない）
ROUND_SETTINGS["1"] = _merge("1wp", "1lift", "1fl", "1cp")
# ラウンド 2（土台は 1）: まわりの輪（色を下げた 2ringd）と窓（2win）を足す（2ring は明るい輪が草の中で浮く）
ROUND_SETTINGS["2"] = _merge("1", "2ringd", "2win")
# ラウンド 3（土台は 2）: 遷車台の長いピットで、床の大きなしみ（1fl）がタイルごとに同じ形で並んで見えた。しみを外し、細かいまだらだけにする
ROUND_SETTINGS["3fl2"] = {"tt_skin": {"turntable_floor": ("concrete", (0.42, 0.41, 0.39), 0.25, 10.0, 0.0, 0.0)}}
ROUND_SETTINGS["3"] = _merge("2", "3fl2")

_PAVINGS = ("paving_red", "paving_blue", "paving_green")


def apply(cfg, n, R, render):
    import sheetlib.marking as M  # noqa: E402
    import sheetlib.turntable as TT  # noqa: E402

    if "lift" in cfg:
        k = cfg["lift"]
        render.MARKING_COLORS = {c: tuple(tuple(min(1.0, x * k) for x in rgb) for rgb in v) for c, v in render.MARKING_COLORS.items()}
        for kind in _PAVINGS + ("paving_red_striped",):
            color = kind.split("_")[1]
            key = "accent" if kind == "paving_red_striped" else "paving"
            render.MARKING_COLOR_ARGS[kind] = dict(render.MARKING_COLOR_ARGS[kind], **{key: _color(R, render, color, n)})
    if "wear" in cfg:
        spans, t = cfg["wear"]
        _wear_bands(M, spans)
        for kind in _PAVINGS:
            color = kind.split("_")[1]
            render.MARKING_COLOR_ARGS[kind] = dict(render.MARKING_COLOR_ARGS[kind], accent=_faded(R, render, color, t, n))
    if "coping_w" in cfg:
        TT.COPING_W = cfg["coping_w"]
    if "apron_ring" in cfg:
        _apron_ring(TT, cfg["apron_ring"])
    if "hut_window" in cfg:
        _hut_window(TT, *cfg["hut_window"])
    if "tt_skin" in cfg:
        skin = {name: _concrete(R, name, spec, n) for name, spec in cfg["tt_skin"].items()}
        orig = TT._obj

        def obj(name, parts, spec):
            if parts and spec[0] in skin:
                return TT.mesh_object(name, *TT.merge(parts), skin[spec[0]]())
            return orig(name, parts, spec)
        TT._obj = obj


def _color(R, render, color, n):
    lo, hi = render.MARKING_COLORS[color]
    return lambda: R.noisy_material(f"r{n}_paving_{color}", lo, hi, scale=60.0, rough=0.9, ramp=render.ROAD_ASPHALT_RAMP)


def _faded(R, render, color, t, n):
    """帯の色を、路面の走行跡の灰色（街路のアスファルトの走行跡 × 持ち上げ）へ t だけ寄せたまだら。粒は粗め（Scale 25）で段を広く取り、
    褪せた所が帯の色と混ざって縁がほつれて見えるようにする"""
    import sheetlib.road_parts as RP  # noqa: E402
    lift = render.ROAD_ASPHALT_LIFT["street"]
    gray = tuple(tuple(x * lift for x in c) for c in (RP._WEAR_LO, RP._WEAR_HI))
    lo, hi = render.MARKING_COLORS[color]
    mix = lambda a, b: tuple(x + (y - x) * t for x, y in zip(a, b))
    return lambda: R.noisy_material(f"r{n}_paving_{color}_faded", mix(lo, gray[0]), mix(hi, gray[1]), scale=25.0, rough=0.9,
                                    ramp=(0.40, 0.60))


def _wear_bands(M, spans):
    """色の帯（_color_bands）を置くたびに、同じ u の範囲の走行跡の帯（spans）を、色の板（accent）として左右に重ねる。
    帯の外（色の帯の範囲 MARKING_COLOR_IN〜MARKING_PAVE_IN の外）へはみ出す分は切る"""
    orig_bands, orig_put_xy = M._color_bands, M._put_xy

    def put_xy(plan, axis):
        f = orig_put_xy(plan, axis)
        g = (lambda u0, u1, v0, v1: f(u0, u1, v0, v1))
        g.accent = (lambda u0, u1, v0, v1: plan.accent(u0, u1, v0, v1)) if axis == "x" else \
            (lambda u0, u1, v0, v1: plan.accent(v0, v1, u0, u1))
        return g

    def bands(put, u0, u1):
        orig_bands(put, u0, u1)
        if getattr(put, "__name__", "") == "accent":  # 赤の縞（縞そのものを accent で置く）には重ねない
            return
        acc = getattr(put, "accent", None) or put.__self__.accent
        lo, hi = M.MARKING_COLOR_IN, M.MARKING_PAVE_IN
        for a, b in spans:
            a, b = max(a, lo), min(b, hi)
            if b <= a:
                continue
            acc(u0, u1, a, b)
            acc(u0, u1, -b, -a)
    M._put_xy, M._color_bands = put_xy, bands


def _apron_ring(TT, w):
    """転車台のまわりのコンクリートを、タイルの四角から、ピットの縁（半径 TT_R）〜 TT_R + w の輪にする（角は地面が見える）"""
    from mathutils import Vector

    def apron(z):
        n = TT.TT_SEG
        inner = [Vector((x, y, z)) for x, y in TT._circle(TT.TT_R, n)]
        outer = [Vector((x, y, z)) for x, y in TT._circle(TT.TT_R + w, n)]
        return inner + outer, [tuple(reversed(f)) for f in TT._ring_faces(n)]
    TT._apron = apron


def _hut_window(TT, h, z_frac, rgb):
    """運転室の 4 面に、窓の暗い帯（高さ h、帯の下の端は壁の高さの z_frac）を回す。壁より 0.02 だけ外へ出した薄い箱"""
    orig = TT._hut
    spec = ("turntable_hut_window", rgb, 0.3)

    def hut(cx, cy, sx, sy, sz, z0, snow):
        obs = orig(cx, cy, sx, sy, sz, z0, snow)
        win = TT._obj("turntable_hut_window", [TT.box(cx, cy, z0 + sz * z_frac + h / 2, sx + 0.04, sy + 0.04, h)], spec)
        return obs + [win]
    TT._hut = hut


def _concrete(R, name, spec, n):
    kind, rgb, amp, grain, stain, grime = spec
    assert kind == "concrete", kind
    extra = dict(grime=grime, grime_z=(-0.55, 0.0)) if grime else {}  # 壁は床（-PIT_D - 床の厚み 約 -0.55）から縁（0）へ
    return lambda: R.tiled_concrete_material(f"r{n}_{name}", rgb, amp, grain, stain=stain, **extra)
