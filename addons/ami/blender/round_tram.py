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
_R1 = ROUND_SETTINGS["1"]
ROUND_SETTINGS.update({
    # ラウンド 2: 欠陥（T字の穴）と床。gore: T字・十字の曲線と直線のあいだを床で埋める
    "2gore": dict(_R1, gore=True),
    "2gored": dict(_R1, gore=True, gore_debug=True),  # 埋めた所を赤で見る（確かめ用）
    # 床（コンクリートの継ぎ目）と縁の帯。ラウンド 1 で頭が明るくなり、縁の帯（約 195）と頭（約 195）の明るい線が 4 本並ぶ
    #   joint: 床の横向きの目地（間隔 2.5、幅 0.08。タイルに 4 本）。joint5: 間隔 5（タイルに 2 本）
    #   edged: 縁の帯を暗く（0.66, 0.65, 0.61）。edgen: 縁の帯を細く（内側 0.87 → 0.92）
    "2joint": dict(_R1, gore=True, joint=(2.5, 0.08)),
    "2joint5": dict(_R1, gore=True, joint=(5.0, 0.08)),
    "2edged": dict(_R1, gore=True, edge_rgb=(0.66, 0.65, 0.61)),
    "2edgen": dict(_R1, gore=True, edge_u0=0.92),
    # ラウンド 2: T字の穴を埋め（2gore）、縁の帯を暗く（2edged）。目地は 1px に満たず見えないので採らない
    "2": dict(_R1, gore=True, edge_rgb=(0.66, 0.65, 0.61)),
})
_R2 = ROUND_SETTINGS["2"]
ROUND_SETTINGS.update({
    # ラウンド 3: 汚れの帯（さび 2 本 rust0・rust1、油 oil）。今はレールの周りの床が、帯の重なりでレールの間ほど暗い
    #   nowear: 帯を全部描かない（汚れの帯の効きを見る）。oiloff: 油を描かない。rust0off: 外の広いさびを描かない。
    #   tight: さびを溝の内（車輪のフランジの当たる所）と頭の外のすぐ脇の細い帯 1 本に寄せる（rust1 を細く濃く、rust0 なし）
    "3nowear": dict(_R2, drop=("rust0", "rust1", "oil")),
    "3oiloff": dict(_R2, drop=("oil",)),
    "3rust0off": dict(_R2, drop=("rust0",)),
    "3tight": dict(_R2, drop=("rust0",), wear={"rust1": ((0.40 - 0.14 - 0.06, 0.54 + 0.08), 0.85)}),
    # ラウンド 3: 油の帯を描かない（= 3oiloff）。電車は油を落とさず、レールの間だけが暗い理由が無い。くどさは線を除いて細かさ 0.0484 → 0.0520・
    # 孤立点 9.09 → 11.65。帯を全部消す 3nowear は、床のまだらがむき出しになり孤立点が 33.6 に上がった（汚れの帯がまだらをならしている）
    "3": dict(_R2, drop=("oil",)),
})
_R3 = ROUND_SETTINGS["3"]
ROUND_SETTINGS.update({
    # ラウンド 4: 画面で横向きの斜め（diag_nw・diag_se・close1）のレール。本番からレールの線が見えない（頭も溝も 1px に満たない）。
    #   hdiag<n>: 横向きの斜めだけ、頭と溝の幅を n/10 倍にする（頭の中心は同じ）
    "4hdiag18": dict(_R3, hdiag=1.8),
    "4hdiag22": dict(_R3, hdiag=2.2),
    "4hdiag26": dict(_R3, hdiag=2.6),
    # 曲線にも点ごとの向きで効かせた版（var_sweep）。横向きの所で 2 本の溝がくっつき、暗い太い帯になったので、溝の倍率を下げる
    "4hd22g14": dict(_R3, hdiag=2.2, hdiag_groove=1.4),
    "4hd22g17": dict(_R3, hdiag=2.2, hdiag_groove=1.7),
    "4hd18g14": dict(_R3, hdiag=1.8, hdiag_groove=1.4),
    # ラウンド 4: 横向きの斜めと曲線の横向きの所で、頭を 2.2 倍・溝を 1.4 倍（= 4hd22g14）。斜めの切り口で頭 198・溝 102〜132、
    # 曲線の中ほどで 頭 203・溝 86・床 152・溝 83・頭 202（直線と同じ並び）
    "4": dict(_R3, hdiag=2.2, hdiag_groove=1.4),
})


def apply(cfg, n, R, render):
    import math
    import sys
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

    hf = cfg.get("hdiag", 1.0)
    gf = cfg.get("hdiag_groove", hf)  # 溝の倍率（無ければ頭と同じ）

    def widen(t, f=None):
        """経路の向き t での、頭と溝の幅の倍率。画面で横向きの斜め（北東–南西へ走る経路。北と西の辺をつなぐ diag_nw・
        南と東の辺をつなぐ diag_se・近い斜めの close1。経路の座標 x は東・y は北で、t.x * t.y > 0）で hf、軸の向きと縦向きの斜めで 1。
        横向きの斜めでは、経路に直角な向きが画面の縦になり、1 単位が約 4.5px（直線・縦向きの斜めは約 9px）で、頭と溝が 1px に満たず
        消える（diag_nw・diag_se・close1 と、曲線の中ほど）。曲線は点ごとの向きで倍率を変える"""
        f = hf if f is None else f
        if f == 1.0:
            return 1.0
        h = max(0.0, 2 * t.x * t.y / max(t.length_squared, 1e-12))
        return 1.0 + (f - 1.0) * h

    def var_sweep(path, section):
        """core.sweep と同じ押し出しで、断面を点ごとの向き t から section(t) で決める"""
        rings = []
        for i, p in enumerate(path):
            a_ = path[max(i - 1, 0)]
            b_ = path[min(i + 1, len(path) - 1)]
            t = (b_ - a_).normalized()
            nv = Vector((t.y, -t.x, 0))
            rings.append([Vector((p.x, p.y, 0)) + nv * u + Vector((0, 0, v)) for u, v in section(t)])
        k_ = len(rings[0])
        verts = [v for ring in rings for v in ring]
        faces = []
        for i in range(len(rings) - 1):
            for j in range(k_):
                j2 = (j + 1) % k_
                faces.append((i * k_ + j, i * k_ + j2, (i + 1) * k_ + j2, (i + 1) * k_ + j))
        faces.append(tuple(reversed(range(k_))))
        last = (len(rings) - 1) * k_
        faces.append(tuple(last + j for j in range(k_)))
        return verts, faces

    def head_span(t):
        """レールの頭の (u0, u1)。頭の中心のまま、幅を widen(t) 倍にする"""
        c, h = (rail_in + rail_out) / 2, (rail_out - rail_in) / 2 * widen(t)
        return c - h, c + h

    def rail_shape(side):
        def shape(path, k):
            def section(t):
                a, b = (u * k for u in head_span(t))
                return TM._section(-b, -a, TM.TRAM_RAIL_Z0, TM.TRAM_RAIL_Z1) if side < 0 else TM._section(a, b, TM.TRAM_RAIL_Z0, TM.TRAM_RAIL_Z1)
            return var_sweep(path, section)
        return shape

    def groove_shape(path, k):
        def side_section(sg):
            def section(t):
                a, _ = head_span(t)
                w = groove_w * widen(t, gf)
                return [(sg * u, z) for u, z in TM._section((a - w) * k, a * k, TM.TRAM_GROOVE_Z, TM.TRAM_GROOVE_Z + TM.TRAM_TH)][::sg]
            return section
        return R.merge([var_sweep(path, side_section(sg)) for sg in (1, -1)])

    gz = TM.TRAM_GROOVE_Z
    parts = [
        replace(base["tram_edge"], material=m_edge),
        replace(base["tram_bed"], material=m_bed,
                shape=TM._to_edge(TM._slab_shape(edge_u0, TM.TRAM_BED_Z0, TM.TRAM_BED_Z1), bed_u - edge_u0)),
    ]
    if cfg.get("gore"):
        # T字・十字の、曲線と 2 本の直線のあいだ（三角の所）を床で埋める。本番では床が届かず、透明な穴（2〜5px）が残る
        # （sheet_audit の holes。T字・分岐の絵の 24 セル）。部品の形は経路 1 本しか受けないので、組み立て（sheetlib.sheetlib の
        # assemble）を包んでセルの経路を覚え、最初の経路のときだけ、曲線ごとに「曲線の点列 + タイルの中心」の多角形を作る。
        # 中心を通る直線があり、曲線の片端がその直線に来ているときだけ埋める（ふつうの曲線のセルは変えない）。T字は直線 + 枝の向きへの
        # 曲線 2 本で、2 つの多角形を合わせると、直線と 2 本の曲線に囲まれた所になる。
        # 高さは縁の帯より上・床より下（床と同じ材質。縁の帯は覆うが、汚れ・溝・レールは上に出る）。この系統の描画のプロセスにしか効かない
        S = sys.modules["sheetlib.sheetlib"]
        cell = {"paths": []}
        if not getattr(S.assemble, "_tram_gore", False):
            orig = S.assemble

            def wrapped(parts_, paths_, *a, **kw):
                cell["paths"] = list(paths_)
                return orig(parts_, paths_, *a, **kw)
            wrapped._tram_gore = True
            S.assemble = wrapped
        z0, z1 = TM.TRAM_BED_Z0, TM.TRAM_BED_Z1 - 0.0005

        def is_curve(p):
            return len(p) > 2

        def near_line(q, p):
            a, b = p[0], p[-1]
            d = b - a
            t = max(0.0, min(1.0, (q - a).dot(d) / d.length_squared))
            return (a + d * t - q).length < 0.3

        def gore(path, k):
            paths = cell["paths"]
            if not paths or path is not paths[0]:
                return None
            straights = [p for p in paths if not is_curve(p)]
            verts, faces = [], []
            for c in (p for p in paths if is_curve(p)):
                pts = [Vector((q.x, q.y)) for q in c if max(abs(q.x), abs(q.y)) <= 5.0 + 1e-6]
                if len(pts) < 2:
                    continue
                ends = (Vector((c[0].x, c[0].y)), Vector((c[-1].x, c[-1].y)))
                if not any(any(near_line(e, s) for s in straights) for e in ends):
                    continue
                if not any(near_line(Vector((0, 0)), s) for s in straights):
                    continue
                # 曲線がタイルの辺に出る所（辺の中点）を両端に足す（隣の曲線の多角形と、中心から辺の中点への線でぴったり接する）
                mids = [Vector(m) for m in ((0, 5), (0, -5), (5, 0), (-5, 0))]
                m0, m1 = (min(mids, key=lambda m: (m - e).length) for e in ends)
                poly = [Vector((0.0, 0.0)), m0] + pts + [m1]
                o = len(verts)
                m = len(poly)
                verts += [Vector((v.x, v.y, z0)) for v in poly] + [Vector((v.x, v.y, z1)) for v in poly]
                faces += [(o, o + i + 1, o + i) for i in range(1, m - 1)]
                faces += [(o + m, o + m + i, o + m + i + 1) for i in range(1, m - 1)]
                faces += [(o + i, o + (i + 1) % m, o + m + (i + 1) % m, o + m + i) for i in range(m)]
                # 隣の曲線の多角形と接する線（中心から辺の中点）に細い帯を重ねる。接する線の上の画素が、どちらの多角形にも
                # 半分ずつしか掛からず、透明のまま残った（南向きの T字の 1px）
                for mid in (m0, m1):
                    d = mid.normalized()
                    nrm = Vector((-d.y, d.x)) * 0.15
                    quad = [-nrm, nrm, mid + nrm, mid - nrm]
                    o = len(verts)
                    verts += [Vector((v.x, v.y, z0)) for v in quad] + [Vector((v.x, v.y, z1)) for v in quad]
                    faces += [(o, o + 1, o + 2, o + 3), (o + 7, o + 6, o + 5, o + 4)]
                    faces += [(o + i, o + (i + 1) % 4, o + 4 + (i + 1) % 4, o + 4 + i) for i in range(4)]
            return (verts, faces) if faces else None
        gmat = ("tram_gore_dbg", (1.0, 0.0, 0.0), 0.9) if cfg.get("gore_debug") else m_bed
        parts.append(R.Part("tram_gore", "tram_bed", "bed", gmat, gore, centre=False))
    if groove_w > 0:
        parts.append(replace(base["tram_groove"], material=m_groove, shape=groove_shape))
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
