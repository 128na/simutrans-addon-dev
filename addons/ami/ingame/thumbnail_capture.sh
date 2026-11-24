#!/bin/bash
# リリース用のサムネイル（#96）の画面を撮る。見本の街区（ingame/thumbnail.nut）を敷き、等倍（gui.set_zoom(3)）で 1 枚撮る。
# 文字を重ねるのは ingame/thumbnail_compose.py（撮った画面は拡大・縮小しない）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> PORT=47300 bash ingame/thumbnail_capture.sh
# ゲームは work/thumbnail_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に dist/ami.pak を足して起動し、
# 撮り終えたら閉じて写しも消す。GAME_DIR には書き込まない（保存データは写しを読むだけで、保存しない）。
# 画面の大きさは SCREEN（既定 2560x1400。上の道具欄と下の状態欄を thumbnail_compose.py が切り落として 2560x1340、OGP の 1.91:1 にする）。撮る場所（画面の中心のタイル "x,y"）は VIEW（既定 101,101。空白で区切って複数渡すと、_0・_1… を付けて撮り分ける）。
# 画像は OUT（既定 work/thumbnail/shot.png）。KEEP=1 を渡すと、撮った後もゲームを閉じない（構図を探すとき。VIEW を替えて shoot だけ呼ぶ）
PORT=${PORT:?PORT を指定する（作業ごとに割り当てられた範囲の中）}
SCREEN=${SCREEN:-2560x1400}
NUT=${NUT:-ingame/thumbnail.nut}
OUT=${OUT:-work/thumbnail/shot.png}
VIEW=${VIEW:-101,101}
SETTLE=${SETTLE:-6}   # 敷いた後、建設費の表示が消えるまで待つ秒数
source "$(dirname "$0")/game_lib.sh"   # 起動・停止・MCP のコマンド M（#243）
WORK="work/thumbnail_game/$PORT"

trap game_cleanup EXIT
trap 'exit 130' INT TERM
mkdir -p "$(dirname "$OUT")"
GAME_TAG=thumb
GAME_ARGS="${GAME_ARGS:-} -screensize $SCREEN"
GAME_WAIT=90
game_start dist/ami.pak=ami.pak || exit 1

# コメントと空行を落として 1 本の文字列にする（コマンドラインの長さを抑える）
SCRIPT=$(sed -e 's/\r$//' -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$NUT")
RESULT=$($M --run-squirrel "$SCRIPT" --timeout 600)
echo "[thumb] $RESULT"
# 全部敷けたとき（返り値が ok）だけ撮る
case $RESULT in *'"result":"ok"'*) ;; *) echo "[thumb] 見本を敷けなかったので撮らない"; exit 1 ;; esac
sleep "$SETTLE"
shoot() {  # $1 = x,y  $2 = 出力先
  $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($1,0)); return 1;" > /dev/null 2>&1
  sleep 1.5
  rm -f "$2"
  $M --capture "$2" > /dev/null 2>&1 && [ -f "$2" ] && echo "[thumb] $2 を撮った（中心 $1）" || { echo "[thumb] 撮れなかった: $2"; FAILED=1; }
}
i=0
for v in $VIEW; do
  if [ "$(echo $VIEW | wc -w)" -eq 1 ]; then shoot "$v" "$OUT"; else shoot "$v" "${OUT%.png}_$i.png"; fi
  i=$((i + 1))
done
if [ -n "$KEEP" ]; then echo "[thumb] ゲームは開いたまま（ポート $PORT、写しは $WORK）"; fi
[ -z "$FAILED" ]
