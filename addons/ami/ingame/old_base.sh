#!/bin/bash
# 旧描画位置の基盤・壁・架線つきの壁（#26）を、新と並べて撮る。見本は ingame/old_base.nut。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami_rail.pak・dist/ami_rail_old.pak・dist/ami_extra.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=<ポート> bash ingame/old_base.sh
# ゲームは work/game/<PORT>/ の写し（ingame/game.sh）で起動する。画面は OUT（既定 work/old_base）に o2・o3（旧の複線 + 壁・架線つきの壁）と
# n2・n3（新の同じ並び）を撮り、docs/old_base.png に 4 枚を並べる（左が旧、右が新。上が壁、下が架線つきの壁）
PORT=${PORT:?PORT に MCP のポートを指定する}
OUT=${OUT:-work/old_base}
G="bash $(dirname "$0")/game.sh"
mkdir -p "$OUT"
trap 'PORT=$PORT $G STOP > /dev/null 2>&1' EXIT
# 出力をパイプに流すと、ゲームを閉じるまで返らない（way-addon.md の 8.2）ので、ファイルに書く
PAK=dist/ami_rail_old.pak EXTRA_PAKS="dist/ami_rail.pak dist/ami_extra.pak" NUT=ingame/old_base.nut $G > "$OUT/start.txt" 2>&1
grep -o '[a-z]* [a-z]* y=[0-9]*=\[[^]]*\]\|[a-z]* [0-9]* missing' "$OUT/start.txt" | sed 's/^/[old_base] 失敗: /'
PORT=$PORT OUT=$OUT SPOTS="o2:26:30 o3:26:40 n2:26:50 n3:26:60" ZOOM=3 $G CAPTURE > "$OUT/capture.txt" 2>&1
python -X utf8 - "$OUT" <<'PY'
import sys
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]
font = ImageFont.truetype("C:/Windows/Fonts/YuGothM.ttc", 18)
names = (("o2", "旧: 複線の基盤 back・front + 壁"), ("n2", "新: 同じ並び"), ("o3", "旧: 架線つきの壁"), ("n3", "新: 同じ並び"))
ims = [Image.open(f"{out}/{n}.png").convert("RGB") for n, _ in names]
w, h = ims[0].size
sheet = Image.new("RGB", (2 * w, 2 * h))
d = ImageDraw.Draw(sheet)
for i, (im, (_, label)) in enumerate(zip(ims, names)):
    x, y = (i % 2) * w, (i // 2) * h
    sheet.paste(im, (x, y))
    d.rectangle((x + 4, y + 48, x + 330, y + 74), fill=(0, 0, 0))
    d.text((x + 8, y + 50), label, font=font, fill=(255, 255, 0))
sheet.save("docs/old_base.png")
print("[old_base] docs/old_base.png")
PY
