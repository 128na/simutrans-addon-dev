"""pak128 以外の大きさ（256）で組む物が、pak128 の物と食い違っていないかを見る（#261・#301）。

256 は、組まない物の表 catalog.SCALED_EXCLUDED（既定は空）以外は全部組む。物を足しても表に書き足さなくてよいので、
足した物の 256 の dat を書き忘れる（コミットし忘れる）ことを、ここで止める。純 Python（Blender・256 の PNG が要らないので、CI でも動く）。次を見る:
- SCALED_EXCLUDED の名前が実在する物（src/<名前>.dat か .png がある。書き間違いで、組まない物が組まれるのを防ぐ）で、理由が書いてある
- src256/ の dat の名前の集まりが、src/ の dat の名前の集まりから SCALED_EXCLUDED を除いた物と同じ（物の足し忘れ・消し忘れ。
  分岐の追加画像の提供用 ex_donors は物ではなく、どちらにもあるので同じに扱う）
- src/ の dat・png の名前が ami_ で始まる（catalog.SCALED_TARGETS は ami_ の絵から作るので、外れた名前が黙って 256 の対象から落ちるのを防ぐ）
- 踏切のシート（SCALED_CROSSING_SHEETS）は、src/ に絵（png）がある
（SCALED_TARGETS が render.py の SHEETS のキーであることは、Blender が要るのでここでは見ない。256 で render.py を流すときに止まる）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "blender"))
import catalog  # noqa: E402

SRC = os.path.join(HERE, "src")
SRC256 = os.path.join(HERE, "src256")
EX_DONORS = "ex_donors"  # 分岐の追加画像の提供用の dat（物ではない。blender/ami_dat.py の EX_DONORS_DAT）


def names(folder, ext):
    return {os.path.splitext(f)[0] for f in os.listdir(folder) if f.endswith(ext)}


def main():
    errors = []
    dats, pngs = names(SRC, ".dat"), names(SRC, ".png")
    for n, reason in catalog.SCALED_EXCLUDED.items():
        if n not in dats and n not in pngs:
            errors.append(f"{n}: SCALED_EXCLUDED にあるが src/ に dat も絵も無い（名前の書き間違いか）")
        if not reason:
            errors.append(f"{n}: SCALED_EXCLUDED に理由が書いていない")
    want = dats - set(catalog.SCALED_EXCLUDED)
    have = names(SRC256, ".dat")
    for n in sorted(want - have):
        errors.append(f"{n}: src/ に dat があるが src256/ に無い（SHEET_PAK_SIZE=256 で blender/ami_dat.py を流して dat をコミットする。256 で組まない物は SCALED_EXCLUDED へ）")
    for n in sorted(have - want):
        errors.append(f"{n}: src256/ に dat があるが src/ に無い（消し忘れか、SCALED_EXCLUDED の物）")
    for n in sorted(dats | pngs):
        if n != EX_DONORS and not n.startswith(catalog.PREFIX):
            errors.append(f"{n}: src/ の名前が {catalog.PREFIX} で始まらない（256 の対象から外れる。名前を直す）")
    for n in catalog.SCALED_CROSSING_SHEETS:
        if n not in pngs:
            errors.append(f"{n}: 踏切のシートだが src/ に絵（png）が無い")
    if errors:
        print("\n".join(errors))
        print(f"256 の物の検査で {len(errors)} 件")
        return 1
    print(f"256 の物の検査は通った（dat {len(have)} 個・描く対象 {len(catalog.SCALED_TARGETS)}・組まない物 {len(catalog.SCALED_EXCLUDED)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
