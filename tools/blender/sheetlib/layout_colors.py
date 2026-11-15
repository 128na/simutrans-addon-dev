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
    "rust0": (0.90, 0.50, 0.20), "rust1": (0.90, 0.30, 0.00), "oil": (0.50, 0.00, 0.60), "sleeper_rust": (0.00, 0.90, 0.90),
    # 壁・基盤・橋脚（線路・道路で共通）
    "wallL": (0.90, 0.05, 0.05), "wallR": (0.60, 0.00, 0.00), "wall": (0.90, 0.05, 0.05), "endw": (1.00, 0.35, 0.35),
    "base": (0.05, 0.25, 0.90), "base_open": (0.05, 0.75, 0.25), "girder": (0.20, 0.45, 0.95),
    "pier": (0.35, 0.35, 1.00), "rampbody": (0.00, 0.50, 0.30),
    # 道路
    "asphalt": (0.25, 0.25, 0.30), "curb": (0.90, 0.90, 0.20), "road_curb": (0.90, 0.90, 0.20), "paving": (0.20, 0.80, 0.30),
    "line": (1.00, 1.00, 1.00),
    "wear0": (0.60, 0.40, 0.20), "wear1": (0.70, 0.50, 0.30), "wear2": (0.80, 0.60, 0.40),
    "slush0": (0.70, 0.90, 1.00), "slush1": (0.50, 0.80, 1.00), "slush2": (0.30, 0.70, 1.00), "snowbank": (0.90, 1.00, 1.00),
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
