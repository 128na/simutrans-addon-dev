#!/bin/bash
# 水路の踏切（跳ね橋）の見本（#117）。ingame/canal_crossing.nut を流して、線路 4 種・道路 3 種 × 運河の踏切を 2 向きで敷き、
# 船と列車・車を往復させる。ゲームは work/canal_crossing_game/<PORT>/ の写し（GAME_DIR の exe・dll・設定・pak128・addons と保存データ）に
# dist/ami.pak を足して起動する。GAME_DIR には書き込まない。敷いた後はゲームを開いたままにする。
# 使い方（アドオンのディレクトリで。python -X utf8 build.py で dist/ami.pak を作っておく）:
#   GAME_DIR=<検証用のフォルダ> EXE=OTRPv64_3.exe PORT=47200 bash ingame/canal_crossing.sh > work/canal_crossing/launch.log
#                                                  … 起動して温暖側に敷き、[check] の行を出す（出力はファイルへ。ゲームを閉じるまで管が閉じないため）
#   PORT=47200 SNOW=1 bash ingame/canal_crossing.sh          … 動いているゲームの降雪側（x+256）に同じ見本を敷く
#   PORT=47200 WATCH=480 bash ingame/canal_crossing.sh       … 480 秒、乗り物の位置を見張り、踏切のタイルを船と列車・車が通ったかを出す
#                                                  （区画 H の船は端から端まで約 400 秒かかる。AMI の 14 か所でどちらかが通らなければ終了コード 1）
#   PORT=47200 CAPTURE=open OUT=work/canal_crossing/shots bash ingame/canal_crossing.sh
#                                                  … 踏切ごとに撮る（<気候>_<H|V|M|W>_<k>_open.png。SNOW=1 で降雪側）
#   PORT=47200 CAPTURE=closed OUT=work/canal_crossing/shots bash ingame/canal_crossing.sh
#                                                  … 船が踏切のタイルに乗ったら撮る（閉じた絵。撮った物は飛ばす。WAIT 秒で打ち切る）
#   PORT=47200 STOP=1 bash ingame/canal_crossing.sh          … 閉じて写しを消す
# 並びの値は canal_crossing.nut と同じにする（H: x = 5 + 6k, y = 4、V: x = 6, y = 15 + 5k、M: x = 47・53, y = 4、W: (20, 15)）
PORT=${PORT:?PORT を指定する}
source "$(dirname "$0")/mcp_client.sh"
M="python $MCP_CLIENT --port $PORT"
WORK="work/canal_crossing_game/$PORT"
NUT=ingame/canal_crossing.nut
OX=20; OY=20; CLIM=temperate
[ "$SNOW" = 1 ] && { OX=$((OX + 256)); CLIM=snow; }
NWAYS=7

# 踏切のタイル: 名前 x y（原点からのずれ）
spots() {
  for k in $(seq 0 $((NWAYS - 1))); do echo "H_$k $((5 + 6 * k)) 4"; done
  echo "M_0 47 4"; echo "M_1 53 4"
  for k in $(seq 0 $((NWAYS - 1))); do echo "V_$k 6 $((15 + 5 * k))"; done
  echo "W_0 20 15"
}

stop_game() {
  local win; win=$(cd "$WORK" 2> /dev/null && pwd -W) || return 0
  powershell.exe -NoProfile -Command "\$d = '$win'.Replace('/', '\') + '\'; Get-Process | Where-Object { \$_.Path -and \$_.Path.StartsWith(\$d, 'OrdinalIgnoreCase') } | Stop-Process -Force" > /dev/null 2>&1
  sleep 1
  rm -rf "$WORK"
}
squirrel() { $M --run-squirrel "$1" | sed 's/.*"result":"\(.*\)".*/\1/'; }
run_nut() { $M --run-squirrel "$(sed -e "s/^local OX = 20;/local OX = $OX;/" -e 's/^[[:space:]]*//' -e '/^\/\//d' -e '/^$/d' "$NUT")" --timeout 300; }
shoot() {  # $1=x $2=y $3=ファイル（飛んだ直後の 1 回目は前の場所の画面になることがあるので捨てる。crossing_sample.sh と同じ）
  $M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($1,$2,0)); return 1;" > /dev/null 2>&1
  sleep "${SHOT_WAIT:-1}"
  $M --capture "$3" > /dev/null 2>&1
  sleep 1
  $M --capture "$3" > /dev/null 2>&1 && echo "[capture] $3 ($1,$2)"
}
# 乗り物の位置（"<waytype>:x:y" を空白区切り）
POS_SQ='local out = ""; foreach (c in world.get_convoy_list()) { local q = c.get_pos(); out += c.get_waytype() + ":" + q.x + ":" + q.y + " "; } return out;'

if [ "$STOP" = 1 ]; then stop_game; echo "[canal_crossing] stopped"; exit 0; fi

if [ -n "$WATCH" ]; then
  # 踏切のタイルに、船（water）と相手の乗り物（線路・道路）が来たかを数える。温暖側・降雪側の両方を見る
  declare -A seen
  end_at=$((SECONDS + WATCH))
  while [ $SECONDS -lt $end_at ]; do
    for tok in $(squirrel "$POS_SQ"); do seen[$tok]=1; done
    sleep 0.3
  done
  # AMI の 14 か所（M・W を除く）は、船と相手の乗り物の両方が通っていなければ NG（M は相手の乗り物を走らせない。W は歩道で船が通らない）
  ng=0
  for ox in 20 276; do
    while read -r name dx dy; do
      [ "$name" = W_0 ] && continue
      x=$((ox + dx)); y=$((OY + dy))
      ship=no; other=no
      for tok in "${!seen[@]}"; do
        IFS=: read -r wt tx ty <<< "$tok"
        [ "$tx" = "$x" ] && [ "$ty" = "$y" ] || continue
        if [ "$wt" = 3 ]; then ship=yes; else other=yes; fi
      done
      echo "[watch] $ox $name ($x,$y) ship=$ship other=$other"
      case $name in M_*) ;; *) [ $ship = yes ] && [ $other = yes ] || ng=$((ng + 1)) ;; esac
    done < <(spots)
  done
  echo "[watch] NG $ng"
  [ $ng = 0 ]; exit
fi

if [ "$CAPTURE" = open ]; then
  OUT=${OUT:-work/canal_crossing/shots}
  mkdir -p "$OUT"
  spots | while read -r name dx dy; do
    if [ -z "$ONLY" ] || [[ " $ONLY " == *" $name "* ]]; then shoot $((OX + dx)) $((OY + dy)) "$OUT/${CLIM}_${name}_open.png"; fi
  done
  exit 0
fi

if [ "$CAPTURE" = closed ]; then
  OUT=${OUT:-work/canal_crossing/shots}
  mkdir -p "$OUT"
  mapfile -t SPOTS < <(spots | grep -v '^W_')
  end_at=$((SECONDS + ${WAIT:-600}))
  while [ $SECONDS -lt $end_at ]; do
    left=0
    for s in "${SPOTS[@]}"; do read -r name _ _ <<< "$s"; [ -f "$OUT/${CLIM}_${name}_closed.png" ] || left=$((left + 1)); done
    [ $left = 0 ] && { echo "[capture] 全部撮った"; exit 0; }
    for tok in $(squirrel "$POS_SQ"); do
      IFS=: read -r wt qx qy <<< "$tok"
      [ "$wt" = 3 ] || continue
      for s in "${SPOTS[@]}"; do
        read -r name dx dy <<< "$s"
        x=$((OX + dx)); y=$((OY + dy)); f="$OUT/${CLIM}_${name}_closed.png"
        [ -f "$f" ] && continue
        ddx=$((qx - x)); ddy=$((qy - y)); ddx=${ddx#-}; ddy=${ddy#-}
        if { [ "$qy" = "$y" ] && [ "$ddx" = 0 ]; } || { [ "$qx" = "$x" ] && [ "$ddy" = 0 ]; }; then shoot "$x" "$y" "$f"; fi
      done
    done
    sleep 0.3
  done
  for s in "${SPOTS[@]}"; do read -r name _ _ <<< "$s"; [ -f "$OUT/${CLIM}_${name}_closed.png" ] || echo "[capture] 撮れなかった: $CLIM $name"; done
  exit 1
fi

if [ "$SNOW" = 1 ]; then run_nut; exit 0; fi

GAME_DIR=${GAME_DIR:?GAME_DIR に検証用のフォルダを指定する}
EXE=${EXE:?EXE を指定する（例: OTRPv64_3.exe）}
SAVE=${SAVE:-flat_512}
PAK=${PAK:-dist/ami.pak}

$M --run-squirrel "return 1;" > /dev/null 2>&1 && { echo "[canal_crossing] ポート $PORT で既にゲームが動いている"; exit 1; }
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
(cd "$WORK" && "./$EXE" -objects pak128/ -addons -load "$SAVE" -mcp-port "$PORT" > /dev/null 2>&1 &)
for i in $(seq 1 60); do $M --run-squirrel "return 1;" > /dev/null 2>&1 && break; sleep 2; done
run_nut
$M --run-squirrel "gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d($((OX + 5)), $((OY + 4)), 0)); return 1;" > /dev/null
