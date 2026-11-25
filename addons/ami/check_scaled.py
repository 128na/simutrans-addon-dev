"""catalog.SCALED_SHEETS（pak128 以外の大きさで描き・組める物。#261）の名前が、実在する物かを見る。

純 Python（Blender・256 の PNG が要らないので、CI でも動く）。256 の PNG はコミットしないため、名前の書き間違い・過不足は
256 の検査では見つからない。次を見る:
- 名前に重複が無い
- src/ の dat が、分岐の追加画像の提供用（ex_donors）を除いて全部 SCALED_SHEETS に入っている（入れ忘れると、256 では ami_dat.py の put が黙って飛ばす）
- dat を持つ物は、src/<名前>.dat がある（dat を持たない SCALED_NO_DAT は、src/<名前>.png がある）
- 描く対象（SCALED_TARGETS）は、pak128 の src/<名前>.png がある（描く物が実在する）
- 描く対象でない名前（SCALED_NO_TARGET）は、壁の単独の名前なら src/<名前>.png が、絵を持たない dat（twin・踏切）なら src/<名前>.dat がある
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "blender"))
import catalog  # noqa: E402

SRC = os.path.join(HERE, "src")
EX_DONORS = "ex_donors"  # 分岐の追加画像の提供用の dat（物ではなく、build.py が継ぎ足す。blender/ami_dat.py の EX_DONORS_DAT）


def has(name, ext):
    return os.path.exists(os.path.join(SRC, name + ext))


def main():
    errors = []
    sheets = list(catalog.SCALED_SHEETS)
    seen = set()
    for n in sheets:
        if n in seen:
            errors.append(f"{n}: SCALED_SHEETS に二重に入っている")
        seen.add(n)
    for n in sheets:
        if n in catalog.SCALED_NO_DAT:
            if not has(n, ".png"):
                errors.append(f"{n}: src/ に絵（png）が無い")
        elif not has(n, ".dat"):
            errors.append(f"{n}: src/ に dat が無い（名前の書き間違いか、dat を持たない物は SCALED_NO_DAT へ）")
    for n in catalog.SCALED_TARGETS:
        if not has(n, ".png"):
            errors.append(f"{n}: 描く対象だが src/ に絵（png）が無い（render.py の SHEETS のキーか）")
    for n in catalog.SCALED_NO_TARGET:
        if n in catalog.SCALED_DAT_ONLY:
            continue
        if not has(n, ".png"):
            errors.append(f"{n}: 壁の単独の名前だが src/ に絵（png）が無い")
    for dat in sorted(os.listdir(SRC)):  # src/ の dat が全部入っているか（入れ忘れると、256 では ami_dat.py の put が黙って飛ばす）
        n, ext = os.path.splitext(dat)
        if ext == ".dat" and n not in seen and n != EX_DONORS:
            errors.append(f"{n}: src/ に dat があるが SCALED_SHEETS に入っていない（256 で描き・組めるようにして、catalog.SCALED_SHEETS に足す）")
    for n in catalog.SCALED_NO_TARGET + catalog.SCALED_NO_DAT:
        if n not in seen:
            errors.append(f"{n}: SCALED_NO_TARGET・SCALED_NO_DAT にあるが SCALED_SHEETS に無い")
    if errors:
        print("\n".join(errors))
        print(f"SCALED_SHEETS の検査で {len(errors)} 件")
        return 1
    print(f"SCALED_SHEETS の検査は通った（{len(sheets)} 名。描く対象 {len(catalog.SCALED_TARGETS)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
