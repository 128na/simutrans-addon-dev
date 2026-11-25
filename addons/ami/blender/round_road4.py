"""精細化のラウンド（#56 の流れ。#256）の、第 4 弾の物（幹線道路・円弧と L 字の一般道路・生活道路・Y 字と三方分岐の絵）の描き分け。
blender/round.py が AMI_FAMILY=road4 のときに読む。

土台は今の本番（render.py の道路一式の質感。ラウンド 3 まで入れ済み）。round_road.py の apply は入れる前の本番に重ねる作りで、
今の本番に重ねると質感が二重になるので使わない。ここは本番の描き分け（R.ROAD_PROFILES の skin）には触らず、部品の追加と材質の差し替えだけをする。

ROUND_SETTINGS: ラウンドの鍵（"1"・葉の試しの "1xxx"）→ 設定。値の決め方は docs/records/ の記録。
設定のキー（どれも無くてよい）:
    shoulder: 路肩の砂ぼこりの帯 (内側の離れ, 外側の離れ, 暗い色, 明るい色, Scale)。路側の白線（実線）の外へ、白線の縁から内側の離れ〜外側の離れ
        の帯を 1 本ずつ敷く。白線と同じ部品（where="line"）なので、分岐・十字・T字・Y 字の線の切れ目・V 字の角にそのまま沿う
    line_chip: 白線のかすれ (色の暗い側, 色の明るい側, Scale, 発光, ramp)。白線を一色の白から、まだらにかすれた白へ替える
apply(cfg, n, R, render): 描く前に、sheetlib の部品の並びと render.py の描き分けを、このプロセスの中でだけ差し替える。
"""
import dataclasses

ROUND_SETTINGS = {
    "0null": {},  # 作りの確かめ: 何も変えない（今の src/ とバイト単位で同じになるか）
    # 路面は一色のアスファルトで、白線の外の路肩（路側線からタイルの端まで）も走行面と同じ。路肩は砂・土ぼこりが吹き寄せる所
    #   1sh: 白線の外 0.2〜1.3 に、砂色のまだらの帯。1sh2: 帯を白線の外 0.1〜0.9 に狭める
    "1sh": {"shoulder": (0.2, 1.3, (0.05, 0.047, 0.040), (0.11, 0.100, 0.085), 40.0)},
    "1sh2": {"shoulder": (0.1, 0.9, (0.05, 0.047, 0.040), (0.11, 0.100, 0.085), 40.0)},
    # 白線は一色の白（色 0.95・発光 0.6）で、新品のように均一。まだらにかすれさせる
    #   1ch: 暗い側 0.45・明るい側 0.95。1ch2: 暗い側 0.65
    "1ch": {"line_chip": (0.45, 0.95, 14.0, 0.5, (0.40, 0.60))},
    "1ch2": {"line_chip": (0.65, 0.95, 14.0, 0.55, (0.40, 0.60))},
    # 1sh は帯が一様で縁石のように見え、分岐の口で四角く切れる。1ch・1ch2 は 1px の線で平均されて、ほとんど見えない
    #   1sh3: 帯を細く（0.15〜0.8）、2 色の差を小さく、粒を粗く、色の段を広げて（0.3〜0.7）まだらにする
    #   1sh4: 1sh3 を砂色から灰色の粉に寄せる。1ch3: かすれを強く（暗い側 0.2・Scale 8・段 0.35〜0.55）
    "1sh3": {"shoulder": (0.15, 0.8, (0.045, 0.043, 0.038), (0.085, 0.080, 0.070), 22.0, (0.30, 0.70))},
    "1sh4": {"shoulder": (0.15, 0.8, (0.04, 0.04, 0.038), (0.08, 0.078, 0.072), 22.0, (0.30, 0.70))},
    "1ch3": {"line_chip": (0.20, 0.95, 8.0, 0.45, (0.35, 0.55))},
}


def _shoulder_part(K, RP, R, cfg, n):
    """路側の白線の外の帯（where="line" の部品）。線ごとに呼ばれ、実線の路側線（|u| > 3 で幅 LINE_W）以外は路面の下に隠す"""
    d0, d1, lo, hi, scale, *rest = cfg["shoulder"]
    ramp = rest[0] if rest else (0.35, 0.65)
    LW = RP.LINE_W

    def shape(path, u, lw, k):
        edge = abs(u) > 3.0 and abs(lw - LW) < 1e-6
        s = 1.0 if u >= 0 else -1.0
        z, th = (0.0, 0.004) if edge else (-0.06, 0.004)
        a, b = (u + s * (lw / 2 + d0)) * k, (u + s * (lw / 2 + d1)) * k
        return K.sweep(path, [(a, z), (b, z), (b, z + th), (a, z + th)][::int(s)])
    mat = lambda: R.noisy_material(f"r{n}_shoulder", lo, hi, scale=scale, rough=0.95, ramp=ramp)
    return K.Part("shoulder", "bed", "road", mat, shape, "marking", "line")


def apply(cfg, n, R, render):
    import sheetlib.road_parts as RP  # noqa: E402
    import sys
    import sheetlib.sheetlib as S  # noqa: E402
    K = sys.modules["sheetlib.core"]  # sweep・Part（sheetlib が再輸出していない。round_road.py と同じ取り方）

    if "shoulder" in cfg:
        parts = list(S.ROAD_PARTS)
        i = next(i for i, p in enumerate(parts) if p.name == "line")
        parts.insert(i, _shoulder_part(K, RP, R, cfg, n))  # 白線の下（先に作る）
        S.ROAD_PARTS = tuple(parts)
    if "line_chip" in cfg:
        lo, hi, scale, emit, ramp = cfg["line_chip"]
        line = lambda: R.noisy_material(f"r{n}_line", (lo,) * 3, (hi,) * 3, scale=scale, rough=0.0, emit=emit, ramp=ramp)
        for prof in R.ROAD_PROFILES.values():
            sheet = str(prof.get("sheet", ""))
            if sheet.startswith(("ami_road_", "ami_wall_road_")):
                prof["skin"] = dict(prof.get("skin", {}), line=line)
