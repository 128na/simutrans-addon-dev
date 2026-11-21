#!/bin/bash
# 交差点の路面表示（#156）の見本と確かめ。NUT（既定は ingame/marking_sample.nut）を流す。
#   ingame/marking_sample.nut … 交差点の見本（2 車線の十字・優先道路の十字・T字、4 車線どうしの十字、敷いた順の見本 O2・O4）
#   ingame/marking_check.nut  … 表示を道路に重ねたときの車の速さ・路面電車と汽車が走れるか・路面軌道と線路とのつながりを見る
# ゲームは work/marking_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に AMI の pak を足して起動する。
# GAME_DIR には書き込まない。EXTRA_PAKS（空白区切り）の pak は写しの addons/pak128/ にだけ入れる。敷いた後はゲームを開いたままにする。
# 出力はパイプで渡さず、ファイルに書く（パイプに渡すと、起動したゲームが終わるまで戻らない）。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=47400 bash ingame/marking.sh > work/marking.log 2>&1 < /dev/null
#   PORT=47400 NUT=<nut> RUN=1 bash ingame/marking.sh             … 動いているゲームに NUT を流す
#   PORT=47400 SNOW=1 bash ingame/marking.sh                       … 動いているゲームの降雪側（x+256）に同じ NUT を流す
#   PORT=47400 CAPTURE=1 OUT=work/marking/shots SPOTS="名前 x y" bash ingame/marking.sh  … 撮る（x y は区画の原点からのずれ）
#   PORT=47400 SPEED=1 bash ingame/marking.sh                      … 編成の位置（区画の原点 20,40 からのずれ）と速さを 2 秒ごとに 25 回読む
#   PORT=47400 STOP=1 bash ingame/marking.sh                       … 閉じて写しを消す
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port $PORT"
WORK="work/marking_game/$PORT"
NUT=${NUT:-ingame/marking_sample.nut}
OX=20; OY=20
[ "$SNOW" = 1 ] && OX=$((OX + 256))
NUT_SED="s/^local OX = 20;/local OX = $OX;/"
PRE=""; [ "$SNOW" = 1 ] && PRE="snow_"
SPOTS=${SPOTS:-"C 6 4
P 16 4
T 26 4
W 8 12
O2 44 4
O4 44 12"}

stop_game() {
  local win; win=$(cd "$WORK" 2> /dev/null && pwd -W) || return 0
  powershell.exe -NoProfile -Command "\$d = '$win'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}

if [ "$STOP" = 1 ]; then stop_game; echo "[marking] stopped"; exit 0; fi

if [ "$SPEED" = 1 ]; then
  for i in $(seq 1 25); do
    $M --run-squirrel 'local s = ""; foreach (cv in world.get_convoy_list()) { local p = cv.get_pos(); s += "(" + (p.x - 20) + "," + (p.y - 40) + ") " + cv.get_speed() + "km/h | "; } return s;'
    sleep 2
  done
  exit 0
fi

run_nut() { $M --run-squirrel "$(sed -e "$NUT_SED" -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$NUT")" --timeout 300; }

if [ "$RUN" = 1 ] || { [ "$SNOW" = 1 ] && [ "$CAPTURE" != 1 ]; }; then run_nut; exit 0; fi

if [ "$CAPTURE" = 1 ]; then
  OUT=${OUT:-work/marking/shots}
  mkdir -p "$OUT"
  echo "$SPOTS" | while read -r name dx dy; do
    if [ -z "$ONLY" ] || [[ " $ONLY " == *" $name "* ]]; then
      $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(${ZOOM:-3}); gui.jump(coord3d($((OX + dx)),$((OY + dy)),0)); return 1;" > /dev/null 2>&1
      sleep 1
      $M --capture "$OUT/${PRE}$name.png" > /dev/null 2>&1 && echo "[capture] $OUT/${PRE}$name.png"
    fi
  done
  exit 0
fi

GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PAK=${PAK:-dist/ami.pak}

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[marking] ポート $PORT で既にゲームが動いている"; exit 1; }
rm -rf "$WORK"
mkdir -p "$WORK/save"
cp "$GAME_DIR/$EXE" "$GAME_DIR"/*.dll "$WORK/" || exit 1
for d in config font themes text script music pak128 addons; do
  [ -d "$GAME_DIR/$d" ] && { cp -r "$GAME_DIR/$d" "$WORK/" || exit 1; }
done
cp "$GAME_DIR/save/$SAVE.sve" "$WORK/save/" || exit 1
[ -f "$GAME_DIR/settings.xml" ] && { cp "$GAME_DIR/settings.xml" "$WORK/settings.xml"; chmod u+w "$WORK/settings.xml"; }
mkdir -p "$WORK/addons/pak128"
cp "$PAK" "$WORK/addons/pak128/ami.pak" || exit 1
for p in $EXTRA_PAKS; do cp "$p" "$WORK/addons/pak128/" || exit 1; done
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
run_nut
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 14)), $((OY + 4)), 0)); return 1;" > /dev/null
