"""精細化のラウンド（#56）の、道路 3 種一式（基盤・高架・橋・トンネル・道路の壁・道路用の橋脚・歩道）の描き分け。blender/round.py が AMI_FAMILY=road のときに読む。

ROUND_SETTINGS: ラウンドの鍵（"1"・葉の試しの "1xxx" など）→ 設定。値の決め方は docs/records/ の各ラウンドの記録。
apply(cfg, n, R, render): 描く前に、render.py の設定（R.ROAD_PROFILES など）に cfg を重ねる。土台は今の render.py。
共有の tools/blender/sheetlib の値をモジュールごと書き換えない（ほかの系統の絵が変わる）。要るときは、描き分けの辞書の中で差し替える。

道路の描き分け（sheetlib の road_sheet）は、プロファイルの辞書から材質（skin）しか差し替えられない（部品の形を差し替える口が無い）。
形を変える試し（走行跡の帯の並びなど）は、この系統を描くプロセスの中でだけ sheetlib.sheetlib の ROAD_PARTS を差し替える
（render_parallel は対象ごとに別のプロセスで、AMI_FAMILY=road のプロセスは道路一式しか描かない）。本番に入れるときは、
road_sheet に部品の差し替えの口（線路の track_sheet の replace・parts と同じもの）を足して置き換える。

設定のキー（どれも無くてよい）:
    asph_k: 路面のまだらの明暗差を、2 色の平均から何倍離すか（生活道路・一般道路と高速道路の両方。走行跡・まだらの雪も同じ 2 色から作り直す）
    asph_scale: 路面のまだらの細かさ（ノイズの Scale。既定 60）
    asph_ramp: 路面のまだらの色の段の位置（既定は noisy_material の 0.35・0.65）。狭めるほど 2 色に分かれ、粒がはっきりする
        （ノイズの値はほとんど 0.4〜0.6 に入るので、2 色を離しても段が広いと明暗差が出ない。ラウンド 1 の 1asph で分かった）
    street_lift: 生活道路・一般道路の路面の 2 色の倍率（明るさ）
    expwy_lift: 高速道路の路面の 2 色の倍率（明るさ）
    street_spec: 生活道路・一般道路の路面・走行跡・まだらの雪の照り返しの強さ（既定 None = Blender の既定 0.5。高速道路は 0）
    wear_layers: 走行跡の帯の並び（road_parts の WEAR_LAYERS と同じ形。帯の並び, 寄せ具合, 行き止まりで開ける距離）
    wear_t: 走行跡の寄せ具合の倍率（wear_layers の後にかける）
    wear_t_expwy: 高速道路だけ、走行跡の寄せ具合にさらにかける倍率（暗い路面では、同じ寄せ具合でも走行跡が明るく出る）
    drop: 描かない部品の名前（"oil" など）
    conc: コンクリートの質感 (明暗の幅, Scale)。壁・基盤・躯体・橋脚の材質（名前 wall・base・elev_body・pier・pier_post・pier_beam）を、
        元の色の (1 - 幅)〜(1 + 幅) 倍のまだらにする。基盤・躯体・橋脚は材質を色の組（material(*mat)）でしか受けないので、このプロセスの
        中でだけ core・assemble・sheetlib の material を包んで、名前で差し替える（本番では描き分けに材質の口を足す）
    line: 白線の材質 (色, 発光)。road_parts の _M_LINE（色 0.95・発光 0.6）の代わりに、道路 3 種の skin の "line" に入れる
    snow: 歩道・縁石と路肩の雪 (明暗の幅, Scale[, 発光[, 色]])。core の _SNOW（一色。色を渡せばその色）を、その色を中心に ±幅 のまだらにする。road_parts の
        ROAD_SNOW_SKIN（道路の雪の絵の skin）をこのプロセスの中でだけ書き換え、sidewalk の _SNOW と ROAD_PARTS の snowbank も差し替える
    pave: 歩道の敷石。("noise", 暗い色, 明るい色, Scale) か ("brick", 敷石の色, 目地の色, Scale)。sidewalk.py の _M_PAVING を差し替える
"""
import dataclasses

ROUND_SETTINGS = {
    "0null": {},  # 作りの確かめ: 何も変えない（今の src/ とバイト単位で同じになるか）
    # ラウンド 1: 路面（アスファルトの粒と走行跡）。今は路面のまだらが弱く（線を除いた細かさ 0.011〜0.032。手本 0.024〜0.065）、
    # 走行跡の帯（片側の車線に 2 本 × 3 段）が明るい縞に見え、カーブで同心の弧が並ぶ
    #   1asph: 路面のまだらの明暗差を 2 倍。1asphf: さらに細かく（Scale 120）
    #   1wear: 走行跡の寄せ具合を半分。1wear1: 走行跡を広く薄い帯 1 段だけにする。1oil: 油の帯を描かない
    "1asph": {"asph_k": 2.0},
    "1asphf": {"asph_k": 2.0, "asph_scale": 120.0},
    "1wear": {"wear_t": 0.5},
    "1wear1": {"wear_layers": ((((0.55, 1.40), (1.80, 2.65)), 0.30, 0.0),)},
    "1oil": {"drop": ("oil",)},
    # 1asph は細かさがほとんど上がらなかった（セルで 0.0102 → 0.0126）。色の段を狭めて粒を出す
    #   1grain: 段を 0.44〜0.56。1grain2: 段を 0.40〜0.60 にして 2 色を 1.6 倍離す。1light: 生活道路・一般道路の路面を 1.4 倍明るく
    "1grain": {"asph_ramp": (0.44, 0.56)},
    "1grain2": {"asph_ramp": (0.40, 0.60), "asph_k": 1.6},
    "1light": {"street_lift": 1.4},
    # 1light でも明るさが 67 → 70 しか動かない。生活道路・一般道路の路面は照り返し（空の色の映り込み）が明るさの大半で、色とまだらが
    # 効かない（高速道路は照り返しを切ってある）。照り返しを切る
    #   1spec: 照り返しを切るだけ。1spec2: 照り返しを切り、路面を 1.6 倍明るく、粒を出す（段 0.40〜0.60、2 色を 1.6 倍離す）
    "1spec": {"street_spec": 0.0},
    "1spec2": {"street_spec": 0.0, "street_lift": 1.6, "asph_ramp": (0.40, 0.60), "asph_k": 1.6},
    # 1spec2 でも線を除いた細かさは 0.015。粒（Scale 60 で約 1px）が描くときの画素の平均で消える。粒を粗くする
    #   1g30・1g20: 1spec2 の粒を Scale 30・20（約 2px・3px）。1g30e: 1g30 を高速道路にも（高速道路は照り返しをもともと切ってある）
    "1g30": {"street_spec": 0.0, "street_lift": 1.6, "asph_ramp": (0.40, 0.60), "asph_k": 1.6, "asph_scale": 30.0},
    "1g20": {"street_spec": 0.0, "street_lift": 1.6, "asph_ramp": (0.40, 0.60), "asph_k": 1.6, "asph_scale": 20.0},
    # 粗くすると斑（SIS の一般道に近い）になり、細かさはあまり上がらない。iss の路面は 1 画素の粒。段をほぼ 2 値にして 1 画素の粒を出す
    #   1bin: 段 0.47〜0.53・Scale 60。1binw: 1bin に走行跡の寄せ具合を半分（1wear）を重ねる
    "1bin": {"street_spec": 0.0, "street_lift": 1.6, "asph_ramp": (0.47, 0.53), "asph_k": 1.4},
    "1binw": {"street_spec": 0.0, "street_lift": 1.6, "asph_ramp": (0.47, 0.53), "asph_k": 1.4, "wear_t": 0.5},
    # ラウンド 1: 1binw（照り返しを切り、路面を 1.6 倍明るく、1 画素の粒、走行跡を半分）。高速道路は 1binw でも暗い路面に走行跡の縞が
    # 残るので、高速道路の走行跡はさらに半分（元の 1/4）
    "1a": {"street_spec": 0.0, "street_lift": 1.6, "asph_ramp": (0.47, 0.53), "asph_k": 1.4, "wear_t": 0.5, "wear_t_expwy": 0.5},
    # 1a をゲームで撮ると、路面が暗くなった（一般道路 52 → 43、高速道路 29 → 24。手本の iss は 74・35、pak128 の Road_050 は 104）。
    # 照り返しと明るい走行跡が減った分。手本から離れる向きなので、路面の色を明るくして戻す
    #   1b: 生活道路・一般道路 2.4 倍、高速道路 1.4 倍
    "1b": {"street_spec": 0.0, "street_lift": 2.4, "expwy_lift": 1.4, "asph_ramp": (0.47, 0.53), "asph_k": 1.4, "wear_t": 0.5,
           "wear_t_expwy": 0.5},
    # ラウンド 1: 1b（セルの直線の明るさが前と同じになった）。高速道路の十字は走行跡が減って暗い（44 → 36）ので、高速道路は 1.6 倍
    "1": {"street_spec": 0.0, "street_lift": 2.4, "expwy_lift": 1.6, "asph_ramp": (0.47, 0.53), "asph_k": 1.4, "wear_t": 0.5,
          "wear_t_expwy": 0.5},
}
_R1 = ROUND_SETTINGS["1"]
ROUND_SETTINGS.update({
    # ラウンド 2: コンクリート（壁・基盤・躯体・橋脚）と歩道の敷石。どれも一色の板で、壁は明るい灰色の帯に見える。
    # 歩道は緑がかった強いまだら（暗 0.025〜明 0.26）で、砂利か草に見える（iss の歩道は赤い敷石と灰色の目地）
    #   2conc: コンクリートを ±12% のまだら（Scale 25）。2conc2: ±20%
    #   2pave: 歩道を灰色の弱いまだら。2brick: 歩道を灰色の敷石と暗い目地（Brick テクスチャ）
    "2conc": dict(_R1, conc=(0.12, 25.0)),
    "2conc2": dict(_R1, conc=(0.20, 25.0)),
    "2pave": dict(_R1, pave=("noise", (0.20, 0.20, 0.19), (0.34, 0.335, 0.32), 35.0)),
    "2brick": dict(_R1, pave=("brick", (0.30, 0.295, 0.28), (0.12, 0.12, 0.115), 1.2)),
    # 2brick は敷石が約 3 x 1.5px で、目地が細かい斜めの模様（モアレ）に見えた。敷石を倍の大きさに（2brick2）
    "2brick2": dict(_R1, pave=("brick", (0.30, 0.295, 0.28), (0.12, 0.12, 0.115), 0.6)),
    # ラウンド 2: 1 + コンクリートの質感 ±12%（2conc。±20% はざらついた）+ 歩道の敷石（2brick2）。敷石の模様のくどさはゲームで測る
    #   2p: 歩道だけ 2pave にした比べ（くどさで敷石が悪くなったときの代わり）
    "2": dict(_R1, conc=(0.12, 25.0), pave=("brick", (0.30, 0.295, 0.28), (0.12, 0.12, 0.115), 0.6)),
    "2p": dict(_R1, conc=(0.12, 25.0), pave=("noise", (0.20, 0.20, 0.19), (0.34, 0.335, 0.32), 35.0)),
})
_R2 = ROUND_SETTINGS["2"]
ROUND_SETTINGS.update({
    # ラウンド 3: 白線をくすませる試し（色 0.95・発光 0.6 で真っ白に出る）。3line: 色 0.85・発光 0.3。3line2: 色 0.75・発光 0.15
    # 描く前に手本の白線を測ると（ゲームの画面の way の画素で明るさ 150 以上の平均）、AMI 225 に対し iss 222〜223・SIS 202〜244 で
    # 同じ帯だった（低いのは明るい路面の pak128 Road_050 の 175 だけ）。くすませると手本から離れるので採らない
    "3line": dict(_R2, line=((0.85, 0.85, 0.83), 0.3)),
    "3line2": dict(_R2, line=((0.75, 0.75, 0.73), 0.15)),
    # ラウンド 3: 雪の歩道・縁石。一色の雪（core の _SNOW）で、ゲームでは地面の雪（明るさ 229、細かさ 3.9）より平らで暗い
    # （歩道の見本で 207、細かさ 1.4）。地面の雪の上に灰色の板が置いてあるように見える
    #   3snow: 雪を ±6% のまだら（Scale 60）。3snow2: ±10%
    "3snow": dict(_R2, snow=(0.06, 60.0)),
    "3snow2": dict(_R2, snow=(0.10, 60.0)),
    # 3snow2 で細かさは地面の雪と同じくらい（セルで 0.0148、地面 0.0151）。明るさは 210〜225 で地面 229 より暗いまま。
    #   3snow3: 3snow2 に発光 0.15 を足して明るさを地面に寄せる
    "3snow3": dict(_R2, snow=(0.10, 60.0, 0.15)),
    # 3snow3 をゲームで撮ると、明るさ（222、地面 229）と細かさ（3.5、地面 3.9）は地面の雪に近いが、色が少し緑がかる
    # （地面 227,227,240、歩道 221,225,229。青みが足りない）。3snow4: 雪の色を青みに寄せる
    "3snow4": dict(_R2, snow=(0.10, 60.0, 0.15, (0.86, 0.86, 0.97))),
    # 3snow4 で sheet_audit に新しい候補（歩道の雪のセル 5.5 に、透明色 231,255,255 に近い画素が 3 つ）が出た。青みの明るい粒が
    # 透明色に寄る。3snow5: 赤を少し足して（緑より赤を上に）透明色から離す
    "3snow5": dict(_R2, snow=(0.10, 60.0, 0.15, (0.88, 0.86, 0.97))),
    # ラウンド 3: 3snow5（雪の歩道・縁石・路肩の雪を、青みの色 0.88,0.86,0.97 を中心に ±10% のまだらと発光 0.15。
    # 歩道のセルで明るさ 225 → 236、細かさ 0.0043 → 0.0160、色 219,223,229 → 234,233,244）
    "3": dict(_R2, snow=(0.10, 60.0, 0.15, (0.88, 0.86, 0.97))),
})

STREET = ((0.013, 0.0135, 0.015), (0.028, 0.029, 0.031))  # 生活道路・一般道路の路面の 2 色（road_parts の _M_ROAD_ASPHALT）


def _away(lo, hi, k):
    m = [(a + b) / 2 for a, b in zip(lo, hi)]
    f = lambda c: tuple(max(0.0, mi + k * (x - mi)) for x, mi in zip(c, m))
    return f(lo), f(hi)


def _grain(R, name, lo, hi, scale, spec, ramp):
    """noisy_material に、色の段の位置（ramp）を渡せるようにしたもの。"""
    def make():
        m = R.noisy_material(name, lo, hi, scale=scale, rough=0.9, spec=spec)
        if ramp:
            el = next(nd for nd in m.node_tree.nodes if nd.type == "VALTORGB").color_ramp.elements
            el[0].position, el[1].position = ramp
        return m
    return make


def _skin(tag, lo, hi, scale, spec, layers, RP, R, ramp=None):
    """路面・走行跡・まだらの雪の材質（road_parts の asphalt_skin と同じ作りで、細かさと走行跡の段を渡せるもの）。"""
    out = {"asphalt": _grain(R, f"{tag}_asphalt", lo, hi, scale, spec, ramp)}
    out.update({f"wear{i}": RP._wear_material(tag, lo, hi, t, spec) for i, (_, t, _) in enumerate(layers)})
    out.update({nm: RP._slush_material(tag, lo, hi, t, spec) for nm, _, t, _, _ in RP.SNOW_LAYERS if t is not None})
    return out


CONC_NAMES = ("wall", "base", "elev_body", "pier", "pier_post", "pier_beam")


def _wrap_material(mods, table):
    """material(name, rgb, ...) を包み、name が table にあれば、その材質を返す関数を呼ぶ。"""
    for m in mods:
        orig = m.material
        if getattr(orig, "_round_wrapped", False):
            continue

        def material(name, *a, _orig=orig, **kw):
            return table[name]() if name in table else _orig(name, *a, **kw)
        material._round_wrapped = True
        m.material = material


def _brick(name, rgb, mortar, scale):
    """敷石の材質: Blender の Brick テクスチャ（物の座標。タイルをまたいでも目地がそろう）。"""
    def make():
        import bpy
        if name in bpy.data.materials:
            return bpy.data.materials[name]
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        tc = nt.nodes.new("ShaderNodeTexCoord")
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.inputs["Scale"].default_value = scale
        br.inputs["Color1"].default_value = (*rgb, 1)
        br.inputs["Color2"].default_value = (*(x * 0.85 for x in rgb), 1)
        br.inputs["Mortar"].default_value = (*mortar, 1)
        br.inputs["Mortar Size"].default_value = 0.03
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
        nt.links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.9
        return m
    return make


def apply(cfg, n, R, render):
    import os
    import sheetlib.road_parts as RP  # noqa: E402
    import sheetlib.sheetlib as S  # noqa: E402
    import sheetlib.sidewalk as SW  # noqa: E402

    # 歩道（sidewalk.py）は一時フォルダ WORK を名前で取り込んでいて、round.py の _run が切り替える core・cells・sheetlib の WORK に
    # 付いていかない。持ち分の画像（_own.png）を work/ に書き、cells はラウンドの一時フォルダから読むので、絵がずれた（2026-11-20）。
    # round.py の _run と同じフォルダにそろえる（round.py を直すまでの間）
    SW.WORK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work", "rounds", "road", f"round{n}", "tmp")

    layers = tuple(cfg.get("wear_layers", RP.WEAR_LAYERS))
    if "wear_t" in cfg:
        layers = tuple((sp, t * cfg["wear_t"], f) for sp, t, f in layers)
    parts = [p for p in S.ROAD_PARTS if not p.name.startswith("wear")]
    old_wear = next(p for p in S.ROAD_PARTS if p.name == "wear0")
    i_oil = next(i for i, p in enumerate(parts) if p.name == "oil")
    wear = [dataclasses.replace(old_wear, name=f"wear{i}", material=RP._wear_material("street", *STREET, t),
                                shape=RP._lane_strips(sp, 0.0015 * i, fade=f)) for i, (sp, t, f) in enumerate(layers)]
    parts[i_oil + 1:i_oil + 1] = wear
    parts = [p for p in parts if p.name not in cfg.get("drop", ())]
    S.ROAD_PARTS = tuple(parts)

    if "conc" in cfg:
        import sys
        import sheetlib.wall_parts as WP  # noqa: E402
        # 名前が関数と重なるモジュールがある（sheetlib の assemble）ので、sys.modules から取る（round.py と同じ）
        A, K = sys.modules["sheetlib.assemble"], sys.modules["sheetlib.core"]
        c, sc = cfg["conc"]
        base = {"wall": WP._M_WALL, "base": WP._M_BASE, "elev_body": WP._M_ELEV_BODY, "pier": WP._M_PIER,
                "pier_post": WP._M_PIER_POST, "pier_beam": WP._M_PIER_BEAM}
        # c・sc は既定の引数で縛る（材質は描くときに呼ばれるので、後の設定が同じ名前を使うと値が変わる。ラウンド 3 の初めの版で起きた）
        table = {nm: (lambda nm=nm, rgb=spec[1], c=c, sc=sc: R.noisy_material(f"r{n}_{nm}", tuple(x * (1 - c) for x in rgb),
                                                                              tuple(x * (1 + c) for x in rgb), scale=sc, rough=0.9))
                 for nm, spec in base.items()}
        _wrap_material((K, A, S), table)
    if "snow" in cfg:
        from sheetlib.core import _SNOW
        sw, ssc, sem, srgb = (tuple(cfg["snow"]) + (0.0, _SNOW[1])[len(cfg["snow"]) - 2:])[:4]
        snow = lambda: R.noisy_material(f"r{n}_snow", tuple(x * (1 - sw) for x in srgb),
                                        tuple(min(1.0, x * (1 + sw)) for x in srgb), scale=ssc, rough=0.9, emit=sem)
        RP.ROAD_SNOW_SKIN.update(curb=snow, paving=snow)  # sheetlib が名前で取り込んだのと同じ辞書
        SW._SNOW = snow
        S.ROAD_PARTS = tuple(dataclasses.replace(p, material=snow) if p.name == "snowbank" else p for p in S.ROAD_PARTS)
    if "pave" in cfg:
        kind, *v = cfg["pave"]
        SW._M_PAVING = (_brick(f"r{n}_paving", *v) if kind == "brick" else
                        (lambda: R.noisy_material(f"r{n}_paving", v[0], v[1], scale=v[2])))

    k, scale, ramp = cfg.get("asph_k", 1.0), cfg.get("asph_scale", 60.0), cfg.get("asph_ramp")
    lift = cfg.get("street_lift", 1.0)
    street_rgb = tuple(tuple(x * lift for x in c) for c in STREET)
    street = _skin(f"r{n}street", *_away(*street_rgb, k), scale, cfg.get("street_spec"), layers, RP, R, ramp)
    xl = tuple((sp, t * cfg.get("wear_t_expwy", 1.0), f) for sp, t, f in layers)
    xlift = cfg.get("expwy_lift", 1.0)
    expwy_rgb = tuple(tuple(x * xlift for x in c) for c in RP.EXPWY_ASPHALT)
    expwy = _skin(f"r{n}expwy", *_away(*expwy_rgb, k), scale, 0.0, xl, RP, R, ramp)
    for prof in R.ROAD_PROFILES.values():
        sheet = str(prof.get("sheet", ""))
        if not sheet.startswith(("ami_road_", "ami_wall_road_")):
            continue
        base = expwy if "expressway" in sheet else street
        if "line" in cfg:
            base = dict(base, line=(f"r{n}_line", cfg["line"][0], 0.6, 0.0, cfg["line"][1]))
        prof["skin"] = dict(prof.get("skin", {}), **base)
