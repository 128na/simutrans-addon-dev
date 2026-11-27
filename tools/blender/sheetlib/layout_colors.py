"""レイアウト検証用モードの色（SHEET_LAYOUT=1。ADR 0005）。部品の名前 → 単色（0〜1 の RGB）。

画像で見分けやすいよう、隣り合う部品が近い色にならない原色寄りの色を割り当てる。
部品を足したら、ここにも色を足す（無いと警告を出し、名前から決めた色で描く）。
"""
import colorsys
import zlib

LAYOUT_COLORS = {
    # 線路
    "ballast": (0.85, 0.75, 0.10), "sleeper": (0.95, 0.95, 0.95), "railL": (0.00, 0.70, 0.90), "railR": (0.90, 0.00, 0.70),
    "stop_postL": (0.50, 0.00, 0.50), "stop_postR": (0.65, 0.25, 0.65), "stop_beam": (0.90, 0.40, 0.00), "stop_mark": (1.00, 1.00, 0.60),
    "buffer_beam": (1.00, 0.20, 0.20), "buffer_leg": (0.20, 0.20, 1.00), "buffer_head": (0.10, 0.60, 0.10),
    "buffer_plate": (1.00, 0.55, 0.85), "buffer_post": (0.40, 0.20, 0.00), "buffer_lamp": (0.00, 0.00, 0.00),
    "buffer_light": (1.00, 1.00, 0.00),
    "ballast_fill": (0.60, 0.50, 0.00), "rail_head": (0.40, 0.90, 1.00),
    "rust0": (0.90, 0.50, 0.20), "rust1": (0.90, 0.30, 0.00), "oil": (0.50, 0.00, 0.60), "sleeper_rust": (0.00, 0.90, 0.90),
    # スラブ軌道（slab_parts）
    "slab_bed": (0.55, 0.30, 0.05), "slab_fill": (0.15, 0.00, 0.30), "slab": (0.75, 1.00, 0.45), "slab_notch": (0.00, 0.35, 0.20),
    "slab_stud": (1.00, 0.00, 0.00), "slab_fastener": (0.00, 0.00, 0.60),
    # 路面軌道（tram_parts）
    "tram_bed": (0.55, 0.55, 0.85), "tram_edge": (1.00, 0.85, 0.00), "tram_groove": (0.10, 0.10, 0.10), "tram_gore": (0.45, 0.10, 0.10),
    # 壁・基盤・橋脚（線路・道路で共通）
    "wallL": (0.90, 0.05, 0.05), "wallR": (0.60, 0.00, 0.00), "wall": (0.90, 0.05, 0.05), "endw": (1.00, 0.35, 0.35), "endw_edge": (1.00, 0.35, 0.35),
    # 道路の中央分離帯（road_parts。AMI #118）: 縁石の帯とガードレール
    "median_curbL": (1.00, 0.60, 0.00), "median_curbR": (0.70, 0.40, 0.00), "median_railL": (0.00, 0.90, 0.90), "median_railR": (0.00, 0.55, 0.55),
    "base": (0.05, 0.25, 0.90), "base_open": (0.05, 0.75, 0.25), "girder": (0.20, 0.45, 0.95),
    "embankment": (0.40, 0.80, 0.20), "pier": (0.35, 0.35, 1.00), "rampbody": (0.00, 0.50, 0.30), "elev_body": (0.00, 0.45, 0.45),
    # 門型の橋脚（pier_gate_sheet）: 柱は角、梁は辺（斜めは外側の角）ごとに色を分ける
    "pier_post_c": (0.35, 0.35, 1.00), "pier_post_ne": (0.10, 0.10, 0.80), "pier_post_nw": (0.60, 0.60, 1.00),
    "pier_post_se": (0.80, 0.00, 0.80), "pier_post_sw": (0.00, 0.80, 0.80),
    "pier_beam_n": (1.00, 0.45, 0.10), "pier_beam_s": (1.00, 0.85, 0.00), "pier_beam_e": (0.85, 0.10, 0.10), "pier_beam_w": (0.55, 0.30, 0.05),
    "pier_beam_ne": (1.00, 0.45, 0.10), "pier_beam_nw": (1.00, 0.85, 0.00), "pier_beam_se": (0.85, 0.10, 0.10), "pier_beam_sw": (0.55, 0.30, 0.05),
    # 架線（catenary_parts）
    "cat_poleL": (0.00, 0.85, 0.85), "cat_poleR": (0.00, 0.55, 0.55), "cat_beam": (1.00, 0.60, 0.00),
    "cat_hanger": (0.60, 1.00, 0.20), "cat_wire": (0.95, 0.00, 0.95),
    "cat_messenger": (0.55, 0.00, 0.95),
    "cat_dropper": (0.95, 0.40, 0.70),
    "cat_pole_tram": (0.00, 0.85, 0.85), "cat_arm_tram": (1.00, 0.60, 0.00),
    # 道路
    "asphalt": (0.25, 0.25, 0.30), "curb": (0.90, 0.90, 0.20), "road_curb": (0.90, 0.90, 0.20), "paving": (0.20, 0.80, 0.30),
    "line": (1.00, 1.00, 1.00),
    "wear0": (0.60, 0.40, 0.20), "wear1": (0.70, 0.50, 0.30), "wear2": (0.80, 0.60, 0.40),
    "slush0": (0.70, 0.90, 1.00), "slush1": (0.50, 0.80, 1.00), "slush2": (0.30, 0.70, 1.00), "snowbank": (0.90, 1.00, 1.00),
    # 踏切（crossing）
    "crossing_panel": (0.30, 0.00, 0.30), "crossing_flange": (0.00, 0.00, 0.00), "crossing_yellow": (1.00, 0.90, 0.00),
    "crossing_black": (0.10, 0.10, 0.10), "crossing_box": (0.00, 0.60, 0.60), "crossing_plate": (0.80, 0.30, 0.00),
    "crossing_lamp": (1.00, 0.00, 0.00),
    # トンネル・そのほか
    "tunnel_dark": (0.05, 0.05, 0.05), "tunnel_plate": (1.00, 0.60, 0.00), "tile": (0.50, 0.50, 0.50), "snow": (0.80, 0.95, 1.00),
}

_warned = set()


def layout_rgb(name):
    if name in LAYOUT_COLORS:
        return LAYOUT_COLORS[name]
    if name not in _warned:
        _warned.add(name)
        print(f"[layout] 色が未登録の部品: {name}（layout_colors.py に足す）")
    h = (zlib.crc32(name.encode("utf8")) % 360) / 360
    return colorsys.hsv_to_rgb(h, 0.9, 0.9)
