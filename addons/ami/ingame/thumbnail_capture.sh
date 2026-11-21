#!/bin/bash
# リリース用のサムネイル（#96）の画面を撮る。見本の街区（ingame/thumbnail.nut）を敷き、等倍（gui.set_zoom(3)）で 1 枚撮る。
# 文字を重ねるのは ingame/thumbnail_compose.py（撮った画面は拡大・縮小しない）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=<実行ファイル> PORT=47300 bash ingame/thumbnail_capture.sh
# ゲームは work/thumbnail_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に dist/ami.pak を足して起動し、
# 撮り終えたら閉じて写しも消す。GAME_DIR には書き込まない（保存データ flat_512.sve は写しを読むだけで、保存しない）。
# 画面の大きさは SCREEN（既定 2560x1400。上の道具欄と下の状態欄を thumbnail_compose.py が切り落として 2560x1340、OGP の 1.91:1 にする）。撮る場所（画面の中心のタイル "x,y"）は VIEW（既定 101,101。空白で区切って複数渡すと、_0・_1… を付けて撮り分ける）。
# 画像は OUT（既定 work/thumbnail/shot.png）。KEEP=1 を渡すと、撮った後もゲームを閉じない（構図を探すとき。VIEW を替えて shoot だけ呼ぶ）
GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
PORT=${PORT:?PORT を指定する（作業ごとに割り当てられた範囲の中）}
SAVE=${SAVE:-flat_512}
SCREEN=${SCREEN:-2560x1400}
NUT=${NUT:-ingame/thumbnail.nut}
OUT=${OUT:-work/thumbnail/shot.png}
VIEW=${VIEW:-101,101}
SETTLE=${SETTLE:-6}   # 敷いた後、建設費の表示が消えるまで待つ秒数
source "$(dirname "$0")/mcp_client.sh"   # MCP_CLIENT の既定（リポジトリの隣の simutrans/）
M="python -X utf8 $MCP_CLIENT --port $PORT"
WORK="work/thumbnail_game/$PORT"

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[thumb] ポート $PORT で既にゲームが動いている"; exit 1; }
[ -f dist/ami.pak ] || { echo "[thumb] dist/ami.pak が無い（build.py を先に）"; exit 1; }
stop_game() {
  [ -n "$KEEP" ] && return
  powershell.exe -NoProfile -Command "\$d = '$WORK_WIN'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}
rm -rf "$WORK"
mkdir -p "$WORK/save" "$(dirname "$OUT")"
WORK_WIN=$(cd "$WORK" && pwd -W)
trap stop_game EXIT
trap 'exit 130' INT TERM
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$WORK/" || exit 1
for d in config font themes text script music pak128 addons; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$WORK/" || exit 1; }
done
cp "$GAME_DIR/save/$SAVE.sve" "$WORK/save/" || exit 1
[ -f "$GAME_DIR/settings.xml" ] && { cp "$GAME_DIR/settings.xml" "$WORK/settings.xml"; chmod u+w "$WORK/settings.xml"; }
# GAME_DIR に入っている AMI の pak（種類別の pak など）を外し、dist/ami.pak だけを入れる（二重に読まないため。icon_capture.sh と同じ）
rm -f "$WORK"/addons/pak128/ami*.pak
cp dist/ami.pak "$WORK/addons/pak128/ami.pak" || exit 1
# 昼夜で画面の明るさが変わらないように止める
printf '\nday_night_shift = 0\n' >> "$WORK/config/simuconf.tab"
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -screensize "$SCREEN" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 90); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done

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
