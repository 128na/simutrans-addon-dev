"""桁・床の板の上に載せる線路（まくらぎとレール）の部品（#353）。

転車台・遷車台（turntable.py）と水路の踏切（canal_crossing.py）が、同じ寸法と並びを別々に写していた（#349 の記録の案 5）。
寸法と直方体の並べ方はここに 1 つだけ置き、両方がここから引く。材質と物の名前・物のまとめ方（材質ごとに 1 つか、
直方体ごとに 1 つか）は、使う側に置く。

座標は経路の座標（u: 経路を横切る向き、s: 経路に沿う向き、z: 高さ）。使う側がタイルの座標に直す。
"""
SLEEPER = (2.4, 0.22, 0.14)  # まくらぎ（長さ・幅・高さ）
SLEEPER_STEP = 0.65          # まくらぎの間隔
DECK_UNDER = 0.12            # レールの腹の高さ（まくらぎの上面からレールの頭の下端まで）。deck_top はレールの頭の下端から、これとまくらぎの高さだけ下


def deck_top(rail):
    """まくらぎの下面（桁・床の板の上面）の高さ。rail は線路の way のレール (内側, 外側, 上面)"""
    return rail[2] - 0.02 - SLEEPER[2] - DECK_UNDER


def deck_track(s0, s1, top, rail):
    """s0〜s1 の範囲に置く、まくらぎとレールの直方体（中心 u, s, z と寸法 u, s, z）。top はまくらぎの下面の高さ。
    戻り値: (まくらぎの list, レールの list)。レールの list は、左右（u の負・正）の順に (腹, 頭) の組"""
    sleepers = []
    n = max(1, round(abs(s1 - s0) / SLEEPER_STEP))
    for i in range(n):
        s = s0 + (s1 - s0) * (i + 0.5) / n
        sleepers.append((0, s, top + SLEEPER[2] / 2, SLEEPER[0], SLEEPER[1], SLEEPER[2]))
    r_in, r_out, r_top = rail
    z_web0, z_head0 = top + SLEEPER[2], r_top - 0.02
    mid, ln = (s0 + s1) / 2, abs(s1 - s0)
    rails = []
    for sgn in (-1, 1):
        u, w = sgn * (r_in + r_out) / 2, r_out - r_in
        rails.append(tuple((u, mid, (z0 + z1) / 2, w, ln, z1 - z0) for z0, z1 in ((z_web0, z_head0), (z_head0, r_top))))
    return sleepers, rails
