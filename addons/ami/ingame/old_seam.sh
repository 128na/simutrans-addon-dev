#!/bin/bash
# 旧描画位置の線路（#26）を、新と並べて SIS の線路につないで撮る（確認画像用。自動の判定は seam_slope_check.sh）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami_rail.pak・dist/ami_rail_old.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=<ポート> bash ingame/old_seam.sh
# ゲームは work/game/<PORT>/ の写し（ingame/game.sh）で起動し、旧の pak（ami_rail_old.pak）と新の pak（ami_rail.pak）を入れる。
# GAME_DIR の addons/pak128 に SIS の新幹線の線路（way.SIS_ShinkansenTrack_Ballast_E01_ds.pak）を入れておく。
# 見本は ingame/old_seam.nut（y=100〜 が新、y=200〜 が旧）。撮った画面は OUT（既定 work/old_seam）に <新|旧>_<種類>_<ew|ns|dg|sl>.png。
# 撮り終えたら閉じて写しを消し、ingame/old_seam_compose.py で docs/old_seam/<種類>.png を作る
PORT=${PORT:?PORT に MCP のポートを指定する}
OUT=${OUT:-work/old_seam}
G="bash $(dirname "$0")/game.sh"
mkdir -p "$OUT"
trap 'PORT=$PORT $G STOP > /dev/null 2>&1' EXIT
# 出力をパイプに流すと、ゲームを閉じるまで返らない（way-addon.md の 8.2）ので、ファイルに書く
PAK=dist/ami_rail_old.pak EXTRA_PAKS=dist/ami_rail.pak NUT=ingame/old_seam.nut $G > "$OUT/start.txt" 2>&1
grep -o '[a-z_]* [a-z0-9]*=\[[^]]*\]' "$OUT/start.txt" | sed 's/^/[old_seam] 失敗: /'
spots=""
i=0
for k in ballast concrete ladder slab; do
  for pre in new:$((100 + 20 * i)) old:$((200 + 20 * i)); do
    IFS=: read p y <<< "$pre"
    spots="$spots ${p}_${k}_ew:136:$y ${p}_${k}_ns:146:$((y + 6)) ${p}_${k}_dg:133:$((y + 7)) ${p}_${k}_sl:152:$((y + 2))"
  done
  i=$((i + 1))
done
PORT=$PORT OUT=$OUT SPOTS="$spots" $G CAPTURE > "$OUT/capture.txt" 2>&1
echo "[old_seam] $(grep -c capture "$OUT/capture.txt") 枚を $OUT に撮った"
uv run "$(dirname "$0")/old_seam_compose.py" "$OUT"
