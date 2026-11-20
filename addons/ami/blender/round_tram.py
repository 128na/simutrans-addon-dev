"""精細化のラウンド（#56）の、路面軌道の描き分け。blender/round.py が AMI_FAMILY=tram のときに読む。

ROUND_SETTINGS: ラウンドの鍵（"1"・葉の試しの "1xxx" など）→ 設定。値の決め方は docs/records/ の各ラウンドの記録。
apply(cfg, n, R, render): 描く前に、render.py の設定（R.TRACK_PROFILES など）に cfg を重ねる。土台は今の render.py。
共有の tools/blender/sheetlib の値をモジュールごと書き換えない（ほかの系統の絵が変わる）。要るときは、描き分けの辞書の中で差し替える。

路面軌道の部品（sheetlib の tram_parts）は、寸法を部品を作るときに形へ焼き込んでいる。定数を書き換えても効かないので、
apply は cfg の値で部品（TRAM_TRACK_PARTS と汚れの TRAM_WEAR_REPLACE に当たるもの）を作り直し、描き分けの辞書の写しに入れる。
cfg の鍵（無ければ今の本番の値）:
  rail       レールの頭の (u0, u1)（経路の中心から）。rail_rgb はその色
  groove     レールの内側の溝の幅。groove_rgb はその色
  seam       レールの外側の目地の幅（0 で描かない）
  bed        床のまだらの (lo, hi)。bed_grain はまだらの細かさ
  edge_u0    縁の明るい帯の内側（外側は床の縁 TRAM_BED_U）。edge_rgb はその色
  wear       汚れの帯 {名前: ((u0, u1), さび色への寄せ具合)}。oil は (半幅, 寄せ具合)。drop は描かない帯の名前
  joint      床の目地（横向きの暗い線）の (間隔, 幅)。間隔はタイルの辺から数え、タイルの継ぎ目でそろう
雪の絵は夏と同じ（README の路面軌道の項目。除雪された想定）なので、汚れの帯を作り直したら snow_skin も同じ材質にする。
"""

ROUND_SETTINGS = {
    "0check": {},  # 描き直しが本番の src/ と同じになるかを確かめる（設定なし）
    "0same": {"seam": 0.05},  # 部品を作り直す道（apply）を通して、本番と同じ値で描く（作り直しが本番と同じになるか）
    # ラウンド 1: レール（頭・溝・目地）。今は明るい頭が 1px に満たず、溝・目地の暗さと混ざって、灰色の帯に暗い細線が 2 本に見える
    #   noseam: 外側の目地を描かない。head: 頭を 0.14 に。headw: 0.17 に。headg: headw + 溝を 0.14 に。headgs: headg + 目地を戻す
    "1noseam": {"seam": 0},
    "1head": {"rail": (0.40, 0.54), "seam": 0},
    "1headw": {"rail": (0.385, 0.555), "seam": 0},
    "1headg": {"rail": (0.385, 0.555), "groove": 0.14, "seam": 0},
    "1headgs": {"rail": (0.385, 0.555), "groove": 0.14},
    # 頭が明るく出ないのは、金属（0.8）の材質が環境を映して暗く写るため（シートで頭の画素は 145 前後、床は 135 前後）。
    #   在来線のラウンド 3 の頭の帯（0.92, 0.91, 0.88、粗さ 0.4、金属 0）にする。dull: 金属 0 の今の色
    "1bright": {"rail_mat": ((0.92, 0.91, 0.88), 0.4, 0.0)},
    "1dull": {"rail_mat": ((0.82, 0.81, 0.79), 0.4, 0.0)},
    "1brighth": {"rail_mat": ((0.92, 0.91, 0.88), 0.4, 0.0), "rail": (0.40, 0.54), "seam": 0},
    "1brighthg": {"rail_mat": ((0.92, 0.91, 0.88), 0.4, 0.0), "rail": (0.40, 0.54), "groove": 0.14, "seam": 0},
    "1brightw": {"rail_mat": ((0.92, 0.91, 0.88), 0.4, 0.0), "rail": (0.385, 0.555), "seam": 0},
    # ラウンド 1: 金属でない明るい頭を 0.14 に、溝を 0.14 に、目地なし（= 1brighthg）。シートの縦の切り口で、頭 195・溝 92〜110・床 135〜145
    "1": {"rail_mat": ((0.92, 0.91, 0.88), 0.4, 0.0), "rail": (0.40, 0.54), "groove": 0.14, "seam": 0},
}


def apply(cfg, n, R, render):
    import math
    from dataclasses import replace

    import sheetlib.tram_parts as TM
    from mathutils import Vector

    if not cfg:
        return
    tag = f"_r{n}"
    prof = dict(R.TRACK_PROFILES[render.TRAM_KEY])
    base = {p.name: p for p in TM.TRAM_TRACK_PARTS}

    bed_u = TM.TRAM_BED_U
    edge_u0 = cfg.get("edge_u0", TM.TRAM_EDGE_U0)
    bed_lo, bed_hi = cfg.get("bed", (TM.TRAM_BED_LO, TM.TRAM_BED_HI))
    bed_rgb = tuple((a + b) / 2 for a, b in zip(bed_lo, bed_hi))
    rail_in, rail_out = cfg.get("rail", (TM.RAIL_IN, TM.RAIL_OUT))
    groove_w = cfg.get("groove", TM.TRAM_GROOVE_W)
    seam_w = cfg.get("seam", TM.TRAM_SEAM_W)

    m_bed = TM.track_noise("tram_bed" + tag, bed_lo, bed_hi, cfg.get("bed_grain", TM.TRAM_BED_GRAIN))
    m_edge = ("tram_edge" + tag, cfg.get("edge_rgb", TM.TRAM_EDGE_RGB), 0.8)
    m_groove = ("tram_groove" + tag, cfg.get("groove_rgb", TM.TRAM_GROOVE_RGB), 0.9)
    rail_mat = TM._M_TRAM_RAIL
    if "rail_rgb" in cfg:
        rail_mat = ("tram_rail" + tag, cfg["rail_rgb"]) + tuple(rail_mat[2:])
    if "rail_mat" in cfg:  # (色, 粗さ, 金属)。本番は金属 0.8 で、環境を映して暗く写る
        rail_mat = ("tram_rail" + tag,) + tuple(cfg["rail_mat"])

    def rail_shape(side):
        def shape(path, k):
            a, b = rail_in * k, rail_out * k
            sec = TM._section(-b, -a, TM.TRAM_RAIL_Z0, TM.TRAM_RAIL_Z1) if side < 0 else TM._section(a, b, TM.TRAM_RAIL_Z0, TM.TRAM_RAIL_Z1)
            return TM.sweep(path, sec)
        return shape

    gz = TM.TRAM_GROOVE_Z
    parts = [
        replace(base["tram_edge"], material=m_edge),
        replace(base["tram_bed"], material=m_bed,
                shape=TM._to_edge(TM._slab_shape(edge_u0, TM.TRAM_BED_Z0, TM.TRAM_BED_Z1), bed_u - edge_u0)),
    ]
    if groove_w > 0:
        parts.append(replace(base["tram_groove"], material=m_groove,
                             shape=TM._pair_shape(rail_in - groove_w, rail_in, gz, gz + TM.TRAM_TH)))
    if seam_w > 0:
        parts.append(replace(base["tram_seam"], material=m_groove,
                             shape=TM._pair_shape(rail_out, rail_out + seam_w, gz, gz + TM.TRAM_TH)))
    if "joint" in cfg:
        pitch, jw = cfg["joint"]
        jrgb = cfg.get("joint_rgb", (0.20, 0.20, 0.19))
        jz = TM.TRAM_BED_Z1 + 0.0009  # 汚れの帯の上、溝・レールの下

        def joint(path, k, pitch=pitch, jw=jw):
            # 経路に沿って、タイルの辺（経路の座標でタイルの中心から ±5）から pitch ごとに横向きの細い板を置く。
            # 行き止まりの経路は、床のある所（_to_edge で延ばした所）まで置く
            boxes = []
            e = TM._edge_reach(path)
            pts = list(path)
            if e is not None:
                reach, d = e
                pts = [pts[0] - d * (reach - (bed_u - edge_u0))] + pts
            half = edge_u0 * k
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                seg = b - a
                L = seg.length
                if L < 1e-6:
                    continue
                dvec = seg / L
                ang = math.atan2(dvec.y, dvec.x)
                # 経路に沿う座標 t（タイルの中心から経路の向きに測る）が、タイルの辺（t = 5）から pitch の倍数になる所に置く。
                # pitch が 10 を割り切れば、直線はタイルの継ぎ目で間隔がそろう
                t0 = (a.to_2d()).dot(dvec.to_2d())
                t1 = t0 + L
                m0 = math.ceil((t0 - 5.0) / pitch - 1e-6)
                m1 = math.floor((t1 - 5.0) / pitch + 1e-6)
                for m in range(m0, m1 + 1):
                    t = 5.0 + m * pitch
                    c = a + dvec * (t - t0)
                    boxes.append(R.box(c.x, c.y, jz, jw, 2 * half, 0.0005, rot=ang))
            return R.merge(boxes) if boxes else None
        parts.append(R.Part("tram_joint", "tram_bed", "bed", ("tram_joint" + tag, jrgb, 0.9), joint, centre=False))
    parts += [replace(base["railL"], material=rail_mat, shape=rail_shape(-1)),
              replace(base["railR"], material=rail_mat, shape=rail_shape(1))]
    prof["track_parts"] = tuple(parts)

    # 汚れの帯
    wear_cfg = cfg.get("wear", {})
    drop = set(cfg.get("drop", ()))
    rep = dict(prof.get("replace", {}))
    snow = dict(prof.get("snow_skin", {}))
    for i, (name, (u0, u1), t) in enumerate(TM.TRAM_WEAR):
        (u0, u1), t = wear_cfg.get(name, ((u0, u1), t))
        mat = TM.track_noise(f"tram_{name}{tag}", TM._mix(bed_rgb, TM._RUST_LO, t), TM._mix(bed_rgb, TM._RUST_HI, t), 3.0)
        shape = (lambda path, k: None) if name in drop else TM._wear_pair(u0, u1, TM._wear_z(i))
        rep[name] = replace(rep[name], material=mat, shape=shape)
        snow[name] = mat
    ou, ot = wear_cfg.get("oil", (TM.TRAM_OIL_U, TM.TRAM_OIL_T))
    mat = TM.track_noise(f"tram_oil{tag}", TM._mix(bed_rgb, TM._OIL_LO, ot), TM._mix(bed_rgb, TM._OIL_HI, ot), 3.0)
    shape = (lambda path, k: None) if "oil" in drop else TM._wear_centre(ou, TM._wear_z(len(TM.TRAM_WEAR)))
    rep["oil"] = replace(rep["oil"], material=mat, shape=shape)
    snow["oil"] = mat
    prof["replace"] = rep
    prof["snow_skin"] = snow
    R.TRACK_PROFILES[render.TRAM_KEY] = prof
