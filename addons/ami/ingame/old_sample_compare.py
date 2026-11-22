# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""旧描画位置（#26）と新の見本を、同じ区画で左右に並べた確認画像にする。

使い方（アドオンのディレクトリで）:
    uv run ingame/old_sample_compare.py <新の画面のフォルダ> <旧の画面のフォルダ> <出力の png> [区画名 ...]

画面は ingame/sample_parallel.sh の出力（`temperate_<区画>.png`）。TRACK=ami_rail_ballast（新）と TRACK=ami_rail_ballast_old（旧）の
同じ SPOTS を撮ったものを渡す。左が新、右が旧。区画名を渡さなければ、両方にある画面を全部並べる。
"""
import os
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = pathlib.Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "YuGothM.ttc"


def main():
    new_dir, old_dir, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
    names = sys.argv[4:] or sorted(p.stem.removeprefix("temperate_") for p in new_dir.glob("temperate_*.png") if (old_dir / p.name).exists())
    font = ImageFont.truetype(str(FONT), 18)
    ims = [(n, Image.open(new_dir / f"temperate_{n}.png").convert("RGB"), Image.open(old_dir / f"temperate_{n}.png").convert("RGB")) for n in names]
    w, h = ims[0][1].size
    sheet = Image.new("RGB", (2 * w + 10, len(ims) * (h + 30)), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    for i, (n, a, b) in enumerate(ims):
        y = i * (h + 30)
        d.text((8, y + 4), f"区画 {n}（左: 新描画位置、右: 旧描画位置）", font=font, fill=(0, 0, 0))
        sheet.paste(a, (0, y + 30))
        sheet.paste(b, (w + 10, y + 30))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"[compare] {out}（{len(ims)} 区画）")


if __name__ == "__main__":
    main()
