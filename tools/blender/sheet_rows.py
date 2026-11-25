"""シートの行の並び（雪の絵・手前の絵の行のずらし）と、セルの位置合わせ（offset）の唯一の定義（Blender を使わない）。

シートを描く側（sheetlib）と、dat を書く側（アドオンの dat を書くスクリプト。AMI の ami_dat.py）が、同じ値を別々に持って
注記でそろえていた（#302。片方だけ直すと、dat が別の行の絵を指す。指す先に別の絵があると検査で拾えない）。
値はここに 1 か所だけ置き、両方がここから引く。sheetlib が読むときも、ami_dat.py が読むときも、Blender を読み込まない。

置くのは「種類ごとの描き方の値」（シートの並びの決まり。全アドオン共通）だけ。どの物がどの並びを使うか
（手前の絵を持つ way・近い斜めの絵を持たない way など）は、アドオンごとの性質なので、アドオンの側（AMI は catalog.py）に置く。
pak の大きさに比例する値（offset）は sheet_settings.SCALE を掛ける。
"""
import sheet_settings

# ---------------------------------------------------------------- way（線路・道路・運河・歩道・モノレールのシート）
# 行の並び: 奥の絵 4 行 →（手前の絵 4 行）→ 雪の奥の絵 4 行 →（雪の手前の絵 4 行）
WAY_SNOW_ROWS = 4          # 手前の絵を持たない way の、夏の絵から雪の絵までの行のずらし（奥の絵 4 行の下）
WAY_FRONT_ROW = 4          # 手前の絵（frontimage）を持つ way の、奥の絵から手前の絵までの行のずらし
WAY_FRONT_SNOW_ROWS = 8    # 手前の絵を持つ way の、夏の絵から雪の絵までの行のずらし（奥と手前の 8 行の下）
CANAL_SNOW_ROWS = 4        # 運河の雪の行（笠石に雪）
SIDEWALK_SNOW_ROWS = 4     # 歩道の雪の行


def way_snow_rows(has_front):
    """way のシートの、夏の絵から雪の絵までの行のずらし（手前の絵を持つかで違う）"""
    return WAY_FRONT_SNOW_ROWS if has_front else WAY_SNOW_ROWS


# ---------------------------------------------------------------- way-object（壁・橋脚・柵）
WALL_FRONT_ROW = 4         # 壁のシートの、奥の絵から手前の絵までの行のずらし（電化の way-object も同じ並び）
FENCE_FRONT_ROW = 4        # 歩道の柵のシートの手前の絵の行（壁と同じ並び）
PIER_GATE_FRONT_ROW = 4    # 門型の橋脚の手前の絵の行
EMBANKMENT_SNOW_ROWS = 4   # 盛土の雪の行
BRIDGE_SNOW_ROWS = 4       # 橋の雪の行（橋脚は夏と同じセル）

# ---------------------------------------------------------------- 踏切・車庫・操車場
CROSSING_SNOW_ROW = 2      # 踏切の雪の行（夏の奥・手前が行 0・1）
DEPOT_SNOW_ROW = 2         # 車庫の雪の行（夏の奥・手前が行 0・1）
YARD_SNOW_ROW = 1          # 操車場の雪の行（夏の奥の絵が行 0）
# 車庫・操車場の dat の offset（画素。セルの左上から建物の基準点まで）。pak128 は -64,-96。大きな pak は倍。
# GROUND_CY + BUILDING_DROP - 96 = 95 が、線路の絵（GROUND_CY - 32）と同じ行になる（128 のとき）
BUILDING_OFFSET = (-64 * sheet_settings.SCALE, -96 * sheet_settings.SCALE)

# ---------------------------------------------------------------- 路面表示
MARKING_ROWS = 4           # 路面表示のシートの、夏の絵の行数（雪の絵は MARKING_ROWS 行下）
MARKING_COLS = 10
MARKING_EMPTY_CELL = (0, 4)  # 絵の無い形が指す空のセル
# 雪の絵（夏と別のセル）を持つ種類
MARKING_SNOW_KINDS = ("lane6_m", "junction4_in", "junction4_out", "junction6_in", "junction6_out", "junction6_m")
