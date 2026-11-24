"""精細化のラウンド（#56 の流れ。#197）の、第 3 弾の物（路面表示・運河と景観の運河）の描き分け。blender/round.py が AMI_FAMILY=wave3 のときに読む

ROUND_SETTINGS: ラウンドの鍵（"1"・葉の試しの "1xxx"）→ 設定。値の決め方は docs/records/ の記録。
apply(cfg, n, R, render): 描く前に、render.py の設定と sheetlib の材質を、このプロセスの中でだけ差し替える（描くプロセスは対象ごとに別。
共有の sheetlib の値をモジュールごと書き換えない）。

ラウンド 1・2 の設定は、PR #214（汚し A・B）を入れた後の本番の render.py に重ねる作りだった。その後、ユーザーが選んだ葉（1wl2・2slush6）は
PR #218 で本番（render.py の `MARKING_SLUSH_T`、canal.py の `SCENIC_STYLE` の `waterline`）に入った。**今の本番に、入れ済みの葉を重ねると二重にかかる**ので、
ROUND_SETTINGS の "1"・"2" をそのまま描き直さない（記録のために残してある）。次のラウンドを回すときは、今の本番を土台にした設定を新しく足す。
入れなかった葉: 1chip2（1px の路側線が点々に切れる）、2wl3（染みが長くてくどい）、1rip（さざ波。PR #214 で取り下げた）。

意味の木（第 3 弾の物）: docs/records/2026-11-23_ami-wave3-refine-round1.md

設定のキー（どれも無くてよい）:
    chip: 白線の塗料の欠け。(欠けの色, 欠けの段の位置の上端, Scale)。路面表示の白線の材質（render.MARKING_LINE_WORN）を、
        2 色の段の下端が欠け（路面の色）になるまだらに替える
    waterline: 景観の運河の護岸の水際の染み。(染みの色, 水面からの高さ, 混ぜる強さ)。壁の材質に、水面から上へ薄れる暗い帯を重ねる
"""

ROUND_SETTINGS = {
    "0null": {},  # 作りの確かめ: 何も変えない（今の src/ とバイト単位で同じになるか）
    # 葉ごとの試し
    "1chip": {"chip": ((0.30, 0.30, 0.32), 0.43, 12.0)},
    "1wl": {"waterline": ((0.10, 0.15, 0.13), 0.7, 0.75)},
    "1wl2": {"waterline": ((0.06, 0.12, 0.10), 1.2, 1.0)},
    "1chip2": {"chip": ((0.30, 0.30, 0.32), 0.41, 12.0)},
    # ラウンド 2（土台は 1）: 雪の縁のぼかしの段を 4 → 6（幅は同じ 0.8 のまま細かく）、水際の染みをもう少し長く
    "2slush6": {"slush": ((0.80, 0.20), (0.67, 0.32), (0.53, 0.44), (0.40, 0.58), (0.27, 0.72), (0.13, 0.86))},
    "2wl3": {"waterline": ((0.06, 0.12, 0.10), 1.8, 1.0)},
}
# ラウンド 1 は、採った葉を合わせる（記録の評価のあとで決める）
# 運河の水面の葉（さざ波。1rip）は、PR #214 でさざ波を取り下げた（交差点と直線で波が連続しない。ユーザーの指摘）ので入れない
ROUND_SETTINGS["1"] = dict(ROUND_SETTINGS["1wl2"], **ROUND_SETTINGS["1chip2"])
# 2wl3（染みを長く）は壁が灰緑に汚れてくどくなったので採らない
ROUND_SETTINGS["2"] = dict(ROUND_SETTINGS["1"], **ROUND_SETTINGS["2slush6"])


def apply(cfg, n, R, render):
    import sheetlib.canal as CA  # noqa: E402

    if "chip" in cfg:
        rgb, top, scale = cfg["chip"]
        worn = render.MARKING_WORN
        render.MARKING_LINE_WORN = lambda: R.noisy_material(
            f"r{n}_marking_chip", rgb, worn[1], scale=scale, rough=0.6, emit=0.35, ramp=(top - 0.03, top))
    if "slush" in cfg:
        render.MARKING_SLUSH = tuple((d, render._marking_slush(t)) for d, t in cfg["slush"])
    if "waterline" in cfg:
        stain, height, k = cfg["waterline"]
        orig_materials = CA._materials

        def materials(st, snow):
            water, wall, cop = orig_materials(st, snow)
            if "wall_col" not in st:
                return water, wall, cop
            return water, _waterline(R, wall, stain, st["water_z"], height, k, n), cop
        CA._materials = materials


def _waterline(R, wall, stain, water_z, height, k, n):
    """壁の材質の複製に、水面（water_z）から height だけ上へ薄れる暗い帯（stain の色、強さ k）を、物の座標の高さで重ねる。"""
    import bpy
    name = f"r{n}_wall_waterline"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = wall.copy()
    m.name = name
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    base = bsdf.inputs["Base Color"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.clamp = True
    rng.inputs["From Min"].default_value = water_z
    rng.inputs["From Max"].default_value = water_z + height
    rng.inputs["To Min"].default_value = k
    rng.inputs["To Max"].default_value = 0.0
    nt.links.new(sep.outputs["Z"], rng.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(rng.outputs["Result"], mix.inputs["Factor"])
    nt.links.new(base, mix.inputs["A"])
    mix.inputs["B"].default_value = (*stain, 1)
    nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    # 壁は発光（emit 0.6）で明るく見せているので、発光の色にも同じ帯を掛ける
    emis = bsdf.inputs["Emission Color"]
    if emis.links:
        nt.links.new(mix.outputs["Result"], emis)
    return m
