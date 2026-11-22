# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""旧描画位置の線路（#26）と SIS の線路の継ぎ目を、新と並べた確認画像にする（ingame/old_seam.sh が撮った画面から）。

使い方（アドオンのディレクトリで）:
    uv run ingame/old_seam_compose.py [撮った画面のフォルダ（既定 work/old_seam）] [出力のフォルダ（既定 docs/old_seam）]

画面は `<新|旧>_<種類>_<ew|ns|dg|sl>.png`（等倍。ingame/old_seam.nut の区画を撮ったもの）。種類ごとに 1 枚の画像を書く:
上の段が新描画位置（今の ami_rail_*）、下の段が旧描画位置（ami_rail_*_old）で、どちらも両端が SIS の線路、真ん中が AMI（SIS_ST_TGbl_E01-999B）。
継ぎ目の周りを、最近傍で 4 倍に切り出して並べる（東西の直線 2 か所・南北の直線 2 か所・斜め 2 か所・坂 1 か所）。
切り出す位置は、等倍の画面（704×560）の継ぎ目の座標。画面の大きさが違うと合わない。
"""
import os
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

KINDS = {"ballast": "在来線", "concrete": "弾性まくらぎ直結軌道", "ladder": "フローティング・ラダー軌道", "slab": "高速線（スラブ軌道）"}
# (画面の名前, 切り出す枠 x0,y0,x1,y1, 見出し)。継ぎ目は SIS → AMI → SIS の順で、見本の座標は ingame/old_seam.nut
JOINTS = [
    ("ew", (100, 270, 220, 340), "東西の直線（西の継ぎ目）"),
    ("ew", (360, 400, 480, 470), "東西の直線（東の継ぎ目）"),
    ("ns", (195, 405, 275, 455), "南北の直線（南の継ぎ目）"),
    ("ns", (430, 285, 510, 335), "南北の直線（北の継ぎ目）"),
    ("dg", (300, 250, 410, 330), "斜め（北の継ぎ目）"),
    ("dg", (300, 345, 410, 425), "斜め（南の継ぎ目）"),
    ("sl", (280, 300, 440, 420), "坂（南が低い 1 段の坂）"),
]
ZOOM = 4
GAP = 12
LABEL_H = 26
FONT = pathlib.Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "YuGothM.ttc"


def main():
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "work/old_seam")
    out = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "docs/old_seam")
    out.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(FONT), 16)
    for kind, title in KINDS.items():
        cells = []
        for shot, box, label in JOINTS:
            pair = []
            for prefix in ("新", "旧"):
                name = f"{'new' if prefix == '新' else 'old'}_{kind}_{shot}.png"
                im = Image.open(src / name).convert("RGB").crop(box)
                pair.append(im.resize((im.width * ZOOM, im.height * ZOOM), Image.NEAREST))
            cells.append((label, pair))
        # 1 行に 4 つ並べる（7 つ → 2 行）。行の高さは、その行の切り出しのうち大きい方
        cols = 4
        groups = [cells[i:i + cols] for i in range(0, len(cells), cols)]
        cw = max(p[0].width for _, p in cells)
        heights = [max(p[0].height for _, p in g) for g in groups]
        total = LABEL_H + sum(LABEL_H + 2 * h + GAP * 2 for h in heights) + GAP
        sheet = Image.new("RGB", (cols * (cw + GAP) + GAP, total), (250, 250, 250))
        d = ImageDraw.Draw(sheet)
        d.text((GAP, 4), f"{title}。各区画の上段が新描画位置（今の ami_rail_*）、下段が旧描画位置（ami_rail_*_old）。両端の幅の広い帯が SIS の線路、真ん中の細い帯が AMI", font=font, fill=(0, 0, 0))
        y = LABEL_H + GAP
        for g, h in zip(groups, heights):
            for i, (label, pair) in enumerate(g):
                x = GAP + i * (cw + GAP)
                d.text((x, y), label, font=font, fill=(0, 0, 0))
                for j, im in enumerate(pair):
                    yy = y + LABEL_H + j * (h + GAP // 2)
                    sheet.paste(im, (x, yy))
                    d.text((x + 4, yy + 2), "新" if j == 0 else "旧", font=font, fill=(255, 255, 0))
            y += LABEL_H + 2 * h + GAP * 2
        path = out / f"{kind}.png"
        sheet.save(path)
        print(f"[compose] {path}")


if __name__ == "__main__":
    main()
