"""踏切の画面に AMI の踏切の絵が出ているかを、遮断機・警報機の黄色の画素の数で判定する（#128）。

本体は踏切を waytype の組と速さだけで選び、script からは踏切の名前が読めない（crossing_t の get_name は固定の "Kreuzung"）。
way の最高速度も、ほかの pak の踏切が選ばれて速さが足りていれば変わらない。そこで撮った画面の色で見分ける。
AMI の遮断かんと柱の黄色（`tools/blender/sheetlib/crossing.py` の `_M_YELLOW`）は、pak128 の踏切・道路・線路・地面に無い色の帯にある。
黄色が無いだけだと、踏切の写っていない画面（ジャンプの失敗・前の場所の撮り残し）も「ほかの踏切」に見えるので、
ほかの踏切は pak128 の踏切の標識の赤の画素で見る（AMI の踏切の赤い灯は少ない）。

使い方（アドオンのディレクトリで。ingame/crossing_sample.sh の JUDGE=1 が流す）:
    blender -b --factory-startup --python ingame/crossing_judge.py -- x0,y0,x1,y1 黄色のしきい値 赤のしきい値 入力1.png 入力2.png ...
    矩形は左上を原点とする画素座標（踏切のタイルが中ほどに来る範囲）。入力ごとに 1 行
    `[judge] <ファイル> yellow=<画素数>,red=<画素数> <判定>` を出す。判定は ami（黄色がしきい値以上）、
    other（黄色が無く、赤がしきい値以上。pak128 の踏切）、none（どちらでもない。踏切が写っていない）

値の目安（2026-11-21、拡大率 3、矩形 196,250,456,470）: 黄色は AMI の踏切が 32〜86（開いた絵・閉じた絵、温暖・降雪、H・V の 96 枚）、pak128 の踏切が 0。
赤は AMI の踏切が 0〜12、pak128 の踏切が 85。しきい値の既定（`crossing_sample.sh` の `JUDGE_MIN`・`JUDGE_RED`）は 20 と 40
"""
import os
import sys

import bpy
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
x0, y0, x1, y1 = map(int, a[0].split(","))
limit, red_limit = int(a[1]), int(a[2])
for path in a[3:]:
    img = bpy.data.images.load(os.path.abspath(path), check_existing=False)
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1][y0:y1, x0:x1, :3]
    r, g, b = (np.round(px[..., i] * 255) for i in range(3))
    # 画面の黄色は (150〜200, 135〜180, 45〜60) あたり。赤みが緑より 10〜90 強く、青が弱い画素を数える
    yellow = int(((r > 150) & (g > 100) & (b < 70) & (r - g > 10) & (r - g < 90)).sum())
    red = int(((r > 140) & (g < 90) & (b < 90) & (r - g > 80)).sum())
    verdict = "ami" if yellow >= limit else "other" if red >= red_limit else "none"
    print(f"[judge] {path} yellow={yellow},red={red} {verdict}")
    bpy.data.images.remove(img)
