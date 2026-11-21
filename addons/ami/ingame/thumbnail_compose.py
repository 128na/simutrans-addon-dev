# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""リリース用のサムネイル（#96）を作る。ingame/thumbnail_capture.sh で撮った画面から、道具欄と状態欄を切り落とし（拡大・縮小はしない）、文字を重ねる。

使い方（アドオンのディレクトリで）:
    uv run ingame/thumbnail_compose.py [撮った画面] [--plain]

- 撮った画面の既定は work/thumbnail/shot.png（thumbnail_capture.sh の既定の出力。SCREEN=2560x1400 で撮る）。
- 出力は docs/thumbnail/ の thumbnail.png（文字入り、2560x1340）と ogp.jpg（同じ大きさの JPEG。手本の iss と同じく、縮めるのはファイルの大きさだけで、画素は縮めない）。
  --plain を付けると、文字なしの plain.png だけを書く（構図の確かめ用）。
- 比率は OGP の 1.91:1（2560x1340）。撮った画面の地図の部分（道具欄の下から状態欄の上まで）の真ん中から切り出す。
- 文字は手本（iss の docs/thumbnail.png）の作りに合わせる: 上に白の太い斜体の英語の題名と影、左下に「内容」の箇条書きと種類の数。
  フォントは Windows の Segoe UI（題名）と游ゴシック（日本語）。無い環境では FONT_* で場所を替える。
"""

import argparse
import os
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent.parent  # アドオンのディレクトリ
OUT_DIR = HERE / "docs" / "thumbnail"
SIZE = (2560, 1340)  # 1.91:1
TOOLBAR = 32  # 画面の上の道具欄の高さ（px）
STATUSBAR = 16  # 画面の下の状態欄の高さ（px）

FONTS = pathlib.Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
FONT_TITLE = os.environ.get("FONT_TITLE", str(FONTS / "segoeuiz.ttf"))  # Segoe UI Bold Italic
FONT_BODY = os.environ.get("FONT_BODY", str(FONTS / "YuGothB.ttc"))  # 游ゴシック Bold

TITLE = "AI Marunage Infrastructure"
BADGE = os.environ.get("BADGE", "")  # 題名の後ろに足す字（例: "β"。ベータ版の字を入れる案）
BODY = [
    "内容",
    "　線路 4 種（バラスト・直結・ラダー・スラブ）",
    "　道路 3 種、路面軌道、歩道",
    "　高架・橋・トンネル・壁・架線",
]
COUNT = "約 {n} 種類"


def count_objects() -> int:
    """ゲームに入る物（way・way-object・橋・トンネル）の数。src/ の dat の obj= の行を数える。
    ex_donors.dat は分岐の追加画像の提供用で、ゲームには入らないので数えない（build.py）。"""
    n = 0
    for p in (HERE / "src").glob("*.dat"):
        if p.stem == "ex_donors":
            continue
        n += sum(1 for line in p.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip().startswith("obj="))
    return n


def crop(shot: Image.Image) -> Image.Image:
    """道具欄と状態欄を除いた地図の部分の、真ん中から SIZE を切り出す（拡大・縮小しない）。"""
    w, h = shot.size
    top, bottom = TOOLBAR, h - STATUSBAR
    if w < SIZE[0] or bottom - top < SIZE[1]:
        raise SystemExit(f"撮った画面が小さい: {w}x{h}（地図の部分が {SIZE[0]}x{SIZE[1]} 以上要る。SCREEN=2560x1400 で撮る）")
    x0 = (w - SIZE[0]) // 2
    y0 = top + (bottom - top - SIZE[1]) // 2
    return shot.crop((x0, y0, x0 + SIZE[0], y0 + SIZE[1])).convert("RGB")


def text_with_shadow(img: Image.Image, xy, text, font, offset=6, blur=6, alpha=200) -> None:
    """白い字に、ぼかした黒い影を付けて描く。"""
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((xy[0] + offset, xy[1] + offset), text, font=font, fill=(0, 0, 0, alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(shadow)
    ImageDraw.Draw(img).text(xy, text, font=font, fill=(255, 255, 255, 255))


def compose(base: Image.Image) -> Image.Image:
    img = base.convert("RGBA")
    title = TITLE + (" " + BADGE if BADGE else "")
    font_title = ImageFont.truetype(FONT_TITLE, 150)
    text_with_shadow(img, (60, 10), title, font_title, offset=8, blur=8)
    font_body = ImageFont.truetype(FONT_BODY, 64)
    lines = BODY + [COUNT.format(n=round(count_objects(), -1))]
    line_h = 84
    y = SIZE[1] - 40 - line_h * len(lines)
    for line in lines:
        text_with_shadow(img, (60, y), line, font_body, offset=4, blur=4, alpha=230)
        y += line_h
    return img.convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("shot", nargs="?", default=str(HERE / "work" / "thumbnail" / "shot.png"))
    ap.add_argument("--plain", action="store_true", help="文字なしの plain.png だけを書く")
    args = ap.parse_args()
    base = crop(Image.open(args.shot))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.plain:
        base.save(OUT_DIR / "plain.png", optimize=True)
        print(f"[compose] {OUT_DIR / 'plain.png'} {base.size}")
        return
    img = compose(base)
    img.save(OUT_DIR / "thumbnail.png", optimize=True)
    img.save(OUT_DIR / "ogp.jpg", quality=85, optimize=True)
    print(f"[compose] {OUT_DIR / 'thumbnail.png'} {img.size}、{OUT_DIR / 'ogp.jpg'}")


if __name__ == "__main__":
    main()
