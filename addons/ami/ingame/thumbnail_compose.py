# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow"]
# ///
"""リリース用のサムネイル（#96）を作る。ingame/thumbnail_capture.sh で撮った画面から、道具欄と状態欄を切り落とし（拡大・縮小はしない）、文字を重ねる。

使い方（アドオンのディレクトリで）:
    uv run ingame/thumbnail_compose.py [撮った画面] [--plain]
    uv run ingame/thumbnail_compose.py --manual <文字入りの画像> [--manual-plain <文字なしの画面>]

--manual（いまの公開物。2026-11-21、ユーザーが手動で撮影し、文字入れまで済ませた画像を使う）:
- 文字入りの画像は、ゲームの画面（道具欄と状態欄が入った画面全体）を、別の道具で縦横同じ倍率で拡大して文字を重ねたもの。
  左右に透明な帯があってもよい（切り落とす）。倍率は、透明な帯を除いた幅 / GAME_WIDTH（撮った画面の幅、既定 2560）で求める。
- 道具欄（TOOLBAR）と状態欄（STATUSBAR）をその倍率で換算して上下を切り落とし（拡大した画像では境の混ざった行も落とす）、
  残りの高さいっぱいで 1.91:1 になる幅を、左端（題名と下の一文がある側）から切り出す。拡大・縮小はしない。
- 出力は docs/thumbnail/thumbnail.png（切り出したそのままの大きさ）と ogp.jpg（1200x628）。
  --manual-plain を渡すと、文字なしの画面（倍率 1）を同じ割合で切り出して plain.png に書く。

- 撮った画面の既定は work/thumbnail/shot.png（thumbnail_capture.sh の既定の出力。SCREEN=2560x1400 で撮る）。
- 出力は docs/thumbnail/ の thumbnail.png（文字入り、2560x1340）と ogp.jpg（Web 用に 1200x628 へ縮めた JPEG。2026-11-21、ユーザーの決定）。
  --plain を付けると、文字なしの plain.png だけを書く（構図の確かめ用）。
- 比率は OGP の 1.91:1（2560x1340）。撮った画面の地図の部分（道具欄の下から状態欄の上まで）の真ん中から切り出す。
- 文字は手本（iss の docs/thumbnail.png）の作りに合わせる: 上に白の太い斜体の英語の題名と影、左下に「内容」の箇条書きと種類の数。
  フォントは Windows の Segoe UI（題名）と游ゴシック（日本語）。無い環境では FONT_* で場所を替える。
"""

import argparse
import math
import os
import pathlib

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent.parent  # アドオンのディレクトリ
OUT_DIR = HERE / "docs" / "thumbnail"
SIZE = (2560, 1340)  # 1.91:1
OGP_SIZE = (1200, 628)  # OGP の推奨の大きさ（1.91:1）
TOOLBAR = 32  # 画面の上の道具欄の高さ（px）
STATUSBAR = 16  # 画面の下の状態欄の高さ（px）

FONTS = pathlib.Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
FONT_TITLE = os.environ.get("FONT_TITLE", str(FONTS / "segoeuiz.ttf"))  # Segoe UI Bold Italic
FONT_BODY = os.environ.get("FONT_BODY", str(FONTS / "YuGothB.ttc"))  # 游ゴシック Bold

TITLE = "AI Marunage Infrastructure"
BODY = [
    "内容",
    "　線路 4 種（バラスト・直結・ラダー・スラブ）",
    "　道路 3 種、路面軌道、歩道",
    "　高架・橋・トンネル・壁・架線",
]
COUNT = "約 {n} 種類"


def count_objects() -> int:
    """ゲームに入る物（way・way-object・橋・トンネル）の数。src/ の ami_*.dat（build.py が pak にするもの）の obj= の行を数える。
    ex_donors.dat は分岐の追加画像の提供用で、ゲームには入らないので数えない（build.py）。"""
    n = 0
    for p in (HERE / "src").glob("ami_*.dat"):  # build.py が pak にする dat と同じ選び方
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


GAME_WIDTH = int(os.environ.get("GAME_WIDTH", "2560"))  # --manual: 元の画面の幅（倍率を求める）


def crop_manual(img: Image.Image, game_width: int = GAME_WIDTH) -> Image.Image:
    """手動の画像から、左右の透明な帯と上下の道具欄・状態欄を切り落とし、1.91:1 を左端から切り出す（拡大・縮小しない）。"""
    rgba = img.convert("RGBA")
    box = rgba.getchannel("A").getbbox()  # 透明でない部分（左右の帯を除く）
    if box is None:
        raise SystemExit("画像が全部透明")
    x0, _, x1, _ = box
    scale = (x1 - x0) / game_width
    edge = 0 if scale == 1 else 1  # 拡大した画像では、欄の境の行が混ざった色になるので 1 行余分に落とす
    top = math.ceil(TOOLBAR * scale) + edge
    bottom = rgba.height - math.ceil(STATUSBAR * scale) - edge
    h = bottom - top
    w = round(h * SIZE[0] / SIZE[1])
    if w > x1 - x0:  # 幅が足りないときは高さを詰める（上下の真ん中を残す）
        w = x1 - x0
        nh = round(w * SIZE[1] / SIZE[0])
        top += (h - nh) // 2
        h = nh
    print(f"[compose] 倍率 {scale:.4f}、切り出し ({x0},{top})-({x0 + w},{top + h}) {w}x{h}")
    return rgba.crop((x0, top, x0 + w, top + h)).convert("RGB")


def text_with_shadow(img: Image.Image, xy, text, font, offset=6, blur=6, alpha=200) -> None:
    """白い字に、ぼかした黒い影を付けて描く。"""
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((xy[0] + offset, xy[1] + offset), text, font=font, fill=(0, 0, 0, alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(shadow)
    ImageDraw.Draw(img).text(xy, text, font=font, fill=(255, 255, 255, 255))


def compose(base: Image.Image) -> Image.Image:
    img = base.convert("RGBA")
    font_title = ImageFont.truetype(FONT_TITLE, 150)
    text_with_shadow(img, (60, 10), TITLE, font_title, offset=8, blur=8)
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
    ap.add_argument("--manual", help="手動で文字まで入れた画像。切り出して thumbnail.png と ogp.jpg に書く（文字は重ねない）")
    ap.add_argument("--manual-plain", help="--manual と一緒に: 文字なしの画面を同じく切り出して plain.png に書く")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.manual:
        img = crop_manual(Image.open(args.manual))
        img.save(OUT_DIR / "thumbnail.png", optimize=True)
        img.resize(OGP_SIZE, Image.LANCZOS).save(OUT_DIR / "ogp.jpg", quality=88, optimize=True)
        print(f"[compose] {OUT_DIR / 'thumbnail.png'} {img.size}、{OUT_DIR / 'ogp.jpg'} {OGP_SIZE}")
        if args.manual_plain:
            plain = crop_manual(Image.open(args.manual_plain))
            plain.save(OUT_DIR / "plain.png", optimize=True)
            print(f"[compose] {OUT_DIR / 'plain.png'} {plain.size}")
        return
    base = crop(Image.open(args.shot))
    if args.plain:
        base.save(OUT_DIR / "plain.png", optimize=True)
        print(f"[compose] {OUT_DIR / 'plain.png'} {base.size}")
        return
    img = compose(base)
    img.save(OUT_DIR / "thumbnail.png", optimize=True)
    img.resize(OGP_SIZE, Image.LANCZOS).save(OUT_DIR / "ogp.jpg", quality=88, optimize=True)
    print(f"[compose] {OUT_DIR / 'thumbnail.png'} {img.size}、{OUT_DIR / 'ogp.jpg'} {OGP_SIZE}")


if __name__ == "__main__":
    main()
