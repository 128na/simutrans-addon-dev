#!/bin/bash
# AMI の線路の、pak128 標準の線路とのつなぎ目（tools/blender/seam_judge.py）と、坂・急坂でのレールの寄り（tools/blender/slope_measure.py）を測る。
# 見本は ingame/seam_slope.nut（線路の種類ごとに、つなぎ目の 4 か所と、急坂・1 段の坂の十字）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=<ポート> bash ingame/seam_slope_check.sh
# 旧描画位置の線路を SIS の新幹線の線路とつなぐとき（#26）: PAK=dist/ami_rail_old.pak に、
#   TRACKS_LIST="ami_rail_ballast_old ami_rail_concrete_old ami_rail_ladder_old ami_rail_slab_old" REF=SIS_ST_TGbl_E01-999B を足す
#   （見本の NUT の TRACKS・REF を、この 2 つで置き換える。SIS の pak は GAME_DIR の addons/pak128 に入れておく）
# ゲームは work/seam_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に PAK を足して起動し、
# 撮り終えたら閉じて写しも消す。GAME_DIR には書き込まない。
# 出力: OUT（既定 work/seam_slope）に <種類>_<場所>.png（画面）・.txt（タイル一覧）・_judge.png・_measure.png（拡大）。
# [seam] の行がつなぎ目ごとの判定、[slope] の行が坂のタイルごとの判定（読み方は各道具の冒頭）
PORT=${PORT:?PORT に MCP のポートを指定する}
PAK=${PAK:-dist/ami.pak}
NUT=${NUT:-ingame/seam_slope.nut}
OUT=${OUT:-work/seam_slope}
B=${BLENDER:-${SHEET_BLENDER:-blender}}  # Blender の場所（PATH に無ければ BLENDER か SHEET_BLENDER で渡す）
command -v "$B" > /dev/null 2>&1 || [ -x "$B" ] || { echo "[seam] Blender が見つからない: $B（BLENDER か SHEET_BLENDER で渡す）"; exit 1; }
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/seam_game/$PORT"
[ -f "$PAK" ] || { echo "[seam] $PAK が無い"; exit 1; }
trap game_cleanup EXIT
trap 'exit 130' INT TERM
mkdir -p "$OUT"
GAME_TAG=seam
game_start "$PAK=ami.pak" || exit 1
SCRIPT=$(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$NUT")
if [ -n "$TRACKS_LIST" ]; then  # 見本の TRACKS（線路の種類）と REF（つなぐ相手）を替える
  q=$(for t in $TRACKS_LIST; do printf '"%s", ' "$t"; done); q=${q%, }
  SCRIPT=$(echo "$SCRIPT" | sed -e "s/^local TRACKS = .*/local TRACKS = [$q];/" -e "s/^local REF = .*/local REF = \"${REF:-Rail_160_Tracks}\";/")
fi
r=$($M --run-squirrel "$SCRIPT" --timeout 300 2>&1)
case $r in *'"result":"'*) ;; *) echo "[seam] 見本を敷けない: ${r:0:400}"; exit 1 ;; esac
# 敷く命令のうち失敗したもの（名前=[理由]）
echo "$r" | python -c "import sys,json; print(json.loads(sys.stdin.read())['result'], end='')" | grep '=\[' | sed 's/^/[seam] 失敗: /'
sleep 5

shot() {  # shot <名前> <x> <y> <半径>
  local n=$1 x=$2 y=$3 d=$4
  $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($x,$y,0)); return 1;" > /dev/null 2>&1
  sleep 1
  $M --capture "$OUT/$n.png" > /dev/null 2>&1
  $M --run-squirrel "local s=\"\"; for(local yy=$y-$d;yy<=$y+$d;yy++) for(local xx=$x-$d;xx<=$x+$d;xx++){ local t=square_x(xx,yy).get_ground_tile(); local w=t.get_way(wt_rail); if(w!=null) s+=xx+\" \"+yy+\" \"+t.z+\" \"+t.get_slope()+\" \"+w.get_dirs()+\" \"+w.get_desc().get_name()+\"\n\"; } return s" 2>/dev/null \
    | python -c "import sys,json; print(json.loads(sys.stdin.read())['result'], end='')" > "$OUT/$n.txt"
}

i=0
for t in ${TRACKS_LIST:-$(sed -n 's/^local TRACKS = \[\(.*\)\];/\1/p' "$NUT" | tr -d '",')}; do
  y0=$((100 + 30 * i)); k=${t#ami_}
  for spec in ew:136:0 ns:146:6 dg:133:7 sl:152:2; do
    IFS=: read s x dy <<< "$spec"
    shot "${k}_$s" "$x" $((y0 + dy)) 6
    "$B" -b --factory-startup --python ../../tools/blender/seam_judge.py -- "$OUT/${k}_$s.png" "$OUT/${k}_$s.txt" "$OUT/${k}_${s}_judge.png" "$x,$((y0 + dy))" 2>&1 \
      | grep "^\[" | sed "s/^/$k $s /"
  done
  for spec in steep:40 slope:60; do
    IFS=: read s y <<< "$spec"
    x=$((20 + 20 * i))
    shot "${k}_$s" "$x" "$y" 4
    "$B" -b --factory-startup --python ../../tools/blender/slope_measure.py -- "$OUT/${k}_$s.png" "$OUT/${k}_$s.txt" "$x,$y" "$OUT/${k}_${s}_measure.png" 2>&1 \
      | grep "^\[" | sed "s/^/$k $s /"
  done
  i=$((i + 1))
done
