"""線路の dat を作る（Blender は使わない。アドオンのディレクトリで `python -X utf8 blender/track_dat.py`）。

src/track.dat の絵の割り当て（[0] の行）を元に、シートの行の並びの決まりに合わせて書き出す:
    奥の絵 4 行 →（手前の絵 4 行。側壁・橋）→ 雪の奥の絵 4 行 →（雪の手前の絵 4 行）
- 手前の絵: front + キー（frontimage・frontimageup・frontimageup2・frontdiagonal）。同じ列の 4 行下
- 雪の絵: 同じキーの [1]。手前の絵が無いシートは 4 行下、あるシートは 8 行下

書き出すもの: track.dat・track_old.dat（雪の行を足す）、track_trial.dat、track_wall_{single,back,center,front}.dat、track_elev_{...}.dat、track_bridge.dat
"""
import os
import re

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
IMG = re.compile(r"(image|imageup|imageup2|diagonal)(\[[^\]]*\])\[0\]=(\w+)\.(\d+)\.(\d+)(.*)")


def template():
    """track.dat の先頭（設定）と、絵の割り当て（キー, 添字, 行, 列, オフセット）。"""
    head, imgs = [], []
    for l in open(os.path.join(SRC, "track.dat"), encoding="utf8").read().splitlines():
        m = IMG.match(l)
        if m:
            imgs.append((m[1], m[2], int(m[4]), int(m[5]), m[6]))
        elif not re.match(r"(front)?(image|imageup|imageup2|diagonal)\[", l):
            head.append(l)
    return head, imgs


def way(name, sheet, comment, front=False, snow=True, elevated=False):
    head, imgs = template()
    out = [comment if l.startswith("#") else l.replace("bpoc_track", name).replace("track.", sheet + ".") for l in head]
    if elevated:
        out = [l.replace("system_type=0", "system_type=1") for l in out]
    block = 8 if front else 4
    for season, base in ((0, 0), (1, block)) if snow else ((0, 0),):
        for key, idx, r, c, off in imgs:
            out.append(f"{key}{idx}[{season}]={sheet}.{r + base}.{c}{off}")
            if front:
                out.append(f"front{key}{idx}[{season}]={sheet}.{r + base + 4}.{c}{off}")
    open(os.path.join(SRC, sheet + ".dat"), "w", encoding="utf8", newline="\n").write("\n".join(out) + "\n")


def bridge():
    head = """# Blender 検証用の線路の橋の試作: 基盤・欄干・橋脚・端の坂の躯体。絵の位置は調整していない
# 端の坂（Ramp）の向きは「坂の高い側」: Ramp[N] は北が高い坂の絵（本体の slope_t::north は南が高い坂で、S の絵を使う）
obj=bridge
name=bpoc_track_bridge
copyright=blender-poc
waytype=track
cost=40000
maintenance=1000
topspeed=100
max_lenght=16
intro_year=1900
intro_month=1
retire_year=2999
retire_month=1
pillar_distance=1
icon=> track_bridge.0.0
cursor=track_bridge.0.1,-64,-32
"""
    cells = {
        "Image[NS]": (0, 2), "Image[EW]": (0, 3),
        "Start[N]": (3, 0), "Start[S]": (3, 1), "Start[E]": (3, 2), "Start[W]": (3, 3),
        "Start2[N]": (3, 5), "Start2[S]": (3, 6), "Start2[E]": (3, 7), "Start2[W]": (3, 8),
        "Ramp[N]": (1, 0), "Ramp[W]": (1, 1), "Ramp[S]": (1, 2), "Ramp[E]": (1, 3),
        "Ramp2[N]": (1, 5), "Ramp2[W]": (1, 6), "Ramp2[S]": (1, 7), "Ramp2[E]": (1, 8),
    }
    out = []
    for season, base in ((0, 0), (1, 8)):
        for k, (r, c) in cells.items():
            out.append(f"Back{k}[{season}]=track_bridge.{r + base}.{c},-64,-32")
            out.append(f"Front{k}[{season}]=track_bridge.{r + base + 4}.{c},-64,-32")
        out += [f"backPillar[S][{season}]=track_bridge.2.0,-64,-32", f"backPillar[W][{season}]=track_bridge.2.1,-64,-32"]
    open(os.path.join(SRC, "track_bridge.dat"), "w", encoding="utf8", newline="\n").write(head + "\n".join(out) + "\n")


if __name__ == "__main__":
    way("bpoc_track", "track", "# Blender 検証用の線路（道床に厚みあり）。セル配置は iss の線路と同じ。下の 4 行は雪の絵（[1]）")
    way("bpoc_track_old", "track_old", "# Blender 検証用の線路（旧描画位置）。下の 4 行は雪の絵（[1]）")
    way("bpoc_track_trial", "track_trial", "# Blender 検証用の線路の試作: 車止め・さび色・雪の絵（[1]。下の 4 行）")
    for side, ja in (("single", "両側（単線用）"), ("back", "奥だけ"), ("center", "なし（中線用）"), ("front", "手前だけ")):
        way(f"bpoc_track_wall_{side}", f"track_wall_{side}",
            f"# Blender 検証用の線路の試作: 側壁 {ja}・基盤・車止め。カメラに近い側の壁は手前の絵（front...）、雪は [1]", front=True)
        way(f"bpoc_track_elev_{side}", f"track_elev_{side}",
            f"# Blender 検証用の線路の試作: 高架（system_type=1）。側壁 {ja}・基盤・橋脚。手前の壁は front...、雪は [1]",
            front=True, elevated=True)
    bridge()
